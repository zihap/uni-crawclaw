<template>
    <view class="game-container">
        <!-- 游戏头部 -->
        <view class="game-header">
            <view class="round-info">
                <text class="round-label">回合</text>
                <text class="round-number">{{ onlineGameStore.currentRound }}/{{ onlineGameStore.maxRounds }}</text>
            </view>
            <view class="phase-info">
                <text class="phase-label">{{ phaseText }}</text>
            </view>
            <button
                class="next-btn"
                v-if="onlineGameStore.currentPhase !== 'settlement'"
                @click="handleNextPhase"
                :disabled="!onlineGameStore.isMyTurn"
            >
                下一阶段
            </button>
        </view>

        <!-- 放置阶段提示 -->
        <view v-if="isPlacementPhase" class="placement-banner">
            <view class="placement-info">
                <text class="placement-text">
                    {{ onlineGameStore.isMyTurn ? '轮到你放置里长' : `等待 ${currentPlacementPlayerName} 放置里长` }}
                </text>
                <text class="placement-hint"> 点击空闲的行动格放置里长 </text>
            </view>
        </view>

        <!-- 玩家栏 -->
        <view class="players-bar">
            <view
                v-for="(player, index) in playerStore.players"
                :key="player.id"
                :class="[
                    'player-item',
                    {
                        active: isCurrentPlacementPlayer(index),
                        'is-me': player.id === onlineGameStore.playerId,
                        starting: player.isStartingPlayer
                    }
                ]"
                :style="getPlayerItemStyle(index)"
            >
                <view class="player-badge" v-if="player.isStartingPlayer">起始</view>
                <view class="player-badge me-badge" v-if="player.id === onlineGameStore.playerId">我</view>
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
                    <view
                        v-for="i in 4"
                        :key="i"
                        :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('shrimp_catching', i - 1),
                                disabled: !canPlaceOnSlot('shrimp_catching', i - 1)
                            }
                        ]"
                        :style="getSlotStyle('shrimp_catching', i - 1)"
                        @click="handleSlotClick('shrimp_catching', i - 1)"
                    >
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
                    <text class="section-desc">放置里长进行交易</text>
                </view>
                <view class="area-slots">
                    <view
                        v-for="i in 4"
                        :key="i"
                        :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('seafood_market', i - 1),
                                disabled: !canPlaceOnSlot('seafood_market', i - 1)
                            }
                        ]"
                        :style="getSlotStyle('seafood_market', i - 1)"
                        @click="handleSlotClick('seafood_market', i - 1)"
                    >
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
                    <view
                        v-for="i in 4"
                        :key="i"
                        :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('breeding', i - 1),
                                disabled: !canPlaceOnSlot('breeding', i - 1)
                            }
                        ]"
                        :style="getSlotStyle('breeding', i - 1)"
                        @click="handleSlotClick('breeding', i - 1)"
                    >
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
                    <view
                        v-for="i in 8"
                        :key="i"
                        :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('tribute', i - 1),
                                disabled: !canPlaceOnSlot('tribute', i - 1),
                                'challenge-slot': i > 3 && i <= 6
                            }
                        ]"
                        :style="getSlotStyle('tribute', i - 1)"
                        @click="handleSlotClick('tribute', i - 1)"
                    >
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
                    <view
                        v-for="i in 3"
                        :key="i"
                        :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('marketplace', i - 1),
                                disabled: !canPlaceOnSlot('marketplace', i - 1) || !isMarketplaceAvailable(i)
                            }
                        ]"
                        :style="getSlotStyle('marketplace', i - 1)"
                        @click="handleSlotClick('marketplace', i - 1)"
                    >
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
        <view class="current-player-panel" v-if="onlineGameStore.myPlayer">
            <view class="panel-header">
                <text class="panel-title">{{ onlineGameStore.myPlayer.name }}的回合</text>
                <text class="lizhang-count"
                    >里长: {{ onlineGameStore.myPlayer.headmen || onlineGameStore.myPlayer.liZhang || 0 }}</text
                >
            </view>
            <view class="panel-resources">
                <view class="resource-item">
                    <text class="resource-label">金币</text>
                    <text class="resource-value">{{
                        onlineGameStore.myPlayer.gold || onlineGameStore.myPlayer.coins || 0
                    }}</text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">海草</text>
                    <text class="resource-value">{{ onlineGameStore.myPlayer.seaweed || 0 }}</text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">虾笼</text>
                    <text class="resource-value">{{ onlineGameStore.myPlayer.cages || 0 }}</text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">龙虾</text>
                    <text class="resource-value">{{ onlineGameStore.myPlayer.lobsters?.length }}</text>
                </view>
            </view>
        </view>

        <!-- 日志面板 -->
        <view class="log-panel">
            <view class="log-header" @click="showLog = !showLog">
                <text class="log-title">游戏日志</text>
                <text class="log-toggle">{{ showLog ? '收起' : '展开' }}</text>
            </view>
            <view class="log-content" v-if="showLog">
                <view class="log-scroll">
                    <view
                        v-for="(log, index) in onlineGameStore.logs?.slice().reverse() || []"
                        :key="index"
                        :class="['log-item', log.type || 'info']"
                    >
                        <text class="log-text">{{ log.message }}</text>
                    </view>
                </view>
            </view>
        </view>

        <!-- 捕虾区结算弹窗 -->
        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'shrimp_catching'">
            <view class="modal-content shrimp-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的捕虾行动</text>
                        <text class="modal-subtitle"
                            >剩余次数:
                            <text class="highlight">{{ pendingSettlement?.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <view class="modal-body">
                    <!-- 指示物展示 -->
                    <view class="indicator-display">
                        <text class="indicator-icon">🎣</text>
                        <text class="indicator-text">抽到了"龙虾或海草"，请选择：</text>
                    </view>

                    <!-- 选择按钮 -->
                    <view class="choice-buttons">
                        <button class="btn btn-choice" @click="chooseShrimpReward('lobster')">🦞 选择龙虾</button>
                        <button class="btn btn-choice" @click="chooseShrimpReward('seaweed')">🌿 选择海草</button>
                    </view>
                </view>

                <view class="modal-footer">
                    <button class="btn btn-secondary w-full" @click="skipSettlementAction">放弃剩余次数并结束</button>
                </view>
            </view>
        </view>

        <!-- 海鲜市场结算弹窗 -->
        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'seafood_market'">
            <view class="modal-content seafood-market-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的市场交易</text>
                        <text class="modal-subtitle"
                            >剩余行动次数:
                            <text class="highlight">{{ pendingSettlement?.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <view class="market-display-board">
                    <view class="market-prices">
                        <text class="price-title">当前流通物价</text>
                        <view class="price-tags">
                            <text>龙虾买: {{ marketPrices.buyLobster }}金 / 卖: {{ marketPrices.sellLobster }}金</text>
                            <text>虾笼买: {{ marketPrices.buyCage }}金 / 卖: {{ marketPrices.sellCage }}金</text>
                            <text>海草买: {{ marketPrices.buySeaweed }}金 / 卖: {{ marketPrices.sellSeaweed }}金</text>
                        </view>
                    </view>
                </view>

                <view class="modal-body">
                    <view class="trade-grid">
                        <view class="trade-row">
                            <button
                                class="btn btn-outline"
                                @click="doSeafoodTrade('buy_lobster')"
                                :disabled="!canBuyLobster"
                            >
                                买入龙虾 (-{{ marketPrices.buyLobster }}金)
                            </button>
                            <button
                                class="btn btn-outline"
                                @click="doSeafoodTrade('sell_lobster')"
                                :disabled="!canSellLobster"
                            >
                                卖出龙虾 (+{{ marketPrices.sellLobster }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('buy_cage')" :disabled="!canBuyCage">
                                买入虾笼 (-{{ marketPrices.buyCage }}金)
                            </button>
                            <button
                                class="btn btn-outline"
                                @click="doSeafoodTrade('sell_cage')"
                                :disabled="!canSellCage"
                            >
                                卖出虾笼 (+{{ marketPrices.sellCage }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button
                                class="btn btn-outline"
                                @click="doSeafoodTrade('buy_seaweed')"
                                :disabled="!canBuySeaweed"
                            >
                                买海草 (-{{ marketPrices.buySeaweed }}金)
                            </button>
                            <button
                                class="btn btn-outline"
                                @click="doSeafoodTrade('sell_seaweed')"
                                :disabled="!canSellSeaweed"
                            >
                                卖海草 (+{{ marketPrices.sellSeaweed }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('hire')" :disabled="!canHire">
                                雇佣头目 (-6金)
                            </button>
                        </view>
                    </view>
                </view>

                <view class="modal-footer">
                    <button class="btn btn-secondary w-full" @click="skipSettlementAction">放弃剩余次数并结束</button>
                </view>
            </view>
        </view>

        <!-- 养蛊区结算弹窗 -->
        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'breeding'">
            <view class="modal-content breeding-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的培养行动</text>
                        <text class="modal-subtitle"
                            >剩余次数:
                            <text class="highlight">{{ pendingSettlement?.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <view class="modal-body">
                    <!-- 第一步：选择龙虾 -->
                    <view v-if="breedingState.lobsterIndex === -1" class="lobster-selection">
                        <text class="section-label">请选择要进行培养的龙虾：</text>
                        <view class="lobster-grid">
                            <view
                                v-for="(lobster, index) in pendingSettlement?.player?.lobsters"
                                :key="lobster.id"
                                class="lobster-card"
                                :class="{ 'max-royal': lobster.grade === LOBSTER_GRADES.ROYAL }"
                                @click="lobster.grade !== LOBSTER_GRADES.ROYAL && selectLobsterForBreeding(index)"
                            >
                                <text class="lobster-icon">🦞</text>
                                <text class="lobster-grade">{{ getLobsterGradeName(lobster.grade) }}</text>
                                <text class="lobster-title" v-if="lobster.title">{{ lobster.title.name }}</text>
                                <view v-if="lobster.grade === LOBSTER_GRADES.ROYAL" class="max-grade-mask">已满级</view>
                            </view>
                        </view>
                        <view v-if="!pendingSettlement?.player?.lobsters?.length" class="empty-hint">
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
                            <view
                                class="checkbox-wrapper"
                                @click="toggleSeaweed"
                                :class="{
                                    disabled:
                                        (pendingSettlement?.player?.seaweed < 1 && !breedingState.useSeaweed) ||
                                        !isSeaweedUseful
                                }"
                            >
                                <view class="custom-checkbox" :class="{ checked: breedingState.useSeaweed }"></view>
                                <text class="checkbox-text"
                                    >消耗 1 海草 额外升一品 (拥有: {{ pendingSettlement?.player?.seaweed }})
                                </text>
                            </view>
                        </view>

                        <!-- 突破至皇家时的附加消耗要求 -->
                        <view v-if="isUpgradingToRoyal" class="royal-requirements animate-fade-in">
                            <text class="req-title">突破至皇家级需支付额外费用：</text>
                            <view class="cost-options">
                                <button
                                    class="cost-btn"
                                    :class="{ active: breedingState.royalCostType === 'cage' }"
                                    :disabled="pendingSettlement?.player?.cages < 1"
                                    @click="breedingState.royalCostType = 'cage'"
                                >
                                    🦞 1 虾笼 (拥有: {{ pendingSettlement?.player?.cages }})
                                </button>
                                <button
                                    class="cost-btn"
                                    :class="{ active: breedingState.royalCostType === 'coin' }"
                                    :disabled="pendingSettlement?.player?.coins < 3"
                                    @click="breedingState.royalCostType = 'coin'"
                                >
                                    🪙 3 金币 (拥有: {{ pendingSettlement?.player?.coins }})
                                </button>
                            </view>
                        </view>

                        <view class="modal-actions">
                            <button class="btn btn-ghost" @click="cancelBreedingAction">返回重选</button>
                            <button
                                class="btn btn-primary"
                                :disabled="!canConfirmBreeding"
                                @click="confirmBreedingAction"
                            >
                                确认培养
                            </button>
                        </view>
                    </view>
                </view>

                <view class="modal-footer" v-if="breedingState.lobsterIndex === -1">
                    <button class="btn btn-secondary w-full" @click="skipSettlementAction">放弃剩余次数并结束</button>
                </view>
            </view>
        </view>

        <!-- 闹市区结算弹窗 -->
        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'marketplace'">
            <view class="modal-content marketplace-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的闹市行动</text>
                        <text class="modal-subtitle">请选择本回合尚未被执行的一张闹市卡</text>
                    </view>
                </view>

                <view class="modal-body">
                    <!-- 第一步：选择卡牌 -->
                    <view class="marketplace-cards">
                        <view
                            v-for="(card, idx) in pendingSettlement?.availableCards"
                            :key="card.id || idx"
                            class="mp-card"
                            :class="{
                                used: card.usedThisRound,
                                selected: marketplaceState.selectedCard?.id === card.id
                            }"
                            @click="selectMarketplaceCard(card)"
                        >
                            <text class="mp-card-name">{{ card.name }}</text>
                            <text class="mp-card-desc">{{ card.description }}</text>
                            <view v-if="card.usedThisRound" class="used-mask">本回合已被使用</view>
                        </view>
                    </view>

                    <!-- 第二步：展示对应选项 -->
                    <view
                        v-if="
                            marketplaceState.selectedCard &&
                            !marketplaceState.selectedCard.auto &&
                            marketplaceState.selectedCard.action?.type === 'exchange'
                        "
                        class="mp-options-panel animate-fade-in"
                    >
                        <text class="section-label">请选择执行方案：</text>
                        <view class="mp-options">
                            <view
                                v-for="(opt, optIdx) in marketplaceState.selectedCard.action?.options || []"
                                :key="optIdx"
                                class="mp-option-btn"
                                :class="{ active: marketplaceState.selectedOptionIndex === optIdx }"
                                @click="marketplaceState.selectedOptionIndex = optIdx"
                            >
                                <view
                                    class="custom-radio"
                                    :class="{ checked: marketplaceState.selectedOptionIndex === optIdx }"
                                ></view>
                                <text class="option-text">{{ formatOptionText(opt) }}</text>
                            </view>
                        </view>
                        <text v-if="!canConfirmMarketplace" class="error-hint">资源不足，无法执行该方案</text>
                    </view>
                </view>

                <view class="modal-footer">
                    <view class="modal-actions">
                        <button class="btn btn-ghost" @click="skipSettlementAction">放弃行动</button>
                        <button
                            class="btn btn-primary"
                            :disabled="!marketplaceState.selectedCard || !canConfirmMarketplace"
                            @click="confirmMarketplaceAction"
                        >
                            确认执行
                        </button>
                    </view>
                </view>
            </view>
        </view>

        <!-- 竞技场龙虾选择弹窗 -->
        <LobsterSelect
            :visible="showArenaModal"
            :challenger="onlineGameStore.currentArenaBattle?.challenger"
            :defender="onlineGameStore.currentArenaBattle?.defender"
            :player-id="onlineGameStore.playerId"
            :room-id="onlineGameStore.roomId"
            @both-ready="handleBothReady"
        />

        <!-- 竞技场弹窗重新打开按钮 -->
        <view v-if="showArenaReopen" class="arena-reopen-btn" @click="showArenaModal = true">
            <text>竞技场</text>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useOnlineGameStore, LOBSTER_GRADES } from '@stores/online-game.js'
import { usePlayerStore } from '@stores/player.js'
import { DEFAULT_SLOT_STYLE, getOccupiedSlotStyle, PLAYER_COLORS } from '@utils/slotConstants.js'
import { getLobsterGradeName, getNextLobsterGrade } from '@utils/gameUtils.js'
import LobsterSelect from './LobsterSelect.vue'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule
const onlineGameStore = useOnlineGameStore()
const playerStore = usePlayerStore()
const showLog = ref(false)
const showArenaModal = ref(false)

// ============ 结算阶段状态 ============
const pendingSettlement = computed(() => onlineGameStore.pendingSettlement)
// 强制监听 pendingSettlement 变化以确保响应式更新
const settlementActionCount = computed(() => pendingSettlement.value?.actionCount ?? 0)

watch(settlementActionCount, (newVal, oldVal) => {
    console.log('[Seafood Market] Action count changed:', oldVal, '->', newVal)
})
const showSettlementModal = computed(() => {
    return pendingSettlement.value !== null && onlineGameStore.currentPhase === 'settlement'
})

const breedingState = ref({
    lobsterIndex: -1,
    useSeaweed: false,
    royalCostType: '',
    selectedTitleId: ''
})

const marketplaceState = ref({
    selectedCard: null,
    selectedOptionIndex: 0
})

// ============ 海鲜市场价格计算 ============
const marketPrices = computed(() => {
    const lobsterCount = pendingSettlement.value?.marketLobsterCount ?? 4
    const base = Math.min(lobsterCount, 8)
    return {
        buyLobster: 2 + Math.floor(base / 2),
        sellLobster: Math.max(1, 4 - Math.floor(base / 2)),
        buyCage: 3,
        sellCage: 2,
        buySeaweed: 2 + Math.floor(base / 4),
        sellSeaweed: Math.max(1, 3 - Math.floor(base / 4))
    }
})

const canBuyLobster = computed(() => {
    const player = pendingSettlement.value?.player
    return (
        player &&
        player.coins >= marketPrices.value.buyLobster &&
        (pendingSettlement.value?.marketLobsterCount ?? 0) > 0
    )
})

const canSellLobster = computed(() => {
    const player = pendingSettlement.value?.player
    return (
        player &&
        player.lobsters &&
        player.lobsters.length > 0 &&
        (pendingSettlement.value?.marketLobsterCount ?? 0) < 8
    )
})

const canBuyCage = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.coins >= marketPrices.value.buyCage
})

const canSellCage = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.cages > 0
})

const canBuySeaweed = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.coins >= marketPrices.value.buySeaweed
})

const canSellSeaweed = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.seaweed >= 1
})

const canHire = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.coins >= 6
})

