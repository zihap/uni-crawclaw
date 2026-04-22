# -*- coding: utf-8 -*-
"""
战斗行动路由器
"""

import random
import math
import asyncio
from utils.constants import AREAS, GRADE_UPGRADE, CHALLENGE_SLOT_DONE, CHALLENGE_TO_DEFENDER_SLOT_MAP
from utils.events import ClientBattleActionTypes, ServerEvents, ServerBattleActionTypes, ServerAreaActionTypes
from utils.helpers import send_error, get_player, update_resources, make_action_message, make_broadcast_fn, make_settlement_state
from utils.logger import log_info, log_debug
from utils.game_state import arena_betting_state
from services.game import broadcast_game_state, start_area_settlement, complete_settlement
from services.tribute_card_effects import check_bet_bonus

def get_dice_type(lobster):
    name = lobster.get('name', '')
    grade = lobster.get('grade', 'normal')
    if name == '红头紫': return 12
    if grade == 'grade3': return 6
    if grade == 'grade2': return 8
    return 10

def calculate_damage(roll_value):
    if roll_value <= 2: return 0
    elif 3 <= roll_value <= 5: return 1
    elif 6 <= roll_value <= 8: return 2
    elif 9 <= roll_value <= 11: return 3
    else: return 4

def get_hp_card_draws(lobster):
    grade = lobster.get('grade')
    name = lobster.get('name', '')
    title = lobster.get('title')

    draws = ['base']
    if grade == 'royal' or title or name:
        draws.append('equip')
    if name == '龙象霸王虾':
        draws.append('god')
    return draws

def draw_hp_values(draw_types):
    hp_values = []
    for t in draw_types:
        if t == 'base': hp_values.append(random.choice([2, 3, 4, 5]))
        elif t == 'equip': hp_values.append(random.choice([1, 2, 3, 4]))
        elif t == 'god': hp_values.append(random.choice([1, 2]))
    return hp_values

async def start_rpg_battle(room_id, battle_id, game_state, manager):
    key = f"{room_id}_{battle_id}"
    state = arena_betting_state.get(key)
    if not state: return

    defender_id = state['defenderId']
    challenger_id = state['challengerId']
    d_lob = state['defenderLobster']
    c_lob = state['challengerLobster']

    challenge_slot = 0
    defender_slot = 0
    for b in game_state.get('battleQueue', []):
        if b['challengerId'] == challenger_id and b['defenderId'] == defender_id:
            challenge_slot = b.get('challengeSlot', 0)
            defender_slot = b.get('defenderSlot', 0)
            break

    game_state['current_battle'] = {
        'battleId': battle_id,
        'challengeSlotIndex': challenge_slot,
        'defenderSlotIndex': defender_slot,
        'phase': 'enrage_roll',
        'activePlayerId': defender_id,
        'original_defender_id': defender_id,
        'original_challenger_id': challenger_id,
        'init_phase_done': False,
        'enrage_rolls_done': 0,
        'critCount': 0,
        'p1': {
            'id': defender_id,
            'name': get_player(game_state, defender_id)['name'],
            'lobster': d_lob,
            'lobsterName': d_lob.get('name') or d_lob.get('title') or d_lob.get('grade', '普虾'),
            'lobsterGrade': d_lob.get('grade', 'normal'),
            'lobsterId': d_lob.get('id'),
            'diceType': get_dice_type(d_lob),
            'dmgTaken': 0,
            'survivedAttacks': 0,
            'enraged': False,
            'enrage_roll_val': 0,
            'seaweed': get_player(game_state, defender_id).get('seaweed', 0)
        },
        'p2': {
            'id': challenger_id,
            'name': get_player(game_state, challenger_id)['name'],
            'lobster': c_lob,
            'lobsterName': c_lob.get('name') or c_lob.get('title') or c_lob.get('grade', '普虾'),
            'lobsterGrade': c_lob.get('grade', 'normal'),
            'lobsterId': c_lob.get('id'),
            'diceType': get_dice_type(c_lob),
            'dmgTaken': 0,
            'survivedAttacks': 0,
            'enraged': False,
            'enrage_roll_val': 0,
            'seaweed': get_player(game_state, challenger_id).get('seaweed', 0)
        }
    }

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message('battleStart', {
            'actionType': 'battleStart',
            'battleData': game_state['current_battle']
        }))

