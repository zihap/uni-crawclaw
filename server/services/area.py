# -*- coding: utf-8 -*-
"""
区域结算服务模块
"""

import random
from utils.constants import FISHING_BAG_ITEMS


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
    fishing_area = game_state['areas']['fishing']
    slots = fishing_area['slots']

    sorted_slots = [(i, slot) for i, slot in enumerate(slots) if slot.get('occupiedBy') is not None]
    sorted_slots.sort(key=lambda x: x[0])

    for slot_idx, slot in sorted_slots:
        player_id = slot['occupiedBy']
        player = game_state['players'][player_id]
        action_count = slot['actionCount']
        reward = slot['reward']
        reward_given = False

        for _ in range(action_count):
            item = draw_from_bag()

            if item == 'bubble':
                player['tempBubbles'] += 1
            elif item == 'lobster':
                player['shrimpPond']['normal'] += 1
            elif item == 'seaweed':
                player['seaweed'] += 3
            elif item == 'either':
                player['tempBubbles'] += 1
                player['shrimpPond']['normal'] += 1

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
    market_area = game_state['areas']['market']
    slots = market_area['slots']

    sorted_slots = [(i, slot) for i, slot in enumerate(slots) if slot.get('occupiedBy') is not None]
    sorted_slots.sort(key=lambda x: x[0])

    for slot_idx, slot in sorted_slots:
        player_id = slot['occupiedBy']
        player = game_state['players'][player_id]
        action_count = slot['actionCount']
        reward = slot['reward']
        reward_given = False

        if not reward_given:
            if reward.get('gold'):
                player['gold'] += reward['gold']
            reward_given = True


def resolve_area(game_state: dict, area_index: int, areas_list: list):
    """根据区域索引结算对应区域"""
    from utils.constants import AREAS
    
    area_name = AREAS[area_index]
    area_data = game_state['areas'].get(area_name)
    if not area_data:
        return

    if area_name == 'fishing':
        resolve_fishing_area(game_state)
    elif area_name == 'market':
        resolve_market_area(game_state)
