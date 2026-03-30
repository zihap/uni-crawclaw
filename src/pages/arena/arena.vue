<template>
    <view class="battle-container">
        <view class="back-btn" @click="exitBattle" />

        <view class="round-badge">
            <text class="round-label">Round</text>
            <text class="round-value">{{ battleData?.currentRound || 1 }}</text>
        </view>

        <view class="players-info">
            <view class="player-card player1-card" :class="{ active: battleData?.currentPlayer === 0 }">
                <view class="player-main">
                    <view class="player-avatar-wrapper">
                        <image class="player-avatar" src="@/static/images/player1_default.png" mode="aspectFit" />
                    </view>
                    <view v-if="shouldShowLobsterWrapper(0)" class="lobster-wrapper" :class="getLobsterWrapperClass(0)">
                        <image
                            class="lobster-icon animate-pulse"
                            src="@/static/images/lobster_left.png"
                            mode="aspectFit"
                            @longpress="showLobsterInfo(0)"
                        />
                    </view>
                </view>
                <text class="player-name">{{ battleData?.players[0]?.name || '' }}</text>
            </view>

            <view class="player-card player2-card" :class="{ active: battleData?.currentPlayer === 1 }">
                <text class="player-name">{{ battleData?.players[1]?.name || '' }}</text>
                <view class="player-main">
                    <view class="player-avatar-wrapper">
                        <image class="player-avatar" src="@/static/images/player2_default.png" mode="aspectFit" />
                    </view>
                    <view v-if="shouldShowLobsterWrapper(1)" class="lobster-wrapper" :class="getLobsterWrapperClass(1)">
                        <image
                            class="lobster-icon animate-pulse"
                            src="@/static/images/lobster_right.png"
                            mode="aspectFit"
                            @longpress="showLobsterInfo(1)"
                        />
                    </view>
                </view>
            </view>
        </view>

        <view class="battle-board">
            <view class="board-row">
                <view class="board-track">
                    <view v-for="(cell, index) in leftCells" :key="'left-' + cell.index" class="board-cell">
                        <image class="cell-bg" :src="`/static/images/${cell.img}`" mode="aspectFit" />
                        <view
                            v-if="shouldShowOnBoard(0) && battleData?.players[0]?.position === cell.index"
                            class="player-token"
                            :class="getMovingClass(0)"
                            :data-player="0"
                        >
                            <image
                                class="player-img animate-pulse"
                                src="@/static/images/lobster_left.png"
                                mode="aspectFit"
                                @longpress="showLobsterInfo(0)"
                            />
                        </view>

                        <view
                            v-if="shouldShowOnBoard(1) && battleData?.players[1]?.position === cell.index"
                            class="player-token"
                            :class="getMovingClass(1)"
                            :data-player="1"
                        >
                            <image
                                class="player-img animate-pulse"
                                src="@/static/images/lobster_right.png"
                                mode="aspectFit"
                                @longpress="showLobsterInfo(1)"
                            />
                        </view>
                    </view>
                    <view class="midline-wrapper">
                        <image class="cell-bg" src="@/static/images/battle_midline.png" mode="aspectFit" />
                    </view>
                    <view v-for="(cell, index) in rightCells" :key="'right-' + cell.index" class="board-cell">
                        <image class="cell-bg" :src="`/static/images/${cell.img}`" mode="aspectFit" />
                        <view
                            v-if="shouldShowOnBoard(0) && battleData?.players[0]?.position === cell.index"
                            class="player-token"
                            :class="getMovingClass(0)"
                            :data-player="0"
                        >
                            <image
                                class="player-img animate-pulse"
                                src="@/static/images/lobster_left.png"
                                mode="aspectFit"
                                @longpress="showLobsterInfo(0)"
                            />
                        </view>
                        <view
                            v-if="shouldShowOnBoard(1) && battleData?.players[1]?.position === cell.index"
                            class="player-token"
                            :class="getMovingClass(1)"
                            :data-player="1"
                        >
                            <image
                                class="player-img animate-pulse"
                                src="@/static/images/lobster_right.png"
                                mode="aspectFit"
                                @longpress="showLobsterInfo(1)"
                            />
                        </view>
                    </view>
                </view>
            </view>
        </view>

        <view class="dice-section">
            <view v-if="lastLogMessage" class="dice-log-message">
                <text class="dice-log-text">{{ lastLogMessage }}</text>
            </view>
            <view class="dice-container">
                <view
                    class="dice"
                    :class="{ rolling: isRolling, disabled: !canRoll }"
                    :style="{ backgroundImage: `url(${currentDiceImage})` }"
                    @click="canRoll && onDiceClick()"
                >
                </view>
            </view>
            <!-- 海草区域 - 骰子下方 -->
            <view class="seaweed-section" @click="toggleSeaweed" :class="{ disabled: !canUseSeaweed }">
                <view class="seaweed-icon" :class="{ checked: isSeaweedChecked }"> 🌿 </view>
                <text class="seaweed-count">x{{ seaweedCount }}</text>
            </view>
            <view v-if="rollCompleted && displayDice" class="dice-result-popup">
                <text class="dice-result-value">{{ displayDice }}</text>
            </view>
            <view v-if="battleStore.canReroll && displayDice && !isRolling" class="skill-popup">
                <image class="skill-popup-bg" src="@/static/images/confirm_box.png" mode="aspectFit" />
                <view class="skill-content">
                    <text class="skill-title">双重投掷</text>
                    <view class="skill-actions">
                        <button class="reroll-btn" @click="onReroll">
                            <image class="btn-bg" src="@/static/images/redbutton.png" mode="aspectFit" />
                            <text class="reroll-btn-text">重新投掷</text>
                        </button>
                        <button class="confirm-btn" @click="onConfirmDice">
                            <image class="btn-bg" src="@/static/images/bluebutton.png" mode="aspectFit" />
                            <text class="confirm-btn-text">确认 {{ displayDice }} 点</text>
                        </button>
                    </view>
                </view>
            </view>
        </view>

        <scroll-view
            class="log-content"
            scroll-y="true"
            :scroll-into-view="logScrollId"
            :scroll-with-animation="true"
            scrollIntoViewAnimationDuration="300"
        >
            <view
                v-for="(log, index) in battleData?.battleLog || []"
                :key="log.timestamp + '-' + index"
                :id="'log-' + index"
                class="log-item"
            >
                <text class="log-message">{{ log.message }}</text>
            </view>
        </scroll-view>

        <view v-if="showInitiativeOverlay" class="initiative-overlay">
            <view class="initiative-content">
                <text class="initiative-title">🎲 先手争夺 🎲</text>
                <view class="initiative-players">
                    <view class="initiative-player">
                        <image class="initiative-avatar" src="@/static/images/player1_default.png" mode="aspectFit" />
                        <text class="initiative-name">{{ battleData?.players[0]?.name || '' }}</text>
                        <view class="initiative-dice-wrapper">
                            <view
                                class="initiative-dice"
                                :class="{ rolling: initiativeRolling }"
                                :style="{ backgroundImage: `url(${getInitiativeDiceImage(0)})` }"
                            >
                            </view>
                            <text v-if="!initiativeRolling && initiativeDisplayP1" class="initiative-dice-side-value">{{
                                initiativeDisplayP1
                            }}</text>
                        </view>
                    </view>
                    <text class="initiative-vs">VS</text>
                    <view class="initiative-player">
                        <image class="initiative-avatar" src="@/static/images/player2_default.png" mode="aspectFit" />
                        <text class="initiative-name">{{ battleData?.players[1]?.name || '' }}</text>
                        <view class="initiative-dice-wrapper">
                            <view
                                class="initiative-dice"
                                :class="{ rolling: initiativeRolling }"
                                :style="{ backgroundImage: `url(${getInitiativeDiceImage(1)})` }"
                            >
                            </view>
                            <text v-if="!initiativeRolling && initiativeDisplayP2" class="initiative-dice-side-value">{{
                                initiativeDisplayP2
                            }}</text>
                        </view>
                    </view>
                </view>
                <text v-if="initiativeResult" class="initiative-result">{{ initiativeResult }}</text>
            </view>
        </view>

        <view v-if="showExitPopup" class="exit-popup-overlay" @click="cancelExit">
            <view class="exit-popup-content" @click.stop>
                <text class="exit-popup-title">确认退出</text>
                <text class="exit-popup-desc">退出战斗将判负，是否继续？</text>
                <view class="exit-popup-actions">
                    <button class="exit-cancel-btn" @click="cancelExit">取消</button>
                    <button class="exit-confirm-btn" @click="confirmExit">确认</button>
                </view>
            </view>
        </view>

        <view v-if="showVictory" class="victory-overlay" @click="closeResult">
            <view class="victory-content">
                <view class="victory-icon-container">
                    <text class="victory-icon">🏆</text>
                </view>
                <text class="victory-title">胜利！</text>
                <text class="victory-name">{{ battleData?.winner?.name }}</text>
                <text class="victory-lobster">{{ battleData?.winner?.lobsterName }} 荣获冠军！</text>
                <view class="victory-effects">
                    <view class="firework" v-for="i in 6" :key="i"></view>
                </view>
                <view class="victory-reward-actions">
                    <button class="reward-btn" @click="selectReward('coins')">
                        <text class="reward-btn-text">💰 获得2金币</text>
                    </button>
                    <button
                        v-if="winnerCanUpgrade"
                        class="reward-btn upgrade-btn"
                        @click="selectReward('gradeUpgrade')"
                    >
                        <text class="reward-btn-text">⭐ 出战龙虾升级</text>
                    </button>
                </view>
            </view>
        </view>

        <view v-if="showDefeat" class="defeat-overlay" @click="closeResult">
            <view class="defeat-content">
                <template v-if="battleStore.myPlayerIndex < 0">
                    <view class="defeat-icon-container">
                        <text class="defeat-icon">🏆</text>
                    </view>
                    <text class="defeat-title">比赛结果</text>
                    <text class="defeat-name">{{ battleData?.winner?.name }}</text>
                    <text class="defeat-lobster">{{ battleData?.winner?.lobsterName }} 获得胜利！</text>
                </template>
                <template v-else>
                    <view class="defeat-icon-container">
                        <text class="defeat-icon">💔</text>
                    </view>
                    <text class="defeat-title">战败</text>
                    <text class="defeat-name">{{ loser?.name }}</text>
                    <text class="defeat-lobster">{{ loser?.lobsterName }} 遗憾落败...</text>
                    <view class="defeat-effects">
                        <view class="tear" v-for="i in 4" :key="i"></view>
                    </view>
                </template>
                <text class="waiting-reward-text">获胜方正在选择奖励，请稍候...</text>
            </view>
        </view>

        <view v-if="showLobsterPopup" class="lobster-popup" @click="closeLobsterPopup">
            <view class="lobster-popup-content" @click.stop>
                <text class="lobster-popup-name">{{ lobsterPopupData.lobsterName }}</text>
                <text class="lobster-popup-desc">{{ lobsterPopupData.lobsterDesc }}</text>
                <text class="lobster-popup-desc">{{ lobsterPopupData.skillDesc }}</text>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useBattleStore } from '@stores/arena.js'
