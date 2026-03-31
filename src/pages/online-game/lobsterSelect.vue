<template>
    <view v-if="visible" class="modal-overlay" @click="handleOverlayClick">
        <view class="modal-container" @click.stop>
            <view class="modal-header">
                <text class="modal-title">竞技场对决</text>
                <text class="modal-subtitle">{{ subtitle }}</text>
            </view>

            <view class="battle-info">
                <view class="player-info" :class="{ active: isChallenger }">
                    <text class="player-label">挑战者</text>
                    <text class="player-name">{{ challenger?.name }}</text>
                    <view v-if="challengerReady" class="ready-badge">已选择</view>
                </view>
                <text class="vs-text">VS</text>
                <view class="player-info" :class="{ active: isDefender }">
                    <text class="player-label">被挑战者</text>
                    <text class="player-name">{{ defender?.name }}</text>
                    <view v-if="defenderReady" class="ready-badge">已选择</view>
                </view>
            </view>

            <!-- Phase 1: Selecting - 战斗双方选龙虾 -->
            <view v-if="localPhase === 'selecting'" class="selection-area">
                <view v-if="isChallenger || isDefender" class="lobster-selection">
                    <text class="selection-title">选择你的出战龙虾</text>
                    <view class="lobster-list">
                        <view
                            v-for="(lobster, index) in myLobsters"
                            :key="lobster.id"
                            :class="['lobster-item', { selected: selectedIndex === index }]"
                            @click="selectLobster(index)"
                        >
                            <view class="lobster-icon">🦞</view>
                            <text class="lobster-name">{{ lobster.name }}</text>
                        </view>
                        <view v-if="myLobsters.length === 0" class="no-lobster">
                            <text>没有可用的龙虾</text>
                        </view>
                    </view>
                </view>
                <view v-else class="spectator-view">
                    <text class="spectator-text">你是观战者，请等待双方选择龙虾...</text>
                </view>
                <view v-if="isChallenger || isDefender" class="modal-actions">
                    <button
                        class="action-btn confirm-btn"
                        :disabled="!canConfirm || hasConfirmed"
                        @click="handleConfirm"
                    >
                        {{ hasConfirmed ? '等待对方...' : '确认选择' }}
                    </button>
                </view>
            </view>

            <!-- Phase 2: Betting - 观战者投注 -->
            <view v-if="localPhase === 'betting'" class="betting-area">
                <view v-if="isSpectator" class="betting-selection">
                    <text class="selection-title">选择你要支持的龙虾（1金币）</text>
                    <view class="betting-fighters">
                        <view class="betting-fighter-card" @click="selectBetTarget('challenger')">
                            <text class="bf-label">{{ challenger?.name }}</text>
                            <text class="bf-lobster">{{ store.challengerLobster?.name || '龙虾' }}</text>
                            <view :class="['bf-select', { selected: betTarget === 'challenger', disabled: !canBet }]">
                                <text>投1金币</text>
                            </view>
                        </view>
                        <text class="vs-text">VS</text>
                        <view class="betting-fighter-card" @click="selectBetTarget('defender')">
                            <text class="bf-label">{{ defender?.name }}</text>
                            <text class="bf-lobster">{{ store.defenderLobster?.name || '龙虾' }}</text>
                            <view :class="['bf-select', { selected: betTarget === 'defender', disabled: !canBet }]">
                                <text>投1金币</text>
                            </view>
                        </view>
                    </view>
                    <view v-if="!canBet" class="gold-warning">
                        <text>金币不足，无法投注</text>
                    </view>
                    <view class="modal-actions">
                        <button class="action-btn confirm-btn" :disabled="hasBet || !canBet" @click="handleBet">
                            {{ hasBet ? '已投注，等待其他观战者...' : '确认投注' }}
                        </button>
                        <button class="action-btn skip-btn" :disabled="hasBet" @click="handleSkipBet">跳过投注</button>
                    </view>
                </view>
                <view v-else class="spectator-view">
                    <text class="spectator-text">龙虾已选定！等待观战者投注...</text>
                    <view class="lobster-preview">
                        <view class="preview-card">
                            <text class="preview-label">{{ challenger?.name }}</text>
                            <text class="preview-lobster">{{ store.challengerLobster?.name || '' }}</text>
                        </view>
                        <text class="vs-text">VS</text>
                        <view class="preview-card">
                            <text class="preview-label">{{ defender?.name }}</text>
                            <text class="preview-lobster">{{ store.defenderLobster?.name || '' }}</text>
                        </view>
                    </view>
                </view>
            </view>

            <!-- Phase 3: Ready - 投注结果 + 倒计时 -->
            <view v-if="localPhase === 'ready'" class="ready-area">
                <text class="ready-title">投注结果</text>
                <view class="bet-results">
                    <view v-for="(bet, pid) in store.spectatorBets" :key="pid" class="bet-result-item">
                        <text class="bet-player-name">{{ getPlayerName(pid) }}</text>
                        <text class="bet-detail" v-if="bet.amount > 0">
                            投了 {{ getBetTargetName(bet.targetFighterId) }} {{ bet.amount }}金币
                        </text>
                        <text class="bet-detail" v-else>跳过投注</text>
                    </view>
                    <view v-if="Object.keys(store.spectatorBets).length === 0" class="bet-result-item">
                        <text class="bet-detail">无观战者投注</text>
                    </view>
                </view>
                <text class="countdown-text">进入竞技场：{{ countdown }}秒</text>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useOnlineGameStore } from '@stores/online-game.js'
