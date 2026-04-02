# -*- coding: utf-8 -*-
"""
游戏房间事件处理函数模块
每个 handler 签名: async def handler(websocket, room_id, player_id, rooms, manager, payload)
返回 False 表示需要 break 循环，否则返回 None。
"""

from utils.constants import AREAS, GRADE_UPGRADE
from utils.events import ServerEvents, ServerRoomActionTypes, ServerGameActionTypes, ServerBattleActionTypes, ServerAreaActionTypes
from utils.helpers import send_error, has_resources, update_resources, get_player
from services.game import (
    broadcast_room_state, broadcast_game_state, start_game, cleanup_room, transfer_host,
    next_round, cleanup_phase
)
from services.area import resolve_area_step
from utils.game_state import arena_betting_state
from utils.game_state import draw_tribute_tasks, draw_downtown_cards


def _sra(action_type, data):
    """构造 serverRoomAction / serverGameAction / serverBattleAction / serverAreaAction 消息体"""
    return {'actionType': action_type, **data}


def _make_bf(manager, room_id):
    """创建资源广播闭包"""
    async def bf(player_id, resources):
        await manager.send_to_room(room_id, ServerEvents.PLAYER_RESOURCE_UPDATE, {
            'playerId': player_id, 'resources': resources
        })
    return bf


def require_playing(fn):
    """装饰器：要求游戏处于 playing 状态"""
    async def wrapper(websocket, room_id, player_id, rooms, manager, payload):
        game_state = rooms.get(room_id)
        if not game_state or game_state.get('status') != 'playing':
            await send_error(websocket, '游戏未开始')
            return
        return await fn(websocket, room_id, player_id, rooms, manager, payload)
    return wrapper


def swap_challenge_slot(game_state, challenge_slot):
    """交换挑战槽位（challenger 获胜时调用）"""
    tribute = game_state['areas'].get('tribute')
    if not tribute:
        return False
    slots = tribute.get('slots', [])
    challenge_slots = tribute.get('challengeSlots', [])
    slot_map = {3: 0, 4: 1, 5: 2}
    idx = slot_map.get(challenge_slot)
    if idx is not None and idx < len(slots) and idx < len(challenge_slots):
        slots[idx], challenge_slots[idx] = challenge_slots[idx], slots[idx]
        return True
    return False


@require_playing
async def handle_use_seaweed(websocket, room_id, player_id, rooms, manager, payload):
    game_state = rooms.get(room_id)
    if not game_state:
        return
    player = get_player(game_state, player_id)
    if not player or player['seaweed'] <= 0:
        await send_error(websocket, '海草不足')
        return
    await update_resources(player, {'seaweed': -1}, broadcast_fn=_make_bf(manager, room_id))


async def handle_leave_room(websocket, room_id, player_id, rooms, manager, payload, fingerprint):
    game_state = rooms.get(room_id)
    player_name = None

    if game_state:
        player = get_player(game_state, player_id)
        if player:
            player_name = player['name']
            game_state['players'].remove(player)

            for uid in list(manager.user_rooms.keys()):
                if manager.user_rooms.get(uid) == room_id:
                    manager.user_rooms.pop(uid, None)

    manager.disconnect(room_id, player_id, fingerprint)

    if player_name:
        if game_state and game_state['players']:
            transfer_host(room_id, game_state)
            await broadcast_room_state(room_id, rooms, manager)
            await manager.broadcast_to_room_members(room_id, ServerEvents.SERVER_ROOM_ACTION,
                _sra(ServerRoomActionTypes.PLAYER_STATUS_CHANGE, {
                    'playerId': player_id, 'playerName': player_name,
                    'status': 'offline', 'players': game_state['players']
                }))
        else:
            cleanup_room(room_id, rooms, manager)

    try:
        await websocket.close()
    except Exception:
        pass
    return False