import { useOnlineGameStore } from '@stores/online-game.js'
import { getSkill } from '@data/cards.js'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule

const battleStore = useBattleStore()
const onlineGameStore = useOnlineGameStore()
const arenaBattleQueue = computed(() => onlineGameStore.arenaBattleQueue)

const isRolling = ref(false)
const rollCompleted = ref(false)
const logScrollId = ref('')
const showVictory = ref(false)
const showDefeat = ref(false)
const loser = ref(null)
const displayDice = ref(null)
const savedRoomId = ref('')
const savedPlayerId = ref(null)
const showLobsterPopup = ref(false)
const lobsterPopupData = ref({ lobsterName: '', lobsterDesc: '', skillDesc: '' })
const showExitPopup = ref(false)
const resultShown = ref(false)
const boardCells = ref([])
const isConfirming = ref(false)
const showInitiativeOverlay = ref(false)
const initiativeRolling = ref(false)
const initiativeDisplayP1 = ref(null)
const initiativeDisplayP2 = ref(null)
const initiativeResult = ref('')
let pendingApplyTimer = null

// 海草相关状态
const seaweedCount = computed(() => {
    const currentPlayer = battleData.value?.currentPlayer
    const player = battleData.value?.players[currentPlayer]
    return player?.seaweed || 0
})
const isSeaweedChecked = ref(false) // 是否勾选使用海草
const seaweedLocked = ref(false) // 海草状态锁定（勇者龙虾重掷时使用）

