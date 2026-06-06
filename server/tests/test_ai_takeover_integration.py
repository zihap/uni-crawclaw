# -*- coding: utf-8 -*-
"""
AI接管功能集成测试
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.ai_scheduler import AIActionScheduler
from utils.game_state import create_player
from utils.events import ServerRoomActionTypes


class TestAITakeoverIntegration:
    """AI接管功能集成测试类"""

    @pytest.mark.asyncio
    async def test_full_takeover_flow(self, monkeypatch):
        """测试完整的AI接管流程 - 验证 start_takeover_timer 实际执行"""
        # 创建测试环境
        rooms = {}
        manager = MagicMock()
        manager.ai_schedulers = {}
        manager.send_to_room = AsyncMock()
        
        room_id = 'test_room'
        player_id = 0
        player = create_player(player_id, 'Test Player')
        player['isOnline'] = False
        
        rooms[room_id] = {
            'players': [player],
            'status': 'playing',
            'currentPlayerIndex': 0
        }
        
        scheduler = AIActionScheduler(rooms, manager)
        
        # 替换 asyncio.sleep，避免实际等待60秒
        async def mock_sleep(seconds):
            pass  # 直接返回，不等待
        
        monkeypatch.setattr(asyncio, 'sleep', mock_sleep)
        
        # 调用实际的 start_takeover_timer 方法
        await scheduler.start_takeover_timer(room_id, player_id, rooms, manager)
        
        # 等待异步任务完成
        for task in scheduler.ai_takeover_timers.values():
            await task
        
        # 验证接管状态
        assert player['isAITakeover'] == True
        assert player['aiTakeoverTime'] is not None
        
        # 验证通知已发送
        manager.send_to_room.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnect_after_takeover(self, monkeypatch):
        """测试AI接管后玩家重连"""
        # 创建测试环境
        rooms = {}
        manager = MagicMock()
        manager.ai_schedulers = {}
        manager.send_to_room = AsyncMock()
        
        room_id = 'test_room'
        player_id = 0
        player = create_player(player_id, 'Test Player')
        player['isOnline'] = False
        
        rooms[room_id] = {
            'players': [player],
            'status': 'playing',
            'currentPlayerIndex': 0
        }
        
        scheduler = AIActionScheduler(rooms, manager)
        
        # 替换 asyncio.sleep
        async def mock_sleep(seconds):
            pass
        
        monkeypatch.setattr(asyncio, 'sleep', mock_sleep)
        
        # 调用 start_takeover_timer
        await scheduler.start_takeover_timer(room_id, player_id, rooms, manager)
        
        # 等待异步任务完成
        for task in scheduler.ai_takeover_timers.values():
            await task
        
        # 验证接管状态
        assert player['isAITakeover'] == True
        
        # 模拟玩家重连
        player['isOnline'] = True
        player['isAITakeover'] = False
        player.pop('aiTakeoverTime', None)
        scheduler.cancel_takeover_timer(room_id, player_id)
        
        # 验证状态已清除
        assert player['isAITakeover'] == False
        assert 'aiTakeoverTime' not in player
        assert player['isOnline'] == True

    @pytest.mark.asyncio
    async def test_takeover_cancelled_on_reconnect_within_60s(self, monkeypatch):
        """测试60秒内重连时AI接管被取消"""
        # 创建测试环境
        rooms = {}
        manager = MagicMock()
        manager.ai_schedulers = {}
        manager.send_to_room = AsyncMock()
        
        room_id = 'test_room'
        player_id = 0
        player = create_player(player_id, 'Test Player')
        player['isOnline'] = False
        
        rooms[room_id] = {
            'players': [player],
            'status': 'playing',
            'currentPlayerIndex': 0
        }
        
        scheduler = AIActionScheduler(rooms, manager)
        
        # 不替换 asyncio.sleep，而是使用 asyncio.create_task 异步启动
        # 然后在任务执行前取消它
        
        # 调用 start_takeover_timer（会创建异步任务）
        await scheduler.start_takeover_timer(room_id, player_id, rooms, manager)
        
        # 验证定时器已创建
        key = f"{room_id}_{player_id}"
        assert key in scheduler.ai_takeover_timers
        
        # 模拟玩家在60秒内重连，取消定时器
        scheduler.cancel_takeover_timer(room_id, player_id)
        
        # 验证定时器已取消
        assert key not in scheduler.ai_takeover_timers
        
        # 验证玩家状态未被AI接管
        assert player['isAITakeover'] == False