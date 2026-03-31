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

    const players = ref([])
    const currentPlayerIndex = ref(0)
    const currentRound = ref(1)
    const currentPhase = ref('waiting')
    const status = ref('waiting')
    const areas = ref({})
    const tributeTasks = ref([])
    const downtownCards = ref([])
    const gameState = ref(null)

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

    // ============ 计算属性 ============
    const myPlayer = computed(() => {
        if (!players.value || playerId.value === null) return null
        return players.value.find((p) => p.id === playerId.value) || null
    })

    const isMyTurn = computed(() => {
        return currentPlayerIndex.value === playerId.value
    })

    const isPlacementPhase = computed(() => {
        return currentPhase.value === GAME_PHASES.PLACEMENT
    })

    const currentRoundDisplay = computed(() => {
        return `${currentRound.value}/5`
    })

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

    // ============ Socket 监听设置 ============
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

        socketService.on('roomStateUpdate', handleRoomStateUpdate)
        socketService.on('gameStarted', handleGameStarted)
        socketService.on('headmanPlaced', handleHeadmanPlaced)
        socketService.on('playerTurn', handlePlayerTurn)
        socketService.on('areaSettled', handleAreaSettled)
        socketService.on('roundStarted', handleRoundStarted)
        socketService.on('gameEnded', handleGameEnded)
        socketService.on('signalsExchanged', handleGenericUpdate)
        socketService.on('itemBought', handleGenericUpdate)
        socketService.on('itemSold', handleGenericUpdate)
        socketService.on('lobsterCultivated', handleGenericUpdate)
        socketService.on('tributeSubmitted', handleGenericUpdate)
        socketService.on('downtownActionExecuted', handleGenericUpdate)
        socketService.on('battleStart', handleBattleStart)
        socketService.on('lobsterSelected', handleLobsterSelected)
        socketService.on('arenaBettingStart', handleArenaBettingStart)
        socketService.on('arenaBettingComplete', handleArenaBettingComplete)
        socketService.on('betResult', handleBetResult)
        socketService.on('playerResourceUpdate', handlePlayerResourceUpdate)
        socketService.on('battleEnded', handleBattleEnded)
        socketService.on('error', (data) => {
            uni.showToast({ title: data.message || '发生错误', icon: 'none' })
        })
    }

    function handleRoomStateUpdate(data) {
        if (data.players) players.value = data.players
        if (data.status) status.value = data.status
        if (data.phase) currentPhase.value = data.phase
        if (data.currentRound) currentRound.value = data.currentRound
        if (data.currentPlayerIndex !== undefined) currentPlayerIndex.value = data.currentPlayerIndex
    }

    function handleGameStarted(data) {
        status.value = 'playing'
        currentPhase.value = data.phase || 'placement'
        currentRound.value = data.currentRound || 1
        currentPlayerIndex.value = data.currentPlayerIndex || 0
        if (data.players) {
            players.value = data.players
            data.players.forEach((p) => {
                playerStore.updatePlayerResources(p.id, p)
            })
        }
        if (data.areas) areas.value = data.areas
        if (data.tributeTasks) tributeTasks.value = data.tributeTasks
        if (data.downtownCards) downtownCards.value = data.downtownCards
        gameState.value = data
    }

    function handleHeadmanPlaced(data) {
        if (data.gameState) updateGameState(data.gameState)
    }

    function handlePlayerTurn(data) {
        if (data.currentPlayerIndex !== undefined) currentPlayerIndex.value = data.currentPlayerIndex
        if (data.gameState) updateGameState(data.gameState)
    }

    function handleAreaSettled(data) {
        if (data.gameState) updateGameState(data.gameState)
    }

    function handleRoundStarted(data) {
        if (data.round) currentRound.value = data.round
        currentPhase.value = 'placement'
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

    function handleGenericUpdate(data) {
        if (data.gameState) updateGameState(data.gameState)
    }

    function handleBattleStart(data) {
        if (data.battleData) {
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
            const challenger = players.value.find((p) => p.id === battle.challengerId)
            const defender = players.value.find((p) => p.id === battle.defenderId)

            const validChallengerLobsters = challenger?.lobsters?.filter((l) => l && l.id && l.id !== 'normal') || []
            const validDefenderLobsters = defender?.lobsters?.filter((l) => l && l.id && l.id !== 'normal') || []
            if (
                !challenger ||
                (validChallengerLobsters.length === 0 && (!challenger.titleCards || challenger.titleCards.length === 0))
            ) {
                addLog(`${challenger?.name || '挑战者'}没有可参战的龙虾（普通龙虾除外），无法进行战斗`, 'warning')
                continue
            }
            if (
                !defender ||
                (validDefenderLobsters.length === 0 && (!defender.titleCards || defender.titleCards.length === 0))
            ) {
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
        // 忽略自己的选择
        if (String(data.playerId) === String(playerId.value)) return

        // 根据当前战斗的 betting state 识别 fighter 身份
        const betting = currentArenaBattle.value
        if (!betting) return

        if (String(data.playerId) === String(betting.challenger?.id)) {
            challengerReady.value = true
            challengerSelectedLobster.value = data.lobster
        } else if (String(data.playerId) === String(betting.defender?.id)) {
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
        if (!data.playerId || !data.resources) return
        playerStore.updatePlayerResources(data.playerId, data.resources)
    }

    function handleBattleEnded(data) {
        const { winnerId, upgradeFrom, upgradeTo } = data
        if (winnerId !== null && upgradeFrom && upgradeTo) {
            const winner = playerStore.getPlayerById(winnerId)
            if (winner && winner.lobsters) {
                const lobster = winner.lobsters.find((l) => l.grade === upgradeFrom)
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
        if (data.players) players.value = data.players
        if (data.areas) areas.value = data.areas
        if (data.phase) currentPhase.value = data.phase
        if (data.currentRound) currentRound.value = data.currentRound
        if (data.currentPlayerIndex !== undefined) currentPlayerIndex.value = data.currentPlayerIndex
        if (data.status) status.value = data.status
        if (data.tributeTasks) tributeTasks.value = data.tributeTasks
        if (data.downtownCards) downtownCards.value = data.downtownCards
        gameState.value = data
    }

    // ============ 联机操作方法 ============
    function placeHeadman(areaIndex, slotIndex) {
        if (!isMyTurn.value) {
            uni.showToast({ title: '不是你的回合', icon: 'none' })
            return false
        }
        socketService._send('placeHeadman', { areaIndex, slotIndex })
        return true
    }

    function nextPlayer() {
        socketService._send('nextPlayer', {})
    }

    function nextArea() {
        socketService._send('nextArea', {})
    }

    function exchangeSignals(exchangeType) {
        socketService._send('exchangeSignals', { exchangeType })
    }

    function buyItem(itemType) {
        socketService._send('buyItem', { itemType })
    }

    function sellItem(itemType) {
        socketService._send('sellItem', { itemType })
    }

    function cultivateLobster(useSeaweed = false) {
        socketService._send('cultivateLobster', { useSeaweed })
    }

    function submitTribute(taskId) {
        socketService._send('submitTribute', { taskId })
    }

    function executeDowntownAction(cardIndex) {
        socketService._send('executeDowntownAction', { cardIndex })
    }

    function cleanupListeners() {
        socketService.off('connect')
        socketService.off('disconnect')
        socketService.off('connectError')
        socketService.off('roomStateUpdate')
        socketService.off('gameStarted')
        socketService.off('headmanPlaced')
        socketService.off('playerTurn')
        socketService.off('areaSettled')
        socketService.off('roundStarted')
        socketService.off('gameEnded')
        socketService.off('signalsExchanged')
        socketService.off('itemBought')
        socketService.off('itemSold')
        socketService.off('lobsterCultivated')
        socketService.off('tributeSubmitted')
        socketService.off('downtownActionExecuted')
        socketService.off('battleStart')
        socketService.off('lobsterSelected')
        socketService.off('arenaBettingStart')
        socketService.off('arenaBettingComplete')
        socketService.off('betResult')
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
        players.value = []
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

        cleanupListeners()
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
        const challenger = players.value.find((p) => p.id === battle.challengerId)
        const defender = players.value.find((p) => p.id === battle.defenderId)

        currentArenaBattle.value = {
            index,
            challenger,
            defender,
            slotIndex: battle.slotIndex
        }
    }

    const getAvailableLobsters = (playerId) => {
        const player = players.value.find((p) => p.id === playerId)
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
        players,
        currentPlayerIndex,
        currentRound,
        currentPhase,
        status,
        areas,
        tributeTasks,
        downtownCards,
        gameState,

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
        placeHeadman,
        nextPlayer,
        nextArea,
        exchangeSignals,
        buyItem,
        sellItem,
        cultivateLobster,
        submitTribute,
        executeDowntownAction,
        getAreaName,
        isSlotOccupied,
        getSlotOccupant,
        getSlotStatus,
        addLog,

        // 竞技场方法
        setCurrentArenaBattle,
        getAvailableLobsters,
        setArenaPhase
    }
})
