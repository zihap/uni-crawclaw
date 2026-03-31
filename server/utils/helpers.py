# -*- coding: utf-8 -*-
"""
辅助函数工具模块
"""

import random
import string
from typing import Dict


def generate_room_id(existing_rooms: Dict[str, dict]) -> str:
    """生成唯一的6位房间号"""
    while True:
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if room_id not in existing_rooms:
            return room_id


async def send_error(websocket, message: str):
    """发送错误消息给客户端"""
    await websocket.send_json({'event': 'error', 'data': {'message': message}})


# 虾池 key 映射: 外部 key → shrimpPond 内部 key
_SHRIMP = {'common': 'normal', 'third': 'grade3', 'second': 'grade2',
           'first': 'grade1', 'royal': 'royal',
           'grade3': 'grade3', 'grade2': 'grade2', 'grade1': 'grade1'}


def _iter_resources(d: dict):
    """遍历资源字典，yield ('attr', key, amount) 或 ('pond', pond_key, amount)"""
    for k, v in d.items():
        if k == 'lobsters':
            for grade, amount in v.items():
                if amount:
                    yield ('pond', grade, amount)
        elif k in _SHRIMP:
            yield ('pond', _SHRIMP[k], v)
        elif v:
            yield ('attr', k, v)


def has_resources(player: dict, cost: dict) -> bool:
    """查询: 玩家是否有足够资源"""
    for kind, key, need in _iter_resources(cost):
        if kind == 'attr':
            if player.get(key, 0) < need:
                return False
        else:
            if player['shrimpPond'].get(key, 0) < need:
                return False
    return True


async def update_resources(player: dict, deltas: dict, sign: int = 1, broadcast_fn=None):
    """更新: 对玩家资源做增减并广播。sign=1 奖励, sign=-1 扣除。
    broadcast_fn: async def(player_id, client_resources) 广播回调"""
    changed = {}
    for kind, key, amount in _iter_resources(deltas):
        delta = amount * sign
        if kind == 'attr':
            player[key] = player.get(key, 0) + delta
            changed[key] = player[key]
        else:
            player['shrimpPond'][key] = player['shrimpPond'].get(key, 0) + delta
    if changed and broadcast_fn:
        await broadcast_fn(player['id'], changed)


def get_player(game_state: dict, player_id: int) -> dict:
    """根据 player_id 从 game_state 中查找玩家"""
    return next((p for p in game_state['players'] if p['id'] == player_id), None)
