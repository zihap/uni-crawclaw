# -*- coding: utf-8 -*-
"""
游戏常量配置
"""

import os
import json

AREAS = ['shrimp_catching', 'seafood_market', 'breeding', 'tribute', 'marketplace']

# 灵螯等级集合（用于资源检查与更新）
LOBSTER_GRADES = {'normal', 'grade3', 'grade2', 'grade1', 'royal'}

# 灵螯等级价值（用于上供区计算）
GRADE_VALUES = {'normal': 0, 'grade3': 1, 'grade2': 2, 'grade1': 3, 'royal': 4}

# 灵螯升级（普通升级 + 吃草跳级）
GRADE_UPGRADE = {'normal': 'grade3', 'grade3': 'grade2', 'grade2': 'grade1', 'grade1': 'royal', 'royal': 'royal'}
GRADE_UPGRADE_SEAWEED = {'normal': 'grade2', 'grade3': 'grade1', 'grade2': 'royal', 'grade1': 'royal', 'royal': 'royal'}

# 上供区挑战槽状态
CHALLENGE_SLOT_DONE = 'Done'

# 上供区挑战槽到防守方槽位的映射
CHALLENGE_TO_DEFENDER_SLOT_MAP = {3: 0, 4: 1, 5: 2}

MARKET_PRICES = {
    'buyLobster': 3,
    'sellLobster': 2,
    'buySeaweed': 2,
    'sellSeaweed': 1,
    'buyCage': 4,
    'sellCage': 3,
    'hireHeadman': 6
}

# 静态行动格模板: 定义每个区域每个格的 actionCount 和 reward
# 这些数据从不改变，不需要存储在可变游戏状态中
SLOT_TEMPLATES = {
    'shrimp_catching': [
        {'actionCount': 1, 'reward': {'cages': 1, 'stealStart': True}},
        {'actionCount': 2, 'reward': {'cages': 1}},
        {'actionCount': 3, 'reward': {'coins': 1}},
        {'actionCount': 4, 'reward': {}}
    ],
    'seafood_market': [
        {'actionCount': 2, 'reward': {'coins': 1}},
        {'actionCount': 3, 'reward': {}},
        {'actionCount': 3, 'reward': {'coins': 1}},
        {'actionCount': 3, 'reward': {'coins': 2}}
    ],
    'breeding': [
        {'actionCount': 1, 'reward': {'seaweed': 1}},
        {'actionCount': 2, 'reward': {}},
        {'actionCount': 2, 'reward': {'coins': 1}},
        {'actionCount': 3, 'reward': {}}
    ],
    'tribute': [
        {'actionCount': 1},
        {'actionCount': 1},
        {'actionCount': 1},
        {'actionCount': 1},
        {'actionCount': 1},
        {'actionCount': 1}
    ],
    'marketplace': [None, None, None]
}

# 每个区域的行动格数量
AREA_SLOT_COUNTS = {
    'shrimp_catching': 4,
    'seafood_market': 4,
    'breeding': 4,
    'tribute': 6,
    'marketplace': 3
}

CARD_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'card_config.json')

_CARD_CONFIG_DEFAULT = {
    'tributeCards': [
        {
            'id': 'tribute_1',
            'name': '王爷',
            'requirements': {'lobsters': {'grade1': 1}, 'seaweed': 2},
            'reward': {'de': 3},
            'aura': {'type': 'doubleWinReward', 'description': '灵螯斗场获胜奖励翻倍'},
            'bonusScore': 0
        },
        {
            'id': 'tribute_2',
            'name': '知府',
            'requirements': {'lobsters': {'grade3': 2}, 'coins': 5},
            'reward': {'wang': 2},
            'aura': {'type': 'bonusGold', 'value': 1, 'description': '每回合额外获得1贝币'},
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
            'aura': {'type': 'extraCage', 'value': 1, 'description': '游戏开始时额外获得1个灵鼎'},
            'bonusScore': 2
        }
    ],
    'marketplaceCards': [
        {
            "id": "marketplace_1",
            "name": "府衙",
            "action": {
                "type": "exchange",
                "options": [
                    {"cost": {"lobsters": 1}, "reward": {"wang": 1}},
                    {"cost": {"lobsters": 3}, "reward": {"wang": 2}}
                ]
            },
            "description": "玩家支付1只灵螯换1运，或者支付3只灵螯换2运",
            "auto": False
        },
        {
            "id": "marketplace_2",
            "name": "县衙",
            "action": {
                "type": "exchange",
                "options": [
                    {"cost": {"coins": 2}, "reward": {"de": 1}},
                    {"cost": {"coins": 5}, "reward": {"de": 2}}
                ]
            },
            "description": "玩家支付2贝币换1道，或者支付5贝币换2道",
            "auto": False
        },
        {
            "id": "marketplace_3",
            "name": "驿站",
            "action": {"type": "post_station"},
            "description": "本回合游戏中每完成一张进贡卡，都可以直接额外获得1道或者1运",
            "auto": True
        },
        {
            "id": "marketplace_4",
            "name": "斗场",
            "action": {"type": "breeding_4"},
            "description": "直接进行4次培养灵螯升级",
            "auto": True
        },
        {
            "id": "marketplace_5",
            "name": "黑市",
            "action": {"type": "black_market"},
            "description": "直接获得一只2品灵螯",
            "auto": True
        },
        {
            "id": "marketplace_6",
            "name": "学堂",
            "action": {"type": "academy"},
            "description": "你的道运轨最低者提升一格（如果道运值一样，则自己选择+1道或者+1运）",
            "auto": True
        },
        {
            "id": "marketplace_7",
            "name": "善堂",
            "action": {"type": "charity"},
            "description": "道轨最低的玩家直接获得2只普通灵螯，运轨最低的玩家直接获得2个贝币",
            "auto": True
        },
        {
            "id": "marketplace_8",
            "name": "市集",
            "action": {"type": "bazaar"},
            "description": "直接获取1根仙草+1个贝币+1只普通灵螯+1个灵鼎",
            "auto": True
        },
        {
            "id": "marketplace_9",
            "name": "客栈",
            "action": {"type": "inn"},
            "description": "本卡上会有一个专属寻山客，获得后在下一回合增加1个放置名额",
            "auto": True
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
    {'type': 'lobster', 'weight': 40},
    {'type': 'seaweed', 'weight': 40},
    {'type': 'either', 'weight': 20}
]