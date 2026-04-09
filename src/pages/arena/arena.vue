<template>
    <view class="battle-container">
        <!-- #ifdef H5 -->
        <!-- H5 使用 CSS background -->
        <!-- #endif -->
        <!-- #ifndef H5 -->
        <image class="bg-image" src="@/static/images/battle_bg.png" mode="aspectFill" />
        <!-- #endif -->

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

        <view v-if="showVictory" class="victory-overlay">
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

        <view v-if="showDefeat" class="defeat-overlay">
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
import { usePlayerStore } from '@stores/player.js'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule

const battleStore = useBattleStore()
const onlineGameStore = useOnlineGameStore()
const playerStore = usePlayerStore()

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

// ============ 海草状态 ============

const seaweedCount = computed(() => {
    const player = playerStore.getPlayerById(savedPlayerId.value)
    return player?.seaweed || 0
})
const isSeaweedChecked = ref(false)
const seaweedLocked = ref(false)

const canUseSeaweed = computed(() => {
    if (seaweedCount.value <= 0) return false
    if (battleData.value?.currentPlayer !== battleStore.myPlayerIndex) return false
    if (battleData.value?.phase !== 'rolling') return false
    if (seaweedLocked.value) return false
    if (battleStore.canReroll) return false
    if (battleData.value?.rollDiceTimestamp) return false
    const player = battleData.value?.players[battleData.value?.currentPlayer]
    if (player?.lobsterGrade === 'grade3') return false
    const opponentIndex = 1 - battleData.value?.currentPlayer
    const opponent = battleData.value?.players[opponentIndex]
    if (opponent && player?.lobsterSkill?.blockSeaweed) return false
    return true
})

const seaweedBonus = computed(() => {
    if (!isSeaweedChecked.value) return 0
    const player = battleData.value?.players[battleData.value?.currentPlayer]
    let base
    switch (player?.lobsterGrade) {
        case 'grade2':
            base = 1
            break
        case 'grade1':
            base = 2
            break
        default:
            base = 3
    }
    const bonus = player?.lobsterSkill?.seaweedDiceBonus || 0
    return base + bonus
})

// ============ 计算属性 ============

const battleData = computed(() => battleStore.battleData)

const winnerCanUpgrade = computed(() => {
    const grade = battleData.value?.winner?.lobsterGrade
    return grade === 'normal' || grade === 'grade3' || grade === 'grade2' || grade === 'grade1'
})

const isWinner = computed(() => {
    if (battleStore.myPlayerIndex < 0) return true
    return battleData.value?.winner?.id === savedPlayerId.value
})

const DICE_IMAGE_MAP = {
    6: '/static/images/dice_d6.png',
    8: '/static/images/dice_d8.png',
    10: '/static/images/dice_d10.png',
    12: '/static/images/dice_d12.png'
}

const currentDiceImage = computed(() => {
    return DICE_IMAGE_MAP[battleStore.getDiceSides(battleData.value?.currentPlayer)] || DICE_IMAGE_MAP[6]
})

// ============ 棋盘 & 龙虾可见性 ============

const getInitialPosition = (playerIndex) => (playerIndex === 0 ? -1 : battleData.value?.totalCells || 8)

const getLobsterImage = (playerIndex) =>
    playerIndex === 0 ? '/static/images/lobster_left.png' : '/static/images/lobster_right.png'

const animatingPlayers = ref([false, false])
const movingPlayers = ref([false, false])

const getLobsterWrapperClass = (playerIndex) => {
    const classes = []
    const player = battleData.value?.players[playerIndex]
    if (player?.started) classes.push('movable')
    if (animatingPlayers.value[playerIndex]) classes.push('animating')
    return classes.join(' ')
}

const getMovingClass = (playerIndex) => (movingPlayers.value[playerIndex] ? 'moving' : '')

const shouldShowLobsterWrapper = (playerIndex) => {
    const player = battleData.value?.players[playerIndex]
    if (!player) return false
    if (animatingPlayers.value[playerIndex]) return true
    if (!player.started) return true
    return player.position === getInitialPosition(playerIndex)
}

const shouldShowOnBoard = (playerIndex) => {
    const player = battleData.value?.players[playerIndex]
    if (!player) return false
    if (!player.started) return false
    if (player.position === getInitialPosition(playerIndex)) return false
    return !animatingPlayers.value[playerIndex]
}

const handlePositionChange = (playerIndex, oldPos, newPos) => {
    const player = battleData.value?.players[playerIndex]
    if (!player) return
    if (player.started) {
        if (oldPos === getInitialPosition(playerIndex)) {
            animatingPlayers.value[playerIndex] = true
            animateLobsterMove(playerIndex)
        } else {
            movingPlayers.value[playerIndex] = true
            setTimeout(() => {
                movingPlayers.value[playerIndex] = false
            }, 500)
        }
    } else {
        movingPlayers.value[playerIndex] = true
        setTimeout(() => {
            movingPlayers.value[playerIndex] = false
        }, 500)
    }
}