import { usePlayerStore } from '@stores/player.js'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule
const store = useOnlineGameStore()
const playerStore = usePlayerStore()

const props = defineProps({
    visible: {
        type: Boolean,
        default: false
    },
    challenger: {
        type: Object,
        default: null
    },
    defender: {
        type: Object,
        default: null
    },
    playerId: {
        type: [Number, String],
        default: null
    },
    roomId: {
        type: String,
        default: ''
    }
})

const emit = defineEmits(['confirm', 'cancel', 'bothReady'])

// ============ 本地状态 ============
const localPhase = ref('selecting')
const selectedIndex = ref(-1)
const hasConfirmed = ref(false)
const hasBet = ref(false)
const betTarget = ref('')
const countdown = ref(5)
let countdownTimer = null
let currentBattleId = ''

// 从 store 读取双方选择状态
const challengerReady = computed(() => store.challengerReady)
const defenderReady = computed(() => store.defenderReady)

// ============ 身份判断 ============
const isChallenger = computed(() => {
    if (props.playerId === null || !props.challenger) return false
    return String(props.challenger.id) === String(props.playerId)
})

const isDefender = computed(() => {
    if (props.playerId === null || !props.defender) return false
    return String(props.defender.id) === String(props.playerId)
})

const isFighter = computed(() => isChallenger.value || isDefender.value)
const isSpectator = computed(() => !isFighter.value)

// ============ 计算属性 ============
const myLobsters = computed(() => {
    if (isFighter.value) {
        const player = isChallenger.value ? props.challenger : props.defender
        const validLobsters = player?.lobsters?.filter((l) => l && l.id && l.id !== 'normal') || []
        const titleCards = player?.titleCards?.filter((t) => t && t.id) || []
        return [...validLobsters, ...titleCards]
    }
    return []
})

const canConfirm = computed(() => selectedIndex.value >= 0)
const canBet = computed(() => {
    const myPlayer = playerStore.getPlayerById(store.playerId)
    return (myPlayer?.coins || 0) >= 1
})

const subtitle = computed(() => {
    if (localPhase.value === 'selecting') {
        if (isChallenger.value) return '你是挑战者，请选择出战龙虾'
        if (isDefender.value) return '你是被挑战者，请选择出战龙虾'
        return '观战模式'
    }
    if (localPhase.value === 'betting') {
        if (isSpectator.value) return '请选择你要支持的龙虾'
        return '等待观战者投注...'
    }
    if (localPhase.value === 'ready') {
        return '即将进入竞技场'
    }
    return ''
})

// ============ 选龙虾逻辑 ============
const selectLobster = (index) => {
    if (hasConfirmed.value) return
    selectedIndex.value = index
}

