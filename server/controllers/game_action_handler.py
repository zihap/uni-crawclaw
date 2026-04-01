# -*- coding: utf-8 -*-
"""
统一游戏行动路由器
将客户端发送的 gameAction 事件按 actionType 分发到具体 handler
"""

from utils.events import GameActionTypes
from utils.helpers import send_error


def _make_game_action_router(handlers: dict):
    """创建游戏行动路由函数"""
    async def handle_game_action(websocket, room_id, player_id, rooms, manager, payload):
        action_type = payload.get('actionType')
        action_payload = payload.get('payload', {})
        handler = handlers.get(action_type)
        if handler:
            return await handler(websocket, room_id, player_id, rooms, manager, action_payload)
        await send_error(websocket, f'未知的游戏行动: {action_type}')
    return handle_game_action


# 延迟导入，避免循环依赖
def get_game_action_handlers():
    """获取游戏行动处理器映射 (延迟导入避免循环依赖)"""
    from controllers.game_handlers import (
        handle_use_seaweed,
        handle_place_headman,
        handle_next_player,
        handle_next_area,
        handle_exchange_signals,
        handle_buy_item,
        handle_sell_item,
        handle_cultivate_lobster,
        handle_submit_tribute,
        handle_downtown_action,
    )
    return {
        GameActionTypes.USE_SEAWEED: handle_use_seaweed,
        GameActionTypes.PLACE_HEADMAN: handle_place_headman,
        GameActionTypes.NEXT_PLAYER: handle_next_player,
        GameActionTypes.NEXT_AREA: handle_next_area,
        GameActionTypes.EXCHANGE_SIGNALS: handle_exchange_signals,
        GameActionTypes.BUY_ITEM: handle_buy_item,
        GameActionTypes.SELL_ITEM: handle_sell_item,
        GameActionTypes.CULTIVATE_LOBSTER: handle_cultivate_lobster,
        GameActionTypes.SUBMIT_TRIBUTE: handle_submit_tribute,
        GameActionTypes.DOWNTOWN_ACTION: handle_downtown_action,
    }


handle_game_action = _make_game_action_router(get_game_action_handlers())
