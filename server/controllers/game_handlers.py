# -*- coding: utf-8 -*-
"""
游戏房间事件处理函数模块
每个 handler 签名: async def handler(websocket, room_id, player_id, rooms, manager, payload)
返回 False 表示需要 break 循环，否则返回 None。
"""

import random
from utils.constants import AREAS, GRADE_UPGRADE
from utils.helpers import send_error, has_resources, update_resources, get_player
from services.game import (
    broadcast_room_state, start_game, cleanup_room, transfer_host,
    next_round
)
from services.area import resolve_area
from utils.game_state import arena_betting_state


def _make_bf(manager, room_id):
    """创建资源广播闭包"""
    async def bf(player_id, resources):
        await manager.send_to_room(room_id, 'playerResourceUpdate', {
            'playerId': player_id, 'resources': resources
        })
    return bf


async def handle_use_seaweed(websocket, room_id, player_id, rooms, manager, payload):
    game_state = rooms.get(room_id)
    if not game_state:
        return
    player = get_player(game_state, player_id)
    if not player or player['seaweed'] <= 0:
        await send_error(websocket, '海草不足')
        return
    await update_resources(player, {'seaweed': 1}, sign=-1, broadcast_fn=_make_bf(manager, room_id))


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
    await websocket.close()

    if player_name:
        if game_state and game_state['players']:
            transfer_host(room_id, game_state)
            await broadcast_room_state(room_id, rooms, manager)
            await manager.broadcast_to_room_members(room_id, 'playerLeft', {
                'playerId': player_id, 'playerName': player_name, 'players': game_state['players']
            })
        else:
            cleanup_room(room_id, rooms, manager)
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
        await manager.send_to_room(room_id, 'playerReady', {
            'playerId': player_id, 'ready': ready, 'players': game_state['players']
        })
        await broadcast_room_state(room_id, rooms, manager)

        if force_start or (len(game_state['players']) >= 1 and all(p['ready'] for p in game_state['players'])):
            await start_game(room_id, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))


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
    await update_resources(player, {'liZhang': 1}, sign=-1, broadcast_fn=bf)
    slots[slot_index] = player_id

    await manager.send_to_room(room_id, 'headmanPlaced', {
        'playerId': player_id, 'areaIndex': area_index, 'slotIndex': slot_index, 'gameState': game_state
    })
    await broadcast_room_state(room_id, rooms, manager)


async def handle_next_player(websocket, room_id, player_id, rooms, manager, payload):
    print(f"DEBUG: nextPlayer event handler triggered for player {player_id} in room {room_id}")
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

        for i, area_name in enumerate(AREAS):
            if area_name in game_state['areas']:
                resolve_area(game_state, i, AREAS)

        # 检查是否有战斗
        battle_queue = game_state.get('battleQueue', [])
        if battle_queue:
            await manager.send_to_room(room_id, 'battleStart', {
                'battleQueue': battle_queue,
                'gameState': game_state
            })

        await manager.send_to_room(room_id, 'playerTurn', {
            'currentPlayerIndex': game_state.get('currentPlayerIndex', 0), 'gameState': game_state
        })
        await broadcast_room_state(room_id, rooms, manager)
        print(f"All players placed, phase changed to settlement, {len(battle_queue)} battles queued")
    else:
        current_idx = game_state.get('currentPlayerIndex', 0)
        game_state['currentPlayerIndex'] = (current_idx + 1) % len(game_state['players'])
        print(f"Next player: {game_state['currentPlayerIndex']}")

        await manager.send_to_room(room_id, 'playerTurn', {
            'currentPlayerIndex': game_state.get('currentPlayerIndex', 0), 'gameState': game_state
        })
        await broadcast_room_state(room_id, rooms, manager)