async def handle_set_ready(websocket, room_id, player_id, rooms, manager, payload):
    ready = payload.get('ready')
    force_start = payload.get('forceStart', False)

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = get_player(game_state, player_id)
    if player:
        player['ready'] = ready
        await manager.send_to_room(room_id, ServerEvents.SERVER_ROOM_ACTION,
            _sra(ServerRoomActionTypes.PLAYER_READY, {
                'playerId': player_id, 'ready': ready, 'players': game_state['players']
            }))
        await broadcast_room_state(room_id, rooms, manager)

        if force_start or (len(game_state['players']) >= 1 and all(p['ready'] for p in game_state['players'])):
            await start_game(room_id, rooms, manager)


async def handle_place_headman(websocket, room_id, player_id, rooms, manager, payload):
    area_index = payload.get('areaIndex')
    slot_index = payload.get('slotIndex')

    game_state = rooms.get(room_id)
    if not game_state or game_state.get('status') != 'playing':
        await send_error(websocket, '游戏未开始')
        return

    if player_id != game_state.get('currentPlayerIndex'):
        await send_error(websocket, '不是你的回合')
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
    bf = _make_bf(manager, room_id)
    if slot_index < 0 or slot_index >= len(slots) or slots[slot_index] is not None:
        await send_error(websocket, '该位置已有米宝')
        return
    await update_resources(player, {'liZhang': -1}, broadcast_fn=bf)
    slots[slot_index] = player_id
    await broadcast_game_state(room_id, rooms, manager)


async def handle_next_player(websocket, room_id, player_id, rooms, manager, payload):
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
        game_state['settlementState'] = {
            'currentSlotIndex': -1,
            'remainingActions': -1,
            'waitingForPlayer': None,
            'areaType': None
        }

        await _start_area_settlement(websocket, room_id, game_state, rooms, manager)
    else:
        current_idx = game_state.get('currentPlayerIndex', 0)
        game_state['currentPlayerIndex'] = (current_idx + 1) % len(game_state['players'])

        await broadcast_game_state(room_id, rooms, manager)


async def _start_area_settlement(websocket, room_id, game_state, rooms, manager):
    """启动当前区域的结算流程"""
    from services.area import resolve_area_step

    current_area = game_state.get('currentArea', 0)
    print(f"[_start_area_settlement] Starting settlement for area index {current_area}")

    if current_area >= len(AREAS):
        await _complete_settlement(room_id, game_state, rooms, manager)
        return

    area_name = AREAS[current_area]
    area_data = game_state['areas'].get(area_name)
    if not area_data:
        game_state['currentArea'] = current_area + 1
        await _start_area_settlement(websocket, room_id, game_state, rooms, manager)
        return

    result = await resolve_area_step(game_state, current_area, manager, room_id)
    print(f"[_start_area_settlement] resolve_area_step returned: {result}")

    if result == 'auto_next':
        if current_area + 1 >= len(AREAS):
            await _complete_settlement(room_id, game_state, rooms, manager)
        else:
            game_state['currentArea'] = current_area + 1
            await _start_area_settlement(websocket, room_id, game_state, rooms, manager)
    elif result == 'waiting_ui':
        await broadcast_game_state(room_id, rooms, manager)


