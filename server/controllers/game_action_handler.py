# -*- coding: utf-8 -*-
"""
游戏行动路由器
将客户端发送的 clientGameAction 事件按 actionType 分发到具体 handler

包含的事件:
  - USE_SEAWEED: 使用海草
  - PLACE_HEADMAN: 放置里长
  - NEXT_PLAYER: 下一个玩家
  - NEXT_AREA: 下一个区域
  - EXCHANGE_SIGNALS: 交换信号
  - BUY_ITEM: 购买物品
  - SELL_ITEM: 出售物品
  - CULTIVATE_LOBSTER: 培养龙虾
  - SUBMIT_TRIBUTE: 提交上供
  - DOWNTOWN_ACTION: 闹市行动
  - AREA_ACTION: 区域行动
"""

from utils.constants import AREAS
from utils.events import ClientGameActionTypes, ServerEvents, ServerGameActionTypes, ServerAreaActionTypes
from utils.helpers import send_error, has_resources, update_resources, get_player, make_action_message, make_broadcast_fn, make_settlement_state
from utils.logger import log_info, log_debug
from services.game import broadcast_game_state, start_area_settlement, complete_settlement
from services.area import resolve_area_step, process_area_action
from services.tribute_card_effects import apply_instant_effect, apply_aura_effect, get_endgame_choices, apply_endgame_choice


async def handle_use_seaweed(websocket, room_id, player_id, rooms, manager, payload):
    """使用海草"""
    game_state = rooms.get(room_id)
    if not game_state:
        return
    player = get_player(game_state, player_id)
    if not player or player['seaweed'] <= 0:
        await send_error(websocket, '海草不足')
        return
    await update_resources(player, {'seaweed': -1}, broadcast_fn=make_broadcast_fn(manager.send_to_room, room_id))


async def handle_place_headman(websocket, room_id, player_id, rooms, manager, payload):
    """放置里长"""
    area_index = payload.get('areaIndex')
    slot_index = payload.get('slotIndex')

    game_state = rooms.get(room_id)
    if not game_state or game_state.get('status') != 'playing':
        await send_error(websocket, '游戏未开始')
        return

    if player_id != game_state.get('currentPlayerIndex'):
        await send_error(websocket, '不是你的回合')
        return

    last_placement = game_state.get('lastPlacement')
    if last_placement and last_placement.get('playerId') == player_id:
        await send_error(websocket, '本回合已放置过里长，请点击下一阶段')
        return

    player = game_state['players'][player_id]
    if not player or player['liZhang'] <= 0:
        await send_error(websocket, '没有米宝了')
        return

    area_name = area_index if isinstance(area_index, str) else AREAS[area_index]
    area_data = game_state['areas'].get(area_name)
    if not area_data:
        await send_error(websocket, '区域不存在')
        return

    slots = area_data['slots']
    bf = make_broadcast_fn(manager.send_to_room, room_id)
    if slot_index < 0 or slot_index >= len(slots) or slots[slot_index] is not None:
        await send_error(websocket, '该位置已有米宝')
        return
    await update_resources(player, {'liZhang': -1}, broadcast_fn=bf)
    slots[slot_index] = player_id
    game_state['lastPlacement'] = {
        'playerId': player_id,
        'areaName': area_name,
        'slotIndex': slot_index
    }
    await broadcast_game_state(room_id, rooms, manager)


async def handle_cancel_headman(websocket, room_id, player_id, rooms, manager, payload):
    """取消放置里长"""
    game_state = rooms.get(room_id)
    if not game_state or game_state.get('status') != 'playing':
        await send_error(websocket, '游戏未开始')
        return

    if player_id != game_state.get('currentPlayerIndex'):
        await send_error(websocket, '不是你的回合')
        return

    last = game_state.get('lastPlacement')
    if not last or last['playerId'] != player_id:
        await send_error(websocket, '没有可取消的放置')
        return

    area_name = last['areaName']
    slot_index = last['slotIndex']
    area_data = game_state['areas'].get(area_name)
    if not area_data:
        game_state['lastPlacement'] = None
        await send_error(websocket, '区域数据异常')
        return

    slots = area_data['slots']
    if slot_index < 0 or slot_index >= len(slots) or slots[slot_index] != player_id:
        game_state['lastPlacement'] = None
        await send_error(websocket, '放置位置已变更')
        return

    player = game_state['players'][player_id]
    slots[slot_index] = None
    game_state['lastPlacement'] = None
    bf = make_broadcast_fn(manager.send_to_room, room_id)
    await update_resources(player, {'liZhang': 1}, broadcast_fn=bf)
    await broadcast_game_state(room_id, rooms, manager)


