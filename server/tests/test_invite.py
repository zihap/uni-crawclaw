# -*- coding: utf-8 -*-
"""
邀请功能测试
"""

import pytest
from unittest.mock import Mock, AsyncMock


class MockWebSocket:
    def __init__(self):
        self.sent_messages = []

    async def send_json(self, data):
        self.sent_messages.append(data)

    async def accept(self):
        pass


@pytest.mark.asyncio
async def test_handle_invite_join():
    """测试邀请加入处理"""
    from controllers.room_action_handler import handle_invite_join

    rooms = {
        'test_room': {
            'players': [],
            'status': 'waiting',
            'maxPlayers': 4
        }
    }

    manager = Mock()
    manager.lobby_connections = {}
    manager.user_rooms = {}
    manager.broadcast_to_room_members = AsyncMock()

    websocket = MockWebSocket()

    payload = {
        'roomId': 'test_room',
        'playerName': '测试玩家',
        'userId': 'test_user_123',
        'inviter': '邀请者'
    }

    await handle_invite_join(websocket, rooms, manager, payload)

    assert len(rooms['test_room']['players']) == 1
    assert rooms['test_room']['players'][0]['name'] == '测试玩家'
    assert len(websocket.sent_messages) == 1
    assert websocket.sent_messages[0]['event'] == 'serverRoomAction'


@pytest.mark.asyncio
async def test_handle_invite_join_room_full():
    """测试房间已满"""
    from controllers.room_action_handler import handle_invite_join

    rooms = {
        'test_room': {
            'players': [{'id': i} for i in range(4)],
            'status': 'waiting',
            'maxPlayers': 4
        }
    }

    manager = Mock()
    websocket = MockWebSocket()

    payload = {
        'roomId': 'test_room',
        'playerName': '测试玩家',
        'userId': 'test_user_123',
        'inviter': '邀请者'
    }

    await handle_invite_join(websocket, rooms, manager, payload)

    assert len(websocket.sent_messages) == 1
    assert websocket.sent_messages[0]['data']['errorCode'] == 'ROOM_FULL'


@pytest.mark.asyncio
async def test_handle_invite_join_game_started():
    """测试游戏已开始"""
    from controllers.room_action_handler import handle_invite_join

    rooms = {
        'test_room': {
            'players': [],
            'status': 'playing',
            'maxPlayers': 4
        }
    }

    manager = Mock()
    websocket = MockWebSocket()

    payload = {
        'roomId': 'test_room',
        'playerName': '测试玩家',
        'userId': 'test_user_123',
        'inviter': '邀请者'
    }

    await handle_invite_join(websocket, rooms, manager, payload)

    assert len(websocket.sent_messages) == 1
    assert websocket.sent_messages[0]['data']['errorCode'] == 'GAME_STARTED'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
