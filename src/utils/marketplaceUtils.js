/**
 * 闹市区相关工具函数和常量
 * 实现闹市区行动格配置及基础奖励计算
 */

// 闹市区行动格配置
export const MARKETPLACE_SLOTS = [
    {
        id: 0,
        reward: {},
        actions: 1,
        availableFrom: 2, // 第2回合开始才能使用
        description: '该区域结算阶段可执行1次闹市行动'
    },
    {
        id: 1,
        reward: { coins: 1 },
        actions: 1,
        availableFrom: 3, // 第3回合开始才能使用
        description: '奖励1枚金币；该区域结算阶段可执行1次闹市行动'
    },
    {
        id: 2,
        reward: { coins: 2 },
        actions: 1,
        availableFrom: 4, // 第4回合开始才能使用
        description: '奖励2枚金币；该区域结算阶段可执行1次闹市行动'
    }
]

/**
 * 计算闹市区行动格奖励
 * @param {Object} player - 玩家对象
 * @param {number} slotIndex - 行动格索引
 * @returns {Object} 奖励结果
 */
export const calculateMarketplaceReward = (player, slotIndex) => {
    const result = {
        success: true,
        message: '',
        changes: {}
    }

    try {
        const slotConfig = MARKETPLACE_SLOTS[slotIndex]
        if (!slotConfig) {
            result.success = false
            result.message = '无效的行动格索引'
            return result
        }

        // 发放奖励 (金币)
        const reward = slotConfig.reward

        if (reward.coins) {
            player.coins += reward.coins
            result.changes.coins = reward.coins
            result.message += `获得${reward.coins}枚金币，`
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
