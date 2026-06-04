# -*- coding: utf-8 -*-
"""
AI行动调度器与WebSocket桩
"""

import asyncio
import random
from typing import Optional
from utils.logger import log_info
from utils.constants import AREAS
from utils.events import ServerEvents, ServerAreaActionTypes, ServerBattleActionTypes
from utils.helpers import make_action_message


class AIWebSocket:
    """AI专用WebSocket桩，复用现有handler时替代真实websocket"""

    async def send_json(self, data: dict):
        """空操作，仅记录日志"""
        log_info(f"[AI-WS] send_json: actionType={data.get('data', {}).get('actionType', data.get('actionType', 'N/A'))}")

    async def send_error(self, message: str):
        """空操作"""
        log_info(f"[AI-WS] send_error: {message}")

    async def close(self):
        """空操作"""
        pass


class AIActionScheduler:
    """AI行动调度器 — 检测AI轮次并自动触发行动"""

    def __init__(self, rooms: dict, manager):
        self.rooms = rooms
        self.manager = manager
        self._running_tasks: dict = {}  # room_id -> asyncio.Task
        self._in_battle_loop = False  # 重入保护
        self._in_check_trigger = False  # check_and_trigger重入保护

    def is_ai_turn(self, room_id: str) -> bool:
        """检测当前是否为AI玩家的回合"""
        gs = self.rooms.get(room_id)
        if not gs or gs.get('status') != 'playing':
            return False
        players = gs.get('players', [])
        idx = gs.get('currentPlayerIndex', 0)
        if idx < 0 or idx >= len(players):
            return False
        return players[idx].get('isAI', False)

    def get_current_ai_player(self, room_id: str) -> Optional[dict]:
        """获取当前AI玩家"""
        gs = self.rooms.get(room_id)
        if not gs:
            return None
        players = gs.get('players', [])
        idx = gs.get('currentPlayerIndex', 0)
        if 0 <= idx < len(players) and players[idx].get('isAI'):
            return players[idx]
        return None

    async def _handle_tribute_lobster_selection(self, room_id: str, gs: dict, manager):
        """处理tribute战斗的AI龙虾选择和判负逻辑"""
        from controllers.battle_action_handler import arena_betting_state, start_rpg_battle
        battle_queue = gs.get('battleQueue', [])
        if not battle_queue:
            return

        for battle_info in list(battle_queue):
            cid = battle_info['challengerId']
            did = battle_info['defenderId']
            bid = str(battle_info.get('battleId', battle_info.get('challengeSlot', f"{cid}_{did}")))
            key = f"{room_id}_{bid}"

            if key not in arena_betting_state:
                spectators = [p['id'] for p in gs['players'] if p['id'] != cid and p['id'] != did]
                arena_betting_state[key] = {
                    'battleId': bid, 'challengerId': cid, 'defenderId': did,
                    'challengerLobster': None, 'defenderLobster': None,
                    'spectators': spectators, 'bets': {}, 'started': False, 'completed': False
                }
            state = arena_betting_state[key]

            grade_order = {'royal': 5, 'grade1': 4, 'grade2': 3, 'grade3': 2, 'normal': 1}

            for pid, role in [(cid, 'challengerLobster'), (did, 'defenderLobster')]:
                if state[role] is not None:
                    continue
                player = next((p for p in gs['players'] if p['id'] == pid), None)
                if not player or not player.get('isAI'):
                    continue
                available = [l for l in player.get('lobsters', []) if not l.get('used') and not l.get('selectedForBattle') and l.get('grade', 'normal') != 'normal']
                if available:
                    best = max(available, key=lambda l: grade_order.get(l.get('grade', 'normal'), 0))
                    best['selectedForBattle'] = True
                    state[role] = best
                    log_info(f"[tribute_lobster] AI player {pid} auto-selected lobster {best.get('id')} ({best.get('grade')})")
                    # 通知前端AI已选龙虾
                    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                        make_action_message(ServerBattleActionTypes.LOBSTER_SELECTED, {
                            'playerId': pid, 'lobster': best
                        }))
                else:
                    log_info(f"[tribute_lobster] AI player {pid} has no battle lobster")

            forfeit_loser = None
            c_has = state['challengerLobster'] is not None
            d_has = state['defenderLobster'] is not None
            c_player = next((p for p in gs['players'] if p['id'] == cid), None)
            d_player = next((p for p in gs['players'] if p['id'] == did), None)
            c_is_ai = c_player and c_player.get('isAI')
            d_is_ai = d_player and d_player.get('isAI')

            if not c_has and c_is_ai:
                forfeit_loser = cid
            elif not d_has and d_is_ai:
                forfeit_loser = did

            if forfeit_loser is not None:
                from utils.constants import CHALLENGE_SLOT_DONE
                challenge_slot = battle_info.get('challengeSlot', 0)
                winner_is_challenge = (forfeit_loser == did)

                tribute = gs.get('areas', {}).get('tribute', {})
                challenge_slots = tribute.get('challengeSlots', [])
                if 0 <= challenge_slot - 3 < len(challenge_slots):
                    challenge_slots[challenge_slot - 3] = CHALLENGE_SLOT_DONE

                if winner_is_challenge:
                    from controllers.battle_action_handler import swap_challenge_slot
                    swap_challenge_slot(gs, challenge_slot)

                gs['battleQueue'] = [b for b in gs.get('battleQueue', []) if b.get('challengeSlot') != challenge_slot]

                await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                    make_action_message('battleEnded', {
                        'actionType': 'battleEnded',
                        'reason': 'no_available_lobsters',
                        'forfeitPlayerId': forfeit_loser,
                        'gameState': gs
                    }))

                continue  # 判负处理完成，继续处理下一个战斗

            # 双方都已选龙虾
            c_player = next((p for p in gs['players'] if p['id'] == cid), None)
            d_player = next((p for p in gs['players'] if p['id'] == did), None)
            both_ai = (c_player and c_player.get('isAI')) and (d_player and d_player.get('isAI'))
            if state['challengerLobster'] and state['defenderLobster'] and not state['started'] and both_ai:
                state['started'] = True
                spectators = state.get('spectators', [])
                has_human_spectators = any(
                    not next((p for p in gs['players'] if p['id'] == sid), {}).get('isAI')
                    for sid in spectators
                )
                if has_human_spectators:
                    # 有人类观战者，进入竞拍阶段
                    log_info(f"[tribute_lobster] both AI lobsters selected, starting betting phase")
                    auto_bet = []
                    for sid in spectators:
                        sp = next((p for p in gs['players'] if p['id'] == sid), None)
                        if sp and (sp.get('isAI') or sp.get('coins', 0) == 0):
                            state['bets'][sid] = {'amount': 0, 'target': None}
                            auto_bet.append(sid)
                    await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                        make_action_message(ServerBattleActionTypes.ARENA_BETTING_START, {
                            'battleId': bid,
                            'challengerId': cid,
                            'challengerName': c_player['name'] if c_player else '',
                            'challengerLobster': state['challengerLobster'],
                            'defenderId': did,
                            'defenderName': d_player['name'] if d_player else '',
                            'defenderLobster': state['defenderLobster'],
                            'spectators': spectators,
                            'autoBetSpectators': auto_bet
                        }))
                    all_bet = all(sid in state['bets'] for sid in spectators)
                    if all_bet:
                        from controllers.battle_action_handler import _start_battle_after_betting
                        await _start_battle_after_betting(room_id, bid, gs, manager)
                else:
                    # 全是AI观战或无观战者，直接开始战斗
                    log_info(f"[tribute_lobster] both AI lobsters selected, starting RPG battle directly")
                    await start_rpg_battle(room_id, bid, gs, manager)

        # 检查是否有人类玩家需要选龙虾，如果是，发送BATTLE_START通知前端
        needs_human_input = False
        for battle_info in gs.get('battleQueue', []):
            cid = battle_info['challengerId']
            did = battle_info['defenderId']
            bid = str(battle_info.get('battleId', battle_info.get('challengeSlot', f"{cid}_{did}")))
            key = f"{room_id}_{bid}"
            state = arena_betting_state.get(key)
            if not state:
                needs_human_input = True
                break
            for pid, role in [(cid, 'challengerLobster'), (did, 'defenderLobster')]:
                player = next((p for p in gs['players'] if p['id'] == pid), None)
                if player and not player.get('isAI') and state[role] is None:
                    needs_human_input = True
                    break
            if needs_human_input:
                break
        if needs_human_input:
            await manager.send_to_room(room_id, ServerEvents.SERVER_BATTLE_ACTION,
                make_action_message(ServerBattleActionTypes.BATTLE_START, {
                    'battleQueue': gs['battleQueue']
                }))

    async def schedule_ai_placement(self, room_id: str, websocket, rooms, manager, handle_place_headman_fn, handle_next_player_fn):
        """调度AI放置阶段行动（循环处理连续AI回合）"""
        while True:
            gs = self.rooms.get(room_id)
            if not gs or gs.get('phase') != 'placement':
                return

            ai_player = self.get_current_ai_player(room_id)
            if not ai_player:
                return

            think_time = random.uniform(1.0, 3.0)
            ai_player['aiState'] = 'thinking'
            await asyncio.sleep(think_time)

            ai_player['aiState'] = 'acting'

            from services.ai_decision_engine import decide_placement
            decision = decide_placement(gs, ai_player)

            ai_ws = AIWebSocket()

            area_index = decision['area_index']
            slot_index = decision['slot_index']
            await handle_place_headman_fn(ai_ws, room_id, ai_player['id'], rooms, manager, {
                'areaIndex': area_index,
                'slotIndex': slot_index
            })

            await handle_next_player_fn(ai_ws, room_id, ai_player['id'], rooms, manager, {})

            ai_player['aiState'] = 'idle'

    async def schedule_ai_settlement(self, room_id: str, websocket, rooms, manager, process_area_action_fn):
        """调度AI结算阶段行动（循环处理连续AI回合）"""
        from services.area import resolve_area_step
        log_info(f"[schedule_ai_settlement] starting settlement loop")
        while True:
            gs = self.rooms.get(room_id)
            if not gs or gs.get('phase') != 'settlement':
                log_info(f"[schedule_ai_settlement] exiting: phase={gs.get('phase') if gs else 'N/A'}")
                return

            settlement_state = gs.get('settlementState', {})
            waiting_player_id = settlement_state.get('waitingForPlayer')
            log_info(f"[schedule_ai_settlement] loop: waitingForPlayer={waiting_player_id}")

            if waiting_player_id is not None:
                # 有等待中的玩家，检查是否为AI
                players = gs.get('players', [])
                ai_player = next((p for p in players if p['id'] == waiting_player_id and p.get('isAI')), None)
                if not ai_player:
                    return  # 人类玩家，交给前端处理

                think_time = random.uniform(1.0, 3.0)
                ai_player['aiState'] = 'thinking'
                await asyncio.sleep(think_time)
                ai_player['aiState'] = 'acting'

                from services.ai_decision_engine import decide_settlement_action
                decision = decide_settlement_action(gs, ai_player, settlement_state)

                ai_ws = AIWebSocket()

                if decision['action_type'] == 'submitTributeChoice':
                    task_id = decision['payload'].get('taskId')
                    choice_type = settlement_state.get('choiceType') or gs.get('pendingTributeChoice', {}).get('choiceType')
                    gs['pendingTributeChoice'] = {
                        'playerId': ai_player['id'],
                        'taskId': task_id,
                        'choiceType': choice_type,
                        'options': gs.get('pendingTributeChoice', {}).get('options', [])
                    }

                result = await process_area_action_fn(gs, decision['action_type'], decision['payload'], manager, room_id, ai_ws)
                ai_player['aiState'] = 'idle'
                if result == 'error':
                    log_info(f"[schedule_ai_settlement] AI action '{decision['action_type']}' returned error, trying skip")
                    skip_result = await process_area_action_fn(gs, 'skip', {}, manager, room_id, ai_ws)
                    if skip_result == 'error':
                        log_info(f"[schedule_ai_settlement] skip also returned error, breaking loop")
                        return
                # 继续循环，检查下一个等待中的玩家
                continue
            else:
                # 没有等待中的玩家，尝试推进到下一个slot
                current_area = gs.get('currentArea', 0)
                log_info(f"[schedule_ai_settlement] no waiting player, resolving area {current_area}")
                result = await resolve_area_step(gs, current_area, manager, room_id)
                log_info(f"[schedule_ai_settlement] resolve_area_step result={result}")
                if result == 'auto_next':
                    if current_area + 1 >= len(AREAS):
                        from services.game import complete_settlement
                        await complete_settlement(room_id, gs, rooms, manager)
                        return  # 结算完成，退出循环
                    else:
                        gs['currentArea'] = current_area + 1
                        next_area_name = AREAS[current_area + 1]
                        from utils.helpers import make_settlement_state
                        gs['settlementState'] = make_settlement_state(next_area_name, 0, 0)
                        await manager.send_to_room(room_id, ServerEvents.SERVER_AREA_ACTION,
                            make_action_message(ServerAreaActionTypes.AREA_SETTLEMENT_START, {
                                'areaType': next_area_name, 'gameState': gs
                            }))
                        continue
                elif result == 'waiting_ui':
                    # 等待玩家操作或战斗开始
                    battle_queue = gs.get('battleQueue', [])
                    if battle_queue:
                        from controllers.battle_action_handler import arena_betting_state
                        has_active_betting = any(
                            arena_betting_state.get(f"{room_id}_{b.get('battleId', b.get('challengeSlot', ''))}", {}).get('started')
                            and not arena_betting_state.get(f"{room_id}_{b.get('battleId', b.get('challengeSlot', ''))}", {}).get('completed')
                            for b in battle_queue
                        )
                        if has_active_betting:
                            return  # 等待下注完成
                        await self._handle_tribute_lobster_selection(room_id, gs, manager)
                        # 龙虾选择处理后，如果战斗队列仍非空（等待RPG战斗），退出调度
                        if gs.get('battleQueue'):
                            return
                        continue
                    return
                else:
                    return

    async def schedule_ai_battle(self, room_id: str, websocket, rooms, manager, handle_battle_action_fn):
        """调度AI战斗阶段行动（循环处理连续AI回合）"""
        if self._in_battle_loop:
            return  # 重入保护
        self._in_battle_loop = True
        try:
            while True:
                gs = self.rooms.get(room_id)
                if not gs:
                    log_info(f"[schedule_ai_battle] exiting: no game state")
                    return

                battle = gs.get('current_battle')
                if not battle:
                    log_info(f"[schedule_ai_battle] exiting: no current_battle")
                    return

                # hp_draw阶段需要targetPlayerId，reward_choice阶段需要winnerId，其他阶段需要activePlayerId
                phase = battle.get('phase', '')
                if phase == 'hp_draw':
                    ai_player_id = battle.get('targetPlayerId')
                elif phase == 'reward_choice':
                    ai_player_id = battle.get('winnerId')
                else:
                    ai_player_id = battle.get('activePlayerId')
                if ai_player_id is None:
                    log_info(f"[schedule_ai_battle] exiting: no activePlayerId")
                    return

                ai_player = next((p for p in gs['players'] if p['id'] == ai_player_id and p.get('isAI')), None)
                if not ai_player:
                    log_info(f"[schedule_ai_battle] exiting: player {ai_player_id} is not AI")
                    return

                log_info(f"[schedule_ai_battle] AI {ai_player_id} acting, phase={battle.get('phase')}")

                think_time = random.uniform(0.5, 1.5)
                ai_player['aiState'] = 'thinking'
                await asyncio.sleep(think_time)
                ai_player['aiState'] = 'acting'

                from services.ai_decision_engine import decide_battle_action
                decision = decide_battle_action(gs, ai_player, battle)
                log_info(f"[schedule_ai_battle] decision: {decision}")

                from controllers.battle_action_handler import handle_rpg_battle_action
                ai_ws = AIWebSocket()
                await handle_rpg_battle_action(ai_ws, room_id, ai_player_id, rooms, manager, decision)
                ai_player['aiState'] = 'idle'
        finally:
            self._in_battle_loop = False

    async def check_and_trigger(self, room_id: str, websocket, rooms, manager,
                                 handle_place_headman_fn=None,
                                 handle_next_player_fn=None,
                                 process_area_action_fn=None,
                                 handle_battle_action_fn=None):
        """统一检测当前是否为AI轮次，自动触发对应阶段的AI行动（循环处理阶段切换）"""
        if self._in_check_trigger:
            return  # 重入保护
        self._in_check_trigger = True
        try:
            await self._check_and_trigger_impl(
                room_id, websocket, rooms, manager,
                handle_place_headman_fn, handle_next_player_fn,
                process_area_action_fn, handle_battle_action_fn)
        finally:
            self._in_check_trigger = False

    async def _check_and_trigger_impl(self, room_id: str, websocket, rooms, manager,
                                       handle_place_headman_fn, handle_next_player_fn,
                                       process_area_action_fn, handle_battle_action_fn):
        while True:
            gs = self.rooms.get(room_id)
            if not gs or gs.get('status') != 'playing':
                return

            phase = gs.get('phase', '')
            log_info(f"[check_and_trigger] phase={phase}")

            if phase == 'placement':
                if self.is_ai_turn(room_id) and handle_place_headman_fn and handle_next_player_fn:
                    log_info(f"[check_and_trigger] triggering placement AI")
                    await self.schedule_ai_placement(
                        room_id, websocket, rooms, manager,
                        handle_place_headman_fn, handle_next_player_fn)
                    # 放置循环可能切换到结算，重新检测
                    continue
                else:
                    return  # 人类回合，等待前端操作

            elif phase == 'settlement':
                # 先检查是否有活跃战斗需要AI操作
                battle = gs.get('current_battle')
                if battle:
                    # hp_draw阶段需要targetPlayerId，reward_choice阶段需要winnerId，其他阶段需要activePlayerId
                    battle_phase = battle.get('phase', '')
                    if battle_phase == 'hp_draw':
                        current_id = battle.get('targetPlayerId')
                    elif battle_phase == 'reward_choice':
                        current_id = battle.get('winnerId')
                    else:
                        current_id = battle.get('activePlayerId')
                    if current_id is not None:
                        player = next((p for p in gs['players'] if p['id'] == current_id and p.get('isAI')), None)
                        if player and handle_battle_action_fn:
                            log_info(f"[check_and_trigger] triggering battle AI during settlement")
                            await self.schedule_ai_battle(
                                room_id, websocket, rooms, manager, handle_battle_action_fn)
                            # 战斗已结束则继续处理结算流程，否则退出等待人类操作
                            if not self.rooms.get(room_id, {}).get('current_battle'):
                                continue
                            return
                    return  # 战斗进行中但不需要AI行动（等待人类操作）

                settlement_state = gs.get('settlementState', {})
                waiting_id = settlement_state.get('waitingForPlayer')
                log_info(f"[check_and_trigger] settlement: waitingForPlayer={waiting_id}")
                if waiting_id is not None:
                    player = next((p for p in gs['players'] if p['id'] == waiting_id and p.get('isAI')), None)
                    log_info(f"[check_and_trigger] waiting player isAI={player.get('isAI') if player else None}")
                    if player and process_area_action_fn:
                        log_info(f"[check_and_trigger] triggering settlement AI for player {waiting_id}")
                        await self.schedule_ai_settlement(
                            room_id, websocket, rooms, manager, process_area_action_fn)
                        # 结算循环可能完成并切换到新回合，重新检测
                        continue
                    else:
                        return  # 人类回合
                else:
                    # 没有等待的玩家，尝试推进区域
                    # 先检查是否有战斗队列需要处理（避免重复调用resolve_area_step）
                    battle_queue = gs.get('battleQueue', [])
                    if battle_queue:
                        await self._handle_tribute_lobster_selection(room_id, gs, manager)
                        if gs.get('current_battle'):
                            continue  # 战斗已开始
                        if gs.get('battleQueue'):
                            return  # 等待人类选龙虾/下注
                        continue  # 队列已清空
                    current_area = gs.get('currentArea', 0)
                    log_info(f"[check_and_trigger] no waiting player, resolving area {current_area}")
                    from services.area import resolve_area_step
                    result = await resolve_area_step(gs, current_area, manager, room_id)
                    log_info(f"[check_and_trigger] resolve_area_step result={result}")
                    if result == 'auto_next':
                        if current_area + 1 >= len(AREAS):
                            from services.game import complete_settlement
                            await complete_settlement(room_id, gs, rooms, manager)
                            continue
                        else:
                            gs['currentArea'] = current_area + 1
                            from utils.helpers import make_settlement_state
                            gs['settlementState'] = make_settlement_state(AREAS[current_area + 1], 0, 0)
                            continue
                    elif result == 'waiting_ui':
                        # 检查是否设置了等待玩家
                        ss = gs.get('settlementState', {})
                        wp = ss.get('waitingForPlayer')
                        if wp is not None:
                            continue  # 等待玩家，重新循环检测是否AI
                        # waitingForPlayer 仍为 None
                        # 检查是否有活跃战斗
                        battle = gs.get('current_battle')
                        if battle:
                            continue
                        # 检查是否有战斗队列（tribute挑战已创建但未开始）
                        battle_queue = gs.get('battleQueue', [])
                        if battle_queue:
                            # 为AI玩家选龙虾 + 判负处理
                            await self._handle_tribute_lobster_selection(room_id, gs, manager)
                            # 检查战斗是否已开始或队列是否已清空
                            if gs.get('current_battle'):
                                continue  # 战斗已开始，重新循环检测AI操作
                            if gs.get('battleQueue'):
                                return  # 仍有战斗队列但无法开始（等待人类选龙虾），停止循环
                            continue  # 队列已清空（判负），继续检测后续区域
                        # 检查是否有等待中的战斗Bonus选择
                        if gs.get('pendingBattleBonusChoices'):
                            return  # 等待玩家选择战斗Bonus
                        return
                    else:
                        return

            elif phase == 'battle':
                battle = gs.get('current_battle')
                if battle:
                    current_id = battle.get('activePlayerId')
                    if current_id is not None:
                        player = next((p for p in gs['players'] if p['id'] == current_id and p.get('isAI')), None)
                        if player and handle_battle_action_fn:
                            await self.schedule_ai_battle(
                                room_id, websocket, rooms, manager, handle_battle_action_fn)
                            continue
                return

            else:
                return
