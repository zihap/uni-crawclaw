# -*- coding: utf-8 -*-
"""
上供卡效果处理模块
"""

from typing import Dict, List, Optional


def has_perma_buff(player: dict, buff_name: str) -> bool:
    """检查玩家是否有指定光环"""
    return buff_name in player.get('permaBuffs', [])


def check_breed_bonus(player: dict) -> bool:
    """检查是否有培养加成光环"""
    return has_perma_buff(player, 'permaBuff_breed_bonus')


def check_market_rule(player: dict) -> Optional[Dict]:
    """检查是否有市场规则光环，返回规则配置"""
    if not has_perma_buff(player, 'permaBuff_market_rule'):
        return None
    return {'buyPrice': 1, 'canSell': False}


def check_tribute_discount(player: dict) -> Optional[Dict]:
    """检查是否有上贡折扣光环，返回折扣配置"""
    coin_discount = 1 if has_perma_buff(player, 'permaBuff_tribute_discount_coin') else 0
    lobster_discount = 1 if has_perma_buff(player, 'permaBuff_tribute_discount_lobster') else 0
    if coin_discount == 0 and lobster_discount == 0:
        return None
    return {'coinDiscount': coin_discount, 'lobsterDiscount': lobster_discount}


def check_battle_bonus(player: dict) -> bool:
    """检查是否有斗龙虾奖励光环"""
    return has_perma_buff(player, 'permaBuff_battle_bonus')


def check_bet_bonus(player: dict) -> bool:
    """检查是否有押注奖励光环"""
    return has_perma_buff(player, 'permaBuff_bet_bonus')


def check_cage_trade(player: dict) -> Optional[Dict]:
    """检查是否有虾笼交易优化光环，返回配置"""
    if not has_perma_buff(player, 'permaBuff_cage_trade'):
        return None
    return {'buyDiscount': 1, 'sellBonus': 1}


def check_adjacent_action(player: dict) -> bool:
    """检查是否有里长相邻行动光环"""
    return has_perma_buff(player, 'permaBuff_adjacent_action')


def get_adjacent_slots(slot_index: int, total_slots: int) -> List[int]:
    """获取相邻位置索引列表
    
    Args:
        slot_index: 当前位置索引
        total_slots: 总位置数
    
    Returns:
        相邻位置索引列表
    """
    if total_slots <= 1:
        return []
    if slot_index == 0:
        return [1]  # 最左边只有右边相邻
    elif slot_index == total_slots - 1:
        return [total_slots - 2]  # 最右边只有左边相邻
    else:
        return [slot_index - 1, slot_index + 1]  # 中间位置有左右相邻


# 各区域位置的资源奖励映射 (用于相邻行动 - 只包含资源，不包含行动次数)
SLOT_REWARDS = {
    'shrimp_catching': [
        {'coins': 1, 'cages': 1},
        {'cages': 1},
        {'coins': 1},
        {}
    ],
    'seafood_market': [
        {'coins': 1},
        {},
        {'coins': 1},
        {'coins': 2}
    ],
    'breeding': [
        {'seaweed': 1},
        {},
        {'coins': 1},
        {}
    ],
    'tribute': [
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {}
    ],
    'marketplace': [
        {},
        {},
        {}
    ]
}


def get_adjacent_rewards(area_name: str, slot_index: int, total_slots: int) -> Dict:
    """获取相邻位置的资源奖励汇总
    
    Args:
        area_name: 区域名称
        slot_index: 当前位置索引
        total_slots: 总位置数
    
    Returns:
        奖励字典
    """
    adjacent_indices = get_adjacent_slots(slot_index, total_slots)
    if not adjacent_indices:
        return {}
    
    rewards = SLOT_REWARDS.get(area_name, [])
    if not rewards:
        return {}
    
    total_reward = {}
    for adj_idx in adjacent_indices:
        if adj_idx < len(rewards):
            for key, value in rewards[adj_idx].items():
                if value:
                    total_reward[key] = total_reward.get(key, 0) + value
    
    return total_reward


