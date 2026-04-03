# -*- coding: utf-8 -*-
"""
游戏逻辑服务模块
"""

from typing import Dict
from utils.constants import AREAS, MARKET_PRICES
from utils.events import ServerEvents, ServerRoomActionTypes, ServerGameActionTypes
from utils.game_state import draw_tribute_tasks, draw_downtown_cards


def _srg(action_type, data):
    """构造 serverGameAction 消息体"""
    return {'actionType': action_type, **data}


def _srr(action_type, data):
    """构造 serverRoomAction 消息体"""
    return {'actionType': action_type, **data}


def update_market_prices(game_state: dict):
    """根据市场龙虾数量更新动态价格"""
    market_area = game_state['areas']['seafood_market']
    count = market_area['marketLobsterCount']

    if count > 5:
        market_area['dynamicPrices'] = {
            **MARKET_PRICES,
            'buyLobster': 1,
            'sellLobster': 1,
            'buyCage': 4,
            'sellCage': 3
        }
    elif count > 3:
        market_area['dynamicPrices'] = {
            **MARKET_PRICES,
            'buyLobster': 2,
            'sellLobster': 2,
            'buyCage': 3,
            'sellCage': 2
        }
    else:
        market_area['dynamicPrices'] = {
            **MARKET_PRICES,
            'buyLobster': 3,
            'sellLobster': 3,
            'buyCage': 2,
            'sellCage': 1
        }


def prepare_phase(game_state: dict):
    """准备阶段处理"""
    game_state['areas']['shrimp_catching']['wildLobsterPool'] = 8
    update_market_prices(game_state)


def cleanup_phase(game_state: dict):
    """清理阶段处理（对齐单机 executeCleanupPhase）"""
    market_area = game_state['areas']['seafood_market']

    if market_area['marketLobsterCount'] > 0:
        market_area['marketLobsterCount'] = 0

    for player in game_state['players']:
        base_headmen = 3
        hired_count = len(player.get('hiredLaborersBonus', []))
        player['liZhang'] = base_headmen + hired_count

    for player in game_state['players']:
        player['coins'] += 2 + player.get('bonusGold', 0)

    if 'taverns' in game_state:
        for tavern in game_state['taverns']:
            tavern['cards'] = []
            tavern['occupants'] = []

    update_market_prices(game_state)


def cleanup_room(room_id: str, rooms: dict, manager):
    """清理房间及其相关连接"""
    if room_id in rooms:
        del rooms[room_id]

        for user_id in list(manager.user_rooms.keys()):
            if manager.user_rooms.get(user_id) == room_id:
                manager.user_rooms.pop(user_id, None)
                manager.lobby_connections.pop(user_id, None)

        if room_id in manager.active_connections:
            del manager.active_connections[room_id]

        from utils.game_state import arena_betting_state
        for key in list(arena_betting_state.keys()):
            if key.startswith(f"{room_id}_"):
                del arena_betting_state[key]

        print(f"Room {room_id} deleted")


def transfer_host(room_id: str, game_state: dict):
    """转移房主身份"""
    if not game_state or game_state['status'] != 'waiting':
        return

    online_players = [p for p in game_state['players'] if p.get('isOnline')]
    if not online_players:
        return

    current_host = next((p for p in game_state['players'] if p.get('isHost')), None)

    if current_host and current_host.get('isOnline'):
        return

    new_host = online_players[0]
    if current_host:
        current_host['isHost'] = False
    new_host['isHost'] = True
    print(f"Host transferred to {new_host['name']} in room {room_id}")


async def handle_player_disconnect(room_id: str, player_id: int, player_name: str, rooms: dict, manager, broadcast_func):
    """处理玩家断开连接"""
    print(f"DEBUG: handle_player_disconnect called for room {room_id}, player {player_id}")

    game_state = rooms.get(room_id)
    if not game_state:
        print(f"DEBUG: game_state not found in handle_player_disconnect for room {room_id}")
        return

    if player_name is None and player_id is not None:
        player = next((p for p in game_state['players'] if p['id'] == player_id), None)
        if player:
            player_name = player.get('name')
            player['isOnline'] = False
            player['ready'] = False
            player['lastSeen'] = int(__import__('time').time())

    transfer_host(room_id, game_state)

    all_offline = all(not p.get('isOnline', True) for p in game_state['players'])

    await broadcast_func(room_id)

    if all_offline:
        cleanup_room(room_id, rooms, manager)
        return

    await manager.broadcast_to_room_members(room_id, ServerEvents.SERVER_ROOM_ACTION,
        _srr(ServerRoomActionTypes.PLAYER_STATUS_CHANGE, {
            'playerId': player_id,
            'playerName': player_name,
            'status': 'offline',
            'players': game_state['players']
        }))


