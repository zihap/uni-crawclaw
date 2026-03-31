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
                    <text class="section-desc">放置里长完成上供任务</text>
                </view>
                <view class="area-slots">
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
                        disabled: !canPlaceOnSlot('marketplace', i - 1)
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

                            <!-- 如果本回合还有剩余称号卡，玩家升到皇家必须强制获取 -->
                            <view v-if="gameStore.gameTitleCards.length > 0" class="title-selection">
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

                    <!-- 第二步：展示对应选项 (针对非自动执行且为exchange类型的兑换卡，加入空数组安全兜底) -->
                    <view
                        v-if="marketplaceState.selectedCard && !marketplaceState.selectedCard.auto && marketplaceState.selectedCard.action?.type === 'exchange'"
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

        <!-- 海鲜市场结算弹窗 (新增) -->
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
                        <!-- 摊位1 (左侧：3格，买方最先空) -->
                        <view class="stall stall-1">
                            <view class="stall-label">一号摊</view>
                            <view class="stall-spaces">
                                <view v-for="i in 3" :key="'s1'+i" class="stall-space"
                                      :class="{filled: isSpaceFilled(i - 1)}"></view>
                            </view>
                        </view>
                        <!-- 摊位2 (中间：2格) -->
                        <view class="stall stall-2">
                            <view class="stall-label">二号摊</view>
                            <view class="stall-spaces">
                                <view v-for="i in 2" :key="'s2'+i" class="stall-space"
                                      :class="{filled: isSpaceFilled(3 + i - 1)}"></view>
                            </view>
                        </view>
                        <!-- 摊位3 (右侧：3格，进货方最先满) -->
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
                                    <text
                                        v-if="gameStore.hiredLiZhangSlots[idx] === currentPendingSeafoodMarket.player.id">
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

    </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useGameStore, GAME_PHASES, LOBSTER_GRADES } from '@stores/game.js'
import { DEFAULT_SLOT_STYLE, getOccupiedSlotStyle, PLAYER_COLORS } from '@utils/slotConstants.js'
import { getLobsterGradeName, getNextLobsterGrade } from '@utils/gameUtils.js'
import {HIRE_LIZHANG_SLOTS, getMarketPrices} from '@utils/seafoodMarketUtils.js'

const gameStore = useGameStore()
const showLog = ref(false)

// ============ 计算属性 ============
const isPlacementPhase = computed(() => gameStore.currentPhase === GAME_PHASES.PLACEMENT)
const currentPlacementPlayerName = computed(() => gameStore.currentPlacementPlayer?.name || '')

// 闹市区 1/2/3 号分别在 2/3/4 回合可用，即 currentRound >= i + 1 即可
const isMarketplaceAvailable = (i) => gameStore.currentRound >= i + 1

const canPlaceOnSlot = (area, slotIndex) => {
    if (!isPlacementPhase.value || gameStore.isPlacementComplete || isSlotOccupied(area, slotIndex)) return false
    // 判断闹市区是否解锁
    if (area === 'marketplace' && !isMarketplaceAvailable(slotIndex + 1)) return false
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
        showToast(`该行动格在第${slotIndex + 2}回合才开放`)
        return
    }

    // 如果行动格已被占用，显示占用者信息
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
    lobsterIndex: -1,
    useSeaweed: false,
    royalCostType: '', // 'cage' | 'coin'
    selectedTitleId: ''
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
    let grade = getNextLobsterGrade(targetLobster.value.grade) // 免费一品
    if (breedingState.useSeaweed) {
        grade = getNextLobsterGrade(grade) // 海草额外一品
    }
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
    breedingState.lobsterIndex = index
    breedingState.useSeaweed = false
    breedingState.royalCostType = ''
    breedingState.selectedTitleId = ''
}

const toggleSeaweed = () => {
    // 如果海草无效（已达一品升皇家阶段），禁止点击
    if (!isSeaweedUseful.value) {
        showToast('已达满级，无需消耗海草')
        return
    }

    const player = currentPendingBreeding.value.player
    if (player.seaweed >= 1 || breedingState.useSeaweed) {
        breedingState.useSeaweed = !breedingState.useSeaweed
    } else {
        showToast('海草数量不足')
    }
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
        player.seaweed -= 1
        logMsg += `消耗1海草，`
    }

    if (isUpgradingToRoyal.value) {
        if (breedingState.royalCostType === 'cage') {
            player.cages -= 1
            logMsg += `消耗1虾笼支付皇家费用，`
        } else if (breedingState.royalCostType === 'coin') {
            player.coins -= 3
            logMsg += `消耗3金币支付皇家费用，`
        }
        if (breedingState.selectedTitleId) {
            const titleIndex = gameStore.gameTitleCards.findIndex(c => c.id === breedingState.selectedTitleId)
            if (titleIndex > -1) {
                // UI层直接切走被选中的称号卡，后续玩家只能在剩下的卡里选
                const titleCard = gameStore.gameTitleCards.splice(titleIndex, 1)[0]
                lobster.title = titleCard
                logMsg += `并夺得霸气称号【${titleCard.name}】`
            }
        }
    }

    lobster.grade = projectedGrade.value
    if (logMsg.endsWith('，')) logMsg = logMsg.slice(0, -1)

    gameStore.addLog(logMsg, 'success')
    currentPendingBreeding.value.actionCount -= 1
    cancelBreedingAction()

    if (currentPendingBreeding.value.actionCount <= 0) {
        finishBreeding()
    }
}

