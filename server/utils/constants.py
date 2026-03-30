# -*- coding: utf-8 -*-
"""
游戏常量配置
"""

import os
import json

AREAS = ['fishing', 'market', 'cultivation', 'tribute', 'downtown']

MARKET_PRICES = {
    'buyLobster': 3,
    'sellLobster': 2,
    'buySeaweed': 2,
    'sellSeaweed': 1,
    'buyCage': 4,
    'sellCage': 3,
    'hireHeadman': 6
}

CARD_CONFIG_PATH = './card_config.json'

if os.path.exists(CARD_CONFIG_PATH):
    with open(CARD_CONFIG_PATH, 'r', encoding='utf-8') as f:
        card_config = json.load(f)

        TRIBUTE_TASKS = card_config.get('offerings', [
            {'id': 1, 'requirement': {'grade2': 1}, 'reward': {'virtue': 2, 'reputation': 1}},
            {'id': 2, 'requirement': {'grade1': 1}, 'reward': {'virtue': 1, 'reputation': 3}},
            {'id': 3, 'requirement': {'royal': 1}, 'reward': {'virtue': 4, 'reputation': 4}},
            {'id': 4, 'requirement': {'seaweed': 3, 'gold': 5}, 'reward': {'virtue': 1, 'reputation': 2}},
            {'id': 5, 'requirement': {'cage': 2}, 'reward': {'virtue': 3, 'reputation': 1}},
            {'id': 6, 'requirement': {'titled': 1}, 'reward': {'virtue': 5, 'reputation': 5}}
        ])

        DOWNTOWN_CARDS = card_config.get('markets', [
            {'id': 1, 'type': 'gold', 'effect': 5, 'description': '获得5金币'},
            {'id': 2, 'type': 'seaweed', 'effect': 3, 'description': '获得3海草'},
            {'id': 3, 'type': 'virtue', 'effect': 2, 'description': '获得2德'},
            {'id': 4, 'type': 'reputation', 'effect': 2, 'description': '获得2望'},
            {'id': 5, 'type': 'cage', 'effect': 1, 'description': '获得1虾笼'},
            {'id': 6, 'type': 'signal', 'effect': 3, 'description': '获得3气泡'}
        ])
