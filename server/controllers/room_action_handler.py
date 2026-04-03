# -*- coding: utf-8 -*-
"""
房间行动路由器
将客户端发送的 clientRoomAction 事件按 action_type 分发到具体 handler

包含的事件:
  - CREATE_ROOM: 创建房间
  - JOIN_ROOM: 加入房间
  - LEAVE_ROOM: 离开房间
  - SET_READY: 设置准备状态
"""

from utils.events import ClientRoomActionTypes, ServerEvents, ServerRoomActionTypes
from utils.helpers import generate_room_id, get_player, send_error
from utils.game_state import create_game_state, create_player
from services.game import broadcast_room_state, start_game, transfer_host, cleanup_room

def _sr(action_type, data):
    """构造 serverRoomAction 消息体"""
    return {'actionType': action_type, **data}


async def handle_create_room(websocket, rooms, manager, payload):
    """创建房间"""
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


async def handle_join_room(websocket, rooms, manager, payload):
    """加入房间"""
    target_room_id = payload.get('roomId')
    player_name = payload.get('playerName')
    user_id = payload.get('userId')

    game_state = rooms.get(target_room_id)

    if not game_state:
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '房间不存在'}
        })
        return

    for p in game_state['players']:
        if p.get('userId') == user_id:
            p['isOnline'] = True
            p['ready'] = False
            manager.lobby_connections[user_id] = websocket
            manager.user_rooms[user_id] = target_room_id
            await websocket.send_json({
                'event': ServerEvents.SERVER_ROOM_ACTION,
                'data': _sr(ServerRoomActionTypes.PLAYER_RECONNECTED, {
                    'player': p, 'players': game_state['players']
                })
            })
            await manager.broadcast_to_room_members(target_room_id, ServerEvents.SERVER_ROOM_ACTION,
                _sr(ServerRoomActionTypes.PLAYER_STATUS_CHANGE, {
                    'playerId': p['id'],
                    'playerName': p['name'],
                    'status': 'online',
                    'players': game_state['players']
                }))
            await manager.broadcast_to_room_members(target_room_id, ServerEvents.SERVER_ROOM_ACTION,
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
            return

        if game_state['status'] != 'waiting':
            await websocket.send_json({
                'event': ServerEvents.ERROR,
                'data': {'message': '游戏已开始'}
            })
            return

        new_player_id = len(game_state['players'])
        player = create_player(new_player_id, player_name, False, user_id, position=new_player_id)
        game_state['players'].append(player)

        manager.lobby_connections[user_id] = websocket
        manager.user_rooms[user_id] = target_room_id

        await websocket.send_json({
            'event': ServerEvents.SERVER_ROOM_ACTION,
            'data': _sr(ServerRoomActionTypes.PLAYER_JOINED, {
                'playerId': new_player_id, 'player': player, 'gameState': game_state
            })
        })

        await manager.broadcast_to_room_members(target_room_id, ServerEvents.SERVER_ROOM_ACTION,
            _sr(ServerRoomActionTypes.ROOM_STATE_UPDATE, {
                'players': game_state['players'],
                'gameStarted': False,
                'status': 'waiting',
                'maxPlayers': game_state.get('maxPlayers', 4)
            }))
        print(f"{player_name} joined room {target_room_id}")


async def handle_leave_room(websocket, room_id, player_id, rooms, manager, payload, fingerprint):
    """离开房间"""
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
                _sr(ServerRoomActionTypes.PLAYER_STATUS_CHANGE, {
                    'playerId': player_id, 'playerName': player_name,
                    'status': 'offline', 'players': game_state['players']
                }))
        else:
            cleanup_room(room_id, rooms, manager)

    try:
        await websocket.close()
    except Exception:
        pass


async def handle_set_ready(websocket, room_id, player_id, rooms, manager, payload):
    """设置准备状态"""
    ready = payload.get('ready')
    force_start = payload.get('forceStart', False)

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = get_player(game_state, player_id)
    if player:
        player['ready'] = ready
        await manager.send_to_room(room_id, ServerEvents.SERVER_ROOM_ACTION,
            _sr(ServerRoomActionTypes.PLAYER_READY, {
                'playerId': player_id, 'ready': ready, 'players': game_state['players']
            }))
        await broadcast_room_state(room_id, rooms, manager)

        if force_start or (len(game_state['players']) >= 1 and all(p['ready'] for p in game_state['players'])):
            await start_game(room_id, rooms, manager)


def _make_room_action_router(handlers: dict):
    """创建房间行动路由函数"""
    async def handle_room_action_router(websocket, rooms, manager, payload):
        action_type = payload.get('action_type')
        handler = handlers.get(action_type)
        if handler:
            return await handler(websocket, rooms, manager, payload)
        await send_error(websocket, f'未知的房间行动: {action_type}')
    return handle_room_action_router


def get_room_action_handlers():
    """获取房间行动处理器映射"""
    return {
        ClientRoomActionTypes.CREATE_ROOM: handle_create_room,
        ClientRoomActionTypes.JOIN_ROOM: handle_join_room,
    }


handle_room_action = _make_room_action_router(get_room_action_handlers())