async def handle_next_player(websocket, room_id, player_id, rooms, manager, payload):
    """下一个玩家"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    if player_id != game_state.get('currentPlayerIndex', 0):
        await send_error(websocket, '不是你的回合')
        return

    all_placed = all(p['liZhang'] == 0 for p in game_state['players'])

    if all_placed:
        game_state['phase'] = 'settlement'
        game_state['currentArea'] = 0
        game_state['battleQueue'] = []
        game_state['settlementState'] = make_settlement_state(None, 0, 0)

        await start_area_settlement(websocket, room_id, game_state, rooms, manager)
    else:
        current_idx = game_state.get('currentPlayerIndex', 0)
        game_state['currentPlayerIndex'] = (current_idx + 1) % len(game_state['players'])
        game_state['lastPlacement'] = None

        await broadcast_game_state(room_id, rooms, manager)


async def handle_next_area(websocket, room_id, player_id, rooms, manager, payload):
    """下一个区域"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    if game_state.get('phase') != 'settlement':
        await send_error(websocket, '当前不在结算阶段')
        return

    current_area = game_state.get('currentArea', 0)

    if current_area + 1 >= len(AREAS):
        await complete_settlement(room_id, game_state, rooms, manager)
    else:
        game_state['currentArea'] = current_area + 1
        await start_area_settlement(websocket, room_id, game_state, rooms, manager)


