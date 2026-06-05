import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state, create_player
from services.ai_player import create_ai_player
from services.tribute_card_effects import get_endgame_choices


def test_endgame_ai_auto_choice():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['currentRound'] = 5
    gs['maxRounds'] = 5
    ai = create_ai_player(0, position=0)
    ai['tributeCards'] = [{
        'id': 'tribute_endgame',
        'name': 'test_endgame',
        'effectType': 'aura_endgame_score',
        'reward': {'de': 2}
    }]
    gs['players'] = [ai]
    choices = get_endgame_choices(ai, ai['tributeCards'][0])
    assert len(choices) > 0
