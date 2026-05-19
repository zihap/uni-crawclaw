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
from utils.error_codes import ErrorCodes
from utils.helpers import generate_room_id, get_player, send_error, make_action_message
from utils.logger import log_info
from utils.game_state import create_game_state, create_player
from services.game import broadcast_room_state, start_game, transfer_host, cleanup_room, cancel_pending_host_transfer


async def _add_player_to_room(websocket, rooms, manager, room_id, player_name, user_id, is_host=False):
    """将玩家加入房间的公共逻辑。返回 (game_state, error_response, is_reconnect)"""
    game_state = rooms.get(room_id)
    
    if not game_state:
        return None, {
            'event': ServerEvents.ERROR,
            'data': {
                'message': '房间不存在',
                'errorCode': ErrorCodes.ROOM_NOT_FOUND
            }
        }, False
    
    for p in game_state['players']:
        if p.get('userId') == user_id:
            p['isOnline'] = True
            p['ready'] = False
            cancel_pending_host_transfer(p['id'])
            manager.lobby_connections[user_id] = websocket
            manager.user_rooms[user_id] = room_id
            return game_state, None, True
    
    max_players = game_state.get('maxPlayers', 4)
    if len(game_state['players']) >= max_players:
        return None, {
            'event': ServerEvents.ERROR,
            'data': {
                'message': '房间已满',
                'errorCode': ErrorCodes.ROOM_FULL
            }
        }, False
    
    if game_state['status'] != 'waiting':
        return None, {
            'event': ServerEvents.ERROR,
            'data': {
                'message': '游戏已开始',
                'errorCode': ErrorCodes.GAME_STARTED
            }
        }, False
    
    # 找最小可用 ID，避免玩家离开后重新加入产生 ID 冲突
    used_ids = {p['id'] for p in game_state['players']}
    new_player_id = 0
    while new_player_id in used_ids:
        new_player_id += 1
    player = create_player(new_player_id, player_name, is_host, user_id, position=new_player_id)
    game_state['players'].append(player)
    
    manager.lobby_connections[user_id] = websocket
    manager.user_rooms[user_id] = room_id
    
    return game_state, None, False


async def _send_join_success(websocket, room_id, manager, game_state, is_reconnect=False, user_id=None):
    """发送加入成功消息并广播房间状态更新"""
    if is_reconnect and user_id:
        player = next((p for p in game_state['players'] if p.get('userId') == user_id), None)
        if not player:
            log_info(f"Warning: reconnect player with userId={user_id} not found, using last player as fallback")
            player = game_state['players'][-1]
    else:
        player = game_state['players'][-1]
    action_type = ServerRoomActionTypes.PLAYER_RECONNECTED if is_reconnect else ServerRoomActionTypes.PLAYER_JOINED
    
    await websocket.send_json({
        'event': ServerEvents.SERVER_ROOM_ACTION,
        'data': make_action_message(action_type, {
            'playerId': player['id'],
            'player': player,
            'gameState': game_state
        })
    })
    
    await manager.broadcast_to_room_members(room_id, ServerEvents.SERVER_ROOM_ACTION,
        make_action_message(ServerRoomActionTypes.ROOM_STATE_UPDATE, {
            'players': game_state['players'],
            'gameStarted': False,
            'status': 'waiting',
            'maxPlayers': game_state.get('maxPlayers', 4)
        }))


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
        'data': make_action_message(ServerRoomActionTypes.ROOM_CREATED, {
            'roomId': new_room_id, 'playerId': 0, 'gameState': game_state
        })
    })
    log_info(f"Room {new_room_id} created by {player_name}")


async def handle_join_room(websocket, rooms, manager, payload):
    """加入房间"""
    target_room_id = payload.get('roomId')
    player_name = payload.get('playerName')
    user_id = payload.get('userId')

    game_state, error, is_reconnect = await _add_player_to_room(websocket, rooms, manager, target_room_id, player_name, user_id)
    if error:
        await websocket.send_json(error)
        return
    
    await _send_join_success(websocket, target_room_id, manager, game_state, is_reconnect, user_id)
    log_info(f"{player_name} joined room {target_room_id}")


async def handle_leave_room(websocket, room_id, player_id, rooms, manager, payload, fingerprint):
    """离开房间"""
    game_state = rooms.get(room_id)
    if not game_state:
        try:
            await websocket.close()
        except Exception:
            pass
        return

    player = get_player(game_state, player_id)
    if not player:
        try:
            await websocket.close()
        except Exception:
            pass
        return

    player_name = player['name']
    player_user_id = player.get('userId')

    # 通知离开者
    try:
        await websocket.send_json({
            'event': ServerEvents.SERVER_ROOM_ACTION,
            'data': make_action_message(ServerRoomActionTypes.PLAYER_LEFT, {
                'message': '您已离开房间',
                'playerId': player_id
            })
        })
    except Exception:
        pass

    # 从游戏状态移除
    game_state['players'].remove(player)

    # 手动清理连接（不调用 manager.disconnect，避免误删其他玩家的 user_rooms）
    if room_id in manager.active_connections:
        manager.active_connections[room_id].pop(str(player_id), None)
        if not manager.active_connections[room_id]:
            del manager.active_connections[room_id]
    manager.heartbeat_timestamps.pop(fingerprint, None)

    # 清理 lobby 映射
    if player_user_id:
        manager.lobby_connections.pop(player_user_id, None)
        manager.user_rooms.pop(player_user_id, None)

    log_info(f"Player {player_name} left room {room_id}")

    # 房主转移 + 广播
    if game_state['players']:
        transfer_host(room_id, game_state)
        await broadcast_room_state(room_id, rooms, manager)
    else:
        cleanup_room(room_id, rooms, manager)

    # 关闭 WebSocket
    try:
        await websocket.close()
    except Exception:
        pass

    return False