async def handle_area_action(websocket, room_id, player_id, rooms, manager, payload):
    """处理结算阶段的前端交互操作"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    if game_state.get('phase') != 'settlement':
        await send_error(websocket, '当前不在结算阶段')
        return

    settlement_state = game_state.get('settlementState', {})
    if settlement_state.get('waitingForPlayer') != player_id:
        await send_error(websocket, '不是你的操作回合')
        return

    action_type = payload.get('actionType')
    action_payload = payload.get('payload', {})

    result = await process_area_action(game_state, action_type, action_payload, manager, room_id, websocket)
    log_debug(f"[handle_settlement_action] actionType={action_type}, result={result}")

    if result == 'action_complete':
        await broadcast_game_state(room_id, rooms, manager)

        current_area = game_state.get('currentArea', 0)
        area_name = AREAS[current_area]
        
        # 检查当前区域是否还有未处理的玩家/slot
        more_players_in_area = False
        if area_name in game_state['areas']:
            area_data = game_state['areas'][area_name]
            slots = area_data.get('slots', [])
            settlement_state = game_state.get('settlementState', {})
            current_slot_index = settlement_state.get('currentSlotIndex', 0)
            log_debug(f"[handle_settlement_action] area={area_name}, slots={slots}, currentSlotIndex={current_slot_index}")
            
            # 检查是否有更多slot需要处理
            # currentSlotIndex 是下一个要处理的slot索引，从这里开始向后检查
            if current_slot_index >= 0 and current_slot_index < len(slots):
                for idx in range(current_slot_index, len(slots)):
                    if slots[idx] is not None:
                        more_players_in_area = True
                        break
        
        remaining_actions = settlement_state.get('remainingActions', 1)
        player_slots = settlement_state.get('playerSlots', [])
        
        log_debug(f"[handle_settlement_action] more_players_in_area={more_players_in_area}, remainingActions={remaining_actions}, playerSlots={player_slots}, waitingForPlayer={player_id}")
        
        if remaining_actions > 1:
            game_state['settlementState']['remainingActions'] = remaining_actions - 1
            await broadcast_game_state(room_id, rooms, manager)
            player = game_state['players'][player_id]
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                    'areaType': area_name,
                    'playerId': player_id,
                    'actionCount': remaining_actions - 1,
                    'slotIndex': player_slots[0] if player_slots else 0,
                    'player': player,
                    'taverns': game_state.get('taverns', []),
                    'tributeTasks': game_state.get('tributeTasks', [])
                }))
        elif more_players_in_area:
            if player_slots and len(player_slots) > 1:
                game_state['settlementState']['currentSlotIndex'] = player_slots[1]
            game_state['settlementState']['waitingForPlayer'] = None
            game_state['settlementState']['playerSlots'] = []
            await broadcast_game_state(room_id, rooms, manager)
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                    'areaType': area_name,
                    'gameState': game_state
                }))
            await start_area_settlement(websocket, room_id, game_state, rooms, manager)
        elif current_area + 1 >= len(AREAS):
            await complete_settlement(room_id, game_state, rooms, manager)
        else:
            # 跳转到下一个区域前，重置settlementState
            next_area = current_area + 1
            next_area_name = AREAS[next_area]
            log_info(f"[handle_settlement_action] Jumping to next area: {next_area_name}")
            game_state['settlementState'] = make_settlement_state(next_area_name, 0, 0)
            game_state['currentArea'] = next_area
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                    'areaType': next_area_name,
                    'gameState': game_state
                }))
            await start_area_settlement(websocket, room_id, game_state, rooms, manager)
    elif result == 'continue_ui':
        await broadcast_game_state(room_id, rooms, manager)


async def handle_exchange_signals(websocket, room_id, player_id, rooms, manager, payload):
    """交换信号"""
    exchange_type = payload.get('exchangeType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    bf = make_broadcast_fn(manager.send_to_room, room_id)

    if exchange_type == '1to1' and player['tempBubbles'] >= 1:
        player['tempBubbles'] -= 1
        await update_resources(player, {'coins': 1}, broadcast_fn=bf)
    elif exchange_type == '2to3' and player['tempBubbles'] >= 2:
        player['tempBubbles'] -= 2
        await update_resources(player, {'grade3': 1}, broadcast_fn=bf)
    elif exchange_type == '3to2' and player['tempBubbles'] >= 3:
        player['tempBubbles'] -= 3
        await update_resources(player, {'grade2': 1}, broadcast_fn=bf)

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        make_action_message(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'signalsExchanged',
            'playerId': player_id,
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


async def handle_buy_item(websocket, room_id, player_id, rooms, manager, payload):
    """购买物品"""
    item_type = payload.get('itemType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    prices = game_state['areas']['seafood_market']['dynamicPrices']
    bf = make_broadcast_fn(manager.send_to_room, room_id)
    success = False

    if item_type == 'lobster' and player['coins'] >= prices['buyLobster']:
        await update_resources(player, {'coins': -prices['buyLobster'], 'normal': 1}, broadcast_fn=bf)
        success = True
    elif item_type == 'seaweed' and player['coins'] >= prices['buySeaweed']:
        await update_resources(player, {'coins': -prices['buySeaweed'], 'seaweed': 1}, broadcast_fn=bf)
        success = True
    elif item_type == 'cage' and player['coins'] >= prices['buyCage']:
        await update_resources(player, {'coins': -prices['buyCage'], 'cages': 1}, broadcast_fn=bf)
        success = True
    elif item_type == 'headman' and player['coins'] >= prices['hireHeadman']:
        await update_resources(player, {'coins': -prices['hireHeadman'], 'liZhang': 1}, broadcast_fn=bf)
        success = True

    if success:
        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            make_action_message(ServerGameActionTypes.GAME_ACTION, {
                'actionType': 'itemBought',
                'playerId': player_id,
                'data': {'itemType': item_type},
                'gameState': game_state
            }))
        await broadcast_game_state(room_id, rooms, manager)
    else:
        await send_error(websocket, '资源不足')


async def handle_sell_item(websocket, room_id, player_id, rooms, manager, payload):
    """出售物品"""
    item_type = payload.get('itemType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    prices = game_state['areas']['seafood_market']['dynamicPrices']
    bf = make_broadcast_fn(manager.send_to_room, room_id)
    success = False

    if item_type == 'lobster' and has_resources(player, {'normal': 1}):
        await update_resources(player, {'normal': -1, 'coins': prices['sellLobster']}, broadcast_fn=bf)
        success = True
    elif item_type == 'seaweed' and player['seaweed'] > 0:
        await update_resources(player, {'seaweed': -1, 'coins': prices['sellSeaweed']}, broadcast_fn=bf)
        success = True
    elif item_type == 'cage' and player['cages'] > 0:
        await update_resources(player, {'cages': -1, 'coins': prices['sellCage']}, broadcast_fn=bf)
        success = True

    if success:
        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            make_action_message(ServerGameActionTypes.GAME_ACTION, {
                'actionType': 'itemSold',
                'playerId': player_id,
                'data': {'itemType': item_type},
                'gameState': game_state
            }))
        await broadcast_game_state(room_id, rooms, manager)
    else:
        await send_error(websocket, '物品不足')


async def handle_cultivate_lobster(websocket, room_id, player_id, rooms, manager, payload):
    """培养龙虾"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    bf = make_broadcast_fn(manager.send_to_room, room_id)
    upgraded = False

    if has_resources(player, {'grade1': 1}) and (player['cages'] > 0 or player['coins'] >= 3):
        deltas = {'grade1': -1, 'royal': 1}
        if player['cages'] > 0:
            deltas['cages'] = -1
        else:
            deltas['coins'] = -3
        await update_resources(player, deltas, broadcast_fn=bf)
        if player['royalCountThisRound'] < 2:
            player['royalCountThisRound'] += 1
        upgraded = True
    elif has_resources(player, {'grade2': 1}):
        await update_resources(player, {'grade2': -1, 'grade1': 1}, broadcast_fn=bf)
        upgraded = True
    elif has_resources(player, {'grade3': 1}):
        await update_resources(player, {'grade3': -1, 'grade2': 1}, broadcast_fn=bf)
        upgraded = True
    elif has_resources(player, {'normal': 1}):
        await update_resources(player, {'normal': -1, 'grade3': 1}, broadcast_fn=bf)
        upgraded = True

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        make_action_message(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'lobsterCultivated',
            'playerId': player_id,
            'data': {'upgraded': upgraded},
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


async def handle_downtown_action(websocket, room_id, player_id, rooms, manager, payload):
    """闹市行动"""
    card_index = payload.get('cardIndex')
    option_index = payload.get('optionIndex', 0)

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    card = game_state['downtownCards'][card_index] if card_index is not None and card_index < len(game_state['downtownCards']) else None
    if not card:
        await send_error(websocket, '卡牌不存在')
        return

    options = card.get('action', {}).get('options', [])
    if not options or option_index >= len(options):
        await send_error(websocket, '无效的选项')
        return

    selected = options[option_index]
    cost = selected.get('cost', {})
    reward = selected.get('reward', {})

    if not has_resources(player, cost):
        await send_error(websocket, '资源不足')
        return

    bf = make_broadcast_fn(manager.send_to_room, room_id)
    await update_resources(player, {**cost, **reward}, broadcast_fn=bf)

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        make_action_message(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'downtownActionExecuted',
            'playerId': player_id,
            'data': {'card': card},
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


async def handle_endgame_score_choice(websocket, room_id, player_id, rooms, manager, payload):
    """处理终局得分选择"""
    choice = payload.get('choice')
    choice_index = payload.get('choiceIndex')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    if game_state.get('status') != 'waitingEndgameChoice':
        await send_error(websocket, '当前不在终局得分选择阶段')
        return

    waiting_list = game_state.get('waitingForEndgameChoice', [])
    current_index = game_state.get('endgameChoiceIndex', 0)

    if current_index >= len(waiting_list):
        await send_error(websocket, '所有玩家已完成选择')
        return

    current_player = waiting_list[current_index]
    if current_player['playerId'] != player_id:
        await send_error(websocket, '还没轮到你进行选择')
        return

    card = current_player['card']
    player = game_state['players'][player_id]

    if choice:
        apply_endgame_choice(player, card, choice)
    elif choice_index is not None:
        choices = get_endgame_choices(player, card)
        if choice_index < 0 or choice_index >= len(choices):
            await send_error(websocket, '无效的选择')
            return
        apply_endgame_choice(player, card, choices[choice_index])
    else:
        await send_error(websocket, '无效的请求')
        return

    game_state['endgameChoiceIndex'] = current_index + 1

    if game_state['endgameChoiceIndex'] >= len(waiting_list):
        game_state['waitingForEndgameChoice'] = None
        game_state['status'] = 'ended'

        winner = sorted(
            game_state['players'],
            key=lambda x: (x.get('de', 0) * x.get('wang', 0) + x.get('bonusPoints', 0), x.get('coins', 0)),
            reverse=True
        )[0]

        await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
            make_action_message(ServerAreaActionTypes.SETTLEMENT_COMPLETE, {
                'gameState': game_state
            }))
        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            make_action_message(ServerGameActionTypes.GAME_ENDED, {'winner': winner, 'gameState': game_state}))
    else:
        next_player = waiting_list[game_state['endgameChoiceIndex']]
        next_card = next_player['card']
        next_choices = get_endgame_choices(game_state['players'][next_player['playerId']], next_card)

        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            make_action_message(ServerGameActionTypes.GAME_ACTION, {
                'actionType': 'endgameScoreChoiceRequired',
                'playerId': next_player['playerId'],
                'playerName': next_player['playerName'],
                'data': {
                    'card': next_card,
                    'choices': next_choices
                },
                'gameState': game_state
            }))

    await broadcast_game_state(room_id, rooms, manager)