async def broadcast_room_state(room_id: str, rooms: dict, manager):
    """广播房间级状态 (players, status) - 不含游戏运行时数据"""
    game_state = rooms.get(room_id)
    if game_state:
        data = {
            'players': game_state.get('players', []),
            'status': game_state['status'],
            'maxPlayers': game_state.get('maxPlayers', 4)
        }
        await manager.send_to_room(room_id, ServerEvents.SERVER_ROOM_ACTION,
            _srr(ServerRoomActionTypes.ROOM_STATE_UPDATE, data))


async def broadcast_game_state(room_id: str, rooms: dict, manager):
    """广播游戏运行时状态 (phase, round, currentPlayer, areas)"""
    game_state = rooms.get(room_id)
    if game_state:
        data = {
            'phase': game_state.get('phase', 'waiting'),
            'currentRound': game_state.get('currentRound', 1),
            'currentPlayerIndex': game_state.get('currentPlayerIndex', 0),
            'currentArea': game_state.get('currentArea', 0),
            'areas': game_state.get('areas', {}),
            'status': game_state['status']
        }
        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            _srg(ServerGameActionTypes.GAME_STATE_UPDATE, data))


async def start_game(room_id: str, rooms: dict, manager):
    """开始游戏"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    game_state['status'] = 'playing'
    game_state['phase'] = 'placement'
    game_state['currentRound'] = 1
    game_state['lastPlacement'] = None

    starting_player_idx = 0
    for idx, player in enumerate(game_state['players']):
        if player.get('isStartingPlayer', False):
            starting_player_idx = idx
            break

    game_state['currentPlayerIndex'] = starting_player_idx

    for p in game_state['players']:
        p['bubbles'] = 0
        p['ready'] = False

    for area_name in AREAS:
        if area_name in game_state['areas']:
            slot_count = len(game_state['areas'][area_name]['slots'])
            game_state['areas'][area_name]['slots'] = [None] * slot_count

    draw_tribute_tasks(game_state)
    draw_downtown_cards(game_state)

    print(f"start_game: Sending gameStarted to room {room_id}")
    print(f"  game_state['status'] = {game_state['status']}")
    print(f"  game_state['phase'] = {game_state['phase']}")
    print(f"  game_state['currentPlayerIndex'] = {game_state['currentPlayerIndex']}")
    print(f"  players in room: {len(game_state['players'])}")
    print(f"  active_connections: {list(manager.active_connections.get(room_id, {}).keys())}")

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        _srg(ServerGameActionTypes.GAME_STARTED, game_state))
    await broadcast_game_state(room_id, rooms, manager)
    print(f"Game started in room {room_id}")


async def next_round(room_id: str, rooms: dict, manager):
    """处理下一回合"""
    from services.area import resolve_area

    game_state = rooms.get(room_id)
    if not game_state:
        return

    if game_state['currentRound'] >= game_state['maxRounds']:
        game_state['status'] = 'ended'

        winner = sorted(
            game_state['players'],
            key=lambda x: (x['de'] * x['wang'] + x['bonusPoints'], x['coins']),
            reverse=True
        )[0]

        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            _srg(ServerGameActionTypes.GAME_ENDED, {'winner': winner, 'gameState': game_state}))
        return

    game_state['currentRound'] += 1
    game_state['phase'] = 'placement'
    game_state['currentPlayerIndex'] = 0
    game_state['currentArea'] = 0
    game_state['lastPlacement'] = None

    for p in game_state['players']:
        p['royalCountThisRound'] = 0
        p['coins'] += 2 + p['bonusGold']

    for area_name in AREAS:
        if area_name in game_state['areas']:
            slot_count = len(game_state['areas'][area_name]['slots'])
            game_state['areas'][area_name]['slots'] = [None] * slot_count

    draw_tribute_tasks(game_state)
    draw_downtown_cards(game_state)

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        _srg(ServerGameActionTypes.ROUND_STARTED, {'round': game_state['currentRound'], 'gameState': game_state}))
    await broadcast_game_state(room_id, rooms, manager)
