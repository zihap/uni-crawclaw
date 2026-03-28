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
                    }]" :style="getSlotStyle('shrimp_catching', i - 1)" @click="handleSlotClick('shrimp_catching', i - 1)">
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
                    <view v-for="i in 4" :key="i" :class="['slot', {
                        occupied: isSlotOccupied('seafood_market', i - 1),
                        disabled: !canPlaceOnSlot('seafood_market', i - 1)
                    }]" :style="getSlotStyle('seafood_market', i - 1)" @click="handleSlotClick('seafood_market', i - 1)">
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
            <view class="log-content" v-if="showLog">
                <view class="log-scroll">
                    <view v-for="(log, index) in gameStore.logs.slice().reverse()" :key="index"
                        :class="['log-item', log.type || 'info']">
                        <text class="log-text">{{ log.message }}</text>
                    </view>
                </view>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useGameStore, GAME_PHASES } from '@stores/game.js'
import { DEFAULT_SLOT_STYLE, getOccupiedSlotStyle, PLAYER_COLORS } from '@utils/slotConstants.js'

const gameStore = useGameStore()
const showLog = ref(false)

// ============ 计算属性 ============
const isPlacementPhase = computed(() => gameStore.currentPhase === GAME_PHASES.PLACEMENT)

const currentPlacementPlayerName = computed(() => {
    return gameStore.currentPlacementPlayer?.name || ''
})

// ============ 视觉样式方法 ============

/**
 * 获取玩家栏目的样式
 * 用于区分当前轮到放置的玩家
 */
const getPlayerItemStyle = (playerId) => {
    if (!isCurrentPlacementPlayer(playerId)) return {}

    const color = PLAYER_COLORS[playerId]
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
    return {
        background: DEFAULT_SLOT_STYLE.background,
        opacity: isPlacementPhase.value ? 1 : 0.6
    }
}

/**
 * 检查行动格是否被占用
 */
const isSlotOccupied = (area, slotIndex) => {
    return gameStore.isSlotOccupied(area, slotIndex)
}

/**
 * 获取占用行动格的玩家标签
 * 用于在UI上显示"1P"、"2P"等标识
 */
const getSlotOccupantLabel = (area, slotIndex) => {
    const status = gameStore.getSlotStatus(area, slotIndex)
    if (status.status === 'occupied') {
        const style = getOccupiedSlotStyle(status.playerId)
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

    // 如果所有玩家都已放置完毕，不能放置
    if (gameStore.isPlacementComplete) return false

    // 如果行动格已被占用，不能放置
    if (isSlotOccupied(area, slotIndex)) return false

    return true
}

/**
 * 检查是否是当前轮到放置的玩家
 */
const isCurrentPlacementPlayer = (playerId) => {
    if (!isPlacementPhase.value) return false
    if (gameStore.isPlacementComplete) return false

    const currentId = gameStore.placementOrder[gameStore.currentPlacementIndex]
    return currentId === playerId
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

    // 如果所有玩家都已放置完毕
    if (gameStore.isPlacementComplete) {
        showToast('工放阶段已结束')
        return
    }

    // 如果行动格已被占用，显示占用者信息
    if (isSlotOccupied(area, slotIndex)) {
        const status = gameStore.getSlotStatus(area, slotIndex)
        const occupantName = gameStore.players[status.playerId]?.name || '未知玩家'
        showToast(`该行动格已被${occupantName}占用`)
        return
    }

    // 执行放置操作
    const result = gameStore.placeLiZhang(area, slotIndex)

    // 处理放置结果
    if (!result.success) {
        // 根据错误类型显示不同的提示
        if (result.error === '当前不是工放阶段') {
            showToast('当前不是工放阶段')
        } else if (result.error === '该行动格已被占用') {
            showToast('该行动格已被占用')
        } else if (result.error === '没有剩余的里长可以放置') {
            showToast(`${result.message}，将自动跳过`)
        } else {
            showToast(result.message)
        }
    }
}

// ============ 工具方法 ============

const getPhaseText = () => {
    const phase = gameStore.getPhaseText()
    return `${phase}阶段`
}

const getShrimpCatchingSlotDesc = (i) => {
    const descs = [
        '1虾笼,夺起始,1次捕虾',
        '1虾笼,2次捕虾',
        '1金币,3次捕虾',
        '4次捕虾'
    ]
    return descs[i - 1]
}

const getSeafoodMarketSlotDesc = (i) => {
    const descs = [
        '1金币,2次交易',
        '3次交易',
        '1金币,3次交易',
        '2金币,3次交易'
    ]
    return descs[i - 1]
}

const getBreedingSlotDesc = (i) => {
    const descs = [
        '1草,1次培养',
        '2次培养',
        '1金币,2次培养',
        '3次培养'
    ]
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
    const descs = [
        '第2回合可用,1次闹市',
        '1金币,第3回合可用,1次闹市',
        '2金币,第4回合可用,1次闹市'
    ]
    return descs[i - 1]
}

/**
 * 检查闹市区行动格是否可用
 * 闹市区有回合限制
 */
const isMarketplaceAvailable = (slotIndex) => {
    const currentRound = gameStore.currentRound
    // 1号格第2回合可用，2号格第3回合可用，3号格第4回合可用
    return currentRound >= slotIndex + 2
}

const handleNextPhase = () => {
    if (gameStore.currentRound >= gameStore.maxRounds &&
        gameStore.currentPhase === GAME_PHASES.CLEANUP) {
        uni.navigateTo({
            url: '/pages/result/result'
        })
    } else {
        gameStore.nextPhase()
    }
}
</script>