// ============ 养蛊区计算属性 ============
const targetLobster = computed(() => {
    if (breedingState.value.lobsterIndex === -1) return null
    const player = pendingSettlement.value?.player
    return player?.lobsters?.[breedingState.value.lobsterIndex]
})

const isSeaweedUseful = computed(() => {
    if (!targetLobster.value) return false
    return targetLobster.value.grade !== LOBSTER_GRADES.GRADE1 && targetLobster.value.grade !== LOBSTER_GRADES.ROYAL
})

const projectedGrade = computed(() => {
    if (!targetLobster.value) return null
    let grade = getNextLobsterGrade(targetLobster.value.grade)
    if (breedingState.value.useSeaweed) {
        grade = getNextLobsterGrade(grade)
    }
    return grade
})

const isUpgradingToRoyal = computed(() => {
    return (
        targetLobster.value &&
        targetLobster.value.grade !== LOBSTER_GRADES.ROYAL &&
        projectedGrade.value === LOBSTER_GRADES.ROYAL
    )
})

const canConfirmBreeding = computed(() => {
    if (!targetLobster.value) return false
    if (breedingState.value.useSeaweed && (pendingSettlement.value?.player?.seaweed ?? 0) < 1) return false
    if (isUpgradingToRoyal.value) {
        const player = pendingSettlement.value?.player
        if (breedingState.value.royalCostType === 'cage' && (player?.cages ?? 0) < 1) return false
        if (breedingState.value.royalCostType === 'coin' && (player?.coins ?? 0) < 3) return false
    }
    return true
})

