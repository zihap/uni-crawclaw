/**
 * 上供区相关工具函数和常量
 * 实现上供区行动格与挑战位置配置
 */

// 上供区行动格配置 (0~2为常规，3~5为挑战)
export const TRIBUTE_SLOTS = [
    {id: 0, type: 'normal', actions: 1, availableFrom: 1, description: '该区域结算阶段可执行1次上供行动'},
    {id: 1, type: 'normal', actions: 1, availableFrom: 1, description: '该区域结算阶段可执行1次上供行动'},
    {id: 2, type: 'normal', actions: 1, availableFrom: 4, description: '第4回合可用，该区域结算阶段可执行1次上供行动'},

    // 挑战位
    {
        id: 3,
        type: 'challenge',
        targetSlot: 0,
        actions: 1,
        availableFrom: 1,
        description: '结算开始时向1号位发起斗龙虾挑战，获胜互换位置；可执行1次上供'
    },
    {
        id: 4,
        type: 'challenge',
        targetSlot: 1,
        actions: 1,
        availableFrom: 1,
        description: '结算开始时向2号位发起斗龙虾挑战，获胜互换位置；可执行1次上供'
    },
    {
        id: 5,
        type: 'challenge',
        targetSlot: 2,
        actions: 1,
        availableFrom: 4,
        description: '第4回合可用，结算开始时向3号位发起挑战，获胜互换；可执行1次上供'
    }
];

// 酒楼名称库
export const TAVERN_NAMES = ['醉仙楼', '太白楼', '望江阁', '迎客客栈', '聚贤庄', '天海酒家'];