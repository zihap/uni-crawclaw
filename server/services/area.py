# -*- coding: utf-8 -*-
"""
区域结算服务模块
"""

import json
import random
from utils.constants import FISHING_BAG_ITEMS, SLOT_TEMPLATES, MARKET_PRICES, CHALLENGE_SLOT_DONE, GRADE_VALUES
from utils.events import ServerEvents, ServerAreaActionTypes, ServerBattleActionTypes
from utils.logger import log_info, log_debug
from utils.helpers import send_error, make_action_message, create_lobster as _make_lobster, calculate_market_prices, make_settlement_state


def _create_lobster(grade='normal'):
    """创建一只龙虾对象（保留别名以兼容内部调用）"""
    return _make_lobster(grade)


def draw_from_bag() -> str:
    """从捕虾盲袋中抽取一个指示物"""
    total_weight = sum(item['weight'] for item in FISHING_BAG_ITEMS)
    rand = random.random() * total_weight

    for item in FISHING_BAG_ITEMS:
        rand -= item['weight']
        if rand <= 0:
            return item['type']

    return FISHING_BAG_ITEMS[0]['type']


# =============================================================================
# 异步逐步结算系统（新）
# =============================================================================

async def resolve_area_step(game_state: dict, area_index: int, manager, room_id):
    """
    根据区域索引结算对应区域（异步版本，支持UI交互）
    
    返回:
        'auto_next' - 自动进入下一区域（无需UI交互）
        'waiting_ui' - 等待前端UI交互
    """
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

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', -1)

    if current_slot_index == -1:
        current_slot_index = 0

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is None:
            current_slot_index += 1
            continue

        player = game_state['players'][player_id]
        template = templates[current_slot_index]
        action_count = template['actionCount']
        reward = template['reward']

        # 强制从模板读取 actionCount，确保正确
        remaining_actions = action_count

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
            'reward': reward,
            'rewardGiven': reward_given
        }))

        return 'waiting_ui'

    remaining_lobsters = area_data.get('wildLobsterPool', 0)
    if remaining_lobsters > 0:
        market_area = game_state['areas']['seafood_market']
        market_area['marketLobsterCount'] += remaining_lobsters
        if market_area['marketLobsterCount'] > 8:
            market_area['marketLobsterCount'] = 8
        area_data['wildLobsterPool'] = 0

    return 'auto_next'


async def _resolve_seafood_market_step(game_state: dict, manager, room_id):
    """
    结算海鲜市场（需要UI交互）
    遍历有玩家的slot，对每个玩家发送AREA_WAITING_UI事件等待交互
    """
    area_data = game_state['areas']['seafood_market']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['seafood_market']

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', -1)

    if current_slot_index == -1:
        current_slot_index = 0

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is not None:
            player = game_state['players'][player_id]
            template = templates[current_slot_index]
            action_count = template['actionCount']
            reward = template['reward']

            if reward.get('coins'):
                player['coins'] += reward['coins']

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
    """
    结算养蛊区（需要UI交互）
    """
    area_data = game_state['areas']['breeding']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['breeding']

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', -1)

    if current_slot_index == -1:
        current_slot_index = 0

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is not None:
            player = game_state['players'][player_id]

            if len(player['lobsters']) == 0:
                current_slot_index += 1
                continue

            # 从模板读取 actionCount 和 reward
            template = templates[current_slot_index]
            action_count = template['actionCount'] if template else 1
            reward = template.get('reward', {})

            # 发放奖励
            if reward.get('seaweed'):
                player['seaweed'] = player.get('seaweed', 0) + reward['seaweed']
            if reward.get('coins'):
                player['coins'] = player.get('coins', 0) + reward['coins']

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
    """结算上供区（需要UI交互进行战斗和上供）"""
    area_data = game_state['areas']['tribute']
    slots = area_data['slots']

    # 只在首次初始化计数器，避免重入时清零导致计数丢失
    if 'tributeBattlesCompleted' not in game_state:
        game_state['tributeBattlesCompleted'] = 0

    # 只在队列为空时重建，避免重入时 battles 仍在进行中导致队列不一致
    if not game_state.get('battleQueue'):
        game_state['battleQueue'] = []

        tribute = game_state['areas'].get('tribute')
        challenge_slots_battle_status = tribute.get('challengeSlots', [])

        for challenge_idx in range(3, 6):
            defender_idx = challenge_idx - 3
            challenger_id = slots[challenge_idx]
            defender_id = slots[defender_idx]

            if challenger_id is not None and defender_id is not None and challenge_slots_battle_status[defender_idx] != CHALLENGE_SLOT_DONE:
                game_state['battleQueue'].append({
                    'challengerId': challenger_id,
                    'defenderId': defender_id,
                    'challengeSlot': challenge_idx,
                    'defenderSlot': defender_idx
                })
                log_info(f"[tribute] Battle queued: player {challenger_id} (slot {challenge_idx}) vs player {defender_id} (slot {defender_idx})")
    else:
        log_debug("[_resolve_tribute_step] battleQueue 已存在，跳过重建")

    if len(game_state['battleQueue']) > 0:
        current_battle_key = json.dumps(game_state['battleQueue'], sort_keys=True)
        last_battle_start = game_state.get('_lastBattleStartSent')

        if last_battle_start == current_battle_key:
            log_debug("[_resolve_tribute_step] 跳过重复的 battleStart 消息")
            game_state['settlementState'] = make_settlement_state('tribute')
            return 'waiting_ui'

        game_state['_lastBattleStartSent'] = current_battle_key

        game_state['settlementState'] = make_settlement_state('tribute')

        await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
            make_action_message(ServerBattleActionTypes.BATTLE_START, {
                'battleQueue': game_state['battleQueue']
            }))

        return 'waiting_ui'

    return await _resolve_tribute_actions(game_state, manager, room_id)


