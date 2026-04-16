# -*- coding: utf-8 -*-
"""
区域结算服务模块
"""

import json
import random
import copy
from utils.constants import FISHING_BAG_ITEMS, SLOT_TEMPLATES, MARKET_PRICES, CHALLENGE_SLOT_DONE, GRADE_VALUES
from utils.events import ServerEvents, ServerAreaActionTypes, ServerBattleActionTypes
from utils.logger import log_info, log_debug
from utils.helpers import send_error, make_action_message, create_lobster as _make_lobster, calculate_market_prices, make_settlement_state
from services.tribute_card_effects import check_market_rule, check_breed_bonus, check_tribute_discount, check_battle_bonus, check_adjacent_action, get_adjacent_rewards, apply_aura_effect


def _create_lobster(grade='normal'):
    """创建一只龙虾对象（保留别名以兼容内部调用）"""
    return _make_lobster(grade)


def draw_from_bag(game_state: dict) -> str:
    """从捕虾盲袋中抽取一个指示物。如果池子空了，自动剔除龙虾牌。"""
    shrimp_area = game_state['areas']['shrimp_catching']
    pool = shrimp_area.get('wildLobsterPool', 0)

    valid_items = []
    for item in FISHING_BAG_ITEMS:
        # 如果池子空了，盲袋里就没有龙虾了
        if item['type'] == 'lobster' and pool <= 0:
            continue
        valid_items.append(item)

    total_weight = sum(item['weight'] for item in valid_items)
    rand = random.random() * total_weight

    for item in valid_items:
        rand -= item['weight']
        if rand <= 0:
            return item['type']

    return valid_items[0]['type']


# =============================================================================
# 【核心】：龙虾生命周期与流转守门员
# =============================================================================
def _check_shrimp_end_and_transfer(game_state, current_slot_index):
    slots = game_state['areas']['shrimp_catching']['slots']
    is_last = True
    for idx in range(current_slot_index, len(slots)):
        if slots[idx] is not None:
            is_last = False
            break

    if is_last:
        area_data = game_state['areas']['shrimp_catching']
        remaining_lobsters = area_data.get('wildLobsterPool', 0)

        # 必须加标记，保证每回合只流入一次
        if remaining_lobsters > 0 and not area_data.get('transferredThisRound'):
            market_area = game_state['areas']['seafood_market']
            market_area['marketLobsterCount'] = market_area.get('marketLobsterCount', 0) + remaining_lobsters
            if market_area['marketLobsterCount'] > 8:
                market_area['marketLobsterCount'] = 8

            area_data['wildLobsterPool'] = 0
            area_data['transferredThisRound'] = True

            try:
                from services.game import update_market_prices
                update_market_prices(game_state)
            except Exception:
                pass
            log_info(f"[shrimp_catching] 结算完毕，剩余 {remaining_lobsters} 只龙虾完美流入海鲜市场！")


# =============================================================================
# 异步逐步结算系统（新）
# =============================================================================

async def resolve_area_step(game_state: dict, area_index: int, manager, room_id):
    from utils.constants import AREAS

    area_name = AREAS[area_index]
    area_data = game_state['areas'].get(area_name)
    if not area_data:
        return 'auto_next'

    if area_name == 'shrimp_catching':
        return await _resolve_shrimp_catching_step(game_state, manager, room_id)
    elif area_name == 'seafood_market':
        return await _resolve_seafood_market_step(game_state, manager, room_id)
    elif area_name == 'breeding':
        return await _resolve_breeding_step(game_state, manager, room_id)
    elif area_name == 'tribute':
        return await _resolve_tribute_step(game_state, manager, room_id)
    elif area_name == 'marketplace':
        return await _resolve_marketplace_step(game_state, manager, room_id)

    return 'auto_next'


async def _resolve_shrimp_catching_step(game_state: dict, manager, room_id):
    """结算捕虾区"""
    area_data = game_state['areas']['shrimp_catching']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['shrimp_catching']

    # 【绝对保障】：跟着回合数走，只要进入新的一回合，强制补充满 8 只！
    current_round = game_state.get('currentRound', 1)
    if area_data.get('poolRound') != current_round:
        area_data['wildLobsterPool'] = 8
        area_data['poolRound'] = current_round
        area_data['transferredThisRound'] = False

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', 0)

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is None:
            current_slot_index += 1
            continue

        player = game_state['players'][player_id]
        template = templates[current_slot_index]
        remaining_actions = template['actionCount']
        reward_given = False

        game_state['settlementState'] = make_settlement_state('shrimp_catching', current_slot_index, remaining_actions, player_id,
            rewardGiven=reward_given, step='waiting_confirm')

        await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
        make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
            'areaType': 'shrimp_catching',
            'playerId': player_id,
            'actionCount': remaining_actions,
            'step': 'waiting_confirm',
            'player': _serialize_player(player),
            'reward': template['reward'],
            'rewardGiven': reward_given
        }))

        return 'waiting_ui'

    # 如果没有任何人占领捕虾区，也要把这 8 只流进去
    _check_shrimp_end_and_transfer(game_state, current_slot_index)
    return 'auto_next'


