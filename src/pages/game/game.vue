<template>
    <view class="game-container">
        <!-- 游戏头部 -->
        <view class="game-header">
            <view class="round-info">
                <text class="round-label">回合</text>
                <text class="round-number">{{ gameStore.currentRound }}/{{ gameStore.maxRounds }}</text>
            </view>
            <view class="phase-info">
                <text class="phase-label">{{ getPhaseText() }}</text>
            </view>
            <button class="next-btn" @click="handleNextPhase">下一阶段</button>
        </view>

        <!-- 放置阶段提示 -->
        <view v-if="isPlacementPhase" class="placement-banner">
            <view class="placement-info">
                <text class="placement-text">
                    {{ gameStore.isPlacementComplete ? '工放阶段结束' : `轮到 ${currentPlacementPlayerName} 放置里长` }}
                </text>
                <text v-if="!gameStore.isPlacementComplete" class="placement-hint">
                    点击空闲的行动格放置里长
                </text>
            </view>
        </view>

        <!-- 玩家栏 -->
        <view class="players-bar">
            <view v-for="(player, index) in gameStore.players" :key="player.id" :class="['player-item', {
                active: isCurrentPlacementPlayer(index),
                starting: player.isStartingPlayer
            }]" :style="getPlayerItemStyle(index)">
                <view class="player-badge" v-if="player.isStartingPlayer">起始</view>
                <text class="player-name">{{ player.name }}</text>
                <view class="player-stats">
                    <text class="stat">德:{{ player.de }}</text>
                    <text class="stat">望:{{ player.wang }}</text>
                    <text class="stat">金:{{ player.coins }}</text>
                    <text class="stat">里长:{{ player.liZhang }}</text>
                </view>
            </view>
        </view>

        <!-- 主游戏板 -->
        <view class="main-board">
            <!-- 捕虾区 -->
            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">捕虾区</text>
                    <text class="section-desc">放置里长获取捕虾机会</text>
                </view>
                <view class="area-slots">
                    <view v-for="i in 4" :key="i" :class="['slot', {
                        occupied: isSlotOccupied('shrimp_catching', i - 1),
                        disabled: !canPlaceOnSlot('shrimp_catching', i - 1)
                    }]" :style="getSlotStyle('shrimp_catching', i - 1)"
                          @click="handleSlotClick('shrimp_catching', i - 1)">
                        <view v-if="getSlotOccupantLabel('shrimp_catching', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('shrimp_catching', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getShrimpCatchingSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <!-- 海鲜市场 -->
            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">海鲜市场</text>
                    <text class="section-desc">放置里长进行买卖与雇佣</text>
                </view>
                <view class="area-slots">
                    <view v-for="i in 4" :key="i" :class="['slot', {
                        occupied: isSlotOccupied('seafood_market', i - 1),
                        disabled: !canPlaceOnSlot('seafood_market', i - 1)
                    }]" :style="getSlotStyle('seafood_market', i - 1)"
                          @click="handleSlotClick('seafood_market', i - 1)">
                        <view v-if="getSlotOccupantLabel('seafood_market', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('seafood_market', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getSeafoodMarketSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <!-- 养蛊区 -->
            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">养蛊区</text>
                    <text class="section-desc">放置里长培养龙虾</text>
                </view>
                <view class="area-slots">
                    <view v-for="i in 4" :key="i" :class="['slot', {
                        occupied: isSlotOccupied('breeding', i - 1),
                        disabled: !canPlaceOnSlot('breeding', i - 1)
                    }]" :style="getSlotStyle('breeding', i - 1)" @click="handleSlotClick('breeding', i - 1)">
                        <view v-if="getSlotOccupantLabel('breeding', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('breeding', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getBreedingSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <!-- 上供区 -->
            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">上供区</text>
                    <text class="section-desc">结交酒楼势力，争夺席位</text>
                </view>
                <view class="area-slots tribute-slots">
                    <view v-for="i in 6" :key="i" :class="['slot', {
                        occupied: isSlotOccupied('tribute', i - 1),
                        disabled: !canPlaceOnSlot('tribute', i - 1),
                        'challenge-slot': i > 3
                    }]" :style="getSlotStyle('tribute', i - 1)" @click="handleSlotClick('tribute', i - 1)">
                        <view v-if="getSlotOccupantLabel('tribute', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('tribute', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getTributeSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <!-- 闹市区 -->
            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">闹市区</text>
                    <text class="section-desc">放置里长执行闹市行动</text>
                </view>
                <view class="area-slots">
                    <view v-for="i in 3" :key="i" :class="['slot', {
                        occupied: isSlotOccupied('marketplace', i - 1),
                        disabled: !canPlaceOnSlot('marketplace', i - 1) || !isMarketplaceAvailable(i)
                    }]" :style="getSlotStyle('marketplace', i - 1)" @click="handleSlotClick('marketplace', i - 1)">
                        <view v-if="getSlotOccupantLabel('marketplace', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('marketplace', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getMarketplaceSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>
        </view>

        <!-- 当前玩家面板 -->
        <view class="current-player-panel" v-if="gameStore.currentPlayer">
            <view class="panel-header">
                <text class="panel-title">{{ gameStore.currentPlayer.name }}的回合</text>
                <text class="lizhang-count">里长: {{ gameStore.currentPlayer.liZhang }}</text>
            </view>
            <view class="panel-resources">
                <view class="resource-item">
                    <text class="resource-label">金币</text>
                    <text class="resource-value">{{ gameStore.currentPlayer.coins }}</text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">海草</text>
                    <text class="resource-value">{{ gameStore.currentPlayer.seaweed }}</text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">虾笼</text>
                    <text class="resource-value">{{ gameStore.currentPlayer.cages }}</text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">龙虾</text>
                    <text class="resource-value">{{ gameStore.currentPlayer.lobsters.length }}</text>
                </view>
            </view>
        </view>

        <!-- 日志面板 -->
        <view class="log-panel">
            <view class="log-header" @click="showLog = !showLog">
                <text class="log-title">游戏日志</text>
                <text class="log-toggle">{{ showLog ? '收起' : '展开' }}</text>
            </view>
            <view class="log-content" :class="{ expanded: showLog }">
                <view class="log-scroll">
                    <view v-for="(log, index) in gameStore.logs.slice().reverse()" :key="index"
                          :class="['log-item', log.type || 'info']">
                        <text class="log-text">{{ log.message }}</text>
                    </view>
                </view>
            </view>
        </view>

        <!-- =======================
             各类交互弹窗区域
        ======================== -->

        <!-- 斗龙虾热坐模式决斗弹窗（与养蛊区一致的长条滚动弹窗） -->
        <view class="modal-overlay" v-if="gameStore.pendingBattle">
            <view class="modal-content battle-modal">
                <view class="modal-header" style="background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);">
                    <view class="modal-title-group" style="align-items: center;">
                        <text class="modal-title" style="font-size: 1.25rem;">⚔️ 席位争夺战 ⚔️</text>
                        <text class="modal-subtitle text-white mt-1">
                            第 {{ gameStore.pendingBattle.challengerSlotIndex + 1 }} 号位挑战第
                            {{ gameStore.pendingBattle.defenderSlotIndex + 1 }} 号位
                        </text>
                    </view>
                </view>

                <!-- 内容区：允许滚动防遮挡 -->
                <view class="modal-body" v-if="battleP1 && battleP2" style="background: #f8fafc;">

                    <!-- 双方简要资源栏 (优化截断防挤压) -->
                    <view class="battle-vs-header">
                        <view class="vs-player p1">
                            <text class="vs-name" style="color: #2563eb;">攻: {{ battleP1.name }}</text>
                            <text class="vs-res">🌿{{ battleP1.seaweed }} 🪙{{ battleP1.coins }} 🎖{{ battleP1.de }}</text>
                        </view>
                        <text class="vs-badge" style="color: #94a3b8;">VS</text>
                        <view class="vs-player p2" style="align-items: flex-end;">
                            <text class="vs-name" style="color: #dc2626;">守: {{ battleP2.name }}</text>
                            <text class="vs-res">🎖{{ battleP2.de }} 🪙{{ battleP2.coins }} 🌿{{ battleP2.seaweed }}</text>
                        </view>
                    </view>

                    <!-- 选虾阶段 -->
                    <view v-if="battleState.phase === 'SELECT'" style="margin-top: 1rem;">
                        <text class="section-label" style="color: #ea580c; text-align: center;">
                            👉 请 {{ battleState.selectPhase === 1 ? battleP1.name : battleP2.name }} 挑选出战龙虾
                        </text>
                        <view class="lobster-grid" style="margin-top: 0.5rem; grid-template-columns: repeat(2, 1fr);">
                            <view v-for="(lobster, idx) in battleSelectableLobsters" :key="idx"
                                  class="lobster-card" :class="{ 'max-royal': isLobsterBanned(lobster) }"
                                  @click="selectBattleLobster(lobster)">
                                <text class="lobster-icon">🦞</text>
                                <text class="lobster-grade" style="font-weight: bold;">
                                    {{ getLobsterGradeName(lobster.grade) }} #{{ idx + 1 }}
                                </text>
                                <text class="lobster-title" v-if="lobster.title">{{ lobster.title.name }}</text>
                                <text class="tc-desc" style="text-align: center; margin-top: 0.5rem;">
                                    {{ getLobsterDesc(lobster) }}
                                </text>
                                <view v-if="isLobsterBanned(lobster)" class="max-grade-mask"
                                      style="background: #ef4444;">{{ lobster.hasFought ? '已参战' : '不可战' }}
                                </view>
                            </view>
                        </view>
                        <view v-if="battleSelectableLobsters.length === 0" class="empty-hint">该玩家没有可出战的龙虾！
                        </view>
                    </view>

                    <!-- 战斗阶段 -->
                    <view v-else-if="battleState.phase === 'BATTLE'" style="margin-top: 1rem;">
                        <!-- 对阵面板 -->
                        <view class="fighter-panels">
                            <view class="fighter-panel" :class="{'active-p1': battleState.currentTurn === 1}">
                                <text class="fp-owner" style="color: #2563eb;">攻方出战</text>
                                <text class="fp-name">{{ getLobsterGradeName(battleState.p1Fighter.grade) }}</text>
                                <text class="fp-title" v-if="battleState.p1Fighter.title">
                                    【{{ battleState.p1Fighter.title.name }}】
                                </text>
                                <text class="fp-status" :class="{'active-status': battleState.p1Started}">
                                    {{ battleState.p1Started ? '⚡处于兴奋(可移动)' : '💤等待兴奋(需≥6点)' }}
                                </text>
                            </view>
                            <view class="fighter-panel" :class="{'active-p2': battleState.currentTurn === 2}">
                                <text class="fp-owner" style="color: #dc2626;">守方出战</text>
                                <text class="fp-name">{{ getLobsterGradeName(battleState.p2Fighter.grade) }}</text>
                                <text class="fp-title" v-if="battleState.p2Fighter.title">
                                    【{{ battleState.p2Fighter.title.name }}】
                                </text>
                                <text class="fp-status" :class="{'active-status': battleState.p2Started}">
                                    {{ battleState.p2Started ? '⚡处于兴奋(可移动)' : '💤等待兴奋(需≥6点)' }}
                                </text>
                            </view>
                        </view>

                        <!-- 战斗棋盘 (脱离绝对定位控制，融入文档流) -->
                        <view class="board-track-container">
                            <view class="board-path">
                                <view class="board-midline"></view>
                                <text class="mid-text">中线(+1战功)</text>
                                <view class="board-dots">
                                    <view v-for="i in 9" :key="i-1" class="dot" :class="{'mid-dot': i-1===4}">{{
                                            i - 1
                                        }}
                                    </view>
                                </view>
                                <view class="chess-p1" :style="{ left: `calc(5% + ${(battleState.p1Pos / 8) * 90}%)` }">
                                    🦐
                                </view>
                                <view class="chess-p2" :style="{ left: `calc(5% + ${(battleState.p2Pos / 8) * 90}%)` }">
                                    🦞
                                </view>
                            </view>
                        </view>

                        <!-- 行动与结果面板 -->
                        <view class="battle-action-box mt-4">
                            <text class="turn-indicator"
                                  :style="{color: battleState.currentTurn === 1 ? '#2563eb' : '#dc2626'}">
                                轮到 {{ battleState.currentTurn === 1 ? battleP1.name : battleP2.name }} 行动
                            </text>

                            <!-- 超大骰子结果框 -->
                            <view class="dice-result-panel" v-if="battleState.lastRollDetail">
                                <text class="dr-header">🎲 掷骰结果 🎲</text>
                                <view class="dr-math">
                                    <text class="dr-base">{{ battleState.lastRollDetail.base }}</text>
                                    <text class="dr-bonus" v-if="battleState.lastRollDetail.bonus > 0"> +
                                        草{{ battleState.lastRollDetail.bonus }}
                                    </text>
                                    <text class="dr-equals"> =</text>
                                    <text class="dr-total">{{ battleState.lastRollDetail.total }}</text>
                                </view>
                                <text class="dr-desc">{{ getMovementDesc(battleState.lastRollDetail) }}</text>
                            </view>

                            <!-- 优化：直观清晰的海草单选按钮，最多限用1棵 -->
                            <view class="grass-toggle-container">
                                <text class="slider-label">海草加成:</text>
                                <view class="grass-options">
                                    <text class="grass-opt" :class="{active: battleState.grassToUse === 0}"
                                          @click="setBattleGrass(0)">不使用
                                    </text>
                                    <text class="grass-opt"
                                          :class="{active: battleState.grassToUse === 1, disabled: battleMaxGrassAllowed < 1}"
                                          @click="setBattleGrass(1)">用 1 株
                                    </text>
                                </view>
                            </view>

                            <text v-if="battleMaxGrassAllowed === 0" class="error-hint block text-center mb-2">⚠️
                                {{ battleDisableGrassReason }}
                            </text>
                            <text v-else class="text-xs text-center text-gray-500 block mb-3">
                                预计点数额外加成:
                                <text style="color: #10b981; font-weight: bold;">+{{ battleExpectedGrassBonus }}</text>
                            </text>

                            <button class="btn w-full roll-action-btn"
                                    :class="battleState.currentTurn === 1 ? 'btn-blue' : 'btn-red'"
                                    @click="doBattleRollDice">
                                🎲 掷出骰子
                            </button>
                        </view>

                        <!-- 战斗日志 (完全修复纯文本渲染防吞字) -->
                        <view class="battle-log-list mt-4">
                            <text class="section-label mb-2" style="font-size: 0.9rem;">战况记录</text>
                            <scroll-view scroll-y class="b-log-scroll" :scroll-top="battleLogScrollTop">
                                <view v-for="(log, idx) in battleState.logs" :key="idx" class="b-log-line">
                                    <text class="log-time">[{{ log.time }}]</text>
                                    <text class="log-msg" :style="{ color: log.color, fontWeight: log.weight }">
                                        {{ log.text }}
                                    </text>
                                </view>
                            </scroll-view>
                        </view>
                    </view>

                    <!-- 结算阶段 (已修复按钮排版挤压，全宽换行) -->
                    <view v-if="battleState.phase === 'RESULT'" style="margin-top: 1.5rem; text-align: center;">
                        <text class="result-title block mb-2" style="font-size: 1.8rem; font-weight: 900;"
                              :style="{color: battleState.winner === 1 ? '#2563eb' : (battleState.winner === 2 ? '#dc2626' : '#475569')}">
                            {{
                                battleState.winner === null ? '平局/异常' : `${battleState.winner === 1 ? battleP1.name : battleP2.name} 获胜！`
                            }}
                        </text>
                        <text class="result-desc block text-gray-600 mb-6 font-bold">
                            {{ battleState.winReason || '恭喜赢下这场惨烈的对决！' }}
                        </text>

                        <view v-if="battleState.winner !== null" class="reward-options flex flex-col gap-3">
                            <text class="text-sm font-bold text-gray-700 block text-center mb-2">请选择决斗战利品：
                            </text>
                            <button class="btn btn-primary w-full mb-3"
                                    style="background: linear-gradient(135deg, #a855f7, #8b5cf6); border: none; padding: 12px; border-radius: 8px; color: white;"
                                    @click="claimBattleReward('UPGRADE')">✨ 参战龙虾升 1 阶 (最高皇家)
                            </button>
                            <button class="btn btn-warning w-full"
                                    style="background: linear-gradient(135deg, #f59e0b, #eab308); border: none; padding: 12px; border-radius: 8px; color: white;"
                                    @click="claimBattleReward('COIN')">🪙 拿取 3 枚金币
                            </button>
                        </view>
                        <button v-else class="btn btn-secondary w-full mt-4" @click="finishBattle">结束并处理席位
                        </button>
                    </view>
                </view>
            </view>
        </view>

        <!-- 养蛊区结算弹窗 -->
        <view class="modal-overlay" v-if="gameStore.pendingBreeding">
            <view class="modal-content breeding-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ currentPendingBreeding.player.name }} 的培养行动</text>
                        <text class="modal-subtitle">剩余次数:
                            <text class="highlight">{{ currentPendingBreeding.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <view class="modal-body">
                    <!-- 第一步：选择龙虾 -->
                    <view v-if="breedingState.lobsterIndex === -1" class="lobster-selection">
                        <text class="section-label">请选择要进行培养的龙虾：</text>
                        <view class="lobster-grid">
                            <view v-for="(lobster, index) in currentPendingBreeding.player.lobsters" :key="lobster.id"
                                  class="lobster-card" :class="{'max-royal': lobster.grade === LOBSTER_GRADES.ROYAL}"
                                  @click="lobster.grade !== LOBSTER_GRADES.ROYAL && selectLobsterForBreeding(index)">
                                <text class="lobster-icon">🦞</text>
                                <text class="lobster-grade">{{ getLobsterGradeName(lobster.grade) }}</text>
                                <text class="lobster-title" v-if="lobster.title">{{ lobster.title.name }}</text>
                                <view v-if="lobster.grade === LOBSTER_GRADES.ROYAL" class="max-grade-mask">已满级</view>
                            </view>
                        </view>
                        <view v-if="currentPendingBreeding.player.lobsters.length === 0" class="empty-hint">
                            您目前没有任何龙虾。
                        </view>
                    </view>

                    <!-- 第二步：选择升级配置 -->
                    <view v-else class="breeding-action-panel">
                        <view class="upgrade-path">
                            <view class="grade-box current">
                                <text>当前</text>
                                <text class="val">{{ getLobsterGradeName(targetLobster.grade) }}</text>
                            </view>
                            <text class="arrow">➔</text>
                            <view class="grade-box target">
                                <text>目标</text>
                                <text class="val highlight">{{ getLobsterGradeName(projectedGrade) }}</text>
                            </view>
                        </view>

                        <view class="options-group">
                            <view class="checkbox-wrapper" @click="toggleSeaweed"
                                  :class="{disabled: (currentPendingBreeding.player.seaweed < 1 && !breedingState.useSeaweed) || !isSeaweedUseful}">
                                <view class="custom-checkbox" :class="{checked: breedingState.useSeaweed}"></view>
                                <text class="checkbox-text">消耗 1 海草 额外升一品 (拥有:
                                    {{ currentPendingBreeding.player.seaweed }})
                                </text>
                            </view>
                        </view>

                        <!-- 突破至皇家时的附加消耗要求 -->
                        <view v-if="isUpgradingToRoyal" class="royal-requirements animate-fade-in">
                            <text class="req-title">突破至皇家级需支付额外费用：</text>
                            <view class="cost-options">
                                <button class="cost-btn" :class="{active: breedingState.royalCostType === 'cage'}"
                                        :disabled="currentPendingBreeding.player.cages < 1"
                                        @click="breedingState.royalCostType = 'cage'">
                                    🦞 1 虾笼 (拥有: {{ currentPendingBreeding.player.cages }})
                                </button>
                                <button class="cost-btn" :class="{active: breedingState.royalCostType === 'coin'}"
                                        :disabled="currentPendingBreeding.player.coins < 3"
                                        @click="breedingState.royalCostType = 'coin'">
                                    🪙 3 金币 (拥有: {{ currentPendingBreeding.player.coins }})
                                </button>
                            </view>

                            <!-- 升级皇家额外奖励选择 -->
                            <view class="req-title" style="margin-top: 1rem;">请选择升级皇家奖励：</view>
                            <view class="reward-options">
                                <view class="custom-radio-wrap"
                                      :class="{'active': breedingState.royalRewardType === 'de'}"
                                      @click="breedingState.royalRewardType = 'de'">
                                    <view class="custom-radio"
                                          :class="{'checked': breedingState.royalRewardType === 'de'}"></view>
                                    获得 1 德
                                </view>
                                <view class="custom-radio-wrap"
                                      :class="{'active': breedingState.royalRewardType === 'wang'}"
                                      @click="breedingState.royalRewardType = 'wang'">
                                    <view class="custom-radio"
                                          :class="{'checked': breedingState.royalRewardType === 'wang'}"></view>
                                    获得 1 望
                                </view>
                            </view>

                            <!-- 如果本回合还有剩余称号卡，玩家升到皇家必须强制获取 -->
                            <view v-if="gameStore.gameTitleCards.length > 0" class="title-selection"
                                  style="margin-top: 1rem;">
                                <text class="req-title">请挑选一个霸气称号：</text>
                                <view class="title-cards">
                                    <view v-for="card in gameStore.gameTitleCards" :key="card.id"
                                          class="title-card"
                                          :class="{active: breedingState.selectedTitleId === card.id}"
                                          @click="breedingState.selectedTitleId = card.id">
                                        {{ card.name }}
                                    </view>
                                </view>
                            </view>
                        </view>

                        <view class="modal-actions">
                            <button class="btn btn-ghost" @click="cancelBreedingAction">返回重选</button>
                            <button class="btn btn-primary" :disabled="!canConfirmBreeding"
                                    @click="confirmBreedingAction">确认培养
                            </button>
                        </view>
                    </view>
                </view>

                <view class="modal-footer" v-if="breedingState.lobsterIndex === -1">
                    <button class="btn btn-secondary w-full" @click="finishBreeding">放弃剩余次数并结束</button>
                </view>
            </view>
        </view>

        <!-- 闹市区结算弹窗 -->
        <view class="modal-overlay" v-if="gameStore.pendingMarketplace">
            <view class="modal-content marketplace-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ currentPendingMarketplace.player.name }} 的闹市行动</text>
                        <text class="modal-subtitle">请选择本回合尚未被执行的一张闹市卡</text>
                    </view>
                </view>

                <view class="modal-body">
                    <!-- 第一步：选择卡牌 -->
                    <view class="marketplace-cards">
                        <view v-for="card in gameStore.gameMarketplaceCards" :key="card.id"
                              class="mp-card"
                              :class="{ 'used': card.usedThisRound, 'selected': marketplaceState.selectedCard?.id === card.id }"
                              @click="selectMarketplaceCard(card)">
                            <text class="mp-card-name">{{ card.name }}</text>
                            <text class="mp-card-desc">{{ card.description }}</text>
                            <view v-if="card.usedThisRound" class="used-mask">本回合已被使用</view>
                        </view>
                    </view>

                    <!-- 第二步：展示对应选项 -->
                    <view v-if="marketplaceState.selectedCard && !marketplaceState.selectedCard.auto && marketplaceState.selectedCard.action?.type === 'exchange'"
                          class="mp-options-panel animate-fade-in">
                        <text class="section-label">请选择执行方案：</text>
                        <view class="mp-options">
                            <view v-for="(opt, idx) in (marketplaceState.selectedCard.action?.options || [])" :key="idx"
                                  class="mp-option-btn"
                                  :class="{ 'active': marketplaceState.selectedOptionIndex === idx }"
                                  @click="marketplaceState.selectedOptionIndex = idx">
                                <view class="custom-radio"
                                      :class="{ 'checked': marketplaceState.selectedOptionIndex === idx }"></view>
                                <!-- 运用通用格式化函数展示转换文本 -->
                                <text class="option-text">{{ formatOptionText(opt) }}</text>
                            </view>
                        </view>
                        <text v-if="!canConfirmMarketplace" class="error-hint">资源不足，无法执行该方案</text>
                    </view>
                </view>

                <view class="modal-footer">
                    <view class="modal-actions">
                        <button class="btn btn-ghost" @click="skipMarketplaceAction">放弃行动</button>
                        <button class="btn btn-primary"
                                :disabled="!marketplaceState.selectedCard || !canConfirmMarketplace"
                                @click="confirmMarketplaceAction">确认执行
                        </button>
                    </view>
                </view>
            </view>
        </view>

        <!-- 海鲜市场结算弹窗 -->
        <view class="modal-overlay" v-if="gameStore.pendingSeafoodMarket">
            <view class="modal-content seafood-market-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ currentPendingSeafoodMarket.player.name }} 的市场交易</text>
                        <text class="modal-subtitle">剩余行动次数:
                            <text class="highlight">{{ currentPendingSeafoodMarket.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <!-- 市场摊位与动态物价展示 -->
                <view class="market-display-board">
                    <view class="market-stalls">
                        <!-- 摊位1 -->
                        <view class="stall stall-1">
                            <view class="stall-label">一号摊</view>
                            <view class="stall-spaces">
                                <view v-for="i in 3" :key="'s1'+i" class="stall-space"
                                      :class="{filled: isSpaceFilled(i - 1)}"></view>
                            </view>
                        </view>
                        <!-- 摊位2 -->
                        <view class="stall stall-2">
                            <view class="stall-label">二号摊</view>
                            <view class="stall-spaces">
                                <view v-for="i in 2" :key="'s2'+i" class="stall-space"
                                      :class="{filled: isSpaceFilled(3 + i - 1)}"></view>
                            </view>
                        </view>
                        <!-- 摊位3 -->
                        <view class="stall stall-3">
                            <view class="stall-label">三号摊</view>
                            <view class="stall-spaces">
                                <view v-for="i in 3" :key="'s3'+i" class="stall-space"
                                      :class="{filled: isSpaceFilled(5 + i - 1)}"></view>
                            </view>
                        </view>
                    </view>
                    <view class="market-prices">
                        <text class="price-title">当前流通物价</text>
                        <view class="price-tags">
                            <text>龙虾: {{ currentMarketPrices.lobster }}金</text>
                            <text>虾笼: {{ currentMarketPrices.cage }}金</text>
                            <text>海草x1: {{ currentMarketPrices.seaweed1 }}金</text>
                            <text>海草x3: {{ currentMarketPrices.seaweed3 }}金</text>
                        </view>
                    </view>
                </view>

                <!-- 切换面板：交易 vs 雇佣 -->
                <view class="modal-tabs">
                    <view class="tab-item" :class="{active: smTab === 'trade'}" @click="smTab = 'trade'">资源买卖</view>
                    <view class="tab-item" :class="{active: smTab === 'hire'}" @click="smTab = 'hire'">雇佣里长</view>
                </view>

                <view class="modal-body" style="padding-top: 0;">
                    <!-- 交易面板 -->
                    <view v-if="smTab === 'trade'" class="trade-grid animate-fade-in">
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('buy_lobster')"
                                    :disabled="gameStore.seafoodMarketLobsters === 0 || currentPendingSeafoodMarket.player.coins < currentMarketPrices.lobster">
                                买入龙虾 (-{{ currentMarketPrices.lobster }}金)
                            </button>
                            <button class="btn btn-outline" @click="doSeafoodTrade('sell_lobster')"
                                    :disabled="gameStore.seafoodMarketLobsters === 8 || currentPendingSeafoodMarket.player.lobsters.length === 0">
                                卖出龙虾 (+{{ currentMarketPrices.lobster }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('buy_cage')"
                                    :disabled="currentPendingSeafoodMarket.player.coins < currentMarketPrices.cage">买入虾笼
                                (-{{ currentMarketPrices.cage }}金)
                            </button>
                            <button class="btn btn-outline" @click="doSeafoodTrade('sell_cage')"
                                    :disabled="currentPendingSeafoodMarket.player.cages === 0">卖出虾笼
                                (+{{ currentMarketPrices.cage }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('buy_seaweed1')"
                                    :disabled="currentPendingSeafoodMarket.player.coins < currentMarketPrices.seaweed1">
                                买1草 (-{{ currentMarketPrices.seaweed1 }}金)
                            </button>
                            <button class="btn btn-outline" @click="doSeafoodTrade('sell_seaweed1')"
                                    :disabled="currentPendingSeafoodMarket.player.seaweed < 1">卖1草
                                (+{{ currentMarketPrices.seaweed1 }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('buy_seaweed3')"
                                    :disabled="currentPendingSeafoodMarket.player.coins < currentMarketPrices.seaweed3">
                                买3草 (-{{ currentMarketPrices.seaweed3 }}金)
                            </button>
                            <button class="btn btn-outline" @click="doSeafoodTrade('sell_seaweed3')"
                                    :disabled="currentPendingSeafoodMarket.player.seaweed < 3">卖3草
                                (+{{ currentMarketPrices.seaweed3 }}金)
                            </button>
                        </view>
                    </view>

                    <!-- 雇佣里长面板 -->
                    <view v-if="smTab === 'hire'" class="hire-grid animate-fade-in">
                        <view class="hire-info">雇佣价格：固定 6 金币/名 (每人最多雇佣2名)</view>
                        <view class="slots-container">
                            <view v-for="(slot, idx) in HIRE_LIZHANG_SLOTS" :key="idx"
                                  class="hire-slot"
                                  :class="{ 'locked': gameStore.currentRound < slot.availableFrom, 'hired': gameStore.hiredLiZhangSlots[idx] !== null }"
                                  @click="doSeafoodHire(idx)">
                                <view class="slot-header">{{ idx + 1 }}号位</view>
                                <text class="slot-req" v-if="gameStore.currentRound < slot.availableFrom">
                                    第{{ slot.availableFrom }}回合开
                                </text>
                                <text class="slot-rew" v-else>送: {{ formatHireReward(slot.reward) }}</text>

                                <view class="status-mask" v-if="gameStore.hiredLiZhangSlots[idx] !== null">
                                    <text v-if="gameStore.hiredLiZhangSlots[idx] === currentPendingSeafoodMarket.player.id">
                                        已归你
                                    </text>
                                    <text v-else>已被占</text>
                                </view>
                            </view>
                        </view>
                        <text v-if="!canHireAny" class="error-hint">无法雇佣 (金币不足 / 达到上限 / 暂未解锁)</text>
                    </view>
                </view>

                <view class="modal-footer">
                    <button class="btn btn-secondary w-full" @click="skipSeafoodMarketAction">放弃剩余次数并结束
                    </button>
                </view>
            </view>
        </view>

        <!-- 上供区结算弹窗 -->
        <view class="modal-overlay" v-if="gameStore.pendingTribute">
            <view class="modal-content tribute-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ currentPendingTribute.player.name }} 的上供行动</text>
                        <text class="modal-subtitle">请选择一家酒楼并支付资源，或者选择裸交</text>
                    </view>
                </view>

                <!-- 常规上供卡列表面板 -->
                <view class="modal-body" v-if="!tributeState.isNakedMode">
                    <view class="taverns-list">
                        <view v-for="tavern in gameStore.taverns" :key="tavern.id" class="tavern-box">
                            <view class="tavern-header">
                                <text class="tavern-name">🏮 {{ tavern.name }}</text>
                                <text class="tavern-status"
                                      v-if="tavern.occupants.includes(currentPendingTribute.player.id)">已占席位
                                </text>
                            </view>

                            <view v-if="tavern.cards.length === 0" class="empty-hint">上供卡已被抢空</view>

                            <view class="tribute-cards">
                                <view v-for="card in tavern.cards" :key="card.id" class="tribute-card">
                                    <text class="tc-name">{{ card.name }}</text>
                                    <text class="tc-desc">{{ card.effectDesc }}</text>
                                    <view class="tc-req">需求：{{ formatTributeReq(card.requirements) }}</view>
                                    <view class="tc-rew">奖励：{{ formatTributeRew(card.reward) }}</view>

                                    <button class="btn btn-primary btn-sm mt-2"
                                            :disabled="!checkTributeReq(card.requirements, currentPendingTribute.player) || tavern.occupants.includes(currentPendingTribute.player.id)"
                                            @click="confirmTributeCard(tavern.id, card.id)">
                                        缴纳上供
                                    </button>
                                </view>
                            </view>
                        </view>
                    </view>
                </view>

                <!-- 裸交模式面板 -->
                <view class="modal-body naked-mode-panel animate-fade-in" v-else>
                    <view class="naked-intro">
                        <text class="warn-text">🔥 裸交模式 🔥</text>
                        <text class="sub-text">
                            如果你无法满足任何酒楼的卡牌要求，你可以选择献祭一只【三品及以上】的龙虾强行上供并抢夺一家酒楼的席位！
                        </text>
                    </view>

                    <view class="section-label">1. 请选择要强行献祭的龙虾：</view>
                    <view class="lobster-grid">
                        <view v-for="(lobster, index) in getValidNakedLobsters(currentPendingTribute.player)"
                              :key="lobster.id"
                              class="lobster-card"
                              :class="{'selected': tributeState.nakedLobsterIndex === lobster.originalIndex}"
                              @click="tributeState.nakedLobsterIndex = lobster.originalIndex">
                            <text class="lobster-icon">🦞</text>
                            <text class="lobster-grade">{{ getLobsterGradeName(lobster.grade) }}</text>
                            <text class="lobster-title" v-if="lobster.title">{{ lobster.title.name }}</text>
                        </view>
                    </view>
                    <view v-if="getValidNakedLobsters(currentPendingTribute.player).length === 0"
                          class="error-hint mt-2">
                        你连一只三品以上的龙虾都没有，怎么好意思裸交？
                    </view>

                    <view class="section-label mt-4">2. 请选择你要抢占席位的酒楼：</view>
                    <view class="tavern-select-grid">
                        <view v-for="t in gameStore.taverns" :key="t.id"
                              class="tavern-select-btn"
                              :class="{ 'active': tributeState.nakedTavernId === t.id, 'disabled': t.occupants.includes(currentPendingTribute.player.id) }"
                              @click="!t.occupants.includes(currentPendingTribute.player.id) && (tributeState.nakedTavernId = t.id)">
                            <text class="ts-name">{{ t.name }}</text>
                            <text class="ts-status">席位: {{ t.occupants.length }}/4</text>
                            <text v-if="t.occupants.includes(currentPendingTribute.player.id)" class="ts-lock">已占
                            </text>
                        </view>
                    </view>

                    <view class="section-label mt-4">3. 请选择保底奖励：</view>
                    <view class="reward-options" style="flex-direction: row;">
                        <view class="custom-radio-wrap" :class="{'active': tributeState.nakedRewardType === 'de'}"
                              @click="tributeState.nakedRewardType = 'de'">
                            <view class="custom-radio"
                                  :class="{'checked': tributeState.nakedRewardType === 'de'}"></view>
                            获得 1 德
                        </view>
                        <view class="custom-radio-wrap" :class="{'active': tributeState.nakedRewardType === 'wang'}"
                              @click="tributeState.nakedRewardType = 'wang'">
                            <view class="custom-radio"
                                  :class="{'checked': tributeState.nakedRewardType === 'wang'}"></view>
                            获得 1 望
                        </view>
                    </view>
                </view>

                <view class="modal-footer">
                    <view class="modal-actions" v-if="!tributeState.isNakedMode">
                        <button class="btn btn-ghost" @click="tributeState.isNakedMode = true">强行裸交</button>
                        <button class="btn btn-secondary" @click="skipTributeAction">放弃上供</button>
                    </view>
                    <view class="modal-actions" v-else>
                        <button class="btn btn-ghost" @click="tributeState.isNakedMode = false">返回卡牌列表</button>
                        <button class="btn btn-warning"
                                :disabled="tributeState.nakedLobsterIndex === -1 || tributeState.nakedTavernId === ''"
                                @click="confirmNakedTribute">确认献祭并抢席位
                        </button>
                    </view>
                </view>
            </view>
        </view>

    </view>
</template>

<script setup>
import {ref, computed, reactive, watch, nextTick} from 'vue'
import { useGameStore, GAME_PHASES, LOBSTER_GRADES } from '@stores/game.js'
import { DEFAULT_SLOT_STYLE, getOccupiedSlotStyle, PLAYER_COLORS } from '@utils/slotConstants.js'
import { getLobsterGradeName, getNextLobsterGrade } from '@utils/gameUtils.js'
import {HIRE_LIZHANG_SLOTS, getMarketPrices} from '@utils/seafoodMarketUtils.js'
import {TRIBUTE_SLOTS} from '@utils/tributeUtils.js'

const gameStore = useGameStore()
const showLog = ref(false)

// ==========================================
// 【终极修正核心】斗龙虾战斗机制 (解决记录展示、海草使用上限、首轮顺位争夺及等待移动机制)
// ==========================================
const battleState = reactive({
    phase: 'SELECT', selectPhase: 1, currentTurn: 1, winner: null, winReason: '',
    p1Fighter: null, p2Fighter: null, p1Pos: 0, p2Pos: 8, p1Started: false, p2Started: false,
    p1CrossedMid: false, p2CrossedMid: false, grassToUse: 0, logs: [], lastRollDetail: null,

    // 【新增核心属性】：用于控制回合掷骰机制
    battleCyclePhase: false,
    p1StartRoll: 0,
    p2StartRoll: 0
})
const battleLogScrollTop = ref(0)
const battleP1 = computed(() => gameStore.pendingBattle?.challenger)
const battleP2 = computed(() => gameStore.pendingBattle?.defender)

const getLevelNum = (grade) => {
    if (grade === LOBSTER_GRADES.NORMAL) return 0;
    if (grade === LOBSTER_GRADES.GRADE3) return 1;
    if (grade === LOBSTER_GRADES.GRADE2) return 2;
    if (grade === LOBSTER_GRADES.GRADE1) return 3;
    if (grade === LOBSTER_GRADES.ROYAL) return 4;
    return 0;
}

const getRankColor = (grade) => {
    const map = {
        0: 'text-gray-500',
        1: 'text-green-600',
        2: 'text-blue-600',
        3: 'text-purple-600',
        4: 'text-orange-500'
    }
    return map[getLevelNum(grade)] || 'text-gray-800'
}

const getLobsterDesc = (lobster) => {
    const lvl = getLevelNum(lobster.grade)
    let desc = `阶级: ${getLobsterGradeName(lobster.grade)}`
    if (lvl === 1) desc += " | 6面骰，禁草。"
    if (lvl === 2) desc += " | 8面骰，1草+1点。"
    if (lvl >= 3) desc += " | 10面骰，1草+2点。"
    return desc
}

// 检查该龙虾在本回合是否已出战
const isLobsterBanned = (lobster) => getLevelNum(lobster.grade) === 0 || lobster.hasFought

const battleSelectableLobsters = computed(() => battleState.selectPhase === 1 ? battleP1.value?.lobsters || [] : battleP2.value?.lobsters || [])
const battleCurrentFighter = computed(() => battleState.currentTurn === 1 ? battleState.p1Fighter : battleState.p2Fighter)
const battleOpponentFighter = computed(() => battleState.currentTurn === 1 ? battleState.p2Fighter : battleState.p1Fighter)
const battleCurrentPlayer = computed(() => battleState.currentTurn === 1 ? battleP1.value : battleP2.value)

// 【规则修复】：最高只允许使用 1 株海草
const battleMaxGrassAllowed = computed(() => {
    if (!battleCurrentFighter.value || !battleOpponentFighter.value) return 0
    if (getLevelNum(battleCurrentFighter.value.grade) === 1) return 0
    if (battleOpponentFighter.value.title?.name === '铁甲将军') return 0
    return Math.min(1, battleCurrentPlayer.value.seaweed)
})

const battleDisableGrassReason = computed(() => {
    if (getLevelNum(battleCurrentFighter.value?.grade) === 1) return "3品战虾无法使用海草加成！"
    if (battleOpponentFighter.value?.title?.name === '铁甲将军') return "对手称号【铁甲将军】威压，禁止使用海草！"
    if (battleCurrentPlayer.value?.seaweed <= 0) return "海草数量不足！"
    return ""
})

const battleGrassBonusPerUnit = computed(() => {
    if (!battleCurrentFighter.value) return 0
    const lvl = getLevelNum(battleCurrentFighter.value.grade)
    let base = 0
    if (lvl === 2) base = 1
    else if (lvl >= 3) base = 2
    return base
})

const battleExpectedGrassBonus = computed(() => {
    let bonus = battleState.grassToUse * battleGrassBonusPerUnit.value
    if (battleState.grassToUse > 0 && battleCurrentFighter.value?.title?.name === '闪电钳') bonus += 1
    return bonus
})

// 【UI修复】：单选按钮控制海草数量
const setBattleGrass = (amount) => {
    if (amount > battleMaxGrassAllowed.value) return;
    battleState.grassToUse = amount;
}

// 监听挂起事件
watch(() => gameStore.pendingBattle, (newVal) => {
    if (newVal) {
        Object.assign(battleState, {
            phase: 'SELECT', selectPhase: 1, currentTurn: 1, winner: null, winReason: '',
            p1Fighter: null, p2Fighter: null, p1Pos: 0, p2Pos: 8, p1Started: false, p2Started: false,
            p1CrossedMid: false, p2CrossedMid: false, grassToUse: 0, logs: [], lastRollDetail: null,
            battleCyclePhase: false, p1StartRoll: 0, p2StartRoll: 0
        })

        // 防卡死判定
        const p1CanFight = newVal.challenger.lobsters.some(l => !isLobsterBanned(l))
        const p2CanFight = newVal.defender.lobsters.some(l => !isLobsterBanned(l))
        if (!p1CanFight && !p2CanFight) {
            battleState.winReason = "双方均拿不出战虾，此战平局！"
            battleState.phase = 'RESULT'
        } else if (!p1CanFight) {
            battleState.winReason = `${battleP1.value.name} 拿不出战虾不战而退，${battleP2.value.name} 直接获胜！`
            battleState.winner = 2;
            battleState.phase = 'RESULT'
        } else if (!p2CanFight) {
            battleState.winReason = `${battleP2.value.name} 无虾可应战弃权，${battleP1.value.name} 直接获胜！`
            battleState.winner = 1;
            battleState.phase = 'RESULT'
        }
    }
})

// 【UI修复】：完全移除 v-html 解决微信小程序战况不显示的问题
const addBattleLog = (text, type = 'normal') => {
    const time = new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric'
    })
    let color = '#334155'
    let weight = 'normal'
    if (type === 'p1') {
        color = '#2563eb';
        weight = 'bold'
    }
    if (type === 'p2') {
        color = '#dc2626';
        weight = 'bold'
    }
    if (type === 'system') {
        color = '#f59e0b';
        weight = 'bold'
    }
    if (type === 'critical') {
        color = '#9333ea';
        weight = 'bold'
    }

    const cleanText = text.replace(/<\/?b>/g, '');

    battleState.logs.push({time, text: cleanText, color, weight})
    nextTick(() => {
        battleLogScrollTop.value += 9999
    })
}

const selectBattleLobster = (lobster) => {
    if (isLobsterBanned(lobster)) return
    if (battleState.selectPhase === 1) {
        battleState.p1Fighter = lobster;
        lobster.hasFought = true;
        battleState.selectPhase = 2
    } else {
        battleState.p2Fighter = lobster;
        lobster.hasFought = true;
        startBattleMode()
    }
}

// 【规则修复】：初始化对决状态与顺位争夺
const startBattleMode = () => {
    battleState.phase = 'BATTLE';
    battleState.p1Pos = 0;
    battleState.p2Pos = 8

    battleState.p1Started = battleState.p1Fighter.title?.skill?.startStarted || battleState.p1Fighter.title?.name === '急先锋龙虾'
    battleState.p2Started = battleState.p2Fighter.title?.skill?.startStarted || battleState.p2Fighter.title?.name === '急先锋龙虾'

    battleState.p1StartRoll = battleState.p1Started ? 999 : 0;
    battleState.p2StartRoll = battleState.p2Started ? 999 : 0;

    battleState.logs = [];
    battleState.lastRollDetail = null;

    if (battleState.p1Started || battleState.p2Started) {
        // 如果有急先锋，直接跳过起步阶段
        battleState.battleCyclePhase = false;
        if (battleState.p1Started && battleState.p2Started) {
            battleState.currentTurn = 2; // 都起步则守方先手
        } else if (battleState.p1Started) {
            battleState.currentTurn = 1;
        } else {
            battleState.currentTurn = 2;
        }
    } else {
        // 都没有起步，进入抢夺顺位阶段，防守方（P2）先掷
        battleState.battleCyclePhase = true;
        battleState.currentTurn = 2;
    }

    addBattleLog(`⚔️ 决斗正式开始！`, 'system')
    if (battleState.p1Started) addBattleLog(`[称号触发] 攻方急先锋，默认已起步！`, 'p1')
    if (battleState.p2Started) addBattleLog(`[称号触发] 守方急先锋，默认已起步！`, 'p2')
    addBattleLog(`--- 轮到 ${battleState.currentTurn === 1 ? '攻方: ' + battleP1.value.name : '守方: ' + battleP2.value.name} 行动 ---`, 'system')
}

const getDiceFaces = (fighter) => {
    if (fighter.title?.skill?.getDiceSides) return fighter.title.skill.getDiceSides();
    if (fighter.title?.skill?.diceSides) return fighter.title.skill.diceSides;
    if (fighter.title?.name === '红头紫') return 12;
    if (fighter.title?.name === '勇者龙虾') return 10;

    const lvl = getLevelNum(fighter.grade)
    if (lvl === 1) return 6;
    if (lvl === 2) return 8;
    if (lvl >= 3) return 10;
    return 6
}

const getMovementDesc = (detail) => {
    if (!detail.isStarted && detail.total < 6) return '未达 6 点，无法起步，原地打滑！';
    if (!detail.isStarted && detail.total >= 6) return `突破界限！成功兴奋，下回合开始移动！`;
    if (detail.steps === 0) return '点数太小，原地打滑 (0步)';
    let msg = `向前冲锋 ${detail.steps} 步！`;
    if (detail.steadyBonus > 0) msg += ` (含稳健加成 ${detail.steadyBonus} 步)`;
    return msg;
}

const doBattleRollDice = () => {
    const fighter = battleCurrentFighter.value;
    const playerTag = battleState.currentTurn === 1 ? '攻方' : '守方'
    const playerName = battleState.currentTurn === 1 ? battleP1.value.name : battleP2.value.name
    const logType = battleState.currentTurn === 1 ? 'p1' : 'p2'

    battleCurrentPlayer.value.seaweed -= battleState.grassToUse
    const consumedGrassText = battleState.grassToUse > 0 ? `消耗 ${battleState.grassToUse} 草` : `无草`
    const faces = getDiceFaces(fighter)
    let baseRoll = Math.floor(Math.random() * faces) + 1
    let logDetail = `掷出 ${baseRoll} 点(D${faces})`

    if (fighter.title?.skill?.canReroll || fighter.title?.name === '勇者龙虾') {
        const roll2 = Math.floor(Math.random() * faces) + 1
        const finalRoll = Math.max(baseRoll, roll2)
        logDetail = `掷出 [${baseRoll}, ${roll2}]，勇者取大为 ${finalRoll} 点`;
        baseRoll = finalRoll
    }

    if (fighter.title?.skill?.modifyRule) {
        const rule = fighter.title.skill.modifyRule;
        if (baseRoll <= rule.threshold) {
            addBattleLog(`[幸运触发] 掷出 ${baseRoll}，转运变为 ${rule.to} 点！`, 'critical');
            baseRoll = rule.to;
        }
    } else if (fighter.title?.name === '幸运龙虾' && baseRoll <= 3) {
        addBattleLog(`[幸运触发] 掷出 ${baseRoll}，幸运转运变为 6 点！`, 'critical');
        baseRoll = 6
    }

    const totalRoll = baseRoll + battleExpectedGrassBonus.value
    if (battleExpectedGrassBonus.value > 0) {
        addBattleLog(`${playerTag} ${consumedGrassText}，基础 ${baseRoll} + 草加成 ${battleExpectedGrassBonus.value} = ${totalRoll} 点！`, logType)
    } else {
        addBattleLog(`${playerTag} ${consumedGrassText}，${logDetail}！`, logType)
    }

    processBattleMovement(baseRoll, totalRoll, playerName, playerTag, logType)
}

// 【规则修复】：起步必须等下一次掷骰子，以及独立顺位争夺循环
const processBattleMovement = (baseRoll, totalRoll, playerName, playerTag, logType) => {
    const isP1 = battleState.currentTurn === 1;
    const fighter = battleCurrentFighter.value
    const wasAlreadyStarted = isP1 ? battleState.p1Started : battleState.p2Started;

    if (!wasAlreadyStarted) {
        // 这是起步阶段的掷骰
        if (totalRoll >= 6) {
            addBattleLog(`✨ 突破界限！成功兴奋起步，等待下回合移动！`, logType)
            if (isP1) {
                battleState.p1Started = true;
                battleState.p1StartRoll = totalRoll;
            } else {
                battleState.p2Started = true;
                battleState.p2StartRoll = totalRoll;
            }
        } else {
            addBattleLog(`点数不足 6 点，未能兴奋起步。`, logType);
            if (isP1) battleState.p1StartRoll = 0; else battleState.p2StartRoll = 0;
        }

        battleState.lastRollDetail = {
            player: playerName,
            base: baseRoll,
            bonus: battleExpectedGrassBonus.value,
            total: totalRoll,
            steps: 0,
            steadyBonus: 0,
            isStarted: false
        };
        endBattleTurn();
        return;
    }

    // 正常移动阶段的掷骰
    let steps = 0
    if (totalRoll >= 3 && totalRoll <= 5) steps = 1
    else if (totalRoll >= 6 && totalRoll <= 8) steps = 2
    else if (totalRoll >= 9 && totalRoll <= 11) steps = 3
    else if (totalRoll >= 12) steps = 4

    let steadyBonus = 0;
    if (fighter.title?.skill?.bonusStep || fighter.title?.name === '稳健龙虾') {
        steadyBonus = fighter.title?.skill?.bonusStep || 1;
        steps += steadyBonus;
        addBattleLog(`[稳健触发] 额外移动 +${steadyBonus} 步！`, 'critical')
    }

    battleState.lastRollDetail = {
        player: playerName,
        base: baseRoll,
        bonus: battleExpectedGrassBonus.value,
        total: totalRoll,
        steps: steps,
        steadyBonus,
        isStarted: true
    };

    if (steps === 0) {
        addBattleLog(`点数太小转换步数为 0，原地打滑。`, logType);
        endBattleTurn();
        return
    }

    addBattleLog(`🏃 向前冲锋 ${steps} 步！`, logType)

    const oldPos = isP1 ? battleState.p1Pos : battleState.p2Pos
    let newPos = oldPos;
    if (isP1) newPos += steps; else newPos -= steps
    if (isP1) battleState.p1Pos = newPos; else battleState.p2Pos = newPos

    if (isP1 && !battleState.p1CrossedMid && oldPos <= 4 && newPos > 4) {
        battleState.p1CrossedMid = true;
        battleP1.value.de += 1
        addBattleLog(`🎖️ 攻方越过中界线，获得 1 点战功(德)！`, 'system')
    }
    if (!isP1 && !battleState.p2CrossedMid && oldPos >= 4 && newPos < 4) {
        battleState.p2CrossedMid = true;
        battleP2.value.de += 1
        addBattleLog(`🎖️ 守方越过中界线，获得 1 点战功(德)！`, 'system')
    }

    checkBattleWinCondition()
}

const checkBattleWinCondition = () => {
    let gameOver = false
    const isP1Win = () => {
        addBattleLog(`🗡️ 攻方完成无情斩杀！`, 'critical');
        battleState.winner = 1;
        gameOver = true;
    }
    const isP2Win = () => {
        addBattleLog(`🗡️ 守方完成无情斩杀！`, 'critical');
        battleState.winner = 2;
        gameOver = true;
    }

    if (battleState.currentTurn === 1) {
        if (battleState.p1Pos >= battleState.p2Pos) {
            if (battleState.p2Fighter.title?.skill?.onCovered || battleState.p2Fighter.title?.name === '铁壁龙虾') {
                addBattleLog(`🛡️ [铁壁触发] 守方坚不可摧，绝境反败为胜！`, 'critical');
                battleState.winner = 2;
                gameOver = true;
            } else {
                isP1Win()
            }
        } else if ((battleState.p1Fighter.title?.skill?.nearWinOnAdjacent || battleState.p1Fighter.title?.name === '长鳌虾') && battleState.p2Pos - battleState.p1Pos <= 1) {
            addBattleLog(`🦀 [长鳌触发] 攻方靠近目标，凭借长鳌提前斩杀！`, 'critical');
            battleState.winner = 1;
            gameOver = true
        }
    } else {
        if (battleState.p2Pos <= battleState.p1Pos) {
            if (battleState.p1Fighter.title?.skill?.onCovered || battleState.p1Fighter.title?.name === '铁壁龙虾') {
                addBattleLog(`🛡️ [铁壁触发] 攻方坚不可摧，绝境反败为胜！`, 'critical');
                battleState.winner = 1;
                gameOver = true;
            } else {
                isP2Win()
            }
        } else if ((battleState.p2Fighter.title?.skill?.nearWinOnAdjacent || battleState.p2Fighter.title?.name === '长鳌虾') && battleState.p1Pos - battleState.p2Pos <= 1) {
            addBattleLog(`🦀 [长鳌触发] 守方靠近目标，凭借长鳌提前斩杀！`, 'critical');
            battleState.winner = 2;
            gameOver = true
        }
    }

    if (gameOver) setTimeout(() => {
        battleState.phase = 'RESULT'
    }, 1500)
    else endBattleTurn()
}

// 【规则修复】：对决掷骰与先手循环判定机制
const endBattleTurn = () => {
    battleState.grassToUse = 0 // 每次重置海草

    if (battleState.battleCyclePhase) {
        // 第一轮抢顺位循环：2先掷，1后掷
        if (battleState.currentTurn === 2) {
            // P2 掷完，轮到 P1
            battleState.currentTurn = 1;
        } else {
            // P1 掷完，一个完整回合结束，开始评判结果
            if (battleState.p1Started && battleState.p2Started) {
                battleState.battleCyclePhase = false;
                if (battleState.p1StartRoll > battleState.p2StartRoll) {
                    battleState.currentTurn = 1;
                    addBattleLog(`双方均兴奋！攻方点数(${battleState.p1StartRoll}) > 守方(${battleState.p2StartRoll})，攻方夺得移动先手！`, 'system');
                } else {
                    battleState.currentTurn = 2;
                    addBattleLog(`双方均兴奋！攻方点数(${battleState.p1StartRoll}) ≤ 守方(${battleState.p2StartRoll})，守方夺得移动先手！`, 'system');
                }
            } else if (battleState.p1Started && !battleState.p2Started) {
                battleState.battleCyclePhase = false;
                battleState.currentTurn = 1;
                addBattleLog(`仅攻方兴奋，攻方夺得移动先手！`, 'system');
            } else if (!battleState.p1Started && battleState.p2Started) {
                battleState.battleCyclePhase = false;
                battleState.currentTurn = 2;
                addBattleLog(`仅守方兴奋，守方夺得移动先手！`, 'system');
            } else {
                // 都没有兴奋，重新开始循环
                battleState.currentTurn = 2;
                addBattleLog(`双方均未能兴奋，重新开始掷骰抢占起步！`, 'system');
            }
        }
    } else {
        // 普通轮流移动
        battleState.currentTurn = battleState.currentTurn === 1 ? 2 : 1;
    }

    addBattleLog(`--- 轮到 ${battleState.currentTurn === 1 ? '攻方: ' + battleP1.value.name : '守方: ' + battleP2.value.name} 行动 ---`, 'system')
}

const claimBattleReward = (type) => {
    const winPlayer = battleState.winner === 1 ? battleP1.value : battleP2.value
    const winFighter = battleState.winner === 1 ? battleState.p1Fighter : battleState.p2Fighter

    if (type === 'UPGRADE') {
        if (winFighter.grade !== LOBSTER_GRADES.ROYAL) {
            winFighter.grade = getNextLobsterGrade(winFighter.grade)
            uni.showToast({title: `成功晋升!`, icon: 'none'})
        } else {
            winPlayer.coins += 3
            uni.showToast({title: `已满阶，转为3金币!`, icon: 'none'})
        }
    } else if (type === 'COIN') {
        winPlayer.coins += 3
        uni.showToast({title: `获得 3 金币!`, icon: 'none'})
    }
    finishBattle()
}

const finishBattle = () => {
    const winnerId = battleState.winner === 1 ? battleP1.value.id : (battleState.winner === 2 ? battleP2.value.id : null)
    if (gameStore.pendingBattle?.resolve) {
        gameStore.pendingBattle.resolve(winnerId)
    }
}

// ============ 常规游戏主流程逻辑 ============
const isPlacementPhase = computed(() => gameStore.currentPhase === GAME_PHASES.PLACEMENT)
const currentPlacementPlayerName = computed(() => gameStore.currentPlacementPlayer?.name || '')

// 闹市区 1/2/3 号分别在 2/3/4 回合可用
const isMarketplaceAvailable = (i) => gameStore.currentRound >= i + 1

const canPlaceOnSlot = (area, slotIndex) => {
    if (!isPlacementPhase.value || gameStore.isPlacementComplete || isSlotOccupied(area, slotIndex)) return false
    if (area === 'marketplace' && !isMarketplaceAvailable(slotIndex + 1)) return false
    // 判断上供区是否解锁 (3号格(idx=2) 和 6号挑战格(idx=5) 需要第4回合开放)
    if (area === 'tribute') {
        const slotConf = TRIBUTE_SLOTS[slotIndex];
        if (slotConf && gameStore.currentRound < slotConf.availableFrom) return false;
    }
    return true
}

// ============ 视觉样式方法 ============

/**
 * 获取玩家栏目的样式
 * 用于区分当前轮到放置的玩家
 */
const getPlayerItemStyle = (playerId) => {
    if (!isCurrentPlacementPlayer(playerId)) return {}
    const color = PLAYER_COLORS[playerId]
    return { borderColor: color.bg, boxShadow: `0 0 10px ${color.bg}40` }
}

/**
 * 获取行动格的样式
 * 根据占用状态返回不同的视觉样式
 */
const getSlotStyle = (area, slotIndex) => {
    const slotStatus = gameStore.getSlotStatus(area, slotIndex)
    if (slotStatus.status === 'occupied') {
        const style = getOccupiedSlotStyle(slotStatus.playerId)
        return {
            background: style.background,
            borderColor: style.borderColor,
            opacity: style.opacity,
            color: style.color
        }
    }
    // 未占用状态
    return { background: DEFAULT_SLOT_STYLE.background, opacity: isPlacementPhase.value ? 1 : 0.6 }
}

/**
 * 检查行动格是否被占用
 */
const isSlotOccupied = (area, slotIndex) => gameStore.isSlotOccupied(area, slotIndex)

/**
 * 获取占用行动格的玩家标签
 * 用于在UI上显示"1P"、"2P"等标识
 */
const getSlotOccupantLabel = (area, slotIndex) => {
    const status = gameStore.getSlotStatus(area, slotIndex)
    if (status.status === 'occupied') return getOccupiedSlotStyle(status.playerId).playerLabel
    return null
}

const isCurrentPlacementPlayer = (playerId) => {
    if (!isPlacementPhase.value || gameStore.isPlacementComplete) return false
    return gameStore.placementOrder[gameStore.currentPlacementIndex] === playerId
}

// ============ 交互处理方法 ============

/**
 * 显示提示信息
 * @param {string} message - 提示内容
 * @param {string} icon - 图标类型
 */
const showToast = (message, icon = 'none') => uni.showToast({ title: message, icon, duration: 2000 })

/**
 * 处理行动格点击事件
 * 实现放置机制的核心交互逻辑
 */
const handleSlotClick = (area, slotIndex) => {
    // 如果不是工放阶段，显示提示
    if (!isPlacementPhase.value) {
        showToast('当前不是工放阶段，无法放置里长');
        return
    }

    // 如果所有玩家都已放置完毕
    if (gameStore.isPlacementComplete) {
        showToast('工放阶段已结束');
        return
    }

    // 拦截未开放的闹市区行动格强行点击
    if (area === 'marketplace' && !isMarketplaceAvailable(slotIndex + 1)) {
        showToast(`该行动格在第${slotIndex + 2}回合才开放`);
        return
    }

    if (area === 'tribute') {
        const slotConf = TRIBUTE_SLOTS[slotIndex];
        if (slotConf && gameStore.currentRound < slotConf.availableFrom) {
            showToast(`该行动格在第${slotConf.availableFrom}回合才开放`);
            return;
        }
    }

    if (isSlotOccupied(area, slotIndex)) {
        const status = gameStore.getSlotStatus(area, slotIndex)
        showToast(`该行动格已被${gameStore.players[status.playerId]?.name || '未知玩家'}占用`)
        return
    }

    // 执行放置操作
    const result = gameStore.placeLiZhang(area, slotIndex)

    // 处理放置结果
    if (!result.success) {
        if (result.error === '没有剩余的里长可以放置') showToast(`${result.message}，将自动跳过`)
        else showToast(result.message || result.error)
    }
}

// ==========================================
// 养蛊区交互逻辑 (Breeding Actions)
// ==========================================
const currentPendingBreeding = computed(() => gameStore.pendingBreeding)
const breedingState = reactive({
    lobsterIndex: -1, useSeaweed: false, royalCostType: '', selectedTitleId: '', royalRewardType: 'de'
})

const targetLobster = computed(() => {
    if (!currentPendingBreeding.value) return null
    return currentPendingBreeding.value.player.lobsters[breedingState.lobsterIndex]
})

// 判断当前吃海草是否还能起作用 (一品龙虾免费升就到皇家满级了，吃草无效)
const isSeaweedUseful = computed(() => {
    if (!targetLobster.value) return false
    return targetLobster.value.grade !== LOBSTER_GRADES.GRADE1 && targetLobster.value.grade !== LOBSTER_GRADES.ROYAL
})

// 目标推演：免费一品 + 选配海草额外一品
const projectedGrade = computed(() => {
    if (!targetLobster.value) return null
    let grade = getNextLobsterGrade(targetLobster.value.grade)
    if (breedingState.useSeaweed) grade = getNextLobsterGrade(grade)
    return grade
})

const isUpgradingToRoyal = computed(() => {
    return targetLobster.value && targetLobster.value.grade !== LOBSTER_GRADES.ROYAL && projectedGrade.value === LOBSTER_GRADES.ROYAL
})

const canAffordRoyal = computed(() => {
    if (!isUpgradingToRoyal.value) return true
    if (breedingState.royalCostType === 'cage' && currentPendingBreeding.value.player.cages >= 1) return true
    if (breedingState.royalCostType === 'coin' && currentPendingBreeding.value.player.coins >= 3) return true
    return false
})

const canConfirmBreeding = computed(() => {
    if (!targetLobster.value) return false
    if (breedingState.useSeaweed && currentPendingBreeding.value.player.seaweed < 1) return false
    if (isUpgradingToRoyal.value && !canAffordRoyal.value) return false
    if (isUpgradingToRoyal.value && gameStore.gameTitleCards.length > 0 && !breedingState.selectedTitleId) return false
    return true
})

const selectLobsterForBreeding = (index) => {
    breedingState.lobsterIndex = index;
    breedingState.useSeaweed = false;
    breedingState.royalCostType = '';
    breedingState.selectedTitleId = '';
    breedingState.royalRewardType = 'de'
}

const toggleSeaweed = () => {
    // 如果海草无效（已达一品升皇家阶段），禁止点击
    if (!isSeaweedUseful.value) {
        showToast('已达满级，无需消耗海草');
        return
    }
    const player = currentPendingBreeding.value.player
    if (player.seaweed >= 1 || breedingState.useSeaweed) breedingState.useSeaweed = !breedingState.useSeaweed
    else showToast('海草数量不足')
}

const cancelBreedingAction = () => {
    breedingState.lobsterIndex = -1
}

const confirmBreedingAction = () => {
    if (!canConfirmBreeding.value) return
    const player = currentPendingBreeding.value.player
    const lobster = targetLobster.value
    let logMsg = `${player.name}将龙虾从[${getLobsterGradeName(lobster.grade)}]培养至[${getLobsterGradeName(projectedGrade.value)}]，`

    if (breedingState.useSeaweed) {
        player.seaweed -= 1;
        logMsg += `消耗1海草，`
    }

    if (isUpgradingToRoyal.value) {
        if (breedingState.royalCostType === 'cage') {
            player.cages -= 1;
            logMsg += `消耗1虾笼支付皇家费用，`
        } else if (breedingState.royalCostType === 'coin') {
            player.coins -= 3;
            logMsg += `消耗3金币支付皇家费用，`
        }

        if (breedingState.selectedTitleId) {
            const titleIndex = gameStore.gameTitleCards.findIndex(c => c.id === breedingState.selectedTitleId)
            if (titleIndex > -1) {
                const titleCard = gameStore.gameTitleCards.splice(titleIndex, 1)[0]
                lobster.title = titleCard;
                logMsg += `并夺得霸气称号【${titleCard.name}】`
            }
        }
        if (breedingState.royalRewardType === 'de') {
            player.de += 1;
            logMsg += `，额外获得 1 德`
        } else if (breedingState.royalRewardType === 'wang') {
            player.wang += 1;
            logMsg += `，额外获得 1 望`
        }
    }

    lobster.grade = projectedGrade.value
    if (logMsg.endsWith('，')) logMsg = logMsg.slice(0, -1)

    gameStore.addLog(logMsg, 'success')
    currentPendingBreeding.value.actionCount -= 1
    cancelBreedingAction()
    if (currentPendingBreeding.value.actionCount <= 0) finishBreeding()
}

const finishBreeding = () => {
    if (currentPendingBreeding.value && currentPendingBreeding.value.resolve) currentPendingBreeding.value.resolve()
}

// ==========================================
// 闹市区交互逻辑 (Marketplace Actions)
// ==========================================
const currentPendingMarketplace = computed(() => gameStore.pendingMarketplace)
const marketplaceState = reactive({selectedCard: null, selectedOptionIndex: 0})

const selectMarketplaceCard = (card) => {
    if (card.usedThisRound) return
    marketplaceState.selectedCard = card;
    marketplaceState.selectedOptionIndex = 0
}

const getResourceName = (key) => {
    const map = {coins: '金币', seaweed: '海草', cages: '虾笼', lobsters: '只龙虾', de: '德', wang: '望'}
    return map[key] || key
}

const formatOptionText = (opt) => {
    if (!opt || !opt.cost || !opt.reward) return ''
    const costStrs = Object.entries(opt.cost).map(([k, v]) => `${v} ${getResourceName(k)}`)
    const rewardStrs = Object.entries(opt.reward).map(([k, v]) => `${v} ${getResourceName(k)}`)
    return `消耗 ${costStrs.join(' 和 ')} ➔ 获得 ${rewardStrs.join(' 和 ')}`
}

// 根据选中的选项计算是否足以支付对应费用（加入可选链安全防爆）
const canConfirmMarketplace = computed(() => {
    if (!marketplaceState.selectedCard) return false
    const card = marketplaceState.selectedCard;
    const player = currentPendingMarketplace.value?.player
    if (!player) return false

    if (!card.auto && card.action?.type === 'exchange') {
        const options = card.action?.options || [];
        const opt = options[marketplaceState.selectedOptionIndex]
        if (!opt || !opt.cost) return false

        for (const [resType, resAmount] of Object.entries(opt.cost)) {
            if (resType === 'lobsters') {
                if (player.lobsters.length < resAmount) return false
            } else {
                if (player[resType] < resAmount) return false
            }
        }
    }
    return true
})

const confirmMarketplaceAction = () => {
    if (!canConfirmMarketplace.value) return
    currentPendingMarketplace.value.resolve({
        card: marketplaceState.selectedCard, optionIndex: marketplaceState.selectedOptionIndex
    })
    marketplaceState.selectedCard = null;
    marketplaceState.selectedOptionIndex = 0
}

const skipMarketplaceAction = () => {
    currentPendingMarketplace.value.resolve(null);
    marketplaceState.selectedCard = null;
    marketplaceState.selectedOptionIndex = 0
}

// ==========================================
// 海鲜市场交互逻辑 (Seafood Market)
// ==========================================
const currentPendingSeafoodMarket = computed(() => gameStore.pendingSeafoodMarket)
const smTab = ref('trade')

const currentMarketPrices = computed(() => getMarketPrices(gameStore.seafoodMarketLobsters))

const isSpaceFilled = (overallIndex) => overallIndex >= (8 - gameStore.seafoodMarketLobsters)

const doSeafoodTrade = (actionType) => {
    if (!currentPendingSeafoodMarket.value) return
    gameStore.processSeafoodMarketAction(currentPendingSeafoodMarket.value.player, actionType)
}

const formatHireReward = (reward) => {
    if (reward.seaweed) return `${reward.seaweed}海草`
    if (reward.lobster) return `1只${getLobsterGradeName(LOBSTER_GRADES[reward.lobster.toUpperCase()] || LOBSTER_GRADES.NORMAL)}`
    return '无'
}

const canHireAny = computed(() => {
    if (!currentPendingSeafoodMarket.value) return false
    const player = currentPendingSeafoodMarket.value.player
    // 基础条件：得有6块钱，且玩家在全局没有占满2个位置
    if (player.coins < 6) return false
    const myHiredCount = gameStore.hiredLiZhangSlots.filter(id => id === player.id).length
    if (myHiredCount >= 2) return false
    return true
})

const canHireSlot = (idx) => {
    if (!canHireAny.value) return false
    const slot = HIRE_LIZHANG_SLOTS[idx]
    if (gameStore.currentRound < slot.availableFrom) return false
    if (gameStore.hiredLiZhangSlots[idx] !== null) return false
    return true
}

const doSeafoodHire = (idx) => {
    if (!canHireSlot(idx)) {
        showToast('无法雇佣该位置');
        return
    }
    gameStore.processSeafoodMarketAction(currentPendingSeafoodMarket.value.player, 'hire', idx)
}

const skipSeafoodMarketAction = () => {
    if (currentPendingSeafoodMarket.value) {
        currentPendingSeafoodMarket.value.actionCount = 0
        currentPendingSeafoodMarket.value.resolve()
    }
}

// ==========================================
// 上供区交互逻辑 (Tribute Actions)
// ==========================================
const currentPendingTribute = computed(() => gameStore.pendingTribute)

const tributeState = reactive({
    isNakedMode: false, nakedLobsterIndex: -1, nakedTavernId: '', nakedRewardType: 'de'
})

// 格式化上供区卡牌资源需求
const formatTributeReq = (req) => {
    const parts = []
    if (req.coins) parts.push(`${req.coins}金币`)
    if (req.seaweed) parts.push(`${req.seaweed}海草`)
    if (req.cages) parts.push(`${req.cages}虾笼`)
    if (req.lobsters) {
        for (const [gradeKey, count] of Object.entries(req.lobsters)) {
            const gradeName = getLobsterGradeName(LOBSTER_GRADES[gradeKey.toUpperCase()] || LOBSTER_GRADES.NORMAL)
            parts.push(`${count}只${gradeName}`)
        }
    }
    return parts.join(' + ') || '无要求'
}

const formatTributeRew = (rew) => {
    const parts = [];
    if (rew.de) parts.push(`+${rew.de}德`);
    if (rew.wang) parts.push(`+${rew.wang}望`)
    return parts.join('，') || '无附加点数'
}

// 检查玩家是否有足够资源上供该卡
const checkTributeReq = (req, player) => {
    if (!player) return false;
    if (req.coins && player.coins < req.coins) return false;
    if (req.seaweed && player.seaweed < req.seaweed) return false;
    if (req.cages && player.cages < req.cages) return false;

    if (req.lobsters) {
        let tempLobsters = [...player.lobsters];
        for (const [gradeKey, count] of Object.entries(req.lobsters)) {
            let foundCount = 0;
            for (let i = 0; i < count; i++) {
                const reqGradeVal = Object.values(LOBSTER_GRADES).indexOf(LOBSTER_GRADES[gradeKey.toUpperCase()]);
                const matchIdx = tempLobsters.findIndex(l => Object.values(LOBSTER_GRADES).indexOf(l.grade) >= reqGradeVal);
                if (matchIdx !== -1) {
                    foundCount++;
                    tempLobsters.splice(matchIdx, 1);
                }
            }
            if (foundCount < count) return false;
        }
    }
    return true;
}

const confirmTributeCard = (tavernId, cardId) => {
    if (currentPendingTribute.value) {
        currentPendingTribute.value.resolve({isNaked: false, tavernId, cardId});
    }
}

// 裸交：筛选三品以上的龙虾
const getValidNakedLobsters = (player) => {
    if (!player) return [];
    return player.lobsters.map((l, index) => ({...l, originalIndex: index}))
            .filter(l => l.grade === LOBSTER_GRADES.GRADE3 || l.grade === LOBSTER_GRADES.GRADE2 || l.grade === LOBSTER_GRADES.GRADE1 || l.grade === LOBSTER_GRADES.ROYAL);
}

const confirmNakedTribute = () => {
    if (currentPendingTribute.value) {
        currentPendingTribute.value.resolve({
            isNaked: true,
            tavernId: tributeState.nakedTavernId,
            nakedLobsterIndex: tributeState.nakedLobsterIndex,
            nakedRewardType: tributeState.nakedRewardType
        });

        // 恢复默认状态
        tributeState.isNakedMode = false;
        tributeState.nakedLobsterIndex = -1;
        tributeState.nakedTavernId = '';
    }
}

const skipTributeAction = () => {
    if (currentPendingTribute.value) currentPendingTribute.value.resolve(null);
}

// ============ 工具方法 ============
const getPhaseText = () => `${gameStore.getPhaseText()}阶段`
const getShrimpCatchingSlotDesc = (i) => ['1虾笼,夺起始,1次捕虾', '1虾笼,2次捕虾', '1金币,3次捕虾', '4次捕虾'][i - 1]
const getSeafoodMarketSlotDesc = (i) => ['1金币,2次交易', '3次交易', '1金币,3次交易', '2金币,3次交易'][i - 1]
const getBreedingSlotDesc = (i) => ['1草,1次培养', '2次培养', '1金币,2次培养', '3次培养'][i - 1]
// 上供区 1/2/3 号是常规，4/5/6 是挑战
const getTributeSlotDesc = (i) => {
    const conf = TRIBUTE_SLOTS[i - 1];
    return conf ? conf.description : '';
}
const getMarketplaceSlotDesc = (i) => ['第2回合可用,1次闹市', '1金币,第3回合可用,1次闹市', '2金币,第4回合可用,1次闹市'][i - 1]

const handleNextPhase = async () => {
    if (gameStore.currentRound >= gameStore.maxRounds && gameStore.currentPhase === GAME_PHASES.CLEANUP) {
        uni.navigateTo({ url: '/pages/result/result' })
    } else {
        await gameStore.nextPhase()
    }
}
</script>