async def handle_rpg_battle_action(websocket, room_id, player_id, rooms, manager, payload):
    action_type = payload.get('actionType') or payload.get('action_type')
    game_state = rooms.get(room_id)
    if not game_state or 'current_battle' not in game_state:
        return

    battle = game_state['current_battle']

    if action_type not in ['confirm_hp_result', 'claim_battle_reward'] and player_id != battle.get('activePlayerId') and player_id != battle.get('targetPlayerId'):
        await send_error(websocket, '还没轮到你操作！')
        return

    active_p = battle['p1'] if battle.get('activePlayerId') == battle['p1']['id'] else battle['p2']
    defender_p = battle['p2'] if active_p == battle['p1'] else battle['p1']

    if action_type == 'roll_dice':
        if battle['phase'] == 'enrage_roll':
            roll = random.randint(1, active_p['diceType'])

            if not battle['init_phase_done']:
                active_p['enrage_roll_val'] = roll
                active_p['enraged'] = (roll >= 6)
                log_str = '<color=#ff0000>成功进入狂暴！</color>' if active_p['enraged'] else '未达6点，起步失败。'
                battle['lastLog'] = f"🎲 【{active_p['name']}】起步判定掷出 {roll}点，{log_str}"

                battle['enrage_rolls_done'] += 1
                if battle['enrage_rolls_done'] == 1:
                    battle['activePlayerId'] = battle['original_challenger_id']
                elif battle['enrage_rolls_done'] == 2:
                    battle['init_phase_done'] = True
                    p1 = battle['p1']
                    p2 = battle['p2']
                    if not p1['enraged'] and not p2['enraged']:
                        battle['lastLog'] += "<br/>🌀 双方均未起步成功，重新进行判定！"
                        battle['enrage_rolls_done'] = 0
                        battle['init_phase_done'] = False
                        battle['activePlayerId'] = battle['original_defender_id']
                    else:
                        if p1['enraged'] and not p2['enraged']: battle['activePlayerId'] = p1['id']
                        elif p2['enraged'] and not p1['enraged']: battle['activePlayerId'] = p2['id']
                        else:
                            if p2['enrage_roll_val'] > p1['enrage_roll_val']: battle['activePlayerId'] = p2['id']
                            else: battle['activePlayerId'] = p1['id']

                        first_player = battle['p1'] if battle['activePlayerId'] == battle['p1']['id'] else battle['p2']
                        battle['phase'] = 'attack_roll'
                        battle['lastLog'] += f"<br/>⚔️ 【{first_player['name']}】夺得先手攻击权！"
            else:
                active_p['enraged'] = (roll >= 6)
                if active_p['enraged']:
                    battle['lastLog'] = f"🎲 【{active_p['name']}】起步掷出 {roll}点，<color=#ff0000>进入狂暴！</color> 可以反击！"
                    battle['phase'] = 'attack_roll'
                else:
                    battle['lastLog'] = f"🎲 【{active_p['name']}】起步掷出 {roll}点，起步失败，回合结束。"
                    battle['activePlayerId'] = defender_p['id']
                    next_p = battle['p1'] if battle['activePlayerId'] == battle['p1']['id'] else battle['p2']
                    battle['phase'] = 'attack_roll' if next_p['enraged'] else 'enrage_roll'

        elif battle['phase'] == 'attack_roll':
            roll = random.randint(1, active_p['diceType'])
            battle['currentRoll'] = roll
            battle['lastLog'] = f"⚔️ 【{active_p['name']}】攻击掷出了 {roll}点！"

            if active_p['lobsterGrade'] == 'grade3':
                _process_damage(battle, active_p, defender_p, roll, 0)
            else:
                battle['phase'] = 'seaweed_choice'

    elif action_type == 'seaweed_choice':
        use_weed = payload.get('useSeaweed', False)
        bonus = 0
        if use_weed and active_p['seaweed'] > 0:
            active_p['seaweed'] -= 1
            player_entity = get_player(game_state, player_id)
            if player_entity: player_entity['seaweed'] -= 1

            grade = active_p['lobsterGrade']
            if grade == 'grade2': bonus = 1
            elif grade == 'grade1': bonus = 2
            elif grade == 'royal': bonus = 3
            battle['lastLog'] = f"🌿 【{active_p['name']}】吃草！获得额外 +{bonus} 攻击点数！"
        else:
            battle['lastLog'] = f"⏭️ 【{active_p['name']}】放弃吃草。"

        final_roll = battle['currentRoll'] + bonus
        _process_damage(battle, active_p, defender_p, final_roll, bonus)

    elif action_type == 'draw_hp':
        if player_id != battle['targetPlayerId']:
            await send_error(websocket, '只能由受击方亲自抽取血量卡！')
            return

        target_p = battle['p1'] if battle['targetPlayerId'] == battle['p1']['id'] else battle['p2']
        attacker_p = battle['p2'] if target_p == battle['p1'] else battle['p1']

        draw_types = get_hp_card_draws(target_p['lobster'])
        hp_values = draw_hp_values(draw_types)
        total_hp = sum(hp_values)

        battle['lastHpDraws'] = hp_values
        dmg = battle['currentDamage']

        target_p['dmgTaken'] += dmg
        battle['phase'] = 'show_hp_result'

        if target_p['dmgTaken'] >= total_hp:
            battle['nextPhase'] = 'reward_choice'
            battle['winnerId'] = attacker_p['id']
            battle['winnerName'] = attacker_p['name']
            battle['nextLog'] = f"🎴 【{target_p['name']}】抽到血量: {total_hp}，累计受伤已达: <color=#ff0000>{target_p['dmgTaken']}点</color>...<br/>💀 承受不住，惨遭斩杀！"
        else:
            target_p['survivedAttacks'] += 1
            battle['nextActivePlayerId'] = target_p['id']
            battle['nextPhase'] = 'attack_roll' if target_p['enraged'] else 'enrage_roll'
            battle['nextLog'] = f"🎴 【{target_p['name']}】抽到血量: {total_hp}，累计受伤达: <color=#ffaa00>{target_p['dmgTaken']}点</color>！<br/>🛡️ 惊险扛下伤害，暴击率飙升！"

    elif action_type == 'confirm_hp_result':
        battle['phase'] = battle['nextPhase']
        battle['lastLog'] = battle.get('nextLog', '')
        battle['lastHpDraws'] = []

        if battle['phase'] == 'reward_choice':
            bf = make_broadcast_fn(manager.send_to_room, room_id)
            for p_key in ['p1', 'p2']:
                p = battle[p_key]
                if p.get('survivedAttacks', 0) >= 3:
                    p_entity = get_player(game_state, p['id'])
                    if p_entity:
                        await update_resources(p_entity, {'wang': 1}, broadcast_fn=bf)
                        battle['lastLog'] += f"<br/>🎖️ 【{p['name']}】在狂暴下撑过了3次攻击，毅力惊人，<br/>获得 <color=#ffaa00>1点望</color> 奖励！"

            battle['lastLog'] += f"<br/>🏆 战斗结束！请胜者【{battle['winnerName']}】选择胜利奖励！"
        else:
            battle['activePlayerId'] = battle['nextActivePlayerId']
            next_active = battle['p1'] if battle['activePlayerId'] == battle['p1']['id'] else battle['p2']
            battle['lastLog'] += f"<br/>🔄 回合交接，轮到 【{next_active['name']}】 行动！"

    elif action_type == 'claim_battle_reward':
        reward_type = payload.get('rewardType')
        if player_id != battle.get('winnerId'):
            return

        winner_p = get_player(game_state, player_id)
        bf = make_broadcast_fn(manager.send_to_room, room_id)

        if reward_type == 'coins':
            await update_resources(winner_p, {'coins': 2}, broadcast_fn=bf)
        elif reward_type == 'upgrade':
            winner_lobster_id = battle['p1']['lobsterId'] if player_id == battle['p1']['id'] else battle['p2']['lobsterId']
            for lob in winner_p.get('lobsters', []):
                if lob.get('id') == winner_lobster_id:
                    g = lob.get('grade', 'normal')
                    if g == 'normal': lob['grade'] = 'grade3'
                    elif g == 'grade3': lob['grade'] = 'grade2'
                    elif g == 'grade2': lob['grade'] = 'grade1'
                    elif g == 'grade1': lob['grade'] = 'royal'
                    break

        await _finalize_rpg_battle(websocket, room_id, game_state, manager, rooms)
        return

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message('battleUpdate', {
            'actionType': 'battleUpdate',
            'battleData': battle
        }))

