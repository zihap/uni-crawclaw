/**
 * 捕虾区相关工具函数和常量
 * 实现捕虾指示物处理、捕虾行动和奖励计算
 */

import { LOBSTER_GRADES } from '@stores/game.js'

// 捕虾指示物类型
export const SHRIMP_INDICATOR_TYPES = {
  LOBSTER: 'lobster',           // 龙虾：获取1只野生龙虾
  LOBSTER_OR_SEAWEED: 'lobster_or_seaweed', // 龙虾或海草：玩家选择
  BUBBLE: 'bubble'              // 气泡：兑换金币或龙虾
}

// 捕虾指示物描述
export const SHRIMP_INDICATOR_DESCRIPTIONS = {
  [SHRIMP_INDICATOR_TYPES.LOBSTER]: '获取1只捕虾区的野生龙虾',
  [SHRIMP_INDICATOR_TYPES.LOBSTER_OR_SEAWEED]: '获取1只捕虾区的野生龙虾或1根海草',
  [SHRIMP_INDICATOR_TYPES.BUBBLE]: '1比1兑换金币，或保留后兑换三品龙虾(2个气泡)或二品龙虾(3个气泡)'
}

// 捕虾区行动格配置
export const SHRIMP_CATCHING_SLOTS = [
  {
    id: 0,
    reward: { cages: 1, takeStartingPlayer: true },
    actions: 1,
    description: '奖励1个虾笼，夺取“起始玩家标志”；执行1次捕虾行动'
  },
  {
    id: 1,
    reward: { cages: 1 },
    actions: 2,
    description: '奖励1个虾笼；执行2次捕虾行动'
  },
  {
    id: 2,
    reward: { coins: 1 },
    actions: 3,
    description: '奖励1枚金币；执行3次捕虾行动'
  },
  {
    id: 3,
    reward: {},
    actions: 4,
    description: '执行4次捕虾行动'
  }
]

// 气泡兑换规则
export const BUBBLE_EXCHANGE_RULES = {
  COIN: 1,                // 1气泡 = 1金币
  GRADE3_LOBSTER: 2,      // 2气泡 = 1三品龙虾
  GRADE2_LOBSTER: 3       // 3气泡 = 1二品龙虾
}

const initBagItems = [
  { type: 'bubble', icon: '💨', name: '气泡' },
  { type: 'bubble', icon: '💨', name: '气泡' },
  { type: 'bubble', icon: '💨', name: '气泡' },
  { type: 'bubble', icon: '💨', name: '气泡' },
  { type: 'bubble', icon: '💨', name: '气泡' },
  { type: 'bubble', icon: '💨', name: '气泡' },
  { type: 'bubble', icon: '💨', name: '气泡' },
  { type: 'lobster', icon: '🦞', name: '龙虾' },
  { type: 'lobster', icon: '🦞', name: '龙虾' },
  { type: 'lobster', icon: '🦞', name: '龙虾' },
  { type: 'lobster', icon: '🦞', name: '龙虾' },
  { type: 'lobster', icon: '🦞', name: '龙虾' },
  { type: 'lobster', icon: '🦞', name: '龙虾' },
  { type: 'lobster', icon: '🦞', name: '龙虾' },
  { type: 'seaweed', icon: '🌿', name: '海草' },
  { type: 'seaweed', icon: '🌿', name: '海草' },
  { type: 'seaweed', icon: '🌿', name: '海草' },
  { type: 'seaweed', icon: '🌿', name: '海草' },
  { type: 'seaweed', icon: '🌿', name: '海草' },
  { type: 'seaweed', icon: '🌿', name: '海草' },
  { type: 'seaweed', icon: '🌿', name: '海草' },
  { type: 'either', icon: '❓', name: '龙虾或海草' },
  { type: 'either', icon: '❓', name: '龙虾或海草' },
  { type: 'either', icon: '❓', name: '龙虾或海草' },
  { type: 'either', icon: '❓', name: '龙虾或海草' },
  { type: 'either', icon: '❓', name: '龙虾或海草' },
  { type: 'either', icon: '❓', name: '龙虾或海草' }
];

/**
 * 随机生成捕虾指示物
 * 模拟抽盲袋机制
 * @returns {string} 捕虾指示物类型
 */
export const generateShrimpIndicator = () => {
  const indicators = [
    SHRIMP_INDICATOR_TYPES.LOBSTER,
    SHRIMP_INDICATOR_TYPES.LOBSTER,
    SHRIMP_INDICATOR_TYPES.LOBSTER,
    SHRIMP_INDICATOR_TYPES.LOBSTER_OR_SEAWEED,
    SHRIMP_INDICATOR_TYPES.LOBSTER_OR_SEAWEED,
    SHRIMP_INDICATOR_TYPES.BUBBLE
  ]
  const randomIndex = Math.floor(Math.random() * indicators.length)
  return indicators[randomIndex]
}

