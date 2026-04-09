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

from utils.constants import AREAS, GRADE_UPGRADE, CHALLENGE_SLOT_DONE, CHALLENGE_TO_DEFENDER_SLOT_MAP
from utils.events import ClientBattleActionTypes, ServerEvents, ServerBattleActionTypes, ServerAreaActionTypes
from utils.helpers import send_error, get_player, update_resources, make_action_message, make_broadcast_fn, make_settlement_state
from utils.logger import log_info, log_debug
from utils.game_state import arena_betting_state
from services.game import broadcast_game_state, start_area_settlement, complete_settlement
from services.tribute_card_effects import check_bet_bonus


async def _check_tribute_battles_complete(game_state, websocket, room_id, rooms, manager):
    """检查上供区所有战斗是否完成，若是则触发上供阶段"""
    tribute = game_state['areas'].get('tribute')
    if not tribute:
        return False

    challenge_slots = tribute.get('challengeSlots', [])
    completed_battles = sum(1 for s in challenge_slots if s == CHALLENGE_SLOT_DONE)
    total_battles = len(game_state.get('battleQueue', []))

    log_info(f"[tribute] Battles completed: {completed_battles}/{total_battles}")

    if completed_battles >= total_battles:
        if '_lastBattleStartSent' in game_state:
            del game_state['_lastBattleStartSent']

        game_state['battleQueue'] = []
        game_state['settlementState'] = make_settlement_state('tribute', 0, 0)

        from services.area import _resolve_tribute_actions
        result = await _resolve_tribute_actions(game_state, manager, room_id)

        if result == 'waiting_ui':
            await broadcast_game_state(room_id, rooms, manager)
        else:
            current_area = game_state.get('currentArea', 0)
            if current_area + 1 >= len(AREAS):
                await complete_settlement(room_id, game_state, rooms, manager)
            else:
                next_area_name = AREAS[current_area + 1]
                await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                    make_action_message(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                        'areaType': next_area_name,
                        'gameState': game_state
                    }))
                await start_area_settlement(websocket, room_id, game_state, rooms, manager)
        return True
    return False


def swap_challenge_slot(game_state, challenge_slot):
    """交换挑战槽位（challenger 获胜时调用）"""
    tribute = game_state['areas'].get('tribute')
    if not tribute:
        return False
    slots = tribute.get('slots', [])
    slot_map = CHALLENGE_TO_DEFENDER_SLOT_MAP
    idx = slot_map.get(challenge_slot)
    log_debug(f"[swap_challenge_slot] challenge_slot={challenge_slot}, idx={idx}")
    if idx is not None and idx < len(slots):
        slots[challenge_slot], slots[idx] = slots[idx], slots[challenge_slot]
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
        make_action_message(ServerBattleActionTypes.BATTLE_START, {
            'battleData': battle_data,
            'initiatorId': player_id
        }))

async def handle_battle_update(websocket, room_id, player_id, rooms, manager, payload):
    """战斗行动"""
    battle_data = payload.get('battleData')
    sender_id = payload.get('senderId')

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message(ServerBattleActionTypes.BATTLE_UPDATE, {
            'battleData': battle_data,
            'senderId': sender_id
        }))

async def handle_battle_end(websocket, room_id, player_id, rooms, manager, payload):
    """战斗结束"""
    battle_data = payload.get('battleData')

    game_state = rooms.get(room_id)
    if game_state:
        winner_id = battle_data.get('winner', {}).get('id')
        challenge_slot = battle_data.get('challengeSlotIndex') or battle_data.get('challengeSlot')

        players_data = battle_data.get('players', [])
        challenger_id = None
        if len(players_data) >= 2:
            challenger_id = players_data[0]['id']

        if winner_id == challenger_id and challenge_slot:
            swap_challenge_slot(game_state, challenge_slot)

        game_state['areas'].get('tribute')['challengeSlots'][challenge_slot-3] = CHALLENGE_SLOT_DONE

        bf = make_broadcast_fn(manager.send_to_room, room_id)

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
                            bet_amount = bet['amount']
                            # aura_bet_bonus: 押注成功额外获得1金币
                            has_bet_bonus = check_bet_bonus(bettor)
                            reward = bet_amount * 2 + (1 if has_bet_bonus else 0)
                            await update_resources(bettor, {'coins': reward}, broadcast_fn=bf)
                            bet_results[str(pid)] = {'won': True, 'reward': reward}
                        else:
                            bet_results[str(pid)] = {'won': False, 'reward': 0}
                    else:
                        bet_results[str(pid)] = {'won': False, 'reward': 0}

                await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                    make_action_message(ServerBattleActionTypes.BET_RESULT, {
                        'winnerId': winner_id,
                        'betResults': bet_results
                    }))
                del arena_betting_state[key]
                break

        award_choice = battle_data.get('winnerAwardChoice')
        upgrade_from = None
        upgrade_to = None
        winner_lobster_id = None
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

                        for key in list(arena_betting_state.keys()):
                            bs = arena_betting_state[key]
                            if not key.startswith(f"{room_id}_"):
                                continue
                            if str(challenge_slot) in key:
                                winner_lobster = None
                                if winner_id == bs.get('challengerId'):
                                    winner_lobster = bs.get('challengerLobster')
                                elif winner_id == bs.get('defenderId'):
                                    winner_lobster = bs.get('defenderLobster')
                                if winner_lobster and winner_lobster.get('id'):
                                    winner_lobster_id = winner_lobster['id']
                                    lobster = next((l for l in winner.get('lobsters', []) if l.get('id') == winner_lobster_id), None)
                                    if lobster:
                                        lobster['grade'] = upgrade_to
                                break

                for pi, field in [(0, 'p1CrossedMidline'), (1, 'p2CrossedMidline')]:
                    if battle_data.get(field):
                        p = players_data[pi] if pi < len(players_data) else None
                        if p:
                            game_player = get_player(game_state, p['id'])
                            if game_player:
                                await update_resources(game_player, {'wang': 1}, broadcast_fn=bf)

                if deltas:
                    await update_resources(winner, deltas, broadcast_fn=bf)

        await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
            make_action_message(ServerBattleActionTypes.BATTLE_ENDED, {
                'winnerId': winner_id,
                'awardChoice': award_choice,
                'upgradeFrom': upgrade_from,
                'upgradeTo': upgrade_to,
                'winnerLobsterId': winner_lobster_id,
                'battleData': battle_data,
                'gameState': game_state
            }))

        await _check_tribute_battles_complete(game_state, websocket, room_id, rooms, manager)
        return