// ============ 闹市区计算属性 ============
const canConfirmMarketplace = computed(() => {
    if (!marketplaceState.value.selectedCard) return false
    const card = marketplaceState.value.selectedCard
    const player = pendingSettlement.value?.player
    if (!player) return false

    if (!card.auto && card.action?.type === 'exchange') {
        const options = card.action?.options || []
        const opt = options[marketplaceState.value.selectedOptionIndex]
        if (!opt || !opt.cost) return false

        for (const [resType, resAmount] of Object.entries(opt.cost)) {
            if (resType === 'lobsters') {
                if ((player.lobsters?.length ?? 0) < resAmount) return false
            } else {
                if ((player[resType] ?? 0) < resAmount) return false
            }
        }
    }
    return true
})

// ============ 计算属性 ============
const isPlacementPhase = computed(() => onlineGameStore.currentPhase === 'placement')

const currentPlacementPlayerName = computed(() => {
    const player = playerStore.players[onlineGameStore.currentPlayerIndex]
    return player?.name || '未知'
})

const phaseText = computed(() => `${onlineGameStore.phaseText}阶段`)

const arenaBattleQueue = computed(() => onlineGameStore.arenaBattleQueue)

const showArenaReopen = computed(
    () => onlineGameStore.arenaPhase !== 'idle' && !showArenaModal.value && arenaBattleQueue.value.length > 0
)

