<template>
    <view class="game-container">
        <!-- 游戏头部 -->
        <view class="game-header">
            <view class="round-info">
                <text class="round-label">回合</text>
                <text class="round-number">{{ onlineGameStore.currentRound }}/{{ onlineGameStore.maxRounds }}</text>
            </view>
            <view class="phase-info">
                <text class="phase-label">{{ getPhaseText() }}</text>
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
                v-for="(player, index) in onlineGameStore.players"
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
                    <text class="resource-value">{{onlineGameStore.myPlayer.lobsters?.length }}</text>
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
            ref="lobsterSelectRef"
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
import { DEFAULT_SLOT_STYLE, getOccupiedSlotStyle, PLAYER_COLORS } from '@utils/slotConstants.js'
import LobsterSelect from './LobsterSelect.vue'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule
const onlineGameStore = useOnlineGameStore()
const showLog = ref(false)
const lobsterSelectRef = ref(null)

// ============ 计算属性 ============
const isPlacementPhase = computed(() => onlineGameStore.currentPhase === 'placement')

const currentPlacementPlayerName = computed(() => {
    const player = onlineGameStore.players[onlineGameStore.currentPlayerIndex]
    return player?.name || '未知'
})

// ============ 视觉样式方法 ============

/**
 * 获取玩家栏目的样式
 * 用于区分当前轮到放置的玩家
 */
const getPlayerItemStyle = (playerId) => {
    if (!isCurrentPlacementPlayer(playerId)) return {}

    const color = PLAYER_COLORS[playerId]
    if (!color) return {}
    return {
        borderColor: color.bg,
        boxShadow: `0 0 10px ${color.bg}40`
    }
}

/**
 * 获取行动格的样式
 * 根据占用状态返回不同的视觉样式
 */
const getSlotStyle = (area, slotIndex) => {
    const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)

    if (occupant !== null && occupant !== undefined) {
        const style = getOccupiedSlotStyle(occupant)
        return {
            background: style.background,
            borderColor: style.borderColor,
            opacity: style.opacity,
            color: style.color
        }
    }

    // 未占用状态
    return {
        background: DEFAULT_SLOT_STYLE.background,
        opacity: isPlacementPhase.value ? 1 : 0.6
    }
}

/**
 * 检查行动格是否被占用
 */
const isSlotOccupied = (area, slotIndex) => {
    return onlineGameStore.isSlotOccupied(area, slotIndex)
}

/**
 * 获取占用行动格的玩家标签
 * 用于在UI上显示"1P"、"2P"等标识
 */
const getSlotOccupantLabel = (area, slotIndex) => {
    const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
    if (occupant !== null && occupant !== undefined) {
        const style = getOccupiedSlotStyle(occupant)
        return style.playerLabel
    }
    return null
}

/**
 * 检查是否可以在该行动格放置
 * 用于UI按钮的禁用状态判断
 */
const canPlaceOnSlot = (area, slotIndex) => {
    // 如果不是工放阶段，不能放置
    if (!isPlacementPhase.value) return false

    // 如果不是我的回合，不能放置（联机特有）
    if (!onlineGameStore.isMyTurn) return false

    // 如果行动格已被占用，不能放置
    if (isSlotOccupied(area, slotIndex)) return false

    return true
}

/**
 * 检查是否是当前轮到放置的玩家
 */
const isCurrentPlacementPlayer = (playerId) => {
    if (!isPlacementPhase.value) return false
    return onlineGameStore.currentPlayerIndex === playerId
}

// ============ 交互处理方法 ============

/**
 * 显示提示信息
 * @param {string} message - 提示内容
 * @param {string} icon - 图标类型
 */
const showToast = (message, icon = 'none') => {
    uni.showToast({
        title: message,
        icon: icon,
        duration: 2000
    })
}

/**
 * 处理行动格点击事件
 * 实现放置机制的核心交互逻辑
 */
const handleSlotClick = (area, slotIndex) => {
    // 如果不是工放阶段，显示提示
    if (!isPlacementPhase.value) {
        showToast('当前不是工放阶段，无法放置里长')
        return
    }

    // 如果不是我的回合（联机特有）
    if (!onlineGameStore.isMyTurn) {
        showToast('不是你的回合')
        return
    }

    // 如果行动格已被占用，显示占用者信息
    if (isSlotOccupied(area, slotIndex)) {
        const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
        const occupantPlayer = onlineGameStore.players.find((p) => p.id === occupant)
        const occupantName = occupantPlayer?.name || '未知玩家'
        showToast(`该行动格已被${occupantName}占用`)
        return
    }

    // 执行放置操作
    onlineGameStore.placeHeadman(area, slotIndex)
}

// ============ 工具方法 ============

const getPhaseText = () => {
    return `${onlineGameStore.phaseText}阶段`
}

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

/**
 * 检查闹市区行动格是否可用
 * 闹市区有回合限制
 */