watch(
    () => [battleData.value?.players[0]?.position, battleData.value?.players[1]?.position],
    (newPositions, oldPositions) => {
        if (!oldPositions) return
        for (let i = 0; i < 2; i++) {
            if (newPositions[i] !== oldPositions[i] && newPositions[i] != null) {
                handlePositionChange(i, oldPositions[i], newPositions[i])
            }
        }
    },
    { deep: true }
)

// ============ 龙虾移动动画 ============

function animateLobsterMove(playerIndex) {
    if (!animatingPlayers.value[playerIndex]) return
    if (typeof document === 'undefined') {
        animatingPlayers.value[playerIndex] = false
        return
    }

    nextTick(() => {
        const wrapperClass = playerIndex === 0 ? '.player1-card .lobster-wrapper' : '.player2-card .lobster-wrapper'
        const wrapperEl = document.querySelector(wrapperClass)
        const player = battleData.value?.players[playerIndex]
        const boardElement = document.querySelector('.battle-board')
        if (!player || !boardElement) {
            animatingPlayers.value[playerIndex] = false
            return
        }

        const boardRect = boardElement.getBoundingClientRect()
        const totalCells = battleData.value?.totalCells || 8
        const cellWidth = boardRect.width / totalCells
        const targetX =
            playerIndex === 0
                ? boardRect.left + player.position * cellWidth
                : boardRect.left + (totalCells - player.position - 1) * cellWidth
        const targetY = boardRect.top + boardRect.height / 2

        if (wrapperEl) {
            const startRect = wrapperEl.getBoundingClientRect()
            const clone = document.createElement('div')
            clone.className = 'lobster-clone'
            clone.style.cssText = `position:fixed;top:${startRect.top}px;left:${startRect.left}px;width:${startRect.width}px;height:${startRect.height}px;z-index:1000;pointer-events:none;`
            const img = document.createElement('img')
            img.src = getLobsterImage(playerIndex)
            img.style.cssText = 'width:100%;height:100%;object-fit:contain;'
            clone.appendChild(img)
            document.body.appendChild(clone)
            wrapperEl.style.opacity = '0'

            setTimeout(() => {
                clone.classList.add('flash')
                clone.style.top = `${targetY - startRect.height / 2}px`
                clone.style.left = `${targetX - startRect.width / 2}px`
            }, 50)

            setTimeout(() => {
                clone.remove()
                wrapperEl.style.opacity = '1'
                animatingPlayers.value[playerIndex] = false
            }, 350)
        } else {
            animatingPlayers.value[playerIndex] = false
        }
    })
}

// ============ 棋盘初始化 ============

const halfIndex = computed(() => Math.floor((battleData.value?.totalCells || 8) / 2))
const leftCells = computed(() => boardCells.value.slice(0, halfIndex.value))
const rightCells = computed(() => boardCells.value.slice(halfIndex.value))

function initBoard() {
    const totalCells = battleData.value?.totalCells || 8
    boardCells.value = Array.from({ length: totalCells }, (_, i) => ({
        index: i,
        img: `battle_num${(i % 8) + 1}.png`
    }))
}

// ============ 日志 & 掷骰 ============

const lastLogMessage = ref('')
let logMessageTimer = null

watch(
    () => battleData.value?.battleLog,
    (logs) => {
        if (logMessageTimer) clearTimeout(logMessageTimer)
        if (!logs?.length) {
            lastLogMessage.value = ''
            return
        }
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
    return !battleData.value?.rollDiceTimestamp
})

function toggleSeaweed() {
    if (canUseSeaweed.value) isSeaweedChecked.value = !isSeaweedChecked.value
}

function onDiceClick() {
    if (!canRoll.value || isRolling.value) return
    const bonus = seaweedBonus.value
    if (bonus > 0) {
        socketService.clientGameAction('useSeaweed', {})
        seaweedLocked.value = true
    }
    const diceValue = battleStore.getDiceValue(battleData.value?.currentPlayer)
    battleStore.rollDice(diceValue + bonus, bonus)
}

function onReroll() {
    if (!battleStore.canReroll || isRolling.value) return
    displayDice.value = null
    rollCompleted.value = false
    const bonus = seaweedBonus.value
    const diceValue = battleStore.getDiceValue(battleData.value?.currentPlayer)
    battleStore.rollDice(diceValue + bonus, bonus)
}

function onConfirmDice() {
    if (!battleStore.canReroll || isConfirming.value) return
    isConfirming.value = true
    battleStore.confirmDice()
    setTimeout(() => {
        isConfirming.value = false
    }, 500)
}

// ============ 先手骰子动画 ============

const getInitiativeDiceImage = (playerIndex) =>
    DICE_IMAGE_MAP[battleStore.getDiceSides(playerIndex)] || DICE_IMAGE_MAP[6]

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
    const isHost = battleStore.myPlayerIndex === 0

    showInitiativeOverlay.value = true

    if (isFromSync) {
        return
    } else if (isHost) {
        battleStore.rollInitiativeDice()
    } else {
        return
    }
}