async def handle_submit_tribute_choice(websocket, room_id, player_id, rooms, manager, payload):
    """处理上供即时效果选择"""
    from utils.helpers import create_lobster
    
    task_id = payload.get('taskId')
    choice = payload.get('choice', {})

    game_state = rooms.get(room_id)
    if not game_state:
        return

    pending = game_state.get('pendingTributeChoice')
    if not pending or pending.get('playerId') != player_id:
        await send_error(websocket, '没有待处理的上供选择')
        return

    if str(pending.get('taskId')) != str(task_id):
        await send_error(websocket, '任务ID不匹配')
        return

    choice_type = pending.get('choiceType')
    player = game_state['players'][player_id]

    if choice_type == 'buy_advanced_lobster':
        grade = choice.get('grade', 'normal')
        if grade == 'normal':
            player['lobsters'].append(create_lobster('normal'))
        elif grade == 'grade1':
            player['lobsters'].append(create_lobster('grade1'))
    elif choice_type == 'discard_attack':
        action = choice.get('action', 'discard')
        if action == 'attack':
            player['attackTokens'] = player.get('attackTokens', 0) + 1
        elif action == 'discard':
            target_type = choice.get('targetType', 'lobster')
            target_player_id = player['id']
            for other_player in game_state['players']:
                if other_player['id'] == target_player_id:
                    continue
                if target_type == 'lobster':
                    if other_player.get('lobsters'):
                        other_player['lobsters'].pop(0)
                elif target_type == 'cage':
                    other_player['cages'] = max(0, other_player.get('cages', 0) - 1)

    aura_task = next((t for t in game_state['tributeTasks'] if str(t['id']) == str(task_id)), None)
    if aura_task:
        aura_result = apply_aura_effect(player, aura_task)
        if aura_result:
            if 'permaBuffs' not in player:
                player['permaBuffs'] = []
            for buff_key in aura_result:
                if aura_result[buff_key]:
                    player['permaBuffs'].append(buff_key)

        if 'tributeCards' not in player:
            player['tributeCards'] = []
        player['tributeCards'].append(aura_task)

    game_state['pendingTributeChoice'] = None

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        make_action_message(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'tributeChoiceSubmitted',
            'playerId': player_id,
            'data': {'taskId': task_id, 'choice': choice},
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


def _make_game_action_router(handlers: dict):
    """创建游戏行动路由函数"""
    async def handle_game_action_router(websocket, room_id, player_id, rooms, manager, payload):
        action_type = payload.get('actionType')
        action_payload = payload.get('payload', {})
        handler = handlers.get(action_type)
        if handler:
            return await handler(websocket, room_id, player_id, rooms, manager, action_payload)
        await send_error(websocket, f'未知的游戏行动: {action_type}')
    return handle_game_action_router


def get_game_action_handlers():
    """获取游戏行动处理器映射"""
    return {
        ClientGameActionTypes.USE_SEAWEED: handle_use_seaweed,
        ClientGameActionTypes.PLACE_HEADMAN: handle_place_headman,
        ClientGameActionTypes.CANCEL_HEADMAN: handle_cancel_headman,
        ClientGameActionTypes.NEXT_PLAYER: handle_next_player,
        ClientGameActionTypes.NEXT_AREA: handle_next_area,
        ClientGameActionTypes.EXCHANGE_SIGNALS: handle_exchange_signals,
        ClientGameActionTypes.BUY_ITEM: handle_buy_item,
        ClientGameActionTypes.SELL_ITEM: handle_sell_item,
        ClientGameActionTypes.CULTIVATE_LOBSTER: handle_cultivate_lobster,
        ClientGameActionTypes.SUBMIT_TRIBUTE_CHOICE: handle_submit_tribute_choice,
        ClientGameActionTypes.DOWNTOWN_ACTION: handle_downtown_action,
        ClientGameActionTypes.AREA_ACTION: handle_area_action,
        ClientGameActionTypes.ENDGAME_SCORE_CHOICE: handle_endgame_score_choice,
    }


handle_game_action = _make_game_action_router(get_game_action_handlers())