// ============ 样式方法 ============

const getPlayerItemStyle = (playerId) => {
    if (!isCurrentPlacementPlayer(playerId)) return {}
    const color = PLAYER_COLORS[playerId]
    if (!color) return {}
    return {
        borderColor: color.bg,
        boxShadow: `0 0 10px ${color.bg}40`
    }
}

const getSlotStyle = (area, slotIndex) => {
    const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
    if (occupant != null) {
        const style = getOccupiedSlotStyle(occupant)
        return {
            background: style.background,
            borderColor: style.borderColor,
            opacity: style.opacity,
            color: style.color
        }
    }
    return {
        background: DEFAULT_SLOT_STYLE.background,
        opacity: isPlacementPhase.value ? 1 : 0.6
    }
}

// ============ 状态查询 ============

const isSlotOccupied = (area, slotIndex) => onlineGameStore.isSlotOccupied(area, slotIndex)

const getSlotOccupantLabel = (area, slotIndex) => {
    const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
    return occupant != null ? getOccupiedSlotStyle(occupant).playerLabel : null
}

const canPlaceOnSlot = (area, slotIndex) => {
    if (!isPlacementPhase.value) return false
    if (!onlineGameStore.isMyTurn) return false
    if (isSlotOccupied(area, slotIndex)) return false
    return true
}

