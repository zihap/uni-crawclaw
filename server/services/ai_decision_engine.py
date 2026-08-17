# -*- coding: utf-8 -*-
"""
AI决策引擎 — 加权随机 + 个性系统
"""

import random
import math
from typing import List, Dict, Any, Optional
from utils.constants import AREAS, MARKET_PRICES, GRADE_UPGRADE_SEAWEED
from services.tribute_card_effects import check_cage_trade


def softmax_choice(scores: List[float], temperature: float = 1.0) -> int:
    """加权随机选择，temperature越低越确定性"""
    if not scores:
        return 0
    if temperature <= 0.001:
        return scores.index(max(scores))

    max_score = max(scores)
    exp_scores = [math.exp((s - max_score) / temperature) for s in scores]
    total = sum(exp_scores)
    if total == 0:
        return random.randint(0, len(scores) - 1)

    probs = [e / total for e in exp_scores]
    r = random.random()
    cumulative = 0.0
    for i, p in enumerate(probs):
        cumulative += p
        if r <= cumulative:
            return i
    return len(scores) - 1


def _get_available_slots(game_state: dict, area_name: str) -> List[int]:
    area_data = game_state['areas'].get(area_name)
    if not area_data:
        return []
    slots = area_data.get('slots', [])
    return [i for i, v in enumerate(slots) if v is None]


def _get_area_base_value(area_name: str, personality: dict) -> float:
    base_values = {
        'tribute': 0.9, 'breeding': 0.7, 'shrimp_catching': 0.6,
        'seafood_market': 0.5, 'marketplace': 0.4,
    }
    base = base_values.get(area_name, 0.5)
    agg = personality.get('aggressiveness', 0.5)
    greed = personality.get('greed', 0.5)
    patience = personality.get('patience', 0.5)
    if area_name == 'tribute': base += agg * 0.2
    elif area_name == 'breeding': base += patience * 0.3
    elif area_name == 'shrimp_catching': base += greed * 0.2
    elif area_name == 'seafood_market': base += greed * 0.3
    elif area_name == 'marketplace': base += (1 - patience) * 0.1
    return base


def _get_slot_position_value(slot_index: int, total_slots: int, decay: float = 0.5) -> float:
    if total_slots <= 1: return 1.0
    return 1.0 - (slot_index / total_slots) * decay


def _has_upgradeable_lobster(ai_player: dict) -> bool:
    """检测AI是否有可培养的灵螯（可升级的非royal灵螯）"""
    has_seaweed = ai_player.get('seaweed', 0) > 0
    has_cage = ai_player.get('cages', 0) > 0
    has_coins_for_royal = ai_player.get('coins', 0) >= 3
    can_afford_royal = has_cage or has_coins_for_royal
    for l in ai_player.get('lobsters', []):
        g = l.get('grade', 'normal')
        if g == 'royal':
            continue
        if g == 'grade1' and not can_afford_royal:
            continue
        return True
    return False


def decide_placement(game_state: dict, ai_player: dict) -> dict:
    personality = ai_player.get('aiPersonality', {})
    randomness = personality.get('randomness', 0.3)
    temperature = 0.5 + randomness * 1.5
    has_upgradeable = _has_upgradeable_lobster(ai_player)
    candidates = []
    for area_idx, area_name in enumerate(AREAS):
        available_slots = _get_available_slots(game_state, area_name)
        if not available_slots: continue
        if area_name == 'marketplace':
            current_round = game_state.get('currentRound', 1)
            available_slots = [s for s in available_slots
                             if (s == 0 and current_round >= 2) or (s == 1 and current_round >= 3) or (s == 2 and current_round >= 4)]
        if area_name == 'tribute':
            current_round = game_state.get('currentRound', 1)
            available_slots = [s for s in available_slots if s != 2 or current_round >= 4]
        for slot_idx in available_slots:
            area_value = _get_area_base_value(area_name, personality)
            if not has_upgradeable:
                if area_name == 'breeding':
                    area_value *= 0.5
                elif area_name == 'shrimp_catching':
                    area_value *= 1.3
            decay = 0.7 if area_name == 'tribute' else 0.5
            slot_value = _get_slot_position_value(slot_idx, len(game_state['areas'][area_name]['slots']), decay)
            noise = random.uniform(-0.1, 0.1) * randomness
            score = area_value * slot_value + noise
            candidates.append({'area_index': area_name, 'slot_index': slot_idx, 'score': score})
    if not candidates:
        for area_name in AREAS:
            slots = _get_available_slots(game_state, area_name)
            if slots: return {'area_index': area_name, 'slot_index': slots[0]}
        return {'area_index': AREAS[0], 'slot_index': 0}
    scores = [c['score'] for c in candidates]
    chosen_idx = softmax_choice(scores, temperature=temperature)
    chosen = candidates[chosen_idx]
    return {'area_index': chosen['area_index'], 'slot_index': chosen['slot_index']}