async def handle_set_ready(websocket, room_id, player_id, rooms, manager, payload):
    """设置准备状态"""
    ready = payload.get('ready')

    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = get_player(game_state, player_id)
    if player:
        player['ready'] = ready
        await manager.send_to_room(room_id, ServerEvents.SERVER_ROOM_ACTION,
            make_action_message(ServerRoomActionTypes.PLAYER_READY, {
                'playerId': player_id, 'ready': ready, 'players': game_state['players']
            }))
        await broadcast_room_state(room_id, rooms, manager)


async def handle_start_game(websocket, room_id, player_id, rooms, manager, payload):
    """开始游戏（仅房主可用）"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = get_player(game_state, player_id)
    if not player or not player.get('isHost'):
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '只有房主可以开始游戏', 'errorCode': ErrorCodes.NOT_HOST}
        })
        return

    if game_state.get('status') != 'waiting':
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '游戏已开始', 'errorCode': ErrorCodes.GAME_STARTED}
        })
        return

    non_host_online = [p for p in game_state['players'] if not p.get('isHost') and p.get('isOnline') is not False]
    if not all(p.get('ready') for p in non_host_online):
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '有玩家未准备', 'errorCode': 'NOT_ALL_READY'}
        })
        return

    await start_game(room_id, rooms, manager)


async def handle_kick_player(websocket, room_id, player_id, rooms, manager, payload):
    """踢出玩家（仅房主可用）"""
    game_state = rooms.get(room_id)
    if not game_state:
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '房间不存在', 'errorCode': ErrorCodes.ROOM_NOT_FOUND}
        })
        return

    if game_state['status'] != 'waiting':
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '游戏已开始，无法踢人', 'errorCode': ErrorCodes.GAME_STARTED}
        })
        return

    kicker = get_player(game_state, player_id)
    if not kicker or not kicker.get('isHost'):
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '只有房主可以踢人', 'errorCode': ErrorCodes.NOT_HOST}
        })
        return

    target_player_id = payload.get('targetPlayerId')
    if target_player_id is None:
        await send_error(websocket, '缺少目标玩家ID')
        return

    target_player_id = int(target_player_id)

    if target_player_id == player_id:
        await websocket.send_json({
            'event': ServerEvents.ERROR,
            'data': {'message': '不能踢出自己', 'errorCode': ErrorCodes.CANNOT_KICK_SELF}
        })
        return

    target_player = get_player(game_state, target_player_id)
    if not target_player:
        await send_error(websocket, '目标玩家不存在')
        return

    # 通知被踢玩家
    target_ws = manager.active_connections.get(room_id, {}).get(str(target_player_id))
    if target_ws:
        try:
            await target_ws.send_json({
                'event': ServerEvents.SERVER_ROOM_ACTION,
                'data': make_action_message(ServerRoomActionTypes.PLAYER_KICKED, {
                    'message': '您已被房主移出房间'
                })
            })
        except Exception:
            pass

    # 关闭被踢玩家的 WebSocket
    if target_ws:
        try:
            await target_ws.close()
        except Exception:
            pass

    # 手动清理连接（不调用 manager.disconnect，避免误删踢人者的连接）
    if room_id in manager.active_connections:
        manager.active_connections[room_id].pop(str(target_player_id), None)
        if not manager.active_connections[room_id]:
            del manager.active_connections[room_id]
    if target_ws:
        manager.heartbeat_timestamps.pop(id(target_ws), None)

    # 清理 lobby 连接
    target_user_id = target_player.get('userId')
    if target_user_id:
        manager.lobby_connections.pop(target_user_id, None)
        manager.user_rooms.pop(target_user_id, None)

    # 从游戏状态移除
    game_state['players'].remove(target_player)
    log_info(f"Player {target_player.get('name')} kicked from room {room_id} by player {kicker['name']}")

    # 广播更新
    await broadcast_room_state(room_id, rooms, manager)

    # 房间空了则清理
    if not game_state['players']:
        cleanup_room(room_id, rooms, manager)


async def handle_invite_join(websocket, rooms, manager, payload):
    """处理邀请加入请求"""
    room_id = payload.get('roomId')
    player_name = payload.get('playerName')
    user_id = payload.get('userId')
    inviter = payload.get('inviter')
    
    game_state, error, is_reconnect = await _add_player_to_room(websocket, rooms, manager, room_id, player_name, user_id)
    if error:
        await websocket.send_json(error)
        return
    
    await _send_join_success(websocket, room_id, manager, game_state, is_reconnect, user_id)
    log_info(f"{player_name} joined room {room_id} via invite from {inviter}")


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
        ClientRoomActionTypes.INVITE_JOIN: handle_invite_join,
    }


handle_room_action = _make_room_action_router(get_room_action_handlers())