const isCurrentPlacementPlayer = (playerId) => isPlacementPhase.value && onlineGameStore.currentPlayerIndex === playerId

const isMarketplaceAvailable = (slotIndex) => onlineGameStore.currentRound >= slotIndex + 1

// ============ 行动格描述 ============

const getShrimpCatchingSlotDesc = (i) => {
    const descs = ['1虾笼,夺起始,1次捕虾', '1虾笼,2次捕虾', '1金币,3次捕虾', '4次捕虾']
    return descs[i - 1]
}

const getSeafoodMarketSlotDesc = (i) => {
    const descs = ['1金币,2次交易', '3次交易', '1金币,3次交易', '2金币,3次交易']
    return descs[i - 1]
}

const getBreedingSlotDesc = (i) => {
    const descs = ['1草,1次培养', '2次培养', '1金币,2次培养', '3次培养']
    return descs[i - 1]
}

const getTributeSlotDesc = (i) => {
    if (i <= 3) {
        return i === 3 ? '第4回合可用,1次上供' : '1次上供'
    } else if (i <= 6) {
        return `挑战${i - 3}号位,1次上供`
    } else {
        return '1次上供'
    }
}

const getMarketplaceSlotDesc = (i) => {
    const descs = ['第2回合可用,1次闹市', '1金币,第3回合可用,1次闹市', '2金币,第4回合可用,1次闹市']
    return descs[i - 1]
}

// ============ 交互处理 ============

const showToast = (message, icon = 'none') => {
    uni.showToast({ title: message, icon, duration: 2000 })
}

const handleSlotClick = (area, slotIndex) => {
    if (!isPlacementPhase.value) {
        showToast('当前不是工放阶段，无法放置里长')
        return
    }
    if (!onlineGameStore.isMyTurn) {
        showToast('不是你的回合')
        return
    }
    if (isSlotOccupied(area, slotIndex)) {
        const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
        const occupantPlayer = playerStore.players.find((p) => p.id === occupant)
        showToast(`该行动格已被${occupantPlayer?.name || '未知玩家'}占用`)
        return
    }
    onlineGameStore.sendGameAction('placeHeadman', { areaIndex: area, slotIndex })
}

const handleNextPhase = () => {
    if (!onlineGameStore.isMyTurn) {
        showToast('不是你的回合')
        return
    }
    if (onlineGameStore.currentPhase === 'placement') {
        onlineGameStore.sendGameAction('nextPlayer', {})
    } else if (onlineGameStore.currentPhase === 'settlement') {
        onlineGameStore.sendGameAction('nextArea', {})
    }
}

// ============ 结算阶段交互处理 ============

const skipSettlementAction = () => {
    onlineGameStore.sendSettlementAction('skip')
    onlineGameStore.clearPendingSettlement()
}

// --- 捕虾区 ---
const chooseShrimpReward = (choice) => {
    onlineGameStore.sendSettlementAction('choose_either', { choice })
}

// --- 海鲜市场 ---
const doSeafoodTrade = (actionType) => {
    onlineGameStore.sendSettlementAction(actionType)
}

// --- 养蛊区 ---
const selectLobsterForBreeding = (index) => {
    breedingState.value.lobsterIndex = index
    breedingState.value.useSeaweed = false
    breedingState.value.royalCostType = ''
    breedingState.value.selectedTitleId = ''
}