// 是否可以使用海草
const canUseSeaweed = computed(() => {
    if (seaweedCount.value <= 0) return false
    if (battleData.value?.currentPlayer !== battleStore.myPlayerIndex) return false
    if (battleData.value?.phase !== 'rolling') return false
    if (seaweedLocked.value) return false // 锁定时不可修改
    if (battleStore.canReroll) return false // 重掷弹窗显示时不可修改
    if (battleData.value?.rollDiceTimestamp) return false // 已掷骰后不可修改

    const currentPlayer = battleData.value?.currentPlayer
    const player = battleData.value?.players[currentPlayer]
    // 三品龙虾（grade3）不能吃海草
    return player?.lobsterId !== 'grade3'
})

// 海草加成值
const seaweedBonus = computed(() => {
    if (!isSeaweedChecked.value) return 0
    const currentPlayer = battleData.value?.currentPlayer
    const player = battleData.value?.players[currentPlayer]

    switch (player?.lobsterId) {
        case 'grade2':
            return 1 // 二品龙虾
        case 'grade1':
            return 2 // 一品龙虾
        default:
            return 3 // 御赐及其他龙虾
    }
})

const battleData = computed(() => battleStore.battleData)

// 获胜方是否可以升级龙虾
const winnerCanUpgrade = computed(() => {
    const winner = battleData.value?.winner
    if (!winner) return false
    const grade = winner.lobsterId
    // 只有 normal, grade3, grade2, grade1 可以升级
    return grade === 'normal' || grade === 'grade3' || grade === 'grade2' || grade === 'grade1'
})

