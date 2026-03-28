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

<style scoped>
.game-container {
    min-height: 100vh;
    background: var(--background-gray);
    padding-bottom: 11.25rem;
    animation: fadeIn 0.8s ease-out;
}

/* 游戏头部 */
.game-header {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
    padding: 0.9375rem 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.round-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.round-label {
    color: rgba(255, 255, 255, 0.8);
    font-size: 1rem;
}

.round-number {
    color: #fff;
    font-size: 1.25rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.phase-info {
    flex: 1;
    text-align: center;
}

.phase-label {
    color: #fff;
    font-size: 1.125rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.next-btn {
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
    border: none;
    border-radius: 1.25rem;
    padding: 0.625rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.next-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
}

.next-btn:active {
    transform: translateY(0);
}

/* 放置阶段提示横幅 */
.placement-banner {
    background: linear-gradient(90deg, var(--secondary-light) 0%, var(--secondary-color) 100%);
    padding: 0.75rem 1.25rem;
    text-align: center;
    border-bottom: 1px solid var(--border-color);
    animation: slideDown 0.5s ease-out;
}

.placement-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.placement-text {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
}

.placement-hint {
    font-size: 0.8125rem;
    color: var(--text-secondary);
}

/* 玩家栏 */
.players-bar {
    background: var(--background-light);
    padding: 0.9375rem;
    display: flex;
    gap: 0.625rem;
    overflow-x: auto;
    border-bottom: 1px solid var(--border-color);
    scrollbar-width: thin;
    scrollbar-color: var(--border-color) transparent;
}

.players-bar::-webkit-scrollbar {
    height: 4px;
}

.players-bar::-webkit-scrollbar-track {
    background: transparent;
}

.players-bar::-webkit-scrollbar-thumb {
    background-color: var(--border-color);
    border-radius: 2px;
}

.player-item {
    flex: 1;
    min-width: 7.5rem;
    padding: 0.9375rem;
    background: var(--background-gray);
    border-radius: 0.625rem;
    border: 2px solid transparent;
    position: relative;
    transition: all 0.3s ease;
    cursor: pointer;
}

.player-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.player-item.active {
    background: rgba(102, 126, 234, 0.05);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.player-item.starting::before {
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    border: 2px dashed #ffd700;
    border-radius: 0.875rem;
    pointer-events: none;
    animation: pulse 2s infinite;
}

.player-badge {
    position: absolute;
    top: -0.5rem;
    right: 0.5rem;
    background: #ffd700;
    color: var(--text-primary);
    font-size: 0.75rem;
    padding: 0.1875rem 0.5rem;
    border-radius: 0.5rem;
    font-weight: 700;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.player-name {
    display: block;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.player-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.stat {
    background: rgba(0, 0, 0, 0.05);
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    transition: all 0.3s ease;
}

.stat:hover {
    background: rgba(102, 126, 234, 0.1);
    color: var(--primary-color);
}

/* 主游戏板 */
.main-board {
    padding: 0.9375rem;
    max-height: calc(100vh - 21.875rem);
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--border-color) transparent;
}

.main-board::-webkit-scrollbar {
    width: 6px;
}

.main-board::-webkit-scrollbar-track {
    background: transparent;
}

.main-board::-webkit-scrollbar-thumb {
    background-color: var(--border-color);
    border-radius: 3px;
}

.board-section {
    background: var(--background-light);
    border-radius: 0.9375rem;
    padding: 1.25rem;
    margin-bottom: 0.9375rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
    animation: fadeInUp 0.5s ease-out;
}

.board-section:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.section-header {
    margin-bottom: 0.9375rem;
    display: flex;
    align-items: center;
    gap: 0.625rem;
}

.section-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
}

.section-desc {
    font-size: 0.8125rem;
    color: var(--text-muted);
}

.area-slots {
    display: flex;
    flex-wrap: wrap;
    gap: 0.625rem;
}

/* 行动格样式 */
.slot {
    flex: 1;
    min-width: 6.875rem;
    padding: 0.9375rem 0.625rem;
    border-radius: 0.625rem;
    text-align: center;
    cursor: pointer;
    position: relative;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    overflow: hidden;
}

.slot::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s;
}

.slot:hover:not(.occupied):not(.disabled)::before {
    left: 100%;
}

.slot:hover:not(.occupied):not(.disabled) {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.slot.occupied {
    cursor: not-allowed;
}

.slot.disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.slot.challenge-slot {
    border-style: dashed;
    animation: borderPulse 2s infinite;
}

/* 占用者徽章 */
.slot-occupant-badge {
    position: absolute;
    top: -0.5rem;
    left: -0.5rem;
    background: rgba(255, 255, 255, 0.95);
    color: var(--text-primary);
    font-size: 0.6875rem;
    font-weight: 700;
    padding: 0.1875rem 0.5rem;
    border-radius: 0.625rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    z-index: 10;
}

.slot-number {
    display: block;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.3125rem;
}

.slot-desc {
    display: block;
    font-size: 0.6875rem;
    line-height: 1.4;
    opacity: 0.9;
}

/* 当前玩家面板 */
.current-player-panel {
    position: fixed;
    bottom: 6.25rem;
    left: 0.9375rem;
    right: 0.9375rem;
    background: var(--background-light);
    border-radius: 0.9375rem;
    padding: 0.9375rem;
    box-shadow: 0 -5px 20px rgba(0, 0, 0, 0.1);
    z-index: 90;
    animation: slideUp 0.5s ease-out;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.panel-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
}

.lizhang-count {
    font-size: 1rem;
    color: var(--primary-color);
    font-weight: 700;
}

.panel-resources {
    display: flex;
    gap: 0.75rem;
}

.resource-item {
    flex: 1;
    text-align: center;
    padding: 0.625rem;
    background: var(--background-gray);
    border-radius: 0.5rem;
    transition: all 0.3s ease;
}

.resource-item:hover {
    background: rgba(102, 126, 234, 0.1);
    transform: translateY(-2px);
}

.resource-label {
    display: block;
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-bottom: 0.1875rem;
}

.resource-value {
    display: block;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
}

/* 日志面板 */
.log-panel {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--background-light);
    border-top: 1px solid var(--border-color);
    z-index: 95;
    animation: slideUp 0.5s ease-out 0.2s both;
}

.log-header {
    padding: 0.75rem 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--background-gray);
    cursor: pointer;
    transition: all 0.3s ease;
}

.log-header:hover {
    background: var(--border-color);
}

.log-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
}

.log-toggle {
    font-size: 0.875rem;
    color: var(--primary-color);
    font-weight: 600;
    transition: all 0.3s ease;
}

.log-toggle:hover {
    color: var(--primary-dark);
}

.log-content {
    height: 7.5rem;
    max-height: 7.5rem;
    overflow: hidden;
    transition: all 0.3s ease;
}

.log-content.expanded {
    height: 15rem;
}

.log-scroll {
    height: 100%;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--border-color) transparent;
}