const toggleSeaweed = () => {
    if (!isSeaweedUseful.value) {
        showToast('已达满级，无需消耗海草')
        return
    }
    const player = pendingSettlement.value?.player
    if ((player?.seaweed ?? 0) >= 1 || breedingState.value.useSeaweed) {
        breedingState.value.useSeaweed = !breedingState.value.useSeaweed
    } else {
        showToast('海草数量不足')
    }
}

const cancelBreedingAction = () => {
    breedingState.value.lobsterIndex = -1
}

const confirmBreedingAction = () => {
    if (!canConfirmBreeding.value) return
    const player = pendingSettlement.value?.player
    const lobster = targetLobster.value
    if (!player || !lobster) return

    onlineGameStore.sendSettlementAction('cultivateLobster', {
        lobsterIndex: breedingState.value.lobsterIndex,
        useSeaweed: breedingState.value.useSeaweed,
        royalCostType: isUpgradingToRoyal.value ? breedingState.value.royalCostType : null
    })

    breedingState.value.lobsterIndex = -1
    breedingState.value.useSeaweed = false
    breedingState.value.royalCostType = ''
}

// --- 闹市区 ---
const selectMarketplaceCard = (card) => {
    if (card.usedThisRound) return
    marketplaceState.value.selectedCard = card
    marketplaceState.value.selectedOptionIndex = 0
}

const formatOptionText = (opt) => {
    if (!opt || !opt.cost || !opt.reward) return ''
    const nameMap = { coins: '金币', seaweed: '海草', cages: '虾笼', lobsters: '龙虾', de: '德', wang: '望' }
    const costStrs = Object.entries(opt.cost).map(([k, v]) => `${v} ${nameMap[k] || k}`)
    const rewardStrs = Object.entries(opt.reward).map(([k, v]) => `${v} ${nameMap[k] || k}`)
    return `消耗 ${costStrs.join(' 和 ')} ➔ 获得 ${rewardStrs.join(' 和 ')}`
}

const confirmMarketplaceAction = () => {
    if (!canConfirmMarketplace.value) return
    const card = marketplaceState.value.selectedCard
    const optionIndex = marketplaceState.value.selectedOptionIndex
    const availableCards = pendingSettlement.value?.availableCards || []
    const cardIndex = availableCards.findIndex((c) => c.id === card.id)

    onlineGameStore.sendSettlementAction('executeDowntownAction', {
        cardIndex,
        optionIndex
    })

    marketplaceState.value.selectedCard = null
    marketplaceState.value.selectedOptionIndex = 0
}

// ============ 竞技场逻辑 ============

const checkBattleAvailability = () => {
    const battle = onlineGameStore.currentArenaBattle
    if (!battle) return { available: true }

    const challengerAvailable = onlineGameStore.getAvailableLobstersForBattle(battle.challenger?.id).length > 0
    const defenderAvailable = onlineGameStore.getAvailableLobstersForBattle(battle.defender?.id).length > 0

    if (!defenderAvailable && challengerAvailable) {
        return { available: false, reason: 'defender_no_lobster', battle }
    }
    if (!challengerAvailable) {
        return { available: false, reason: 'challenger_no_lobster', battle }
    }
    return { available: true }
}

const skipCurrentBattle = (reason, battle) => {
    if (reason === 'defender_no_lobster') {
        showToast(`${battle.defender?.name} 无可用龙虾，${battle.challenger?.name} 获胜并交换位置`)
        socketService._send('clientBattleAction', {
            action_type: 'noLobsterForfeit',
            challengeSlot: battle.slotIndex
        })
    } else {
        showToast(`${battle.challenger?.name} 无可用龙虾，跳过本场战斗`)
    }

    onlineGameStore.arenaBattleQueue.shift()
    if (onlineGameStore.arenaBattleQueue.length > 0) {
        onlineGameStore.setCurrentArenaBattle(0)
    }
}

const shouldShowArena = () => {
    if (arenaBattleQueue.value.length === 0) return false
    if (onlineGameStore.currentPhase !== 'settlement') return false
    if (onlineGameStore.arenaPhase !== 'idle') return false

    // 如果有非上供区的 pending settlement，优先显示结算UI
    const pending = onlineGameStore.pendingSettlement
    if (pending && pending.areaType && pending.areaType !== 'tribute') {
        return false
    }

    const check = checkBattleAvailability()
    if (!check.available) {
        skipCurrentBattle(check.reason, check.battle)
        return false
    }
    return true
}

const openArenaModal = () => {
    onlineGameStore.setCurrentArenaBattle(0)
    showArenaModal.value = true
}

watch(
    arenaBattleQueue,
    () => {
        if (shouldShowArena()) openArenaModal()
    },
    { deep: true }
)

watch(
    () => onlineGameStore.currentPhase,
    () => {
        if (shouldShowArena()) openArenaModal()
    }
)

const buildArenaPlayerData = (player, selectedLobster, defaultColor) => ({
    id: player.id,
    name: player.name,
    lobsterId: selectedLobster.id,
    lobsterName: selectedLobster.name,
    lobsterDesc: selectedLobster.description,
    color: PLAYER_COLORS[player.id]?.bg || defaultColor
})

