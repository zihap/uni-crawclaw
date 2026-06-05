import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state
from utils.helpers import make_settlement_state
from services.ai_player import create_ai_player
from services.ai_scheduler import AIActionScheduler


def test_ai_settlement_detection():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'settlement'
    gs['currentArea'] = 0
    gs['currentRound'] = 1
    ai = create_ai_player(0, position=0)
    gs['players'] = [ai]
    gs['settlementState'] = make_settlement_state('shrimp_catching', 0, 1, waiting_for_player=0)
    rooms = {'R001': gs}
    scheduler = AIActionScheduler(rooms, None)
    settlement_state = gs.get('settlementState', {})
    waiting_id = settlement_state.get('waitingForPlayer')
    assert waiting_id is not None
    player = next((p for p in gs['players'] if p['id'] == waiting_id), None)
    assert player is not None
    assert player.get('isAI') is True
