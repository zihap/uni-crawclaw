# -*- coding: utf-8 -*-
"""
游戏逻辑服务模块
"""

from typing import Dict
import time
from utils.constants import AREAS, MARKET_PRICES, CHALLENGE_SLOT_DONE
from utils.events import ServerEvents, ServerRoomActionTypes, ServerGameActionTypes, ServerAreaActionTypes
from utils.game_state import draw_tribute_tasks, draw_downtown_cards, draw_title_cards
from utils.logger import log_info, log_debug
from utils.helpers import make_action_message, calculate_market_prices
from services.tribute_card_effects import get_endgame_choices


def update_market_prices(game_state: dict):
    """根据市场龙虾数量更新动态价格"""
    market_area = game_state['areas']['seafood_market']
    market_area['dynamicPrices'] = calculate_market_prices(market_area['marketLobsterCount'])


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
        player['tributesThisRound'] = 0  # 重置进贡次数
        base_headmen = 3
        hired_count = len(player.get('hiredLaborersBonus', []))
        player['liZhang'] = base_headmen + hired_count
        # 处理闹市卡“客栈”的专属里长
        if player.get('inn_headman'):
            player['liZhang'] += 1
            player['inn_headman'] = False

    for player in game_state['players']:
        player['coins'] += 2 + player.get('bonusGold', 0)

    if 'taverns' in game_state:
        for tavern in game_state['taverns']:
            tavern['cards'] = []
            tavern['occupants'] = []

    # 【新增逻辑】：新回合开始前，仅重置本局固定的闹市卡的使用状态
    if 'downtownCards' in game_state:
        for card in game_state['downtownCards']:
            card['usedThisRound'] = False

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

        log_info(f"Room {room_id} deleted")


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
    log_info(f"Host transferred to {new_host['name']} in room {room_id}")


async def handle_player_disconnect(room_id: str, player_id: int, player_name: str, rooms: dict, manager, broadcast_func):
    """处理玩家断开连接"""
    log_debug(f"handle_player_disconnect called for room {room_id}, player {player_id}")

    game_state = rooms.get(room_id)
    if not game_state:
        log_debug(f"game_state not found in handle_player_disconnect for room {room_id}")
        return

    if player_name is None and player_id is not None:
        player = next((p for p in game_state['players'] if p['id'] == player_id), None)
        if player:
            player_name = player.get('name')
            player['isOnline'] = False
            player['ready'] = False
            player['lastSeen'] = int(time.time())

    transfer_host(room_id, game_state)

    all_offline = all(not p.get('isOnline', True) for p in game_state['players'])

    await broadcast_func(room_id)

    if all_offline:
        cleanup_room(room_id, rooms, manager)
        return

    await manager.broadcast_to_room_members(room_id, ServerEvents.SERVER_ROOM_ACTION,
        make_action_message(ServerRoomActionTypes.PLAYER_STATUS_CHANGE,
            playerId=player_id,
            playerName=player_name,
            status='offline',
            players=game_state['players']
        ))


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
            make_action_message(ServerRoomActionTypes.ROOM_STATE_UPDATE, **data))


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
            'status': game_state['status'],
            'gameTitleCards': game_state.get('gameTitleCards', [])
        }
        await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
            make_action_message(ServerGameActionTypes.GAME_STATE_UPDATE, **data))


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

        # 初始化新的状态追踪
        player['tributesThisRound'] = 0
        player['inn_headman'] = False

    game_state['currentPlayerIndex'] = starting_player_idx

    for p in game_state['players']:
        p['bubbles'] = 0
        p['ready'] = False

    for area_name in AREAS:
        if area_name in game_state['areas']:
            slot_count = len(game_state['areas'][area_name]['slots'])
            game_state['areas'][area_name]['slots'] = [None] * slot_count

    draw_tribute_tasks(game_state)
    draw_downtown_cards(game_state)  # 游戏开始时只执行这一次
    draw_title_cards(game_state)

    log_debug(f"start_game: Sending gameStarted to room {room_id}")
    log_debug(f"  game_state['status'] = {game_state['status']}")
    log_debug(f"  game_state['phase'] = {game_state['phase']}")
    log_debug(f"  game_state['currentPlayerIndex'] = {game_state['currentPlayerIndex']}")
    log_debug(f"  players in room: {len(game_state['players'])}")
    log_debug(f"  active_connections: {list(manager.active_connections.get(room_id, {}).keys())}")

    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        make_action_message(ServerGameActionTypes.GAME_STARTED, **game_state))
    await broadcast_game_state(room_id, rooms, manager)
    log_info(f"Game started in room {room_id}")


