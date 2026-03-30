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
                        v-for="i in 6"
                        :key="i"
                        :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('tribute', i - 1),
                                disabled: !canPlaceOnSlot('tribute', i - 1),
                                'challenge-slot': i > 3
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
                    <text class="resource-value">{{
                        onlineGameStore.myPlayer.lobsters?.length || getLobsterCount(onlineGameStore.myPlayer)
                    }}</text>
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
            :challenger="currentArenaBattle?.challenger"
            :defender="currentArenaBattle?.defender"
            :player-id="onlineGameStore.playerId"
            :room-id="onlineGameStore.roomId"
            @confirm="handleArenaConfirm"
            @both-ready="handleBothReady"
        />
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
    } else {
        return `挑战${i - 3}号位,1次上供`
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

const getLobsterCount = (player) => {
    if (!player || !player.shrimpPond) return 0
    const pond = player.shrimpPond
    return (pond.normal || 0) + (pond.grade3 || 0) + (pond.grade2 || 0) + (pond.grade1 || 0) + (pond.royal || 0)
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
const currentArenaBattle = ref(null)
const arenaBattleQueue = ref([])

/**
 * 监听竞技场战斗队列变化
 */
watch(
    () => arenaBattleQueue,
    (queue) => {
        console.log('[DEBUG onlineGame] arenaBattleQueue 变化:', queue.value)
        console.log('[DEBUG onlineGame] currentPhase:', onlineGameStore.currentPhase)
        if (queue.value.length > 0 && onlineGameStore.currentPhase === 'settlement') {
            console.log('[DEBUG onlineGame] 显示竞技场弹窗')
            showArenaModal.value = true
        }
    },
    { deep: true }
)

/**
 * 处理单方龙虾选择确认（只是确认自己的选择）
 */
const handleArenaConfirm = ({}) => {
    // 单方确认时不做跳转，等待双方都选择
    console.log('[竞技场] 单方已选择龙虾')
}

/**
 * 处理双方都选择完成，进入竞技场
 */
const handleBothReady = ({ challenger, defender, challengerLobster, defenderLobster }) => {
    showArenaModal.value = false

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

    // 跳转到竞技场页面
    // 注意：不要在这里调用 shift()，让队列保持完整
    // 在跳转前保存队列到本地存储，防止页面卸载导致队列丢失
    const storageKey = `arenaBattleQueue_${onlineGameStore.roomId}`
    uni.setStorageSync(storageKey, arenaBattleQueue.value)
    console.log('[DEBUG handleBothReady] 保存队列到本地存储:', storageKey, arenaBattleQueue.value)

    uni.navigateTo({
        url: `/pages/arena/arena?player1=${encodeURIComponent(JSON.stringify(player1Data))}&player2=${encodeURIComponent(JSON.stringify(player2Data))}&roomId=${onlineGameStore.roomId}&playerId=${onlineGameStore.playerId}&challengeSlot=${currentArenaBattle.value?.slotIndex}`
    })
}

// ============ 竞技场调试（联机特有） ============

import { titleCards } from '@data/cards.js'

/**
 * 构建调试用的完整龙虾列表
 * 包含：titleCards全部龙虾 + 普通 + 三品 + 二品 + 一品 + 皇家
 */
const buildDebugLobsters = () => {
    const lobsters = []

    // 添加 titleCards 中的所有龙虾
    titleCards.forEach((card) => {
        lobsters.push({
            id: card.id,
            grade: 'title',
            name: card.name,
            description: card.description,
            skill: card.skill
        })
    })

    // 添加基础等级龙虾
    const baseGrades = [
        { id: 'normal', grade: 'normal', name: '普通龙虾' },
        { id: 'grade3', grade: 'grade3', name: '三品龙虾' },
        { id: 'grade2', grade: 'grade2', name: '二品龙虾' },
        { id: 'grade1', grade: 'grade1', name: '一品龙虾' },
        { id: 'royal', grade: 'royal', name: '皇家龙虾' }
    ]

    baseGrades.forEach((g) => {
        lobsters.push(g)
    })

    return lobsters
}

/**
 * 调试：直接进入竞技场战斗（触发2场）
 * 第一场：玩家1是challenger，玩家2是defender（slot 4 vs slot 1）
 * 第二场：玩家2是challenger，玩家1是defender（slot 5 vs slot 2）
 */
const debugArenaBattle = () => {
    const players = onlineGameStore.players

    if (players.length < 2) {
        console.log('[Debug] 玩家数量不足，无法触发竞技场战斗')
        return
    }

    const player1 = players[0]
    const player2 = players[1]
    const allLobsters = buildDebugLobsters()

    console.log('[Debug] 触发竞技场战斗（2场）')
    console.log('[Debug] 玩家1:', player1.name)
    console.log('[Debug] 玩家2:', player2.name)
    console.log('[Debug] 龙虾数量:', allLobsters.length)

    // 第1场战斗：玩家1是challenger(4号位)，玩家2是defender(1号位)
    arenaBattleQueue.value.push({
        challengerId: player1.id,
        defenderId: player2.id,
        slotIndex: 4 // challenge slot 4 = defender slot 1
    })
    player1.lobsters = allLobsters
    player2.lobsters = allLobsters
    // 第2场战斗：玩家2是challenger(5号位)，玩家1是defender(2号位)
    arenaBattleQueue.value.push({
        challengerId: player2.id,
        defenderId: player1.id,
        slotIndex: 5 // challenge slot 5 = defender slot 2
    })

    console.log('[Debug] 竞技场队列:', arenaBattleQueue.value)

    if (arenaBattleQueue.value.length > 0) {
        // 设置 currentArenaBattle 为队列第一个元素，确保 LobsterSelect 能正确获取 challenger/defender
        currentArenaBattle.value = {
            challenger: player1,
            defender: player2,
            slotIndex: arenaBattleQueue.value[0].slotIndex
        }
        console.log('[Debug] currentArenaBattle 设置:', currentArenaBattle.value)
        showArenaModal.value = true
    }
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
        console.log('[DEBUG onlineGame onMounted] 从本地存储恢复队列:', storageKey, savedQueue)
        arenaBattleQueue.value = savedQueue
        uni.removeStorageSync(storageKey)
    } else {
        console.log('[DEBUG onlineGame onMounted] arenaBattleQueue:', arenaBattleQueue.value)
    }

    if (!rId || pId === null) {
        uni.redirectTo({ url: '/pages/lobby/lobby' })
        return
    }

    onlineGameStore.initOnlineMode(rId, pId)

    const isAlreadyConnected = onlineGameStore.isConnected && onlineGameStore.roomId === rId
    if (!isAlreadyConnected) {
        socketService.setRoomContext(rId, pId)
        socketService.connect(rId, pId)
    }

    // 调试模式：等待连接后直接触发竞技场战斗
    setTimeout(() => {
        if (onlineGameStore.players.length >= 2) {
            debugArenaBattle()
        }
    }, 1000)
})

onUnmounted(() => {
    onlineGameStore.cleanupListeners()
})
</script>