// 当前玩家是否是获胜者
const isWinner = computed(() => {
    if (battleStore.myPlayerIndex < 0) return true
    return battleData.value?.winner?.id === savedPlayerId.value
})

// 根据当前玩家的skill获取对应的骰子图片
const currentDiceImage = computed(() => {
    const currentPlayer = battleData.value?.currentPlayer
    if (currentPlayer === undefined || currentPlayer === null) {
        return '/static/images/dice_d6.png'
    }
    const player = battleData.value?.players[currentPlayer]
    if (!player || !player.lobsterId) {
        return '/static/images/dice_d6.png'
    }
    const diceSides = battleStore.getDiceSides(currentPlayer)
    const diceImageMap = {
        6: '/static/images/dice_d6.png',
        8: '/static/images/dice_d8.png',
        10: '/static/images/dice_d10.png',
        12: '/static/images/dice_d12.png'
    }
    return diceImageMap[diceSides] || '/static/images/dice_d6.png'
})

// 获取玩家初始位置
const getInitialPosition = (playerIndex) => {
    return playerIndex === 0 ? -1 : battleData.value?.totalCells || 8
}

// 龙虾图片路径映射
const getLobsterImage = (playerIndex) => {
    return playerIndex === 0 ? '/static/images/lobster_left.png' : '/static/images/lobster_right.png'
}

// 龙虾容器样式类计算属性
const getLobsterWrapperClass = (playerIndex) => {
    const player = battleData.value?.players[playerIndex]
    if (!player) return ''

    const classes = []

    // 如果玩家已开始（started为true），则添加可移动类
    if (player.started) {
        classes.push('movable')
    }

    // 如果正在动画中，添加动画类
    if (animatingPlayers.value[playerIndex]) {
        classes.push('animating')
    }

    return classes.join(' ')
}

// 用于检测移动的响应式变量
const movingPlayers = ref([false, false])

// 获取移动类
const getMovingClass = (playerIndex) => {
    return movingPlayers.value[playerIndex] ? 'moving' : ''
}

// 判断是否应该显示lobster-wrapper
const shouldShowLobsterWrapper = (playerIndex) => {
    const player = battleData.value?.players[playerIndex]
    if (!player) return false

    // 如果正在动画中，显示lobster-wrapper
    if (animatingPlayers.value[playerIndex]) return true

    // 如果未开始（started为false），显示lobster-wrapper
    if (!player.started) return true

    // 如果位置在初始位置，显示lobster-wrapper
    return player.position === getInitialPosition(playerIndex)
}

// 判断是否应该在棋盘上显示龙虾图标
const shouldShowOnBoard = (playerIndex) => {
    const player = battleData.value?.players[playerIndex]
    if (!player) return false

    // 如果started为false，不在棋盘上显示
    if (!player.started) return false

    // 如果位置在初始位置，不在棋盘上显示
    if (player.position === getInitialPosition(playerIndex)) return false

    // 如果正在动画中，不在棋盘上显示
    if (animatingPlayers.value[playerIndex]) return false

    return true
}

// 监听玩家started状态变化
const animatingPlayers = ref([false, false])

