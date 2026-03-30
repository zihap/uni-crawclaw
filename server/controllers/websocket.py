# -*- coding: utf-8 -*-
"""
WebSocket控制器模块
"""

import time
import random
from fastapi import WebSocket, WebSocketDisconnect
from utils.constants import AREAS
from utils.helpers import generate_room_id
from utils.game_state import create_game_state, create_player
from services.game import (
    broadcast_room_state, start_game, cleanup_room, transfer_host,
    handle_player_disconnect, handle_next_round
)
from services.area import resolve_area


async def handle_lobby_websocket(websocket: WebSocket, rooms: dict, manager):
    """大厅WebSocket处理"""
    fingerprint = id(websocket)
    await websocket.accept()

    user_id = None

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get('event')
            payload = data.get('data', {})

            if event == 'heartbeat':
                manager.heartbeat_timestamps[fingerprint] = time.time()
                await websocket.send_json({'event': 'heartbeatAck', 'data': {'timestamp': int(time.time())}})

            elif event == 'createRoom':
                player_name = payload.get('playerName')
                user_id = payload.get('userId')
                max_players = payload.get('maxPlayers', 4)

                new_room_id = generate_room_id(rooms)

                game_state = create_game_state()
                game_state['gameId'] = new_room_id
                game_state['status'] = 'waiting'
                game_state['maxPlayers'] = max_players

                player = create_player(0, player_name, True, user_id, position=0)
                game_state['players'].append(player)

                rooms[new_room_id] = game_state
                manager.lobby_connections[user_id] = websocket
                manager.user_rooms[user_id] = new_room_id

                await websocket.send_json({
                    'event': 'roomCreated',
                    'data': {'roomId': new_room_id, 'playerId': 0, 'gameState': game_state}
                })
                print(f"Room {new_room_id} created by {player_name}")

            elif event == 'joinRoom':
                room_id = payload.get('roomId')
                player_name = payload.get('playerName')
                user_id = payload.get('userId')

                game_state = rooms.get(room_id)

                if not game_state:
                    await websocket.send_json({'event': 'error', 'data': {'message': '房间不存在'}})
                    continue

                for p in game_state['players']:
                    if p.get('userId') == user_id:
                        p['isOnline'] = True
                        p['ready'] = False
                        manager.lobby_connections[user_id] = websocket
                        manager.user_rooms[user_id] = room_id
                        await websocket.send_json({
                            'event': 'playerReconnected',
                            'data': {'player': p, 'players': game_state['players']}
                        })
                        await manager.broadcast_to_room_members(room_id, 'playerOnline', {
                            'playerId': p['id'], 'playerName': p['name'], 'players': game_state['players']
                        })
                        await manager.broadcast_to_room_members(room_id, 'roomStateUpdate', {
                            'players': game_state['players'],
                            'gameStarted': False,
                            'status': 'waiting',
                            'maxPlayers': game_state.get('maxPlayers', 4)
                        })
                        continue

                max_players = game_state.get('maxPlayers', 4)
                if len(game_state['players']) >= max_players:
                    await websocket.send_json({'event': 'error', 'data': {'message': '房间已满'}})
                    continue

                if game_state['status'] != 'waiting':
                    await websocket.send_json({'event': 'error', 'data': {'message': '游戏已开始'}})
                    continue

                new_player_id = len(game_state['players'])
                player = create_player(new_player_id, player_name, False, user_id, position=new_player_id)
                game_state['players'].append(player)

                manager.lobby_connections[user_id] = websocket
                manager.user_rooms[user_id] = room_id

                await websocket.send_json({
                    'event': 'playerJoined',
                    'data': {'playerId': new_player_id, 'player': player, 'gameState': game_state}
                })

                await manager.broadcast_to_room_members(room_id, 'roomStateUpdate', {
                    'players': game_state['players'],
                    'gameStarted': False,
                    'status': 'waiting',
                    'maxPlayers': game_state.get('maxPlayers', 4)
                })
                print(f"{player_name} joined room {room_id}")

            elif event == 'setReady':
                room_id = manager.user_rooms.get(user_id)
                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                ready = payload.get('ready')
                force_start = payload.get('forceStart', False)

                player = next((p for p in game_state['players'] if p.get('userId') == user_id), None)
                if player:
                    player['ready'] = ready
                    await manager.broadcast_to_room_members(room_id, 'playerReady', {
                        'playerId': player['id'], 'ready': ready, 'players': game_state['players']
                    })
                    await manager.broadcast_to_room_members(room_id, 'roomStateUpdate', {
                        'players': game_state['players'],
                        'gameStarted': game_state['status'] == 'playing',
                        'status': game_state['status'],
                        'maxPlayers': game_state.get('maxPlayers', 4)
                    })

                    if force_start or (len(game_state['players']) >= 1 and all(p['ready'] for p in game_state['players'])):
                        await start_game(room_id, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))

            elif event == 'ping':
                await websocket.send_json({'event': 'pong', 'data': {}})

    except WebSocketDisconnect:
        room_id = manager.user_rooms.get(user_id)
        manager.lobby_disconnect(user_id, fingerprint)
        if room_id:
            game_state = rooms.get(room_id)
            if game_state:
                player = next((p for p in game_state['players'] if p.get('userId') == user_id), None)
                if player:
                    await handle_player_disconnect(room_id, player['id'], player.get('name'), rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))

    except Exception as e:
        print(f"Lobby WebSocket error: {e}")

    finally:
        manager.heartbeat_timestamps.pop(fingerprint, None)


