import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import socketModule from '@utils/socket.js'
import { usePlayerStore } from '@stores/player'
import {
    DEFAULT_SLOT_STYLE,
    getOccupiedSlotStyle,
    AREA_CONFIG,
    SLOT_STATUS,
    PLACEMENT_ERRORS
} from '@utils/slotConstants'
import { SHRIMP_CATCHING_SLOTS, calculateShrimpCatchingReward, executeShrimpCatching } from '@utils/shrimpCatchingUtils'
import { createLobster } from '@utils/gameUtils'
import { getNextLobsterGrade } from '@utils/gameUtils'

const socketService = socketModule.socketService || socketModule

export const LOBSTER_GRADES = {
    NORMAL: 'normal',
    GRADE3: 'grade3',
    GRADE2: 'grade2',
    GRADE1: 'grade1',
    ROYAL: 'royal'
}

export const GAME_PHASES = {
    PREPARATION: 'preparation',
    PLACEMENT: 'placement',
    SETTLEMENT: 'settlement',
    CLEANUP: 'cleanup'
}

export const AREA_NAMES = {
    fishing: '捕虾区',
    market: '海鲜市场',
    cultivation: '养蛊区',
    tribute: '上供区',
    downtown: '闹市区'
}

export const useOnlineGameStore = defineStore('online-game', () => {
    // ============ 基础联机状态 ============
    const maxRounds = 5
    const roomId = ref('')
    const playerId = ref(null)
    const isConnected = ref(false)
    const isOnlineMode = ref(false)

    const currentPlayerIndex = ref(0)
    const currentRound = ref(1)
    const currentPhase = ref('waiting')
    const currentArea = ref('')
    const status = ref('waiting')
    const areas = ref({})
    const tributeTasks = ref([])
    const downtownCards = ref([])
    const gameState = ref(null)
    const lastPlacement = ref(null)

    // 玩家store
    const playerStore = usePlayerStore()

    // ============ 游戏资源状态（复刻game.js） ============
    const wildLobsterPool = ref([])
    const seafoodMarketLobsters = ref(0)
    const gameTitleCards = ref([])
    const gameTributeCards = ref([])
    const gameMarketplaceCards = ref([])
    const taverns = ref([])
    const royalLobsterCount = ref(0)
    const logs = ref([])

    // ============ 放置机制核心状态（复刻game.js） ============
    const slotOccupancy = ref({})
    const placementOrder = ref([])
    const currentPlacementIndex = ref(0)

    // ============ 竞技场状态 ============
    const arenaBattleQueue = ref([])
    const currentArenaBattle = ref(null)
    const arenaPhase = ref('idle') // 'idle' | 'betting' | 'ready'
    const challengerLobster = ref(null)
    const defenderLobster = ref(null)
    const challengerReady = ref(false)
    const defenderReady = ref(false)
    const challengerSelectedLobster = ref(null)
    const defenderSelectedLobster = ref(null)
    const spectatorBets = ref({})

    // ============ 结算阶段UI状态 ============
    const pendingSettlement = ref(null) // { areaType, playerId, actionCount, player, prices, availableCards, marketLobsterCount }

    // ============ 上供区UI状态 ============
    const pendingTribute = ref(null) // { player, slotIndex, taverns, tributeTasks, resolve }

    // ============ 同回合龙虾出战记录 ============
    const usedLobstersThisRound = ref({}) // { playerId: [lobsterId, ...] }

    // ============ 计算属性 ============
    const myPlayer = computed(() => {
        if (playerId.value === null) return null
        return playerStore.getPlayerById(playerId.value)
    })

    const isMyTurn = computed(() => currentPlayerIndex.value === playerId.value)

    const isPlacementPhase = computed(() => currentPhase.value === GAME_PHASES.PLACEMENT)

    const currentRoundDisplay = computed(() => `${currentRound.value}/5`)

    const phaseText = computed(() => {
        const phaseMap = {
            waiting: '等待中',
            preparation: '准备',
            placement: '工放',
            settlement: '结算',
            cleanup: '清理',
            ended: '结束'
        }
        return phaseMap[currentPhase.value] || '未知'
    })

    // ============ 日志工具（复刻game.js） ============
    const addLog = (message, type = 'info') => {
        logs.value.push({
            timestamp: Date.now(),
            message,
            type,
            round: currentRound.value,
            phase: currentPhase.value
        })
    }

    // ============ 服务端->客户端  ============
    function setupSocketListeners() {
        socketService.on('connect', () => {
            isConnected.value = true
        })

        socketService.on('disconnect', () => {
            isConnected.value = false
        })

        socketService.on('connectError', () => {
            isConnected.value = false
        })

        // serverGameAction 聚合事件
        socketService.onAction('serverGameAction', 'gameStateUpdate', handleGameStateUpdate)
        socketService.onAction('serverGameAction', 'gameStarted', handleGameStarted)
        socketService.onAction('serverGameAction', 'roundStarted', handleRoundStarted)
        socketService.onAction('serverGameAction', 'gameEnded', handleGameEnded)
        socketService.onAction('serverGameAction', 'gameAction', handleGameAction)
        socketService.onAction('serverGameAction', 'tributeChoiceRequired', handleTributeChoiceRequired)
        socketService.onAction('serverGameAction', 'endgameScoreChoiceRequired', handleEndgameScoreChoiceRequired)

        // serverBattleAction 聚合事件
        socketService.onAction('serverBattleAction', 'battleStart', handleBattleStart)
        socketService.onAction('serverBattleAction', 'lobsterSelected', handleLobsterSelected)
        socketService.onAction('serverBattleAction', 'arenaBettingStart', handleArenaBettingStart)
        socketService.onAction('serverBattleAction', 'arenaBettingComplete', handleArenaBettingComplete)
        socketService.onAction('serverBattleAction', 'betResult', handleBetResult)
        socketService.onAction('serverBattleAction', 'battleEnded', handleBattleEnded)

        // serverAreaAction 聚合事件
        socketService.onAction('serverAreaAction', 'areaSettlementStart', handleAreaSettlementStart)
        socketService.onAction('serverAreaAction', 'areaActionComplete', handleAreaActionComplete)
        socketService.onAction('serverAreaAction', 'settlementComplete', handleSettlementComplete)
        socketService.onAction('serverAreaAction', 'areaWaitingUI', handleAreaWaitingUI)

        // 独立事件
        socketService.on('playerResourceUpdate', handlePlayerResourceUpdate)
        socketService.on('error', (data) => {
            uni.showToast({ title: data.message || '发生错误', icon: 'none' })
        })
    }

    const hasValidLobsters = (player) => {
        if (!player) return false
        const validLobsters = player.lobsters?.filter((l) => l?.id && l.id !== 'normal') || []
        const hasTitleCards = player.titleCards?.length > 0
        return validLobsters.length > 0 || hasTitleCards
    }

    function handleGameStarted(data) {
        status.value = 'playing'
        currentPhase.value = data.phase || 'placement'
        currentRound.value = data.currentRound || 1
        currentPlayerIndex.value = data.currentPlayerIndex || 0
        if (data.players) {
            playerStore.syncPlayers(data.players)
        }
        if (data.areas) areas.value = data.areas
        if (data.tributeTasks) tributeTasks.value = data.tributeTasks
        if (data.downtownCards) downtownCards.value = data.downtownCards
        if (data.lastPlacement !== undefined) lastPlacement.value = data.lastPlacement
        gameState.value = data
    }

    function handleRoundStarted(data) {
        if (data.round) currentRound.value = data.round
        currentPhase.value = 'placement'
        resetUsedLobsters()
        if (data.gameState) updateGameState(data.gameState)
    }

    function handleGameEnded(data) {
        status.value = 'ended'
        if (data.winner) {
            uni.showModal({
                title: '游戏结束',
                content: `${data.winner.name} 获得胜利！`,
                showCancel: false,
                success: () => {
                    reset()
                    uni.redirectTo({ url: '/pages/index/index' })
                }
            })
        }
    }

    function handleGameAction(data) {
        const actionType = data.actionType
        if (
            actionType === 'signalsExchanged' ||
            actionType === 'itemBought' ||
            actionType === 'itemSold' ||
            actionType === 'lobsterCultivated' ||
            actionType === 'tributeSubmitted' ||
            actionType === 'downtownActionExecuted'
        ) {
            if (data.gameState) updateGameState(data.gameState)
        }
    }

    function handleTributeChoiceRequired(data) {
        const { choiceType, taskId, playerId } = data?.data || data || {}
        console.log('[tributeChoiceRequired] choiceType:', choiceType, 'taskId:', taskId)

        if (choiceType === 'buy_advanced_lobster') {
            uni.showModal({
                title: '选择龙虾品级',
                content: '选择要获得的龙虾品级',
                confirmText: '普通龙虾',
                cancelText: '进阶龙虾',
                success: function (res) {
                    if (!res.confirm && !res.cancel) {
                        return
                    }
                    const grade = res.confirm ? 'normal' : 'grade1'
                    socketService.clientGameAction('submitTributeChoice', {
                        taskId: taskId,
                        choice: { grade: grade }
                    })
                },
                fail: function () {
                    uni.showToast({ title: '请做出选择', icon: 'none' })
                }
            })
        } else if (choiceType === 'discard_attack') {
            uni.showModal({
                title: '选择目标类型',
                content: '所有其他玩家将弃置1个对应的资源',
                confirmText: '龙虾',
                cancelText: '虾笼',
                success: function (res) {
                    if (!res.confirm && !res.cancel) {
                        return
                    }
                    const targetType = res.confirm ? 'lobster' : 'cage'
                    socketService.clientGameAction('submitTributeChoice', {
                        taskId: taskId,
                        choice: { action: 'discard', targetType: targetType }
                    })
                },
                fail: function () {
                    uni.showToast({ title: '请做出选择', icon: 'none' })
                }
            })
        }
    }

    function handleEndgameScoreChoiceRequired(data) {
        const { choices, card } = data?.data || data || {}
        const costResourceType = card?.costResourceType || 'coins'
        const resourceName = costResourceType === 'coins' ? '金币' : '海草'

        const options = (choices || []).map(function (c) {
            return '支付' + c.cost + resourceName + '获得' + c.reward + '德'
        })

        if (options.length === 0) {
            uni.showToast({ title: '没有可用的选择', icon: 'none' })
            return
        }

        uni.showActionSheet({
            itemList: options,
            success: function (res) {
                const selectedChoice = choices?.[res.tapIndex]
                if (!selectedChoice) {
                    uni.showToast({ title: '选择无效', icon: 'none' })
                    return
                }
                socketService.clientGameAction('submitEndgameChoice', {
                    choice: selectedChoice
                })
            },
            fail: function () {
                uni.showToast({ title: '请做出选择', icon: 'none' })
            }
        })
    }

    function handleGameStateUpdate(data) {
        if (data.areas) areas.value = data.areas
        if (data.phase) currentPhase.value = data.phase
        if (data.currentRound) currentRound.value = data.currentRound
        if (data.currentPlayerIndex !== undefined) currentPlayerIndex.value = data.currentPlayerIndex
        if (data.currentArea !== undefined) {
            const areaNames = ['shrimp_catching', 'seafood_market', 'breeding', 'tribute', 'marketplace']
            currentArea.value = areaNames[data.currentArea] || ''
        }
        if (data.status) status.value = data.status
    }

    function handleSettlementComplete(data) {
        if (data.gameState) updateGameState(data.gameState)
        currentPhase.value = 'placement'
    }

    function handleAreaSettlementStart(data) {
        if (data.areaType) {
            currentPhase.value = 'settlement'
            currentArea.value = data.areaType
            pendingSettlement.value = null
            arenaBattleQueue.value = []
            currentArenaBattle.value = null
        }
        if (data.gameState) updateGameState(data.gameState)
    }

    function handleAreaActionComplete(data) {
        if (data.gameState) updateGameState(data.gameState)
        if (data.nextArea) {
            currentArea.value = data.nextArea
        }
    }

    function handleAreaWaitingUI(data) {
        console.log('[handleAreaWaitingUI] Received:', JSON.stringify(data))
        if (data.areaType) {
            currentPhase.value = 'settlement'
            // 非上供区等待UI时，清空竞技场队列，防止旧数据干扰
            if (data.areaType !== 'tribute') {
                arenaBattleQueue.value = []
                currentArenaBattle.value = null
            }
            pendingSettlement.value = {
                areaType: data.areaType,
                playerId: data.playerId,
                actionCount: data.actionCount,
                player: data.player,
                prices: data.prices,
                availableCards: data.availableCards,
                marketLobsterCount: data.marketLobsterCount,
                indicatorType: data.indicatorType,
                reward: data.reward,
                rewardGiven: data.rewardGiven,
                slotIndex: data.slotIndex,
                taverns: data.taverns,
                tributeTasks: data.tributeTasks,
                step: data.step,
                lastResult: data.lastResult,
                lastItem: data.lastItem
            }
            if (data.areaType === 'tribute') {
                pendingTribute.value = {
                    player: data.player,
                    slotIndex: data.slotIndex,
                    taverns: data.taverns || [],
                    tributeTasks: data.tributeTasks || []
                }
            }
        }
    }

    function handleBattleStart(data) {
        if (data.battleData) {
            const pages = getCurrentPages()
            const currentPage = pages[pages.length - 1]
            if (currentPage?.route === 'pages/arena/arena') {
                return
            }

            const battleDataStr = encodeURIComponent(JSON.stringify(data.battleData))
            const player1 = data.battleData.players?.[0]
            const player2 = data.battleData.players?.[1]
            if (player1 && player2) {
                const player1Str = encodeURIComponent(JSON.stringify(player1))
                const player2Str = encodeURIComponent(JSON.stringify(player2))
                uni.navigateTo({
                    url: `/pages/arena/arena?player1=${player1Str}&player2=${player2Str}&roomId=${roomId.value}&playerId=${playerId.value}&battleData=${battleDataStr}`
                })
            }
        } else if (data.battleQueue) {
            filterAndSetBattleQueue(data.battleQueue)
        }
    }

    function filterAndSetBattleQueue(rawQueue) {
        addLog('执行竞技场结算', 'info')
        arenaBattleQueue.value = []

        for (const battle of rawQueue) {
            const challenger = playerStore.players.find((p) => p.id === battle.challengerId)
            const defender = playerStore.players.find((p) => p.id === battle.defenderId)

            if (!hasValidLobsters(challenger)) {
                addLog(`${challenger?.name || '挑战者'}没有可参战的龙虾（普通龙虾除外），无法进行战斗`, 'warning')
                continue
            }
            if (!hasValidLobsters(defender)) {
                addLog(`${defender?.name || '被挑战者'}没有可参战的龙虾（普通龙虾除外），无法进行战斗`, 'warning')
                continue
            }

            arenaBattleQueue.value.push({
                challengerId: battle.challengerId,
                defenderId: battle.defenderId,
                slotIndex: battle.challengeSlot
            })

            addLog(`${challenger.name} 挑战 ${defender.name}！`, 'success')
        }

        if (arenaBattleQueue.value.length > 0) {
            addLog(`竞技场有${arenaBattleQueue.value.length}场战斗需要进行`, 'info')
            setCurrentArenaBattle(0)
        } else {
            addLog('竞技场没有需要进行的战斗', 'info')
        }
    }

    function handleLobsterSelected(data) {
        if (String(data.playerId) === String(playerId.value)) return

        const battle = currentArenaBattle.value
        if (!battle) return

        const isChallenger = String(data.playerId) === String(battle.challenger?.id)
        const isDefender = String(data.playerId) === String(battle.defender?.id)

        if (isChallenger) {
            challengerReady.value = true
            challengerSelectedLobster.value = data.lobster
        } else if (isDefender) {
            defenderReady.value = true
            defenderSelectedLobster.value = data.lobster
        }
    }

    function handleArenaBettingStart(data) {
        challengerLobster.value = data.challengerLobster
        defenderLobster.value = data.defenderLobster
        arenaPhase.value = 'betting'
        addLog('观战者投注阶段开始', 'info')
    }

    function handleArenaBettingComplete(data) {
        spectatorBets.value = data.bets || {}
        arenaPhase.value = 'ready'
        addLog('投注阶段结束，即将进入竞技场', 'info')
    }

    function handleBetResult(data) {
        const myResult = data.betResults?.[String(playerId.value)]
        if (myResult?.won) {
            addLog(`投注成功！获得 ${myResult.reward} 金币`, 'success')
            playerStore.updatePlayerResources(playerId.value, { coins: myResult.reward })
        } else if (myResult && !myResult.won) {
            addLog('投注失败', 'warning')
        }
    }

    function handlePlayerResourceUpdate(data) {
        if (data.playerId === undefined || data.playerId === null || !data.resources) return

        const numericPlayerId = Number(data.playerId)
        playerStore.updatePlayerResources(numericPlayerId, data.resources)
    }

    function handleBattleEnded(data) {
        const { winnerId, upgradeFrom, upgradeTo, winnerLobsterId } = data
        if (winnerId !== null && upgradeFrom && upgradeTo) {
            const winner = playerStore.getPlayerById(winnerId)
            if (winner && winner.lobsters) {
                let lobster = null
                if (winnerLobsterId) {
                    lobster = winner.lobsters.find((l) => l.id === winnerLobsterId)
                }
                if (!lobster) {
                    lobster = winner.lobsters.find((l) => l.grade === upgradeFrom)
                }
                if (lobster) {
                    lobster.grade = upgradeTo
                }
            }
        }
    }

    function setArenaPhase(phase) {
        arenaPhase.value = phase
    }

    function updateGameState(data) {
        if (data.players) playerStore.syncPlayers(data.players)
        if (data.areas) areas.value = data.areas
        if (data.phase) currentPhase.value = data.phase
        if (data.currentRound) currentRound.value = data.currentRound
        if (data.currentPlayerIndex !== undefined) currentPlayerIndex.value = data.currentPlayerIndex
        if (data.status) status.value = data.status
        if (data.tributeTasks) tributeTasks.value = data.tributeTasks
        if (data.downtownCards) downtownCards.value = data.downtownCards
        if (data.lastPlacement !== undefined) lastPlacement.value = data.lastPlacement
        gameState.value = data
    }

    // ============ 客户端->服务端 ============
    function sendGameAction(actionType, payload = {}) {
        const turnRequiredActions = ['placeHeadman', 'nextPlayer', 'nextArea']

        if (turnRequiredActions.includes(actionType) && !isMyTurn.value) {
            uni.showToast({ title: '不是你的回合', icon: 'none' })
            return false
        }
        socketService.clientGameAction(actionType, payload)
        return true
    }

    function sendSettlementAction(actionType, payload = {}) {
        socketService.clientGameAction('areaAction', {
            actionType,
            payload
        })
    }

    function cancelHeadmanAction() {
        if (!isMyTurn.value) {
            uni.showToast({ title: '不是你的回合', icon: 'none' })
            return false
        }
        socketService.clientGameAction('cancelHeadman', {})
        return true
    }

    function clearPendingSettlement() {
        pendingSettlement.value = null
    }

    function clearPendingTribute() {
        pendingTribute.value = null
    }

    // ============ 龙虾出战管理 ============

    const markLobsterUsed = (playerId, lobsterId) => {
        const pid = String(playerId)
        if (!usedLobstersThisRound.value[pid]) {
            usedLobstersThisRound.value[pid] = []
        }
        if (!usedLobstersThisRound.value[pid].includes(lobsterId)) {
            usedLobstersThisRound.value[pid].push(lobsterId)
        }
    }

    const getUsedLobsterIds = (playerId) => {
        return usedLobstersThisRound.value[String(playerId)] || []
    }

    const getAvailableLobstersForBattle = (playerId) => {
        const player = playerStore.players.find((p) => p.id === playerId)
        if (!player) return []
        const usedIds = new Set(getUsedLobsterIds(playerId))
        const validLobsters = player.lobsters?.filter((l) => l?.id && l.id !== 'normal' && !usedIds.has(l.id)) || []
        const titleCards = player.titleCards?.filter((t) => t?.id && !usedIds.has(t.id)) || []
        return [...validLobsters, ...titleCards]
    }

    const resetUsedLobsters = () => {
        usedLobstersThisRound.value = {}
    }

    function cleanupListeners() {
        socketService.off('connect')
        socketService.off('disconnect')
        socketService.off('connectError')
        socketService.offAction('serverGameAction')
        socketService.offAction('serverBattleAction')
        socketService.offAction('serverAreaAction')
        socketService.off('playerResourceUpdate')
        socketService.off('error')
    }

    // ============ 初始化方法 ============
    function initOnlineMode(rId, pId) {
        roomId.value = rId
        playerId.value = pId
        isOnlineMode.value = true
        setupSocketListeners()
    }

    function reset() {
        roomId.value = ''
        playerId.value = null
        isConnected.value = false
        isOnlineMode.value = false
        gameState.value = null
        playerStore.resetPlayers()
        currentPlayerIndex.value = 0
        currentRound.value = 1
        currentPhase.value = 'waiting'
        status.value = 'waiting'
        areas.value = {}
        tributeTasks.value = []
        downtownCards.value = []

        wildLobsterPool.value = []
        seafoodMarketLobsters.value = 0
        gameTitleCards.value = []
        gameTributeCards.value = []
        gameMarketplaceCards.value = []
        taverns.value = []
        royalLobsterCount.value = 0
        logs.value = []

        slotOccupancy.value = {}
        placementOrder.value = []
        currentPlacementIndex.value = 0

        arenaBattleQueue.value = []
        currentArenaBattle.value = null
        arenaPhase.value = 'idle'
        challengerLobster.value = null
        defenderLobster.value = null
        challengerReady.value = false
        defenderReady.value = false
        challengerSelectedLobster.value = null
        defenderSelectedLobster.value = null
        spectatorBets.value = {}
        usedLobstersThisRound.value = {}
        pendingSettlement.value = null
        cleanupListeners()
    }

    function resetArenaBattleState() {
        arenaPhase.value = 'idle'
        challengerLobster.value = null
        defenderLobster.value = null
        challengerReady.value = false
        defenderReady.value = false
        challengerSelectedLobster.value = null
        defenderSelectedLobster.value = null
        spectatorBets.value = {}
    }

    // ============ 工具方法（复刻game.js） ============
    function getAreaName(areaKey) {
        return AREA_NAMES[areaKey] || areaKey
    }

    function isSlotOccupied(areaKey, slotIndex) {
        const area = areas.value[areaKey]
        if (!area || !area.slots) return false
        const slot = area.slots[slotIndex]
        if (slot === undefined || slot === null) return false
        if (typeof slot === 'object') return slot.occupiedBy !== null && slot.occupiedBy !== undefined
        return true
    }

    function getSlotOccupant(areaKey, slotIndex) {
        const area = areas.value[areaKey]
        if (!area || !area.slots) return null
        const slot = area.slots[slotIndex]
        if (slot === undefined || slot === null) return null
        if (typeof slot === 'object') return slot.occupiedBy
        return slot
    }

    const getSlotStatus = (area, slotIndex) => {
        const key = `${area}_${slotIndex}`
        const occupancy = slotOccupancy.value[key]

        if (occupancy && occupancy.round === currentRound.value) {
            return {
                status: SLOT_STATUS.OCCUPIED,
                playerId: occupancy.playerId,
                ...occupancy
            }
        }

        return { status: SLOT_STATUS.EMPTY, playerId: null }
    }

    // ============ 竞技场方法 ============
    const setCurrentArenaBattle = (index) => {
        if (index < 0 || index >= arenaBattleQueue.value.length) {
            currentArenaBattle.value = null
            return
        }

        const battle = arenaBattleQueue.value[index]
        const challenger = playerStore.players.find((p) => p.id === battle.challengerId)
        const defender = playerStore.players.find((p) => p.id === battle.defenderId)

        currentArenaBattle.value = {
            index,
            challenger,
            defender,
            slotIndex: battle.slotIndex
        }
    }

    const getAvailableLobsters = (playerId) => {
        const player = playerStore.players.find((p) => p.id === playerId)
        if (!player) return []
        return player.lobsters.filter((lobster) => lobster && lobster.grade)
    }

    // ============ 导出 ============
    return {
        // 基础联机状态
        maxRounds,
        roomId,
        playerId,
        isConnected,
        isOnlineMode,
        currentPlayerIndex,
        currentRound,
        currentPhase,
        currentArea,
        status,
        areas,
        tributeTasks,
        downtownCards,
        gameState,
        lastPlacement,

        // 游戏资源状态
        wildLobsterPool,
        seafoodMarketLobsters,
        gameTitleCards,
        gameTributeCards,
        gameMarketplaceCards,
        taverns,
        royalLobsterCount,
        logs,

        // 放置机制状态
        slotOccupancy,
        placementOrder,
        currentPlacementIndex,

        // 竞技场状态
        arenaBattleQueue,
        currentArenaBattle,
        arenaPhase,
        challengerLobster,
        defenderLobster,
        challengerReady,
        defenderReady,
        challengerSelectedLobster,
        defenderSelectedLobster,
        spectatorBets,

        // 结算阶段UI状态
        pendingSettlement,

        // 计算属性
        myPlayer,
        isMyTurn,
        isPlacementPhase,
        currentRoundDisplay,
        phaseText,

        // 方法
        initOnlineMode,
        setupSocketListeners,
        cleanupListeners,
        reset,
        updateGameState,
        sendGameAction,
        getAreaName,
        isSlotOccupied,
        getSlotOccupant,
        getSlotStatus,
        addLog,

        // 竞技场方法
        setCurrentArenaBattle,
        getAvailableLobsters,
        setArenaPhase,
        markLobsterUsed,
        getUsedLobsterIds,
        getAvailableLobstersForBattle,
        resetUsedLobsters,
        resetArenaBattleState,

        // 结算阶段
        sendSettlementAction,
        clearPendingSettlement,
        clearPendingTribute,
        pendingTribute,

        // 放置阶段
        cancelHeadmanAction
    }
})
