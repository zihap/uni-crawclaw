import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import socketModule from '@/utils/socket'
import { getSkill } from '@/data/cards'
import { getNextLobsterGrade, getLobsterGradeName } from '@/utils/gameUtils'
const socketService = socketModule.socketService || socketModule

const BATTLE_CELLS = 8

export const useBattleStore = defineStore('battle', () => {
    const battleData = ref(null)
    const myPlayerIndex = ref(null)
    const battleRoomId = ref(null)
    const pendingDiceValue = ref(null)
    const canReroll = ref(false)
    const hasRerolled = ref(false)
    const initiativeDice = ref({ p1: null, p2: null })

    const isMyTurn = computed(() => {
        if (myPlayerIndex.value < 0) return false
        return battleData.value?.currentPlayer === myPlayerIndex.value && battleData.value?.phase === 'rolling'
    })

    // ============ 技能方法统一 ============

    const applySkillMethod = (playerIndex, methodName, fallback, ...args) => {
        const player = battleData.value?.players[playerIndex]
        if (!player) return fallback
        let skill = getSkill(player.lobsterGrade)
        if (player.lobsterSkill) {
            skill = player.lobsterSkill
        }
        return skill?.[methodName] ? skill[methodName](fallback, ...args) : fallback
    }

    function getDiceValue(playerIndex) {
        const player = battleData.value?.players[playerIndex]
        if (!player) return Math.floor(Math.random() * 6) + 1
        let skill = getSkill(player.lobsterGrade)
        if (player.lobsterSkill) {
            skill = player.lobsterSkill
        }
        if (skill?.getDiceValue) return skill.getDiceValue()
        return Math.floor(Math.random() * getDiceSides(playerIndex)) + 1
    }

    function getDiceSides(playerIndex) {
        return applySkillMethod(playerIndex, 'getDiceSides', 6)
    }

    function modifyDiceValue(playerIndex, value) {
        return applySkillMethod(playerIndex, 'modifyDice', value)
    }

    // ============ 战斗数据构建 ============

    const createPlayerData = (data, startPosition, defaultColor) => ({
        id: data.id ?? 1,
        name: data.name || '玩家1',
        color: data.color || defaultColor,
        lobsterName: data.lobsterName,
        lobsterId: data.lobsterId,
        lobsterGrade: data.lobsterGrade,
        lobsterDesc: data.lobsterDesc,
        lobsterSkill: data.lobsterSkill,
        position: startPosition,
        started: data.lobsterSkill?.startStarted || false
    })

    const buildInitialBattleLog = (p1Data, p2Data) => {
        const formatLobsterInfo = (data) =>
            `${data.name || '玩家1'} 的 ${data.lobsterName}${data?.lobsterSkill?.description ? '[' + data.lobsterSkill.description + ']' : ''}`

        const logs = [
            { timestamp: Date.now(), message: '🦞 斗龙虾争锋开始！' },
            {
                timestamp: Date.now(),
                message: `${formatLobsterInfo(p1Data)} vs ${formatLobsterInfo(p2Data)}`
            },
            { timestamp: Date.now(), message: '🎲 投掷先手骰子决定行动顺序...' }
        ]

        if (p1Data.lobsterSkill?.startStarted) {
            logs.push({ timestamp: Date.now(), message: `${p1Data.name} 的龙虾为急先锋，出场即可移动！` })
        }
        if (p2Data.lobsterSkill?.startStarted) {
            logs.push({ timestamp: Date.now(), message: `${p2Data.name} 的龙虾为急先锋，出场即可移动！` })
        }
        return logs
    }

    function createBattleData(p1Data, p2Data, initialCurrentPlayer = 0, challengeSlotIndex = null) {
        return {
            phase: 'initiative',
            currentRound: 1,
            currentPlayer: initialCurrentPlayer,
            totalCells: BATTLE_CELLS,
            challengeSlotIndex,
            players: [createPlayerData(p1Data, -1, '#FF6B6B'), createPlayerData(p2Data, BATTLE_CELLS, '#4ECDC4')],
            diceValue: null,
            diceRoller: null,
            rollDiceTimestamp: null,
            seaweedBonus: 0,
            initiative: { p1: null, p2: null, timestamp: null },
            battleLog: [],
            winner: null,
            lastAction: null,
            isInitialized: false,
            p1CrossedMidline: false,
            p2CrossedMidline: false,
            winnerAwardChoice: null
        }
    }

    function initBattle(p1Data, p2Data, params) {
        battleData.value = createBattleData(
            p1Data,
            p2Data,
            params?.initialCurrentPlayer ?? 0,
            params?.challengeSlotIndex ?? null
        )
        myPlayerIndex.value = params?.myPlayerIndex ?? -1
        battleRoomId.value = params?.roomId
        pendingDiceValue.value = null
        canReroll.value = false
        hasRerolled.value = false
        initiativeDice.value = { p1: null, p2: null }

        battleData.value.battleLog = buildInitialBattleLog(p1Data, p2Data)
        battleData.value.isInitialized = true
    }

    // ============ 先手骰子 ============

    function rollInitiativeDice() {
        if (battleData.value.phase !== 'initiative' || battleData.value.initiative.p1 !== null) return

        const p1Roll = Math.floor(Math.random() * getDiceSides(0)) + 1
        const p2Roll = Math.floor(Math.random() * getDiceSides(1)) + 1

        initiativeDice.value = { p1: p1Roll, p2: p2Roll }
        battleData.value.initiative = { p1: p1Roll, p2: p2Roll, timestamp: Date.now() }
        battleData.value.lastAction = 'initiativeRolled'
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleUpdate')

        return { p1: p1Roll, p2: p2Roll }
    }

    const determineFirstPlayer = (p1, p2, p1Name, p2Name) => {
        if (p1 > p2) return { first: 0, log: `${p1Name} 点数更大，获得先手！` }
        if (p2 > p1) return { first: 1, log: `${p2Name} 点数更大，获得先手！` }
        return { first: 1, log: `双方点数一致，${p2Name} 获得先手！` }
    }

    function applyInitiative() {
        if (battleData.value.phase !== 'initiative') return
        const { p1, p2 } = battleData.value.initiative
        if (p1 === null || p2 === null) return

        const p1Data = battleData.value.players[0]
        const p2Data = battleData.value.players[1]

        const p1DiceDesc = getDiceSides(0) !== 6 ? `(${getDiceSides(0)}面骰)` : ''
        const p2DiceDesc = getDiceSides(1) !== 6 ? `(${getDiceSides(1)}面骰)` : ''

        addLog(`${p1Data.name} 掷出 ${p1} 点${p1DiceDesc}`)
        addLog(`${p2Data.name} 掷出 ${p2} 点${p2DiceDesc}`)

        if (p1 >= 6 && !p1Data.lobsterSkill?.startStarted) {
            p1Data.started = true
            addLog(`${p1Data.name} 掷出>=6点，龙虾标记为可移动状态！`)
        }
        if (p2 >= 6 && !p2Data.lobsterSkill?.startStarted) {
            p2Data.started = true
            addLog(`${p2Data.name} 掷出>=6点，龙虾标记为可移动状态！`)
        }

        const { first: firstPlayer, log } = determineFirstPlayer(p1, p2, p1Data.name, p2Data.name)
        addLog(log)

        battleData.value.currentPlayer = firstPlayer
        battleData.value.initiative.firstPlayer = firstPlayer
        battleData.value.phase = 'rolling'
        battleData.value.lastAction = 'initiativeApplied'
        battleData.value.diceValue = null
        battleData.value.rollDiceTimestamp = null
        battleData.value = { ...battleData.value }

        addLog(`轮到 ${battleData.value.players[firstPlayer].name} 掷骰子`)

        const nextSkill = battleData.value.players[firstPlayer].lobsterSkill
        if (nextSkill?.canReroll && nextSkill?.description) {
            addLog(`[${nextSkill.description}] 可重新投掷一次`)
        }

        broadcastBattleUpdate('battleUpdate')
    }

    // ============ 掷骰子 ============

    function rollDice(diceValue, seaweedBonus = 0) {
        const roller = battleData.value.currentPlayer
        const player = battleData.value.players[roller]
        const skill = player.lobsterSkill

        if (skill?.canReroll) {
            if (pendingDiceValue.value === null) {
                pendingDiceValue.value = diceValue
                canReroll.value = true
                hasRerolled.value = false
            } else if (!hasRerolled.value) {
                hasRerolled.value = true
                canReroll.value = false
            } else {
                pendingDiceValue.value = null
            }
        } else {
            pendingDiceValue.value = null
        }

        battleData.value.diceValue = diceValue
        battleData.value.diceRoller = roller
        battleData.value.rollDiceTimestamp = Date.now()
        battleData.value.seaweedBonus = seaweedBonus
        battleData.value.lastAction = 'diceRolled'
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleUpdate')
    }

    function confirmDice() {
        if (!canReroll.value || pendingDiceValue.value === null) return
        const roller = battleData.value.currentPlayer
        const diceValue = pendingDiceValue.value
        pendingDiceValue.value = null
        canReroll.value = false
        hasRerolled.value = false

        battleData.value.diceValue = diceValue
        battleData.value.diceRoller = roller
        battleData.value.lastAction = 'diceConfirmed'
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleUpdate')
    }

    // ============ 应用骰子结果 ============

    const calculateSteps = (diceValue) => {
        if (diceValue <= 2) return 0
        if (diceValue <= 5) return 1
        if (diceValue <= 8) return 2
        if (diceValue <= 11) return 3
        return 4
    }

    const applySkillBonus = (skill) => {
        if (!skill?.apply) return { bonusSteps: 0, skillDesc: '' }
        const context = { bonusSteps: 0 }
        skill.apply(context)
        const bonusSteps = context.bonusSteps || 0
        const skillDesc =
            bonusSteps > 0 && skill?.description ? ` [${skill.description}触发，额外+${bonusSteps}步]` : ''
        return { bonusSteps, skillDesc }
    }

    const applyMovement = (player, roller, steps) => {
        if (steps > 0) {
            player.position = roller === 0 ? player.position + steps : player.position - steps
        }
    }

    const checkMidlineCrossing = (roller, player) => {
        const crossedField = roller === 0 ? 'p1CrossedMidline' : 'p2CrossedMidline'
        const midline = BATTLE_CELLS / 2
        const crossed = roller === 0 ? player.position >= midline : player.position < midline

        if (!battleData.value[crossedField] && crossed) {
            battleData.value[crossedField] = true
            addLog(`🎯 ${player.name} 越过中线，获得1望！`)
        }
    }

    function applyDiceResult() {
        if (battleData.value.phase === 'ended') return
        const diceValue = battleData.value.diceValue
        const roller = battleData.value.diceRoller
        if (diceValue == null) return

        const player = battleData.value.players[roller]
        const diceSides = getDiceSides(roller)
        const skill = player.lobsterSkill
        let finalDiceValue = modifyDiceValue(roller, diceValue)

        const diceSidesDesc = diceSides !== 6 ? `(${diceSides}面骰)` : ''
        let skillDesc =
            finalDiceValue !== diceValue && skill?.description
                ? ` [${skill.description}触发，${diceValue}→${finalDiceValue}]`
                : ''

        const seaweedBonus = battleData.value.seaweedBonus || 0
        const seaweedDesc = seaweedBonus > 0 ? `(+${seaweedBonus}海草)` : ''

        let logMessage = ''
        let steps = 0

        if (!player.started) {
            if (finalDiceValue >= 6) {
                player.started = true
                logMessage = `${player.name} 掷出 ${finalDiceValue} 点${seaweedDesc}${diceSidesDesc}${skillDesc}，触发移动条件！龙虾标记为可移动状态`
            } else {
                logMessage = `${player.name} 掷出 ${finalDiceValue} 点${seaweedDesc}${skillDesc}，不足6点，龙虾不可移动`
            }
        } else {
            steps = calculateSteps(finalDiceValue)
            const { bonusSteps, skillDesc: bonusDesc } = applySkillBonus(skill)
            if (bonusDesc) skillDesc = bonusDesc
            steps += bonusSteps

            const stepsDesc = steps > 0 ? `，前进 ${steps} 步` : '，原地不动'
            logMessage = `${player.name} 掷出 ${finalDiceValue} 点${seaweedDesc}${diceSidesDesc}${skillDesc}${stepsDesc}`
            applyMovement(player, roller, steps)
        }

        battleData.value = { ...battleData.value }
        addLog(logMessage)
        checkMidlineCrossing(roller, player)
        battleData.value.seaweedBonus = 0

        if (checkWinCondition(roller)) return

        const nextPlayer = roller === 0 ? 1 : 0
        addLog(`轮到 ${battleData.value.players[nextPlayer].name} 掷骰子`)

        battleData.value.currentPlayer = nextPlayer
        if (nextPlayer === battleData.value.initiative?.firstPlayer) {
            battleData.value.currentRound++
            addLog(`--- 第 ${battleData.value.currentRound} 回合 ---`)
        }

        battleData.value.lastAction = 'turnChange'
        battleData.value.diceValue = null
        battleData.value.rollDiceTimestamp = null
        pendingDiceValue.value = null
        canReroll.value = false
        hasRerolled.value = false
        broadcastBattleUpdate('battleUpdate')
    }

    // ============ 胜负判定 ============

    const endBattle = (winner, logMessage) => {
        battleData.value.winner = winner
        battleData.value.phase = 'ended'
        addLog(logMessage)
        broadcastBattleUpdate('battleUpdate')
        return true
    }

    function checkWinCondition(roller) {
        const p1 = battleData.value.players[0]
        const p2 = battleData.value.players[1]
        const rollerPlayer = battleData.value.players[roller]
        const opponentPlayer = roller === 0 ? p2 : p1
        const rollerSkill = rollerPlayer.lobsterSkill
        const opponentSkill = opponentPlayer.lobsterSkill

        const isCovered = p1.position === p2.position
        if (isCovered) {
            if (opponentSkill?.onCovered) {
                const desc = opponentSkill?.description ? ` 的 [${opponentSkill.description}]` : ''
                return endBattle(opponentPlayer, `🛡️ ${opponentPlayer.name}${desc} 触发！被覆盖反而获胜！`)
            }
            return endBattle(rollerPlayer, `🏆 ${rollerPlayer.name} 的 [${rollerPlayer.lobsterName}] 获胜！`)
        }

        const absPositionDiff = Math.abs(p1.position - p2.position)
        const rollerWon = roller === 0 ? p1.position > p2.position : p2.position < p1.position
        if (absPositionDiff === 0 || rollerWon) {
            return endBattle(rollerPlayer, `🏆 ${rollerPlayer.name} 的 [${rollerPlayer.lobsterName}] 获胜！`)
        }

        if (absPositionDiff === 1) {
            if (rollerSkill?.nearWinOnAdjacent) {
                const desc = rollerSkill?.description ? ` [${rollerSkill.description}]` : ''
                return endBattle(
                    rollerPlayer,
                    `⚔️ ${rollerPlayer.name} 的 [${rollerPlayer.lobsterName}] 触发${desc}！紧贴对方龙虾，判定获胜！`
                )
            }
            if (opponentSkill?.nearWinOnAdjacent) {
                const desc = opponentSkill?.description ? ` [${opponentSkill.description}]` : ''
                return endBattle(
                    opponentPlayer,
                    `⚔️ ${opponentPlayer.name} 的 [${opponentPlayer.lobsterName}]${desc} 触发！紧贴对方龙虾，判定获胜！`
                )
            }
        }

        return false
    }

    // ============ 奖励 & 杂项 ============

    function applyWinnerAward(choice) {
        const winner = battleData.value?.winner
        if (!winner) return

        if (choice === 'coins') {
            winner.coins = (winner.coins || 0) + 2
            addLog(`💰 ${winner.name} 获得2金币奖励！`)
        } else if (choice === 'gradeUpgrade') {
            const newGrade = getNextLobsterGrade(winner.lobsterId)
            winner.lobsterGrade = newGrade
            winner.lobsterName = getLobsterGradeName(newGrade)
            addLog(`⭐ ${winner.name} 的${winner.lobsterName}升级成功！`)
        }

        battleData.value.winnerAwardChoice = choice
        battleData.value.lastAction = 'rewardSelected'
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleEnd')
    }

    function addLog(message) {
        battleData.value.battleLog.push({ timestamp: Date.now(), message })
    }

    function quitBattle() {
        if (!battleRoomId.value || myPlayerIndex.value < 0) return

        if (battleData.value.phase !== 'ended') {
            const winnerIndex = myPlayerIndex.value === 0 ? 1 : 0
            battleData.value.winner = battleData.value.players[winnerIndex]
            battleData.value.phase = 'ended'
            addLog(`${battleData.value.players[myPlayerIndex.value].name} 退出战斗`)
            addLog(`🏆 ${battleData.value.winner.name} 获得胜利！`)
        }

        broadcastBattleUpdate('battleEnd')
    }

    function broadcastBattleUpdate(eventType) {
        if (!battleRoomId.value || !battleData.value) return
        socketService.clientBattleAction(
            eventType,
            {
                ...battleData.value,
                myPlayerIndex: myPlayerIndex.value
            },
            myPlayerIndex.value
        )
    }

    function broadcastRewardSelected() {
        battleData.value.lastAction = 'rewardSelected'
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleEnd')
    }

    // ============ 数据同步 ============

    const syncBattleFields = (syncedData) => {
        const fields = [
            'phase',
            'currentRound',
            'currentPlayer',
            'diceValue',
            'diceRoller',
            'lastAction',
            'winnerAwardChoice',
            'p1CrossedMidline',
            'p2CrossedMidline'
        ]
        fields.forEach((field) => {
            if (syncedData[field] !== undefined) {
                battleData.value[field] = syncedData[field]
            }
        })
        if (
            syncedData.rollDiceTimestamp !== undefined &&
            syncedData.rollDiceTimestamp !== battleData.value.rollDiceTimestamp
        ) {
            battleData.value.rollDiceTimestamp = syncedData.rollDiceTimestamp
        }
    }

    const syncPlayerFields = (syncedData) => {
        if (syncedData.players?.length !== 2) return
        const fields = ['position', 'started', 'skill']
        syncedData.players.forEach((p, i) => {
            if (battleData.value.players[i]) {
                fields.forEach((field) => {
                    if (p[field] !== undefined) battleData.value.players[i][field] = p[field]
                })
            }
        })
    }

    const syncBattleLog = (syncedData) => {
        if (!syncedData.battleLog?.length) return
        const currentLen = battleData.value.battleLog?.length || 0
        if (!battleData.value.isInitialized) {
            battleData.value.battleLog = [...syncedData.battleLog]
        } else if (syncedData.battleLog.length > currentLen) {
            battleData.value.battleLog.push(...syncedData.battleLog.slice(currentLen))
        }
    }

    function updateFromSync(syncedData) {
        if (!syncedData || !battleData.value) return
        syncBattleFields(syncedData)
        syncPlayerFields(syncedData)
        if (syncedData.initiative) {
            battleData.value.initiative = { ...battleData.value.initiative, ...syncedData.initiative }
        }
        if (syncedData.winner) {
            battleData.value.winner = battleData.value.players.find((p) => p.id === syncedData.winner.id)
        }
        syncBattleLog(syncedData)
    }

    function resetBattle() {
        battleData.value = null
        myPlayerIndex.value = null
        battleRoomId.value = null
        pendingDiceValue.value = null
        canReroll.value = false
        hasRerolled.value = false
        initiativeDice.value = { p1: null, p2: null }
    }

    // ============ battleAction 事件处理 ============
    let _onRewardSelected = null

    function handleBattleAction(data) {
        if (!data.battleData) return

        // 跳过自己发送的消息回显
        if (data.senderId !== myPlayerIndex.value) {
            updateFromSync(data.battleData)
        }

        // 监听奖励选择完成，通过回调通知外部
        if (data.battleData.lastAction === 'rewardSelected') {
            if (_onRewardSelected) {
                _onRewardSelected()
            }
        }

        // 同步 winnerAwardChoice（失败玩家需要收到胜利玩家的选择）
        if (data.battleData.winnerAwardChoice && battleData.value) {
            battleData.value.winnerAwardChoice = data.battleData.winnerAwardChoice
        }
    }

    function setupBattleActionListener(onRewardSelected) {
        _onRewardSelected = onRewardSelected || null
        socketService.onAction('serverBattleAction', 'battleUpdate', handleBattleAction)
        socketService.onAction('serverBattleAction', 'battleEnded', handleBattleAction)
    }

    function cleanupBattleActionListener() {
        socketService.offAction('serverBattleAction', 'battleUpdate')
        socketService.offAction('serverBattleAction', 'battleEnded')
        _onRewardSelected = null
    }

    return {
        battleData,
        myPlayerIndex,
        battleRoomId,
        pendingDiceValue,
        canReroll,
        isMyTurn,
        getDiceValue,
        getDiceSides,
        modifyDiceValue,
        initBattle,
        rollInitiativeDice,
        applyInitiative,
        rollDice,
        confirmDice,
        applyDiceResult,
        applyWinnerAward,
        broadcastRewardSelected,
        quitBattle,
        addLog,
        updateFromSync,
        resetBattle,
        setupBattleActionListener,
        cleanupBattleActionListener
    }
})
