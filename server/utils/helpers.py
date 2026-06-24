# -*- coding: utf-8 -*-
"""
辅助函数工具模块
"""

import random
import string
from typing import Dict, Callable, Awaitable, Optional
from utils.constants import LOBSTER_GRADES
from utils.events import ServerEvents


def make_action_message(action_type: str, data: dict = None, **kwargs) -> dict:
    """构造统一的消息体"""
    if data is not None:
        return {'actionType': action_type, **data}
    return {'actionType': action_type, **kwargs}


def is_ai_player(player: dict) -> bool:
    """检查是否为AI玩家（包括AI接管的人类玩家）"""
    return player.get('isAI', False) or player.get('isAITakeover', False)


def create_lobster(grade: str = 'normal') -> dict:
    """创建一只龙虾对象"""
    return {
        'id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
        'grade': grade
    }


def make_broadcast_fn(broadcast_fn, room_id: str) -> Callable:
    """创建资源广播闭包"""
    async def bf(player_id: int, resources: dict):
        await broadcast_fn(room_id, ServerEvents.PLAYER_RESOURCE_UPDATE, {
            'playerId': player_id, 'resources': resources
        })
    return bf


def make_delta_broadcast_fn(broadcast_fn, room_id: str) -> Callable:
    """创建资源变化量广播闭包"""
    async def bf(player_id: int, deltas: dict):
        await broadcast_fn(room_id, ServerEvents.PLAYER_RESOURCE_DELTA, {
            'playerId': player_id, 'deltas': deltas
        })
    return bf


def make_resource_broadcast_fns(broadcast_fn, room_id: str) -> tuple:
    """创建资源快照和变化量广播闭包 (bf, dbf)"""
    return (
        make_broadcast_fn(broadcast_fn, room_id),
        make_delta_broadcast_fn(broadcast_fn, room_id)
    )


def calculate_market_prices(lobster_count: int) -> dict:
    """根据市场龙虾数量计算动态价格"""

    # 市场流通龙虾数大于5只并且小于等于8只 (即 6, 7, 8)
    if lobster_count > 5:
        return {
            'buyLobster': 1, 'sellLobster': 1,
            'buyCage': 4, 'sellCage': 4,
            'buySeaweed': 1, 'sellSeaweed': 1,
            'buySeaweed3': 4, 'sellSeaweed3': 4
        }
    # 市场流通龙虾数大于3只并且小于等于5只 (即 4, 5)
    elif lobster_count > 3:
        return {
            'buyLobster': 2, 'sellLobster': 2,
            'buyCage': 3, 'sellCage': 3,
            'buySeaweed': 1, 'sellSeaweed': 1,
            'buySeaweed3': 4, 'sellSeaweed3': 4
        }
    # 市场流通龙虾数小于等于3只 (即 0, 1, 2, 3)
    else:
        return {
            'buyLobster': 3, 'sellLobster': 3,
            'buyCage': 2, 'sellCage': 2,
            'buySeaweed': 1, 'sellSeaweed': 1,
            'buySeaweed3': 4, 'sellSeaweed3': 4
        }


def handle_skip_action(settlement_state: dict, current_slot_index: Optional[int] = None) -> None:
    """处理 skip 动作，更新 settlement_state 以跳到下一个 slot"""
    settlement_state['waitingForPlayer'] = None
    idx = current_slot_index if current_slot_index is not None else settlement_state.get('currentSlotIndex', 0)
    settlement_state['currentSlotIndex'] = idx + 1


def make_settlement_state(area_type: str, current_slot_index: int = 0, remaining_actions: int = 0, waiting_for_player: Optional[int] = None, **extra) -> dict:
    """构造结算状态字典"""
    state = {
        'currentSlotIndex': current_slot_index,
        'remainingActions': remaining_actions,
        'waitingForPlayer': waiting_for_player,
        'areaType': area_type,
    }
    state.update(extra)
    return state


def make_action_router(handlers: dict, action_key: str = 'actionType', error_prefix: str = '未知的行动', extract_payload: bool = False):
    """创建通用的行动路由函数"""
    async def router(websocket, *args, payload):
        action_type = payload.get(action_key)
        handler_payload = payload.get('payload', {}) if extract_payload else payload
        handler = handlers.get(action_type)
        if handler:
            return await handler(websocket, *args, handler_payload)
        await send_error(websocket, f'{error_prefix}: {action_type}')
    return router


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
            player['lobsters'].append(create_lobster(grade))
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
        'bonusGold': player.get('bonusGold', 0),
        'bonusPoints': player.get('bonusPoints', 0),
        'lobsters': player.get('lobsters', []),
        'titleCards': player.get('titleCards', []),
        'completedTasks': player.get('completedTasks', []),
        'tavernCompletions': player.get('tavernCompletions', {}),
        'tributeCards': player.get('tributeCards', []),
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


async def update_resources(player: dict, deltas: dict, broadcast_fn=None, delta_broadcast_fn=None):
    """更新玩家资源并广播变化量和快照。
    delta 正数增加，负数减少。
    支持的 delta 格式:
      - int: 直接加减 (coins, seaweed, cages, de, wang, liZhang, bonusPoints, bonusGold)
      - dict with grade keys: 龙虾增减 (lobsters: {'grade3': 1, 'normal': -1})
      - dict with 'add': 数组追加 (titleCards: {'add': [obj]}, completedTasks: {'add': [id]})
      - dict with 'set': 字典设置 (tavernCompletions: {'set': {tavern_id: order}})
    """
    for k, v in deltas.items():
        if k in LOBSTER_GRADES:
            _update_lobster_grade(player, k, v)
        elif k == 'lobsters':
            if isinstance(v, dict):
                for grade, amount in v.items():
                    _update_lobster_grade(player, grade, amount)
        elif k in ('titleCards', 'completedTasks'):
            if isinstance(v, dict) and 'add' in v:
                player.setdefault(k, []).extend(v['add'])
        elif k == 'tavernCompletions':
            if isinstance(v, dict) and 'set' in v:
                player.setdefault(k, {}).update(v['set'])
        else:
            player[k] = player.get(k, 0) + v

    if delta_broadcast_fn:
        await delta_broadcast_fn(player['id'], deltas)
    if broadcast_fn:
        await broadcast_fn(player['id'], _build_resource_snapshot(player))


def get_player(game_state: dict, player_id: int) -> dict:
    """根据 player_id 从 game_state 中查找玩家"""
    return next((p for p in game_state['players'] if p['id'] == player_id), None)