/**
 * 行动格相关常量定义
 * 用于统一管理行动格的状态、样式和规则
 */

// 玩家颜色配置 - 用于区分不同玩家的行动格占用状态
export const PLAYER_COLORS = {
    0: { bg: '#667eea', border: '#5a6fd6', label: '1P', name: '蓝色' },
    1: { bg: '#4CAF50', border: '#45a049', label: '2P', name: '绿色' },
    2: { bg: '#F44336', border: '#da3a2f', label: '3P', name: '红色' },
    3: { bg: '#FF9800', border: '#e68900', label: '4P', name: '黄色' }
}

// 行动格默认样式
export const DEFAULT_SLOT_STYLE = {
    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    color: '#fff',
    opacity: 1,
    occupied: false
}

// 行动格占用状态样式
export const getOccupiedSlotStyle = (playerId) => {
    const playerColor = PLAYER_COLORS[playerId] || PLAYER_COLORS[0]
    return {
        background: playerColor.bg,
        borderColor: playerColor.border,
        color: '#fff',
        opacity: 0.85,
        occupied: true,
        playerLabel: playerColor.label,
        playerId
    }
}

// 区域配置 - 定义每个区域的行动格数量
export const AREA_CONFIG = {
    shrimp_catching: { name: '捕虾区', slots: 4 },
    seafood_market: { name: '海鲜市场', slots: 4 },
    breeding: { name: '养蛊区', slots: 4 },
    tribute: { name: '上供区', slots: 6 },
    marketplace: { name: '闹市区', slots: 3 }
}

// 行动格状态枚举
export const SLOT_STATUS = {
    EMPTY: 'empty',
    OCCUPIED: 'occupied',
    DISABLED: 'disabled'
}

// 放置错误类型
export const PLACEMENT_ERRORS = {
    NOT_PLACEMENT_PHASE: '当前不是工放阶段',
    SLOT_OCCUPIED: '该行动格已被占用',
    NO_LIZHANG: '没有剩余的里长可以放置',
    SLOT_DISABLED: '该行动格当前不可用',
    GAME_NOT_INITIALIZED: '游戏尚未初始化'
}