async def handle_lobster_selected(websocket, room_id, player_id, rooms, manager, payload):
    """龙虾选择"""
    lobster_data = payload.get('lobster')

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message(ServerBattleActionTypes.LOBSTER_SELECTED, {
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
                make_action_message(ServerBattleActionTypes.ARENA_BETTING_START, {
                    'battleId': battle_id,
                    'challengerId': state['challengerId'],
                    'defenderId': state['defenderId'],
                    'challengerLobster': state['challengerLobster'],
                    'defenderLobster': state['defenderLobster'],
                    'spectators': state['spectators']
                }))

            if len(state['spectators']) == 0:
                await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                    make_action_message(ServerBattleActionTypes.ARENA_BETTING_COMPLETE, {
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
                await update_resources(player, {'coins': -bet_amount}, broadcast_fn=make_broadcast_fn(manager.send_to_room, room_id))

    if len(state['bets']) >= len(state['spectators']):
        await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
            make_action_message(ServerBattleActionTypes.ARENA_BETTING_COMPLETE, {
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

    # 标记该战斗槽位已完成
    tribute = game_state['areas'].get('tribute')
    if tribute and challenge_slot is not None:
        challenge_slots = tribute.get('challengeSlots', [])
        if 0 <= challenge_slot - 3 < len(challenge_slots):
            challenge_slots[challenge_slot - 3] = CHALLENGE_SLOT_DONE
            log_info(f"[noLobsterForfeit] Marked challenge slot {challenge_slot} as Done")

    if swap_challenge_slot(game_state, challenge_slot):
        log_info(f"[noLobsterForfeit] Slot swapped: challenger wins at slot {challenge_slot}")

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message(ServerBattleActionTypes.BATTLE_ENDED, {
            'battleData': {
                'challengeSlot': challenge_slot,
                'reason': 'no_available_lobsters',
                'winner': 'challenger'
            },
            'senderId': player_id
        }))

    # 更新上供战斗完成计数并检查是否全部完成
    await _check_tribute_battles_complete(game_state, websocket, room_id, rooms, manager)


async def handle_battle_bonus_choice(websocket, room_id, player_id, rooms, manager, payload):
    """处理战斗奖励资源选择"""
    game_state = rooms.get(room_id)
    if not game_state:
        return

    player = get_player(game_state, player_id)
    if not player:
        return

    pending_choices = game_state.get('pendingBattleBonusChoices', [])
    if player_id not in pending_choices:
        await send_error(websocket, '你没有待选择的战斗奖励')
        return

    choice = payload.get('choice')
    if choice not in ('coins', 'seaweed', 'lobster'):
        await send_error(websocket, '无效的资源选择')
        return

    if choice == 'coins':
        player['coins'] += 1
    elif choice == 'seaweed':
        player['seaweed'] = player.get('seaweed', 0) + 1
    elif choice == 'lobster':
        from utils.helpers import create_lobster
        player['lobsters'].append(create_lobster('normal'))

    pending_choices.remove(player_id)
    if pending_choices:
        game_state['pendingBattleBonusChoices'] = pending_choices
        await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
            make_action_message(ServerAreaActionTypes.AREA_WAITING_UI, {
                'areaType': 'tribute',
                'waitingForBattleBonusChoice': True,
                'playersNeedChoice': pending_choices,
                'battleQueue': game_state.get('battleQueue', [])
            }))
    else:
        del game_state['pendingBattleBonusChoices']
        del game_state['_lastBattleStartSent']
        await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
            make_action_message(ServerBattleActionTypes.BATTLE_START, {
                'battleQueue': game_state.get('battleQueue', [])
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
        ClientBattleActionTypes.BATTLE_BONUS_CHOICE: handle_battle_bonus_choice,
    }


handle_battle_action = _make_battle_action_router(get_battle_action_handlers())