def _process_damage(battle, active_p, defender_p, final_roll, bonus):
    base_dmg = calculate_damage(final_roll)
    crit_chance = min(1.0, active_p['dmgTaken'] * 0.2)
    is_crit = random.random() < crit_chance

    final_dmg = math.ceil(base_dmg * 1.5) if is_crit else base_dmg
    battle['currentDamage'] = final_dmg

    if is_crit:
        battle['critCount'] += 1

    crit_str = "<color=#ffaa00>💥【暴击】</color>" if is_crit else ""
    battle['lastLog'] += f"<br/>🎯 最终判定 {final_roll}点！{crit_str}造成了 <color=#ff0000>{final_dmg}点</color> 伤害！"

    battle['phase'] = 'hp_draw'
    battle['targetPlayerId'] = defender_p['id']
    battle['requiredHPCards'] = len(get_hp_card_draws(defender_p['lobster']))

async def _finalize_rpg_battle(websocket, room_id, game_state, manager, rooms):
    battle = game_state['current_battle']
    winner_id = battle['winnerId']
    challenge_slot = battle['challengeSlotIndex']
    p1 = battle['p1']
    p2 = battle['p2']

    challenger_id = battle['original_challenger_id']
    if winner_id == challenger_id:
        swap_challenge_slot(game_state, challenge_slot)

    game_state['areas'].get('tribute')['challengeSlots'][challenge_slot-3] = CHALLENGE_SLOT_DONE

    winner_lobster_id = p1['lobsterId'] if winner_id == p1['id'] else p2['lobsterId']
    loser_lobster_id = p2['lobsterId'] if winner_id == p1['id'] else p1['lobsterId']

    for player in game_state['players']:
        for lobster in player['lobsters']:
            if lobster.get('id') == winner_lobster_id or lobster.get('id') == loser_lobster_id:
                lobster['used'] = True
        for titleCard in player['titleCards']:
            if titleCard.get('id') == winner_lobster_id or titleCard.get('id') == loser_lobster_id:
                titleCard['used'] = True

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message('battleEnded', {
            'actionType': 'battleEnded',
            'gameState': game_state
        }))

    # ==========================================
    # 【死锁终结者】：休眠2秒！绝对留足时间让前端删掉弹窗
    # ==========================================
    await asyncio.sleep(2.0)
    await _check_tribute_battles_complete(game_state, websocket, room_id, rooms, manager)


