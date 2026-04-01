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
            <button class="next-btn" @click="handleNextPhase" :disabled="!onlineGameStore.isMyTurn">下一阶段</button>
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
import { useOnlineGameStore } from '@stores/online-game.js'
import { usePlayerStore } from '@stores/player.js'
import { DEFAULT_SLOT_STYLE, getOccupiedSlotStyle, PLAYER_COLORS } from '@utils/slotConstants.js'
import LobsterSelect from './LobsterSelect.vue'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule
const onlineGameStore = useOnlineGameStore()
const playerStore = usePlayerStore()
const showLog = ref(false)
const showArenaModal = ref(false)

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
        socketService._send('noLobsterForfeit', {
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

    restoreArenaQueue(roomId)
    initGameState(options)
    onlineGameStore.initOnlineMode(roomId, playerId)
    initSocket(roomId, playerId)
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
</style>