// ============ 龙虾信息弹窗 ============

function showLobsterInfo(playerIndex) {
    const player = battleData.value?.players[playerIndex]
    if (!player) return
    lobsterPopupData.value = {
        lobsterName: player.lobsterName,
        lobsterDesc: player.lobsterDesc,
        skillDesc: player.lobsterSkill || ''
    }
    showLobsterPopup.value = true
}

function closeLobsterPopup() {
    showLobsterPopup.value = false
}

// ============ 战斗结果 & 导航 ============

function showResult() {
    if (resultShown.value || !battleData.value?.winner) return
    if (battleData.value.winnerAwardChoice) return
    resultShown.value = true
    const winnerIndex = battleData.value.winner.id === battleData.value.players[0].id ? 0 : 1
    loser.value = battleData.value.players[1 - winnerIndex]
    if (battleStore.myPlayerIndex < 0) showDefeat.value = true
    else if (battleStore.myPlayerIndex === winnerIndex) showVictory.value = true
    else showDefeat.value = true
}

function selectReward(choice) {
    battleStore.applyWinnerAward(choice)
    showVictory.value = false
    showDefeat.value = false
}

function exitBattle() {
    showExitPopup.value = true
}

function cancelExit() {
    showExitPopup.value = false
}

function confirmExit() {
    showExitPopup.value = false
    loser.value = battleData.value.players[battleStore.myPlayerIndex]
    battleStore.quitBattle()
    resultShown.value = true
    showDefeat.value = true
}

const resetBattleState = () => {
    battleStore.resetBattle()
    resultShown.value = false
    showVictory.value = false
    showDefeat.value = false
}

const buildReturnUrl = () => {
    if (savedRoomId.value && savedPlayerId.value !== null) {
        return `/pages/online-game/onlineGame?roomId=${savedRoomId.value}&playerId=${savedPlayerId.value}`
    }
    return '/pages/online-game/onlineGame'
}

function navigateBackToGame() {
    const battleQueue = onlineGameStore.arenaBattleQueue
    let roomId = savedRoomId.value
    if (battleQueue?.length > 0) {
        const pages = getCurrentPages()
        const currentOptions = pages[pages.length - 1].options || {}
        roomId = currentOptions.roomId || savedRoomId.value
        uni.setStorageSync(`arenaBattleQueue_${roomId}`, battleQueue)
    }
    resetBattleState()

    // 强制使用 reLaunch 确保页面重新加载
    uni.reLaunch({ url: `/pages/online-game/onlineGame?roomId=${roomId}&playerId=${savedPlayerId.value}` })
}

// ============ 监听器 ============

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
        if (diceRoller == null || !newDice) return

        isRolling.value = true
        rollCompleted.value = false
        let step = 0
        const steps = 1000 / 100
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
        }, 100)
    }
)

watch(
    () => battleData.value?.phase,
    (phase) => {
        if (phase === 'ended' && battleData.value?.winner) {
            if (!battleData.value.winnerAwardChoice) {
                setTimeout(showResult, 500)
            }
        }
    }
)

watch(
    () => battleData.value?.winnerAwardChoice,
    (choice) => {
        if (choice) {
            navigateBackToGame()
        }
    }
)

watch(
    () => battleData.value?.initiative,
    (newInitiative) => {
        if (showInitiativeOverlay.value && newInitiative?.p1 !== null && newInitiative?.p2 !== null) {
            setTimeout(() => {
                playInitiativeAnimation({ p1: newInitiative.p1, p2: newInitiative.p2 }, false)
            }, 200)
        }
    },
    { deep: true }
)

watch(
    () => battleData.value?.currentPlayer,
    () => {
        isSeaweedChecked.value = false
        seaweedLocked.value = false
    }
)

// ============ 生命周期 ============

const parseArenaOptions = (options) => {
    let player1Data = {}
    let player2Data = {}
    let battleDataFromParams = null
    try {
        if (options.player1) player1Data = JSON.parse(decodeURIComponent(options.player1))
        if (options.player2) player2Data = JSON.parse(decodeURIComponent(options.player2))
        if (options.battleData) battleDataFromParams = JSON.parse(decodeURIComponent(options.battleData))
    } catch {
        // ignore parse errors
    }
    return { player1Data, player2Data, battleDataFromParams }
}

onMounted(() => {
    const options = getCurrentPages().slice(-1)[0].options || {}
    const { player1Data, player2Data, battleDataFromParams } = parseArenaOptions(options)
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

        if (battleStore.battleData?.phase === 'initiative') {
            triggerInitiativeRoll()
        }
    }

    initBoard()
    battleStore.setupBattleActionListener(() => {
        showVictory.value = false
        showDefeat.value = false
    })
})

onUnmounted(() => {
    battleStore.resetBattle()
    resultShown.value = false
    battleStore.cleanupBattleActionListener()
})
</script>
