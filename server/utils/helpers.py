# -*- coding: utf-8 -*-
"""
辅助函数工具模块
"""

import random
import string
from typing import Dict
from utils.constants import LOBSTER_GRADES
from utils.events import ServerEvents


def generate_room_id(existing_rooms: Dict[str, dict]) -> str:
    """生成唯一的6位房间号"""
    while True:
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if room_id not in existing_rooms:
            return room_id


async def send_error(websocket, message: str):
    """发送错误消息给客户端"""
    await websocket.send_json({'event': ServerEvents.ERROR, 'data': {'message': message}})


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


def _update_lobster_grade(player: dict, grade: str, delta: int):
    """添加或移除指定等级的龙虾"""
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


def _build_resource_snapshot(player: dict) -> dict:
    """构建玩家完整资源快照"""
    return {
        'coins': player.get('coins', 0),
        'seaweed': player.get('seaweed', 0),
        'cages': player.get('cages', 0),
        'de': player.get('de', 0),
        'wang': player.get('wang', 0),
        'liZhang': player.get('liZhang', 0),
        'bubbles': player.get('bubbles', 0),
        'bonusGold': player.get('bonusGold', 0),
        'lobsters': player.get('lobsters', []),
        'titleCards': player.get('titleCards', []),
    }


def has_resources(player: dict, cost: dict) -> bool:
    """查询: 玩家是否有足够资源"""
    lobster_counts = _count_lobsters_by_grade(player)
    for k, v in cost.items():
        if k in LOBSTER_GRADES:
            if lobster_counts.get(k, 0) < v:
                return False
        elif k == 'lobsters':
            for grade, amount in v.items():
                if lobster_counts.get(grade, 0) < amount:
                    return False
        else:
            if player.get(k, 0) < v:
                return False
    return True


async def update_resources(player: dict, deltas: dict, broadcast_fn=None):
    """更新玩家资源。delta 正数增加，负数减少。
    广播完整资源快照，客户端直接替换。"""
    for k, v in deltas.items():
        if k in LOBSTER_GRADES:
            _update_lobster_grade(player, k, v)
        elif k == 'lobsters':
            for grade, amount in v.items():
                _update_lobster_grade(player, grade, amount)
        else:
            player[k] = player.get(k, 0) + v

    if broadcast_fn:
        await broadcast_fn(player['id'], _build_resource_snapshot(player))


def get_player(game_state: dict, player_id: int) -> dict:
    """根据 player_id 从 game_state 中查找玩家"""
    return next((p for p in game_state['players'] if p['id'] == player_id), None)