def apply_instant_effect(player: dict, card: dict, game_state: dict) -> dict:
    """
    根据 effectType 分发到对应的即时效果处理方法
    
    Args:
        player: 玩家数据
        card: 上供卡数据
        game_state: 游戏状态
    
    Returns:
        即时效果结果 dict
    """
    effect_type = card.get('effectType', '')
    
    if effect_type == 'instant_breed':
        # 执行3次培养龙虾升级（每次升级1个龙虾1品）
        breed_count = 3
        lobsters = player.get('lobsters', [])
        upgrade_count = 0
        for lobster in lobsters:
            if upgrade_count >= breed_count:
                break
            current_grade = lobster.get('grade', 'normal')
            # 每次培养升级1品
            if current_grade == 'normal':
                lobster['grade'] = 'grade3'
                upgrade_count += 1
            elif current_grade == 'grade3':
                lobster['grade'] = 'grade2'
                upgrade_count += 1
            elif current_grade == 'grade2':
                lobster['grade'] = 'grade1'
                upgrade_count += 1
            elif current_grade == 'grade1':
                lobster['grade'] = 'royal'
                upgrade_count += 1
        return {'upgraded': upgrade_count}
    
    elif effect_type == 'instant_upgrade_all':
        lobsters = player.get('lobsters', [])
        for lobster in lobsters:
            current_grade = lobster.get('grade', 'normal')
            if current_grade == 'normal':
                lobster['grade'] = 'grade3'
            elif current_grade == 'grade3':
                lobster['grade'] = 'grade2'
            elif current_grade == 'grade2':
                lobster['grade'] = 'grade1'
            elif current_grade == 'grade1':
                lobster['grade'] = 'royal'
        return {}
    
    elif effect_type == 'instant_gain_cages':
        player['cages'] = player.get('cages', 0) + 2
        return {}
    
    elif effect_type == 'instant_buy_advanced_lobster':
        return {'needChoice': True, 'choiceType': 'buy_advanced_lobster', 'options': [
            {'cost': 1, 'grade': 'grade3'},
            {'cost': 2, 'grade': 'grade2'},
            {'cost': 3, 'grade': 'grade1'}
        ]}
    
    elif effect_type == 'instant_discard_attack':
        return {'needChoice': True, 'choiceType': 'discard_attack'}
    
    return {}


def apply_aura_effect(player: dict, card: dict) -> dict:
    """
    返回光环效果要设置的 permaBuff
    
    Args:
        player: 玩家数据
        card: 上供卡数据
    
    Returns:
        permaBuff 字典
    """
    effect_type = card.get('effectType', '')
    
    aura_to_buff_map = {
        'aura_breed_bonus': 'permaBuff_breed_bonus',
        'aura_adjacent_action': 'permaBuff_adjacent_action',
        'aura_tribute_discount_coin': 'permaBuff_tribute_discount_coin',
        'aura_tribute_discount_lobster': 'permaBuff_tribute_discount_lobster',
        'aura_market_rule': 'permaBuff_market_rule',
        'aura_battle_bonus': 'permaBuff_battle_bonus',
        'aura_bet_bonus': 'permaBuff_bet_bonus',
        'aura_endgame_score': 'permaBuff_endgame_score',
        'aura_round_seaweed': 'permaBuff_round_seaweed',
        'aura_cage_trade': 'permaBuff_cage_trade',
        'aura_round_coin': 'permaBuff_round_coin'
    }
    
    buff_key = aura_to_buff_map.get(effect_type, '')
    if buff_key:
        return {buff_key: True}
    
    return {}


def get_endgame_choices(player: dict, card: dict) -> List[dict]:
    """
    返回终局得分选项
    
    Args:
        player: 玩家数据
        card: 上供卡数据
    
    Returns:
        终局选择列表
    """
    cost_resource_type = card.get('costResourceType', 'coins')
    
    if cost_resource_type == 'coins':
        return [
            {'cost': 3, 'reward': 1},
            {'cost': 5, 'reward': 2},
            {'cost': 8, 'reward': 3}
        ]
    elif cost_resource_type == 'seaweed':
        return [
            {'cost': 2, 'reward': 1},
            {'cost': 4, 'reward': 2},
            {'cost': 7, 'reward': 3}
        ]
    
    return []


def apply_endgame_choice(player: dict, card: dict, choice: dict) -> bool:
    """
    应用终局选择
    
    Args:
        player: 玩家数据
        card: 上供卡数据
        choice: 选择数据，包含 cost 和 reward
    
    Returns:
        bool: 是否成功应用选择
    """
    cost = choice.get('cost', 0)
    reward = choice.get('reward', 0)
    cost_resource_type = card.get('costResourceType', 'coins')
    
    current_resource = player.get(cost_resource_type, 0)
    if current_resource < cost:
        return False
    
    if cost_resource_type == 'coins':
        player['coins'] -= cost
    elif cost_resource_type == 'seaweed':
        player['seaweed'] -= cost
    
    player['de'] = player.get('de', 0) + reward
    return True