const navigateToArena = (player1Data, player2Data) => {
    if (onlineGameStore.arenaBattleQueue.length > 0) {
        onlineGameStore.arenaBattleQueue.shift()
    }

    const storageKey = `arenaBattleQueue_${onlineGameStore.roomId}`
    uni.setStorageSync(storageKey, onlineGameStore.arenaBattleQueue)

    const battle = onlineGameStore.currentArenaBattle
    const url = `/pages/arena/arena?player1=${encodeURIComponent(JSON.stringify(player1Data))}&player2=${encodeURIComponent(JSON.stringify(player2Data))}&roomId=${onlineGameStore.roomId}&playerId=${onlineGameStore.playerId}&challengeSlot=${battle?.slotIndex}`

    uni.navigateTo({ url })
}

const handleBothReady = ({ challenger, defender, challengerLobster, defenderLobster }) => {
    showArenaModal.value = false
    onlineGameStore.setArenaPhase('idle')

    const player1Data = buildArenaPlayerData(challenger, challengerLobster, '#FF6B6B')
    const player2Data = buildArenaPlayerData(defender, defenderLobster, '#4ECDC4')

    navigateToArena(player1Data, player2Data)
}

// ============ 生命周期 ============

const parsePageOptions = () => {
    const pages = getCurrentPages()
    return pages[pages.length - 1].options || {}
}

const restoreArenaQueue = (roomId) => {
    const storageKey = `arenaBattleQueue_${roomId}`
    const savedQueue = uni.getStorageSync(storageKey)
    if (savedQueue?.length > 0) {
        onlineGameStore.arenaBattleQueue = savedQueue
        uni.removeStorageSync(storageKey)
        return true
    }
    return false
}

const autoContinueAfterBattles = () => {
    if (onlineGameStore.currentPhase === 'settlement' && onlineGameStore.arenaBattleQueue.length === 0) {
        const lastArea = onlineGameStore.gameState?.areas
        if (lastArea) {
            const tributeSlots = lastArea.tribute?.slots || []
            const hasBattles = tributeSlots.some((slot) => slot !== null)
            if (hasBattles) {
                onlineGameStore.sendGameAction('nextArea', {})
            }
        }
    }
}

const initGameState = (options) => {
    if (options.gameState) {
        try {
            const gs = JSON.parse(decodeURIComponent(options.gameState))
            onlineGameStore.updateGameState(gs)
        } catch {
            // ignore parse errors
        }
    }
}

const initSocket = (roomId, playerId) => {
    const isAlreadyConnected = onlineGameStore.isConnected && onlineGameStore.roomId === roomId
    if (!isAlreadyConnected) {
        socketService.setRoomContext(roomId, playerId)
        socketService.connect(roomId, playerId)
    }
}

onMounted(() => {
    const options = parsePageOptions()
    const roomId = options.roomId || uni.getStorageSync('roomId') || ''
    const playerId = parseInt(options.playerId) || uni.getStorageSync('playerId')

    if (!roomId || playerId === null) {
        uni.redirectTo({ url: '/pages/lobby/lobby' })
        return
    }

    const hadQueue = restoreArenaQueue(roomId)
    initGameState(options)
    onlineGameStore.initOnlineMode(roomId, playerId)
    initSocket(roomId, playerId)

    if (hadQueue && onlineGameStore.arenaBattleQueue.length === 0) {
        setTimeout(() => autoContinueAfterBattles(), 1000)
    }
})

onUnmounted(() => {
    onlineGameStore.cleanupListeners()
})
</script>

<style scoped>
.arena-reopen-btn {
    position: fixed;
    bottom: 120px;
    right: 20px;
    background: #e94560;
    color: #fff;
    padding: 12px 20px;
    border-radius: 24px;
    font-size: 15px;
    font-weight: bold;
    z-index: 999;
    box-shadow: 0 4px 12px rgba(233, 69, 96, 0.4);
    animation: arena-pulse 2s ease-in-out infinite;
}

@keyframes arena-pulse {
    0%,
    100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.08);
    }
}

/* ============ 结算弹窗通用样式 ============ */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: #1a1a2e;
    border-radius: 16px;
    width: 90%;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.modal-header {
    padding: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-title-group {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.modal-title {
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
}

.modal-subtitle {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
}

.modal-subtitle .highlight {
    color: #4ecdc4;
    font-weight: bold;
}

.modal-body {
    padding: 20px;
}

.modal-footer {
    padding: 16px 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-actions {
    display: flex;
    gap: 12px;
    justify-content: space-between;
}

/* 按钮通用样式 */
.btn {
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: #4ecdc4;
    color: #1a1a2e;
    font-weight: bold;
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
}

.btn-ghost {
    background: transparent;
    color: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-outline {
    background: transparent;
    color: #4ecdc4;
    border: 1px solid #4ecdc4;
    padding: 10px 16px;
    font-size: 13px;
}

.btn-outline:disabled {
    opacity: 0.4;
    border-color: rgba(78, 205, 196, 0.3);
    color: rgba(78, 205, 196, 0.4);
}

.w-full {
    width: 100%;
}

/* ============ 捕虾区弹窗 ============ */
.shrimp-modal .indicator-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;
}

.shrimp-modal .indicator-icon {
    font-size: 48px;
    margin-bottom: 16px;
}

.shrimp-modal .indicator-text {
    color: #fff;
    font-size: 16px;
    text-align: center;
}

.shrimp-modal .choice-buttons {
    display: flex;
    gap: 16px;
    margin-top: 20px;
}

.shrimp-modal .btn-choice {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    padding: 16px;
    font-size: 16px;
    border: 2px solid rgba(78, 205, 196, 0.3);
}

.shrimp-modal .btn-choice:hover {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.1);
}

/* ============ 海鲜市场弹窗 ============ */
.seafood-market-modal .market-display-board {
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.05);
}

.seafood-market-modal .price-title {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
    font-weight: bold;
    display: block;
    margin-bottom: 8px;
}

.seafood-market-modal .price-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.seafood-market-modal .price-tags text {
    color: rgba(255, 255, 255, 0.6);
    font-size: 12px;
    background: rgba(255, 255, 255, 0.05);
    padding: 4px 8px;
    border-radius: 4px;
}

.seafood-market-modal .trade-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.seafood-market-modal .trade-row {
    display: flex;
    gap: 12px;
}

.seafood-market-modal .trade-row .btn {
    flex: 1;
}

/* ============ 养蛊区弹窗 ============ */
.breeding-modal .lobster-selection {
    display: flex;
    flex-direction: column;
}

.breeding-modal .section-label {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
    margin-bottom: 12px;
}

.breeding-modal .lobster-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.breeding-modal .lobster-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow: hidden;
}