async def _resolve_seafood_market_step(game_state: dict, manager, room_id):
    """结算海鲜市场"""
    area_data = game_state['areas']['seafood_market']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['seafood_market']

    # =========================================================================
    # 【双重保险兜底】：如果跳过了前面的检验，市场门一开直接强制强吸！
    # =========================================================================
    shrimp_area = game_state['areas']['shrimp_catching']
    remaining_lobsters = shrimp_area.get('wildLobsterPool', 0)

    if remaining_lobsters > 0 and not shrimp_area.get('transferredThisRound'):
        area_data['marketLobsterCount'] = area_data.get('marketLobsterCount', 0) + remaining_lobsters
        if area_data['marketLobsterCount'] > 8:
            area_data['marketLobsterCount'] = 8

        shrimp_area['wildLobsterPool'] = 0
        shrimp_area['transferredThisRound'] = True

        try:
            from services.game import update_market_prices
            update_market_prices(game_state)
        except Exception:
            pass
        log_info(f"[seafood_market] 兜底吸入捕虾区剩余 {remaining_lobsters} 只龙虾！当前市场总数: {area_data['marketLobsterCount']}")
    # =========================================================================

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', 0)

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is not None:
            player = game_state['players'][player_id]
            template = templates[current_slot_index]
            action_count = template['actionCount']
            reward = template['reward']

            if reward.get('coins'):
                player['coins'] += reward['coins']

            if check_adjacent_action(player):
                total_slots = len(slots)
                adjacent_reward = get_adjacent_rewards('seafood_market', current_slot_index, total_slots)
                for res_type, res_value in adjacent_reward.items():
                    if res_type == 'coins':
                        player['coins'] = player.get('coins', 0) + res_value
                    elif res_type == 'cages':
                        player['cages'] = player.get('cages', 0) + res_value
                    elif res_type == 'seaweed':
                        player['seaweed'] = player.get('seaweed', 0) + res_value

            if action_count > 0:
                prices = calculate_market_prices(area_data['marketLobsterCount'])
                game_state['settlementState'] = make_settlement_state('seafood_market', current_slot_index, action_count, player_id)

                await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
        make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'seafood_market',
                    'playerId': player_id,
                    'actionCount': action_count,
                    'prices': prices,
                    'player': _serialize_player(player),
                    'marketLobsterCount': area_data['marketLobsterCount']
                }))

                return 'waiting_ui'

        current_slot_index += 1

    return 'auto_next'


async def _resolve_breeding_step(game_state: dict, manager, room_id):
    """结算养蛊区"""
    area_data = game_state['areas']['breeding']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['breeding']

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', 0)

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is not None:
            player = game_state['players'][player_id]
            template = templates[current_slot_index]
            action_count = template['actionCount'] if template else 1

            is_arena_override = settlement_state.get('overrideActionCount') is not None
            if is_arena_override:
                action_count = settlement_state.get('overrideActionCount')

            reward = template.get('reward', {})

            if not is_arena_override:
                if reward.get('seaweed'):
                    player['seaweed'] = player.get('seaweed', 0) + reward['seaweed']
                if reward.get('coins'):
                    player['coins'] = player.get('coins', 0) + reward['coins']

                if check_adjacent_action(player):
                    total_slots = len(slots)
                    adjacent_reward = get_adjacent_rewards('breeding', current_slot_index, total_slots)
                    for res_type, res_value in adjacent_reward.items():
                        if res_type == 'coins':
                            player['coins'] = player.get('coins', 0) + res_value
                        elif res_type == 'seaweed':
                            player['seaweed'] = player.get('seaweed', 0) + res_value
                        elif res_type == 'cages':
                            player['cages'] = player.get('cages', 0) + res_value

            if len(player['lobsters']) == 0:
                if is_arena_override:
                    game_state['settlementState'] = make_settlement_state('marketplace', current_slot_index, 1, player_id)
                    game_state['settlementState']['currentSlotIndex'] += 1
                    game_state['settlementState']['waitingForPlayer'] = None
                    return 'action_complete'
                current_slot_index += 1
                continue

            if not is_arena_override:
                game_state['settlementState'] = make_settlement_state('breeding', current_slot_index, action_count, player_id)

            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'breeding',
                    'playerId': player_id,
                    'actionCount': action_count,
                    'player': _serialize_player(player),
                }))

            return 'waiting_ui'

        current_slot_index += 1

    return 'auto_next'


async def _resolve_tribute_step(game_state: dict, manager, room_id):
    """结算上供区"""
    area_data = game_state['areas']['tribute']
    slots = area_data['slots']

    if 'tributeBattlesCompleted' not in game_state:
        game_state['tributeBattlesCompleted'] = 0

    if not game_state.get('battleQueue'):
        game_state['battleQueue'] = []
        tribute = game_state['areas'].get('tribute')
        challenge_slots_battle_status = tribute.get('challengeSlots', [])

        for challenge_idx in range(3, 6):
            defender_idx = challenge_idx - 3
            challenger_id = slots[challenge_idx]
            defender_id = slots[defender_idx]

            if challenger_id is not None and defender_id is not None and challenge_slots_battle_status[defender_idx] != CHALLENGE_SLOT_DONE and challenger_id != defender_id:
                game_state['battleQueue'].append({
                    'challengerId': challenger_id,
                    'defenderId': defender_id,
                    'challengeSlot': challenge_idx,
                    'defenderSlot': defender_idx
                })
    else:
        log_debug("[_resolve_tribute_step] battleQueue 已存在，跳过重建")

    if len(game_state['battleQueue']) > 0:
        current_battle_key = json.dumps(game_state['battleQueue'], sort_keys=True)
        last_battle_start = game_state.get('_lastBattleStartSent')

        if last_battle_start == current_battle_key:
            game_state['settlementState'] = make_settlement_state('tribute')
            return 'waiting_ui'

        game_state['_lastBattleStartSent'] = current_battle_key
        players_need_choice = []
        for battle in game_state.get('battleQueue', []):
            challenger = next((p for p in game_state['players'] if p['id'] == battle['challengerId']), None)
            defender = next((p for p in game_state['players'] if p['id'] == battle['defenderId']), None)
            if challenger and check_battle_bonus(challenger):
                if challenger['id'] not in players_need_choice:
                    players_need_choice.append(challenger['id'])
            if defender and check_battle_bonus(defender):
                if defender['id'] not in players_need_choice:
                    players_need_choice.append(defender['id'])

        if players_need_choice:
            game_state['pendingBattleBonusChoices'] = players_need_choice
            game_state['settlementState'] = make_settlement_state('tribute')
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'tribute',
                    'waitingForBattleBonusChoice': True,
                    'playersNeedChoice': players_need_choice,
                    'battleQueue': game_state['battleQueue']
                }))
            return 'waiting_ui'

        game_state['settlementState'] = make_settlement_state('tribute')
        await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
            make_action_message(ServerBattleActionTypes.BATTLE_START, {
                'battleQueue': game_state['battleQueue']
            }))
        return 'waiting_ui'

    return await _resolve_tribute_actions(game_state, manager, room_id)


