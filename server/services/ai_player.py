# -*- coding: utf-8 -*-
"""
AI玩家创建与管理模块
"""

import random
from utils.game_state import create_player

AI_NAME_PREFIXES = ['聪明的', '机智的', '冷静的', '果断的', '谨慎的', '狡猾的', '勇猛的', '沉稳的']
AI_NAME_SUFFIXES = ['灵螯', '渔夫', '船长', '商人', '寻山客', '水手', '舵手', '渔翁']


def generate_ai_name() -> str:
    """生成随机AI名称"""
    prefix = random.choice(AI_NAME_PREFIXES)
    suffix = random.choice(AI_NAME_SUFFIXES)
    return f"{prefix}{suffix}"


def create_ai_personality() -> dict:
    """生成随机AI个性特征，每个特征0-1"""
    return {
        'aggressiveness': round(random.uniform(0.2, 0.9), 2),
        'greed': round(random.uniform(0.3, 0.9), 2),
        'caution': round(random.uniform(0.2, 0.8), 2),
        'patience': round(random.uniform(0.3, 0.8), 2),
        'randomness': round(random.uniform(0.1, 0.5), 2),
    }


def create_ai_player(player_id: int, position: int = 0) -> dict:
    """创建AI玩家，基于create_player扩展AI字段"""
    name = generate_ai_name()
    player = create_player(player_id, name, is_host=False, user_id=f'ai_{player_id}', position=position)
    player['isAI'] = True
    player['ready'] = True
    player['isOnline'] = True
    player['aiName'] = f"[AI]{name}"
    player['aiState'] = 'idle'
    player['aiThinkTime'] = random.uniform(1.0, 3.0)
    player['aiPersonality'] = create_ai_personality()
    return player