.breeding-modal .lobster-card.max-royal {
    opacity: 0.6;
}

.breeding-modal .lobster-icon {
    font-size: 32px;
    margin-bottom: 8px;
}

.breeding-modal .lobster-grade {
    color: #4ecdc4;
    font-size: 12px;
    font-weight: bold;
}

.breeding-modal .lobster-title {
    color: rgba(255, 255, 255, 0.6);
    font-size: 11px;
    margin-top: 4px;
}

.breeding-modal .max-grade-mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 14px;
    font-weight: bold;
}

.breeding-modal .empty-hint {
    color: rgba(255, 255, 255, 0.4);
    text-align: center;
    padding: 20px;
}

.breeding-modal .breeding-action-panel {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.breeding-modal .upgrade-path {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
}

.breeding-modal .grade-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
    padding: 8px 16px;
    border-radius: 8px;
}

.breeding-modal .grade-box text {
    color: rgba(255, 255, 255, 0.5);
    font-size: 11px;
}

.breeding-modal .grade-box .val {
    color: #fff;
    font-size: 14px;
    font-weight: bold;
    margin-top: 4px;
}

.breeding-modal .grade-box .val.highlight {
    color: #4ecdc4;
}

.breeding-modal .arrow {
    color: #4ecdc4;
    font-size: 20px;
}

.breeding-modal .options-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.breeding-modal .checkbox-wrapper {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
}

.breeding-modal .checkbox-wrapper.disabled {
    opacity: 0.5;
}

.breeding-modal .custom-checkbox {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 4px;
}

.breeding-modal .custom-checkbox.checked {
    background: #4ecdc4;
    border-color: #4ecdc4;
}

.breeding-modal .checkbox-text {
    color: rgba(255, 255, 255, 0.7);
    font-size: 13px;
}

.breeding-modal .royal-requirements {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px;
    background: rgba(255, 215, 0, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(255, 215, 0, 0.2);
}

.breeding-modal .req-title {
    color: rgba(255, 255, 255, 0.8);
    font-size: 13px;
    font-weight: bold;
}

.breeding-modal .cost-options {
    display: flex;
    gap: 8px;
}

.breeding-modal .cost-btn {
    flex: 1;
    padding: 10px;
    background: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    font-size: 12px;
}

.breeding-modal .cost-btn.active {
    background: rgba(78, 205, 196, 0.2);
    border-color: #4ecdc4;
    color: #4ecdc4;
}

.breeding-modal .cost-btn:disabled {
    opacity: 0.4;
}

.breeding-modal .modal-actions {
    display: flex;
    gap: 12px;
}

/* ============ 闹市区弹窗 ============ */
.marketplace-modal .marketplace-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.marketplace-modal .mp-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    position: relative;
    overflow: hidden;
}

.marketplace-modal .mp-card.selected {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.1);
}

.marketplace-modal .mp-card.used {
    opacity: 0.5;
}

.marketplace-modal .mp-card-name {
    color: #fff;
    font-size: 14px;
    font-weight: bold;
    display: block;
    margin-bottom: 4px;
}

.marketplace-modal .mp-card-desc {
    color: rgba(255, 255, 255, 0.5);
    font-size: 11px;
    display: block;
}

.marketplace-modal .used-mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 12px;
    font-weight: bold;
}

.marketplace-modal .mp-options-panel {
    margin-top: 16px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
}

.marketplace-modal .mp-options {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
}

.marketplace-modal .mp-option-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

.marketplace-modal .mp-option-btn.active {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.1);
}

.marketplace-modal .custom-radio {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
}

.marketplace-modal .custom-radio.checked {
    border-color: #4ecdc4;
    background: #4ecdc4;
}

.marketplace-modal .option-text {
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
}

.marketplace-modal .error-hint {
    color: #e94560;
    font-size: 12px;
    margin-top: 8px;
    display: block;
}

/* 动画 */
.animate-fade-in {
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