/**
 * 处理捕虾指示物
 * @param {Object} player - 玩家对象
 * @param {string} indicatorType - 捕虾指示物类型
 * @param {Array} wildLobsterPool - 野生龙虾池
 * @param {Object} options - 选项
 * @returns {Object} 处理结果
 */
export const processShrimpIndicator = (player, indicatorType, wildLobsterPool, options = {}) => {
  const result = {
    success: true,
    message: '',
    changes: {}
  }

  try {
    switch (indicatorType) {
      case SHRIMP_INDICATOR_TYPES.LOBSTER:
        // 获取1只野生龙虾
        if (wildLobsterPool.length === 0) {
          result.success = false
          result.message = '野生龙虾池已空'
          return result
        }

        const lobster = wildLobsterPool.shift()
        player.lobsters.push(lobster)
        result.message = '获得1只野生龙虾'
        result.changes.lobsters = 1
        break

      case SHRIMP_INDICATOR_TYPES.LOBSTER_OR_SEAWEED:
        // 玩家选择获取龙虾或海草
        // 这里默认选择龙虾，实际游戏中需要玩家选择
        const choice = options.choice || 'lobster'

        if (choice === 'lobster') {
          if (wildLobsterPool.length === 0) {
            result.success = false
            result.message = '野生龙虾池已空'
            return result
          }

          const lobster = wildLobsterPool.shift()
          player.lobsters.push(lobster)
          result.message = '获得1只野生龙虾'
          result.changes.lobsters = 1
        } else {
          player.seaweed += 1
          result.message = '获得1根海草'
          result.changes.seaweed = 1
        }
        break

      case SHRIMP_INDICATOR_TYPES.BUBBLE:
        // 获得1个气泡
        player.bubbles += 1
        result.message = '获得1个气泡'
        result.changes.bubbles = 1
        break

      default:
        result.success = false
        result.message = '未知的捕虾指示物类型'
        return result
    }
  } catch (error) {
    result.success = false
    result.message = `处理捕虾指示物失败: ${error.message}`
  }

  return result
}

/**
 * 执行捕虾行动
 * @param {Object} player - 玩家对象
 * @param {number} actionCount - 行动次数
 * @param {Array} wildLobsterPool - 野生龙虾池
 * @param {Function} onIndicator - 捕虾指示物处理回调
 * @returns {Promise<Object>} 行动结果
 */
export const executeShrimpCatching = async (player, actionCount, wildLobsterPool, onIndicator = null) => {
  const results = []
  let totalChanges = { lobsters: 0, seaweed: 0, bubbles: 0 }

  for (let i = 0; i < actionCount; i++) {
    // 弹出确认弹窗
    const confirmResult = await showConfirmModal()
    if (!confirmResult) {
      // 玩家取消，中断行动
      return {
        success: false,
        results,
        totalChanges,
        message: '玩家取消捕虾行动'
      }
    }

    // 生成捕虾指示物
    const indicatorType = generateShrimpIndicator()

    // 处理指示物
    let result
    if (indicatorType === SHRIMP_INDICATOR_TYPES.LOBSTER_OR_SEAWEED) {
      // 弹出二选一选择界面
      const choice = await showLobsterOrSeaweedChoice()
      if (!choice) {
        // 玩家取消，中断行动
        return {
          success: false,
          results,
          totalChanges,
          message: '玩家取消选择'
        }
      }
      result = processShrimpIndicator(player, indicatorType, wildLobsterPool, { choice })
    } else {
      result = processShrimpIndicator(player, indicatorType, wildLobsterPool)
    }

    results.push(result)

    if (result.success && result.changes) {
      Object.keys(result.changes).forEach(key => {
        totalChanges[key] = (totalChanges[key] || 0) + result.changes[key]
      })
    }

    // 调用回调
    if (onIndicator) {
      onIndicator(indicatorType, result)
    }
  }

  return {
    success: results.every(r => r.success),
    results,
    totalChanges
  }
}

/**
 * 显示确认弹窗
 * @returns {Promise<boolean>} 玩家是否确认
 */
const showConfirmModal = () => {
  return new Promise((resolve) => {
    uni.showModal({
      title: '捕虾行动',
      content: '开始捕虾？',
      confirmText: '冲！',
      success: (res) => {
        resolve(res.confirm)
      },
      fail: () => {
        resolve(false)
      }
    })
  })
}

/**
 * 显示龙虾或海草选择弹窗
 * @returns {Promise<string|null>} 玩家选择的类型或null（取消）
 */