async def _resolve_tribute_actions(game_state: dict, manager, room_id):
    """处理上供区上供行动（8个slot，依次上供）"""
    area_data = game_state['areas']['tribute']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['tribute']

    log_info(f"[_resolve_tribute_actions] ENTRY - tribute slots: {slots}")

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
    """
    结算闹市区（需要UI交互）
    """
    area_data = game_state['areas']['marketplace']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['marketplace']
    current_round = game_state.get('currentRound', 1)

    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', -1)

    if current_slot_index == -1:
        current_slot_index = 0

    while current_slot_index < len(slots):
        player_id = slots[current_slot_index]
        if player_id is not None:
            player = game_state['players'][player_id]

            available_cards = [
                card for card in game_state.get('downtownCards', [])
                if not card.get('usedThisRound', False)
            ]

            if len(available_cards) == 0:
                current_slot_index += 1
                continue

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
    """
    处理结算阶段的前端交互操作
    
    返回:
        'action_complete' - 当前区域所有行动完成
        'continue_ui' - 继续等待UI交互（同一玩家还有行动）
        'error' - 操作失败
    """

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
    """处理捕虾区玩家选择行动"""
    settlement_state = game_state.get('settlementState', {})
    remaining_actions = settlement_state.get('remainingActions', 0)
    current_slot_index = settlement_state.get('currentSlotIndex', 0)
    templates = SLOT_TEMPLATES['shrimp_catching']
    template = templates[current_slot_index]
    reward_given = settlement_state.get('rewardGiven', False)
    step = settlement_state.get('step', 'waiting_confirm')

    if action_type == 'confirm':
        # 玩家确认继续捕虾，抽取指示物
        if step != 'waiting_confirm':
            await send_error(websocket, '当前状态不允许确认')
            return 'error'
        if remaining_actions <= 0:
            await send_error(websocket, '没有剩余行动次数')
            return 'error'

        item = draw_from_bag()
        log_debug(f"[shrimp_catching] draw_from_bag result: {item}, remaining_actions: {remaining_actions}")
        result_msg = ''

        if item == 'either':
            # 需要玩家选择
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
            player['lobsters'].append(_create_lobster('normal'))
            result_msg = '获得1只野生龙虾'
        elif item == 'seaweed':
            player['seaweed'] += 1
            result_msg = '获得1根海草'

        # 处理首次奖励
        if not reward_given:
            reward = template.get('reward', {})
            if reward.get('cages'):
                player['cages'] += reward['cages']
            if reward.get('coins'):
                player['coins'] += reward['coins']
            if reward.get('stealStart'):
                game_state['startingPlayerIndex'] = settlement_state.get('waitingForPlayer')
                for p in game_state['players']:
                    p['isStartingPlayer'] = False
                player['isStartingPlayer'] = True
            reward_given = True

        remaining_actions -= 1

        if remaining_actions <= 0:
            game_state['settlementState']['waitingForPlayer'] = None
            game_state['settlementState']['step'] = 'done'
            game_state['settlementState']['lastResult'] = result_msg
            game_state['settlementState']['lastItem'] = item
            # 增加 slot 索引，继续下一个玩家
            game_state['settlementState']['currentSlotIndex'] = current_slot_index + 1
            # 广播最后一次结果给前端悬浮提示展示
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
            log_debug(f"[confirm] action_complete, moved to slot {current_slot_index + 1}")
            return 'action_complete'
        else:
            log_debug(f"[confirm] continue with {remaining_actions} actions")
            # 继续下一次，暂停等待确认
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
        log_debug(f"[choose_either] remaining_actions before: {remaining_actions}")
        if choice not in ('lobster', 'seaweed'):
            await send_error(websocket, '无效的选择')
            return 'error'

        result_msg = ''
        if choice == 'lobster':
            player['lobsters'].append(_create_lobster('normal'))
            result_msg = '获得1只野生龙虾'
        elif choice == 'seaweed':
            player['seaweed'] += 1
            result_msg = '获得1根海草'

        if not reward_given:
            reward = template.get('reward', {})
            if reward.get('cages'):
                player['cages'] += reward['cages']
            if reward.get('coins'):
                player['coins'] += reward['coins']
            if reward.get('stealStart'):
                game_state['startingPlayerIndex'] = settlement_state.get('waitingForPlayer')
                for p in game_state['players']:
                    p['isStartingPlayer'] = False
                player['isStartingPlayer'] = True
            reward_given = True

        remaining_actions -= 1

        if remaining_actions <= 0:
            game_state['settlementState']['waitingForPlayer'] = None
            game_state['settlementState']['step'] = 'done'
            # 增加 slot 索引，继续下一个玩家
            game_state['settlementState']['currentSlotIndex'] = current_slot_index + 1
            log_debug(f"[choose_either] action_complete, moved to slot {current_slot_index + 1}")
            return 'action_complete'
        else:
            log_debug(f"[choose_either] continue with {remaining_actions} actions")
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
        # 增加 slot 索引，继续下一个玩家
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    else:
        await send_error(websocket, '未知操作类型')
        return 'error'


