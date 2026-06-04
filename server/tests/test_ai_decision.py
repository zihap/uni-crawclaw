import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state
from services.ai_player import create_ai_player
from services.ai_decision_engine import decide_placement, softmax_choice


def test_softmax_choice_returns_valid_index():
    scores = [0.5, 0.8, 0.3, 0.9]
    idx = softmax_choice(scores, temperature=1.0)
    assert 0 <= idx < len(scores)


def test_softmax_choice_deterministic_low_temp():
    scores = [0.1, 0.1, 0.1, 0.9]
    results = [softmax_choice(scores, temperature=0.01) for _ in range(100)]
    assert results.count(3) > 90


def test_decide_placement_returns_valid_decision():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'placement'
    gs['currentRound'] = 1

    ai = create_ai_player(0, position=0)
    gs['players'] = [ai]

    for area_name in ['shrimp_catching', 'seafood_market', 'breeding', 'tribute', 'marketplace']:
        area_data = gs['areas'][area_name]
        area_data['slots'] = [None] * len(area_data['slots'])

    decision = decide_placement(gs, ai)
    assert 'area_index' in decision
    assert 'slot_index' in decision
    assert isinstance(decision['area_index'], (str, int))
    assert isinstance(decision['slot_index'], int)


def test_decide_placement_ignores_occupied_slots():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'placement'
    gs['currentRound'] = 1

    ai = create_ai_player(0, position=0)
    gs['players'] = [ai]

    gs['areas']['shrimp_catching']['slots'] = [0, 0, 0, 0]
    gs['areas']['seafood_market']['slots'] = [0, 0, 0, 0]

    for area_name in ['breeding', 'tribute', 'marketplace']:
        area_data = gs['areas'][area_name]
        area_data['slots'] = [None] * len(area_data['slots'])

    decision = decide_placement(gs, ai)
    assert decision['area_index'] not in ['shrimp_catching', 'seafood_market']
