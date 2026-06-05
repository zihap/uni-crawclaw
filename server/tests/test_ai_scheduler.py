import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.ai_scheduler import AIWebSocket, AIActionScheduler


def test_ai_websocket_send_json_is_noop():
    ws = AIWebSocket()
    asyncio.run(ws.send_json({'test': 1}))


def test_ai_websocket_send_error_is_noop():
    ws = AIWebSocket()
    asyncio.run(ws.send_error('test error'))


def test_ai_websocket_close_is_noop():
    ws = AIWebSocket()
    asyncio.run(ws.close())


def test_ai_scheduler_init():
    rooms = {}
    manager = None
    scheduler = AIActionScheduler(rooms, manager)
    assert scheduler.rooms is rooms
    assert scheduler.manager is manager


def test_ai_scheduler_detects_ai_turn():
    from utils.game_state import create_game_state, create_player
    from services.ai_player import create_ai_player

    gs = create_game_state()
    human = create_player(0, 'Human', is_host=True, user_id='h0', position=0)
    ai = create_ai_player(1, position=1)
    gs['players'] = [human, ai]
    gs['currentPlayerIndex'] = 1
    gs['status'] = 'playing'
    gs['phase'] = 'placement'

    rooms = {'R001': gs}
    scheduler = AIActionScheduler(rooms, None)
    assert scheduler.is_ai_turn('R001') is True


def test_ai_scheduler_detects_human_turn():
    from utils.game_state import create_game_state, create_player
    from services.ai_player import create_ai_player

    gs = create_game_state()
    human = create_player(0, 'Human', is_host=True, user_id='h0', position=0)
    ai = create_ai_player(1, position=1)
    gs['players'] = [human, ai]
    gs['currentPlayerIndex'] = 0
    gs['status'] = 'playing'
    gs['phase'] = 'placement'

    rooms = {'R001': gs}
    scheduler = AIActionScheduler(rooms, None)
    assert scheduler.is_ai_turn('R001') is False