async def handle_game_websocket(websocket: WebSocket, room_id: str, player_id: int, rooms: dict, manager):
    """游戏房间WebSocket处理"""
    fingerprint = id(websocket)

    print(f"WebSocket connection: room_id={room_id}, player_id={player_id}")
    print(f"DEBUG: rooms at connection time: {list(rooms.keys())}")

    await manager.connect(websocket, room_id, player_id)

    game_state = rooms.get(room_id)
    if game_state:
        player = next((p for p in game_state['players'] if p['id'] == player_id), None)
        if player:
            player['isOnline'] = True
            await manager.send_to_room(room_id, 'playerOnline', {
                'playerId': player_id,
                'playerName': player['name'],
                'players': game_state['players']
            })

        await manager.send_to_player(room_id, player_id, 'roomStateUpdate', {
            'players': game_state['players'],
            'gameStarted': game_state['status'] == 'playing',
            'status': game_state['status'],
            'phase': game_state.get('phase', 'waiting'),
            'currentRound': game_state.get('currentRound', 1),
            'currentPlayerIndex': game_state.get('currentPlayerIndex', 0)
        })

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get('event')
            payload = data.get('data', {})
            print(f"WebSocket message in room {room_id} from player {player_id}: event={event}, payload={payload}")

            if event == 'heartbeat':
                manager.heartbeat_timestamps[fingerprint] = time.time()
                await websocket.send_json({'event': 'heartbeatAck', 'data': {'timestamp': int(time.time())}})

            elif event == 'createRoom':
                player_name = payload.get('playerName')
                user_id = payload.get('userId')
                max_players = payload.get('maxPlayers', 4)

                new_room_id = generate_room_id(rooms)
                game_state = create_game_state()
                game_state['gameId'] = new_room_id
                game_state['status'] = 'waiting'
                game_state['maxPlayers'] = max_players

                player = create_player(0, player_name, True, user_id, position=0)
                game_state['players'].append(player)

                rooms[new_room_id] = game_state
                await websocket.send_json({
                    'event': 'roomCreated',
                    'data': {'roomId': new_room_id, 'playerId': 0, 'gameState': game_state}
                })
                print(f"Room {new_room_id} created by {player_name}")

            elif event == 'joinRoom':
                player_name = payload.get('playerName')
                user_id = payload.get('userId')

                game_state = rooms.get(room_id)
                if not game_state:
                    await websocket.send_json({'event': 'error', 'data': {'message': '房间不存在'}})
                    continue

                for p in game_state['players']:
                    if p.get('userId') == user_id:
                        p['isOnline'] = True
                        p['ready'] = False
                        await manager.send_to_player(room_id, p['id'], 'playerReconnected', {
                            'player': p, 'players': game_state['players']
                        })
                        await broadcast_room_state(room_id, rooms, manager)
                        continue

                max_players = game_state.get('maxPlayers', 4)
                if len(game_state['players']) >= max_players:
                    await websocket.send_json({'event': 'error', 'data': {'message': '房间已满'}})
                    continue

                if game_state['status'] != 'waiting':
                    await websocket.send_json({'event': 'error', 'data': {'message': '游戏已开始'}})
                    continue

                new_player_id = len(game_state['players'])
                player = create_player(new_player_id, player_name, False, user_id, position=new_player_id)
                game_state['players'].append(player)

                await manager.send_to_room(room_id, 'playerJoined', {
                    'player': player, 'players': game_state['players']
                })
                await broadcast_room_state(room_id, rooms, manager)
                print(f"{player_name} joined room {room_id}")

            elif event == 'setReady':
                ready = payload.get('ready')
                force_start = payload.get('forceStart', False)

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                player = next((p for p in game_state['players'] if p['id'] == player_id), None)
                if player:
                    player['ready'] = ready
                    await manager.send_to_room(room_id, 'playerReady', {
                        'playerId': player_id, 'ready': ready, 'players': game_state['players']
                    })
                    await broadcast_room_state(room_id, rooms, manager)

                    if force_start or (len(game_state['players']) >= 1 and all(p['ready'] for p in game_state['players'])):
                        await start_game(room_id, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))

            elif event == 'placeHeadman':
                area_index = payload.get('areaIndex')
                slot_index = payload.get('slotIndex')

                game_state = rooms.get(room_id)
                if not game_state or game_state.get('status') != 'playing':
                    await websocket.send_json({'event': 'error', 'data': {'message': '游戏未开始'}})
                    continue

                if player_id != game_state.get('currentPlayerIndex'):
                    await websocket.send_json({'event': 'error', 'data': {'message': '不是你的回合'}})
                    continue

                player = game_state['players'][player_id]
                if not player or player['headmen'] <= 0:
                    await websocket.send_json({'event': 'error', 'data': {'message': '没有米宝了'}})
                    continue

                area_name = AREAS[area_index]
                area_data = game_state['areas'].get(area_name)
                if not area_data:
                    await websocket.send_json({'event': 'error', 'data': {'message': '区域不存在'}})
                    continue

                slots = area_data['slots']
                if isinstance(slots[0], dict) if slots else True:
                    if slot_index < 0 or slot_index >= len(slots) or slots[slot_index].get('occupiedBy') is not None:
                        await websocket.send_json({'event': 'error', 'data': {'message': '该位置已有米宝'}})
                        continue
                    player['headmen'] -= 1
                    slots[slot_index]['occupiedBy'] = player_id
                else:
                    if slot_index < 0 or slot_index >= len(slots) or slots[slot_index] is not None:
                        await websocket.send_json({'event': 'error', 'data': {'message': '该位置已有米宝'}})
                        continue
                    player['headmen'] -= 1
                    slots[slot_index] = player_id

                await manager.send_to_room(room_id, 'headmanPlaced', {
                    'playerId': player_id, 'areaIndex': area_index, 'slotIndex': slot_index, 'gameState': game_state
                })
                await broadcast_room_state(room_id, rooms, manager)

            elif event == 'nextPlayer':
                print(f"DEBUG: nextPlayer event handler triggered for player {player_id} in room {room_id}")
                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                if player_id != game_state.get('currentPlayerIndex', 0):
                    await websocket.send_json({'event': 'error', 'data': {'message': '不是你的回合'}})
                    continue

                all_placed = all(p['headmen'] == 0 for p in game_state['players'])

                if all_placed:
                    game_state['phase'] = 'settlement'
                    game_state['currentArea'] = 0
                    resolve_area(game_state, 0, AREAS)
                    print(f"All players placed, phase changed to settlement")
                else:
                    current_idx = game_state.get('currentPlayerIndex', 0)
                    game_state['currentPlayerIndex'] = (current_idx + 1) % len(game_state['players'])
                    print(f"Next player: {game_state['currentPlayerIndex']}")

                await manager.send_to_room(room_id, 'playerTurn', {
                    'currentPlayerIndex': game_state.get('currentPlayerIndex', 0), 'gameState': game_state
                })
                await broadcast_room_state(room_id, rooms, manager)

            elif event == 'nextArea':
                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                current_area = game_state.get('currentArea', 0)

                for area_name in AREAS:
                    if area_name in game_state['areas']:
                        slots = game_state['areas'][area_name]['slots']
                        if isinstance(slots, list) and len(slots) > 0:
                            if isinstance(slots[0], dict):
                                game_state['areas'][area_name]['slots'] = [
                                    {**slot, 'occupiedBy': None} for slot in slots
                                ]
                            else:
                                game_state['areas'][area_name]['slots'] = [None] * len(slots)

                for p in game_state['players']:
                    p['headmen'] = min(p['headmen'] + 1, 5)

                if current_area + 1 >= len(AREAS):
                    await handle_next_round(room_id, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))
                else:
                    current_area += 1
                    game_state['currentArea'] = current_area
                    resolve_area(game_state, current_area, AREAS)

                    await manager.send_to_room(room_id, 'areaSettled', {
                        'areaIndex': current_area, 'gameState': game_state
                    })
                    await broadcast_room_state(room_id, rooms, manager)

            elif event == 'nextRound':
                await handle_next_round(room_id, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))

            elif event == 'exchangeSignals':
                exchange_type = payload.get('exchangeType')

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                player = game_state['players'][player_id]

                if exchange_type == '1to1' and player['tempBubbles'] >= 1:
                    player['tempBubbles'] -= 1
                    player['gold'] += 1
                elif exchange_type == '2to3' and player['tempBubbles'] >= 2:
                    player['tempBubbles'] -= 2
                    player['shrimpPond']['grade3'] += 1
                elif exchange_type == '3to2' and player['tempBubbles'] >= 3:
                    player['tempBubbles'] -= 3
                    player['shrimpPond']['grade2'] += 1

                await manager.send_to_room(room_id, 'signalsExchanged', {
                    'playerId': player_id, 'gameState': game_state
                })
                await broadcast_room_state(room_id, rooms, manager)

            elif event == 'buyItem':
                item_type = payload.get('itemType')

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                player = game_state['players'][player_id]
                prices = game_state['areas']['market']['dynamicPrices']
                success = False

                if item_type == 'lobster' and player['gold'] >= prices['buyLobster']:
                    player['gold'] -= prices['buyLobster']
                    player['shrimpPond']['normal'] += 1
                    success = True
                elif item_type == 'seaweed' and player['gold'] >= prices['buySeaweed']:
                    player['gold'] -= prices['buySeaweed']
                    player['seaweed'] += 1
                    success = True
                elif item_type == 'cage' and player['gold'] >= prices['buyCage']:
                    player['gold'] -= prices['buyCage']
                    player['cages'] += 1
                    success = True
                elif item_type == 'headman' and player['gold'] >= prices['hireHeadman']:
                    player['gold'] -= prices['hireHeadman']
                    player['headmen'] += 1
                    success = True

                if success:
                    await manager.send_to_room(room_id, 'itemBought', {
                        'playerId': player_id, 'itemType': item_type, 'gameState': game_state
                    })
                    await broadcast_room_state(room_id, rooms, manager)
                else:
                    await websocket.send_json({'event': 'error', 'data': {'message': '资源不足'}})

            elif event == 'sellItem':
                item_type = payload.get('itemType')

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                player = game_state['players'][player_id]
                prices = game_state['areas']['market']['dynamicPrices']
                success = False

                if item_type == 'lobster' and player['shrimpPond']['normal'] > 0:
                    player['shrimpPond']['normal'] -= 1
                    player['gold'] += prices['sellLobster']
                    success = True
                elif item_type == 'seaweed' and player['seaweed'] > 0:
                    player['seaweed'] -= 1
                    player['gold'] += prices['sellSeaweed']
                    success = True
                elif item_type == 'cage' and player['cages'] > 0:
                    player['cages'] -= 1
                    player['gold'] += prices['sellCage']
                    success = True

                if success:
                    await manager.send_to_room(room_id, 'itemSold', {
                        'playerId': player_id, 'itemType': item_type, 'gameState': game_state
                    })
                    await broadcast_room_state(room_id, rooms, manager)
                else:
                    await websocket.send_json({'event': 'error', 'data': {'message': '物品不足'}})

            elif event == 'cultivateLobster':
                use_seaweed = payload.get('useSeaweed', False)

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                player = game_state['players'][player_id]
                upgraded = False

                if player['shrimpPond']['grade1'] > 0 and (player['cages'] > 0 or player['gold'] >= 3):
                    if player['cages'] > 0:
                        player['cages'] -= 1
                    else:
                        player['gold'] -= 3
                    player['shrimpPond']['grade1'] -= 1
                    player['shrimpPond']['royal'] += 1
                    if player['royalCountThisRound'] < 2:
                        player['shrimpPond']['titled'].append({'id': random.random(), 'skill': True})
                        player['royalCountThisRound'] += 1
                    upgraded = True
                elif player['shrimpPond']['grade2'] > 0:
                    player['shrimpPond']['grade2'] -= 1
                    player['shrimpPond']['grade1'] += 1
                    upgraded = True
                elif player['shrimpPond']['grade3'] > 0:
                    player['shrimpPond']['grade3'] -= 1
                    player['shrimpPond']['grade2'] += 1
                    upgraded = True
                elif player['shrimpPond']['normal'] > 0:
                    player['shrimpPond']['normal'] -= 1
                    player['shrimpPond']['grade3'] += 1
                    upgraded = True

                await manager.send_to_room(room_id, 'lobsterCultivated', {
                    'playerId': player_id, 'upgraded': upgraded, 'gameState': game_state
                })
                await broadcast_room_state(room_id, rooms, manager)

            elif event == 'submitTribute':
                task_id = payload.get('taskId')

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                player = game_state['players'][player_id]

                task = next((t for t in game_state['tributeTasks'] if str(t['id']) == str(task_id)), None)
                if not task:
                    await websocket.send_json({'event': 'error', 'data': {'message': '任务不存在'}})
                    continue

                if 'completedTaverns' not in player:
                    player['completedTaverns'] = []

                tavern_id = task.get('tavernId')
                if tavern_id and tavern_id in player['completedTaverns']:
                    await websocket.send_json({'event': 'error', 'data': {'message': '您已经在此酒楼完成过上供'}})
                    continue

                req = task['requirement']
                can_submit = True

                if req.get('shrimp'):
                    if req['shrimp'].get('common') and player['shrimpPond']['normal'] < req['shrimp']['common']: can_submit = False
                    if req['shrimp'].get('third') and player['shrimpPond']['grade3'] < req['shrimp']['third']: can_submit = False
                    if req['shrimp'].get('second') and player['shrimpPond']['grade2'] < req['shrimp']['second']: can_submit = False
                    if req['shrimp'].get('first') and player['shrimpPond']['grade1'] < req['shrimp']['first']: can_submit = False
                    if req['shrimp'].get('royal') and player['shrimpPond']['royal'] < req['shrimp']['royal']: can_submit = False
                else:
                    if req.get('grade2') and player['shrimpPond']['grade2'] < req['grade2']: can_submit = False
                    if req.get('grade1') and player['shrimpPond']['grade1'] < req['grade1']: can_submit = False
                    if req.get('royal') and player['shrimpPond']['royal'] < req['royal']: can_submit = False

                if req.get('seaweed') and player['seaweed'] < req['seaweed']: can_submit = False
                if req.get('gold') and player['gold'] < req['gold']: can_submit = False
                if req.get('cage') and player['cages'] < req['cage']: can_submit = False

                if not can_submit:
                    await websocket.send_json({'event': 'error', 'data': {'message': '资源不足'}})
                    continue

                if req.get('shrimp'):
                    if req['shrimp'].get('common'): player['shrimpPond']['normal'] -= req['shrimp']['common']
                    if req['shrimp'].get('third'): player['shrimpPond']['grade3'] -= req['shrimp']['third']
                    if req['shrimp'].get('second'): player['shrimpPond']['grade2'] -= req['shrimp']['second']
                    if req['shrimp'].get('first'): player['shrimpPond']['grade1'] -= req['shrimp']['first']
                    if req['shrimp'].get('royal'): player['shrimpPond']['royal'] -= req['shrimp']['royal']
                else:
                    if req.get('grade2'): player['shrimpPond']['grade2'] -= req['grade2']
                    if req.get('grade1'): player['shrimpPond']['grade1'] -= req['grade1']
                    if req.get('royal'): player['shrimpPond']['royal'] -= req['royal']

                if req.get('seaweed'): player['seaweed'] -= req['seaweed']
                if req.get('gold'): player['gold'] -= req['gold']
                if req.get('cage'): player['cages'] -= req['cage']

                if task['reward'].get('de') is not None: player['virtue'] += task['reward']['de']
                if task['reward'].get('wang') is not None: player['reputation'] += task['reward']['wang']
                if task['reward'].get('virtue') is not None: player['virtue'] += task['reward']['virtue']
                if task['reward'].get('reputation') is not None: player['reputation'] += task['reward']['reputation']
                if task['reward'].get('gold') is not None: player['gold'] += task['reward']['gold']

                if task['reward'].get('incomeBonus'): player['incomePerRound'] += task['reward']['incomeBonus']

                if 'completedTasks' not in player:
                    player['completedTasks'] = []
                player['completedTasks'].append(task_id)

                if tavern_id and tavern_id not in player['completedTaverns']:
                    player['completedTaverns'].append(tavern_id)

                aura = task.get('aura')
                if aura:
                    if 'permaBuffs' not in player:
                        player['permaBuffs'] = []
                    if aura.get('type') == 'permanent' and aura.get('effect') and aura['effect'] not in player['permaBuffs']:
                        player['permaBuffs'].append(aura['effect'])

                await manager.send_to_room(room_id, 'tributeSubmitted', {
                    'playerId': player_id, 'taskId': task_id, 'gameState': game_state
                })
                await broadcast_room_state(room_id, rooms, manager)

            elif event == 'executeDowntownAction':
                card_index = payload.get('cardIndex')

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                player = game_state['players'][player_id]
                card = game_state['downtownCards'][card_index] if card_index < len(game_state['downtownCards']) else None
                if not card:
                    await websocket.send_json({'event': 'error', 'data': {'message': '卡牌不存在'}})
                    continue

                if 'action' in card:
                    cost = card.get('action', {}).get('cost', {})
                    reward = card.get('action', {}).get('reward', {})

                    has_resources = True
                    if cost.get('gold') and player['gold'] < cost['gold']: has_resources = False
                    if cost.get('shrimp', {}).get('common') and player['shrimpPond']['normal'] < cost['shrimp']['common']: has_resources = False
                    if cost.get('shrimp', {}).get('third') and player['shrimpPond']['grade3'] < cost['shrimp']['third']: has_resources = False
                    if cost.get('shrimp', {}).get('second') and player['shrimpPond']['grade2'] < cost['shrimp']['second']: has_resources = False
                    if cost.get('shrimp', {}).get('first') and player['shrimpPond']['grade1'] < cost['shrimp']['first']: has_resources = False
                    if cost.get('shrimp', {}).get('royal') and player['shrimpPond']['royal'] < cost['shrimp']['royal']: has_resources = False
                    if cost.get('seaweed') and player['seaweed'] < cost['seaweed']: has_resources = False
                    if cost.get('cage') and player['cages'] < cost['cage']: has_resources = False

                    if not has_resources:
                        await websocket.send_json({'event': 'error', 'data': {'message': '资源不足'}})
                        continue

                    if cost.get('gold'): player['gold'] -= cost['gold']
                    if cost.get('shrimp', {}).get('common'): player['shrimpPond']['normal'] -= cost['shrimp']['common']
                    if cost.get('shrimp', {}).get('third'): player['shrimpPond']['grade3'] -= cost['shrimp']['third']
                    if cost.get('shrimp', {}).get('second'): player['shrimpPond']['grade2'] -= cost['shrimp']['second']
                    if cost.get('shrimp', {}).get('first'): player['shrimpPond']['grade1'] -= cost['shrimp']['first']
                    if cost.get('shrimp', {}).get('royal'): player['shrimpPond']['royal'] -= cost['shrimp']['royal']
                    if cost.get('seaweed'): player['seaweed'] -= cost['seaweed']
                    if cost.get('cage'): player['cages'] -= cost['cage']

                    if reward.get('gold') is not None: player['gold'] += reward['gold']
                    if reward.get('virtue'): player['virtue'] += reward['virtue']
                    if reward.get('reputation'): player['reputation'] += reward['reputation']
                    if reward.get('seaweed'): player['seaweed'] += reward['seaweed']
                    if reward.get('cage'): player['cages'] += reward['cage']
                    if reward.get('shrimp'):
                        if reward['shrimp'].get('common'): player['shrimpPond']['normal'] += reward['shrimp']['common']
                        if reward['shrimp'].get('third'): player['shrimpPond']['grade3'] += reward['shrimp']['third']
                        if reward['shrimp'].get('second'): player['shrimpPond']['grade2'] += reward['shrimp']['second']
                        if reward['shrimp'].get('first'): player['shrimpPond']['grade1'] += reward['shrimp']['first']
                        if reward['shrimp'].get('royal'): player['shrimpPond']['royal'] += reward['shrimp']['royal']
                else:
                    if card['type'] == 'gold': player['gold'] += card['effect']
                    elif card['type'] == 'seaweed': player['seaweed'] += card['effect']
                    elif card['type'] == 'virtue': player['virtue'] += card['effect']
                    elif card['type'] == 'reputation': player['reputation'] += card['effect']
                    elif card['type'] == 'cage': player['cages'] += card['effect']
                    elif card['type'] == 'signal': player['signals'] += card['effect']

                await manager.send_to_room(room_id, 'downtownActionExecuted', {
                    'playerId': player_id, 'card': card, 'gameState': game_state
                })
                await broadcast_room_state(room_id, rooms, manager)

            elif event == 'lobsterBattleInvite':
                target_player_id = payload.get('targetPlayerId')
                lobster_data = payload.get('lobster')

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                inviter = game_state['players'][player_id] if player_id < len(game_state['players']) else None
                if not inviter:
                    continue

                await manager.send_to_player(room_id, target_player_id, 'lobsterBattleInvite', {
                    'inviter': inviter,
                    'lobster': lobster_data
                })

            elif event == 'lobsterBattleResponse':
                accept = payload.get('accept')
                lobster_data = payload.get('lobster')
                target_player_id = payload.get('targetPlayerId')

                game_state = rooms.get(room_id)
                if not game_state:
                    continue

                responder = game_state['players'][player_id] if player_id < len(game_state['players']) else None
                if not responder:
                    continue

                await manager.send_to_player(room_id, target_player_id, 'lobsterBattleResponse', {
                    'accept': accept,
                    'responder': responder,
                    'lobster': lobster_data
                })

            elif event == 'battleStart':
                battle_data = payload.get('battleData')

                await manager.send_to_room(room_id, 'battleStart', {
                    'battleData': battle_data,
                    'initiatorId': player_id
                })

            elif event == 'battleAction':
                action_type = payload.get('actionType')
                battle_data = payload.get('battleData')
                sender_id = payload.get('senderId')

                # 处理 battleEnd 事件，检查是否需要交换 slot
                if action_type == 'battleEnd':
                    game_state = rooms.get(room_id)
                    if game_state:
                        winner_id = battle_data.get('winner', {}).get('id')
                        challenge_slot = battle_data.get('challengeSlotIndex')
                        
                        # 获取 challengerId - 根据 battle_data 中的 players 数组判断
                        players_data = battle_data.get('players', [])
                        challenger_id = None
                        if len(players_data) >= 2:
                            # players[0] 是 challenger (左侧), players[1] 是 defender (右侧)
                            challenger_id = players_data[0]['id']
                        
                        # 如果 challenger 获胜，交换 slot
                        if winner_id == challenger_id and challenge_slot:
                            tribute_data = game_state['areas'].get('tribute')
                            if tribute_data:
                                slots = tribute_data.get('slots', [])
                                challenge_slots = tribute_data.get('challengeSlots', [])
                                
                                # challengeSlot 3→defenderSlot 0, 4→1, 5→2
                                slot_map = {3: 0, 4: 1, 5: 2}
                                defender_idx = slot_map.get(challenge_slot)
                                
                                if defender_idx is not None and defender_idx < len(slots) and defender_idx < len(challenge_slots):
                                    # 交换 slot
                                    slots[defender_idx], challenge_slots[defender_idx] = \
                                        challenge_slots[defender_idx], slots[defender_idx]
                                    print(f"[battleEnd] Slot swapped: challenger wins at slot {challenge_slot}")

                await manager.send_to_room(room_id, 'battleAction', {
                    'actionType': action_type,
                    'battleData': battle_data,
                    'senderId': sender_id
                })

            elif event == 'lobsterSelected':
                lobster_data = payload.get('lobster')

                print(f"[lobsterSelected] Player {player_id} selected lobster in room {room_id}")
                print(f"[lobsterSelected] Broadcasting to room members...")

                # 广播玩家的龙虾选择给房间内所有玩家
                await manager.send_to_room(room_id, 'lobsterSelected', {
                    'playerId': player_id,
                    'lobster': lobster_data
                })
                print(f"[lobsterSelected] Broadcast complete")

            elif event == 'leaveRoom':
                game_state = rooms.get(room_id)
                player_name = None

                if game_state:
                    player = next((p for p in game_state['players'] if p['id'] == player_id), None)
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
                break

    except WebSocketDisconnect:
        print(f"DEBUG: WebSocketDisconnect for player {player_id} in room {room_id}")
        manager.disconnect(room_id, player_id, fingerprint)
        await handle_player_disconnect(room_id, player_id, None, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))
