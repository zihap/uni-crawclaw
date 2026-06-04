# -*- coding: utf-8 -*-
"""
AI完整游戏流程集成测试
模拟2个AI玩家 + 1个人类玩家的整局游戏
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from utils.game_state import create_game_state, create_player, distribute_tavern_cards, draw_downtown_cards
from utils.helpers import make_settlement_state, calculate_market_prices
from utils.constants import AREAS, MARKET_PRICES
from services.ai_player import create_ai_player
from services.ai_decision_engine import (
    decide_placement,
    decide_settlement_action,
    decide_battle_action,
    decide_endgame_score_choice
)
from services.ai_scheduler import AIActionScheduler, AIWebSocket


class MockManager:
    """模拟WebSocket管理器，记录所有发送的消息"""

    def __init__(self):
        self.sent_messages = []

    async def send_to_room(self, room_id: str, event: str, data: dict):
        self.sent_messages.append({
            'type': 'room',
            'room_id': room_id,
            'event': event,
            'data': data
        })

    async def send_to_player(self, room_id: str, player_id: int, event: str, data: dict):
        self.sent_messages.append({
            'type': 'player',
            'room_id': room_id,
            'player_id': player_id,
            'event': event,
            'data': data
        })


@pytest.fixture
def game_setup():
    """创建完整的游戏设置"""
    gs = create_game_state()
    gs['status'] = 'playing'
    gs['phase'] = 'placement'
    gs['currentRound'] = 1
    gs['currentPlayerIndex'] = 0

    # 创建1个人类玩家（房主）
    human_player = create_player(0, '人类玩家', is_host=True, position=0)
    human_player['isOnline'] = True

    # 创建2个AI玩家
    ai_player_1 = create_ai_player(1, position=1)
    ai_player_2 = create_ai_player(2, position=2)

    gs['players'] = [human_player, ai_player_1, ai_player_2]

    # 初始化所有区域的slots为空
    for area_name in AREAS:
        slot_count = len(gs['areas'][area_name]['slots'])
        gs['areas'][area_name]['slots'] = [None] * slot_count

    # 初始化酒楼上供卡
    distribute_tavern_cards(gs)

    # 初始化闹市卡
    draw_downtown_cards(gs)

    return gs, human_player, ai_player_1, ai_player_2


class TestAIFullGame:
    """AI完整游戏流程测试"""

    def test_ai_player_creation(self, game_setup):
        """验证AI玩家创建成功，包含所有必要字段"""
        gs, human, ai1, ai2 = game_setup

        # 验证人类玩家
        assert not human.get('isAI', False), "人类玩家不应有isAI标志"
        assert human['isHost'] is True

        # 验证AI玩家1
        assert ai1['isAI'] is True, "AI玩家1应有isAI标志"
        assert ai1['aiState'] == 'idle', "AI玩家1初始状态应为idle"
        assert 'aiPersonality' in ai1, "AI玩家1应有aiPersonality"
        assert 'aiName' in ai1, "AI玩家1应有aiName"
        assert ai1['ready'] is True, "AI玩家1应已准备"
        assert ai1['isOnline'] is True, "AI玩家1应在线"

        # 验证AI玩家2
        assert ai2['isAI'] is True, "AI玩家2应有isAI标志"
        assert ai2['aiState'] == 'idle', "AI玩家2初始状态应为idle"
        assert 'aiPersonality' in ai2, "AI玩家2应有aiPersonality"

        # 验证个性特征
        personality = ai1['aiPersonality']
        assert 0.0 <= personality['aggressiveness'] <= 1.0
        assert 0.0 <= personality['greed'] <= 1.0
        assert 0.0 <= personality['caution'] <= 1.0
        assert 0.0 <= personality['patience'] <= 1.0
        assert 0.0 <= personality['randomness'] <= 1.0

    def test_placement_phase_ai_decisions(self, game_setup):
        """验证AI在放置阶段能自动选择放置位置"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'placement'

        # AI玩家1选择放置位置
        decision1 = decide_placement(gs, ai1)
        assert 'area_index' in decision1, "AI决策应包含area_index"
        assert 'slot_index' in decision1, "AI决策应包含slot_index"
        assert decision1['area_index'] in AREAS, f"area_index应是有效区域，得到: {decision1['area_index']}"
        assert isinstance(decision1['slot_index'], int), "slot_index应为整数"

        # 验证选择的slot是可用的
        area_name = decision1['area_index']
        slot_idx = decision1['slot_index']
        assert 0 <= slot_idx < len(gs['areas'][area_name]['slots']), "slot_index应在有效范围内"

        # 模拟放置后，AI玩家2再选择
        gs['areas'][area_name]['slots'][slot_idx] = ai1['id']
        decision2 = decide_placement(gs, ai2)
        assert decision2['area_index'] in AREAS

    def test_settlement_phase_shrimp_catching(self, game_setup):
        """验证AI在虾捕区域结算时的决策"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'settlement'

        # 设置AI玩家有足够的资源
        ai1['lobsters'] = [{'id': 'lob1', 'grade': 'normal'}]
        ai1['seaweed'] = 2
        ai1['coins'] = 10

        # 创建虾捕区域结算状态
        settlement_state = make_settlement_state(
            'shrimp_catching',
            current_slot_index=0,
            remaining_actions=1,
            waiting_for_player=ai1['id'],
            step='waiting_choice'
        )

        decision = decide_settlement_action(gs, ai1, settlement_state)
        assert 'action_type' in decision, "决策应包含action_type"
        assert 'payload' in decision, "决策应包含payload"

        # 虾捕区域应该返回 choose_either 或 confirm
        assert decision['action_type'] in ['choose_either', 'confirm', 'skip']
        if decision['action_type'] == 'choose_either':
            assert decision['payload'].get('choice') in ['lobster', 'seaweed']

    def test_settlement_phase_seafood_market(self, game_setup):
        """验证AI在海鲜市场结算时的决策"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'settlement'

        # 设置AI玩家资源
        ai1['lobsters'] = [{'id': 'lob1', 'grade': 'normal'}]
        ai1['seaweed'] = 3
        ai1['coins'] = 10
        ai1['cages'] = 2

        # 设置市场动态价格
        gs['areas']['seafood_market']['dynamicPrices'] = calculate_market_prices(3)

        settlement_state = make_settlement_state(
            'seafood_market',
            current_slot_index=0,
            remaining_actions=1,
            waiting_for_player=ai1['id']
        )

        decision = decide_settlement_action(gs, ai1, settlement_state)
        assert 'action_type' in decision
        # 海鲜市场的有效动作
        valid_actions = [
            'sell_lobster', 'buy_lobster', 'sell_seaweed', 'buy_seaweed',
            'buy_seaweed_3', 'sell_cage', 'buy_cage', 'hire_headman_slot', 'skip'
        ]
        assert decision['action_type'] in valid_actions, f"无效的市场动作: {decision['action_type']}"

    def test_settlement_phase_breeding(self, game_setup):
        """验证AI在繁殖区域结算时的决策"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'settlement'

        # 设置AI玩家有可升级的龙虾
        ai1['lobsters'] = [
            {'id': 'lob1', 'grade': 'grade3'},
            {'id': 'lob2', 'grade': 'normal'}
        ]
        ai1['seaweed'] = 2
        ai1['coins'] = 10

        settlement_state = make_settlement_state(
            'breeding',
            current_slot_index=0,
            remaining_actions=1,
            waiting_for_player=ai1['id']
        )

        decision = decide_settlement_action(gs, ai1, settlement_state)
        assert 'action_type' in decision
        assert decision['action_type'] in ['cultivateLobster', 'skip']

        if decision['action_type'] == 'cultivateLobster':
            assert 'lobsterIndex' in decision['payload']

    def test_settlement_phase_tribute(self, game_setup):
        """验证AI在上供区域结算时的决策"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'settlement'

        # 设置AI玩家资源
        ai1['lobsters'] = [
            {'id': 'lob1', 'grade': 'grade1'},
            {'id': 'lob2', 'grade': 'grade3'}
        ]
        ai1['seaweed'] = 5
        ai1['coins'] = 15

        settlement_state = make_settlement_state(
            'tribute',
            current_slot_index=0,
            remaining_actions=1,
            waiting_for_player=ai1['id']
        )

        decision = decide_settlement_action(gs, ai1, settlement_state)
        assert 'action_type' in decision
        # 上供区域的有效动作
        valid_actions = ['submitTribute', 'submitTributeChoice', 'skip']
        assert decision['action_type'] in valid_actions

    def test_settlement_phase_marketplace(self, game_setup):
        """验证AI在市场街结算时的决策"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'settlement'

        # 确保有闹市卡
        if not gs.get('downtownCards'):
            draw_downtown_cards(gs)

        settlement_state = make_settlement_state(
            'marketplace',
            current_slot_index=0,
            remaining_actions=1,
            waiting_for_player=ai1['id']
        )

        decision = decide_settlement_action(gs, ai1, settlement_state)
        assert 'action_type' in decision
        # 市场街的有效动作
        valid_actions = ['executeDowntownAction', 'skip']
        assert decision['action_type'] in valid_actions

    def test_battle_phase_lobster_select(self, game_setup):
        """验证AI在战斗阶段选择龙虾"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'battle'

        # 设置AI玩家有可用的龙虾
        ai1['lobsters'] = [
            {'id': 'lob1', 'grade': 'grade2', 'used': False},
            {'id': 'lob2', 'grade': 'normal', 'used': False}
        ]

        battle = {
            'phase': 'lobster_select',
            'attackerId': ai1['id'],
            'activePlayerId': ai1['id'],
            'currentPlayerId': ai1['id']
        }

        decision = decide_battle_action(gs, ai1, battle)
        assert 'actionType' in decision, "战斗决策应包含actionType"

        if decision['actionType'] == 'lobster_selected':
            assert 'lobsterId' in decision['payload']
            # 验证选择的龙虾ID有效
            valid_ids = [l['id'] for l in ai1['lobsters']]
            assert decision['payload']['lobsterId'] in valid_ids

    def test_battle_phase_dice_roll(self, game_setup):
        """验证AI在战斗阶段掷骰子"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'battle'

        battle = {
            'phase': 'start_roll',
            'attackerId': ai1['id'],
            'activePlayerId': ai1['id'],
            'currentRoll': 0,
            'targetValue': 6
        }

        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'roll_dice', "掷骰子阶段应返回roll_dice"

        # 测试攻击掷骰子
        battle['phase'] = 'attack_roll'
        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'roll_dice'

    def test_battle_phase_seaweed_choice(self, game_setup):
        """验证AI在战斗阶段选择是否使用海草"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'battle'

        # AI有海草
        ai1['seaweed'] = 2

        battle = {
            'phase': 'seaweed_choice',
            'attackerId': ai1['id'],
            'activePlayerId': ai1['id'],
            'currentRoll': 3,
            'targetValue': 6
        }

        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'seaweed_choice'
        assert 'useSeaweed' in decision['payload']
        assert isinstance(decision['payload']['useSeaweed'], bool)

        # AI没有海草
        ai1['seaweed'] = 0
        decision = decide_battle_action(gs, ai1, battle)
        assert decision['payload']['useSeaweed'] is False, "没有海草时应返回False"

    def test_battle_phase_reward_choice(self, game_setup):
        """验证AI在战斗阶段选择奖励"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'battle'

        ai1['lobsters'] = [{'id': 'lob1', 'grade': 'normal', 'used': False}]

        battle = {
            'phase': 'reward_choice',
            'attackerId': ai1['id'],
            'activePlayerId': ai1['id'],
            'winnerId': ai1['id']
        }

        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'claim_battle_reward'
        assert 'rewardType' in decision['payload']
        assert decision['payload']['rewardType'] in ['coins', 'upgrade']

    def test_battle_phase_no_lobster(self, game_setup):
        """验证AI在没有龙虾可用时的处理"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'battle'

        # AI没有龙虾
        ai1['lobsters'] = []

        battle = {
            'phase': 'no_lobster',
            'attackerId': ai1['id'],
            'activePlayerId': ai1['id']
        }

        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'no_lobster_forfeit'

    def test_endgame_score_choice(self, game_setup):
        """验证AI在终局阶段选择得分卡"""
        gs, human, ai1, ai2 = game_setup

        # 设置AI玩家资源
        ai1['coins'] = 10
        ai1['seaweed'] = 5
        ai1['de'] = 2
        ai1['wang'] = 3

        # 创建终局得分卡
        card = {
            'id': 'endgame_coins',
            'name': '金币得分',
            'costResourceType': 'coins'
        }

        decision = decide_endgame_score_choice(ai1, card)
        assert 'cost' in decision, "终局决策应包含cost"
        assert 'reward' in decision, "终局决策应包含reward"
        assert isinstance(decision['cost'], int)
        assert isinstance(decision['reward'], int)

        # 测试海草类型得分卡
        card_seaweed = {
            'id': 'endgame_seaweed',
            'name': '海草得分',
            'costResourceType': 'seaweed'
        }

        decision_seaweed = decide_endgame_score_choice(ai1, card_seaweed)
        assert 'cost' in decision_seaweed
        assert 'reward' in decision_seaweed

    def test_full_game_flow_no_errors(self, game_setup):
        """验证完整游戏流程没有运行时错误"""
        gs, human, ai1, ai2 = game_setup

        # 1. 放置阶段
        gs['phase'] = 'placement'
        for round_num in range(1, 6):
            gs['currentRound'] = round_num
            for player in gs['players']:
                if player.get('isAI'):
                    decision = decide_placement(gs, player)
                    assert 'area_index' in decision
                    assert 'slot_index' in decision
                    # 模拟放置
                    area = decision['area_index']
                    slot = decision['slot_index']
                    if gs['areas'][area]['slots'][slot] is None:
                        gs['areas'][area]['slots'][slot] = player['id']

        # 2. 结算阶段 - 虾捕
        gs['phase'] = 'settlement'
        for player in gs['players']:
            if player.get('isAI'):
                ai1['lobsters'] = [{'id': 'lob1', 'grade': 'normal'}]
                settlement_state = make_settlement_state(
                    'shrimp_catching',
                    current_slot_index=0,
                    remaining_actions=1,
                    waiting_for_player=player['id'],
                    step='waiting_choice'
                )
                decision = decide_settlement_action(gs, player, settlement_state)
                assert 'action_type' in decision

        # 3. 结算阶段 - 海鲜市场
        gs['areas']['seafood_market']['dynamicPrices'] = calculate_market_prices(3)
        for player in gs['players']:
            if player.get('isAI'):
                player['coins'] = 10
                player['lobsters'] = [{'id': 'lob1', 'grade': 'normal'}]
                settlement_state = make_settlement_state(
                    'seafood_market',
                    current_slot_index=0,
                    remaining_actions=1,
                    waiting_for_player=player['id']
                )
                decision = decide_settlement_action(gs, player, settlement_state)
                assert 'action_type' in decision

        # 4. 结算阶段 - 繁殖
        for player in gs['players']:
            if player.get('isAI'):
                player['lobsters'] = [{'id': 'lob1', 'grade': 'grade3'}]
                settlement_state = make_settlement_state(
                    'breeding',
                    current_slot_index=0,
                    remaining_actions=1,
                    waiting_for_player=player['id']
                )
                decision = decide_settlement_action(gs, player, settlement_state)
                assert 'action_type' in decision

        # 5. 战斗阶段
        gs['phase'] = 'battle'
        ai1['lobsters'] = [{'id': 'lob1', 'grade': 'grade2', 'used': False}]
        ai1['seaweed'] = 2

        # 龙虾选择
        battle = {
            'phase': 'lobster_select',
            'attackerId': ai1['id'],
            'activePlayerId': ai1['id']
        }
        decision = decide_battle_action(gs, ai1, battle)
        assert 'actionType' in decision

        # 掷骰子
        battle['phase'] = 'start_roll'
        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'roll_dice'

        # 海草选择
        battle['phase'] = 'seaweed_choice'
        battle['currentRoll'] = 3
        battle['targetValue'] = 6
        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'seaweed_choice'

        # 奖励选择
        battle['phase'] = 'reward_choice'
        battle['winnerId'] = ai1['id']
        decision = decide_battle_action(gs, ai1, battle)
        assert decision['actionType'] == 'claim_battle_reward'

        # 6. 终局得分
        ai1['coins'] = 10
        card = {'id': 'endgame', 'costResourceType': 'coins'}
        decision = decide_endgame_score_choice(ai1, card)
        assert 'cost' in decision

    def test_ai_scheduler_detection(self, game_setup):
        """验证AI调度器能正确检测AI回合"""
        gs, human, ai1, ai2 = game_setup
        rooms = {'TEST01': gs}
        manager = MockManager()
        scheduler = AIActionScheduler(rooms, manager)

        # 设置当前玩家为AI
        gs['currentPlayerIndex'] = 1
        assert scheduler.is_ai_turn('TEST01') is True

        # 获取当前AI玩家
        current_ai = scheduler.get_current_ai_player('TEST01')
        assert current_ai is not None
        assert current_ai['isAI'] is True
        assert current_ai['id'] == ai1['id']

        # 设置当前玩家为人类
        gs['currentPlayerIndex'] = 0
        assert scheduler.is_ai_turn('TEST01') is False

    def test_ai_scheduler_battle_detection(self, game_setup):
        """验证AI调度器在战斗阶段的检测"""
        gs, human, ai1, ai2 = game_setup
        gs['phase'] = 'battle'

        rooms = {'TEST01': gs}
        manager = MockManager()
        scheduler = AIActionScheduler(rooms, manager)

        # 设置战斗状态，AI为活跃玩家
        gs['current_battle'] = {
            'activePlayerId': ai1['id'],
            'phase': 'lobster_select'
        }

        # get_current_ai_player 基于 currentPlayerIndex，需要设置为AI的索引
        gs['currentPlayerIndex'] = 1  # ai1 的索引
        ai_player = scheduler.get_current_ai_player('TEST01')
        assert ai_player is not None
        assert ai_player['id'] == ai1['id']
        assert ai_player['isAI'] is True

    def test_multiple_ai_personality_differences(self):
        """验证不同AI玩家有不同的个性"""
        ai1 = create_ai_player(1, position=0)
        ai2 = create_ai_player(2, position=1)

        # 由于随机生成，我们验证字段存在且在有效范围
        p1 = ai1['aiPersonality']
        p2 = ai2['aiPersonality']

        for key in ['aggressiveness', 'greed', 'caution', 'patience', 'randomness']:
            assert key in p1
            assert key in p2
            assert 0.0 <= p1[key] <= 1.0
            assert 0.0 <= p2[key] <= 1.0

    def test_mock_manager_message_recording(self):
        """验证MockManager正确记录消息"""
        manager = MockManager()

        # 测试房间消息
        import asyncio
        asyncio.run(manager.send_to_room('ROOM01', 'test_event', {'key': 'value'}))
        assert len(manager.sent_messages) == 1
        assert manager.sent_messages[0]['type'] == 'room'
        assert manager.sent_messages[0]['room_id'] == 'ROOM01'
        assert manager.sent_messages[0]['event'] == 'test_event'

        # 测试玩家消息
        asyncio.run(manager.send_to_player('ROOM01', 1, 'player_event', {'data': 123}))
        assert len(manager.sent_messages) == 2
        assert manager.sent_messages[1]['type'] == 'player'
        assert manager.sent_messages[1]['player_id'] == 1

    def test_ai_websocket_no_errors(self):
        """验证AIWebSocket桩不会抛出错误"""
        import asyncio
        ws = AIWebSocket()

        # 测试各种操作
        asyncio.run(ws.send_json({'actionType': 'test', 'data': {}}))
        asyncio.run(ws.send_error('test error'))
        asyncio.run(ws.close())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