// 监听玩家位置变化，当位置变化时触发动画
watch(
    () => [battleData.value?.players[0]?.position, battleData.value?.players[1]?.position],
    (newPositions, oldPositions) => {
        if (!oldPositions) return

        for (let i = 0; i < 2; i++) {
            const player = battleData.value?.players[i]
            if (!player) continue

            // 检查位置是否变化
            if (newPositions[i] !== oldPositions[i] && newPositions[i] !== null) {
                if (player.started) {
                    // 检查是否从初始位置移动到棋盘上
                    if (oldPositions[i] === getInitialPosition(i)) {
                        // 从lobster-wrapper移动到棋盘，触发动画
                        animatingPlayers.value[i] = true
                        animateLobsterMove(i)
                    } else {
                        // 在棋盘上移动，使用移动动画
                        movingPlayers.value[i] = true
                        setTimeout(() => {
                            movingPlayers.value[i] = false
                        }, 500)
                    }
                } else {
                    // 未开始时的位置变化，触发移动动画
                    movingPlayers.value[i] = true
                    setTimeout(() => {
                        movingPlayers.value[i] = false
                    }, 500)
                }
            }
        }
    },
    { deep: true }
)

// 龙虾移动动画函数 - 闪现效果（仅H5环境）
function animateLobsterMove(playerIndex) {
    if (!animatingPlayers.value[playerIndex]) return

    // 非H5环境（小程序）跳过DOM动画，直接结束
    if (typeof document === 'undefined') {
        animatingPlayers.value[playerIndex] = false
        return
    }

    nextTick(() => {
        // 获取lobster-wrapper元素
        const wrapperClass = playerIndex === 0 ? '.player1-card .lobster-wrapper' : '.player2-card .lobster-wrapper'
        const wrapperEl = document.querySelector(wrapperClass)

        // 获取玩家的新位置
        const player = battleData.value?.players[playerIndex]
        if (!player) return

        // 获取棋盘区域的位置
        const boardElement = document.querySelector('.battle-board')
        if (!boardElement) return

        const boardRect = boardElement.getBoundingClientRect()

        // 计算目标位置
        // 对于player1，位置从左到右增加
        // 对于player2，位置从右到左减少
        const totalCells = battleData.value?.totalCells || 8
        const cellWidth = boardRect.width / totalCells

        let targetX
        if (playerIndex === 0) {
            // player1: 从左边开始，位置从0开始
            targetX = boardRect.left + player.position * cellWidth
        } else {
            // player2: 从右边开始，位置从totalCells开始
            targetX = boardRect.left + (totalCells - player.position - 1) * cellWidth
        }

        const targetY = boardRect.top + boardRect.height / 2

        if (wrapperEl) {
            // 获取起始位置
            const startRect = wrapperEl.getBoundingClientRect()

            // 创建克隆元素
            const clone = document.createElement('div')
            clone.className = 'lobster-clone'
            clone.style.cssText = `
        position: fixed;
        top: ${startRect.top}px;
        left: ${startRect.left}px;
        width: ${startRect.width}px;
        height: ${startRect.height}px;
        z-index: 1000;
        pointer-events: none;
      `

            // 复制龙虾图标
            const img = document.createElement('img')
            img.src = getLobsterImage(playerIndex)
            img.style.cssText = 'width: 100%; height: 100%; object-fit: contain;'
            clone.appendChild(img)

            document.body.appendChild(clone)

            // 隐藏原始wrapper
            wrapperEl.style.opacity = '0'

            // 闪现到目标位置
            setTimeout(() => {
                clone.classList.add('flash')
                clone.style.top = `${targetY - startRect.height / 2}px`
                clone.style.left = `${targetX - startRect.width / 2}px`
            }, 50)

            // 动画结束后
            setTimeout(() => {
                clone.remove()
                wrapperEl.style.opacity = '1'
                animatingPlayers.value[playerIndex] = false
            }, 350)
        } else {
            // 如果找不到元素，直接结束动画
            animatingPlayers.value[playerIndex] = false
        }
    })
}

const halfIndex = computed(() => {
    return Math.floor((battleData.value?.totalCells || 8) / 2)
})

const leftCells = computed(() => boardCells.value.slice(0, halfIndex.value))
const rightCells = computed(() => boardCells.value.slice(halfIndex.value))

const lastLogMessage = ref('')
let logMessageTimer = null