async def complete_settlement(room_id, game_state, rooms, manager):
    """完成结算阶段，进入清理和下一回合"""
    cleanup_phase(game_state)

    if game_state['currentRound'] >= game_state['maxRounds']:
        players_need_endgame_choice = []
        for player in game_state['players']:
            tribute_cards = player.get('tributeCards', [])
            for card in tribute_cards:
                if card.get('effectType') == 'aura_endgame_score':
                    players_need_endgame_choice.append({
                        'playerId': player['id'],
                        'playerName': player['name'],
                        'card': card
                    })
                    break

        if players_need_endgame_choice:
            game_state['status'] = 'waitingEndgameChoice'
            game_state['waitingForEndgameChoice'] = players_need_endgame_choice
            game_state['endgameChoiceIndex'] = 0

            first_player = players_need_endgame_choice[0]
            player = game_state['players'][first_player['playerId']]
            card = first_player['card']
            choices = get_endgame_choices(player, card)

            await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
                make_action_message(ServerGameActionTypes.GAME_ACTION, {
                    'actionType': 'endgameScoreChoiceRequired',
                    'playerId': first_player['playerId'],
                    'playerName': first_player['playerName'],
                    'data': {
                        'card': card,
                        'choices': choices
                    },
                    'gameState': game_state
                }))
            await broadcast_game_state(room_id, rooms, manager)
            return

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
        await broadcast_game_state(room_id, rooms, manager)
        return

    game_state['currentRound'] += 1

    # 触发每轮 aura 效果
    for player in game_state['players']:
        tribute_cards = player.get('tributeCards', [])
        for card in tribute_cards:
            effect_type = card.get('effectType')
            if effect_type == 'aura_round_coin':
                player['coins'] = player.get('coins', 0) + 1
            elif effect_type == 'aura_round_seaweed':
                player['seaweed'] = player.get('seaweed', 0) + 1

    game_state['phase'] = 'placement'
    game_state['currentPlayerIndex'] = game_state.get('startingPlayerIndex', 0)
    game_state['currentArea'] = 0
    game_state['lastPlacement'] = None
    game_state['areas'].get('tribute')['challengeSlots'] = [None] * 3

    for area_name in AREAS:
        if area_name in game_state['areas']:
            slot_count = len(game_state['areas'][area_name]['slots'])
            game_state['areas'][area_name]['slots'] = [None] * slot_count

    for p in game_state['players']:
        p['royalCountThisRound'] = 0

    draw_tribute_tasks(game_state)
    # 【重点修复】：已删除 draw_downtown_cards(game_state) ，不再每回合刷新卡牌！
    draw_title_cards(game_state)

    await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
        make_action_message(ServerAreaActionTypes.SETTLEMENT_COMPLETE, {
            'gameState': game_state
        }))
    await manager.send_to_room(room_id, ServerEvents.SERVER_GAME_ACTION,
        make_action_message(ServerGameActionTypes.ROUND_STARTED, {
            'round': game_state['currentRound'],
            'gameState': game_state
        }))
    await broadcast_game_state(room_id, rooms, manager)


async def start_area_settlement(websocket, room_id, game_state, rooms, manager):
    """启动当前区域的结算流程"""
    from services.area import resolve_area_step

    current_area = game_state.get('currentArea', 0)
    log_debug(f"[start_area_settlement] current_area={current_area}, area_name={AREAS[current_area] if current_area < len(AREAS) else 'N/A'}")

    if current_area >= len(AREAS):
        await complete_settlement(room_id, game_state, rooms, manager)
        return

    area_name = AREAS[current_area]
    log_info(f"[start_area_settlement] resolving area: {area_name}")

    area_data = game_state['areas'].get(area_name)
    if not area_data:
        game_state['currentArea'] = current_area + 1
        await start_area_settlement(websocket, room_id, game_state, rooms, manager)
        return

    result = await resolve_area_step(game_state, current_area, manager, room_id)
    log_debug(f"[start_area_settlement] result={result}, area={area_name}")

    if result == 'auto_next':
        if current_area + 1 >= len(AREAS):
            await complete_settlement(room_id, game_state, rooms, manager)
        else:
            next_area = current_area + 1
            game_state['currentArea'] = next_area
            next_area_name = AREAS[next_area]
            await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                make_action_message(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                    'areaType': next_area_name,
                    'gameState': game_state
                }))
            await start_area_settlement(websocket, room_id, game_state, rooms, manager)
    elif result == 'waiting_ui':
        await broadcast_game_state(room_id, rooms, manager)