def decide_settlement_action(game_state: dict, ai_player: dict, settlement_state: dict) -> dict:
    area_type = settlement_state.get('areaType', '')
    if area_type == 'shrimp_catching': return _decide_shrimp_catching(game_state, ai_player, settlement_state)
    elif area_type == 'seafood_market': return _decide_market(game_state, ai_player, settlement_state)
    elif area_type == 'breeding': return _decide_breeding(game_state, ai_player, settlement_state)
    elif area_type == 'tribute': return _decide_tribute(game_state, ai_player, settlement_state)
    elif area_type == 'marketplace': return _decide_marketplace(game_state, ai_player, settlement_state)
    else: return {'action_type': 'skip', 'payload': {}}


def _decide_shrimp_catching(game_state: dict, ai_player: dict, settlement_state: dict) -> dict:
    personality = ai_player.get('aiPersonality', {})
    greed = personality.get('greed', 0.5)
    randomness = personality.get('randomness', 0.3)
    temperature = 0.3 + randomness
    step = settlement_state.get('step', 'waiting_confirm')
    if step == 'waiting_choice':
        lobster_score = 0.7 + greed * 0.3
        seaweed_score = 0.4 + (1 - greed) * 0.3
        scores = [lobster_score, seaweed_score]
        choice = softmax_choice(scores, temperature)
        if choice == 0: return {'action_type': 'choose_either', 'payload': {'choice': 'lobster'}}
        else: return {'action_type': 'choose_either', 'payload': {'choice': 'seaweed'}}
    return {'action_type': 'confirm', 'payload': {}}


def _decide_market(game_state: dict, ai_player: dict, settlement_state: dict) -> dict:
    personality = ai_player.get('aiPersonality', {})
    greed = personality.get('greed', 0.5)
    randomness = personality.get('randomness', 0.3)
    temperature = 0.5 + randomness
    market_area = game_state['areas']['seafood_market']
    dynamic_prices = market_area.get('dynamicPrices', MARKET_PRICES)
    options = []
    player_coins = ai_player.get('coins', 0)
    
    # Check for cage_trade buff
    cage_trade = check_cage_trade(ai_player)
    cage_buy_price = dynamic_prices.get('buyCage', 4)
    cage_sell_price = dynamic_prices.get('sellCage', 4)
    if cage_trade:
        cage_buy_price = max(1, cage_buy_price - cage_trade['buyDiscount'])
        cage_sell_price = cage_sell_price + cage_trade['sellBonus']
    
    if len(ai_player.get('lobsters', [])) > 0:
        sell_price = dynamic_prices.get('sellLobster', 2)
        options.append(('sell_lobster', sell_price * 0.3 + greed * 0.2))
    buy_price = dynamic_prices.get('buyLobster', 3)
    if player_coins >= buy_price:
        options.append(('buy_lobster', (4 - buy_price) * 0.2 + greed * 0.1))
    if ai_player.get('seaweed', 0) > 0:
        options.append(('sell_seaweed', 0.3 + greed * 0.2))
    seaweed_price = dynamic_prices.get('buySeaweed', 1)
    if player_coins >= seaweed_price:
        options.append(('buy_seaweed', 0.2 + (1 - greed) * 0.1))
    bulk_price = dynamic_prices.get('buySeaweed3', 4)
    if player_coins >= bulk_price:
        options.append(('buy_seaweed_3', 0.25 + greed * 0.15))
    if ai_player.get('cages', 0) > 0:
        options.append(('sell_cage', 0.3 + greed * 0.2))
    if player_coins >= cage_buy_price:
        options.append(('buy_cage', 0.2 + (1 - greed) * 0.1))
    hire_price = MARKET_PRICES.get('hireHeadman', 6)
    hire_slots = game_state.get('hireSlots', [None] * 8)
    current_round = game_state.get('currentRound', 1)
    if player_coins >= hire_price:
        # 雇佣槽位：按回合数开放，已占用的不可用
        available_hire = []
        for s in range(8):
            if hire_slots[s] is not None:
                continue
            if s <= 1 and current_round >= 2:
                available_hire.append(s)
            elif 2 <= s <= 3 and current_round >= 3:
                available_hire.append(s)
            elif 4 <= s <= 7 and current_round >= 4:
                available_hire.append(s)
        if available_hire:
            options.append(('hire_headman_slot', 0.5 + (1 - greed) * 0.1))
    if not options: return {'action_type': 'skip', 'payload': {}}
    options.append(('skip', 0.1))
    action_types = [o[0] for o in options]
    scores = [o[1] for o in options]
    chosen = softmax_choice(scores, temperature)
    action = action_types[chosen]
    if action == 'hire_headman_slot':
        slot = random.choice(available_hire)
        return {'action_type': action, 'payload': {'slotIndex': slot}}
    return {'action_type': action, 'payload': {}}


