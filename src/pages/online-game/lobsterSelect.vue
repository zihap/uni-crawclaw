<template>
    <view v-if="visible" class="modal-overlay" @click.stop>
        <view class="modal-container" @click.stop>
            <view class="modal-header">
                <text class="modal-title">竞技场对决</text>
                <view class="title-line"></view>
                <text class="modal-subtitle">{{ subtitle }}</text>
            </view>

            <view class="battle-info">
                <view class="player-info" :class="{ active: isChallenger }">
                    <text class="player-label">挑战者</text>
                    <text class="player-name">{{ challenger?.name }}</text>
                    <view v-if="store.challengerReady" class="ready-badge">已选择</view>
                </view>
                <text class="vs-text">VS</text>
                <view class="player-info" :class="{ active: isDefender }">
                    <text class="player-label">被挑战者</text>
                    <text class="player-name">{{ defender?.name }}</text>
                    <view v-if="store.defenderReady" class="ready-badge">已选择</view>
                </view>
            </view>

            <!-- Phase 1: Selecting -->
            <view v-if="localPhase === 'selecting'" class="selection-area">
                <view v-if="isChallenger || isDefender" class="lobster-selection">
                    <text class="selection-title">选择你的出战龙虾</text>
                    <view class="lobster-list">
                        <view
                            v-for="(lobster, index) in myLobsters"
                            :key="lobster.id"
                            :class="['lobster-item', { selected: selectedIndex === index, used: lobster.used || lobster.grade === 'normal'}]"
                            @click="selectLobster(index)"
                        >
                            <view class="lobster-icon">🦞</view>
                            <text class="lobster-name">{{ lobster.name || getLobsterGradeName(lobster.grade) }}</text>
                            <view v-if="lobster.used" class="used-badge">已参战</view>
                            <view v-if="lobster.grade === 'normal'" class="used-badge">无法参战</view>
                        </view>
                    </view>
                </view>
                <view v-if="!isFighter" class="spectator-view">
                    <text class="spectator-text">你是观战者，请等待双方选择龙虾...</text>
                </view>
                <view v-if="isChallenger || isDefender" class="modal-actions">
                    <button
                        class="action-btn confirm-btn"
                        :disabled="hasConfirmed || (availableLobsters.length > 0 && selectedIndex < 0)"
                        @click="availableLobsters.length === 0 ? handleForfeit() : handleConfirm()"
                    >
                        {{ hasConfirmed ? '等待对方...' : availableLobsters.length === 0 ? '认输' : '确认选择' }}
                    </button>
                </view>
            </view>

            <!-- Phase 2: Betting -->
            <view v-if="localPhase === 'betting'" class="betting-area">
                <view v-if="!isFighter" class="betting-selection">
                    <text class="selection-title">选择你要支持的龙虾（1金币）</text>
                    <view class="betting-fighters">
                        <view class="betting-fighter-card" @click="selectBetTarget('challenger')">
                            <text class="bf-label">{{ challenger?.name }}</text>
                            <text class="bf-lobster">{{ challengerLobsterInfo?.name || '-' }}</text>
                            <text class="fighter-skill" v-if="store.challengerSelectedLobster?.skill">
                                技能：{{ store.challengerSelectedLobster?.skill.description }}
                            </text>
                            <view :class="['bf-select', { selected: betTarget === 'challenger', disabled: !canBet }]">
                                <text>投1金币</text>
                            </view>
                        </view>
                        <text class="vs-text">VS</text>
                        <view class="betting-fighter-card" @click="selectBetTarget('defender')">
                            <text class="bf-label">{{ defender?.name }}</text>
                            <text class="bf-lobster">{{ defenderLobsterInfo?.name || '-' }}</text>
                            <text class="fighter-skill" v-if="store.defenderSelectedLobster?.skill">
                                技能：{{ store.defenderSelectedLobster?.skill.description }}
                            </text>
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
                <view v-if="isFighter" class="spectator-view">
                    <text class="spectator-text">龙虾已选定！等待观战者投注...</text>
                    <view class="lobster-preview">
                        <view class="preview-card">
                            <text class="preview-label">{{ challenger?.name }}</text>
                            <text class="preview-lobster">{{ challengerLobsterInfo?.name || '-' }}</text>
                            <text class="fighter-skill" v-if="store.challengerSelectedLobster?.skill">
                                技能：{{ store.challengerSelectedLobster?.skill.description }}
                            </text>
                        </view>
                        <text class="vs-text">VS</text>
                        <view class="preview-card">
                            <text class="preview-label">{{ defender?.name }}</text>
                            <text class="preview-lobster">{{ defenderLobsterInfo?.name || '-' }}</text>
                            <text class="fighter-skill" v-if="store.defenderSelectedLobster?.skill">
                                技能：{{ store.defenderSelectedLobster?.skill.description }}
                            </text>
                        </view>
                    </view>
                </view>
            </view>

            <!-- Phase 3: Ready -->
            <view v-if="localPhase === 'ready'" class="ready-area">
                <view class="fighters-preview">
                    <view class="fighter-card challenger">
                        <text class="fighter-label">挑战者</text>
                        <text class="fighter-name">{{ challengerLobsterInfo?.name || '-' }}</text>
                        <text class="fighter-skill" v-if="store.challengerSelectedLobster?.skill">
                            技能：{{ store.challengerSelectedLobster?.skill.description }}
                        </text>
                    </view>
                    <text class="vs-text">VS</text>
                    <view class="fighter-card defender">
                        <text class="fighter-label">被挑战者</text>
                        <text class="fighter-name">{{ defenderLobsterInfo?.name || '-' }}</text>
                        <text class="fighter-skill" v-if="store.defenderSelectedLobster?.skill">
                            技能：{{ store.defenderSelectedLobster?.skill.description }}
                        </text>
                    </view>
                </view>
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
import { ref, computed, watch, onUnmounted } from 'vue'
import { useOnlineGameStore } from '@stores/online-game.js'
import { usePlayerStore } from '@stores/player.js'
import { socketService } from '@utils/socket.js'
import { getSkill } from '@data/cards.js'
import { getLobsterGradeName } from '@utils/gameUtils.js'