async def _process_seafood_market_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    """处理海鲜市场单次交易行动"""
    settlement_state = game_state.get('settlementState', {})
    remaining_actions = settlement_state.get('remainingActions', 0)

    if remaining_actions <= 0:
        await send_error(websocket, '没有剩余行动次数')
        return 'error'

    area_data = game_state['areas']['seafood_market']
    prices = calculate_market_prices(area_data['marketLobsterCount'])

    success = False

    if action_type == 'buy_lobster':
        if player['coins'] >= prices['buyLobster'] and area_data['marketLobsterCount'] > 0:
            player['coins'] -= prices['buyLobster']
            area_data['marketLobsterCount'] -= 1
            player['lobsters'].append(_create_lobster('normal'))
            success = True
        else:
            await send_error(websocket, '金币不足或市场无龙虾')
    elif action_type == 'sell_lobster':
        if len(player['lobsters']) > 0:
            player['lobsters'].pop(0)
            player['coins'] += prices['sellLobster']
            area_data['marketLobsterCount'] += 1
            if area_data['marketLobsterCount'] > 8:
                area_data['marketLobsterCount'] = 8
            success = True
        else:
            await send_error(websocket, '没有龙虾可卖')
    elif action_type == 'buy_cage':
        if player['coins'] >= prices['buyCage']:
            player['coins'] -= prices['buyCage']
            player['cages'] += 1
            success = True
        else:
            await send_error(websocket, '金币不足')
    elif action_type == 'sell_cage':
        if player['cages'] > 0:
            player['cages'] -= 1
            player['coins'] += prices['sellCage']
            success = True
        else:
            await send_error(websocket, '没有虾笼可卖')
    elif action_type == 'buy_seaweed':
        if player['coins'] >= prices['buySeaweed']:
            player['coins'] -= prices['buySeaweed']
            player['seaweed'] += 1
            success = True
        else:
            await send_error(websocket, '金币不足')
    elif action_type == 'sell_seaweed':
        if player['seaweed'] > 0:
            player['seaweed'] -= 1
            player['coins'] += prices['sellSeaweed']
            success = True
        else:
            await send_error(websocket, '没有海草可卖')
    elif action_type == 'hire':
        if player['coins'] >= prices['hireHeadman']:
            player['coins'] -= prices['hireHeadman']
            if 'hiredLaborersBonus' not in player:
                player['hiredLaborersBonus'] = []
            player['hiredLaborersBonus'].append(settlement_state.get('currentSlotIndex'))
            success = True
        else:
            await send_error(websocket, '金币不足')
    elif action_type == 'skip':
        game_state['settlementState']['waitingForPlayer'] = None
        game_state['settlementState']['remainingActions'] = 0
        # 增加 slot 索引，继续下一个玩家
        current_idx = settlement_state.get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    else:
        await send_error(websocket, '未知操作类型')
        return 'error'

    if not success:
        return 'error'

    remaining_actions -= 1
    game_state['settlementState']['remainingActions'] = remaining_actions

    if remaining_actions <= 0:
        game_state['settlementState']['waitingForPlayer'] = None
        # 增加 slot 索引，继续下一个玩家
        current_idx = settlement_state.get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    else:
        log_info(f"[Seafood Market] Sending AREA_WAITING_UI with actionCount={remaining_actions}")
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
    """处理养蛊区单次培养行动"""
    settlement_state = game_state.get('settlementState', {})
    remaining_actions = settlement_state.get('remainingActions', 0)

    if remaining_actions <= 0:
        await send_error(websocket, '没有剩余行动次数')
        return 'error'

    if action_type == 'cultivateLobster':
        lobster_index = action_payload.get('lobsterIndex')
        use_seaweed = action_payload.get('useSeaweed', False)
        if lobster_index is None or lobster_index >= len(player['lobsters']):
            await send_error(websocket, '无效的龙虾选择')
            return 'error'

        lobster = player['lobsters'][lobster_index]
        old_grade = lobster['grade']

        if use_seaweed and player.get('seaweed', 0) >= 1:
            player['seaweed'] -= 1
            if old_grade == 'normal':
                lobster['grade'] = 'grade2'
            elif old_grade == 'grade3':
                lobster['grade'] = 'grade1'
            elif old_grade == 'grade2':
                if player['cages'] > 0:
                    player['cages'] -= 1
                    lobster['grade'] = 'royal'
                elif player['coins'] >= 3:
                    player['coins'] -= 3
                    lobster['grade'] = 'royal'
                else:
                    await send_error(websocket, '需要虾笼或3金币')
                    return 'error'
            else:
                await send_error(websocket, '当前品级无法使用海草升级')
                return 'error'
        elif use_seaweed:
            await send_error(websocket, '海草数量不足')
            return 'error'
        else:
            if old_grade == 'normal':
                lobster['grade'] = 'grade3'
            elif old_grade == 'grade3':
                lobster['grade'] = 'grade2'
            elif old_grade == 'grade2':
                if player['cages'] > 0:
                    player['cages'] -= 1
                    lobster['grade'] = 'grade1'
                elif player['coins'] >= 3:
                    player['coins'] -= 3
                    lobster['grade'] = 'grade1'
                else:
                    await send_error(websocket, '需要虾笼或3金币')
                    return 'error'
            elif old_grade == 'grade1':
                if player['cages'] > 0:
                    player['cages'] -= 1
                    lobster['grade'] = 'royal'
                elif player['coins'] >= 3:
                    player['coins'] -= 3
                    lobster['grade'] = 'royal'
                else:
                    await send_error(websocket, '需要虾笼或3金币')
                    return 'error'

        remaining_actions -= 1
        game_state['settlementState']['remainingActions'] = remaining_actions

        if remaining_actions <= 0:
            game_state['settlementState']['waitingForPlayer'] = None
            # 增加 currentSlotIndex 以继续下一个玩家
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
        game_state['settlementState']['waitingForPlayer'] = None
        game_state['settlementState']['remainingActions'] = 0
        # 增加 slot 索引，继续下一个玩家
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        log_debug(f"[breeding skip] action_complete, moved to slot {current_idx + 1}")
        return 'action_complete'
    else:
        await send_error(websocket, '未知操作类型')
        return 'error'


