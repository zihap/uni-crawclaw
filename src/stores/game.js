import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { titleCards, tributeCards, marketplaceCards } from '@data/cards'
import { shuffleArray, createLobster } from '@utils/gameUtils'
import {
    DEFAULT_SLOT_STYLE,
    getOccupiedSlotStyle,
    AREA_CONFIG,
    SLOT_STATUS,
    PLACEMENT_ERRORS
} from '@utils/slotConstants'
import {
    SHRIMP_CATCHING_SLOTS,
    executeShrimpCatching,
    calculateShrimpCatchingReward,
    exchangeBubbles
} from '@utils/shrimpCatchingUtils'
import { BREEDING_SLOTS, calculateBreedingReward } from '@utils/breedingUtils'
import {MARKETPLACE_SLOTS, calculateMarketplaceReward} from '@utils/marketplaceUtils'
import { usePlayerStore } from '@stores/player'

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

export const AREAS = {
    SHRIMP_CATCHING: 'shrimp_catching',
    SEAFOOD_MARKET: 'seafood_market',
    BREEDING: 'breeding',
    TRIBUTE: 'tribute',
    MARKETPLACE: 'marketplace'
}

/**
 * 游戏状态管理Store
 * 实现放置机制的核心逻辑，包括行动格独占、视觉区分、异常处理等
 */
