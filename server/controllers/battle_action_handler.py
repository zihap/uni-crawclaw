# -*- coding: utf-8 -*-
"""
战斗行动路由器
将客户端发送的 clientBattleAction 事件按 action_type 分发到具体 handler

包含的事件:
  - BATTLE_ACTION: 战斗行动（battleStart, battleUpdate, battleEnd）
  - LOBSTER_SELECTED: 龙虾选择
  - SPECTATOR_BET: 观战者投注
  - NO_LOBSTER_FORFEIT: 无龙虾判负
"""

from utils.constants import AREAS, GRADE_UPGRADE
from utils.events import ClientBattleActionTypes, ServerEvents, ServerBattleActionTypes, ServerAreaActionTypes
from utils.helpers import send_error, get_player, update_resources
from utils.game_state import arena_betting_state
from controllers.game_action_handler import _start_area_settlement, _complete_settlement
from services.game import broadcast_game_state


def _sra(action_type, data):
    """构造 serverBattleAction / serverAreaAction 消息体"""
    return {'actionType': action_type, **data}


def _make_bf(manager, room_id):
    """创建资源广播闭包"""
    async def bf(player_id, resources):
        await manager.send_to_room(room_id, ServerEvents.PLAYER_RESOURCE_UPDATE, {
            'playerId': player_id, 'resources': resources
        })
    return bf


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

async def handle_battle_start(websocket, room_id, player_id, rooms, manager, payload):
    """战斗开始"""
    game_state = rooms.get(room_id)
    if game_state and game_state.get('_lastBattleStartSent'):
        return

    battle_data = payload.get('battleData')

    if game_state:
        game_state['_lastBattleStartSent'] = True

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        _sra(ServerBattleActionTypes.BATTLE_START, {
            'battleData': battle_data,
            'initiatorId': player_id
        }))

async def handle_battle_update(websocket, room_id, player_id, rooms, manager, payload):
    """战斗行动"""
    battle_data = payload.get('battleData')
    sender_id = payload.get('senderId')

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        _sra(ServerBattleActionTypes.BATTLE_UPDATE, {
            'battleData': battle_data,
            'senderId': sender_id
        }))

async def handle_battle_end(websocket, room_id, player_id, rooms, manager, payload):
    """战斗结束"""
    battle_data = payload.get('battleData')

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

        if '_lastBattleStartSent' in game_state:
            del game_state['_lastBattleStartSent']

        total_battles = len(game_state.get('battleQueue', []))
        if game_state['tributeBattlesCompleted'] >= total_battles:
            game_state['settlementState'] = {
                'currentSlotIndex': 0,
                'remainingActions': -1,
                'waitingForPlayer': None,
                'areaType': 'tribute'
            }

            from services.area import _resolve_tribute_actions
            result = await _resolve_tribute_actions(game_state, manager, room_id)

            if result == 'waiting_ui':
                await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                    _sra(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                        'areaType': 'tribute',
                        'gameState': game_state
                    }))
                await broadcast_game_state(room_id, rooms, manager)
            else:
                current_area = game_state.get('currentArea', 0)
                if current_area + 1 >= len(AREAS):
                    await _complete_settlement(room_id, game_state, rooms, manager)
                else:
                    next_area_name = AREAS[current_area + 1]
                    await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                        _sra(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                            'areaType': next_area_name,
                            'gameState': game_state
                        }))
                    await _start_area_settlement(websocket, room_id, game_state, rooms, manager)
            return

async def handle_lobster_selected(websocket, room_id, player_id, rooms, manager, payload):
    """龙虾选择"""
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


async def handle_spectator_bet(websocket, room_id, player_id, rooms, manager, payload):
    """观战者投注"""
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


async def handle_no_lobster_forfeit(websocket, room_id, player_id, rooms, manager, payload):
    """无龙虾判负"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    challenge_slot = payload.get('challengeSlot')
    if swap_challenge_slot(game_state, challenge_slot):
        print(f"[noLobsterForfeit] Slot swapped: challenger wins at slot {challenge_slot}")

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        _sra(ServerBattleActionTypes.BATTLE_ENDED, {
            'battleData': {
                'challengeSlot': challenge_slot,
                'reason': 'no_available_lobsters',
                'winner': 'challenger'
            },
            'senderId': player_id
        }))


def _make_battle_action_router(handlers: dict):
    """创建战斗行动路由函数"""
    async def handle_battle_action_router(websocket, room_id, player_id, rooms, manager, payload):
        action_type = payload.get('action_type')
        handler = handlers.get(action_type)
        if handler:
            return await handler(websocket, room_id, player_id, rooms, manager, payload)
        await send_error(websocket, f'未知的战斗行动: {action_type}')
    return handle_battle_action_router


def get_battle_action_handlers():
    """获取战斗行动处理器映射"""
    return {
        ClientBattleActionTypes.BATTLE_START: handle_battle_start,
        ClientBattleActionTypes.BATTLE_UPDATE: handle_battle_update,
        ClientBattleActionTypes.BATTLE_END: handle_battle_end,
        ClientBattleActionTypes.LOBSTER_SELECTED: handle_lobster_selected,
        ClientBattleActionTypes.SPECTATOR_BET: handle_spectator_bet,
        ClientBattleActionTypes.NO_LOBSTER_FORFEIT: handle_no_lobster_forfeit,
    }


handle_battle_action = _make_battle_action_router(get_battle_action_handlers())