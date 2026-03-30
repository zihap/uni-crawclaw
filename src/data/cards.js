export const titleCards = [
    {
        id: 'title_1',
        name: '红头紫',
        skill: null,
        description: '留空，随龙虾斗场一起稍后完善'
    },
    {
        id: 'title_2',
        name: '铁甲将军',
        skill: null,
        description: '留空，随龙虾斗场一起稍后完善'
    },
    {
        id: 'title_3',
        name: '黄金鳌',
        skill: null,
        description: '留空，随龙虾斗场一起稍后完善'
    },
    {
        id: 'title_4',
        name: '闪电钳',
        skill: null,
        description: '留空，随龙虾斗场一起稍后完善'
    },
    {
        id: 'doubleRoll',
        name: '勇者龙虾',
        description: '非常骁勇善战',
        skill: {
            description: '可抛两次骰子，选择较优结果',
            canReroll: true,
            getDiceSides: () => 12
        }
    },
    {
        id: 'readyToMove',
        name: '急先锋龙虾',
        description: '',
        skill: {
            description: '出场即可移动，使用10面骰',
            startStarted: true,
            getDiceSides: () => 10
        }
    },
    {
        id: 'counterStrike',
        name: '铁壁龙虾',
        description: '',
        skill: {
            description: '被覆盖时反败为胜',
            onCovered: true,
            getDiceSides: () => 12
        }
    },
    {
        id: 'longStrike',
        name: '长鳌虾',
        description: '',
        skill: {
            description: '紧贴对方一格即可获胜',
            nearWinOnAdjacent: true,
            getDiceSides: () => 12
        }
    },
    {
        id: 'steady',
        name: '稳健龙虾',
        description: '天生沉稳，谋定而后动',
        skill: {
            description: '每次移动额外+1步',
            apply: (context) => {
                context.bonusSteps = (context.bonusSteps || 0) + 1
            },
            getDiceSides: () => 12
        }
    },
    {
        id: 'lucky',
        name: '幸运龙虾',
        description: '',
        skill: {
            description: '掷出1、2、3点视为6点',
            modifyDice: (value) => (value <= 3 ? 6 : value),
            getDiceSides: () => 12
        }
    }
]

export const tributeCards = [
    {
        id: 'tribute_1',
        name: '王爷',
        requirements: {
            lobsters: 1,
            minGrade: 'grade1',
            seaweed: 2
        },
        reward: {
            type: 'de',
            value: 3
        },
        aura: {
            type: 'doubleWinReward',
            description: '龙虾斗场获胜奖励翻倍'
        },
        bonusScore: 0
    },
    {
        id: 'tribute_2',
        name: '知府',
        requirements: {
            lobsters: 2,
            coins: 5
        },
        reward: {
            type: 'wang',
            value: 2
        },
        aura: {
            type: 'bonusGold',
            value: 1,
            description: '每回合额外获得1金币'
        },
        bonusScore: 2
    },
    {
        id: 'tribute_3',
        name: '县令',
        requirements: {
            lobsters: 1,
            seaweed: 3
        },
        reward: {
            type: 'de',
            value: 2
        },
        aura: null,
        bonusScore: 3
    },
    {
        id: 'tribute_4',
        name: '乡绅',
        requirements: {
            coins: 10
        },
        reward: {
            type: 'wang',
            value: 3
        },
        aura: null,
        bonusScore: 1
    },
    {
        id: 'tribute_5',
        name: '举人',
        requirements: {
            lobsters: 3
        },
        reward: {
            type: 'de',
            value: 1
        },
        aura: {
            type: 'extraCage',
            value: 1,
            description: '游戏开始时额外获得1个虾笼'
        },
        bonusScore: 2
    }
]

// 闹市卡（闹市区）- 每次游戏随机抽取3张（已更新为您指定的6张专属卡片）
export const marketplaceCards = [
    {
        id: 'm1',
        name: '县衙',
        type: 'county',
        action: {
            type: 'exchange',
            options: [
                {cost: {coins: 2}, reward: {de: 1}},
                {cost: {coins: 5}, reward: {de: 2}}
            ]
        },
        description: '花2金币换1德，或者花5金币换2德',
        auto: false
    },
    {
        id: 'm2',
        name: '府衙',
        type: 'prefecture',
        action: {
            type: 'exchange',
            options: [
                {cost: {lobsters: 1}, reward: {wang: 1}},
                {cost: {lobsters: 3}, reward: {wang: 2}}
            ]
        },
        description: '用1只龙虾换1望，或者用3只龙虾换2望',
        auto: false
    },
    {
        id: 'm3',
        name: '学堂',
        type: 'academy',
        description: '你的德望轨最低的一个提升一格，如果一样低则提升望的轨道一格',
        auto: true // 标志：不需要玩家做出二级选择，直接执行
    },
    {
                id: 'm4',
        name: '善堂',
        type: 'charity',
        description: '所有玩家中德轨最低者损失2只龙虾，望轨最低者损失2个金币',
        auto: true
    },
    {
        id: 'm5',
        name: '善学',
        type: 'breeding',
        description: '进行3次培养龙虾升级的行动',
        auto: true
    },
    {
        id: 'm6',
        name: '不劳而获',
        type: 'freebie',
        description: '可以直接获取一只普通龙虾',
        auto: true
    }
]

export function getSkill(lobsterId) {
    const card = titleCards.find((c) => c.id === lobsterId)
    if (lobsterId === 'grade3') return { getDiceSides: () => 6 }
    else if (lobsterId === 'grade2') return { getDiceSides: () => 8 }
    else if (lobsterId === 'grade1') return { getDiceSides: () => 10 }
    else if (lobsterId === 'royal') return { getDiceSides: () => 12 }
    else return card?.skill || null
}