export const useGameStore = defineStore('game', () => {
    // ============ 基础状态 ============
    const maxRounds = 5
    const phases = Object.values(GAME_PHASES)
    const currentRound = ref(1)
    const currentPhase = ref(GAME_PHASES.PREPARATION)

    // 玩家store
    const playerStore = usePlayerStore()

    // ============ 游戏资源状态 ============
    const wildLobsterPool = ref([])
    const seafoodMarketLobsters = ref(0)
    const titleCardDeck = ref([]) // 全局称号卡牌堆，防止重复抽取
    const gameTitleCards = ref([])
    const gameTributeCards = ref([])
    const gameMarketplaceCards = ref([])
    const taverns = ref([])
    const royalLobsterCount = ref(0)
    const logs = ref([])

    // 挂起状态：用于通知前端UI弹出对应面板并等待操作完成
    const pendingBreeding = ref(null)
    const pendingMarketplace = ref(null) // 新增：闹市区交互挂起状态

    // ============ 放置机制核心状态 ============
    /*
     * 行动格占用状态
     * 结构: { 'area_slotIndex': { playerId, timestamp, round } }
     * 示例: { 'shrimp_catching_0': { playerId: 0, timestamp: 123456, round: 1 } }
     */
    const slotOccupancy = ref({})

    /*
     * 已放置的里长记录
     * 用于追踪每个里长的放置信息
     */
    // const placedLiZhang = ref([])

    /*
     * 当前放置顺序的玩家列表
     * 从起始玩家开始，按顺时针顺序
     */
    const placementOrder = ref([])

    /*
     * 当前轮到放置的玩家索引
     */
    const currentPlacementIndex = ref(0)

    // ============ 计算属性 ============
    const currentPlayer = computed(() => playerStore.currentPlayer)
    const startingPlayer = computed(() => playerStore.startingPlayer)
    const players = computed(() => playerStore.players)
    const currentPlayerIndex = computed(() => playerStore.currentPlayerIndex)
    const startingPlayerIndex = computed(() => playerStore.startingPlayerIndex)

    /**
     * 获取指定行动格的占用状态
     */
    const getSlotStatus = (area, slotIndex) => {
        const key = `${area}_${slotIndex}`
        const occupancy = slotOccupancy.value[key]

        // 检查占用是否在当前回合内有效
        if (occupancy && occupancy.round === currentRound.value) {
            return {
                status: SLOT_STATUS.OCCUPIED,
                playerId: occupancy.playerId,
                ...occupancy
            }
        }

        return { status: SLOT_STATUS.EMPTY, playerId: null }
    }

    /**
     * 检查行动格是否被占用
     */
    const isSlotOccupied = (area, slotIndex) => {
        return getSlotStatus(area, slotIndex).status === SLOT_STATUS.OCCUPIED
    }

    /**
     * 获取行动格的视觉样式
     */
    const getSlotStyle = (area, slotIndex) => {
        const status = getSlotStatus(area, slotIndex)

        if (status.status === SLOT_STATUS.OCCUPIED) {
            return getOccupiedSlotStyle(status.playerId)
        }

        return DEFAULT_SLOT_STYLE
    }

    /**
     * 检查是否所有玩家都已放完里长
     */
    const isPlacementComplete = computed(() => {
        return currentPlacementIndex.value >= placementOrder.value.length
    })

    /**
     * 获取当前轮到放置的玩家
     */
    const currentPlacementPlayer = computed(() => {
        if (isPlacementComplete.value) return null
        const playerId = placementOrder.value[currentPlacementIndex.value]
        return players.value[playerId]
    })

    // ============ 日志工具 ============
    const addLog = (message, type = 'info') => {
        logs.value.push({
            timestamp: Date.now(),
            message,
            type,
            round: currentRound.value,
            phase: currentPhase.value
        })
    }

    // ============ 游戏初始化 ============
    const initGame = (playerCount) => {
        // 重置基础状态
        currentRound.value = 1
        currentPhase.value = GAME_PHASES.PREPARATION
        currentPlayerIndex.value = 0
        startingPlayerIndex.value = 0

        // 重置资源状态
        wildLobsterPool.value = []
        seafoodMarketLobsters.value = 0
        titleCardDeck.value = []
        gameTitleCards.value = []
        gameTributeCards.value = []
        gameMarketplaceCards.value = []
        taverns.value = Array.from({ length: 6 }, () => ({ cards: [], completions: 0 }))
        royalLobsterCount.value = 0
        logs.value = []
        pendingBreeding.value = null
        pendingMarketplace.value = null

        // 重置放置机制状态
        slotOccupancy.value = {}
        // placedLiZhang.value = []
        placementOrder.value = []
        currentPlacementIndex.value = 0

        // 初始化玩家
        playerStore.initPlayers(playerCount)

        // 初始化卡牌
        gameTributeCards.value = shuffleArray([...tributeCards])
        titleCardDeck.value = shuffleArray([...titleCards])

        addLog(`游戏初始化完成，${playerCount}名玩家`, 'success')
    }

    /**
     * 初始化放置顺序
     * 核心逻辑：为每个里长创建放置机会，按顺时针顺序循环
     * * 实现原理：
     * 1. 计算所有玩家中的最大里长数量
     * 2. 外层循环：按里长数量从 0 到 maxLiZhangCt - 1
     * 3. 内层循环：按顺时针顺序遍历所有玩家
     * 4. 检查玩家是否还有剩余里长（liZhang > 当前循环次数）
     * 5. 如果有，将玩家添加到放置顺序中
     * * 示例：
     * - 玩家1: 3里长, 玩家2: 2里长
     * - 最大里长数量: 3
     * - 循环1 (i=0): 玩家1, 玩家2 → [1, 2]
     * - 循环2 (i=1): 玩家1, 玩家2 → [1, 2, 1, 2]
     * - 循环3 (i=2): 玩家1 → [1, 2, 1, 2, 1]
     * - 最终顺序: 1 → 2 → 1 → 2 → 1
     * * 特点：
     * - 里长多的玩家获得更多的放置机会
     * - 放置顺序保持顺时针方向
     * - 确保每个里长都有放置机会
     */
    const initPlacementOrder = () => {
        const playerCount = playerStore.players.length
        const maxLiZhangCt = Math.max(...playerStore.players.map((p) => p.liZhang))
        const order = []

        for (let i = 0; i < maxLiZhangCt; i++) {
            for (let j = 0; j < playerCount; j++) {
                if (playerStore.players[j].liZhang <= i) continue
                const playerId = (playerStore.startingPlayerIndex + j) % playerCount
                order.push(playerId)
            }
        }

        placementOrder.value = order
        currentPlacementIndex.value = 0

        addLog(`放置顺序: ${order.map((id) => `玩家${id + 1}`).join(' → ')}`, 'info')
    }

    // ============ 放置机制核心方法 ============

    /**
     * 放置里长到行动格
     * 实现行动格独占机制的核心逻辑
     * * @param {string} area - 区域标识
     * @param {number} slotIndex - 行动格索引
     * @returns {object} { success: boolean, message: string, error?: string }
     */
    const placeLiZhang = (area, slotIndex) => {
        // 1. 检查游戏是否已初始化
        if (!currentPlayer.value) {
            const error = PLACEMENT_ERRORS.GAME_NOT_INITIALIZED
            addLog(error, 'error')
            return { success: false, message: error, error }
        }

        // 2. 检查当前是否为工放阶段
        if (currentPhase.value !== GAME_PHASES.PLACEMENT) {
            const error = PLACEMENT_ERRORS.NOT_PLACEMENT_PHASE
            addLog(error, 'warning')
            return { success: false, message: error, error }
        }

        // 3. 检查行动格是否已被占用（独占机制核心）
        if (isSlotOccupied(area, slotIndex)) {
            const occupant = getSlotStatus(area, slotIndex)
            const occupantPlayer = playerStore.getPlayerById(occupant.playerId)
            const occupantName = occupantPlayer?.name || '未知玩家'
            const error = `${PLACEMENT_ERRORS.SLOT_OCCUPIED}（已被${occupantName}占用）`
            addLog(error, 'warning')
            return { success: false, message: error, error: PLACEMENT_ERRORS.SLOT_OCCUPIED }
        }

        // 4. 获取当前要放置的玩家
        const player = currentPlacementPlayer.value
        if (!player) {
            const error = '当前没有可放置的玩家'
            addLog(error, 'warning')
            return { success: false, message: error, error }
        }

        // 5. 检查玩家是否有剩余的里长
        if (player.liZhang <= 0) {
            const error = `${player.name}${PLACEMENT_ERRORS.NO_LIZHANG}`
            addLog(error, 'warning')

            // 自动跳过该玩家
            skipPlayerPlacement()
            return { success: false, message: error, error: PLACEMENT_ERRORS.NO_LIZHANG }
        }

        // 6. 执行放置操作
        try {
            // 扣除玩家里长
            player.liZhang--

            // 记录行动格占用状态
            const slotKey = `${area}_${slotIndex}`
            slotOccupancy.value[slotKey] = {
                playerId: player.id,
                area,
                slotIndex,
                timestamp: Date.now(),
                round: currentRound.value
            }

            // 记录放置历史
            // placedLiZhang.value.push({
            //     playerId: player.id,
            //     area,
            //     slotIndex,
            //     round: currentRound.value,
            //     timestamp: Date.now()
            // })

            // 记录日志
            const areaName = AREA_CONFIG[area]?.name || area
            addLog(`${player.name}在${areaName}的${slotIndex + 1}号行动格放置了里长`, 'success')

            // 移动到下一个玩家
            nextPlayer()

            return {
                success: true,
                message: '放置成功',
                player: player.name,
                area: areaName,
                slotIndex
            }
        } catch (err) {
            const error = `放置失败: ${err.message}`
            addLog(error, 'error')
            return { success: false, message: error, error: err.message }
        }
    }

    /**
     * 跳过当前玩家的放置回合
     * 用于玩家没有里长可放的情况
     */
    const skipPlayerPlacement = () => {
        const player = currentPlacementPlayer.value
        if (player) {
            addLog(`${player.name}没有里长可放，跳过放置回合`, 'info')
        }

        currentPlacementIndex.value++

        // 检查是否所有玩家都已放置完毕
        if (isPlacementComplete.value) {
            addLog('所有玩家放置完毕，工放阶段结束', 'success')
        }
    }

    /**
     * 移动到下一个玩家
     */
    const nextPlayer = () => {
        currentPlacementIndex.value++

        // 检查是否所有玩家都已放置完毕
        if (isPlacementComplete.value) {
            addLog('所有玩家放置完毕，工放阶段结束', 'success')
        } else {
            const nextPlayerName = currentPlacementPlayer.value?.name
            if (nextPlayerName) {
                addLog(`轮到${nextPlayerName}放置里长`, 'info')
            }
        }
    }

    /**
     * 检查玩家是否可以放置里长
     * 用于UI按钮的禁用状态判断
     */
    const canPlayerPlace = (playerId) => {
        if (currentPhase.value !== GAME_PHASES.PLACEMENT) return false
        if (isPlacementComplete.value) return false

        const currentId = placementOrder.value[currentPlacementIndex.value]
        if (currentId !== playerId) return false

        const player = players.value[playerId]
        if (!player || player.liZhang <= 0) return false

        return true
    }

    // ============ 阶段管理 ============

    /**
     * 执行捕虾区结算
     * 按照行动格序号依次执行捕虾行动
     */
    const executeShrimpCatchingSettlement = async () => {
        addLog('执行捕虾区结算', 'info')
        for (const slot of SHRIMP_CATCHING_SLOTS) {
            const slotIndex = slot.id
            const playerId = getSlotStatus('shrimp_catching', slotIndex).playerId
            if (null === playerId) continue
            const player = playerStore.getPlayerById(playerId)
            if (!player) {
                addLog(`玩家${playerId}不存在，跳过捕虾行动`, 'warning')
                continue
            }

            // 计算行动格奖励
            const rewardResult = calculateShrimpCatchingReward(
                player,
                slotIndex,
                playerStore.players,
                playerStore.startingPlayerIndex
            )
            if (rewardResult.success && rewardResult.message) {
                addLog(`${player.name}${rewardResult.message}`, 'info')
            }

            // 执行捕虾行动
            const slotConfig = SHRIMP_CATCHING_SLOTS[slotIndex]
            if (slotConfig) {
                const actionCount = slotConfig.actions
                const result = await executeShrimpCatching(
                    player,
                    actionCount,
                    wildLobsterPool.value,
                    (indicatorType, indicatorResult) => {
                        if (indicatorResult.success) {
                            addLog(`${player.name}${indicatorResult.message}`, 'info')
                        }
                    }
                )

                if (result.success) {
                    addLog(`${player.name}执行了${actionCount}次捕虾行动`, 'success')
                }
            }
        }
        addLog('捕虾区结算完成', 'success')
    }

    /**
     * 执行养蛊区结算
     */
    const executeBreedingSettlement = async () => {
        addLog('执行养蛊区结算', 'info')
        for (const slot of BREEDING_SLOTS) {
            const slotIndex = slot.id
            const playerId = getSlotStatus('breeding', slotIndex).playerId
            if (playerId === null) continue

            const player = playerStore.getPlayerById(playerId)
            if (!player) continue

            const rewardResult = calculateBreedingReward(player, slotIndex)

            if (rewardResult.success && rewardResult.message) {
                addLog(`${player.name}${rewardResult.message}`, 'info')
            }

            const actionCount = slot.actions
            if (player.lobsters.length === 0) {
                addLog(`${player.name}没有龙虾可以培养，跳过行动`, 'warning')
                continue
            }

            addLog(`${player.name}开始执行${actionCount}次培养行动`, 'info')

            // 挂起引擎，等待 UI 的玩家交互返回 Promise
            await new Promise((resolve) => {
                pendingBreeding.value = {
                    player,
                    actionCount,
                    resolve: () => {
                        pendingBreeding.value = null
                        resolve()
                    }
                }
            })
        }
        addLog('养蛊区结算完成', 'success')
    }

    /**
     * 执行闹市区结算 (新增功能)
     */
    const executeMarketplaceSettlement = async () => {
        addLog('执行闹市区结算', 'info')
        for (const slot of MARKETPLACE_SLOTS) {
            const slotIndex = slot.id
            // 校验行动格是否在当前回合可用
            if (currentRound.value < slot.availableFrom) continue

            const playerId = getSlotStatus('marketplace', slotIndex).playerId
            if (playerId === null) continue

            const player = playerStore.getPlayerById(playerId)
            if (!player) continue

            // 发放基础奖励
            const rewardResult = calculateMarketplaceReward(player, slotIndex)
            if (rewardResult.success && rewardResult.message) {
                addLog(`${player.name}${rewardResult.message}`, 'info')
            }

            // 校验是否还有未使用的闹市卡
            const availableCards = gameMarketplaceCards.value.filter(c => !c.usedThisRound)
            if (availableCards.length === 0) {
                addLog(`${player.name}准备执行闹市行动，但本回合所有闹市卡均已被使用`, 'warning')
                continue
            }

            addLog(`${player.name}开始执行闹市行动`, 'info')

            // 挂起引擎，等待 UI 玩家交互返回 Promise
            await new Promise((resolve) => {
                pendingMarketplace.value = {
                    player,
                    resolve: async (result) => {
                        pendingMarketplace.value = null
                        if (result && result.card) {
                            // 执行对应卡牌逻辑
                            await processMarketplaceAction(player, result.card, result.optionIndex)
                        } else {
                            addLog(`${player.name}放弃了闹市行动`, 'info')
                        }
                        resolve()
                    }
                }
            })
        }
        addLog('闹市区结算完成', 'success')
    }

    /**
     * 处理卡牌对应逻辑
     */
    const processMarketplaceAction = async (player, card, optionIndex) => {
        card.usedThisRound = true; // 标记本回合已使用
        let logMsg = `${player.name}执行了【${card.name}】闹市卡：`;

        if (card.type === 'county') {
            const opt = card.options[optionIndex];
            player.coins -= opt.cost.coins;
            player.de += opt.reward.de;
            logMsg += `消耗${opt.cost.coins}金币，获得${opt.reward.de}德`;
        } else if (card.type === 'prefecture') {
            const opt = card.options[optionIndex];
            const removeCount = opt.cost.lobsters;
            // 优先消耗最低品级的龙虾
            player.lobsters.sort((a, b) => Object.values(LOBSTER_GRADES).indexOf(a.grade) - Object.values(LOBSTER_GRADES).indexOf(b.grade));
            player.lobsters.splice(0, removeCount);
            player.wang += opt.reward.wang;
            logMsg += `消耗${removeCount}只龙虾，获得${opt.reward.wang}望`;
        } else if (card.type === 'academy') {
            if (player.de < player.wang) {
                player.de++;
                logMsg += `德轨最低，提升1德`;
            } else {
                player.wang++;
                logMsg += `望轨提升1望`;
            }
        } else if (card.type === 'charity') {
            logMsg += `触发善堂群体效果！`;
            addLog(logMsg, 'warning');

            const minDe = Math.min(...players.value.map(p => p.de));
            const minWang = Math.min(...players.value.map(p => p.wang));

            players.value.forEach(p => {
                if (p.de === minDe) {
                    const lostLobsters = Math.min(2, p.lobsters.length);
                    p.lobsters.sort((a, b) => Object.values(LOBSTER_GRADES).indexOf(a.grade) - Object.values(LOBSTER_GRADES).indexOf(b.grade));
                    p.lobsters.splice(0, lostLobsters);
                    if (lostLobsters > 0) addLog(`${p.name}因德轨最低，损失了${lostLobsters}只龙虾`, 'error');
                }
                if (p.wang === minWang) {
                    const lostCoins = Math.min(2, p.coins);
                    p.coins -= lostCoins;
                    if (lostCoins > 0) addLog(`${p.name}因望轨最低，损失了${lostCoins}金币`, 'error');
                }
            });
            return; // 提前结束，防止重复输出 log
        } else if (card.type === 'breeding') {
            logMsg += `获得3次培养机会`;
            addLog(logMsg, 'success');
            // 直接触发养蛊区弹窗逻辑挂起引擎
            if (player.lobsters.length === 0) {
                addLog(`${player.name}没有龙虾可以培养，浪费了善学卡的效果`, 'warning')
                return;
            }
            await new Promise((resolve) => {
                pendingBreeding.value = {
                    player,
                    actionCount: 3,
                    resolve: () => {
                        pendingBreeding.value = null;
                        resolve();
                    }
                }
            });
            return;
        } else if (card.type === 'freebie') {
            const newLobster = createLobster();
            newLobster.grade = LOBSTER_GRADES.NORMAL; // 规定直接获取的是普通龙虾
            player.lobsters.push(newLobster);
            logMsg += `直接获取1只普通龙虾`;
        }

        addLog(logMsg, 'success');
    }


    const executePreparationPhase = () => {
        addLog('执行准备阶段', 'info')

        wildLobsterPool.value = Array.from({ length: 8 }, () => createLobster())
        addLog('捕虾区：添加8只野生龙虾', 'info')

        // 弃置场上剩余称号卡，直接从牌堆抽取2张全新的
        gameTitleCards.value = titleCardDeck.value.splice(0, 2)
        addLog('养蛊区：刷新2张待获取的称号卡', 'info')

        taverns.value.forEach((tavern) => {
            if (tavern.cards.length < 2 && gameTributeCards.value.length > 0) {
                tavern.cards.push(gameTributeCards.value.shift())
            }
        })
        addLog('上供区：补充酒楼的上供卡', 'info')

        if (currentRound.value === 1) {
            // 第一回合初始化抽出并绑定使用状态
            gameMarketplaceCards.value = shuffleArray([...marketplaceCards]).slice(0, 3).map(c => ({
                ...c,
                usedThisRound: false
            }))
            addLog('闹市区：抽取3张本局游戏固定的闹市卡', 'info')
        } else {
            // 每回合重置闹市卡使用状态
            gameMarketplaceCards.value.forEach(c => c.usedThisRound = false)
            addLog('闹市区：已重置闹市卡使用状态', 'info')
        }

        // 重置放置顺序
        initPlacementOrder()
    }

    /**
     * 执行结算阶段
     * 按顺序结算各个区域
     */
    const executeSettlementPhase = async () => {
        addLog('执行结算阶段', 'info')

        // 按顺序结算各个区域
        // 1. 捕虾区结算
        await executeShrimpCatchingSettlement()

        // 3. 养蛊区结算
        await executeBreedingSettlement()

        // 5. 闹市区结算
        await executeMarketplaceSettlement()

        // 后续可以添加其他区域的结算逻辑
        // 2. 海鲜市场结算
        // 4. 上供区结算

        addLog('结算阶段完成', 'success')
    }

    const executeCleanupPhase = () => {
        addLog('执行清理阶段', 'info')

        seafoodMarketLobsters.value += wildLobsterPool.value.length
        addLog(`海鲜市场：添加${wildLobsterPool.value.length}只龙虾`, 'info')
        wildLobsterPool.value = []

        // 重置玩家里长数量
        playerStore.resetPlayerLiZhang()

        // 给所有玩家添加金币
        playerStore.addCoinsToAllPlayers()

        // 清理放置状态
        // placedLiZhang.value = []
        royalLobsterCount.value = 0
        playerStore.setCurrentPlayer(playerStore.startingPlayerIndex)

        // 注意：slotOccupancy 在清理阶段不清除，而是在下一回合的准备阶段自动失效
        // 因为占用状态是基于 round 字段判断的
    }

    const phaseHandlers = {
        [GAME_PHASES.PREPARATION]: executePreparationPhase,
        [GAME_PHASES.SETTLEMENT]: executeSettlementPhase,
        [GAME_PHASES.CLEANUP]: executeCleanupPhase
    }

    const nextPhase = async () => {
        // 执行当前阶段的预处理
        if (phaseHandlers[currentPhase.value]) {
            const result = phaseHandlers[currentPhase.value]()
            if (result instanceof Promise) {
                await result
            }
        }

        // 计算下一个阶段
        const currentIndex = phases.indexOf(currentPhase.value)
        const nextIndex = (currentIndex + 1) % phases.length
        currentPhase.value = phases[nextIndex]

        // 如果回到第一个阶段，增加回合数
        if (nextIndex === 0) {
            currentRound.value++
        }

        addLog(`进入${getPhaseText()}阶段`, 'info')
    }

    const getPhaseText = () => {
        const phaseMap = {
            [GAME_PHASES.PREPARATION]: '准备',
            [GAME_PHASES.PLACEMENT]: '工放',
            [GAME_PHASES.SETTLEMENT]: '结算',
            [GAME_PHASES.CLEANUP]: '清理'
        }
        return phaseMap[currentPhase.value] || '未知'
    }

    // ============ 计分系统 ============
    const calculateTotalScore = (player) => {
        return playerStore.calculateTotalScore(player)
    }

    const getSortedPlayers = () => {
        return playerStore.getSortedPlayers()
    }

    // ============ 导出 ============
    return {
        // 基础状态
        currentRound,
        maxRounds,
        currentPhase,
        players,
        currentPlayerIndex,
        startingPlayerIndex,
        currentPlayer,
        startingPlayer,

        // 资源状态
        wildLobsterPool,
        seafoodMarketLobsters,
        titleCardDeck,
        gameTitleCards,
        gameTributeCards,
        gameMarketplaceCards,
        taverns,
        royalLobsterCount,
        logs,
        pendingBreeding,
        pendingMarketplace, // 导出挂起状态

        // 放置机制状态
        slotOccupancy,
        // placedLiZhang,
        placementOrder,
        currentPlacementIndex,
        isPlacementComplete,
        currentPlacementPlayer,

        // 方法
        initGame,
        placeLiZhang,
        nextPlayer,
        nextPhase,
        addLog,
        calculateTotalScore,
        getSortedPlayers,
        getPhaseText,

        // 放置机制工具方法
        getSlotStatus,
        isSlotOccupied,
        getSlotStyle,
        canPlayerPlace,
        skipPlayerPlacement,
        initPlacementOrder
    }
})
