# -*- coding: utf-8 -*-
"""
WebSocket控制器模块
- handle_lobby_websocket: 大厅事件处理
- handle_game_websocket: 游戏房间事件分发器

事件分类:
  房间管理: clientRoomAction -> room_action_handler
  游戏行动: clientGameAction -> game_action_handler
  战斗相关: clientBattleAction -> battle_action_handler
"""

import time
from fastapi import WebSocket, WebSocketDisconnect
from utils.events import ClientEvents, ServerEvents, ServerRoomActionTypes, ClientRoomActionTypes
from utils.helpers import get_player
from services.game import handle_player_disconnect, broadcast_room_state
from controllers.room_action_handler import handle_room_action
from controllers.game_action_handler import handle_game_action
from controllers.battle_action_handler import handle_battle_action
from controllers.room_action_handler import handle_set_ready, handle_leave_room


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
                result = await handle_room_action(websocket, rooms, manager, payload)
                if result is False:
                    break
                continue

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
      - clientGameAction: 按 action_type 分发 (useSeaweed, placeHeadman, nextPlayer, nextArea, exchangeSignals,
                        buyItem, sellItem, cultivateLobster, submitTribute, executeDowntownAction, areaAction)
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

            # clientRoomAction 路由
            if event == ClientEvents.CLIENT_ROOM_ACTION:
                if _check_idempotency(player_id, ClientEvents.CLIENT_ROOM_ACTION, payload):
                    continue
                action_type = payload.get('action_type')
                result = None
                if action_type == ClientRoomActionTypes.LEAVE_ROOM:
                    result = await handle_leave_room(websocket, room_id, player_id, rooms, manager, payload, fingerprint)
                elif action_type == ClientRoomActionTypes.SET_READY:
                    result = await handle_set_ready(websocket, room_id, player_id, rooms, manager, payload)
                if result is False:
                    break
                continue

            # clientBattleAction 路由
            if event == ClientEvents.CLIENT_BATTLE_ACTION:
                if _check_idempotency(player_id, ClientEvents.CLIENT_BATTLE_ACTION, payload):
                    continue
                result = await handle_battle_action(websocket, room_id, player_id, rooms, manager, payload)
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