const store = useOnlineGameStore()
const playerStore = usePlayerStore()

const props = defineProps({
    visible: { type: Boolean, default: false },
    challenger: { type: Object, default: null },
    defender: { type: Object, default: null },
    playerId: { type: [Number, String], default: null },
    roomId: { type: String, default: '' }
})

const emit = defineEmits(['bothReady', 'forfeit'])

const localPhase = ref('selecting')
const selectedIndex = ref(-1)
const hasConfirmed = ref(false)
const hasBet = ref(false)
const betTarget = ref('')
const countdown = ref(5)
let countdownTimer = null
let currentBattleId = ''

const isChallenger = computed(
    () => props.playerId !== null && props.challenger && String(props.challenger.id) === String(props.playerId)
)

const isDefender = computed(
    () => props.playerId !== null && props.defender && String(props.defender.id) === String(props.playerId)
)

const isFighter = computed(() => isChallenger.value || isDefender.value)

const myLobsters = computed(() => {
    if (!isFighter.value) return []
    const player = isChallenger.value ? props.challenger : props.defender
    return [...player?.lobsters, ...player?.titleCards]
})

const availableLobsters = computed(() => {
    return myLobsters.value.filter((l) => !l.used && l.grade !== 'normal')
})

const challengerLobsterInfo = computed(() => {
    const lobster = store.challengerSelectedLobster || store.challengerLobster
    if (!lobster) return null
    let skill = getSkill(lobster.grade)
    if (lobster.skill) {
        skill = lobster.skill
    }
    return {
        name: lobster.name || getLobsterGradeName(lobster.grade),
        skillDesc: skill?.description || ''
    }
})

const defenderLobsterInfo = computed(() => {
    const lobster = store.defenderSelectedLobster || store.defenderLobster
    if (!lobster) return null
    let skill = getSkill(lobster.grade)
    if (lobster.skill) {
        skill = lobster.skill
    }
    return {
        name: lobster.name || getLobsterGradeName(lobster.grade),
        skillDesc: skill?.description || ''
    }
})

const canConfirm = computed(() => selectedIndex.value >= 0 && availableLobsters.value.length > 0)

const canBet = computed(() => {
    const myPlayer = playerStore.getPlayerById(store.playerId)
    return (myPlayer?.coins || 0) >= 1
})

const subtitle = computed(() => {
    const subtitles = {
        selecting: isChallenger.value
            ? '你是挑战者，请选择出战龙虾'
            : isDefender.value
              ? '你是被挑战者，请选择出战龙虾'
              : '观战模式',
        betting: isFighter.value ? '等待观战者投注...' : '请选择你要支持的龙虾',
        ready: '即将进入竞技场'
    }
    return subtitles[localPhase.value] || ''
})

const stopCountdown = () => {
    if (countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
    }
}

const resetLocalState = () => {
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
    stopCountdown()
    const battle = store.arenaBattleQueue[0]
    currentBattleId = battle ? `${store.roomId}_${battle.slotIndex}` : ''
}

const sendBetMessage = (betAmount, targetFighterId) => {
    socketService._send('clientBattleAction', {
        action_type: 'spectatorBet',
        battleId: currentBattleId,
        betAmount,
        targetFighterId
    })
}

const getPlayerName = (playerId) => {
    const player = playerStore.players.find((p) => String(p.id) === String(playerId))
    return player?.name || '未知玩家'
}

