# -*- coding: utf-8 -*-
"""
AI接管功能测试
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.ai_scheduler import AIActionScheduler
from utils.game_state import create_player
from utils.helpers import is_ai_player


class TestAITakeover:
    """AI接管功能测试类"""

    def setup_method(self):
        """测试前准备"""
        self.rooms = {}
        self.manager = MagicMock()
        self.manager.ai_schedulers = {}
        self.scheduler = AIActionScheduler(self.rooms, self.manager)

    @pytest.mark.asyncio
    async def test_start_takeover_timer(self):
        """测试启动AI接管定时器"""
        room_id = 'test_room'
        player_id = 0
        player = create_player(player_id, 'Test Player')
        player['isOnline'] = False
        
        self.rooms[room_id] = {
            'players': [player],
            'status': 'playing'
        }
        
        # 启动定时器
        await self.scheduler.start_takeover_timer(room_id, player_id, self.rooms, self.manager)
        
        # 验证定时器已创建
        key = f"{room_id}_{player_id}"
        assert key in self.scheduler.ai_takeover_timers
        
        # 取消定时器（避免实际等待60秒）
        self.scheduler.cancel_takeover_timer(room_id, player_id)

    @pytest.mark.asyncio
    async def test_cancel_takeover_timer(self):
        """测试取消AI接管定时器"""
        room_id = 'test_room'
        player_id = 0
        
        # 创建定时器
        key = f"{room_id}_{player_id}"
        self.scheduler.ai_takeover_timers[key] = asyncio.create_task(asyncio.sleep(60))
        
        # 取消定时器
        self.scheduler.cancel_takeover_timer(room_id, player_id)
        
        # 验证定时器已取消
        assert key not in self.scheduler.ai_takeover_timers

    def test_is_ai_turn_with_takeover(self):
        """测试AI回合检测（包括AI接管）"""
        room_id = 'test_room'
        player = create_player(0, 'Test Player')
        player['isAITakeover'] = True
        
        self.rooms[room_id] = {
            'players': [player],
            'status': 'playing',
            'currentPlayerIndex': 0
        }
        
        # 验证AI接管玩家被识别为AI回合
        assert self.scheduler.is_ai_turn(room_id) == True

    def test_is_ai_turn_without_takeover(self):
        """测试AI回合检测（无AI接管）"""
        room_id = 'test_room'
        player = create_player(0, 'Test Player')
        player['isAITakeover'] = False
        
        self.rooms[room_id] = {
            'players': [player],
            'status': 'playing',
            'currentPlayerIndex': 0
        }
        
        # 验证普通玩家不被识别为AI回合
        assert self.scheduler.is_ai_turn(room_id) == False

    def test_get_current_ai_player_with_takeover(self):
        """测试获取当前AI玩家（包括AI接管）"""
        room_id = 'test_room'
        player = create_player(0, 'Test Player')
        player['isAITakeover'] = True
        
        self.rooms[room_id] = {
            'players': [player],
            'currentPlayerIndex': 0
        }
        
        # 验证能获取AI接管玩家
        result = self.scheduler.get_current_ai_player(room_id)
        assert result is not None
        assert result['id'] == 0

    @pytest.mark.asyncio
    async def test_cleanup_room_timers(self):
        """测试清理房间定时器"""
        room_id = 'test_room'
        
        # 创建定时器
        key1 = f"{room_id}_0"
        key2 = f"{room_id}_1"
        task1 = asyncio.create_task(asyncio.sleep(60))
        task2 = asyncio.create_task(asyncio.sleep(60))
        self.scheduler.ai_takeover_timers[key1] = task1
        self.scheduler.ai_takeover_timers[key2] = task2
        
        # 清理定时器
        self.scheduler.cleanup_room_timers(room_id)
        
        # 验证定时器已清理
        assert key1 not in self.scheduler.ai_takeover_timers
        assert key2 not in self.scheduler.ai_takeover_timers
        
        # 等待已取消的任务（抑制警告）
        for t in [task1, task2]:
            try:
                await t
            except asyncio.CancelledError:
                pass

    def test_is_ai_player_with_takeover(self):
        """测试is_ai_player对AI接管玩家返回True"""
        player = create_player(0, 'Test Player')
        player['isAITakeover'] = True
        assert is_ai_player(player) == True

    def test_is_ai_player_with_ai(self):
        """测试is_ai_player对原AI玩家返回True"""
        from services.ai_player import create_ai_player
        player = create_ai_player(0, 0)
        assert is_ai_player(player) == True

    def test_is_ai_player_with_human(self):
        """测试is_ai_player对普通人类玩家返回False"""
        player = create_player(0, 'Test Player')
        assert is_ai_player(player) == False

    def test_is_ai_turn_detects_takeover_during_other_turn(self):
        """回归测试：其他玩家行动时掉线，AI接管后能检测到当前玩家是AI"""
        room_id = 'test_room'
        player0 = create_player(0, 'Player 0')
        player0['isAITakeover'] = True  # 被AI接管
        player1 = create_player(1, 'Player 1')
        
        self.rooms[room_id] = {
            'players': [player0, player1],
            'status': 'playing',
            'currentPlayerIndex': 0  # 轮到被接管的玩家
        }
        
        # 验证AI接管玩家被正确识别为AI
        assert self.scheduler.is_ai_turn(room_id) == True
        assert self.scheduler.get_current_ai_player(room_id) is not None
        assert self.scheduler.get_current_ai_player(room_id)['id'] == 0

    @pytest.mark.asyncio
    async def test_settlement_detects_takeover_player(self):
        """回归测试：结算阶段AI接管玩家被正确识别为AI"""
        room_id = 'test_room'
        player = create_player(0, 'Test Player')
        player['isAITakeover'] = True
        
        self.rooms[room_id] = {
            'players': [player],
            'status': 'playing',
            'phase': 'settlement',
            'settlementState': {'waitingForPlayer': 0},
            'currentArea': 0
        }
        
        # 验证is_ai_turn能检测到AI接管玩家
        assert self.scheduler.is_ai_turn(room_id) == True