async def handle_next_area(websocket, room_id, player_id, rooms, manager, payload):
    """结算当前区域并进入下一个区域"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    current_area = game_state.get('currentArea', 0)

    # 结算下一个区域
    if current_area + 1 >= len(AREAS):
        # 所有区域已结算完毕，清空所有槽位，发放里长，进入下一回合
        for area_name in AREAS:
            if area_name in game_state['areas']:
                slot_count = len(game_state['areas'][area_name]['slots'])
                game_state['areas'][area_name]['slots'] = [None] * slot_count

        for p in game_state['players']:
            p['liZhang'] = min(p['liZhang'] + 1, 5)

        await next_round(room_id, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))
    else:
        # 先结算当前区域
        resolve_area(game_state, current_area, AREAS)

        # 清空所有区域槽位，发放里长
        for area_name in AREAS:
            if area_name in game_state['areas']:
                slot_count = len(game_state['areas'][area_name]['slots'])
                game_state['areas'][area_name]['slots'] = [None] * slot_count

        for p in game_state['players']:
            p['liZhang'] = min(p['liZhang'] + 1, 5)

        current_area += 1
        game_state['currentArea'] = current_area

        await manager.send_to_room(room_id, 'areaSettled', {
            'areaIndex': current_area, 'gameState': game_state
        })
        await broadcast_room_state(room_id, rooms, manager)


async def handle_next_round(websocket, room_id, player_id, rooms, manager, payload):
    await next_round(room_id, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))


async def handle_exchange_signals(websocket, room_id, player_id, rooms, manager, payload):
    exchange_type = payload.get('exchangeType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    bf = _make_bf(manager, room_id)

    if exchange_type == '1to1' and player['tempBubbles'] >= 1:
        player['tempBubbles'] -= 1
        await update_resources(player, {'coins': 1}, sign=1, broadcast_fn=bf)
    elif exchange_type == '2to3' and player['tempBubbles'] >= 2:
        player['tempBubbles'] -= 2
        await update_resources(player, {'grade3': 1}, sign=1, broadcast_fn=bf)
    elif exchange_type == '3to2' and player['tempBubbles'] >= 3:
        player['tempBubbles'] -= 3
        await update_resources(player, {'grade2': 1}, sign=1, broadcast_fn=bf)

    await manager.send_to_room(room_id, 'signalsExchanged', {
        'playerId': player_id, 'gameState': game_state
    })
    await broadcast_room_state(room_id, rooms, manager)


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
        await update_resources(player, {'coins': prices['buyLobster']}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'common': 1}, sign=1, broadcast_fn=bf)
        success = True
    elif item_type == 'seaweed' and player['coins'] >= prices['buySeaweed']:
        await update_resources(player, {'coins': prices['buySeaweed']}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'seaweed': 1}, sign=1, broadcast_fn=bf)
        success = True
    elif item_type == 'cage' and player['coins'] >= prices['buyCage']:
        await update_resources(player, {'coins': prices['buyCage']}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'cage': 1}, sign=1, broadcast_fn=bf)
        success = True
    elif item_type == 'headman' and player['coins'] >= prices['hireHeadman']:
        await update_resources(player, {'coins': prices['hireHeadman']}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'liZhang': 1}, sign=1, broadcast_fn=bf)
        success = True

    if success:
        await manager.send_to_room(room_id, 'itemBought', {
            'playerId': player_id, 'itemType': item_type, 'gameState': game_state
        })
        await broadcast_room_state(room_id, rooms, manager)
    else:
        await send_error(websocket, '资源不足')


async def handle_sell_item(websocket, room_id, player_id, rooms, manager, payload):
    item_type = payload.get('itemType')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    prices = game_state['areas']['seafood_market']['dynamicPrices']
    bf = _make_bf(manager, room_id)
    success = False

    if item_type == 'lobster' and has_resources(player, {'common': 1}):
        await update_resources(player, {'common': 1}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'coins': prices['sellLobster']}, sign=1, broadcast_fn=bf)
        success = True
    elif item_type == 'seaweed' and player['seaweed'] > 0:
        await update_resources(player, {'seaweed': 1}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'coins': prices['sellSeaweed']}, sign=1, broadcast_fn=bf)
        success = True
    elif item_type == 'cage' and player['cages'] > 0:
        await update_resources(player, {'cages': 1}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'coins': prices['sellCage']}, sign=1, broadcast_fn=bf)
        success = True

    if success:
        await manager.send_to_room(room_id, 'itemSold', {
            'playerId': player_id, 'itemType': item_type, 'gameState': game_state
        })
        await broadcast_room_state(room_id, rooms, manager)
    else:
        await send_error(websocket, '物品不足')


async def handle_cultivate_lobster(websocket, room_id, player_id, rooms, manager, payload):
    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = game_state['players'][player_id]
    bf = _make_bf(manager, room_id)
    upgraded = False

    if has_resources(player, {'grade1': 1}) and (player['cages'] > 0 or player['coins'] >= 3):
        if player['cages'] > 0:
            await update_resources(player, {'cages': 1}, sign=-1, broadcast_fn=bf)
        else:
            await update_resources(player, {'coins': 3}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'grade1': 1}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'royal': 1}, sign=1, broadcast_fn=bf)
        if player['royalCountThisRound'] < 2:
            player['royalCountThisRound'] += 1
        upgraded = True
    elif has_resources(player, {'grade2': 1}):
        await update_resources(player, {'grade2': 1}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'grade1': 1}, sign=1, broadcast_fn=bf)
        upgraded = True
    elif has_resources(player, {'grade3': 1}):
        await update_resources(player, {'grade3': 1}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'grade2': 1}, sign=1, broadcast_fn=bf)
        upgraded = True
    elif has_resources(player, {'common': 1}):
        await update_resources(player, {'common': 1}, sign=-1, broadcast_fn=bf)
        await update_resources(player, {'grade3': 1}, sign=1, broadcast_fn=bf)
        upgraded = True

    await manager.send_to_room(room_id, 'lobsterCultivated', {
        'playerId': player_id, 'upgraded': upgraded, 'gameState': game_state
    })
    await broadcast_room_state(room_id, rooms, manager)


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
    await update_resources(player, req, sign=-1, broadcast_fn=bf)
    await update_resources(player, task['reward'], sign=1, broadcast_fn=bf)

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

    await manager.send_to_room(room_id, 'tributeSubmitted', {
        'playerId': player_id, 'taskId': task_id, 'gameState': game_state
    })
    await broadcast_room_state(room_id, rooms, manager)


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
    await update_resources(player, cost, sign=-1, broadcast_fn=bf)
    await update_resources(player, reward, sign=1, broadcast_fn=bf)

    await manager.send_to_room(room_id, 'downtownActionExecuted', {
        'playerId': player_id, 'card': card, 'gameState': game_state
    })
    await broadcast_room_state(room_id, rooms, manager)


async def handle_battle_start(websocket, room_id, player_id, rooms, manager, payload):
    battle_data = payload.get('battleData')

    await manager.send_to_room(room_id, 'battleStart', {
        'battleData': battle_data,
        'initiatorId': player_id
    })


async def handle_battle_action(websocket, room_id, player_id, rooms, manager, payload):
    action_type = payload.get('actionType')
    battle_data = payload.get('battleData')
    sender_id = payload.get('senderId')
    # 处理 battleEnd 事件，检查是否需要交换 slot
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
                tribute_data = game_state['areas'].get('tribute')
                if tribute_data:
                    slots = tribute_data.get('slots', [])
                    challenge_slots = tribute_data.get('challengeSlots', [])

                    slot_map = {3: 0, 4: 1, 5: 2}
                    defender_idx = slot_map.get(challenge_slot)

                    if defender_idx is not None and defender_idx < len(slots) and defender_idx < len(challenge_slots):
                        slots[defender_idx], challenge_slots[defender_idx] = \
                            challenge_slots[defender_idx], slots[defender_idx]
                        print(f"[battleEnd] Slot swapped: challenger wins at slot {challenge_slot}")

            # 处理投注结算
            winner_id = battle_data.get('winner', {}).get('id')
            challenge_slot = battle_data.get('challengeSlotIndex')
            for key in list(arena_betting_state.keys()):
                bs = arena_betting_state[key]
                if not bs.get('completed') or not key.startswith(f"{room_id}_"):
                    continue
                if str(challenge_slot) in key:
                    bet_results = {}
                    bf = _make_bf(manager, room_id)
                    for pid, bet in bs['bets'].items():
                        if bet['amount'] > 0 and bet.get('targetFighterId') == winner_id:
                            bettor = get_player(game_state, pid)
                            if bettor:
                                await update_resources(bettor, {'coins': bet['amount'] * 2}, sign=1, broadcast_fn=bf)
                            bet_results[str(pid)] = {'won': True, 'reward': bet['amount'] * 2}
                        else:
                            bet_results[str(pid)] = {'won': False, 'reward': 0}

                    await manager.send_to_room(room_id, 'betResult', {
                        'winnerId': winner_id,
                        'betResults': bet_results
                    })
                    del arena_betting_state[key]
                    break

            # 处理胜者奖励
            award_choice = battle_data.get('winnerAwardChoice')
            upgrade_from = None
            upgrade_to = None
            if winner_id is not None and award_choice:
                winner = get_player(game_state, winner_id)
                if winner:
                    bf = _make_bf(manager, room_id)
                    if award_choice == 'coins':
                        await update_resources(winner, {'coins': 2}, sign=1, broadcast_fn=bf)
                    elif award_choice == 'gradeUpgrade':
                        new_grade = battle_data.get('winner', {}).get('lobsterId')
                        if new_grade and new_grade in GRADE_UPGRADE:
                            upgrade_from = GRADE_UPGRADE[new_grade]
                            upgrade_to = new_grade
                            await update_resources(winner, {upgrade_from: 1}, sign=-1, broadcast_fn=bf)
                            await update_resources(winner, {upgrade_to: 1}, sign=1, broadcast_fn=bf)

            # 广播 battleEnded
            await manager.send_to_room(room_id, 'battleEnded', {
                'winnerId': winner_id,
                'awardChoice': award_choice,
                'upgradeFrom': upgrade_from,
                'upgradeTo': upgrade_to,
                'gameState': game_state
            })

    await manager.send_to_room(room_id, 'battleAction', {
        'actionType': action_type,
        'battleData': battle_data,
        'senderId': sender_id
    })


async def handle_lobster_selected(websocket, room_id, player_id, rooms, manager, payload):
    lobster_data = payload.get('lobster')

    print(f"[lobsterSelected] Player {player_id} selected lobster in room {room_id}")

    await manager.send_to_room(room_id, 'lobsterSelected', {
        'playerId': player_id,
        'lobster': lobster_data
    })

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
            await manager.send_to_room(room_id, 'arenaBettingStart', {
                'battleId': battle_id,
                'challengerId': state['challengerId'],
                'defenderId': state['defenderId'],
                'challengerLobster': state['challengerLobster'],
                'defenderLobster': state['defenderLobster'],
                'spectators': state['spectators']
            })
            print(f"[arenaBettingStart] Battle {battle_id} betting started")

            if len(state['spectators']) == 0:
                await manager.send_to_room(room_id, 'arenaBettingComplete', {
                    'battleId': battle_id,
                    'bets': {}
                })
                state['completed'] = True


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
                await update_resources(player, {'coins': bet_amount}, sign=-1, broadcast_fn=_make_bf(manager, room_id))

    if len(state['bets']) >= len(state['spectators']):
        await manager.send_to_room(room_id, 'arenaBettingComplete', {
            'battleId': battle_id,
            'bets': state['bets']
        })
        state['completed'] = True


# =============================================================================
# 事件分发表
# =============================================================================
GAME_EVENT_HANDLERS = {
    'leaveRoom': handle_leave_room,
    'setReady': handle_set_ready,
    'placeHeadman': handle_place_headman,
    'nextPlayer': handle_next_player,
    'nextArea': handle_next_area,
    'nextRound': handle_next_round,
    'exchangeSignals': handle_exchange_signals,
    'buyItem': handle_buy_item,
    'sellItem': handle_sell_item,
    'cultivateLobster': handle_cultivate_lobster,
    'submitTribute': handle_submit_tribute,
    'executeDowntownAction': handle_downtown_action,
    'battleStart': handle_battle_start,
    'battleAction': handle_battle_action,
    'lobsterSelected': handle_lobster_selected,
    'spectatorBet': handle_spectator_bet,
    'useSeaweed': handle_use_seaweed,
}