watch(
    () => battleData.value?.battleLog,
    (logs) => {
        if (logMessageTimer) clearTimeout(logMessageTimer)
        if (!logs || logs.length === 0) {
            lastLogMessage.value = ''
            return
        }
        // 掷骰动画进行中或掷骰已开始但未完成，跳过服务器同步触发的更新
        if (isRolling.value || battleData.value?.rollDiceTimestamp) return
        for (let i = logs.length - 1; i >= 0; i--) {
            if (logs[i].message.includes('掷出')) {
                lastLogMessage.value = logs[i].message
                logMessageTimer = setTimeout(() => {
                    lastLogMessage.value = ''
                }, 3000)
                return
            }
        }
        lastLogMessage.value = ''
    },
    { deep: true }
)

const canRoll = computed(() => {
    if (isRolling.value) return false
    if (!battleStore.isMyTurn) return false
    if (battleData.value?.phase !== 'rolling') return false
    if (battleStore.canReroll) return false
    if (battleData.value?.rollDiceTimestamp) return false
    return true
})

function initBoard() {
    const totalCells = battleData.value?.totalCells || 8
    const cells = []
    for (let i = 0; i < totalCells; i++) {
        const imgIndex = (i % 8) + 1
        cells.push({ index: i, img: `battle_num${imgIndex}.png` })
    }
    boardCells.value = cells
}

function toggleSeaweed() {
    if (!canUseSeaweed.value) return
    isSeaweedChecked.value = !isSeaweedChecked.value
}

async function onDiceClick() {
    if (!canRoll.value || isRolling.value) return

    const bonus = seaweedBonus.value
    if (bonus > 0) {
        seaweedCount.value-- // 海草数量-1
        seaweedLocked.value = true // 锁定海草状态
    }

    const diceValue = battleStore.getDiceValue(battleData.value?.currentPlayer)
    const finalValue = diceValue + bonus // 直接累加

    battleStore.rollDice(finalValue, bonus)
}

function onReroll() {
    if (!battleStore.canReroll || isRolling.value) return
    displayDice.value = null
    rollCompleted.value = false

    const bonus = seaweedBonus.value
    const diceValue = battleStore.getDiceValue(battleData.value?.currentPlayer)
    const finalValue = diceValue + bonus // 海草加成也应用于重掷

    battleStore.rollDice(finalValue, bonus)
}

function onConfirmDice() {
    if (!battleStore.canReroll || isConfirming.value) return
    isConfirming.value = true
    battleStore.confirmDice()
    setTimeout(() => {
        isConfirming.value = false
    }, 500)
}

function getInitiativeDiceImage(playerIndex) {
    const diceSides = battleStore.getDiceSides(playerIndex)
    const diceImageMap = {
        6: '/static/images/dice_d6.png',
        8: '/static/images/dice_d8.png',
        10: '/static/images/dice_d10.png',
        12: '/static/images/dice_d12.png'
    }
    return diceImageMap[diceSides] || '/static/images/dice_d6.png'
}

function playInitiativeAnimation(result, isFromSync) {
    if (initiativeRolling.value) return
    initiativeRolling.value = true
    initiativeDisplayP1.value = null
    initiativeDisplayP2.value = null
    initiativeResult.value = ''

    const animationDuration = 1500
    const interval = 80
    const steps = animationDuration / interval
    let step = 0

    const p1Sides = battleStore.getDiceSides(0)
    const p2Sides = battleStore.getDiceSides(1)

    const rollInterval = setInterval(() => {
        step++
        initiativeDisplayP1.value = Math.floor(Math.random() * p1Sides) + 1
        initiativeDisplayP2.value = Math.floor(Math.random() * p2Sides) + 1

        if (step >= steps) {
            clearInterval(rollInterval)
            initiativeRolling.value = false
            initiativeDisplayP1.value = result.p1
            initiativeDisplayP2.value = result.p2

            setTimeout(() => {
                const p1Name = battleData.value?.players[0]?.name || '玩家1'
                const p2Name = battleData.value?.players[1]?.name || '玩家2'

                if (result.p1 > result.p2) {
                    initiativeResult.value = `${p1Name} 获得先手！`
                } else if (result.p2 > result.p1) {
                    initiativeResult.value = `${p2Name} 获得先手！`
                } else {
                    initiativeResult.value = `点数一致，${p2Name} 获得先手！`
                }

                setTimeout(() => {
                    if (!isFromSync) {
                        battleStore.applyInitiative()
                    }
                    showInitiativeOverlay.value = false
                    initiativeDisplayP1.value = null
                    initiativeDisplayP2.value = null
                    initiativeResult.value = ''
                }, 2000)
            }, 500)
        }
    }, interval)
}

