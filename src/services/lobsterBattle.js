import { logger } from '@utils/logger'

export const LOBSTER_BATTLE_STATUS = {
    IDLE: 'idle',
    CHALLENGING: 'challenging',
    COMPLETED: 'completed'
}

class LobsterBattleService {
    constructor() {
        this.battleStatus = LOBSTER_BATTLE_STATUS.IDLE
        this.currentBattle = null
    }

    initBattle(challenger, defender, challengerLobster, defenderLobster) {
        logger.info('初始化龙虾斗场', { challenger, defender, challengerLobster, defenderLobster })

        this.battleStatus = LOBSTER_BATTLE_STATUS.CHALLENGING
        this.currentBattle = {
            challenger,
            defender,
            challengerLobster,
            defenderLobster,
            challengerRolls: [],
            defenderRolls: [],
            winner: null,
            timestamp: Date.now()
        }

        return this.currentBattle
    }

    rollDice(count = 1) {
        if (!this.currentBattle || this.battleStatus !== LOBSTER_BATTLE_STATUS.CHALLENGING) {
            logger.warn('没有进行中的战斗')
            return null
        }

        const rolls = Array.from({ length: count }, () => Math.floor(Math.random() * 6) + 1)
        logger.info('投掷骰子', { rolls })

        return rolls
    }

    executeBattle() {
        if (!this.currentBattle) {
            logger.warn('没有进行中的战斗')
            return null
        }

        logger.info('执行龙虾战斗')

        const challengerRoll = this.rollDice(1)[0]
        const defenderRoll = this.rollDice(1)[0]

        this.currentBattle.challengerRolls = [challengerRoll]
        this.currentBattle.defenderRolls = [defenderRoll]

        let winner
        if (challengerRoll > defenderRoll) {
            winner = 'challenger'
        } else if (defenderRoll > challengerRoll) {
            winner = 'defender'
        } else {
            winner = Math.random() > 0.5 ? 'challenger' : 'defender'
        }

        this.currentBattle.winner = winner
        this.battleStatus = LOBSTER_BATTLE_STATUS.COMPLETED

        logger.info('战斗结束', { winner, challengerRoll, defenderRoll })

        return this.currentBattle
    }

    swapPositions(challengerIndex, defenderIndex, placements) {
        logger.info('交换位置', { challengerIndex, defenderIndex })

        const newPlacements = [...placements]
        const challengerPlacement = newPlacements.find((p) => p.playerId === challengerIndex)
        const defenderPlacement = newPlacements.find((p) => p.playerId === defenderIndex)

        if (challengerPlacement && defenderPlacement) {
            const tempArea = challengerPlacement.area
            const tempSlot = challengerPlacement.slotIndex
            challengerPlacement.area = defenderPlacement.area
            challengerPlacement.slotIndex = defenderPlacement.slotIndex
            defenderPlacement.area = tempArea
            defenderPlacement.slotIndex = tempSlot
        }

        return newPlacements
    }

    reset() {
        this.battleStatus = LOBSTER_BATTLE_STATUS.IDLE
        this.currentBattle = null
        logger.info('重置龙虾斗场')
    }

    getBattleResult() {
        if (this.battleStatus !== LOBSTER_BATTLE_STATUS.COMPLETED) {
            return null
        }
        return this.currentBattle
    }
}

export const lobsterBattleService = new LobsterBattleService()
