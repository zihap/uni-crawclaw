/**
 * 养蛊区相关工具函数和常量
 * 实现养蛊区行动格配置及基础奖励计算
 */

// 养蛊区行动格配置
export const BREEDING_SLOTS = [
    {
        id: 0,
        reward: { seaweed: 1 },
        actions: 1,
        description: '奖励1根海草；执行1次培养行动'
    },
    {
        id: 1,
        reward: {},
        actions: 2,
        description: '执行2次培养行动'
    },
    {
        id: 2,
        reward: { coins: 1 },
        actions: 2,
        description: '奖励1枚金币；执行2次培养行动'
    },
    {
        id: 3,
        reward: {},
        actions: 3,
        description: '执行3次培养行动'
    }
]

/**
 * 计算养蛊区行动格奖励
 * @param {Object} player - 玩家对象
 * @param {number} slotIndex - 行动格索引
 * @returns {Object} 奖励结果
 */
export const calculateBreedingReward = (player, slotIndex) => {
    const result = {
        success: true,
        message: '',
        changes: {}
    }

    try {
        const slotConfig = BREEDING_SLOTS[slotIndex]
        if (!slotConfig) {
            result.success = false
            result.message = '无效的行动格索引'
            return result
        }

        // 发放奖励
        const reward = slotConfig.reward

        if (reward.seaweed) {
            player.seaweed += reward.seaweed
            result.changes.seaweed = reward.seaweed
            result.message += `获得${reward.seaweed}根海草，`
        }

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
