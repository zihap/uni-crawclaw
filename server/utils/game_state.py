# -*- coding: utf-8 -*-
"""
游戏状态和玩家创建模块
"""

import time
import random
import string
import json
import os
from typing import Dict
from .constants import AREAS, MARKET_PRICES, TRIBUTE_TASKS, DOWNTOWN_CARDS, SLOT_TEMPLATES, AREA_SLOT_COUNTS

_CARD_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'card_config.json')
with open(_CARD_CONFIG_PATH, 'r', encoding='utf-8') as _f:
    _ALL_TITLE_CARDS = json.load(_f).get('titleCards', [])


def generate_user_id() -> str:
    """生成唯一的用户ID"""
    return 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))


def create_game_state() -> dict:
    """创建初始游戏状态对象"""
    return {
        'gameId': None,
        'currentPlayerIndex': 0,
        'currentRound': 1,
        'maxRounds': 5,
        'phase': 'waiting',
        'players': [],
        'startingPlayerIndex': 0,

        'areas': {
            'shrimp_catching': {
                'slots': [None] * AREA_SLOT_COUNTS['shrimp_catching'],
                'wildLobsterPool': 0
            },
            'seafood_market': {
                'slots': [None] * AREA_SLOT_COUNTS['seafood_market'],
                'marketLobsterCount': 0,
                'dynamicPrices': MARKET_PRICES.copy()
            },
            'breeding': {
                'slots': [None] * AREA_SLOT_COUNTS['breeding']
            },
            'tribute': {
                'slots': [None] * AREA_SLOT_COUNTS['tribute'],
                'challengeSlots': [None] * 3
            },
            'marketplace': {
                'slots': [None] * AREA_SLOT_COUNTS['marketplace']
            }
        },

        'tributeTasks': [],
        'downtownCards': [],
        'status': 'waiting'
    }


def create_player(player_id: int, name: str, is_host: bool = False, user_id: str = None, position: int = 0) -> dict:
    """创建玩家对象"""
    position_resources = {
        0: {'liZhang': 3, 'lobsters': 2, 'coins': 5, 'seaweed': 1, 'cages': 1},
        1: {'liZhang': 3, 'lobsters': 2, 'coins': 6, 'seaweed': 1, 'cages': 1},
        2: {'liZhang': 3, 'lobsters': 2, 'coins': 5, 'seaweed': 2, 'cages': 1},
        3: {'liZhang': 3, 'lobsters': 2, 'coins': 6, 'seaweed': 2, 'cages': 1}
    }

    resources = position_resources.get(position, position_resources[0])

    lobsters = []
    for _ in range(resources['lobsters']):
        lobsters.append({
            'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
            'grade': 'normal',
            'title': None
        })

    return {
        'id': player_id,
        'name': name,
        'userId': user_id or generate_user_id(),
        'isOnline': True,
        'lastSeen': int(time.time()),

        'coins': resources['coins'],
        'seaweed': resources['seaweed'],
        'cages': resources['cages'],
        'de': 0,
        'wang': 0,
        'bonusPoints': 0,
        'liZhang': resources['liZhang'],
        'bubbles': 0,
        'lobsters': lobsters,

        'completedTasks': [],
        'completedTaverns': [],
        'royalCountThisRound': 0,
        'bonusGold': 0,

        'permaBuffs': [],

        'titleCards': _ALL_TITLE_CARDS.copy(),

        'ready': False,
        'isHost': is_host,
        'isStartingPlayer': position == 0,

        'tempBubbles': 0,
        'hiredLaborersBonus': []
    }


def draw_tribute_tasks(game_state: dict):
    """抽取上供卡到游戏状态"""
    shuffled = TRIBUTE_TASKS.copy()
    random.shuffle(shuffled)
    game_state['tributeTasks'] = shuffled[:3]


def draw_downtown_cards(game_state: dict):
    """抽取闹市卡到游戏状态"""
    shuffled = DOWNTOWN_CARDS.copy()
    random.shuffle(shuffled)
    game_state['downtownCards'] = shuffled[:3]


# 竞技场投注状态: { "roomId_battleId": { challengerId, defenderId, challengerLobster, defenderLobster, spectators, bets, started, completed } }
arena_betting_state = {}
