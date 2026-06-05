import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.ai_player import generate_ai_name, create_ai_personality, create_ai_player


def test_generate_ai_name_returns_string():
    name = generate_ai_name()
    assert isinstance(name, str)
    assert len(name) > 0


def test_generate_ai_name_has_prefix_and_suffix():
    name = generate_ai_name()
    assert len(name) >= 3


def test_create_ai_personality_has_five_traits():
    p = create_ai_personality()
    assert 'aggressiveness' in p
    assert 'greed' in p
    assert 'caution' in p
    assert 'patience' in p
    assert 'randomness' in p
    for v in p.values():
        assert 0 <= v <= 1


def test_create_ai_player_has_required_fields():
    player = create_ai_player(0, position=0)
    assert player['isAI'] is True
    assert player['ready'] is True
    assert player['isOnline'] is True
    assert isinstance(player['name'], str)
    assert 'aiPersonality' in player
    assert player['aiState'] == 'idle'


def test_create_ai_player_has_game_resources():
    player = create_ai_player(1, position=1)
    assert player['coins'] > 0
    assert player['seaweed'] >= 0
    assert player['cages'] >= 0
    assert player['liZhang'] > 0
    assert len(player['lobsters']) > 0
