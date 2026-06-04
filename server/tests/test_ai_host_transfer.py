import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state, create_player
from services.ai_player import create_ai_player
from services.game import transfer_host


def test_transfer_host_skips_ai():
    gs = create_game_state()
    gs['status'] = 'waiting'
    host = create_player(0, 'Host', is_host=True, user_id='h0', position=0)
    host['isOnline'] = False
    ai = create_ai_player(1, position=1)
    ai['isOnline'] = True
    human = create_player(2, 'Human', is_host=False, user_id='h2', position=2)
    human['isOnline'] = True
    gs['players'] = [host, ai, human]
    transfer_host('R001', gs)
    assert human['isHost'] is True
    assert ai['isHost'] is False
    assert host['isHost'] is False


def test_transfer_host_all_ai_no_transfer():
    gs = create_game_state()
    gs['status'] = 'waiting'
    host = create_player(0, 'Host', is_host=True, user_id='h0', position=0)
    host['isOnline'] = False
    ai1 = create_ai_player(1, position=1)
    ai1['isOnline'] = True
    ai2 = create_ai_player(2, position=2)
    ai2['isOnline'] = True
    gs['players'] = [host, ai1, ai2]
    transfer_host('R001', gs)
    assert host['isHost'] is True
    assert ai1['isHost'] is False
    assert ai2['isHost'] is False