const getBetTargetName = (targetFighterId) => {
    if (String(targetFighterId) === String(props.challenger?.id)) return props.challenger?.name || '挑战者'
    if (String(targetFighterId) === String(props.defender?.id)) return props.defender?.name || '被挑战者'
    return '未知'
}

const selectLobster = (index) => {
    if (myLobsters.value[index]?.used) return
    if (myLobsters.value[index]?.grade === 'normal') return
    if (!hasConfirmed.value) selectedIndex.value = index
}

const buildBattleContext = () => {
    const battle = store.arenaBattleQueue[0]
    if (!battle) return null
    return {
        spectators: playerStore.players
            .filter((p) => p.id !== battle.challengerId && p.id !== battle.defenderId)
            .map((p) => p.id),
        battle
    }
}

const handleConfirm = () => {
    if (!canConfirm.value || hasConfirmed.value) return

    const selectedLobster = myLobsters.value[selectedIndex.value]
    hasConfirmed.value = true

    const context = buildBattleContext()
    if (!context) return

    socketService._send('clientBattleAction', {
        action_type: 'lobsterSelected',
        lobster: selectedLobster,
        battleId: currentBattleId,
        challengerId: context.battle.challengerId,
        defenderId: context.battle.defenderId,
        spectators: context.spectators
    })

    if (isChallenger.value) {
        store.challengerReady = true
        store.challengerSelectedLobster = selectedLobster
    } else if (isDefender.value) {
        store.defenderReady = true
        store.defenderSelectedLobster = selectedLobster
    }
}

const handleForfeit = () => {
    const winner = isChallenger.value ? 'defender' : 'challenge'
    const context = buildBattleContext()
    if (!context) return

    socketService._send('clientBattleAction', {
        action_type: 'noLobsterForfeit',
        challengeSlot: context.battle.slotIndex,
        winner: winner
    })

    emit('forfeit')
}

const selectBetTarget = (target) => {
    if (!hasBet.value) betTarget.value = target
}

const handleBet = () => {
    if (hasBet.value || !betTarget.value) return
    hasBet.value = true

    const battle = store.arenaBattleQueue[0]
    if (!battle) return
    const targetFighterId = betTarget.value === 'challenger' ? battle.challengerId : battle.defenderId
    sendBetMessage(1, targetFighterId)
}

const handleSkipBet = () => {
    if (hasBet.value) return
    hasBet.value = true
    sendBetMessage(0, null)
}

const startCountdown = () => {
    countdown.value = 5
    countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
            stopCountdown()
            emit('bothReady', {
                challenger: props.challenger,
                defender: props.defender,
                challengerLobster: store.challengerSelectedLobster || store.challengerLobster,
                defenderLobster: store.defenderSelectedLobster || store.defenderLobster
            })
        }
    }, 1000)
}

watch(
    () => store.arenaPhase,
    (newPhase) => {
        if (newPhase === 'betting') localPhase.value = 'betting'
        else if (newPhase === 'ready') {
            localPhase.value = 'ready'
            startCountdown()
        }
    }
)

watch(
    () => props.visible,
    (newVal) => {
        if (newVal) resetLocalState()
        else stopCountdown()
    }
)

onUnmounted(() => {
    stopCountdown()
    if (store.arenaBattleQueue.length > 0) {
        store.arenaBattleQueue.shift()
        const roomId = store.roomId
        if (roomId) {
            uni.setStorageSync(`arenaBattleQueue_${roomId}`, store.arenaBattleQueue)
        }
    }
})
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 10, 26, 0.9);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(8px);
}

.modal-container {
    background: #1a1a2e;
    border-radius: 16px;
    padding: 24px;
    width: 90%;
    max-width: 400px;
    max-height: 80vh;
    overflow-y: auto;
    border: 1px solid rgba(78, 205, 196, 0.2);
    box-shadow:
        0 0 40px rgba(0, 0, 0, 0.6),
        0 0 20px rgba(233, 69, 96, 0.1),
        inset 0 0 30px rgba(78, 205, 196, 0.02);
    position: relative;
}

.modal-container::before {
    content: '';
    position: absolute;
    top: -1px;
    left: 15%;
    right: 15%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #e94560, transparent);
    border-radius: 50%;
}

.modal-header {
    text-align: center;
    margin-bottom: 20px;
}

.modal-title {
    font-size: 22px;
    font-weight: bold;
    color: #fff;
    display: block;
    text-shadow:
        0 0 10px rgba(233, 69, 96, 0.6),
        0 0 20px rgba(233, 69, 96, 0.3);
}

.title-line {
    display: block;
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #e94560, transparent);
    margin: 8px auto;
    box-shadow: 0 0 8px rgba(233, 69, 96, 0.5);
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
    border: 1px solid rgba(78, 205, 196, 0.1);
    position: relative;
    transition: all 0.3s ease;
}