function triggerInitiativeRoll() {
    if (showInitiativeOverlay.value) return

    const initiative = battleData.value?.initiative
    const isFromSync = initiative && initiative.p1 !== null && initiative.p2 !== null
    const isHost = battleStore.myPlayerIndex === 0 || battleStore.myPlayerIndex < 0

    showInitiativeOverlay.value = true

    let result
    if (isFromSync) {
        result = { p1: initiative.p1, p2: initiative.p2 }
    } else if (isHost) {
        result = battleStore.rollInitiativeDice()
        if (!result) return
    } else {
        return
    }

    playInitiativeAnimation(result, isFromSync)
}

function showLobsterInfo(playerIndex) {
    const player = battleData.value?.players[playerIndex]
    if (!player) return
    const skill = getSkill(player.lobsterId)
    let skillDesc = ''
    if (skill) {
        skillDesc = skill.description
    }
    lobsterPopupData.value = {
        lobsterName: player.lobsterName,
        lobsterDesc: player.lobsterDesc,
        skillDesc: skillDesc
    }
    showLobsterPopup.value = true
}

function closeLobsterPopup() {
    showLobsterPopup.value = false
}

function showResult() {
    if (resultShown.value || !battleData.value?.winner) return
    resultShown.value = true

    const winnerIndex = battleData.value.winner.id === battleData.value.players[0].id ? 0 : 1
    loser.value = battleData.value.players[1 - winnerIndex]

    if (battleStore.myPlayerIndex < 0) {
        showDefeat.value = true
    } else {
        battleStore.myPlayerIndex === winnerIndex ? (showVictory.value = true) : (showDefeat.value = true)
    }
}

function selectReward(choice) {
    battleStore.applyWinnerAward(choice)
    battleStore.broadcastRewardSelected()
    showVictory.value = false
    showDefeat.value = false
    navigateBackToGame()
}

function closeResult() {
    showVictory.value = false
    showDefeat.value = false
    navigateBackToGame()
}

function exitBattle() {
    showExitPopup.value = true
}

function confirmExit() {
    showExitPopup.value = false
    loser.value = battleData.value.players[battleStore.myPlayerIndex]
    battleStore.quitBattle()
    resultShown.value = true
    showDefeat.value = true
}

function cancelExit() {
    showExitPopup.value = false
}

function navigateBackToGame() {
    // 使用 store 中的队列数据
    const battleQueue = onlineGameStore.arenaBattleQueue

    // 检查 arenaBattleQueue 中是否还有战斗
    if (battleQueue && battleQueue.length > 0) {
        // 保存队列到本地存储，使用 roomId 作为 key 区分不同房间
        const storageKey = `arenaBattleQueue_${savedRoomId.value}`
        uni.setStorageSync(storageKey, battleQueue)

        // 还有战斗，返回 online-game 页面，触发下一场战斗
        battleStore.resetBattle()
        resultShown.value = false
        showVictory.value = false
        showDefeat.value = false

        // 返回 online-game 页面，watch 会自动检测到队列变化并显示下一场
        if (savedRoomId.value && savedPlayerId.value !== null) {
            uni.reLaunch({
                url: `/pages/online-game/onlineGame?roomId=${savedRoomId.value}&playerId=${savedPlayerId.value}`
            })
        } else {
            uni.reLaunch({ url: '/pages/online-game/onlineGame' })
        }

        return
    }

    // 没有剩余战斗，正常返回 game 页面
    battleStore.resetBattle()
    resultShown.value = false
    showVictory.value = false
    showDefeat.value = false

    if (savedRoomId.value && savedPlayerId.value !== null) {
        uni.reLaunch({ url: `/pages/game/game?roomId=${savedRoomId.value}&playerId=${savedPlayerId.value}` })
    } else {
        uni.reLaunch({ url: '/pages/game/game' })
    }
}

watch(
    () => battleData.value?.battleLog?.length,
    (newLen) => {
        if (newLen > 0) {
            nextTick(() => {
                logScrollId.value = 'log-' + (newLen - 1)
                setTimeout(() => {
                    logScrollId.value = ''
                }, 100)
            })
        }
    }
)

let lastHandledIdentifier = null

watch(
    () => battleData.value?.lastAction,
    (action) => {
        if (action === 'diceConfirmed') {
            battleStore.applyDiceResult()
            displayDice.value = null
            rollCompleted.value = false
        }
    }
)

