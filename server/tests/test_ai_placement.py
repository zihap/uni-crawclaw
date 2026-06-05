import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state
from utils.helpers import make_settlement_state
from services.ai_player import create_ai_player
from services.ai_scheduler import AIActionScheduler, AIWebSocket


class MockManager:
    def __init__(self):
        self.sent = []
    async def send_to_room(self, room_id, event, data):
        self.sent.append(data)
    async def send_to_player(self, room_id, player_id, event, data):
        pass
    async def broadcast_to_room_members(self, room_id, event, data):
        pass


def test_ai_scheduler_calls_placement():
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
    scheduler = AIActionScheduler(rooms, None)
    assert scheduler.is_ai_turn('R001') is True
    ai_player = scheduler.get_current_ai_player('R001')
    assert ai_player is not None
    assert ai_player['isAI'] is True
