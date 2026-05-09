# -*- coding: utf-8 -*-
"""
战斗行动路由器 - 通用技能调度中心引擎版 (Hook Pattern)
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
    skill_id = lobster.get('skillId', '')
    if skill_id == 's30': return 12
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
    id = lobster.get('id')
    grade = lobster.get('grade')
    skill_id = lobster.get('skillId', '')
    draws = ['base']
    if grade == 'royal' or id.startswith('title_'): draws.append('equip')
    if skill_id == 's31': draws.append('god')
    return draws

def draw_hp_values(draw_types):
    hp_values = []
    for t in draw_types:
        if t == 'base': hp_values.append(random.choice([2, 3, 4, 5]))
        elif t == 'equip': hp_values.append(random.choice([1, 2, 3, 4]))
        elif t == 'god': hp_values.append(random.choice([1, 2]))
    return hp_values



# ==============================================================================
# 核心引擎：统一技能调度中心 (Skill Executor)
# 所有的技能特效、点数修饰、数值拦截全部集中于此
# ==============================================================================
class SkillExecutor:
    @staticmethod
    def trigger(event_name, player, enemy, battle, ctx):
        logs = []
        skills = player.get('skills', []) if player else []
        enemy_skills = enemy.get('skills', []) if enemy else []
        
        # 1. 战斗初始化阶段
        if event_name == 'battle_start':
            if 's30' in skills:
                player['diceType'] = 12
                logs.append("<color=#00ffff>✨[技能生效-百足] 使用众多的触足，掷骰子使用12面骰！</color><br/>")
            if 's1' in skills:
                battle['init_phase_done'] = True
                battle['phase'] = 'attack_roll'
                player['enraged'] = True
                logs.append("<color=#00ffff>✨[技能生效-疾风] 立即处于行动状态，直接进入攻击回合！</color><br/>")
        
        # 2. 回合开始阶段
        elif event_name == 'turn_start':
            if 's3' in skills:
                player['s3_buff_stacks'] = player.get('s3_buff_stacks', 0) + 1
                logs.append(f"<color=#00ffff>✨[技能生效-蓄势] 回合开始，获得 1 层【增益】(共 {player['s3_buff_stacks']} 层)！</color><br/>")
            if 's10' in skills and player['dmgTaken'] > 0:
                player['dmgTaken'] -= 1
                logs.append(f"<color=#00ffff>✨[技能生效-自愈] 回合开始，自愈能力发动，恢复了 1 点血量！</color><br/>")

        # 3. 掷骰子数值修饰
        elif event_name == 'roll_calc':
            # 状态结算
            if player.get('poisoned_stacks', 0) > 0:
                ctx['roll'] -= 2
                player['poisoned_stacks'] -= 1
                logs.append(f"<br/><color=#00ffff>✨[状态生效-冥毒] 毒发！虚弱导致掷骰点数 -2！</color>")

            # 技能修饰
            if 's22' in skills and ctx['roll'] == 1:
                ctx['roll'] = random.randint(1, player['diceType'])
                player['critChance'] = min(1.0, player['critChance'] + 0.3)
                logs.append(f"<br/><color=#00ffff>✨[技能生效-逆鳞] 掷出 1 点触发重掷，本次掷出 {ctx['roll']} 点，暴击率飙升！</color>")
            if 's26' in skills:
                ctx['roll'] += 3
                player['dmgTaken'] += 1
                logs.append(f"<br/><color=#00ffff>✨[技能生效-燃血] 燃烧鲜血，掷骰点数+3！(自身受伤+1)</color>")
            if 's5' in skills:
                ctx['roll'] += 2
                logs.append(f"<br/><color=#00ffff>✨[技能生效-天佑] 抛掷点数默认 +2！</color>")
            if 's3' in skills:
                buffs = player.get('s3_buff_stacks', 0)
                ctx['roll'] += buffs
                logs.append(f"<br/><color=#00ffff>✨[技能生效-蓄势] 掷骰点数额外增加 {buffs} 点！</color>")
            if 's2' in skills and ctx['roll'] <= 3:
                ctx['roll'] = 6
                logs.append(f"<br/><color=#00ffff>✨[技能生效-稳扎] 点数过低，强制拉升视为 6 点！</color>")

        # 5. 吃海草修饰
        elif event_name == 'seaweed_calc':
            if 's15' in skills:
                ctx['bonus'] = 3
                logs.append(f"🌿 【{player['name']}】<color=#00ffff>✨[技能生效-贪食]</color> 吃草获得额外 +3 投掷点数！")
        
        # 6. 基础伤害计算修饰 (Player: 攻击方)
        elif event_name == 'damage_calc':
            if 's23' in skills:
                stacks = player.get('bloodlust_stacks', 0)
                ctx['base_dmg'] += stacks
                if stacks > 0:
                    logs.append(f"<br/><color=#00ffff>✨[技能生效-嗜血] 嗜血狂化，基础伤害叠加 +{stacks}！</color>")
            if 's4' in skills and ctx['final_roll'] >= player['diceType']:
                ctx['base_dmg'] += 2
                logs.append(f"<br/><color=#00ffff>✨[技能生效-会心] 抛出绝杀上限，基础伤害猛增+2！</color>")
            if 's6' in skills and ctx['final_roll'] % 2 != 0:
                ctx['base_dmg'] += 1
                logs.append(f"<br/><color=#00ffff>✨[技能生效-奇变] 骰出奇数，基础伤害+1！</color>")
            if 's7' in skills and ctx['final_roll'] % 2 == 0:
                ctx['base_dmg'] += 1
                logs.append(f"<br/><color=#00ffff>✨[技能生效-偶成] 骰出偶数，基础伤害+1！</color>")

        # 7. 防御与闪避计算 (Player: 防守方, Enemy: 攻击方)
        elif event_name == 'defense_calc':
            if 's21' in enemy_skills and ctx['base_dmg'] > 0:
                logs.append(f"<br/><color=#00ffff>✨[技能生效-破法] 破法一击，无视对方一切防御与闪避！</color>")
            else:
                if 's18' in skills and random.random() < 0.3:
                    ctx['base_dmg'] = 0
                    logs.append(f"<br/><color=#00ffff>✨[技能生效-幻影] 【{player['name']}】触发闪避，将伤害完全化解！</color>")
                if 's28' in skills and random.random() < 0.2:
                    ctx['base_dmg'] = 0
                    enemy['dmgTaken'] += 1
                    logs.append(f"<br/><color=#00ffff>✨[技能生效-反制] 闪避同时做出反击，【{enemy['name']}】受到 1 点伤害！</color>")
                elif 's17' in skills and ctx['base_dmg'] > 0:
                    ctx['base_dmg'] = max(0, ctx['base_dmg'] - 1)
                    logs.append(f"<br/><color=#00ffff>✨[技能生效-坚甲] 【{player['name']}】触发防御减伤，受到的伤害-1！</color>")

        # 8. 暴击体系 (Player: 攻击方, Enemy: 防守方)
        elif event_name == 'crit_calc':
            ctx['is_crit'] = random.random() < player['critChance']
            ctx['crit_mult'] = 2.0 if 's12' in skills else 1.5
            if 's25' in enemy_skills:
                ctx['crit_mult'] = 1.0  # 铁骨抵消暴击倍率
            
            if ctx['is_crit']:
                battle['critCount'] += 1
                if 's24' in skills:
                    # 龙威震慑：强行清空对手暴击率
                    enemy['critChance'] = 0.0
                    logs.append(f"<br/><color=#00ffff>✨[技能生效-龙威] 龙威震慑！【{enemy['name']}】战意全无，暴击率被强行清零！</color>")
                
                if 's11' in skills: player['critChance'] = player['critChance'] - 0.1
                else: player['critChance'] = 0.0

        # 9. 伤害结算后的追加效果 (Player: 攻击方, Enemy: 防守方)
        elif event_name == 'post_damage':
            if 's29' in skills and enemy['dmgTaken'] > 5:
                ctx['final_dmg'] = 999
                logs.append(f"<br/><color=#00ffff>✨[技能生效-处决] 对手伤势严重，触发【斩杀】！无视剩余血量，直接终结对手！</color>")

            if ctx['final_dmg'] > 0:
                if 's20' in skills:
                    enemy['poisoned_stacks'] = enemy.get('poisoned_stacks', 0) + 1
                if 's19' in enemy_skills:
                    reflect_dmg = ctx['final_dmg'] // 2
                    if reflect_dmg > 0:
                        player['dmgTaken'] += reflect_dmg
                        logs.append(f"<br/><color=#00ffff>✨[技能生效-棘甲] 【{enemy['name']}】的棘甲反弹了 {reflect_dmg} 点伤害！</color>")

        # 10. 抽血量卡数量限制 (Player: 防守方, Enemy: 攻击方)
        elif event_name == 'hp_draw_req':
            if 's8' in enemy_skills:
                ctx['req_cards'] = max(1, ctx['req_cards'] - 1)
                logs.append(f"<br/><color=#00ffff>✨[技能生效-威压] 压制对手生命力，使其少翻 1 张血量卡！</color>")
        
        # 11. 抽血量卡数值篡改 (Player: 防守方, Enemy: 攻击方)
        elif event_name == 'hp_cards_mod':
            if 's9' in enemy_skills and len(ctx['hp_values']) > 0:
                max_val = max(ctx['hp_values'])
                max_idx = ctx['hp_values'].index(max_val)
                ctx['hp_values'][max_idx] = 1
                logs.append(f"<br/><color=#00ffff>✨[技能生效-破绽] 【{enemy['name']}】将对手抽出的最大血量卡强压为 1 点！</color>")
            if 's27' in skills:
                ctx['hp_values'] = [max(3, v) for v in ctx['hp_values']]
                logs.append(f"<br/><color=#00ffff>✨[技能生效-归元] 抽出的低质量血量卡自动提升为 3 点！</color>")

        # 12. 致死判定与免死 (Player: 防守方)
        elif event_name == 'lethal_check':
            if 's16' in skills and not player.get('s16_used'):
                ctx['survived'] = True
                player['s16_used'] = True
                logs.append(f"<br/><color=#00ffff>✨[技能生效-涅槃] 触发【免死】！抵消致命伤！</color>")

        # 13. 受伤存活后的属性变更 (Player: 防守方)
        elif event_name == 'survival_check':
            # 嗜血：基础攻击力永久提升
            if 's23' in skills and ctx.get('damage_taken', 0) > 1:
                player['bloodlust_stacks'] = player.get('bloodlust_stacks', 0) + 1
                logs.append(f"<br/><color=#00ffff>✨[技能生效-嗜血] 受到重创激发了血性，基础攻击力永久 +1！</color>")

            # 暴击率提升逻辑 (需检查是否被 [龙威 s24] 震慑)
            if battle.get('lastAttackWasCrit') and 's24' in enemy_skills:
                player['critChance'] = 0.0
                logs.append(f"<br/><color=#999999>受到[龙威]震慑，战意全无，暴击率无法恢复...</color>")
            else:
                crit_inc = 0.2
                if 's13' in skills:
                    crit_inc = 0.4
                    logs.append(f"<br/><color=#00ffff>✨[技能生效-背水] 受到伤害激发了斗志，本次暴击率提升 40%！</color>")
                player['critChance'] = min(1.0, player['critChance'] + crit_inc)

        # 14. 追加回合判定 (Player: 防守方, Enemy: 攻击方)
        elif event_name == 'post_survival':
            if ctx.get('lastAttackWasCrit') and 's14' in enemy_skills:
                ctx['extra_turn'] = True
                logs.append(f"<br/><color=#00ffff>✨[技能生效-连斩] 狂暴连击！【{enemy['name']}】立刻获得一个全新的行动回合！</color>")

        return "".join(logs)


# ==============================================================================
# 纯净的主流程逻辑
# ==============================================================================
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
        'lastAttackWasCrit': False,
        'p1': {
            'id': defender_id,
            'name': get_player(game_state, defender_id)['name'],
            'lobster': d_lob,
            'lobsterName': d_lob.get('name') or d_lob.get('grade', '普虾'),
            'lobsterGrade': d_lob.get('grade', 'royal'),
            'lobsterId': d_lob.get('id'),
            'diceType': get_dice_type(d_lob),
            'dmgTaken': 0,
            'survivedAttacks': 0,
            'enraged': False,
            'enrage_roll_val': 0,
            'seaweed': get_player(game_state, defender_id).get('seaweed', 0),
            'skills': [d_lob.get('skillId')],
            'skillDesc': d_lob.get('description', ''),
            'critChance': 0.2 if d_lob.get('skillId') == 's11' else 0.0
        },
        'p2': {
            'id': challenger_id,
            'name': get_player(game_state, challenger_id)['name'],
            'lobster': c_lob,
            'lobsterName': c_lob.get('name') or c_lob.get('grade', '普虾'),
            'lobsterGrade': c_lob.get('grade', 'royal'),
            'lobsterId': c_lob.get('id'),
            'diceType': get_dice_type(c_lob),
            'dmgTaken': 0,
            'survivedAttacks': 0,
            'enraged': False,
            'enrage_roll_val': 0,
            'seaweed': get_player(game_state, challenger_id).get('seaweed', 0),
            'skills': [c_lob.get('skillId')],
            'skillDesc': c_lob.get('description', ''),
            'critChance': 0.2 if c_lob.get('skillId') == 's11' else 0.0
        }
    }
    
    p1 = game_state['current_battle']['p1']
    p2 = game_state['current_battle']['p2']

    # 【Hook调度】战斗开始判定
    log_d = SkillExecutor.trigger('battle_start', p1, p2, game_state['current_battle'], {})
    log_c = SkillExecutor.trigger('battle_start', p2, p1, game_state['current_battle'], {})
    
    if p1['enraged'] or p2['enraged']:
        if p1['enraged'] and not p2['enraged']: game_state['current_battle']['activePlayerId'] = p1['id']
        elif p2['enraged'] and not p1['enraged']: game_state['current_battle']['activePlayerId'] = p2['id']

    combo_log = log_d + log_c
    if combo_log: game_state['current_battle']['lastLog'] = combo_log

    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
        make_action_message('battleStart', {
            'actionType': 'battleStart',
            'battleData': game_state['current_battle']
        }))

async def handle_rpg_battle_action(websocket, room_id, player_id, rooms, manager, payload):
    action_type = payload.get('actionType') or payload.get('action_type')
    game_state = rooms.get(room_id)
    if not game_state or 'current_battle' not in game_state: return

    battle = game_state['current_battle']

    if action_type not in ['confirm_hp_result', 'claim_battle_reward'] and player_id != battle.get('activePlayerId') and player_id != battle.get('targetPlayerId'):
        await send_error(websocket, '还没轮到你操作！')
        return

    active_p = battle['p1'] if battle.get('activePlayerId') == battle['p1']['id'] else battle['p2']
    defender_p = battle['p2'] if active_p == battle['p1'] else battle['p1']

    if action_type == 'roll_dice':
        battle['lastLog'] = SkillExecutor.trigger('turn_start', active_p, defender_p, battle, {})
        ctx_roll = {'roll': random.randint(1, active_p['diceType'])}
        
        # 【Hook调度】点数计算
        battle['lastLog'] += SkillExecutor.trigger('roll_calc', active_p, defender_p, battle, ctx_roll)
        roll = ctx_roll['roll']

        if battle['phase'] == 'enrage_roll':
            if not battle['init_phase_done']:
                active_p['enrage_roll_val'] = roll
                active_p['enraged'] = (roll >= 6)
                log_str = '<color=#ff0000>成功进入狂暴！</color>' if active_p['enraged'] else '未达6点，起步失败。'
                battle['lastLog'] += f"<br/>🎲 【{active_p['name']}】起步判定掷出 {roll}点，{log_str}"

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
                    battle['lastLog'] += f"<br/>🎲 【{active_p['name']}】起步掷出 {roll}点，<color=#ff0000>进入狂暴！</color> 开始攻击！"
                    battle['phase'] = 'attack_roll'
                else:
                    battle['lastLog'] += f"<br/>🎲 【{active_p['name']}】起步掷出 {roll}点，起步失败，回合结束。"
                    battle['activePlayerId'] = defender_p['id']
                    next_p = battle['p1'] if battle['activePlayerId'] == battle['p1']['id'] else battle['p2']
                    battle['phase'] = 'attack_roll' if next_p['enraged'] else 'enrage_roll'

        elif battle['phase'] == 'attack_roll':
            battle['currentRoll'] = roll
            battle['lastLog'] += f"<br/>⚔️ 【{active_p['name']}】攻击掷出了 {roll}点！"
            if active_p['lobsterGrade'] == 'grade3': _process_damage(battle, active_p, defender_p, roll, 0)
            else: battle['phase'] = 'seaweed_choice'

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
            
            ctx_weed = {'bonus': bonus}
            # 【Hook调度】吃草修饰
            log_add = SkillExecutor.trigger('seaweed_calc', active_p, defender_p, battle, ctx_weed)
            if log_add: battle['lastLog'] = log_add
            else: battle['lastLog'] = f"🌿 【{active_p['name']}】吃草！获得额外 +{ctx_weed['bonus']} 投掷点数！"
            bonus = ctx_weed['bonus']
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
        hp_values = draw_hp_values(draw_types)[:battle['requiredHPCards']]
        
        ctx_mod = {'hp_values': hp_values}
        # 【Hook调度】血卡被恶意篡改或自我提升
        battle['lastLog'] += SkillExecutor.trigger('hp_cards_mod', target_p, attacker_p, battle, ctx_mod)
        hp_values = ctx_mod['hp_values']

        total_hp = sum(hp_values)
        battle['lastHpDraws'] = hp_values
        dmg = battle['currentDamage']

        target_p['dmgTaken'] += dmg
        battle['phase'] = 'show_hp_result'

        if target_p['dmgTaken'] >= total_hp:
            ctx_lethal = {'survived': False, 'total_hp': total_hp}
            # 【Hook调度】检测免死技能
            log_lethal = SkillExecutor.trigger('lethal_check', target_p, attacker_p, battle, ctx_lethal)
            
            if ctx_lethal['survived']:
                target_p['survivedAttacks'] += 1
                battle['nextPhase'] = 'attack_roll' if target_p['enraged'] else 'enrage_roll'
                battle['nextActivePlayerId'] = target_p['id']
                battle['nextLog'] = f"🎴 【{target_p['name']}】本将被斩杀...{log_lethal}"
            else:
                battle['nextPhase'] = 'reward_choice'
                battle['winnerId'] = attacker_p['id']
                battle['winnerName'] = attacker_p['name']
                battle['nextLog'] = f"🎴 【{target_p['name']}】抽到血量: {total_hp}，累计受伤已达: <color=#ff0000>{target_p['dmgTaken']}点</color>...<br/>💀 承受不住，惨遭斩杀！"
        else:
            target_p['survivedAttacks'] += 1
            battle['nextActivePlayerId'] = target_p['id']
            battle['nextPhase'] = 'attack_roll' if target_p['enraged'] else 'enrage_roll'
            battle['nextLog'] = f"🎴 【{target_p['name']}】抽到血量: {total_hp}，累计受伤达: <color=#ffaa00>{target_p['dmgTaken']}点</color>！<br/>🛡️ 惊险扛下伤害！"
            # 【Hook调度】大难不死后触发
            battle['nextLog'] += SkillExecutor.trigger('survival_check', target_p, attacker_p, battle, {'damage_taken': dmg})
            
        ctx_turn = {'extra_turn': False, 'lastAttackWasCrit': battle.get('lastAttackWasCrit')}
        # 【Hook调度】生存判定完毕，查验攻击方是否有连动能力
        battle['nextLog'] += SkillExecutor.trigger('post_survival', target_p, attacker_p, battle, ctx_turn)
        if ctx_turn['extra_turn'] and battle['nextPhase'] != 'reward_choice':
            battle['nextPhase'] = 'attack_roll'
            battle['nextActivePlayerId'] = attacker_p['id']

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
        if player_id != battle.get('winnerId'): return
        winner_p = get_player(game_state, player_id)
        bf = make_broadcast_fn(manager.send_to_room, room_id)
        if reward_type == 'coins': await update_resources(winner_p, {'coins': 2}, broadcast_fn=bf)
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
    ctx_dmg = {'final_roll': final_roll, 'base_dmg': calculate_damage(final_roll)}
    # 【Hook调度】基础伤害加成 (攻击方)
    battle['lastLog'] += SkillExecutor.trigger('damage_calc', active_p, defender_p, battle, ctx_dmg)
    
    is_crit = False
    crit_mult = 1.0
    # 【Hook调度】暴击系统算力 (仅当有基础伤害时触发)
    if ctx_dmg['base_dmg'] > 0:
        ctx_crit = {'is_crit': False, 'crit_mult': 1.5}
        battle['lastLog'] += SkillExecutor.trigger('crit_calc', active_p, defender_p, battle, ctx_crit)
        is_crit = ctx_crit['is_crit']
        crit_mult = ctx_crit['crit_mult']
        
        # 若触发暴击，先对伤害进行翻倍结算
        if is_crit:
            ctx_dmg['base_dmg'] = math.ceil(ctx_dmg['base_dmg'] * crit_mult)

    # 【Hook调度】防守减免与闪避 (在暴击结算后执行，支持暴击 Miss)
    battle['lastLog'] += SkillExecutor.trigger('defense_calc', defender_p, active_p, battle, ctx_dmg)
    final_dmg = ctx_dmg['base_dmg']

    ctx_post = {'final_dmg': final_dmg}
    # 【Hook调度】伤害造成后的追击特效 (反伤、吸血、处决、挂毒)
    battle['lastLog'] += SkillExecutor.trigger('post_damage', active_p, defender_p, battle, ctx_post)
    final_dmg = ctx_post['final_dmg']

    battle['currentDamage'] = final_dmg
    battle['lastAttackWasCrit'] = is_crit

    crit_str = f"<color=#ffaa00>💥【暴击】(倍率{crit_mult}x)</color>" if is_crit else ""
    battle['lastLog'] += f"<br/>🎯 最终判定 {final_roll}点！{crit_str}造成了 <color=#ff0000>{final_dmg}点</color> 伤害！"

    battle['phase'] = 'hp_draw'
    battle['targetPlayerId'] = defender_p['id']
    
    ctx_req = {'req_cards': len(get_hp_card_draws(defender_p['lobster']))}
    # 【Hook调度】抽卡数锁定限制
    battle['lastLog'] += SkillExecutor.trigger('hp_draw_req', defender_p, active_p, battle, ctx_req)
    battle['requiredHPCards'] = ctx_req['req_cards']


async def _finalize_rpg_battle(websocket, room_id, game_state, manager, rooms):
    battle = game_state['current_battle']
    winner_id = battle['winnerId']
    challenge_slot = battle['challengeSlotIndex']
    p1 = battle['p1']
    p2 = battle['p2']

    challenger_id = battle['original_challenger_id']
    if winner_id == challenger_id: swap_challenge_slot(game_state, challenge_slot)

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
            'actionType': 'battleEnded', 'gameState': game_state
        }))
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
                'actionType': 'battleStart', 'battleQueue': game_state['battleQueue']
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

    if winner == 'challenge' and swap_challenge_slot(game_state, challenge_slot): pass

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
        action_type = payload.get('actionType') or payload.get('action_type')
        inner_payload = payload.get('payload', payload)
        inner_action_type = inner_payload.get('actionType') or inner_payload.get('action_type')

        all_actions = [action_type, inner_action_type]

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

        handler = handlers.get(action_type)
        if handler: return await handler(websocket, room_id, player_id, rooms, manager, payload)
        await send_error(websocket, f'未知的战斗行动: {action_type}')
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