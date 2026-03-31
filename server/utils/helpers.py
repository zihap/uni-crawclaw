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


def _count_lobsters_by_grade(player: dict) -> dict:
    """统计玩家各等级龙虾数量"""
    counts = {}
    for lobster in player.get('lobsters', []):
        grade = lobster.get('grade', 'normal')
        counts[grade] = counts.get(grade, 0) + 1
    return counts


def _find_lobster_by_grade(player: dict, grade: str) -> dict:
    """找到一只指定等级的龙虾"""
    for lobster in player.get('lobsters', []):
        if lobster.get('grade') == grade:
            return lobster
    return None


def has_resources(player: dict, cost: dict) -> bool:
    """查询: 玩家是否有足够资源"""
    lobster_counts = _count_lobsters_by_grade(player)
    for k, v in cost.items():
        if k == 'lobsters':
            for grade, amount in v.items():
                if lobster_counts.get(grade, 0) < amount:
                    return False
        elif k == 'normal':
            if lobster_counts.get('normal', 0) < v:
                return False
        elif k == 'grade3':
            if lobster_counts.get('grade3', 0) < v:
                return False
        elif k == 'grade2':
            if lobster_counts.get('grade2', 0) < v:
                return False
        elif k == 'grade1':
            if lobster_counts.get('grade1', 0) < v:
                return False
        elif k == 'royal':
            if lobster_counts.get('royal', 0) < v:
                return False
        else:
            if player.get(k, 0) < v:
                return False
    return True


async def update_resources(player: dict, deltas: dict, sign: int = 1, broadcast_fn=None):
    """更新: 对玩家资源做增减并广播。sign=1 奖励, sign=-1 扣除。
    broadcast_fn: async def(player_id, client_resources) 广播回调"""
    changed = {}
    for k, v in deltas.items():
        if k == 'lobsters':
            for grade, amount in v.items():
                delta = amount * sign
                if delta > 0:
                    for _ in range(delta):
                        player['lobsters'].append({
                            'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
                            'grade': grade,
                            'title': None
                        })
                elif delta < 0:
                    for _ in range(abs(delta)):
                        lobster = _find_lobster_by_grade(player, grade)
                        if lobster:
                            player['lobsters'].remove(lobster)
        elif k == 'normal':
            delta = v * sign
            if delta > 0:
                for _ in range(delta):
                    player['lobsters'].append({
                        'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
                        'grade': 'normal',
                        'title': None
                    })
            elif delta < 0:
                for _ in range(abs(delta)):
                    lobster = _find_lobster_by_grade(player, 'normal')
                    if lobster:
                        player['lobsters'].remove(lobster)
        elif k == 'grade3':
            delta = v * sign
            if delta > 0:
                for _ in range(delta):
                    player['lobsters'].append({
                        'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
                        'grade': 'grade3',
                        'title': None
                    })
            elif delta < 0:
                for _ in range(abs(delta)):
                    lobster = _find_lobster_by_grade(player, 'grade3')
                    if lobster:
                        player['lobsters'].remove(lobster)
        elif k == 'grade2':
            delta = v * sign
            if delta > 0:
                for _ in range(delta):
                    player['lobsters'].append({
                        'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
                        'grade': 'grade2',
                        'title': None
                    })
            elif delta < 0:
                for _ in range(abs(delta)):
                    lobster = _find_lobster_by_grade(player, 'grade2')
                    if lobster:
                        player['lobsters'].remove(lobster)
        elif k == 'grade1':
            delta = v * sign
            if delta > 0:
                for _ in range(delta):
                    player['lobsters'].append({
                        'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
                        'grade': 'grade1',
                        'title': None
                    })
            elif delta < 0:
                for _ in range(abs(delta)):
                    lobster = _find_lobster_by_grade(player, 'grade1')
                    if lobster:
                        player['lobsters'].remove(lobster)
        elif k == 'royal':
            delta = v * sign
            if delta > 0:
                for _ in range(delta):
                    player['lobsters'].append({
                        'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
                        'grade': 'royal',
                        'title': None
                    })
            elif delta < 0:
                for _ in range(abs(delta)):
                    lobster = _find_lobster_by_grade(player, 'royal')
                    if lobster:
                        player['lobsters'].remove(lobster)
        else:
            player[k] = player.get(k, 0) + v * sign
            changed[k] = player[k]
    if changed and broadcast_fn:
        await broadcast_fn(player['id'], changed)


def get_player(game_state: dict, player_id: int) -> dict:
    """根据 player_id 从 game_state 中查找玩家"""
    return next((p for p in game_state['players'] if p['id'] == player_id), None)