const handleConfirm = () => {
    if (!canConfirm.value || hasConfirmed.value) return

    const selectedLobster = myLobsters.value[selectedIndex.value]
    hasConfirmed.value = true

    // 构建 battle context
    const battle = store.arenaBattleQueue[0]
    if (!battle) return
    const spectators = store.players
        .filter((p) => p.id !== battle.challengerId && p.id !== battle.defenderId)
        .map((p) => p.id)

    socketService._send('lobsterSelected', {
        roomId: props.roomId,
        playerId: props.playerId,
        lobster: selectedLobster,
        battleId: currentBattleId,
        challengerId: battle.challengerId,
        defenderId: battle.defenderId,
        spectators
    })

    // 本地标记自己已选择（写入 store）
    if (isChallenger.value) {
        store.challengerReady = true
        store.challengerSelectedLobster = selectedLobster
    } else if (isDefender.value) {
        store.defenderReady = true
        store.defenderSelectedLobster = selectedLobster
    }
}

// ============ 投注逻辑 ============
const selectBetTarget = (target) => {
    if (hasBet.value) return
    betTarget.value = target
}

const handleBet = () => {
    if (hasBet.value || !betTarget.value) return
    hasBet.value = true

    const battle = store.arenaBattleQueue[0]
    if (!battle) return
    const targetFighterId = betTarget.value === 'challenger' ? battle.challengerId : battle.defenderId

    socketService._send('spectatorBet', {
        roomId: props.roomId,
        playerId: props.playerId,
        battleId: currentBattleId,
        betAmount: 1,
        targetFighterId
    })
}

const handleSkipBet = () => {
    if (hasBet.value) return
    hasBet.value = true

    socketService._send('spectatorBet', {
        roomId: props.roomId,
        playerId: props.playerId,
        battleId: currentBattleId,
        betAmount: 0,
        targetFighterId: null
    })
}

// ============ Ready 阶段辅助 ============
const getPlayerName = (playerId) => {
    const player = store.players.find((p) => String(p.id) === String(playerId))
    return player?.name || '未知玩家'
}

const getBetTargetName = (targetFighterId) => {
    if (String(targetFighterId) === String(props.challenger?.id)) return props.challenger?.name || '挑战者'
    if (String(targetFighterId) === String(props.defender?.id)) return props.defender?.name || '被挑战者'
    return '未知'
}

const startCountdown = () => {
    countdown.value = 5
    countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
            clearInterval(countdownTimer)
            countdownTimer = null
            emit('bothReady', {
                challenger: props.challenger,
                defender: props.defender,
                challengerLobster: store.challengerSelectedLobster || store.challengerLobster,
                defenderLobster: store.defenderSelectedLobster || store.defenderLobster
            })
        }
    }, 1000)
}

// ============ 监听 store 阶段变化 ============
watch(
    () => store.arenaPhase,
    (newPhase) => {
        if (newPhase === 'betting') {
            localPhase.value = 'betting'
        } else if (newPhase === 'ready') {
            localPhase.value = 'ready'
            startCountdown()
        }
    }
)

// ============ 弹窗开关 ============
watch(
    () => props.visible,
    (newVal) => {
        if (newVal) {
            // 重置所有状态
            localPhase.value = 'selecting'
            selectedIndex.value = -1
            hasConfirmed.value = false
            store.challengerReady = false
            store.defenderReady = false
            store.challengerSelectedLobster = null
            store.defenderSelectedLobster = null
            hasBet.value = false
            betTarget.value = ''
            countdown.value = 5
            if (countdownTimer) {
                clearInterval(countdownTimer)
                countdownTimer = null
            }
            // 生成一致的 battleId
            const battle = store.arenaBattleQueue[0]
            currentBattleId = battle ? `${store.roomId}_${battle.slotIndex}` : ''
        } else {
            if (countdownTimer) {
                clearInterval(countdownTimer)
                countdownTimer = null
            }
        }
    }
)

onMounted(() => {
    // store 已统一管理 lobsterSelected 监听
})

onUnmounted(() => {
    if (countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
    }
})

const handleOverlayClick = () => {
    // 点击遮罩层不关闭
}
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-container {
    background: #1a1a2e;
    border-radius: 16px;
    padding: 24px;
    width: 90%;
    max-width: 400px;
    max-height: 80vh;
    overflow-y: auto;
}

.modal-header {
    text-align: center;
    margin-bottom: 20px;
}