async def _resolve_tribute_actions(game_state: dict, manager, room_id):
    area_data = game_state['areas']['tribute']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['tribute']

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', 0)

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]

        if player_id is not None:
            template = templates[current_slot_index]
            action_count = template['actionCount'] if template else 1
            player = game_state['players'][player_id]

            game_state['settlementState'] = make_settlement_state('tribute', current_slot_index, action_count, player_id)
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'tribute',
                    'playerId': player_id,
                    'actionCount': action_count,
                    'slotIndex': current_slot_index,
                    'player': _serialize_player(player),
                    'taverns': game_state.get('taverns', []),
                    'tributeTasks': game_state.get('tributeTasks', [])
                }))
            return 'waiting_ui'
        current_slot_index += 1

    return 'auto_next'


async def _resolve_marketplace_step(game_state: dict, manager, room_id):
    """结算闹市区"""
    area_data = game_state['areas']['marketplace']
    slots = area_data['slots']
    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', 0)

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is not None:
            player = game_state['players'][player_id]
            raw_available_cards = [
                card for card in game_state.get('downtownCards', [])
                if not card.get('usedThisRound', False)
            ]

            if len(raw_available_cards) == 0:
                current_slot_index += 1
                continue

            available_cards = []
            for card in raw_available_cards:
                c = copy.deepcopy(card)
                inner_type = c.get('action', {}).get('type')

                if inner_type == 'post_station':
                    tributes_count = player.get('tributesThisRound', 0)
                    if tributes_count > 0:
                        c['action']['type'] = 'exchange'
                        c['auto'] = False
                        options = []
                        for i in range(tributes_count + 1):
                            options.append({'cost': {}, 'reward': {'de': i, 'wang': tributes_count - i}})
                        c['action']['options'] = options
                    else:
                        c['auto'] = True

                elif inner_type == 'academy':
                    if player.get('de', 0) == player.get('wang', 0):
                        c['action']['type'] = 'exchange'
                        c['auto'] = False
                        c['action']['options'] = [
                            {'cost': {}, 'reward': {'de': 1}},
                            {'cost': {}, 'reward': {'wang': 1}}
                        ]
                    else:
                        c['auto'] = True

                available_cards.append(c)

            game_state['settlementState'] = make_settlement_state('marketplace', current_slot_index, 1, player_id)
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'marketplace',
                    'playerId': player_id,
                    'actionCount': 1,
                    'availableCards': available_cards,
                    'player': _serialize_player(player),
                }))
            return 'waiting_ui'
        current_slot_index += 1
    return 'auto_next'


async def process_area_action(game_state: dict, action_type: str, action_payload: dict, manager, room_id, websocket):
    """处理结算阶段的前端交互操作"""
    settlement_state = game_state.get('settlementState', {})
    area_type = settlement_state.get('areaType')
    player_id = settlement_state.get('waitingForPlayer')

    if player_id is None:
        return 'error'

    player = next((p for p in game_state['players'] if p['id'] == player_id), None)
    if not player:
        return 'error'

    if area_type == 'shrimp_catching':
        return await _process_shrimp_catching_action(game_state, action_type, action_payload, player, manager, room_id, websocket)
    elif area_type == 'seafood_market':
        return await _process_seafood_market_action(game_state, action_type, action_payload, player, manager, room_id, websocket)
    elif area_type == 'breeding':
        return await _process_breeding_action(game_state, action_type, action_payload, player, manager, room_id, websocket)
    elif area_type == 'tribute':
        return await _process_tribute_action(game_state, action_type, action_payload, player, manager, room_id, websocket)
    elif area_type == 'marketplace':
        return await _process_marketplace_action(game_state, action_type, action_payload, player, manager, room_id, websocket)

    return 'error'