else:
    TRIBUTE_TASKS = [
        {
            'id': 'offering_001',
            'tavernId': 1,
            'requirement': {'grade1': 1, 'seaweed': 2},
            'reward': {'virtue': 3, 'reputation': 0, 'incomeBonus': 1},
            'aura': {'type': 'permanent', 'effect': 'lobsterFightRewardDouble'}
        },
        {
            'id': 'offering_002',
            'tavernId': 1,
            'requirement': {'grade2': 1, 'gold': 3},
            'reward': {'virtue': 2, 'reputation': 1, 'incomeBonus': 1},
            'aura': {'type': 'final', 'finalScore': 2}
        },
        {
            'id': 'offering_003',
            'tavernId': 2,
            'requirement': {'grade3': 1, 'seaweed': 1},
            'reward': {'virtue': 1, 'reputation': 2, 'incomeBonus': 1},
            'aura': None
        },
        {
            'id': 'offering_004',
            'tavernId': 2,
            'requirement': {'royal': 1},
            'reward': {'virtue': 4, 'reputation': 3, 'incomeBonus': 2},
            'aura': {'type': 'permanent', 'effect': 'tributeRewardPlusOne'}
        },
        {
            'id': 'offering_005',
            'tavernId': 3,
            'requirement': {'grade1': 1, 'grade2': 1, 'gold': 5},
            'reward': {'virtue': 3, 'reputation': 3, 'incomeBonus': 2},
            'aura': {'type': 'final', 'finalScore': 5}
        },
        {
            'id': 'offering_006',
            'tavernId': 3,
            'requirement': {'royal': 1, 'gold': 10},
            'reward': {'virtue': 5, 'reputation': 5, 'incomeBonus': 3},
            'aura': {'type': 'permanent', 'effect': 'allRewardsDouble'}
        },
        {
            'id': 'offering_007',
            'tavernId': 4,
            'requirement': {'royal': 1, 'seaweed': 3},
            'reward': {'virtue': 4, 'reputation': 4, 'incomeBonus': 2},
            'aura': {'type': 'permanent', 'effect': 'startWithExtraHeadman'}
        },
        {
            'id': 'offering_008',
            'tavernId': 4,
            'requirement': {'grade1': 1, 'cage': 1},
            'reward': {'virtue': 3, 'reputation': 2, 'incomeBonus': 1},
            'aura': None
        },
        {
            'id': 'offering_009',
            'tavernId': 5,
            'requirement': {'grade2': 1, 'gold': 8},
            'reward': {'virtue': 2, 'reputation': 3, 'incomeBonus': 1},
            'aura': {'type': 'final', 'finalScore': 3}
        },
        {
            'id': 'offering_010',
            'tavernId': 5,
            'requirement': {'grade3': 1, 'grade2': 1, 'gold': 6, 'seaweed': 2},
            'reward': {'virtue': 4, 'reputation': 1, 'incomeBonus': 2},
            'aura': {'type': 'permanent', 'effect': 'extraMarketAction'}
        },
        {
            'id': 'offering_011',
            'tavernId': 6,
            'requirement': {'royal': 1, 'gold': 12},
            'reward': {'virtue': 5, 'reputation': 2, 'incomeBonus': 2},
            'aura': {'type': 'permanent', 'effect': 'startWithExtraResource'}
        },
        {
            'id': 'offering_012',
            'tavernId': 6,
            'requirement': {'royal': 1, 'grade1': 1, 'gold': 15, 'seaweed': 5},
            'reward': {'virtue': 6, 'reputation': 4, 'incomeBonus': 3},
            'aura': {'type': 'final', 'finalScore': 10}
        }
    ]

    DOWNTOWN_CARDS = [
        {
            'id': 'market_001',
            'type': 'market',
            'name': '府衙',
            'description': '可捐龙虾换取声望',
            'action': {
                'cost': {'shrimp': {'common': 1}},
                'reward': {'reputation': 1}
            },
            'detail': '支付1只龙虾换1望'
        },
        {
            'id': 'market_002',
            'type': 'market',
            'name': '钱庄',
            'description': '可存钱生息',
            'action': {
                'cost': {'gold': 5},
                'reward': {'gold': 6}
            },
            'detail': '存5金币，得6金币'
        },
        {
            'id': 'market_003',
            'type': 'market',
            'name': '渔具店',
            'description': '购买渔具',
            'action': {
                'cost': {'gold': 8},
                'reward': {'cage': 1}
            },
            'detail': '花费8金币购买1个虾笼'
        },
        {
            'id': 'market_004',
            'type': 'market',
            'name': '药材铺',
            'description': '购买增益道具',
            'action': {
                'cost': {'gold': 6},
                'reward': {'seaweed': 2}
            },
            'detail': '花费6金币购买2根海草'
        },
        {
            'id': 'market_005',
            'type': 'market',
            'name': '茶馆',
            'description': '打听消息',
            'action': {
                'cost': {'gold': 3},
                'reward': {'virtue': 1}
            },
            'detail': '花费3金币获得1德'
        },
        {
            'id': 'market_006',
            'type': 'market',
            'name': '赌坊',
            'description': '小赌怡情',
            'action': {
                'cost': {'gold': 4},
                'reward': {'gold': 0}
            },
            'detail': '花费4金币，有机会获得更多金币'
        }
    ]

FISHING_BAG_ITEMS = [
    {'type': 'bubble', 'weight': 30},
    {'type': 'lobster', 'weight': 25},
    {'type': 'seaweed', 'weight': 25},
    {'type': 'either', 'weight': 20}
]
