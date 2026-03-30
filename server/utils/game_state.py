# -*- coding: utf-8 -*-
"""
游戏状态和玩家创建模块
"""

import time
import random
import string
from typing import Dict
from .constants import AREAS, MARKET_PRICES, TRIBUTE_TASKS, DOWNTOWN_CARDS


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
            'fishing': {
                'slots': [
                    {'occupiedBy': None, 'actionCount': 1, 'reward': {'cages': 1, 'stealStart': True}},
                    {'occupiedBy': None, 'actionCount': 2, 'reward': {'cages': 1}},
                    {'occupiedBy': None, 'actionCount': 3, 'reward': {'gold': 1}},
                    {'occupiedBy': None, 'actionCount': 4, 'reward': {}}
                ],
                'wildLobsterPool': 0
            },

            'market': {
                'slots': [
                    {'occupiedBy': None, 'actionCount': 2, 'reward': {'gold': 1}},
                    {'occupiedBy': None, 'actionCount': 3, 'reward': {}},
                    {'occupiedBy': None, 'actionCount': 3, 'reward': {'gold': 1}},
                    {'occupiedBy': None, 'actionCount': 3, 'reward': {'gold': 2}}
                ],
                'marketLobsterCount': 0,

                'hiredPositions': [
                    {'id': 1, 'unlockedRound': 2, 'reward': {'seaweed': 1}, 'hired': False},
                    {'id': 2, 'unlockedRound': 2, 'reward': {'seaweed': 1}, 'hired': False},
                    {'id': 3, 'unlockedRound': 3, 'reward': {'lobster': 1}, 'hired': False},
                    {'id': 4, 'unlockedRound': 3, 'reward': {'lobster': 1}, 'hired': False},
                    {'id': 5, 'unlockedRound': 3, 'reward': {'grade3': 1}, 'hired': False},
                    {'id': 6, 'unlockedRound': 4, 'reward': {'grade3': 1}, 'hired': False},
                    {'id': 7, 'unlockedRound': 4, 'reward': {'grade2': 1}, 'hired': False},
                    {'id': 8, 'unlockedRound': 4, 'reward': {'grade2': 1}, 'hired': False}
                ],

                'basePrices': MARKET_PRICES.copy(),
                'dynamicPrices': MARKET_PRICES.copy()
            },

            'cultivation': {
                'slots': [None, None, None, None]
            },

            'tribute': {
                'slots': [None, None, None],
                'challengeSlots': [None, None, None]
            },

            'downtown': {
                'slots': [None, None, None]
            }
        },

        'tributeTasks': [],
        'downtownCards': [],
        'status': 'waiting'
    }


def create_player(player_id: int, name: str, is_host: bool = False, user_id: str = None, position: int = 0) -> dict:
    """创建玩家对象"""
    position_resources = {
        0: {'headmen': 3, 'normal': 2, 'gold': 5, 'seaweed': 1, 'cages': 1},
        1: {'headmen': 3, 'normal': 2, 'gold': 6, 'seaweed': 1, 'cages': 1},
        2: {'headmen': 3, 'normal': 2, 'gold': 5, 'seaweed': 2, 'cages': 1},
        3: {'headmen': 3, 'normal': 2, 'gold': 6, 'seaweed': 2, 'cages': 1}
    }

    resources = position_resources.get(position, position_resources[0])

    return {
        'id': player_id,
        'name': name,
        'userId': user_id or generate_user_id(),
        'isOnline': True,
        'lastSeen': int(time.time()),

        'gold': resources['gold'],
        'seaweed': resources['seaweed'],
        'cages': resources['cages'],
        'virtue': 0,
        'reputation': 0,
        'bonusPoints': 0,
        'headmen': resources['headmen'],
        'signals': 0,

        'shrimpPond': {
            'normal': resources['normal'],
            'grade3': 0,
            'grade2': 0,
            'grade1': 0,
            'royal': 0,
            'titled': []
        },

        'completedTasks': [],
        'completedTaverns': [],
        'royalCountThisRound': 0,
        'incomePerRound': 0,

        'permaBuffs': [],

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