watch(
    () => battleData.value?.rollDiceTimestamp,
    (newTimestamp) => {
        if (pendingApplyTimer) {
            clearTimeout(pendingApplyTimer)
            pendingApplyTimer = null
        }

        if (!newTimestamp) {
            displayDice.value = null
            isRolling.value = false
            rollCompleted.value = false
            return
        }

        lastLogMessage.value = ''

        const diceRoller = battleData.value?.diceRoller
        const newDice = battleData.value?.diceValue
        if (diceRoller === undefined || diceRoller === null || !newDice) return

        isRolling.value = true
        rollCompleted.value = false
        const animationDuration = 1000
        const interval = 100
        const steps = animationDuration / interval

        let step = 0
        const rollInterval = setInterval(() => {
            step++
            displayDice.value = Math.floor(Math.random() * 6) + 1
            if (step >= steps) {
                clearInterval(rollInterval)
                displayDice.value = battleData.value?.diceValue || newDice
                isRolling.value = false
                rollCompleted.value = true

                if (!battleStore.canReroll && diceRoller === battleStore.myPlayerIndex) {
                    pendingApplyTimer = setTimeout(() => {
                        pendingApplyTimer = null
                        battleStore.applyDiceResult()
                        displayDice.value = null
                        rollCompleted.value = false
                    }, 1500)
                }
            }
        }, interval)
    }
)

watch(
    () => battleData.value?.phase,
    (phase) => {
        if (phase === 'initiative' && !showInitiativeOverlay.value) {
            nextTick(() => {
                setTimeout(triggerInitiativeRoll, 500)
            })
        }
        if (phase === 'ended' && battleData.value?.winner) {
            setTimeout(showResult, 500)
        }
    }
)

// 等待先手骰子同步数据到达后触发动画（覆盖非房主和race condition场景）
watch(
    () => battleData.value?.initiative,
    (newInitiative) => {
        if (showInitiativeOverlay.value && newInitiative?.p1 !== null && newInitiative?.p2 !== null) {
            playInitiativeAnimation({ p1: newInitiative.p1, p2: newInitiative.p2 }, true)
        }
    },
    { deep: true }
)

// 回合切换时重置海草状态
watch(
    () => battleData.value?.currentPlayer,
    () => {
        isSeaweedChecked.value = false
        seaweedLocked.value = false
    }
)

onMounted(() => {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    const options = currentPage.options || {}

    let player1Data = {}
    let player2Data = {}
    let battleDataFromParams = null

    try {
        if (options.player1) player1Data = JSON.parse(decodeURIComponent(options.player1))
        if (options.player2) player2Data = JSON.parse(decodeURIComponent(options.player2))
        if (options.battleData) battleDataFromParams = JSON.parse(decodeURIComponent(options.battleData))
    } catch (e) {
        console.error('解析玩家数据失败:', e)
    }

    const myPlayerId = parseInt(options.playerId)
    savedRoomId.value = options.roomId
    savedPlayerId.value = myPlayerId

    const autoMyIndex = parseInt(player1Data.id) === myPlayerId ? 0 : parseInt(player2Data.id) === myPlayerId ? 1 : -1

    if (player1Data.id !== undefined && player2Data.id !== undefined) {
        battleStore.initBattle(player1Data, player2Data, {
            myPlayerIndex: autoMyIndex,
            roomId: options.roomId,
            initialCurrentPlayer: battleDataFromParams?.currentPlayer ?? 0,
            challengeSlotIndex: options.challengeSlot
                ? parseInt(options.challengeSlot)
                : (battleDataFromParams?.challengeSlotIndex ?? null)
        })
    }

    initBoard()

    socketService.on('battleAction', (data) => {
        if (data.battleData) {
            // 跳过自己发送的消息回显，避免覆盖本地已处理的状态（如 diceConfirmed → turnChange）
            if (data.senderId !== savedPlayerId.value) {
                battleStore.updateFromSync(data.battleData)
            }

            // 监听奖励选择完成，只有胜者才触发返回逻辑
            if (data.battleData.lastAction === 'rewardSelected') {
                const winnerId = data.battleData.winner?.id
                // 只有获胜的玩家才会触发返回，避免重复调用
                if (winnerId === savedPlayerId.value) {
                    showVictory.value = false
                    showDefeat.value = false
                    navigateBackToGame()
                }
            }
        }
    })
})

onUnmounted(() => {
    battleStore.resetBattle()
    resultShown.value = false
    socketService.off('battleAction')
})
</script>