async def _complete_settlement(room_id, game_state, rooms, manager):
    """完成结算阶段，进入清理和下一回合"""
    from services.game import cleanup_phase

    cleanup_phase(game_state)

    game_state['phase'] = 'placement'
    game_state['currentPlayerIndex'] = game_state.get('startingPlayerIndex', 0)
    game_state['currentArea'] = 0

    for area_name in AREAS:
        if area_name in game_state['areas']:
            slot_count = len(game_state['areas'][area_name]['slots'])
            game_state['areas'][area_name]['slots'] = [None] * slot_count

    for p in game_state['players']:
        p['royalCountThisRound'] = 0

    draw_tribute_tasks(game_state)
    draw_downtown_cards(game_state)

    await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
        _sra(ServerAreaActionTypes.SETTLEMENT_COMPLETE, {
            'gameState': game_state
        }))
    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        _sra(ServerGameActionTypes.ROUND_STARTED, {
            'round': game_state['currentRound'],
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)

async def handle_next_area(websocket, room_id, player_id, rooms, manager, payload):
    """结算当前区域并进入下一个区域"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    if game_state.get('phase') != 'settlement':
        await send_error(websocket, '当前不在结算阶段')
        return

    current_area = game_state.get('currentArea', 0)
    area_name = AREAS[current_area] if current_area < len(AREAS) else None

    if area_name and area_name in game_state['areas']:
        slot_count = len(game_state['areas'][area_name]['slots'])
        game_state['areas'][area_name]['slots'] = [None] * slot_count

    if current_area + 1 >= len(AREAS):
        await _complete_settlement(room_id, game_state, rooms, manager)
    else:
        game_state['currentArea'] = current_area + 1
        await _start_area_settlement(websocket, room_id, game_state, rooms, manager)

@require_playing
async def handle_area_action(websocket, room_id, player_id, rooms, manager, payload):
    """处理结算阶段的前端交互操作（海鲜市场买卖、养蛊区培养、闹市区选卡）"""
    from services.area import process_area_action

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
    
    print(f"[handle_area_action] player={player_id}, actionType={action_type}, currentArea={game_state.get('currentArea')}, settlementState={settlement_state}")

    result = await process_area_action(game_state, action_type, action_payload, manager, room_id, websocket)

    if result == 'action_complete':
        print(f"[handle_area_action] action_complete, currentArea={game_state.get('currentArea')}")
        await broadcast_game_state(room_id, rooms, manager)

        current_area = game_state.get('currentArea', 0)
        print(f"[handle_area_action] Advancing from area {current_area} to next...")
        if current_area + 1 >= len(AREAS):
            await _complete_settlement(room_id, game_state, rooms, manager)
        else:
            game_state['currentArea'] = current_area + 1
            await _start_area_settlement(websocket, room_id, game_state, rooms, manager)
    elif result == 'continue_ui':
        await broadcast_game_state(room_id, rooms, manager)
    elif result == 'error':
        pass


@require_playing
async def handle_exchange_signals(websocket, room_id, player_id, rooms, manager, payload):
    exchange_type = payload.get('exchangeType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    bf = _make_bf(manager, room_id)

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
        _sra(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'signalsExchanged',
            'playerId': player_id,
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


@require_playing
async def handle_buy_item(websocket, room_id, player_id, rooms, manager, payload):
    item_type = payload.get('itemType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    prices = game_state['areas']['seafood_market']['dynamicPrices']
    bf = _make_bf(manager, room_id)
    success = False

    if item_type == 'lobster' and player['coins'] >= prices['buyLobster']:
        await update_resources(player, {
            'coins': -prices['buyLobster'],
            'normal': 1
        }, broadcast_fn=bf)
        success = True
    elif item_type == 'seaweed' and player['coins'] >= prices['buySeaweed']:
        await update_resources(player, {
            'coins': -prices['buySeaweed'],
            'seaweed': 1
        }, broadcast_fn=bf)
        success = True
    elif item_type == 'cage' and player['coins'] >= prices['buyCage']:
        await update_resources(player, {
            'coins': -prices['buyCage'],
            'cages': 1
        }, broadcast_fn=bf)
        success = True
    elif item_type == 'headman' and player['coins'] >= prices['hireHeadman']:
        await update_resources(player, {
            'coins': -prices['hireHeadman'],
            'liZhang': 1
        }, broadcast_fn=bf)
        success = True

    if success:
        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            _sra(ServerGameActionTypes.GAME_ACTION, {
                'actionType': 'itemBought',
                'playerId': player_id,
                'data': {'itemType': item_type},
                'gameState': game_state
            }))
        await broadcast_game_state(room_id, rooms, manager)
    else:
        await send_error(websocket, '资源不足')


@require_playing
async def handle_sell_item(websocket, room_id, player_id, rooms, manager, payload):
    item_type = payload.get('itemType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    prices = game_state['areas']['seafood_market']['dynamicPrices']
    bf = _make_bf(manager, room_id)
    success = False

    if item_type == 'lobster' and has_resources(player, {'normal': 1}):
        await update_resources(player, {
            'normal': -1,
            'coins': prices['sellLobster']
        }, broadcast_fn=bf)
        success = True
    elif item_type == 'seaweed' and player['seaweed'] > 0:
        await update_resources(player, {
            'seaweed': -1,
            'coins': prices['sellSeaweed']
        }, broadcast_fn=bf)
        success = True
    elif item_type == 'cage' and player['cages'] > 0:
        await update_resources(player, {
            'cages': -1,
            'coins': prices['sellCage']
        }, broadcast_fn=bf)
        success = True

    if success:
        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            _sra(ServerGameActionTypes.GAME_ACTION, {
                'actionType': 'itemSold',
                'playerId': player_id,
                'data': {'itemType': item_type},
                'gameState': game_state
            }))
        await broadcast_game_state(room_id, rooms, manager)
    else:
        await send_error(websocket, '物品不足')


@require_playing
async def handle_cultivate_lobster(websocket, room_id, player_id, rooms, manager, payload):
    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    bf = _make_bf(manager, room_id)
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
        _sra(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'lobsterCultivated',
            'playerId': player_id,
            'data': {'upgraded': upgraded},
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


@require_playing
async def handle_submit_tribute(websocket, room_id, player_id, rooms, manager, payload):
    task_id = payload.get('taskId')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]

    task = next((t for t in game_state['tributeTasks'] if str(t['id']) == str(task_id)), None)
    if not task:
        await send_error(websocket, '任务不存在')
        return

    if task_id in player.get('completedTasks', []):
        await send_error(websocket, '您已完成过此上供')
        return

    req = task['requirements']
    if not has_resources(player, req):
        await send_error(websocket, '资源不足')
        return

    bf = _make_bf(manager, room_id)
    await update_resources(player, {**req, **task['reward']}, broadcast_fn=bf)

    if 'completedTasks' not in player:
        player['completedTasks'] = []
    player['completedTasks'].append(task_id)

    aura = task.get('aura')
    if aura:
        aura_type = aura.get('type')
        if aura_type == 'bonusGold':
            player['bonusGold'] = player.get('bonusGold', 0) + aura.get('value', 0)
        elif aura_type == 'extraCage':
            player['cages'] = player.get('cages', 0) + aura.get('value', 0)
        else:
            if 'permaBuffs' not in player:
                player['permaBuffs'] = []
            player['permaBuffs'].append(aura_type)

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        _sra(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'tributeSubmitted',
            'playerId': player_id,
            'data': {'taskId': task_id},
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


@require_playing
async def handle_downtown_action(websocket, room_id, player_id, rooms, manager, payload):
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

    bf = _make_bf(manager, room_id)
    await update_resources(player, {**cost, **reward}, broadcast_fn=bf)

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        _sra(ServerGameActionTypes.GAME_ACTION, {
            'actionType': 'downtownActionExecuted',
            'playerId': player_id,
            'data': {'card': card},
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


@require_playing
async def handle_battle_start(websocket, room_id, player_id, rooms, manager, payload):
    battle_data = payload.get('battleData')

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        _sra(ServerBattleActionTypes.BATTLE_START, {
            'battleData': battle_data,
            'initiatorId': player_id
        }))


async def handle_battle_action(websocket, room_id, player_id, rooms, manager, payload):
    action_type = payload.get('actionType')
    battle_data = payload.get('battleData')
    sender_id = payload.get('senderId')

    if action_type == 'battleEnd':
        game_state = rooms.get(room_id)
        if game_state:
            winner_id = battle_data.get('winner', {}).get('id')
            challenge_slot = battle_data.get('challengeSlotIndex')

            players_data = battle_data.get('players', [])
            challenger_id = None
            if len(players_data) >= 2:
                challenger_id = players_data[0]['id']

            if winner_id == challenger_id and challenge_slot:
                if swap_challenge_slot(game_state, challenge_slot):
                    print(f"[battleEnd] Slot swapped: challenger wins at slot {challenge_slot}")

            # 处理投注结算 + 胜者奖励 + 中线望值（合并为一次 update_resources）
            winner_id = battle_data.get('winner', {}).get('id')
            challenge_slot = battle_data.get('challengeSlotIndex')
            bf = _make_bf(manager, room_id)

            for key in list(arena_betting_state.keys()):
                bs = arena_betting_state[key]
                if not bs.get('completed') or not key.startswith(f"{room_id}_"):
                    continue
                if str(challenge_slot) in key:
                    bet_results = {}
                    for pid, bet in bs['bets'].items():
                        if bet['amount'] > 0 and bet.get('targetFighterId') == winner_id:
                            bettor = get_player(game_state, pid)
                            if bettor:
                                await update_resources(bettor, {'coins': bet['amount'] * 2}, broadcast_fn=bf)
                            bet_results[str(pid)] = {'won': True, 'reward': bet['amount'] * 2}
                        else:
                            bet_results[str(pid)] = {'won': False, 'reward': 0}

                    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                        _sra(ServerBattleActionTypes.BET_RESULT, {
                            'winnerId': winner_id,
                            'betResults': bet_results
                        }))
                    del arena_betting_state[key]
                    break

            # 处理胜者奖励（含中线望值）
            award_choice = battle_data.get('winnerAwardChoice')
            upgrade_from = None
            upgrade_to = None
            if winner_id is not None and award_choice:
                winner = get_player(game_state, winner_id)
                if winner:
                    deltas = {}
                    if award_choice == 'coins':
                        deltas['coins'] = 2
                    elif award_choice == 'gradeUpgrade':
                        new_grade = battle_data.get('winner', {}).get('lobsterId')
                        if new_grade and new_grade in GRADE_UPGRADE:
                            upgrade_from = GRADE_UPGRADE[new_grade]
                            upgrade_to = new_grade
                            deltas[upgrade_from] = -1
                            deltas[upgrade_to] = 1

                    # 中线望值
                    for pi, field in [(0, 'p1CrossedMidline'), (1, 'p2CrossedMidline')]:
                        if battle_data.get(field):
                            p = players_data[pi] if pi < len(players_data) else None
                            if p and p.get('id') == winner_id:
                                deltas['wang'] = deltas.get('wang', 0) + 1

                    if deltas:
                        await update_resources(winner, deltas, broadcast_fn=bf)

            await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                _sra(ServerBattleActionTypes.BATTLE_ENDED, {
                    'winnerId': winner_id,
                    'awardChoice': award_choice,
                    'upgradeFrom': upgrade_from,
                    'upgradeTo': upgrade_to,
                    'gameState': game_state
                }))

            if 'tributeBattlesCompleted' not in game_state:
                game_state['tributeBattlesCompleted'] = 0
            game_state['tributeBattlesCompleted'] += 1

            # 清理 battleStart 去重标记
            if '_lastBattleStartSent' in game_state:
                del game_state['_lastBattleStartSent']

            total_battles = len(game_state.get('battleQueue', []))
            if game_state['tributeBattlesCompleted'] >= total_battles:
                current_area = game_state.get('currentArea', 0)
                area_name = AREAS[current_area] if current_area < len(AREAS) else None
                if area_name and area_name in game_state['areas']:
                    slot_count = len(game_state['areas'][area_name]['slots'])
                    game_state['areas'][area_name]['slots'] = [None] * slot_count

                if current_area + 1 >= len(AREAS):
                    await _complete_settlement(room_id, game_state, rooms, manager)
                else:
                    game_state['currentArea'] = current_area + 1
                    await _start_area_settlement(websocket, room_id, game_state, rooms, manager)

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        _sra(ServerBattleActionTypes.BATTLE_ACTION, {
            'actionType': action_type,
            'battleData': battle_data,
            'senderId': sender_id
        }))


@require_playing
async def handle_lobster_selected(websocket, room_id, player_id, rooms, manager, payload):
    lobster_data = payload.get('lobster')

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        _sra(ServerBattleActionTypes.LOBSTER_SELECTED, {
            'playerId': player_id,
            'lobster': lobster_data
        }))

    battle_id = payload.get('battleId')
    if battle_id:
        key = f"{room_id}_{battle_id}"
        if key not in arena_betting_state:
            arena_betting_state[key] = {
                'battleId': battle_id,
                'challengerId': payload.get('challengerId'),
                'defenderId': payload.get('defenderId'),
                'challengerLobster': None,
                'defenderLobster': None,
                'spectators': payload.get('spectators', []),
                'bets': {},
                'started': False,
                'completed': False
            }

        state = arena_betting_state[key]
        if player_id == state['challengerId']:
            state['challengerLobster'] = lobster_data
        elif player_id == state['defenderId']:
            state['defenderLobster'] = lobster_data

        if state['challengerLobster'] and state['defenderLobster'] and not state['started']:
            state['started'] = True
            await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                _sra(ServerBattleActionTypes.ARENA_BETTING_START, {
                    'battleId': battle_id,
                    'challengerId': state['challengerId'],
                    'defenderId': state['defenderId'],
                    'challengerLobster': state['challengerLobster'],
                    'defenderLobster': state['defenderLobster'],
                    'spectators': state['spectators']
                }))

            if len(state['spectators']) == 0:
                await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                    _sra(ServerBattleActionTypes.ARENA_BETTING_COMPLETE, {
                        'battleId': battle_id,
                        'bets': {}
                    }))
                state['completed'] = True


@require_playing
async def handle_spectator_bet(websocket, room_id, player_id, rooms, manager, payload):
    battle_id = payload.get('battleId')
    bet_amount = payload.get('betAmount', 0)
    target_fighter_id = payload.get('targetFighterId')

    key = f"{room_id}_{battle_id}"
    state = arena_betting_state.get(key)
    if not state:
        await send_error(websocket, '投注已结束')
        return

    if player_id not in state['spectators']:
        await send_error(websocket, '你不是观战者')
        return

    if player_id in state['bets']:
        await send_error(websocket, '已投注')
        return

    state['bets'][player_id] = {
        'amount': bet_amount,
        'targetFighterId': target_fighter_id
    }

    if bet_amount > 0:
        game_state = rooms.get(room_id)
        if game_state:
            player = get_player(game_state, player_id)
            if player and player.get('coins', 0) >= bet_amount:
                await update_resources(player, {'coins': -bet_amount}, broadcast_fn=_make_bf(manager, room_id))

    if len(state['bets']) >= len(state['spectators']):
        await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
            _sra(ServerBattleActionTypes.ARENA_BETTING_COMPLETE, {
                'battleId': battle_id,
                'bets': state['bets']
            }))
        state['completed'] = True


@require_playing
async def handle_no_lobster_forfeit(websocket, room_id, player_id, rooms, manager, payload):
    """处理因无可用龙虾导致的自动判负（defender 无龙虾时 challenger 获胜并交换 slot）"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    challenge_slot = payload.get('challengeSlot')
    if swap_challenge_slot(game_state, challenge_slot):
        print(f"[noLobsterForfeit] Slot swapped: challenger wins at slot {challenge_slot}")

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        _sra(ServerBattleActionTypes.BATTLE_ACTION, {
            'actionType': 'skipped',
            'battleData': {
                'challengeSlot': challenge_slot,
                'reason': 'no_available_lobsters',
                'winner': 'challenger'
            },
            'senderId': player_id
        }))


# =============================================================================
# 事件分发表 (精简版)
#
# 已合并到 gameAction 的事件 (由 game_action_handler.py 路由):
#   placeHeadman, nextPlayer, nextArea, exchangeSignals,
#   buyItem, sellItem, cultivateLobster, submitTribute,
#   executeDowntownAction, useSeaweed
#
# 保留的顶级事件: 房间管理 + 战斗相关
# =============================================================================

_last_action_ts: dict = {}

def _check_idempotency(player_id: int, event: str, payload: dict) -> bool:
    """检查操作是否重复（500ms 窗口），返回 True 表示是重复请求"""
    import time
    key = f"{player_id}:{event}"
    now = time.time()
    last = _last_action_ts.get(key)
    if last is not None and now - last < 0.5:
        return True
    _last_action_ts[key] = now
    return False

GAME_EVENT_HANDLERS = {
    'leaveRoom': handle_leave_room,
    'setReady': handle_set_ready,
    'battleStart': handle_battle_start,
    'battleAction': handle_battle_action,
    'lobsterSelected': handle_lobster_selected,
    'spectatorBet': handle_spectator_bet,
    'noLobsterForfeit': handle_no_lobster_forfeit,
}
