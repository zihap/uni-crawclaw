import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.events import ClientRoomActionTypes, ServerEvents, ServerRoomActionTypes
from utils.game_state import create_game_state, create_player


class MockWebSocket:
    def __init__(self):
        self.sent = []
    async def send_json(self, data):
        self.sent.append(data)
    async def close(self):
        pass


class MockManager:
    def __init__(self):
        self.lobby_connections = {}
        self.user_rooms = {}
        self.active_connections = {}
        self.heartbeat_timestamps = {}
    async def send_to_room(self, room_id, event, data):
        pass
    async def broadcast_to_room_members(self, room_id, event, data):
        pass


def _make_room_with_host():
    gs = create_game_state()
    gs['status'] = 'waiting'
    gs['maxPlayers'] = 4
    host = create_player(0, 'Host', is_host=True, user_id='host_0', position=0)
    gs['players'].append(host)
    return gs


def test_add_ai_creates_ai_player():
    from controllers.room_action_handler import handle_add_ai
    ws = MockWebSocket()
    rooms = {'R001': _make_room_with_host()}
    manager = MockManager()
    asyncio.run(
        handle_add_ai(ws, 'R001', 0, rooms, manager, {})
    )
    gs = rooms['R001']
    assert len(gs['players']) == 2
    ai_player = gs['players'][-1]
    assert ai_player['isAI'] is True
    assert ai_player['ready'] is True


def test_add_ai_rejects_non_host():
    from controllers.room_action_handler import handle_add_ai
    ws = MockWebSocket()
    gs = _make_room_with_host()
    guest = create_player(1, 'Guest', is_host=False, user_id='guest_1', position=1)
    gs['players'].append(guest)
    rooms = {'R001': gs}
    manager = MockManager()
    asyncio.run(
        handle_add_ai(ws, 'R001', 1, rooms, manager, {})
    )
    assert any('errorCode' in str(s) for s in ws.sent)


def test_kick_ai_removes_ai_player():
    from controllers.room_action_handler import handle_add_ai, handle_kick_ai
    ws = MockWebSocket()
    rooms = {'R001': _make_room_with_host()}
    manager = MockManager()
    asyncio.run(
        handle_add_ai(ws, 'R001', 0, rooms, manager, {})
    )
    gs = rooms['R001']
    ai_id = gs['players'][-1]['id']
    ws.sent.clear()
    asyncio.run(
        handle_kick_ai(ws, 'R001', 0, rooms, manager, {'targetPlayerId': ai_id})
    )
    assert len(gs['players']) == 1
    assert not any(p.get('isAI') for p in gs['players'])


def test_kick_ai_rejects_non_ai_target():
    from controllers.room_action_handler import handle_kick_ai
    ws = MockWebSocket()
    rooms = {'R001': _make_room_with_host()}
    manager = MockManager()
    asyncio.run(
        handle_kick_ai(ws, 'R001', 0, rooms, manager, {'targetPlayerId': 0})
    )
    assert any('errorCode' in str(s) or '只能踢出AI' in str(s) for s in ws.sent)