const finishBreeding = () => {
    if (currentPendingBreeding.value && currentPendingBreeding.value.resolve) {
        currentPendingBreeding.value.resolve()
    }
}

// ==========================================
// 闹市区交互逻辑 (Marketplace Actions)
// ==========================================
const currentPendingMarketplace = computed(() => gameStore.pendingMarketplace)
const marketplaceState = reactive({
    selectedCard: null,
    selectedOptionIndex: 0
})

const selectMarketplaceCard = (card) => {
    if (card.usedThisRound) return
    marketplaceState.selectedCard = card
    marketplaceState.selectedOptionIndex = 0
}

// 通用的选项文本格式化方法
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
    const card = marketplaceState.selectedCard
    const player = currentPendingMarketplace.value?.player // 添加可选链防爆

    if (!player) return false

    if (!card.auto && card.action?.type === 'exchange') {
        const options = card.action?.options || [] // 兜底处理
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
        card: marketplaceState.selectedCard,
        optionIndex: marketplaceState.selectedOptionIndex
    })
    marketplaceState.selectedCard = null
    marketplaceState.selectedOptionIndex = 0
}

const skipMarketplaceAction = () => {
    currentPendingMarketplace.value.resolve(null)
    marketplaceState.selectedCard = null
    marketplaceState.selectedOptionIndex = 0
}

// ==========================================
// 海鲜市场交互逻辑 (Seafood Market)
// ==========================================
const currentPendingSeafoodMarket = computed(() => gameStore.pendingSeafoodMarket)
const smTab = ref('trade') // 'trade' | 'hire' 切换控制

// 动态计算当前物价
const currentMarketPrices = computed(() => {
    return getMarketPrices(gameStore.seafoodMarketLobsters)
})

// 计算摊位填充逻辑 (从右到左填满，0-7分别对应1~3号摊位左至右的格子。如果有 N 只虾，那么填满最后 N 个格子)
const isSpaceFilled = (overallIndex) => {
    return overallIndex >= (8 - gameStore.seafoodMarketLobsters)
}

const doSeafoodTrade = (actionType) => {
    if (!currentPendingSeafoodMarket.value) return
    gameStore.processSeafoodMarketAction(currentPendingSeafoodMarket.value.player, actionType)
}

// 雇佣相关方法
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
    if (gameStore.currentRound < slot.availableFrom) return false // 未开放
    if (gameStore.hiredLiZhangSlots[idx] !== null) return false // 已被占
    return true
}

const doSeafoodHire = (idx) => {
    if (!canHireSlot(idx)) {
        showToast('无法雇佣该位置')
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

// ============ 工具方法 ============
const getPhaseText = () => `${gameStore.getPhaseText()}阶段`
const getShrimpCatchingSlotDesc = (i) => ['1虾笼,夺起始,1次捕虾', '1虾笼,2次捕虾', '1金币,3次捕虾', '4次捕虾'][i - 1]
const getSeafoodMarketSlotDesc = (i) => ['1金币,2次交易', '3次交易', '1金币,3次交易', '2金币,3次交易'][i - 1]
const getBreedingSlotDesc = (i) => ['1草,1次培养', '2次培养', '1金币,2次培养', '3次培养'][i - 1]
const getTributeSlotDesc = (i) => i <= 3 ? (i === 3 ? '第4回合可用,1次上供' : '1次上供') : `挑战${i - 3}号位,1次上供`
const getMarketplaceSlotDesc = (i) => ['第2回合可用,1次闹市', '1金币,第3回合可用,1次闹市', '2金币,第4回合可用,1次闹市'][i - 1]

const handleNextPhase = async () => {
    if (gameStore.currentRound >= gameStore.maxRounds && gameStore.currentPhase === GAME_PHASES.CLEANUP) {
        uni.navigateTo({ url: '/pages/result/result' })
    } else {
        await gameStore.nextPhase()
    }
}
</script>