async def _check_tribute_battles_complete(game_state, websocket, room_id, rooms, manager):
    tribute = game_state['areas'].get('tribute')
    if not tribute: return False
    challenge_slots = tribute.get('challengeSlots', [])

    remaining_battles = []
    for b in game_state.get('battleQueue', []):
        c_slot = b['challengeSlot']
        if challenge_slots[c_slot - 3] != CHALLENGE_SLOT_DONE:
            remaining_battles.append(b)

    game_state['battleQueue'] = remaining_battles

    if len(remaining_battles) == 0:
        if '_lastBattleStartSent' in game_state: del game_state['_lastBattleStartSent']
        game_state['settlementState'] = make_settlement_state('tribute', 0, 0)
        from services.area import _resolve_tribute_actions
        result = await _resolve_tribute_actions(game_state, manager, room_id)
        if result == 'waiting_ui':
            await broadcast_game_state(room_id, rooms, manager)
        else:
            current_area = game_state.get('currentArea', 0)
            if current_area + 1 >= len(AREAS): await complete_settlement(room_id, game_state, rooms, manager)
            else:
                next_area_name = AREAS[current_area + 1]
                await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                    make_action_message(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                        'areaType': next_area_name, 'gameState': game_state
                    }))
                await start_area_settlement(websocket, room_id, game_state, rooms, manager)
        return True
    else:
        await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
            make_action_message('battleStart', {
                'actionType': 'battleStart',
                'battleQueue': game_state['battleQueue']
            }))
        return False

def swap_challenge_slot(game_state, challenge_slot):
    tribute = game_state['areas'].get('tribute')
    if not tribute: return False
    slots = tribute.get('slots', [])
    idx = CHALLENGE_TO_DEFENDER_SLOT_MAP.get(challenge_slot)
    if idx is not None and idx < len(slots):
        slots[challenge_slot], slots[idx] = slots[idx], slots[challenge_slot]
        return True
    return False