async def _process_shrimp_catching_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    settlement_state = game_state.get('settlementState', {})
    remaining_actions = settlement_state.get('remainingActions', 0)
    current_slot_index = settlement_state.get('currentSlotIndex', 0)
    templates = SLOT_TEMPLATES['shrimp_catching']
    template = templates[current_slot_index]
    reward_given = settlement_state.get('rewardGiven', False)
    step = settlement_state.get('step', 'waiting_confirm')

    if action_type == 'confirm':
        if step != 'waiting_confirm':
            await send_error(websocket, '当前状态不允许确认')
            return 'error'
        if remaining_actions <= 0:
            await send_error(websocket, '没有剩余行动次数')
            return 'error'

        # 抽卡时将当前物理游戏数据扔进去
        item = draw_from_bag(game_state)
        result_msg = ''

        # 预防性降级：如果抽到 either 但没龙虾了，直接当成海草
        if item == 'either' and game_state['areas']['shrimp_catching'].get('wildLobsterPool', 0) <= 0:
            item = 'seaweed'

        if item == 'either':
            game_state['settlementState'] = make_settlement_state('shrimp_catching', current_slot_index, remaining_actions,
                settlement_state.get('waitingForPlayer'), rewardGiven=reward_given, step='waiting_choice', item=item)

            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'shrimp_catching',
                    'playerId': settlement_state.get('waitingForPlayer'),
                    'actionCount': remaining_actions,
                    'step': 'waiting_choice',
                    'indicatorType': 'either',
                    'player': _serialize_player(player),
                    'reward': template.get('reward', {}),
                    'rewardGiven': reward_given
                }))
            return 'continue_ui'

        elif item == 'bubble':
            player['tempBubbles'] += 1
            result_msg = '获得1个气泡'
        elif item == 'lobster':
            shrimp_area = game_state['areas']['shrimp_catching']
            pool = shrimp_area.get('wildLobsterPool', 0)
            if pool > 0:
                shrimp_area['wildLobsterPool'] = pool - 1
                player['lobsters'].append(_create_lobster('normal'))
                result_msg = '获得1只野生龙虾'
            else:
                result_msg = '野生龙虾已空'
        elif item == 'seaweed':
            player['seaweed'] += 1
            result_msg = '获得1根海草'

        if not reward_given:
            reward = template.get('reward', {})
            if reward.get('cages'): player['cages'] += reward['cages']
            if reward.get('coins'): player['coins'] += reward['coins']
            if reward.get('stealStart'):
                game_state['startingPlayerIndex'] = settlement_state.get('waitingForPlayer')
                for p in game_state['players']: p['isStartingPlayer'] = False
                player['isStartingPlayer'] = True
            reward_given = True

            if check_adjacent_action(player):
                total_slots = len(game_state['areas']['shrimp_catching']['slots'])
                adjacent_reward = get_adjacent_rewards('shrimp_catching', current_slot_index, total_slots)
                for res_type, res_value in adjacent_reward.items():
                    if res_type == 'coins': player['coins'] = player.get('coins', 0) + res_value
                    elif res_type == 'cages': player['cages'] = player.get('cages', 0) + res_value

        remaining_actions -= 1

        if remaining_actions <= 0:
            game_state['settlementState']['waitingForPlayer'] = None
            game_state['settlementState']['step'] = 'done'
            game_state['settlementState']['currentSlotIndex'] = current_slot_index + 1

            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'shrimp_catching',
                    'playerId': settlement_state.get('waitingForPlayer'),
                    'actionCount': 0,
                    'step': 'done',
                    'lastResult': result_msg,
                    'lastItem': item,
                    'player': _serialize_player(player),
                    'reward': template.get('reward', {}),
                    'rewardGiven': reward_given
                }))

            # 本玩家结束后，强行检查流转
            _check_shrimp_end_and_transfer(game_state, current_slot_index + 1)
            return 'action_complete'
        else:
            game_state['settlementState'] = make_settlement_state('shrimp_catching', current_slot_index, remaining_actions,
                settlement_state.get('waitingForPlayer'), rewardGiven=reward_given, step='waiting_confirm', lastResult=result_msg, lastItem=item)

            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'shrimp_catching',
                    'playerId': settlement_state.get('waitingForPlayer'),
                    'actionCount': remaining_actions,
                    'step': 'waiting_confirm',
                    'lastResult': result_msg,
                    'lastItem': item,
                    'player': _serialize_player(player),
                    'reward': template.get('reward', {}),
                    'rewardGiven': reward_given
                }))
            return 'continue_ui'

    elif action_type == 'choose_either':
        if step != 'waiting_choice':
            await send_error(websocket, '当前状态不允许选择')
            return 'error'
        choice = action_payload.get('choice')
        if choice not in ('lobster', 'seaweed'):
            await send_error(websocket, '无效的选择')
            return 'error'

        result_msg = ''
        if choice == 'lobster':
            shrimp_area = game_state['areas']['shrimp_catching']
            pool = shrimp_area.get('wildLobsterPool', 0)
            if pool > 0:
                shrimp_area['wildLobsterPool'] = pool - 1
                player['lobsters'].append(_create_lobster('normal'))
                result_msg = '获得1只野生龙虾'
            else:
                result_msg = '野生龙虾已空'
        elif choice == 'seaweed':
            player['seaweed'] += 1
            result_msg = '获得1根海草'

        if not reward_given:
            reward = template.get('reward', {})
            if reward.get('cages'): player['cages'] += reward['cages']
            if reward.get('coins'): player['coins'] += reward['coins']
            if reward.get('stealStart'):
                game_state['startingPlayerIndex'] = settlement_state.get('waitingForPlayer')
                for p in game_state['players']: p['isStartingPlayer'] = False
                player['isStartingPlayer'] = True
            reward_given = True

        remaining_actions -= 1

        if remaining_actions <= 0:
            game_state['settlementState']['waitingForPlayer'] = None
            game_state['settlementState']['step'] = 'done'
            game_state['settlementState']['currentSlotIndex'] = current_slot_index + 1

            _check_shrimp_end_and_transfer(game_state, current_slot_index + 1)
            return 'action_complete'
        else:
            game_state['settlementState'] = make_settlement_state('shrimp_catching', current_slot_index, remaining_actions,
                settlement_state.get('waitingForPlayer'), rewardGiven=reward_given, step='waiting_confirm', lastResult=result_msg, lastItem='either')

            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'shrimp_catching',
                    'playerId': settlement_state.get('waitingForPlayer'),
                    'actionCount': remaining_actions,
                    'step': 'waiting_confirm',
                    'lastResult': result_msg,
                    'lastItem': 'either',
                    'player': _serialize_player(player),
                    'reward': template.get('reward', {}),
                    'rewardGiven': reward_given
                }))
            return 'continue_ui'

    elif action_type == 'skip':
        game_state['settlementState']['waitingForPlayer'] = None
        game_state['settlementState']['remainingActions'] = 0
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1

        _check_shrimp_end_and_transfer(game_state, current_idx + 1)
        return 'action_complete'
    else:
        await send_error(websocket, '未知操作类型')
        return 'error'


