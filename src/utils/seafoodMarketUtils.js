/**
 * 海鲜市场相关工具函数和常量
 * 实现动态物价、行动格配置及里长雇佣逻辑
 */

// 海鲜市场行动格配置 (工放阶段放置坑位)
export const SEAFOOD_MARKET_SLOTS = [
    {id: 0, reward: {coins: 1}, actions: 2, description: '奖励1枚金币；该区域结算阶段可执行2次交易行动'},
    {id: 1, reward: {}, actions: 3, description: '该区域结算阶段可执行3次交易行动'},
    {id: 2, reward: {coins: 1}, actions: 3, description: '奖励1枚金币；该区域结算阶段可执行3次交易行动'},
    {id: 3, reward: {coins: 2}, actions: 3, description: '奖励2枚金币；该区域结算阶段可执行3次交易行动'}
]

// 8个里长雇佣名额配置
export const HIRE_LIZHANG_SLOTS = [
    {id: 0, cost: 6, reward: {seaweed: 1}, availableFrom: 2},
    {id: 1, cost: 6, reward: {seaweed: 1}, availableFrom: 2},
    {id: 2, cost: 6, reward: {lobster: 'normal'}, availableFrom: 3},
    {id: 3, cost: 6, reward: {lobster: 'normal'}, availableFrom: 3},
    {id: 4, cost: 6, reward: {lobster: 'grade3'}, availableFrom: 3},
    {id: 5, cost: 6, reward: {lobster: 'grade3'}, availableFrom: 4},
    {id: 6, cost: 6, reward: {lobster: 'grade2'}, availableFrom: 4},
    {id: 7, cost: 6, reward: {lobster: 'grade2'}, availableFrom: 4}
]

/**
 * 动态计算当前市场物价
 * @param {number} lobsterCount - 市场流通的龙虾数 (0-8)
 * @returns {Object} 物价表
 */
export const getMarketPrices = (lobsterCount) => {
    // 龙虾数 <= 3
    if (lobsterCount <= 3) {
        return {lobster: 3, cage: 2, seaweed1: 1, seaweed3: 4}
    }
    // 龙虾数 > 3 且 <= 5
    else if (lobsterCount <= 5) {
        return {lobster: 2, cage: 3, seaweed1: 1, seaweed3: 4}
    }
    // 龙虾数 > 5 且 <= 8
    else {
        return {lobster: 1, cage: 4, seaweed1: 1, seaweed3: 4}
    }
}

/**
 * 计算行动格基础奖励
 */
export const calculateSeafoodMarketReward = (player, slotIndex) => {
    const result = {success: true, message: '', changes: {}}
    try {
        const slotConfig = SEAFOOD_MARKET_SLOTS[slotIndex]
        if (!slotConfig) {
            result.success = false;
            result.message = '无效的行动格'
            return result
        }
        const reward = slotConfig.reward
        if (reward.coins) {
            player.coins += reward.coins
            result.changes.coins = reward.coins
            result.message += `获得${reward.coins}枚金币，`
        }
        if (result.message.endsWith('，')) result.message = result.message.slice(0, -1)
    } catch (error) {
        result.success = false;
        result.message = `计算失败: ${error.message}`
    }
    return result
}