async def handle_lobster_selected(websocket, room_id, player_id, rooms, manager, payload):
    lobster_data = payload.get('lobster')
    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message(ServerBattleActionTypes.LOBSTER_SELECTED, {
            'playerId': player_id, 'lobster': lobster_data
        }))
    battle_id = payload.get('battleId')
    if battle_id:
        key = f"{room_id}_{battle_id}"
        if key not in arena_betting_state:
            arena_betting_state[key] = {
                'battleId': battle_id, 'challengerId': payload.get('challengerId'),
                'defenderId': payload.get('defenderId'), 'challengerLobster': None,
                'defenderLobster': None, 'spectators': payload.get('spectators', []),
                'bets': {}, 'started': False, 'completed': False
            }
        state = arena_betting_state[key]
        if player_id == state['challengerId']: state['challengerLobster'] = lobster_data
        elif player_id == state['defenderId']: state['defenderLobster'] = lobster_data

        if state['challengerLobster'] and state['defenderLobster'] and not state['started']:
            state['started'] = True
            game_state = rooms.get(room_id)
            await start_rpg_battle(room_id, battle_id, game_state, manager)

async def handle_no_lobster_forfeit(websocket, room_id, player_id, rooms, manager, payload):
    game_state = rooms.get(room_id)
    if not game_state: return
    winner = payload.get('winner')
    challenge_slot = payload.get('challengeSlot')

    tribute = game_state['areas'].get('tribute')
    if tribute and challenge_slot is not None:
        challenge_slots = tribute.get('challengeSlots', [])
        if 0 <= challenge_slot - 3 < len(challenge_slots):
            challenge_slots[challenge_slot - 3] = CHALLENGE_SLOT_DONE

    if winner == 'challenge' and swap_challenge_slot(game_state, challenge_slot):
        pass

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message('battleEnded', {
            'actionType': 'battleEnded', 'reason': 'no_available_lobsters', 'gameState': game_state
        }))
    await asyncio.sleep(2.0)
    await _check_tribute_battles_complete(game_state, websocket, room_id, rooms, manager)

async def handle_battle_update_OLD(websocket, room_id, player_id, rooms, manager, payload): pass
async def handle_battle_end_OLD(websocket, room_id, player_id, rooms, manager, payload): pass
async def handle_spectator_bet(websocket, room_id, player_id, rooms, manager, payload): pass
async def handle_battle_bonus_choice(websocket, room_id, player_id, rooms, manager, payload): pass

def _make_battle_action_router(handlers: dict):
    async def handle_battle_action_router(websocket, room_id, player_id, rooms, manager, payload):

        action_t1 = payload.get('actionType')
        action_t2 = payload.get('action_type')
        inner_payload = payload.get('payload', payload)
        action_t3 = inner_payload.get('actionType')
        action_t4 = inner_payload.get('action_type')

        all_actions = [action_t1, action_t2, action_t3, action_t4]

        if 'lobster_selected' in all_actions:
            return await handle_lobster_selected(websocket, room_id, player_id, rooms, manager, inner_payload)

        if 'no_lobster_forfeit' in all_actions:
            return await handle_no_lobster_forfeit(websocket, room_id, player_id, rooms, manager, inner_payload)

        rpg_actions = ['battleAction', 'roll_dice', 'seaweed_choice', 'draw_hp', 'confirm_hp_result', 'claim_battle_reward']

        if any(a in rpg_actions for a in all_actions if a):
            if inner_payload.get('actionType') is None:
                valid_a = next((a for a in all_actions if a in rpg_actions and a != 'battleAction'), 'battleAction')
                inner_payload['actionType'] = valid_a
            return await handle_rpg_battle_action(websocket, room_id, player_id, rooms, manager, inner_payload)

        handler = handlers.get(action_t1 or action_t2)
        if handler: return await handler(websocket, room_id, player_id, rooms, manager, payload)
        await send_error(websocket, f'未知的战斗行动: {action_t1 or action_t2}')

    return handle_battle_action_router

def get_battle_action_handlers():
    return {
        ClientBattleActionTypes.BATTLE_UPDATE: handle_battle_update_OLD,
        ClientBattleActionTypes.BATTLE_END: handle_battle_end_OLD,
        ClientBattleActionTypes.LOBSTER_SELECTED: handle_lobster_selected,
        ClientBattleActionTypes.SPECTATOR_BET: handle_spectator_bet,
        ClientBattleActionTypes.NO_LOBSTER_FORFEIT: handle_no_lobster_forfeit,
        ClientBattleActionTypes.BATTLE_BONUS_CHOICE: handle_battle_bonus_choice,
    }

handle_battle_action = _make_battle_action_router(get_battle_action_handlers())