async def _process_seafood_market_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    settlement_state = game_state.get('settlementState', {})
    remaining_actions = settlement_state.get('remainingActions', 0)

    if remaining_actions <= 0:
        await send_error(websocket, '没有剩余行动次数')
        return 'error'

    area_data = game_state['areas']['seafood_market']
    prices = calculate_market_prices(area_data['marketLobsterCount'])

    market_rule = check_market_rule(player)
    buy_price = market_rule['buyPrice'] if market_rule else prices['buyLobster']

    success = False

    if action_type == 'buy_lobster':
        if player['coins'] >= buy_price and area_data['marketLobsterCount'] > 0:
            player['coins'] -= buy_price
            area_data['marketLobsterCount'] -= 1
            player['lobsters'].append(_create_lobster('normal'))
            success = True
        else:
            await send_error(websocket, '金币不足或市场无龙虾')
            return 'error'
    elif action_type == 'sell_lobster':
        if market_rule and not market_rule.get('canSell', True):
            await send_error(websocket, '不能再卖龙虾给集市')
            return 'error'
        if len(player['lobsters']) > 0:
            player['lobsters'].pop(0)
            player['coins'] += prices['sellLobster']
            area_data['marketLobsterCount'] += 1
            if area_data['marketLobsterCount'] > 8: area_data['marketLobsterCount'] = 8
            success = True
        else:
            await send_error(websocket, '没有龙虾可卖')
            return 'error'
    elif action_type == 'buy_cage':
        if player['coins'] >= prices['buyCage']:
            player['coins'] -= prices['buyCage']
            player['cages'] += 1
            success = True
        else:
            await send_error(websocket, '金币不足')
            return 'error'
    elif action_type == 'sell_cage':
        if player['cages'] > 0:
            player['cages'] -= 1
            player['coins'] += prices['sellCage']
            success = True
        else:
            await send_error(websocket, '没有虾笼可卖')
            return 'error'
    elif action_type == 'buy_seaweed':
        if player['coins'] >= prices['buySeaweed']:
            player['coins'] -= prices['buySeaweed']
            player['seaweed'] += 1
            success = True
        else:
            await send_error(websocket, '金币不足')
            return 'error'
    elif action_type == 'sell_seaweed':
        if player['seaweed'] > 0:
            player['seaweed'] -= 1
            player['coins'] += prices['sellSeaweed']
            success = True
        else:
            await send_error(websocket, '没有海草可卖')
            return 'error'

    # 【处理批发买卖海草】
    elif action_type == 'buy_seaweed_3':
        if player['coins'] >= prices['buySeaweed3']:
            player['coins'] -= prices['buySeaweed3']
            player['seaweed'] += 3
            success = True
        else:
            await send_error(websocket, '金币不足')
            return 'error'
    elif action_type == 'sell_seaweed_3':
        if player['seaweed'] >= 3:
            player['seaweed'] -= 3
            player['coins'] += prices['sellSeaweed3']
            success = True
        else:
            await send_error(websocket, '海草不足(需3根)')
            return 'error'

    elif action_type == 'hire_headman_slot':
        slot_index = action_payload.get('slotIndex')
        if player['coins'] < 6:
            await send_error(websocket, '金币不足(需6金币)')
            return 'error'

        if 'hireSlots' not in game_state: game_state['hireSlots'] = [None] * 8
        if game_state['hireSlots'][slot_index] is not None:
            await send_error(websocket, '该槽位已被占领')
            return 'error'

        player['coins'] -= 6
        game_state['hireSlots'][slot_index] = player['id']

        if 'hiredLaborersBonus' not in player: player['hiredLaborersBonus'] = []
        player['hiredLaborersBonus'].append(slot_index)

        if slot_index in [0, 1]: player['seaweed'] = player.get('seaweed', 0) + 1
        elif slot_index in [2, 3]: player['lobsters'].append(_create_lobster('normal'))
        elif slot_index in [4, 5]: player['lobsters'].append(_create_lobster('grade3'))
        elif slot_index in [6, 7]: player['lobsters'].append(_create_lobster('grade2'))
        success = True
    elif action_type == 'skip':
        game_state['settlementState']['waitingForPlayer'] = None
        game_state['settlementState']['remainingActions'] = 0
        current_idx = settlement_state.get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    else:
        await send_error(websocket, '未知操作类型')
        return 'error'

    if not success: return 'error'

    remaining_actions -= 1
    game_state['settlementState']['remainingActions'] = remaining_actions

    if remaining_actions <= 0:
        game_state['settlementState']['waitingForPlayer'] = None
        current_idx = settlement_state.get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    else:
        await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
            make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                'areaType': 'seafood_market',
                'playerId': settlement_state.get('waitingForPlayer'),
                'actionCount': remaining_actions,
                'prices': calculate_market_prices(area_data['marketLobsterCount']),
                'player': _serialize_player(player),
                'marketLobsterCount': area_data['marketLobsterCount']
            }))
        return 'continue_ui'