def _decide_breeding(game_state: dict, ai_player: dict, settlement_state: dict) -> dict:
    upgradeable = [l for l in ai_player.get('lobsters', []) if l.get('grade', 'normal') in ('normal', 'grade3', 'grade2', 'grade1')]
    if not upgradeable: return {'action_type': 'skip', 'payload': {}}

    has_seaweed = ai_player.get('seaweed', 0) > 0
    has_cage = ai_player.get('cages', 0) > 0
    has_coins_for_royal = ai_player.get('coins', 0) >= 3
    can_afford_royal = has_cage or has_coins_for_royal

    # 过滤掉无法升级到下一等级的灵螯
    def is_upgradeable(lobster):
        g = lobster.get('grade', 'normal')
        if g == 'grade1' and not can_afford_royal:
            return False  # grade1→royal需要额外资源，无法负担则排除
        if g == 'grade2' and has_seaweed and not can_afford_royal:
            return True  # grade2吃草→royal无法负担，但可以不吃草正常升级grade2→grade1
        return True

    upgradeable = [l for l in upgradeable if is_upgradeable(l)]
    if not upgradeable: return {'action_type': 'skip', 'payload': {}}

    # 构建候选列表：每只灵螯作为一个候选，权重=品级越高权重越高
    grade_weight = {'normal': 1, 'grade3': 2, 'grade2': 3, 'grade1': 4}
    candidates = []
    for lobster in upgradeable:
        w = grade_weight.get(lobster.get('grade', 'normal'), 1)
        candidates.append((lobster, w))

    # 加权随机选择灵螯
    lobsters_list = [c[0] for c in candidates]
    weights = [c[1] for c in candidates]
    chosen_lobster = random.choices(lobsters_list, weights=weights, k=1)[0]
    lobster_index = ai_player['lobsters'].index(chosen_lobster)
    old_grade = chosen_lobster.get('grade', 'normal')

    # 判断是否吃草跳级
    use_seaweed = False
    seaweed_target = GRADE_UPGRADE_SEAWEED.get(old_grade)
    if has_seaweed and seaweed_target:
        # 吃草跳到royal需要额外资源
        if seaweed_target == 'royal' and not can_afford_royal:
            use_seaweed = False
        else:
            use_seaweed = random.random() < min(0.5, 0.1 + ai_player.get('seaweed', 0) * 0.1)

    payload = {'lobsterIndex': lobster_index}
    if use_seaweed:
        payload['useSeaweed'] = True
        target = GRADE_UPGRADE_SEAWEED.get(old_grade)
        if target == 'royal':
            if has_cage and has_coins_for_royal:
                payload['royalCostType'] = random.choice(['cage', 'coin'])
            elif has_cage:
                payload['royalCostType'] = 'cage'
            else:
                payload['royalCostType'] = 'coin'
            payload['royalRewardType'] = random.choice(['de', 'wang'])
            title_cards = game_state.get('gameTitleCards', [])
            if title_cards:
                payload['selectedTitleId'] = random.choice(title_cards).get('id')
    elif old_grade == 'grade1':
        if not can_afford_royal:
            non_grade1 = [l for l in upgradeable if l.get('grade', 'normal') != 'grade1']
            if non_grade1:
                chosen_lobster = random.choices(non_grade1, weights=[grade_weight.get(l.get('grade', 'normal'), 1) for l in non_grade1], k=1)[0]
                lobster_index = ai_player['lobsters'].index(chosen_lobster)
                old_grade = chosen_lobster.get('grade', 'normal')
            else:
                return {'action_type': 'skip', 'payload': {}}
        else:
            if has_cage and has_coins_for_royal:
                payload['royalCostType'] = random.choice(['cage', 'coin'])
            elif has_cage:
                payload['royalCostType'] = 'cage'
            else:
                payload['royalCostType'] = 'coin'
            payload['royalRewardType'] = random.choice(['de', 'wang'])
            title_cards = game_state.get('gameTitleCards', [])
            if title_cards:
                payload['selectedTitleId'] = random.choice(title_cards).get('id')

    return {'action_type': 'cultivateLobster', 'payload': payload}


