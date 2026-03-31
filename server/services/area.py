# -*- coding: utf-8 -*-
"""
区域结算服务模块
"""

import random
from utils.constants import FISHING_BAG_ITEMS, SLOT_TEMPLATES


def _create_lobster(grade='normal'):
    """创建一只龙虾对象"""
    import random
    import string
    return {
        'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
        'grade': grade,
        'title': None
    }


def draw_from_bag() -> str:
    """从捕虾盲袋中抽取一个指示物"""
    total_weight = sum(item['weight'] for item in FISHING_BAG_ITEMS)
    rand = random.random() * total_weight

    for item in FISHING_BAG_ITEMS:
        rand -= item['weight']
        if rand <= 0:
            return item['type']

    return FISHING_BAG_ITEMS[0]['type']


def resolve_fishing_area(game_state: dict):
    """结算捕虾区"""
    area_data = game_state['areas']['shrimp_catching']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['shrimp_catching']

    for slot_idx, player_id in enumerate(slots):
        if player_id is None:
            continue

        player = game_state['players'][player_id]
        template = templates[slot_idx]
        action_count = template['actionCount']
        reward = template['reward']
        reward_given = False

        for _ in range(action_count):
            item = draw_from_bag()

            if item == 'bubble':
                player['tempBubbles'] += 1
            elif item == 'lobster':
                player['lobsters'].append(_create_lobster('normal'))
            elif item == 'seaweed':
                player['seaweed'] += 3
            elif item == 'either':
                player['tempBubbles'] += 1
                player['lobsters'].append(_create_lobster('normal'))

            if not reward_given:
                if reward.get('cages'):
                    player['cages'] += reward['cages']
                if reward.get('gold'):
                    player['gold'] += reward['gold']
                if reward.get('stealStart'):
                    old_starting_idx = game_state['startingPlayerIndex']
                    game_state['startingPlayerIndex'] = player_id

                    for p in game_state['players']:
                        p['isStartingPlayer'] = False
                    player['isStartingPlayer'] = True

                    print(f"DEBUG: Starting player stolen by player {player_id} (was {old_starting_idx})")

                reward_given = True


def resolve_market_area(game_state: dict):
    """结算海鲜市场"""
    area_data = game_state['areas']['seafood_market']
    slots = area_data['slots']
    templates = SLOT_TEMPLATES['seafood_market']

    for slot_idx, player_id in enumerate(slots):
        if player_id is None:
            continue

        player = game_state['players'][player_id]
        template = templates[slot_idx]
        reward = template['reward']

        if reward.get('coins'):
            player['coins'] += reward['coins']


def resolve_breeding_area(game_state: dict):
    """结算养殖区"""
    # TODO: 养殖区结算逻辑待定
    pass


def resolve_tribute_area(game_state: dict):
    """结算上供区：检查挑战位与防守位配对，生成战斗候选列表"""
    area_data = game_state['areas']['tribute']
    slots = area_data['slots']

    if 'battleQueue' not in game_state:
        game_state['battleQueue'] = []

    for challenge_idx in range(3, 6):
        defender_idx = challenge_idx - 3
        challenger_id = slots[challenge_idx]
        defender_id = slots[defender_idx]

        if challenger_id is not None and defender_id is not None:
            game_state['battleQueue'].append({
                'challengerId': challenger_id,
                'defenderId': defender_id,
                'challengeSlot': challenge_idx,
                'defenderSlot': defender_idx
            })
            print(f"[tribute] Battle queued: player {challenger_id} (slot {challenge_idx}) vs player {defender_id} (slot {defender_idx})")

    # 普通位(6-7)和未被挑战的防守位(0-2)的结算由玩家主动提交上供任务处理


def resolve_marketplace_area(game_state: dict):
    """结算闹市区"""
    # TODO: 闹市区结算逻辑待定
    pass


def resolve_area(game_state: dict, area_index: int, areas_list: list):
    """根据区域索引结算对应区域"""
    from utils.constants import AREAS

    area_name = AREAS[area_index]
    area_data = game_state['areas'].get(area_name)
    if not area_data:
        return

    if area_name == 'shrimp_catching':
        resolve_fishing_area(game_state)
    elif area_name == 'seafood_market':
        resolve_market_area(game_state)
    elif area_name == 'breeding':
        resolve_breeding_area(game_state)
    elif area_name == 'tribute':
        resolve_tribute_area(game_state)
    elif area_name == 'marketplace':
        resolve_marketplace_area(game_state)