async def _process_breeding_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    settlement_state = game_state.get('settlementState', {})
    remaining_actions = settlement_state.get('remainingActions', 0)

    if remaining_actions <= 0:
        await send_error(websocket, '没有剩余行动次数')
        return 'error'

    if action_type == 'cultivateLobster':
        lobster_index = action_payload.get('lobsterIndex')
        use_seaweed = action_payload.get('useSeaweed', False)
        royal_cost_type = action_payload.get('royalCostType')
        royal_reward_type = action_payload.get('royalRewardType', 'de')
        selected_title_id = action_payload.get('selectedTitleId')

        if lobster_index is None or lobster_index >= len(player['lobsters']):
            await send_error(websocket, '无效的龙虾选择')
            return 'error'

        lobster = player['lobsters'][lobster_index]
        old_grade = lobster['grade']

        def get_next_grade(g):
            mapping = {'normal': 'grade3', 'grade3': 'grade2', 'grade2': 'grade1', 'grade1': 'royal', 'royal': 'royal'}
            return mapping.get(g, g)

        target_grade = get_next_grade(old_grade)

        if use_seaweed:
            if player.get('seaweed', 0) < 1:
                await send_error(websocket, '海草不足')
                return 'error'
            if old_grade == 'normal': target_grade = 'grade2'
            elif old_grade == 'grade3': target_grade = 'grade1'
            else: target_grade = 'royal'

        is_upgrading_to_royal = (old_grade != 'royal' and target_grade == 'royal')

        if is_upgrading_to_royal:
            if royal_cost_type == 'cage':
                if player.get('cages', 0) < 1: return 'error'
                player['cages'] -= 1
            elif royal_cost_type == 'coin':
                if player.get('coins', 0) < 3: return 'error'
                player['coins'] -= 3
            else: return 'error'

            if royal_reward_type == 'de': player['de'] = player.get('de', 0) + 1
            elif royal_reward_type == 'wang': player['wang'] = player.get('wang', 0) + 1

            if selected_title_id:
                game_titles = game_state.get('gameTitleCards', [])
                for i, tc in enumerate(game_titles):
                    if tc.get('id') == selected_title_id:
                        player['titleCards'].append(game_titles.pop(i))
                        player['lobsters'].pop(lobster_index)
                        break

        if use_seaweed: player['seaweed'] -= 1
        lobster['grade'] = target_grade

        has_breed_bonus = check_breed_bonus(player)
        if has_breed_bonus and lobster['grade'] != 'royal':
            lobster['grade'] = get_next_grade(lobster['grade'])

        remaining_actions -= 1
        game_state['settlementState']['remainingActions'] = remaining_actions

        if remaining_actions <= 0:
            is_arena_override = settlement_state.get('overrideActionCount') is not None
            if is_arena_override:
                game_state['settlementState'] = make_settlement_state('marketplace', settlement_state.get('currentSlotIndex'), 1, player['id'])
                game_state['settlementState']['currentSlotIndex'] += 1
                game_state['settlementState']['waitingForPlayer'] = None
                return 'action_complete'
            else:
                game_state['settlementState']['waitingForPlayer'] = None
                current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
                game_state['settlementState']['currentSlotIndex'] = current_idx + 1
                return 'action_complete'
        else:
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': 'breeding',
                    'playerId': settlement_state.get('waitingForPlayer'),
                    'actionCount': remaining_actions,
                    'player': _serialize_player(player),
                }))
            return 'continue_ui'
    elif action_type == 'skip':
        is_arena_override = settlement_state.get('overrideActionCount') is not None
        if is_arena_override:
            game_state['settlementState'] = make_settlement_state('marketplace', settlement_state.get('currentSlotIndex'), 1, player['id'])
            game_state['settlementState']['currentSlotIndex'] += 1
            game_state['settlementState']['waitingForPlayer'] = None
            return 'action_complete'

        game_state['settlementState']['waitingForPlayer'] = None
        game_state['settlementState']['remainingActions'] = 0
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    else:
        return 'error'


async def _process_marketplace_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    settlement_state = game_state.get('settlementState', {})

    if action_type == 'executeDowntownAction':
        card_index = action_payload.get('cardIndex')
        option_index = action_payload.get('optionIndex', 0)
        available_cards = [c for c in game_state.get('downtownCards', []) if not c.get('usedThisRound', False)]

        if card_index is None or card_index >= len(available_cards): return 'error'
        card = available_cards[card_index]
        card['usedThisRound'] = True
        action_type_inner = card.get('action', {}).get('type')

        if action_type_inner == 'exchange':
            options = card.get('action', {}).get('options', [])
            if option_index >= len(options): return 'error'
            cost = options[option_index].get('cost', {})
            reward = options[option_index].get('reward', {})

            for res_type, res_amount in cost.items():
                if res_type == 'lobsters':
                    if len(player['lobsters']) < res_amount: return 'error'
                    for _ in range(res_amount): player['lobsters'].pop(0)
                elif res_type == 'de':
                    if player['de'] < res_amount: return 'error'
                    player['de'] -= res_amount
                elif res_type == 'wang':
                    if player['wang'] < res_amount: return 'error'
                    player['wang'] -= res_amount
                elif res_type == 'coins':
                    if player['coins'] < res_amount: return 'error'
                    player['coins'] -= res_amount
                elif res_type == 'seaweed':
                    if player['seaweed'] < res_amount: return 'error'
                    player['seaweed'] -= res_amount
                elif res_type == 'cages':
                    if player['cages'] < res_amount: return 'error'
                    player['cages'] -= res_amount

            for res_type, res_amount in reward.items():
                if res_type == 'lobsters':
                    for _ in range(res_amount): player['lobsters'].append(_create_lobster('normal'))
                elif res_type == 'de': player['de'] += res_amount
                elif res_type == 'wang': player['wang'] += res_amount
                elif res_type == 'coins': player['coins'] += res_amount
                elif res_type == 'seaweed': player['seaweed'] += res_amount
                elif res_type == 'cages': player['cages'] += res_amount

        elif action_type_inner == 'post_station':
            tributes_count = player.get('tributesThisRound', 0)
            if tributes_count > 0:
                if option_index < 0 or option_index > tributes_count: return 'error'
                player['de'] = player.get('de', 0) + option_index
                player['wang'] = player.get('wang', 0) + (tributes_count - option_index)

        elif action_type_inner == 'breeding_4':
            if len(player['lobsters']) > 0:
                current_slot_index = settlement_state.get('currentSlotIndex', 0)
                game_state['settlementState'] = make_settlement_state('breeding', current_slot_index, 4, player['id'])
                game_state['settlementState']['overrideActionCount'] = 4
                await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                    make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                        'areaType': 'breeding',
                        'playerId': player['id'],
                        'actionCount': 4,
                        'player': _serialize_player(player),
                    }))
                return 'continue_ui'

        elif action_type_inner == 'black_market':
            player['lobsters'].append(_create_lobster('grade2'))

        elif action_type_inner == 'academy':
            if player.get('de', 0) < player.get('wang', 0): player['de'] += 1
            elif player.get('wang', 0) < player.get('de', 0): player['wang'] += 1
            else:
                if option_index == 0: player['de'] += 1
                else: player['wang'] += 1

        elif action_type_inner == 'charity':
            min_de = min(p.get('de', 0) for p in game_state['players'])
            min_wang = min(p.get('wang', 0) for p in game_state['players'])
            for p in game_state['players']:
                if p.get('de', 0) == min_de:
                    p['lobsters'].append(_create_lobster('normal'))
                    p['lobsters'].append(_create_lobster('normal'))
                if p.get('wang', 0) == min_wang: p['coins'] += 2

        elif action_type_inner == 'bazaar':
            player['seaweed'] = player.get('seaweed', 0) + 1
            player['coins'] = player.get('coins', 0) + 1
            player['cages'] = player.get('cages', 0) + 1
            player['lobsters'].append(_create_lobster('normal'))

        elif action_type_inner == 'inn':
            player['inn_headman'] = True

        game_state['settlementState']['waitingForPlayer'] = None
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'

    elif action_type == 'skip':
        game_state['settlementState']['waitingForPlayer'] = None
        game_state['settlementState']['remainingActions'] = 0
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    return 'error'