async def _process_marketplace_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    """处理闹市区单次闹市卡行动"""
    settlement_state = game_state.get('settlementState', {})

    if action_type == 'executeDowntownAction':
        card_index = action_payload.get('cardIndex')
        option_index = action_payload.get('optionIndex', 0)

        available_cards = [
            card for card in game_state.get('downtownCards', [])
            if not card.get('usedThisRound', False)
        ]

        if card_index is None or card_index >= len(available_cards):
            await send_error(websocket, '无效的卡牌选择')
            return 'error'

        card = available_cards[card_index]
        card['usedThisRound'] = True

        action = card.get('action', {})
        action_type_inner = action.get('type')

        if action_type_inner == 'exchange':
            options = action.get('options', [])
            if option_index >= len(options):
                await send_error(websocket, '无效的选项')
                return 'error'

            option = options[option_index]
            cost = option.get('cost', {})
            reward = option.get('reward', {})

            for res_type, res_amount in cost.items():
                if res_type == 'lobsters':
                    if len(player['lobsters']) < res_amount:
                        await send_error(websocket, '龙虾不足')
                        return 'error'
                    for _ in range(res_amount):
                        player['lobsters'].pop(0)
                elif res_type == 'de':
                    if player['de'] < res_amount:
                        await send_error(websocket, '德不足')
                        return 'error'
                    player['de'] -= res_amount
                elif res_type == 'wang':
                    if player['wang'] < res_amount:
                        await send_error(websocket, '望不足')
                        return 'error'
                    player['wang'] -= res_amount
                elif res_type == 'coins':
                    if player['coins'] < res_amount:
                        await send_error(websocket, '金币不足')
                        return 'error'
                    player['coins'] -= res_amount
                elif res_type == 'seaweed':
                    if player['seaweed'] < res_amount:
                        await send_error(websocket, '海草不足')
                        return 'error'
                    player['seaweed'] -= res_amount
                elif res_type == 'cages':
                    if player['cages'] < res_amount:
                        await send_error(websocket, '虾笼不足')
                        return 'error'
                    player['cages'] -= res_amount

            for res_type, res_amount in reward.items():
                if res_type == 'lobsters':
                    for _ in range(res_amount):
                        player['lobsters'].append(_create_lobster('normal'))
                elif res_type == 'de':
                    player['de'] += res_amount
                elif res_type == 'wang':
                    player['wang'] += res_amount
                elif res_type == 'coins':
                    player['coins'] += res_amount
                elif res_type == 'seaweed':
                    player['seaweed'] += res_amount
                elif res_type == 'cages':
                    player['cages'] += res_amount

        elif action_type_inner == 'academy':
            if player['de'] < player['wang']:
                player['de'] += 1
            else:
                player['wang'] += 1

        elif action_type_inner == 'charity':
            min_de = min(p['de'] for p in game_state['players'])
            min_wang = min(p['wang'] for p in game_state['players'])

            for p in game_state['players']:
                if p['de'] == min_de:
                    lost = min(2, len(p['lobsters']))
                    for _ in range(lost):
                        p['lobsters'].pop(0)
                if p['wang'] == min_wang:
                    lost = min(2, len(p['lobsters']))
                    for _ in range(lost):
                        p['lobsters'].pop(0)

        game_state['settlementState']['waitingForPlayer'] = None
        # 增加 slot 索引，继续下一个玩家
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'

    elif action_type == 'skip':
        game_state['settlementState']['waitingForPlayer'] = None
        game_state['settlementState']['remainingActions'] = 0
        # 增加 slot 索引，继续下一个玩家
        current_idx = game_state['settlementState'].get('currentSlotIndex', 0)
        game_state['settlementState']['currentSlotIndex'] = current_idx + 1
        return 'action_complete'
    else:
        await send_error(websocket, '未知操作类型')
        return 'error'


