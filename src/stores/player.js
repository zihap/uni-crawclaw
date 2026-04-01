import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { PLAYER_COLORS } from '@utils/slotConstants'
import { createLobster } from '@utils/gameUtils'

/**
 * 玩家状态管理Store
 * 负责管理玩家的基本信息、资源数据和状态更新
 */
export const usePlayerStore = defineStore('player', () => {
    // 玩家列表
    const players = ref([])
    const currentPlayerIndex = ref(0)
    const startingPlayerIndex = ref(0)

    // 计算属性
    const currentPlayer = computed(() => players.value[currentPlayerIndex.value])
    const startingPlayer = computed(() => players.value[startingPlayerIndex.value])

    /**
     * 初始化玩家列表
     * @param {number} playerCount - 玩家数量
     * @returns {Array} 初始化后的玩家列表
     */
    const initPlayers = (playerCount) => {
        // 初始资源配置
        const initialResources = [
            { lobsters: 2, coins: 5, seaweed: 1, cages: 1 },
            { lobsters: 2, coins: 6, seaweed: 1, cages: 1 },
            { lobsters: 2, coins: 5, seaweed: 2, cages: 1 },
            { lobsters: 2, coins: 6, seaweed: 2, cages: 1 }
        ]

        players.value = Array.from({ length: playerCount }, (_, i) => ({
            id: i,
            name: `玩家${i + 1}`,
            isStartingPlayer: i === 0,
            liZhang: 3,
            maxLiZhang: 5,
            coins: initialResources[i].coins,
            seaweed: initialResources[i].seaweed,
            cages: initialResources[i].cages,
            lobsters: Array.from({ length: initialResources[i].lobsters }, () => createLobster()),
            de: 0,
            wang: 0,
            bubbles: 0,
            tributeCards: [],
            titleCards: [],
            bonusGold: 0,
            tavernCompletions: {},
            // 玩家颜色配置
            color: PLAYER_COLORS[i]
        }))

        currentPlayerIndex.value = 0
        startingPlayerIndex.value = 0

        return players.value
    }

    /**
     * 获取指定玩家
     * @param {number} playerId - 玩家ID
     * @returns {Object|null} 玩家对象或null
     */
    const getPlayerById = (playerId) => {
        const numericId = Number(playerId)
        return players.value.find((player) => Number(player.id) === numericId) || null
    }

    /**
     * 更新玩家资源
     * @param {number} playerId - 玩家ID
     * @param {Object} resources - 资源对象，包含要更新的资源及其数量
     * @returns {boolean} 更新是否成功
     */
    const updatePlayerResources = (playerId, resources) => {
        const player = getPlayerById(playerId)
        if (!player) return false

        Object.entries(resources).forEach(([key, value]) => {
            if (key in player) {
                player[key] = value
            }
        })

        return true
    }

    /**
     * 设置当前玩家
     * @param {number} playerIndex - 玩家索引
     */
    const setCurrentPlayer = (playerIndex) => {
        if (playerIndex >= 0 && playerIndex < players.value.length) {
            currentPlayerIndex.value = playerIndex
        }
    }

    /**
     * 设置起始玩家
     * @param {number} playerIndex - 玩家索引
     */
    const setStartingPlayer = (playerIndex) => {
        if (playerIndex >= 0 && playerIndex < players.value.length) {
            // 移除原起始玩家的标志
            if (startingPlayer.value) {
                startingPlayer.value.isStartingPlayer = false
            }

            // 设置新的起始玩家
            startingPlayerIndex.value = playerIndex
            const newStartingPlayer = players.value[playerIndex]
            if (newStartingPlayer) {
                newStartingPlayer.isStartingPlayer = true
            }
        }
    }

    /**
     * 计算玩家总分
     * @param {Object} player - 玩家对象
     * @returns {number} 玩家总分
     */
    const calculateTotalScore = (player) => {
        let score = player.de * player.wang
        score += player.coins
        player.tributeCards.forEach((card) => {
            if (card.bonusScore) {
                score += card.bonusScore
            }
        })
        Object.values(player.tavernCompletions).forEach((completion) => {
            if (completion === 1) score += 3
            if (completion === 2) score += 2
            if (completion === 3) score += 1
        })
        return score
    }

    /**
     * 获取排序后的玩家列表（按总分降序）
     * @returns {Array} 排序后的玩家列表
     */
    const getSortedPlayers = () => {
        return [...players.value].sort((a, b) => {
            const scoreA = calculateTotalScore(a)
            const scoreB = calculateTotalScore(b)
            if (scoreB !== scoreA) return scoreB - scoreA
            return b.coins - a.coins
        })
    }

    /**
     * 重置玩家里长数量
     * @param {number} baseLiZhang - 基础里长数量
     */
    const resetPlayerLiZhang = (baseLiZhang = 3) => {
        players.value.forEach((player) => {
            player.liZhang = baseLiZhang + player.tributeCards.filter((c) => c.aura?.type === 'extraLiZhang').length
        })
    }

    /**
     * 给所有玩家添加金币
     * @param {number} baseCoins - 基础金币数量
     */
    const addCoinsToAllPlayers = (baseCoins = 1) => {
        players.value.forEach((player) => {
            player.coins += baseCoins + player.bonusGold
        })
    }

    /**
     * 导出
     */
    return {
        // 状态
        players,
        currentPlayerIndex,
        startingPlayerIndex,
        currentPlayer,
        startingPlayer,

        // 方法
        initPlayers,
        getPlayerById,
        updatePlayerResources,
        setCurrentPlayer,
        setStartingPlayer,
        calculateTotalScore,
        getSortedPlayers,
        resetPlayerLiZhang,
        addCoinsToAllPlayers
    }
})
