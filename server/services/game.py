# -*- coding: utf-8 -*-
"""
游戏逻辑服务模块
"""

from typing import Dict
from utils.constants import AREAS, MARKET_PRICES
from utils.game_state import draw_tribute_tasks, draw_downtown_cards


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
    """清理阶段处理"""
    fishing_area = game_state['areas']['shrimp_catching']
    market_area = game_state['areas']['seafood_market']

    # 将野生龙虾池的龙虾转移到市场
    market_area['marketLobsterCount'] += fishing_area['wildLobsterPool']
    fishing_area['wildLobsterPool'] = 0

    # 重置玩家里长数量（基础3个 + 额外雇佣的）
    for player in game_state['players']:
        base_headmen = 3
        hired_count = len(player.get('hiredLaborersBonus', []))
        player['liZhang'] = base_headmen + hired_count

    # 发放回合收入
    for player in game_state['players']:
        player['coins'] += player.get('bonusGold', 0)

    # 更新市场价格
    update_market_prices(game_state)

    game_state['currentRound'] += 1


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

    await manager.broadcast_to_room_members(room_id, 'playerOffline', {
        'playerId': player_id,
        'playerName': player_name,
        'players': game_state['players']
    })


async def broadcast_room_state(room_id: str, rooms: dict, manager):
    """广播房间状态到所有相关客户端"""
    game_state = rooms.get(room_id)
    if game_state:
        data = {
            'players': game_state['players'],
            'gameStarted': game_state['status'] == 'playing',
            'status': game_state['status'],
            'phase': game_state.get('phase', 'waiting'),
            'currentRound': game_state.get('currentRound', 1),
            'currentPlayerIndex': game_state.get('currentPlayerIndex', 0)
        }
        print(f"broadcast_room_state to room {room_id}: status={data['status']}, phase={data['phase']}, currentPlayerIndex={data['currentPlayerIndex']}")
        await manager.send_to_room(room_id, 'roomStateUpdate', data)


async def start_game(room_id: str, rooms: dict, manager, broadcast_func):
    """开始游戏"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    game_state['status'] = 'playing'
    game_state['phase'] = 'placement'
    game_state['currentRound'] = 1

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

    await manager.send_to_room(room_id, 'gameStarted', game_state)
    await broadcast_func(room_id)
    print(f"Game started in room {room_id}")


async def next_round(room_id: str, rooms: dict, manager, broadcast_func):
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

        await manager.send_to_room(room_id, 'gameEnded', {'winner': winner, 'gameState': game_state})
        return

    game_state['currentRound'] += 1
    game_state['phase'] = 'placement'
    game_state['currentPlayerIndex'] = 0
    game_state['currentArea'] = 0

    for p in game_state['players']:
        p['royalCountThisRound'] = 0
        p['coins'] += 2 + p['bonusGold']

    for area_name in AREAS:
        if area_name in game_state['areas']:
            slot_count = len(game_state['areas'][area_name]['slots'])
            game_state['areas'][area_name]['slots'] = [None] * slot_count

    draw_tribute_tasks(game_state)
    draw_downtown_cards(game_state)

    await manager.send_to_room(room_id, 'roundStarted', {'round': game_state['currentRound'], 'gameState': game_state})
    await broadcast_func(room_id)
