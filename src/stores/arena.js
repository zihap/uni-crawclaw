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

    function getDiceValue(playerIndex) {
        const player = battleData.value?.players[playerIndex]
        if (!player) return Math.floor(Math.random() * 6) + 1

        const skill = getSkill(player.lobsterId)
        if (skill?.getDiceValue) {
            return skill.getDiceValue()
        }

        const diceSides = getDiceSides(playerIndex)
        return Math.floor(Math.random() * diceSides) + 1
    }

    function getDiceSides(playerIndex) {
        const player = battleData.value?.players[playerIndex]
        if (!player) return 6

        const skill = getSkill(player.lobsterId)
        if (skill?.getDiceSides) {
            return skill.getDiceSides()
        }

        return 6
    }

    function modifyDiceValue(playerIndex, value) {
        const player = battleData.value?.players[playerIndex]
        if (!player) return value

        const skill = getSkill(player.lobsterId)
        if (skill?.modifyDice) {
            return skill.modifyDice(value)
        }

        return value
    }

    function createBattleData(p1Data, p2Data, initialCurrentPlayer = 0, challengeSlotIndex = null) {
        return {
            phase: 'initiative',
            currentRound: 1,
            currentPlayer: initialCurrentPlayer,
            totalCells: BATTLE_CELLS,
            challengeSlotIndex,
            players: [
                {
                    id: p1Data.id ?? 1,
                    name: p1Data.name || '玩家1',
                    color: p1Data.color || '#FF6B6B',
                    lobsterName: p1Data.lobsterName,
                    lobsterId: p1Data.lobsterId,
                    lobsterDesc: p1Data.lobsterDesc,
                    position: -1,
                    started: getSkill(p1Data.lobsterId)?.startStarted || false
                },
                {
                    id: p2Data.id ?? 2,
                    name: p2Data.name || '玩家2',
                    color: p2Data.color || '#4ECDC4',
                    lobsterName: p2Data.lobsterName,
                    lobsterId: p2Data.lobsterId,
                    lobsterDesc: p2Data.lobsterDesc,
                    position: BATTLE_CELLS,
                    started: getSkill(p2Data.lobsterId)?.startStarted || false
                }
            ],
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

        const p1Skill = getSkill(p1Data.lobsterId)
        const p2Skill = getSkill(p2Data.lobsterId)

        battleData.value.battleLog = [
            { timestamp: Date.now(), message: '🦞 斗龙虾争锋开始！' },
            {
                timestamp: Date.now(),
                message: `${p1Data.name || '玩家1'} 的 ${p1Data.lobsterName}[${p1Skill.description}] vs ${p2Data.name || '玩家2'} 的 ${p2Data.lobsterName}[${p2Skill.description}]`
            },
            { timestamp: Date.now(), message: '🎲 投掷先手骰子决定行动顺序...' }
        ]

        if (p1Skill?.startStarted) {
            battleData.value.battleLog.push({
                timestamp: Date.now(),
                message: `${p1Data.name} 的龙虾为急先锋，出场即可移动！`
            })
        }
        if (p2Skill?.startStarted) {
            battleData.value.battleLog.push({
                timestamp: Date.now(),
                message: `${p2Data.name} 的龙虾为急先锋，出场即可移动！`
            })
        }

        battleData.value.isInitialized = true
        broadcastBattleUpdate('battleStart')
    }

    function rollInitiativeDice() {
        if (battleData.value.phase !== 'initiative') return
        if (battleData.value.initiative.p1 !== null) return

        const p1DiceSides = getDiceSides(0)
        const p2DiceSides = getDiceSides(1)
        const p1Roll = Math.floor(Math.random() * p1DiceSides) + 1
        const p2Roll = Math.floor(Math.random() * p2DiceSides) + 1

        initiativeDice.value = { p1: p1Roll, p2: p2Roll }

        battleData.value.initiative = { p1: p1Roll, p2: p2Roll, timestamp: Date.now() }
        battleData.value.lastAction = 'initiativeRolled'
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleUpdate')

        return { p1: p1Roll, p2: p2Roll }
    }

    function applyInitiative() {
        if (battleData.value.phase !== 'initiative') return

        const { p1, p2 } = battleData.value.initiative
        if (p1 === null || p2 === null) return

        const p1Data = battleData.value.players[0]
        const p2Data = battleData.value.players[1]
        const p1DiceSides = getDiceSides(0)
        const p2DiceSides = getDiceSides(1)
        const p1DiceDesc = p1DiceSides !== 6 ? `(${p1DiceSides}面骰)` : ''
        const p2DiceDesc = p2DiceSides !== 6 ? `(${p2DiceSides}面骰)` : ''

        addLog(`${p1Data.name} 掷出 ${p1} 点${p1DiceDesc}`)
        addLog(`${p2Data.name} 掷出 ${p2} 点${p2DiceDesc}`)

        if (p1 >= 6 && !getSkill(p1Data.lobsterId)?.startStarted) {
            p1Data.started = true
            addLog(`${p1Data.name} 掷出>=6点，龙虾标记为可移动状态！`)
        }
        if (p2 >= 6 && !getSkill(p2Data.lobsterId)?.startStarted) {
            p2Data.started = true
            addLog(`${p2Data.name} 掷出>=6点，龙虾标记为可移动状态！`)
        }

        let firstPlayer
        if (p1 > p2) {
            firstPlayer = 0
            addLog(`${p1Data.name} 点数更大，获得先手！`)
        } else if (p2 > p1) {
            firstPlayer = 1
            addLog(`${p2Data.name} 点数更大，获得先手！`)
        } else {
            firstPlayer = 1
            addLog(`双方点数一致，${p2Data.name} 获得先手！`)
        }

        battleData.value.currentPlayer = firstPlayer
        battleData.value.phase = 'rolling'
        battleData.value.lastAction = 'initiativeApplied'
        battleData.value.diceValue = null
        battleData.value.rollDiceTimestamp = null
        battleData.value = { ...battleData.value }

        addLog(`轮到 ${battleData.value.players[firstPlayer].name} 掷骰子`)

        const nextSkill = getSkill(battleData.value.players[firstPlayer].lobsterId)
        if (nextSkill?.canReroll) {
            addLog(`[${nextSkill.description}] 可重新投掷一次`)
        }

        broadcastBattleUpdate('battleUpdate')
    }

    function rollDice(diceValue, seaweedBonus = 0) {
        const roller = battleData.value.currentPlayer
        const player = battleData.value.players[roller]
        const skill = getSkill(player.lobsterId)

        // 处理可以重掷的技能
        if (skill?.canReroll) {
            if (pendingDiceValue.value === null) {
                // 第一次掷骰
                pendingDiceValue.value = diceValue
                canReroll.value = true
                hasRerolled.value = false
            } else if (!hasRerolled.value) {
                // 重掷
                hasRerolled.value = true
                canReroll.value = false
            } else {
                pendingDiceValue.value = null
            }
        } else {
            pendingDiceValue.value = null
        }

        // 更新掷骰数据并广播
        battleData.value.diceValue = diceValue
        battleData.value.diceRoller = roller
        battleData.value.rollDiceTimestamp = Date.now()
        battleData.value.seaweedBonus = seaweedBonus
        battleData.value.lastAction = 'diceRolled'
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleUpdate')
    }

    function confirmDice() {
        if (!canReroll.value || pendingDiceValue.value === null) {
            return
        }
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

    function applyDiceResult() {
        if (battleData.value.phase === 'ended') {
            return
        }
        const diceValue = battleData.value.diceValue
        if (diceValue === null || diceValue === undefined) {
            return
        }

        const roller = battleData.value.diceRoller
        const player = battleData.value.players[roller]

        const diceSides = getDiceSides(roller)
        let finalDiceValue = modifyDiceValue(roller, diceValue)

        const skill = getSkill(player.lobsterId)
        const diceSidesDesc = diceSides !== 6 ? `(${diceSides}面骰)` : ''
        let skillDesc =
            finalDiceValue !== diceValue ? ` [${skill.description}触发，${diceValue}→${finalDiceValue}]` : ''

        const seaweedBonus = battleData.value.seaweedBonus || 0
        const seaweedDesc = seaweedBonus > 0 ? `(+${seaweedBonus}海草)` : ''

        let logMessage = ''
        let steps = 0

        if (!player.started) {
            // 未开始状态
            if (finalDiceValue >= 6) {
                player.started = true
                logMessage = `${player.name} 掷出 ${finalDiceValue} 点${seaweedDesc}${diceSidesDesc}${skillDesc}，触发移动条件！龙虾标记为可移动状态`
            } else {
                logMessage = `${player.name} 掷出 ${finalDiceValue} 点${seaweedDesc}${skillDesc}，不足6点，龙虾不可移动`
            }
        } else {
            // 已开始状态，根据点数计算步数
            if (finalDiceValue <= 2) steps = 0
            else if (finalDiceValue <= 5) steps = 1
            else if (finalDiceValue <= 8) steps = 2
            else if (finalDiceValue <= 11) steps = 3
            else steps = 4

            // 应用技能效果
            if (skill?.apply) {
                const context = { bonusSteps: 0 }
                skill.apply(context)
                const bonusSteps = context.bonusSteps || 0
                if (bonusSteps > 0) {
                    skillDesc = ` [${skill.description}触发，额外+${bonusSteps}步]`
                    steps += bonusSteps
                }
            }

            const stepsDesc = steps > 0 ? `，前进 ${steps} 步` : '，原地不动'
            logMessage = `${player.name} 掷出 ${finalDiceValue} 点${seaweedDesc}${diceSidesDesc}${skillDesc}${stepsDesc}`

            if (steps > 0) {
                player.position = roller === 0 ? player.position + steps : player.position - steps

                // 检查是否首次穿过中线
                if (roller === 0) {
                    if (!battleData.value.p1CrossedMidline && player.position >= BATTLE_CELLS / 2) {
                        player.wang = (player.wang || 0) + 1
                        battleData.value.p1CrossedMidline = true
                        addLog(`🎯 ${player.name} 越过中线，获得1望！`)
                    }
                } else {
                    if (!battleData.value.p2CrossedMidline && player.position < BATTLE_CELLS / 2) {
                        player.wang = (player.wang || 0) + 1
                        battleData.value.p2CrossedMidline = true
                        addLog(`🎯 ${player.name} 越过中线，获得1望！`)
                    }
                }
            }
        }

        battleData.value = { ...battleData.value }
        addLog(logMessage)
        battleData.value.seaweedBonus = 0

        if (checkWinCondition(roller)) {
            return
        }

        // 切换到下一个玩家
        const nextPlayer = roller === 0 ? 1 : 0
        const nextPlayerObj = battleData.value.players[nextPlayer]
        const nextSkill = getSkill(nextPlayerObj.lobsterId)

        addLog(`轮到 ${nextPlayerObj.name} 掷骰子`)
        if (nextSkill?.canReroll) {
            addLog(`[${nextSkill.description}] 可重新投掷一次`)
        }

        battleData.value.currentPlayer = nextPlayer
        if (nextPlayer === 0) {
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

    function checkWinCondition(roller) {
        const p1 = battleData.value.players[0]
        const p2 = battleData.value.players[1]
        const rollerPlayer = battleData.value.players[roller]
        const opponentPlayer = roller === 0 ? p2 : p1
        const rollerSkill = getSkill(rollerPlayer.lobsterId)
        const opponentSkill = getSkill(opponentPlayer.lobsterId)

        // 设置胜利者并结束游戏
        const endBattle = (winner, logMessage) => {
            battleData.value.winner = winner
            battleData.value.phase = 'ended'
            addLog(logMessage)
            // 立即广播战斗结束，让所有玩家知道战斗结果
            broadcastBattleUpdate('battleAction')
            return true
        }

        const isCovered = p1.position === p2.position

        if (isCovered) {
            if (opponentSkill?.onCovered) {
                return endBattle(
                    opponentPlayer,
                    `🛡️ ${opponentPlayer.name} 的 [${opponentSkill.description}] 触发！被覆盖反而获胜！`
                )
            }
            return endBattle(rollerPlayer, `🏆 ${rollerPlayer.name} 的 [${rollerPlayer.lobsterName}] 获胜！`)
        }

        const absPositionDiff = Math.abs(p1.position - p2.position)
        const isAdjacent = absPositionDiff === 1
        const rollerWon = roller === 0 ? p1.position > p2.position : p2.position < p1.position
        const rollerPassedOpponent = absPositionDiff === 0 || rollerWon

        if (rollerPassedOpponent) {
            return endBattle(rollerPlayer, `🏆 ${rollerPlayer.name} 的 [${rollerPlayer.lobsterName}] 获胜！`)
        }

        if (isAdjacent) {
            if (rollerSkill?.nearWinOnAdjacent) {
                return endBattle(
                    rollerPlayer,
                    `⚔️ ${rollerPlayer.name} 的 [${rollerPlayer.lobsterName}] 触发 [${rollerSkill.description}] ！紧贴对方龙虾，判定获胜！`
                )
            }
            if (opponentSkill?.nearWinOnAdjacent) {
                return endBattle(
                    opponentPlayer,
                    `⚔️ ${opponentPlayer.name} 的 [${opponentPlayer.lobsterName}] [${opponentSkill.description}] 触发！紧贴对方龙虾，判定获胜！`
                )
            }
        }

        return false
    }

    function applyWinnerAward(choice) {
        const winner = battleData.value?.winner
        if (!winner) return

        if (choice === 'coins') {
            winner.coins = (winner.coins || 0) + 2
            addLog(`💰 ${winner.name} 获得2金币奖励！`)
        } else if (choice === 'gradeUpgrade') {
            const oldGrade = winner.lobsterId
            const newGrade = getNextLobsterGrade(oldGrade)
            winner.lobsterId = newGrade
            winner.lobsterName = getLobsterGradeName(newGrade)
            addLog(`⭐ ${winner.name} 的${winner.lobsterName}升级成功！`)
        }

        battleData.value.winnerAwardChoice = choice
        battleData.value = { ...battleData.value }
        broadcastBattleUpdate('battleEnd')
    }

    function addLog(message) {
        battleData.value.battleLog.push({
            timestamp: Date.now(),
            message
        })
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

        broadcastBattleUpdate('playerQuit')
    }

    function broadcastBattleUpdate(eventType) {
        if (!battleRoomId.value || !battleData.value) return

        socketService.sendBattleAction(
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
        broadcastBattleUpdate('battleAction')
    }

    function updateFromSync(syncedData) {
        if (!syncedData || !battleData.value) {
            return
        }

        // 批量更新简单字段
        const simpleFields = ['phase', 'currentRound', 'currentPlayer', 'diceValue', 'diceRoller', 'lastAction']
        simpleFields.forEach((field) => {
            if (syncedData[field] !== undefined) {
                battleData.value[field] = syncedData[field]
            }
        })

        // rollDiceTimestamp 需要特殊检查是否变化
        if (
            syncedData.rollDiceTimestamp !== undefined &&
            syncedData.rollDiceTimestamp !== battleData.value.rollDiceTimestamp
        ) {
            battleData.value.rollDiceTimestamp = syncedData.rollDiceTimestamp
        }

        // 更新玩家数据
        if (syncedData.players?.length === 2) {
            const playerFields = ['position', 'started', 'skill']
            syncedData.players.forEach((p, i) => {
                if (battleData.value.players[i]) {
                    playerFields.forEach((field) => {
                        if (p[field] !== undefined) {
                            battleData.value.players[i][field] = p[field]
                        }
                    })
                }
            })
        }

        // 更新先手骰子数据
        if (syncedData.initiative) {
            battleData.value.initiative = { ...battleData.value.initiative, ...syncedData.initiative }
        }

        // 更新胜利者
        if (syncedData.winner) {
            battleData.value.winner = battleData.value.players.find((p) => p.id === syncedData.winner.id)
        }

        // 同步战斗日志
        if (syncedData.battleLog?.length > 0) {
            const currentLogLen = battleData.value.battleLog?.length || 0
            if (!battleData.value.isInitialized) {
                battleData.value.battleLog = [...syncedData.battleLog]
            } else if (syncedData.battleLog.length > currentLogLen) {
                battleData.value.battleLog.push(...syncedData.battleLog.slice(currentLogLen))
            }
        }
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
        resetBattle
    }
})