.modal-title {
    font-size: 22px;
    font-weight: bold;
    color: #e94560;
    display: block;
}

.modal-subtitle {
    font-size: 14px;
    color: #a0a0b0;
    margin-top: 8px;
    display: block;
}

.battle-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.player-info {
    flex: 1;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    background: #16213e;
    position: relative;
}

.player-info.active {
    border: 2px solid #e94560;
    box-shadow: 0 0 10px rgba(233, 69, 96, 0.3);
}

.player-label {
    font-size: 12px;
    color: #a0a0b0;
    display: block;
}

.player-name {
    font-size: 16px;
    font-weight: bold;
    color: #fff;
    display: block;
    margin-top: 4px;
}

.ready-badge {
    position: absolute;
    top: -8px;
    right: -8px;
    background: #0f3460;
    color: #4ecca3;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
}

.vs-text {
    font-size: 18px;
    font-weight: bold;
    color: #e94560;
    margin: 0 10px;
}

/* Selecting phase */
.selection-area {
    margin-top: 10px;
}

.selection-title {
    font-size: 14px;
    color: #a0a0b0;
    display: block;
    text-align: center;
    margin-bottom: 12px;
}

.lobster-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
}

.lobster-item {
    background: #16213e;
    border: 2px solid #0f3460;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
    cursor: pointer;
    min-width: 80px;
    transition: all 0.2s;
}

.lobster-item.selected {
    border-color: #e94560;
    background: rgba(233, 69, 96, 0.15);
}

.lobster-icon {
    font-size: 28px;
}

.lobster-name {
    font-size: 12px;
    color: #fff;
    margin-top: 4px;
    display: block;
}

.no-lobster {
    text-align: center;
    padding: 20px;
    color: #a0a0b0;
}

.spectator-view {
    text-align: center;
    padding: 20px;
}

.spectator-text {
    font-size: 14px;
    color: #a0a0b0;
}

/* Betting phase */
.betting-area {
    margin-top: 10px;
}

.betting-selection .selection-title {
    margin-bottom: 16px;
}

.betting-fighters {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.betting-fighter-card {
    flex: 1;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    background: #16213e;
}

.bf-label {
    font-size: 12px;
    color: #a0a0b0;
    display: block;
}

.bf-lobster {
    font-size: 14px;
    font-weight: bold;
    color: #fff;
    display: block;
    margin: 4px 0 8px;
}

.bf-select {
    background: #0f3460;
    color: #a0a0b0;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
}

.bf-select.selected {
    background: #e94560;
    color: #fff;
}

.bf-select.disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.gold-warning {
    text-align: center;
    margin: 8px 0;
    padding: 6px;
    background: rgba(233, 69, 96, 0.15);
    border-radius: 6px;
}

.gold-warning text {
    font-size: 13px;
    color: #e94560;
}

.lobster-preview {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
}

.preview-card {
    flex: 1;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    background: #16213e;
}

.preview-label {
    font-size: 12px;
    color: #a0a0b0;
    display: block;
}

.preview-lobster {
    font-size: 14px;
    font-weight: bold;
    color: #4ecca3;
    display: block;
    margin-top: 4px;
}

/* Ready phase */
.ready-area {
    margin-top: 10px;
    text-align: center;
}

.ready-title {
    font-size: 16px;
    font-weight: bold;
    color: #4ecca3;
    display: block;
    margin-bottom: 16px;
}

.bet-results {
    margin-bottom: 20px;
}

.bet-result-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 12px;
    margin-bottom: 6px;
    background: #16213e;
    border-radius: 6px;
}

.bet-player-name {
    font-size: 13px;
    color: #fff;
}

.bet-detail {
    font-size: 13px;
    color: #a0a0b0;
}

.countdown-text {
    font-size: 28px;
    font-weight: bold;
    color: #e94560;
    display: block;
    margin-top: 10px;
}

/* Actions */
.modal-actions {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.action-btn {
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: bold;
    border: none;
    cursor: pointer;
}

.action-btn[disabled] {
    opacity: 0.5;
    cursor: not-allowed;
}

.confirm-btn {
    background: #e94560;
    color: #fff;
}

.skip-btn {
    background: #0f3460;
    color: #a0a0b0;
}
</style>