async def _process_tribute_action(game_state: dict, action_type: str, action_payload: dict, player: dict, manager, room_id, websocket):
    """处理上供区上供行动"""
    settlement_state = game_state.get('settlementState', {})
    current_slot_index = settlement_state.get('currentSlotIndex', 0)

    if action_type == 'submitTribute':
        is_naked = action_payload.get('isNaked', False)
        tavern_id = action_payload.get('tavernId')
        card_id = action_payload.get('cardId')
        naked_lobster_index = action_payload.get('nakedLobsterIndex', -1)
        naked_reward_type = action_payload.get('nakedRewardType', 'de')

        taverns = game_state.get('taverns', [])
        if tavern_id >= len(taverns):
            await send_error(websocket, '无效的酒楼选择')
            return 'error'

        tavern = taverns[tavern_id]

        if is_naked:
            if naked_lobster_index < 0 or naked_lobster_index >= len(player['lobsters']):
                await send_error(websocket, '无效的龙虾选择')
                return 'error'

            lobster = player['lobsters'][naked_lobster_index]
            if GRADE_VALUES.get(lobster.get('grade', 'normal'), 0) < 1:
                await send_error(websocket, '裸交需要献祭3品及以上的龙虾')
                return 'error'

            del player['lobsters'][naked_lobster_index]

            if naked_reward_type == 'de':
                player['de'] += 1
                if lobster.get('title'):
                    player['de'] += 1
            else:
                player['wang'] += 1
                if lobster.get('title'):
                    player['wang'] += 1

            if player['id'] not in tavern['occupants']:
                tavern['occupants'].append(player['id'])

        else:
            if not card_id:
                await send_error(websocket, '请选择上供卡牌')
                return 'error'

            card = None
            card_index = -1
            for idx, c in enumerate(tavern['cards']):
                if c.get('id') == card_id:
                    card = c
                    card_index = idx
                    break

            if not card:
                await send_error(websocket, '无效的卡牌选择')
                return 'error'

            requirements = card.get('requirements', {})
            if requirements.get('coins', 0) > player.get('coins', 0):
                await send_error(websocket, '金币不足')
                return 'error'
            if requirements.get('seaweed', 0) > player.get('seaweed', 0):
                await send_error(websocket, '海草不足')
                return 'error'
            if requirements.get('cages', 0) > player.get('cages', 0):
                await send_error(websocket, '虾笼不足')
                return 'error'

            player['coins'] = player.get('coins', 0) - requirements.get('coins', 0)
            player['seaweed'] = player.get('seaweed', 0) - requirements.get('seaweed', 0)
            player['cages'] = player.get('cages', 0) - requirements.get('cages', 0)

            del tavern['cards'][card_index]

            reward = card.get('reward', {})
            player['de'] = player.get('de', 0) + reward.get('de', 0)
            player['wang'] = player.get('wang', 0) + reward.get('wang', 0)

            effect_type = card.get('effectType')
            if effect_type == 'instant_upgrade_all':
                for l in player.get('lobsters', []):
                    if l.get('grade') != 'royal':
                        if l.get('grade') == 'normal':
                            l['grade'] = 'grade3'
                        elif l.get('grade') == 'grade3':
                            l['grade'] = 'grade2'
                        elif l.get('grade') == 'grade2':
                            l['grade'] = 'grade1'
                        elif l.get('grade') == 'grade1':
                            l['grade'] = 'royal'
            elif effect_type == 'instant_gain_cages':
                player['cages'] = player.get('cages', 0) + 2

            if player['id'] not in tavern['occupants'] and len(tavern['occupants']) < 4:
                tavern['occupants'].append(player['id'])

        remaining = game_state['settlementState'].get('remainingActions', 1)
        if remaining > 1:
            game_state['settlementState']['remainingActions'] = remaining - 1
            player_slots = game_state['settlementState'].get('playerSlots', [])
            if player_slots:
                game_state['settlementState']['currentSlotIndex'] = player_slots[0]
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
            if player_slots:
                game_state['settlementState']['currentSlotIndex'] = player_slots[0]
        else:
            current_slot_index = game_state['settlementState'].get('currentSlotIndex', 0)
            game_state['settlementState']['currentSlotIndex'] = current_slot_index + 1
            game_state['settlementState']['waitingForPlayer'] = None
        return 'action_complete'
    else:
        await send_error(websocket, '未知操作类型')
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
        'tempBubbles': player.get('tempBubbles', 0),
    }
