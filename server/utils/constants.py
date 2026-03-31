# -*- coding: utf-8 -*-
"""
游戏常量配置
"""

import os
import json

AREAS = ['fishing', 'market', 'cultivation', 'tribute', 'downtown']

# 龙虾升级: 新grade → 旧grade (用于 battleEnd 时反推消耗)
GRADE_UPGRADE = {'grade2': 'grade3', 'grade1': 'grade2', 'royal': 'grade1'}

MARKET_PRICES = {
    'buyLobster': 3,
    'sellLobster': 2,
    'buySeaweed': 2,
    'sellSeaweed': 1,
    'buyCage': 4,
    'sellCage': 3,
    'hireHeadman': 6
}

CARD_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'card_config.json')

_CARD_CONFIG_DEFAULT = {
    'tributeCards': [
        {
            'id': 'tribute_1',
            'name': '王爷',
            'requirements': {'lobsters': {'grade1': 1}, 'seaweed': 2},
            'reward': {'de': 3},
            'aura': {'type': 'doubleWinReward', 'description': '龙虾斗场获胜奖励翻倍'},
            'bonusScore': 0
        },
        {
            'id': 'tribute_2',
            'name': '知府',
            'requirements': {'lobsters': {'grade3': 2}, 'coins': 5},
            'reward': {'wang': 2},
            'aura': {'type': 'bonusGold', 'value': 1, 'description': '每回合额外获得1金币'},
            'bonusScore': 2
        },
        {
            'id': 'tribute_3',
            'name': '县令',
            'requirements': {'lobsters': {'grade3': 1}, 'seaweed': 3},
            'reward': {'de': 2},
            'aura': None,
            'bonusScore': 3
        },
        {
            'id': 'tribute_4',
            'name': '乡绅',
            'requirements': {'coins': 10},
            'reward': {'wang': 3},
            'aura': None,
            'bonusScore': 1
        },
        {
            'id': 'tribute_5',
            'name': '举人',
            'requirements': {'lobsters': {'grade3': 3}},
            'reward': {'de': 1},
            'aura': {'type': 'extraCage', 'value': 1, 'description': '游戏开始时额外获得1个虾笼'},
            'bonusScore': 2
        }
    ],
    'marketplaceCards': [
        {
            'id': 'marketplace_1',
            'name': '府衙',
            'action': {
                'type': 'exchange',
                'options': [
                    {'cost': {'lobsters': 1}, 'reward': {'wang': 1}},
                    {'cost': {'lobsters': 3}, 'reward': {'wang': 2}}
                ]
            },
            'description': '玩家支付1只龙虾换1望，或者3只龙虾换2望'
        },
        {
            'id': 'marketplace_2',
            'name': '书院',
            'action': {
                'type': 'exchange',
                'options': [
                    {'cost': {'seaweed': 2}, 'reward': {'de': 1}},
                    {'cost': {'coins': 5}, 'reward': {'de': 2}}
                ]
            },
            'description': '支付2根海草换1德，或5金币换2德'
        },
        {
            'id': 'marketplace_3',
            'name': '码头',
            'action': {
                'type': 'exchange',
                'options': [
                    {'cost': {'coins': 3}, 'reward': {'lobsters': 2}},
                    {'cost': {'cages': 1}, 'reward': {'seaweed': 3}}
                ]
            },
            'description': '3金币换2只龙虾，或1个虾笼换3根海草'
        },
        {
            'id': 'marketplace_4',
            'name': '钱庄',
            'action': {
                'type': 'exchange',
                'options': [
                    {'cost': {'lobsters': 1}, 'reward': {'coins': 2}},
                    {'cost': {'de': 1}, 'reward': {'coins': 5}}
                ]
            },
            'description': '1只龙虾换2金币，或1德换5金币'
        }
    ]
}

try:
    if os.path.exists(CARD_CONFIG_PATH):
        with open(CARD_CONFIG_PATH, 'r', encoding='utf-8') as f:
            card_config = json.load(f)
    else:
        card_config = {}
except json.JSONDecodeError:
    card_config = {}

TRIBUTE_TASKS = card_config.get('tributeCards', _CARD_CONFIG_DEFAULT['tributeCards'])
DOWNTOWN_CARDS = card_config.get('marketplaceCards', _CARD_CONFIG_DEFAULT['marketplaceCards'])

FISHING_BAG_ITEMS = [
    {'type': 'bubble', 'weight': 30},
    {'type': 'lobster', 'weight': 25},
    {'type': 'seaweed', 'weight': 25},
    {'type': 'either', 'weight': 20}
]