def _can_afford(player, req):
    if req.get('coins', 0) > player.get('coins', 0): return False
    if req.get('seaweed', 0) > player.get('seaweed', 0): return False
    if req.get('cages', 0) > player.get('cages', 0): return False
    lobster_reqs = req.get('lobsters', {})
    grade_values = {'normal': 0, 'grade3': 1, 'grade2': 2, 'grade1': 3, 'royal': 4}
    for grade_key, count in lobster_reqs.items():
        needed_val = grade_values.get(grade_key, 0)
        available = sum(1 for l in player.get('lobsters', []) if grade_values.get(l.get('grade', 'normal'), 0) >= needed_val)
        if available < count: return False
    return True


def _decide_tribute(game_state: dict, ai_player: dict, settlement_state: dict) -> dict:
    personality = ai_player.get('aiPersonality', {})
    greed = personality.get('greed', 0.5)
    randomness = personality.get('randomness', 0.3)
    temperature = 0.5 + randomness
    pending = game_state.get('pendingTributeChoice')
    if pending and pending.get('playerId') == ai_player['id']:
        return _decide_tribute_choice(game_state, ai_player, pending)
    taverns = game_state.get('taverns', [])
    if not taverns: return {'action_type': 'skip', 'payload': {}}
    best_option = None
    best_score = -1
    for tavern_idx, tavern in enumerate(taverns):
        for card in tavern.get('cards', []):
            req = card.get('requirements', {})
            if not _can_afford(ai_player, req): continue
            reward = card.get('reward', {})
            score = reward.get('de', 0) * 2 + reward.get('wang', 0) * 2 + greed * 0.5
            if score > best_score:
                best_score = score
                best_option = {'tavern_idx': tavern_idx, 'tavern': tavern, 'card': card}
    if best_option:
        card = best_option['card']
        req = card.get('requirements', {})
        lobster_reqs = req.get('lobsters', {})
        grade_values = {'normal': 0, 'grade3': 1, 'grade2': 2, 'grade1': 3, 'royal': 4}
        selected_lobster_ids = []
        if lobster_reqs:
            available = [(l, grade_values.get(l.get('grade', 'normal'), 0)) for l in ai_player.get('lobsters', [])]
            available.sort(key=lambda x: x[1])
            used = set()
            for grade_key, count in lobster_reqs.items():
                req_val = grade_values.get(grade_key, 0)
                matched = 0
                for i, (lobster, val) in enumerate(available):
                    if i not in used and val >= req_val and matched < count:
                        selected_lobster_ids.append(lobster.get('id'))
                        used.add(i)
                        matched += 1
        return {'action_type': 'submitTribute', 'payload': {
            'tavernId': best_option['tavern_idx'],
            'cardId': card.get('id'),
            'selectedLobsterIds': selected_lobster_ids
        }}
    return {'action_type': 'skip', 'payload': {}}


def _decide_tribute_choice(game_state: dict, ai_player: dict, pending: dict) -> dict:
    choice_type = pending.get('choiceType')
    personality = ai_player.get('aiPersonality', {})
    greed = personality.get('greed', 0.5)
    aggressiveness = personality.get('aggressiveness', 0.5)
    if choice_type == 'buy_advanced_lobster':
        options = pending.get('options', [])
        player_coins = ai_player.get('coins', 0)
        for opt in options:
            grade = opt.get('grade', 'normal')
            cost = opt.get('cost', 0)
            if player_coins >= cost:
                grade_values = {'grade3': 1, 'grade2': 2, 'grade1': 3}
                value = grade_values.get(grade, 0)
                if value * greed > cost * 0.3:
                    return {'action_type': 'submitTributeChoice', 'payload': {'taskId': pending.get('taskId'), 'choice': {'grade': grade, 'cost': cost}}}
        return {'action_type': 'submitTributeChoice', 'payload': {'taskId': pending.get('taskId'), 'choice': {'grade': 'skip', 'cost': 0}}}
    elif choice_type == 'discard_attack':
        if aggressiveness * 0.7 > 0.3:
            return {'action_type': 'submitTributeChoice', 'payload': {'taskId': pending.get('taskId'), 'choice': {'action': 'attack'}}}
        else:
            return {'action_type': 'submitTributeChoice', 'payload': {'taskId': pending.get('taskId'), 'choice': {'action': 'discard', 'targetType': 'lobster'}}}
    return {'action_type': 'skip', 'payload': {}}