const isMarketplaceAvailable = (slotIndex) => {
    // 1号格第2回合可用，2号格第3回合可用，3号格第4回合可用
    return onlineGameStore.currentRound >= slotIndex + 2
}

const handleNextPhase = () => {
    if (!onlineGameStore.isMyTurn) {
        showToast('不是你的回合')
        return
    }

    if (onlineGameStore.currentPhase === 'placement') {
        onlineGameStore.nextPlayer()
    } else if (onlineGameStore.currentPhase === 'settlement') {
        onlineGameStore.nextArea()
    }
}

// ============ 竞技场战斗逻辑（联机特有） ============

const showArenaModal = ref(false)
const arenaBattleQueue = computed(() => onlineGameStore.arenaBattleQueue)
const showArenaReopen = computed(() => {
    return onlineGameStore.arenaPhase !== 'idle' && !showArenaModal.value && arenaBattleQueue.value.length > 0
})

/**
 * 监听竞技场战斗队列变化
 */
watch(
    () => arenaBattleQueue.value,
    (queue) => {
        if (
            queue.length > 0 &&
            onlineGameStore.currentPhase === 'settlement' &&
            onlineGameStore.arenaPhase === 'idle'
        ) {
            onlineGameStore.setCurrentArenaBattle(0)
            showArenaModal.value = true
        }
    },
    { deep: true }
)

watch(
    () => onlineGameStore.currentPhase,
    (phase) => {
        if (phase === 'settlement' && arenaBattleQueue.value.length > 0 && onlineGameStore.arenaPhase === 'idle') {
            onlineGameStore.setCurrentArenaBattle(0)
            showArenaModal.value = true
        }
    }
)

/**
 * 处理双方都选择完成（含投注完成+倒计时结束），进入竞技场
 */
const handleBothReady = ({ challenger, defender, challengerLobster, defenderLobster }) => {
    showArenaModal.value = false
    onlineGameStore.setArenaPhase('idle')

    const player1Data = {
        id: challenger.id,
        name: challenger.name,
        lobsterId: challengerLobster.id,
        lobsterName: challengerLobster.name,
        lobsterDesc: challengerLobster.description,
        color: PLAYER_COLORS[challenger.id]?.bg || '#FF6B6B'
    }

    const player2Data = {
        id: defender.id,
        name: defender.name,
        lobsterId: defenderLobster.id,
        lobsterName: defenderLobster.name,
        lobsterDesc: defenderLobster.description,
        color: PLAYER_COLORS[defender.id]?.bg || '#4ECDC4'
    }

    // 移除当前这场战斗（开始后就从队列中删除）
    if (onlineGameStore.arenaBattleQueue.length > 0) {
        onlineGameStore.arenaBattleQueue.shift()
    }

    // 跳转到竞技场页面
    const storageKey = `arenaBattleQueue_${onlineGameStore.roomId}`
    uni.setStorageSync(storageKey, onlineGameStore.arenaBattleQueue)

    uni.navigateTo({
        url: `/pages/arena/arena?player1=${encodeURIComponent(JSON.stringify(player1Data))}&player2=${encodeURIComponent(JSON.stringify(player2Data))}&roomId=${onlineGameStore.roomId}&playerId=${onlineGameStore.playerId}&challengeSlot=${onlineGameStore.currentArenaBattle?.slotIndex}`
    })
}

// ============ 生命周期（联机特有） ============

onMounted(() => {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    const options = currentPage.options || {}

    const rId = options.roomId || uni.getStorageSync('roomId') || ''
    const pId = parseInt(options.playerId) || uni.getStorageSync('playerId')

    // 恢复 arenaBattleQueue（从 arena 页面返回时可能有队列）
    const storageKey = `arenaBattleQueue_${rId}`
    const savedQueue = uni.getStorageSync(storageKey)
    if (savedQueue && savedQueue.length > 0) {
        onlineGameStore.arenaBattleQueue = savedQueue
        uni.removeStorageSync(storageKey)
    }

    if (!rId || pId === null) {
        uni.redirectTo({ url: '/pages/lobby/lobby' })
        return
    }

    // 使用 URL 传递的 gameState 初始化状态，避免 room.vue 销毁到 onlineGame.vue 挂载期间
    // socket 监听器空窗期导致错过 roomStateUpdate 事件的竞态问题
    if (options.gameState) {
        try {
            const gs = JSON.parse(decodeURIComponent(options.gameState))
            onlineGameStore.updateGameState(gs)
        } catch (e) {
            console.error('Failed to parse gameState from URL:', e)
        }
    }

    onlineGameStore.initOnlineMode(rId, pId)

    const isAlreadyConnected = onlineGameStore.isConnected && onlineGameStore.roomId === rId
    if (!isAlreadyConnected) {
        socketService.setRoomContext(rId, pId)
        socketService.connect(rId, pId)
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
</style>
