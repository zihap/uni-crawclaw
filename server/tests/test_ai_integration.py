import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.game_state import create_game_state, create_player
from services.ai_player import create_ai_player
from services.ai_scheduler import AIActionScheduler, AIWebSocket
from services.ai_decision_engine import decide_placement, decide_settlement_action, decide_battle_action


class MockManager:
    def __init__(self):
        self.sent = []
    async def send_to_room(self, room_id, event, data):
        self.sent.append((event, data))
    async def send_to_player(self, room_id, player_id, event, data):
        pass


def test_full_ai_placement_flow():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'placement'
    gs['currentRound'] = 1
    gs['currentPlayerIndex'] = 0
    ai = create_ai_player(0, position=0)
    gs['players'] = [ai]
    for area_name in ['shrimp_catching', 'seafood_market', 'breeding', 'tribute', 'marketplace']:
        gs['areas'][area_name]['slots'] = [None] * len(gs['areas'][area_name]['slots'])
    decision = decide_placement(gs, ai)
    assert 'area_index' in decision
    assert 'slot_index' in decision


def test_full_ai_settlement_flow():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'settlement'
    gs['currentRound'] = 1
    gs['currentArea'] = 0
    ai = create_ai_player(0, position=0)
    ai['lobsters'] = [{'id': 'test1', 'grade': 'grade3'}]
    ai['seaweed'] = 2
    ai['coins'] = 10
    gs['players'] = [ai]
    from utils.helpers import make_settlement_state
    gs['settlementState'] = make_settlement_state('shrimp_catching', 0, 1, waiting_for_player=0)
    decision = decide_settlement_action(gs, ai, gs['settlementState'])
    assert 'action_type' in decision
    assert 'payload' in decision


def test_full_ai_battle_flow():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'battle'
    ai = create_ai_player(0, position=0)
    ai['lobsters'] = [{'id': 'test1', 'grade': 'grade2', 'used': False}]
    gs['players'] = [ai]
    battle = {'phase': 'lobster_select', 'attackerId': 0, 'currentPlayerId': 0}
    decision = decide_battle_action(gs, ai, battle)
    assert 'actionType' in decision


def test_ai_scheduler_integration():
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
    ai_player = scheduler.get_current_ai_player('R001')
    assert ai_player['isAI'] is True
    assert ai_player['aiState'] == 'idle'


def test_ai_personality_variation():
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'placement'
    gs['currentRound'] = 1
    for area_name in ['shrimp_catching', 'seafood_market', 'breeding', 'tribute', 'marketplace']:
        gs['areas'][area_name]['slots'] = [None] * len(gs['areas'][area_name]['slots'])
    aggressive_ai = create_ai_player(0, position=0)
    aggressive_ai['aiPersonality'] = {
        'aggressiveness': 0.9, 'greed': 0.8, 'caution': 0.2, 'patience': 0.3, 'randomness': 0.1
    }
    gs['players'] = [aggressive_ai]
    decisions = [decide_placement(gs, aggressive_ai)['area_index'] for _ in range(20)]
    from collections import Counter
    counts = Counter(decisions)
    most_common = counts.most_common(1)[0][1]
    assert most_common >= 5
