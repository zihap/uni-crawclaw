import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.events import ClientRoomActionTypes, ServerRoomActionTypes


def test_add_ai_action_type_exists():
    assert hasattr(ClientRoomActionTypes, 'ADD_AI')
    assert ClientRoomActionTypes.ADD_AI == 'addAI'


def test_kick_ai_action_type_exists():
    assert hasattr(ClientRoomActionTypes, 'KICK_AI')
    assert ClientRoomActionTypes.KICK_AI == 'kickAI'


def test_ai_action_server_types_exist():
    assert hasattr(ServerRoomActionTypes, 'AI_ADDED')
    assert ServerRoomActionTypes.AI_ADDED == 'aiAdded'
    assert hasattr(ServerRoomActionTypes, 'AI_KICKED')
    assert ServerRoomActionTypes.AI_KICKED == 'aiKicked'