def _decide_marketplace(game_state: dict, ai_player: dict, settlement_state: dict) -> dict:
    personality = ai_player.get('aiPersonality', {})
    greed = personality.get('greed', 0.5)
    randomness = personality.get('randomness', 0.3)
    temperature = 0.5 + randomness
    downtown_cards = game_state.get('downtownCards', [])
    if not downtown_cards: return {'action_type': 'skip', 'payload': {}}
    available_cards = [c for c in downtown_cards if not c.get('usedThisRound')]
    if not available_cards: return {'action_type': 'skip', 'payload': {}}
    card_scores = []
    for card in available_cards:
        action = card.get('action', {})
        action_type = action.get('type', '')
        auto = action.get('auto', False)
        score = 0.5
        if auto: score += 0.2
        if action_type in ('black_market', 'bazaar', 'academy'): score += greed * 0.3
        elif action_type == 'charity': score += (1 - greed) * 0.3
        elif action_type == 'inn': score += 0.3
        elif action_type == 'breeding_4': score += greed * 0.4
        card_scores.append((card, score))
    if not card_scores: return {'action_type': 'skip', 'payload': {}}
    cards = [c[0] for c in card_scores]
    scores = [c[1] for c in card_scores]
    chosen = softmax_choice(scores, temperature)
    return {'action_type': 'executeDowntownAction', 'payload': {'cardIndex': chosen}}


def decide_battle_action(game_state: dict, ai_player: dict, battle: dict) -> dict:
    personality = ai_player.get('aiPersonality', {})
    aggressiveness = personality.get('aggressiveness', 0.5)
    caution = personality.get('caution', 0.5)
    randomness = personality.get('randomness', 0.3)
    temperature = 0.3 + randomness
    phase = battle.get('phase', '')
    if phase == 'lobster_select': return _decide_battle_lobster(game_state, ai_player, battle, temperature)
    elif phase in ('start_roll', 'attack_roll'): return {'actionType': 'roll_dice', 'payload': {}}
    elif phase == 'seaweed_choice': return _decide_seaweed(game_state, ai_player, battle, aggressiveness, temperature)
    elif phase == 'hp_draw': return {'actionType': 'draw_hp', 'payload': {}}
    elif phase in ('hp_confirm', 'show_hp_result'): return {'actionType': 'confirm_hp_result', 'payload': {}}
    elif phase == 'reward_choice': return _decide_battle_reward(game_state, ai_player, battle, greed=personality.get('greed', 0.5), temperature=temperature)
    elif phase == 'no_lobster': return {'actionType': 'no_lobster_forfeit', 'payload': {}}
    else: return {'actionType': 'roll_dice', 'payload': {}}


def _decide_battle_lobster(game_state, ai_player, battle, temperature):
    available = [l for l in ai_player.get('lobsters', []) if not l.get('used') and not l.get('selectedForBattle')]
    if not available: return {'actionType': 'no_lobster_forfeit', 'payload': {}}
    grade_values = {'normal': 0, 'grade3': 1, 'grade2': 2, 'grade1': 3, 'royal': 4}
    scores = [grade_values.get(l.get('grade', 'normal'), 0) + random.uniform(-0.2, 0.2) for l in available]
    chosen = softmax_choice(scores, temperature)
    return {'actionType': 'lobster_selected', 'payload': {'lobsterId': available[chosen].get('id')}}


def _decide_seaweed(game_state, ai_player, battle, aggressiveness, temperature):
    if ai_player.get('seaweed', 0) <= 0: return {'actionType': 'seaweed_choice', 'payload': {'useSeaweed': False}}
    gap = battle.get('targetValue', 6) - battle.get('currentRoll', 0)
    use_probability = min(1.0, max(0.0, gap * 0.3 + aggressiveness * 0.3))
    return {'actionType': 'seaweed_choice', 'payload': {'useSeaweed': random.random() < use_probability}}


def _decide_battle_reward(game_state, ai_player, battle, greed, temperature):
    scores = [greed * 0.7, (1 - greed) * 0.6 + 0.3]
    choice = softmax_choice(scores, temperature)
    if choice == 0: return {'actionType': 'claim_battle_reward', 'payload': {'rewardType': 'coins'}}
    else: return {'actionType': 'claim_battle_reward', 'payload': {'rewardType': 'upgrade'}}


def decide_endgame_score_choice(ai_player: dict, card: dict) -> dict:
    from services.tribute_card_effects import get_endgame_choices
    choices = get_endgame_choices(ai_player, card)
    if not choices: return {}
    de = ai_player.get('de', 0)
    wang = ai_player.get('wang', 0)
    if de <= wang:
        for c in choices:
            if 'de' in str(c).lower(): return c
    else:
        for c in choices:
            if 'wang' in str(c).lower(): return c
    return choices[0] if choices else {}