async def _process_tribute_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', 0)

    if action_type == 'submitTribute':
        is_naked = action_payload.get('isNaked', False)
        tavern_id = action_payload.get('tavernId')
        card_id = action_payload.get('cardId')
        naked_lobster_index = action_payload.get('nakedLobsterIndex', -1)
        naked_reward_type = action_payload.get('nakedRewardType', 'de')

        taverns = game_state.get('taverns', [])
        if tavern_id >= len(taverns): return 'error'
        tavern = taverns[tavern_id]

        if is_naked:
            if player.get('tavernCompletions', {}).get(tavern_id) is not None: return 'error'
            player_lobsters = player.get('lobsters', [])
            player_title_cards = player.get('titleCards', [])

            if naked_lobster_index < 0: return 'error'
            lobster = None
            if naked_lobster_index < len(player_lobsters):
                lobster = player_lobsters[naked_lobster_index]
            else:
                tc_index = naked_lobster_index - len(player_lobsters)
                if tc_index < 0 or tc_index >= len(player_title_cards): return 'error'
                lobster = player_title_cards[tc_index]

            if GRADE_VALUES.get(lobster.get('grade', 'normal'), 0) < 1 and not lobster.get('name'): return 'error'

            if naked_lobster_index < len(player_lobsters): del player_lobsters[naked_lobster_index]
            else:
                tc_index = naked_lobster_index - len(player_lobsters)
                del player_title_cards[tc_index]

            if naked_reward_type == 'de':
                player['de'] += 1
                if lobster.get('title') or lobster.get('name'): player['de'] += 1
                if action_payload.get('bonusTributeChoice') == 'de': player['de'] += 1
            else:
                player['wang'] += 1
                if lobster.get('title') or lobster.get('name'): player['wang'] += 1
                if action_payload.get('bonusTributeChoice') == 'wang': player['wang'] += 1

            if player['id'] not in tavern['occupants']: tavern['occupants'].append(player['id'])
            if 'tavernCompletionOrder' not in game_state: game_state['tavernCompletionOrder'] = {}
            tavern_id_str = str(tavern_id)
            if tavern_id_str not in game_state['tavernCompletionOrder']: game_state['tavernCompletionOrder'][tavern_id_str] = []
            game_state['tavernCompletionOrder'][tavern_id_str].append(player['id'])
            order = len(game_state['tavernCompletionOrder'][tavern_id_str])

            if 'tavernCompletions' not in player: player['tavernCompletions'] = {}
            player['tavernCompletions'][tavern_id] = order
            player['tributesThisRound'] = player.get('tributesThisRound', 0) + 1

        else:
            card_ids = action_payload.get('cardIds', [])
            if not card_ids and not card_id: return 'error'
            if card_id and not card_ids: card_ids = [card_id]

            cards_to_process = []
            for cid in card_ids:
                card = None
                card_index = -1
                for idx, c in enumerate(tavern['cards']):
                    if c.get('id') == cid:
                        card = c
                        card_index = idx
                        break
                if not card: return 'error'
                cards_to_process.append((card, card_index))

            total_coins = sum(c.get('requirements', {}).get('coins', 0) for c, _ in cards_to_process)
            total_seaweed = sum(c.get('requirements', {}).get('seaweed', 0) for c, _ in cards_to_process)
            total_cages = sum(c.get('requirements', {}).get('cages', 0) for c, _ in cards_to_process)

            tribute_discount = check_tribute_discount(player)
            if tribute_discount:
                if tribute_discount.get('coinDiscount'): total_coins = max(0, total_coins - tribute_discount['coinDiscount'])

            all_lobster_reqs = {}
            for card, _ in cards_to_process:
                lr = card.get('requirements', {}).get('lobsters', {})
                for grade, count in lr.items():
                    all_lobster_reqs[grade] = all_lobster_reqs.get(grade, 0) + count

            if tribute_discount and tribute_discount.get('lobsterDiscount'):
                if 'normal' in all_lobster_reqs and all_lobster_reqs['normal'] > 0:
                    all_lobster_reqs['normal'] = max(0, all_lobster_reqs['normal'] - tribute_discount['lobsterDiscount'])

            if player.get('coins', 0) < total_coins: return 'error'
            if player.get('seaweed', 0) < total_seaweed: return 'error'
            if player.get('cages', 0) < total_cages: return 'error'

            selected_lobster_ids = action_payload.get('selectedLobsterIds', [])
            if all_lobster_reqs:
                if not selected_lobster_ids or len(selected_lobster_ids) == 0: return 'error'
                grade_values = {'normal': 0, 'grade3': 1, 'grade2': 2, 'grade1': 3, 'royal': 4}
                player_lobsters = player.get('lobsters', [])
                player_title_cards = player.get('titleCards', [])

                selected_items = []
                for lid in selected_lobster_ids:
                    lobster = next((l for l in player_lobsters if l.get('id') == lid), None)
                    if lobster:
                        selected_items.append(('lobster', lobster))
                        continue
                    tc = next((t for t in player_title_cards if t.get('id') == lid), None)
                    if tc:
                        selected_items.append(('titleCard', tc))
                        continue
                    return 'error'

                def get_lobster_value(item):
                    kind, obj = item
                    if kind == 'titleCard': return 4
                    if obj.get('title'): return 4
                    return grade_values.get(obj.get('grade', 'normal'), 0)

                req_by_grade = []
                for grade_key, count in all_lobster_reqs.items():
                    req_val = grade_values.get(grade_key, 0)
                    req_by_grade.append((req_val, count))
                req_by_grade.sort(key=lambda x: x[0], reverse=True)

                used_indices = set()
                for req_val, count in req_by_grade:
                    matched = 0
                    candidates = []
                    for idx, item in enumerate(selected_items):
                        if idx not in used_indices and get_lobster_value(item) >= req_val:
                            candidates.append((get_lobster_value(item), idx))
                    candidates.sort(key=lambda x: x[0])
                    for _, idx in candidates[:count]:
                        used_indices.add(idx)
                        matched += 1
                    if matched < count: return 'error'

                for lid in selected_lobster_ids:
                    for i, lobster in enumerate(player_lobsters):
                        if lobster.get('id') == lid:
                            del player_lobsters[i]
                            break
                    else:
                        for i, tc in enumerate(player_title_cards):
                            if tc.get('id') == lid:
                                del player_title_cards[i]
                                break

            player['coins'] = player.get('coins', 0) - total_coins
            player['seaweed'] = player.get('seaweed', 0) - total_seaweed
            player['cages'] = player.get('cages', 0) - total_cages

            sorted_indices = sorted([ci for _, ci in cards_to_process], reverse=True)
            for ci in sorted_indices: del tavern['cards'][ci]

            for card, _ in cards_to_process:
                reward = card.get('reward', {})
                player['de'] = player.get('de', 0) + reward.get('de', 0)
                player['wang'] = player.get('wang', 0) + reward.get('wang', 0)

                from services.tribute_card_effects import apply_instant_effect
                instant_result = apply_instant_effect(player, card, game_state)

                if instant_result.get('needChoice'):
                    from utils.events import ServerEvents, ServerGameActionTypes
                    from utils.helpers import make_action_message
                    game_state['pendingTributeChoice'] = {
                        'playerId': player['id'], 'taskId': card.get('id'),
                        'choiceType': instant_result.get('choiceType'), 'options': instant_result.get('options')
                    }
                    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
                        make_action_message(ServerGameActionTypes.TRIBUTE_CHOICE_REQUIRED, {
                            'choiceType': instant_result.get('choiceType'), 'taskId': card.get('id'),
                            'playerId': player['id'], 'options': instant_result.get('options')
                        }))
                    return 'waiting_choice'

                if 'tributeCards' not in player: player['tributeCards'] = []
                player['tributeCards'].append(card)

                aura_result = apply_aura_effect(player, card)
                if aura_result:
                    if 'permaBuffs' not in player: player['permaBuffs'] = []
                    for buff_key in aura_result:
                        if aura_result[buff_key] and buff_key not in player['permaBuffs']:
                            player['permaBuffs'].append(buff_key)

            if action_payload.get('bonusTributeChoice') == 'de': player['de'] = player.get('de', 0) + 1
            elif action_payload.get('bonusTributeChoice') == 'wang': player['wang'] = player.get('wang', 0) + 1

            if player['id'] not in tavern['occupants'] and len(tavern['occupants']) < 4:
                tavern['occupants'].append(player['id'])

            if 'tavernCompletionOrder' not in game_state: game_state['tavernCompletionOrder'] = {}
            tavern_id_str = str(tavern_id)
            if tavern_id_str not in game_state['tavernCompletionOrder']: game_state['tavernCompletionOrder'][tavern_id_str] = []
            game_state['tavernCompletionOrder'][tavern_id_str].append(player['id'])
            order = len(game_state['tavernCompletionOrder'][tavern_id_str])

            if 'tavernCompletions' not in player: player['tavernCompletions'] = {}
            player['tavernCompletions'][tavern_id] = order
            player['tributesThisRound'] = player.get('tributesThisRound', 0) + len(cards_to_process)

        remaining = game_state['settlementState'].get('remainingActions', 1)
        if remaining > 1:
            game_state['settlementState']['remainingActions'] = remaining - 1
            player_slots = game_state['settlementState'].get('playerSlots', [])
            if player_slots: game_state['settlementState']['currentSlotIndex'] = player_slots[0]
        else:
            current_slot_index = game_state['settlementState'].get('currentSlotIndex', 0)
            game_state['settlementState']['currentSlotIndex'] = current_slot_index + 1
            game_state['settlementState']['waitingForPlayer'] = None
        return 'action_complete'

    elif action_type == 'skip':
        remaining = game_state['settlementState'].get('remainingActions', 1)
        if remaining > 1:
            game_state['settlementState']['remainingActions'] = remaining - 1
            player_slots = game_state['settlementState'].get('playerSlots', [])
            if player_slots: game_state['settlementState']['currentSlotIndex'] = player_slots[0]
        else:
            current_slot_index = game_state['settlementState'].get('currentSlotIndex', 0)
            game_state['settlementState']['currentSlotIndex'] = current_slot_index + 1
            game_state['settlementState']['waitingForPlayer'] = None
        return 'action_complete'
    return 'error'


def _serialize_player(player: dict) -> dict:
    """序列化玩家数据用于前端传输"""
    return {
        'id': player['id'],
        'name': player['name'],
        'coins': player['coins'],
        'seaweed': player['seaweed'],
        'cages': player['cages'],
        'de': player['de'],
        'wang': player['wang'],
        'lobsters': player['lobsters'],
        'titleCards': player['titleCards'],
        'tributeCards': player.get('tributeCards', []),
        'tempBubbles': player.get('tempBubbles', 0),
        'tavernCompletions': player.get('tavernCompletions', {}),
        'hiredLaborersBonus': player.get('hiredLaborersBonus', [])
    }