.player-info.active {
    border: 2px solid #e94560;
    box-shadow:
        0 0 15px rgba(233, 69, 96, 0.3),
        inset 0 0 15px rgba(233, 69, 96, 0.05);
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
    background: linear-gradient(135deg, #4ecdc4, #3ba89f);
    color: #0a0a1a;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: bold;
    box-shadow: 0 0 10px rgba(78, 205, 196, 0.4);
}

.vs-text {
    font-size: 18px;
    font-weight: bold;
    color: #e94560;
    margin: 0 10px;
    text-shadow:
        0 0 10px rgba(233, 69, 96, 0.6),
        0 0 20px rgba(233, 69, 96, 0.3);
    animation: vs-pulse 2s ease-in-out infinite;
}

@keyframes vs-pulse {
    0%,
    100% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.15);
        opacity: 0.8;
    }
}

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
    border: 2px solid rgba(78, 205, 196, 0.15);
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
    box-shadow: 0 0 15px rgba(233, 69, 96, 0.3);
}

.lobster-item.used {
    opacity: 0.4;
    border-color: rgba(255, 255, 255, 0.1);
    cursor: not-allowed;
    position: relative;
}

.used-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: rgba(100, 100, 100, 0.9);
    color: #ccc;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 8px;
    font-weight: bold;
    white-space: nowrap;
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

.spectator-view {
    text-align: center;
    padding: 20px;
}

.spectator-text {
    font-size: 14px;
    color: #666;
}

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
    border: 1px solid rgba(78, 205, 196, 0.1);
    transition: all 0.2s;
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
    background: #0d0d2b;
    color: #a0a0b0;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid rgba(78, 205, 196, 0.15);
}

.bf-select.selected {
    background: linear-gradient(135deg, #e94560, #c23152);
    color: #fff;
    border-color: #e94560;
    box-shadow: 0 0 10px rgba(233, 69, 96, 0.3);
}

.bf-select.disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.gold-warning {
    text-align: center;
    margin: 8px 0;
    padding: 6px;
    background: rgba(233, 69, 96, 0.1);
    border: 1px solid rgba(233, 69, 96, 0.2);
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
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.preview-label {
    font-size: 12px;
    color: #a0a0b0;
    display: block;
}

.preview-lobster {
    font-size: 14px;
    font-weight: bold;
    color: #4ecdc4;
    display: block;
    margin-top: 4px;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
}

.ready-area {
    margin-top: 10px;
    text-align: center;
}

.fighters-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 16px;
    padding: 12px;
    background: #16213e;
    border-radius: 8px;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.fighter-card {
    flex: 1;
    padding: 10px;
    border-radius: 6px;
    background: #1a1a2e;
}

.fighter-card.challenger {
    border: 1px solid rgba(233, 69, 96, 0.4);
}

.fighter-card.defender {
    border: 1px solid rgba(78, 205, 196, 0.4);
}

.fighter-label {
    font-size: 11px;
    color: #666;
    display: block;
    margin-bottom: 4px;
}

.fighter-name {
    font-size: 14px;
    font-weight: bold;
    color: #fff;
    display: block;
    margin-bottom: 4px;
}

.fighter-card.challenger .fighter-name {
    color: #e94560;
    text-shadow: 0 0 8px rgba(233, 69, 96, 0.3);
}

.fighter-card.defender .fighter-name {
    color: #4ecdc4;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
}

.fighter-skill {
    font-size: 11px;
    color: #666;
    display: block;
}

.ready-title {
    font-size: 16px;
    font-weight: bold;
    color: #4ecdc4;
    display: block;
    margin-bottom: 16px;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
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
    border: 1px solid rgba(78, 205, 196, 0.08);
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
    text-shadow:
        0 0 10px rgba(233, 69, 96, 0.6),
        0 0 20px rgba(233, 69, 96, 0.3);
    animation: countdown-pulse 1s ease-in-out infinite;
}

@keyframes countdown-pulse {
    0%,
    100% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.05);
        opacity: 0.8;
    }
}

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
    transition: all 0.2s;
}

.action-btn[disabled] {
    opacity: 0.5;
    cursor: not-allowed;
}

.confirm-btn {
    background: linear-gradient(135deg, #e94560, #c23152);
    color: #fff;
    box-shadow: 0 0 15px rgba(233, 69, 96, 0.3);
}

.confirm-btn:active {
    box-shadow: 0 0 25px rgba(233, 69, 96, 0.5);
    transform: scale(0.98);
}

.skip-btn {
    background: #0d0d2b;
    color: #a0a0b0;
    border: 1px solid rgba(78, 205, 196, 0.15);
}
</style>
