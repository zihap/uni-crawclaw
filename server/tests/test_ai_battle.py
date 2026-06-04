import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state
from services.ai_player import create_ai_player
from services.ai_scheduler import AIActionScheduler


def test_ai_battle_detection():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'battle'
    gs['currentRound'] = 1
    ai = create_ai_player(0, position=0)
    gs['players'] = [ai]
    gs['battleState'] = {
        'phase': 'lobster_select',
        'attackerId': 0,
        'defenderId': 1,
        'currentPlayerId': 0
    }
    rooms = {'R001': gs}
    scheduler = AIActionScheduler(rooms, None)
    battle = gs.get('battleState')
    assert battle is not None
    ai_id = battle.get('currentPlayerId')
    ai_player = next((p for p in gs['players'] if p['id'] == ai_id and p.get('isAI')), None)
    assert ai_player is not None


def test_ai_no_lobster_forfeit():
    from services.ai_decision_engine import decide_battle_action
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'battle'
    ai = create_ai_player(0, position=0)
    ai['lobsters'] = []
    gs['players'] = [ai]
    battle = {'phase': 'lobster_select', 'attackerId': 0, 'currentPlayerId': 0}
    decision = decide_battle_action(gs, ai, battle)
    assert decision['actionType'] == 'no_lobster_forfeit'