.log-scroll::-webkit-scrollbar {
    width: 4px;
}

.log-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.log-scroll::-webkit-scrollbar-thumb {
    background-color: var(--border-color);
    border-radius: 2px;
}

.log-item {
    padding: 0.625rem 1.25rem;
    border-bottom: 1px solid #f0f0f0;
    font-size: 0.8125rem;
    transition: all 0.3s ease;
    animation: fadeIn 0.3s ease-out;
}

.log-item.success {
    color: var(--success-color);
    background: rgba(76, 175, 80, 0.05);
}

.log-item.warning {
    color: var(--warning-color);
    background: rgba(255, 152, 0, 0.05);
}

.log-item.error {
    color: var(--error-color);
    background: rgba(244, 67, 54, 0.05);
}

.log-item.info {
    color: var(--text-secondary);
}

.log-text {
    display: block;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .game-container {
        padding-bottom: 10rem;
    }
    
    .game-header {
        padding: 0.75rem 1rem;
    }
    
    .round-number {
        font-size: 1.125rem;
    }
    
    .phase-label {
        font-size: 1rem;
    }
    
    .next-btn {
        padding: 0.5rem 1rem;
        font-size: 0.75rem;
    }
    
    .players-bar {
        padding: 0.75rem;
    }
    
    .player-item {
        min-width: 6.25rem;
        padding: 0.75rem;
    }
    
    .main-board {
        padding: 0.75rem;
        max-height: calc(100vh - 20rem);
    }
    
    .board-section {
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .slot {
        min-width: 6rem;
        padding: 0.75rem 0.5rem;
    }
    
    .current-player-panel {
        bottom: 5.5rem;
        left: 0.75rem;
        right: 0.75rem;
        padding: 0.75rem;
    }
    
    .panel-resources {
        gap: 0.5rem;
    }
    
    .resource-item {
        padding: 0.5rem;
    }
    
    .log-header {
        padding: 0.625rem 1rem;
    }
    
    .log-content {
        height: 6rem;
    }
    
    .log-content.expanded {
        height: 12rem;
    }
    
    .log-item {
        padding: 0.5rem 1rem;
    }
}

/* 动画效果 */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.05);
        opacity: 0.8;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

@keyframes borderPulse {
    0% {
        border-color: var(--border-color);
    }
    50% {
        border-color: var(--primary-color);
    }
    100% {
        border-color: var(--border-color);
    }
}
</style>
