# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state, create_player
from services.ai_player import create_ai_player
from services.ai_scheduler import AIActionScheduler


class MockManager:
    def __init__(self):
        self.ai_schedulers = {}

    async def send_to_room(self, room_id, event, data):
        pass

    async def send_to_player(self, room_id, player_id, event, data):
        pass

    async def broadcast_to_room_members(self, room_id, event, data):
        pass


def test_scheduler_created_per_room():
    rooms = {'R001': create_game_state()}
    manager = MockManager()
    scheduler = AIActionScheduler(rooms, manager)
    manager.ai_schedulers['R001'] = scheduler
    assert 'R001' in manager.ai_schedulers


def test_check_and_trigger_skips_non_playing():
    gs = create_game_state()
    gs['status'] = 'waiting'
    rooms = {'R001': gs}
    scheduler = AIActionScheduler(rooms, MockManager())
    import asyncio
    asyncio.run(
        scheduler.check_and_trigger('R001', None, rooms, None))


def test_check_and_trigger_placement():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'placement'
    gs['currentPlayerIndex'] = 0
    gs['currentRound'] = 1
    ai = create_ai_player(0, position=0)
    gs['players'] = [ai]
    for area_name in ['shrimp_catching', 'seafood_market', 'breeding', 'tribute', 'marketplace']:
        gs['areas'][area_name]['slots'] = [None] * len(gs['areas'][area_name]['slots'])
    rooms = {'R001': gs}
    scheduler = AIActionScheduler(rooms, MockManager())
    assert scheduler.is_ai_turn('R001') is True
