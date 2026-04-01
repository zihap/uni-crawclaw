# -*- coding: utf-8 -*-
"""
WebSocket控制器模块
- handle_lobby_websocket: 大厅事件处理
- handle_game_websocket: 游戏房间事件分发器（具体逻辑见 game_handlers.py）

事件分类:
  房间管理: clientRoomAction (action_type: leaveRoom, setReady)
  游戏行动: clientGameAction (按 actionType 路由到具体 handler)
  战斗相关: clientBattleAction (action_type: battleStart, lobsterSelected, spectatorBet, noLobsterForfeit)
"""

import time
from fastapi import WebSocket, WebSocketDisconnect
from utils.events import ClientEvents, ServerEvents, ServerRoomActionTypes, ClientRoomActionTypes
from utils.helpers import generate_room_id, get_player
from utils.game_state import create_game_state, create_player
from services.game import broadcast_room_state, handle_player_disconnect
from controllers.game_handlers import GAME_EVENT_HANDLERS, _check_idempotency
from controllers.game_action_handler import handle_game_action


def _sr(action_type, data):
    """构造 serverRoomAction 消息体"""
    return {'actionType': action_type, **data}


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

            if event == ClientEvents.HEARTBEAT:
                manager.heartbeat_timestamps[fingerprint] = time.time()
                await websocket.send_json({
                    'event': ServerEvents.HEARTBEAT_ACK,
                    'data': {'timestamp': int(time.time())}
                })

            # clientRoomAction 路由
            elif event == ClientEvents.CLIENT_ROOM_ACTION:
                action_type = payload.get('action_type')

                if action_type == ClientRoomActionTypes.CREATE_ROOM:
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
                        'event': ServerEvents.SERVER_ROOM_ACTION,
                        'data': _sr(ServerRoomActionTypes.ROOM_CREATED, {
                            'roomId': new_room_id, 'playerId': 0, 'gameState': game_state
                        })
                    })
                    print(f"Room {new_room_id} created by {player_name}")

                elif action_type == ClientRoomActionTypes.JOIN_ROOM:
                    room_id = payload.get('roomId')
                    player_name = payload.get('playerName')
                    user_id = payload.get('userId')

                    game_state = rooms.get(room_id)

                    if not game_state:
                        await websocket.send_json({
                            'event': ServerEvents.ERROR,
                            'data': {'message': '房间不存在'}
                        })
                        continue

                    for p in game_state['players']:
                        if p.get('userId') == user_id:
                            p['isOnline'] = True
                            p['ready'] = False
                            manager.lobby_connections[user_id] = websocket
                            manager.user_rooms[user_id] = room_id
                            await websocket.send_json({
                                'event': ServerEvents.SERVER_ROOM_ACTION,
                                'data': _sr(ServerRoomActionTypes.PLAYER_RECONNECTED, {
                                    'player': p, 'players': game_state['players']
                                })
                            })
                            await manager.broadcast_to_room_members(room_id, ServerEvents.SERVER_ROOM_ACTION,
                                _sr(ServerRoomActionTypes.PLAYER_STATUS_CHANGE, {
                                    'playerId': p['id'],
                                    'playerName': p['name'],
                                    'status': 'online',
                                    'players': game_state['players']
                                }))
                            await manager.broadcast_to_room_members(room_id, ServerEvents.SERVER_ROOM_ACTION,
                                _sr(ServerRoomActionTypes.ROOM_STATE_UPDATE, {
                                    'players': game_state['players'],
                                    'gameStarted': False,
                                    'status': 'waiting',
                                    'maxPlayers': game_state.get('maxPlayers', 4)
                                }))
                            break
                    else:
                        max_players = game_state.get('maxPlayers', 4)
                        if len(game_state['players']) >= max_players:
                            await websocket.send_json({
                                'event': ServerEvents.ERROR,
                                'data': {'message': '房间已满'}
                            })
                            continue

                        if game_state['status'] != 'waiting':
                            await websocket.send_json({
                                'event': ServerEvents.ERROR,
                                'data': {'message': '游戏已开始'}
                            })
                            continue

                        new_player_id = len(game_state['players'])
                        player = create_player(new_player_id, player_name, False, user_id, position=new_player_id)
                        game_state['players'].append(player)

                        manager.lobby_connections[user_id] = websocket
                        manager.user_rooms[user_id] = room_id

                        await websocket.send_json({
                            'event': ServerEvents.SERVER_ROOM_ACTION,
                            'data': _sr(ServerRoomActionTypes.PLAYER_JOINED, {
                                'playerId': new_player_id, 'player': player, 'gameState': game_state
                            })
                        })

                        await manager.broadcast_to_room_members(room_id, ServerEvents.SERVER_ROOM_ACTION,
                            _sr(ServerRoomActionTypes.ROOM_STATE_UPDATE, {
                                'players': game_state['players'],
                                'gameStarted': False,
                                'status': 'waiting',
                                'maxPlayers': game_state.get('maxPlayers', 4)
                            }))
                        print(f"{player_name} joined room {room_id}")

            elif event == 'ping':
                await websocket.send_json({'event': ServerEvents.PONG, 'data': {}})

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
    """游戏房间WebSocket事件分发器

    事件路由:
      - heartbeat: 内联处理
      - clientRoomAction: 按 action_type 分发 (leaveRoom, setReady)
      - clientBattleAction: 按 action_type 分发 (battleStart, lobsterSelected, spectatorBet, noLobsterForfeit)
      - clientGameAction: 路由到 game_action_handler (按 actionType 分发)
    """
    fingerprint = id(websocket)

    print(f"WebSocket connection: room_id={room_id}, player_id={player_id}")
    print(f"DEBUG: rooms at connection time: {list(rooms.keys())}")

    await manager.connect(websocket, room_id, player_id)

    game_state = rooms.get(room_id)
    if game_state:
        player = get_player(game_state, player_id)
        if player:
            player['isOnline'] = True
            await manager.send_to_room(room_id, ServerEvents.SERVER_ROOM_ACTION,
                _sr(ServerRoomActionTypes.PLAYER_STATUS_CHANGE, {
                    'playerId': player_id,
                    'playerName': player['name'],
                    'status': 'online',
                    'players': game_state['players']
                }))

        await manager.send_to_player(room_id, player_id, ServerEvents.SERVER_ROOM_ACTION,
            _sr(ServerRoomActionTypes.ROOM_STATE_UPDATE, {
                'players': game_state['players'],
                'gameStarted': game_state['status'] == 'playing',
                'status': game_state['status'],
                'phase': game_state.get('phase', 'waiting'),
                'currentRound': game_state.get('currentRound', 1),
                'currentPlayerIndex': game_state.get('currentPlayerIndex', 0)
            }))

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get('event')
            payload = data.get('data', {})
            print(f"WebSocket message in room {room_id} from player {player_id}: event={event}, payload={payload}")

            if event == ClientEvents.HEARTBEAT:
                manager.heartbeat_timestamps[fingerprint] = time.time()
                await websocket.send_json({
                    'event': ServerEvents.HEARTBEAT_ACK,
                    'data': {'timestamp': int(time.time())}
                })
                continue

            # clientRoomAction / clientBattleAction 路由
            if event in (ClientEvents.CLIENT_ROOM_ACTION, ClientEvents.CLIENT_BATTLE_ACTION):
                action_type = payload.get('action_type')
                lookup_key = action_type
                if _check_idempotency(player_id, lookup_key, payload):
                    continue
                handler = GAME_EVENT_HANDLERS.get(lookup_key)
                if handler:
                    if handler == handle_leave_room_handler:
                        result = await handler(websocket, room_id, player_id, rooms, manager, payload, fingerprint)
                    else:
                        result = await handler(websocket, room_id, player_id, rooms, manager, payload)
                    if result is False:
                        break
                continue

            # clientGameAction 路由
            if event == ClientEvents.CLIENT_GAME_ACTION:
                if _check_idempotency(player_id, ClientEvents.CLIENT_GAME_ACTION, payload):
                    continue
                result = await handle_game_action(websocket, room_id, player_id, rooms, manager, payload)
                if result is False:
                    break
                continue

    except WebSocketDisconnect:
        print(f"DEBUG: WebSocketDisconnect for player {player_id} in room {room_id}")
        manager.disconnect(room_id, player_id, fingerprint)
        await handle_player_disconnect(room_id, player_id, None, rooms, manager, lambda r: broadcast_room_state(r, rooms, manager))


# 引用 game_handlers 中的 handle_leave_room，用于分发表中的特殊判断
from controllers.game_handlers import handle_leave_room as handle_leave_room_handler