const showLobsterOrSeaweedChoice = () => {
  return new Promise((resolve) => {
    uni.showActionSheet({
      itemList: ['选龙虾', '选海草'],
      success: (res) => {
        if (res.tapIndex === 0) {
          resolve('lobster')
        } else if (res.tapIndex === 1) {
          resolve('seaweed')
        } else {
          resolve(null)
        }
      },
      fail: () => {
        resolve(null)
      }
    })
  })
}

/**
 * 处理气泡兑换
 * @param {Object} player - 玩家对象
 * @param {string} exchangeType - 兑换类型
 * @param {Array} wildLobsterPool - 野生龙虾池
 * @returns {Object} 兑换结果
 */
export const exchangeBubbles = (player, exchangeType, wildLobsterPool) => {
  const result = {
    success: true,
    message: '',
    changes: {}
  }

  try {
    switch (exchangeType) {
      case 'coin':
        if (player.bubbles < BUBBLE_EXCHANGE_RULES.COIN) {
          result.success = false
          result.message = '气泡数量不足'
          return result
        }
        player.bubbles -= BUBBLE_EXCHANGE_RULES.COIN
        player.coins += 1
        result.message = '兑换1枚金币'
        result.changes.coins = 1
        result.changes.bubbles = -1
        break

      case 'grade3_lobster':
        if (player.bubbles < BUBBLE_EXCHANGE_RULES.GRADE3_LOBSTER) {
          result.success = false
          result.message = '气泡数量不足（需要2个气泡）'
          return result
        }
        if (wildLobsterPool.length === 0) {
          result.success = false
          result.message = '野生龙虾池已空'
          return result
        }

        player.bubbles -= BUBBLE_EXCHANGE_RULES.GRADE3_LOBSTER
        const lobster = wildLobsterPool.shift()
        lobster.grade = LOBSTER_GRADES.GRADE3
        player.lobsters.push(lobster)
        result.message = '兑换1只三品龙虾'
        result.changes.lobsters = 1
        result.changes.bubbles = -2
        break

      case 'grade2_lobster':
        if (player.bubbles < BUBBLE_EXCHANGE_RULES.GRADE2_LOBSTER) {
          result.success = false
          result.message = '气泡数量不足（需要3个气泡）'
          return result
        }
        if (wildLobsterPool.length === 0) {
          result.success = false
          result.message = '野生龙虾池已空'
          return result
        }

        player.bubbles -= BUBBLE_EXCHANGE_RULES.GRADE2_LOBSTER
        const lobster2 = wildLobsterPool.shift()
        lobster2.grade = LOBSTER_GRADES.GRADE2
        player.lobsters.push(lobster2)
        result.message = '兑换1只二品龙虾'
        result.changes.lobsters = 1
        result.changes.bubbles = -3
        break

      default:
        result.success = false
        result.message = '未知的兑换类型'
        return result
    }
  } catch (error) {
    result.success = false
    result.message = `气泡兑换失败: ${error.message}`
  }

  return result
}

/**
 * 计算捕虾区行动格奖励
 * @param {Object} player - 玩家对象
 * @param {number} slotIndex - 行动格索引
 * @param {Array} players - 所有玩家
 * @param {number} startingPlayerIndex - 当前起始玩家索引
 * @returns {Object} 奖励结果
 */
export const calculateShrimpCatchingReward = (player, slotIndex, players, startingPlayerIndex) => {
  const result = {
    success: true,
    message: '',
    changes: {}
  }

  try {
    const slotConfig = SHRIMP_CATCHING_SLOTS[slotIndex]
    if (!slotConfig) {
      result.success = false
      result.message = '无效的行动格索引'
      return result
    }

    // 发放奖励
    const reward = slotConfig.reward

    if (reward.cages) {
      player.cages += reward.cages
      result.changes.cages = reward.cages
      result.message += `获得${reward.cages}个虾笼，`
    }

    if (reward.coins) {
      player.coins += reward.coins
      result.changes.coins = reward.coins
      result.message += `获得${reward.coins}枚金币，`
    }

    // 处理起始玩家标志转移
    if (reward.takeStartingPlayer) {
      // 移除原起始玩家的标志
      players[startingPlayerIndex].isStartingPlayer = false
      // 设置新的起始玩家
      player.isStartingPlayer = true
      result.message += '获得起始玩家标志'
      result.changes.startingPlayer = true
    }

    // 移除最后的逗号
    if (result.message.endsWith('，')) {
      result.message = result.message.slice(0, -1)
    }
  } catch (error) {
    result.success = false
    result.message = `计算奖励失败: ${error.message}`
  }

  return result
}
