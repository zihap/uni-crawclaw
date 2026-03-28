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

export const marketplaceCards = [
  {
    id: 'marketplace_1',
    name: '府衙',
    action: {
      type: 'exchange',
      options: [
        { cost: { lobsters: 1 }, reward: { wang: 1 } },
        { cost: { lobsters: 3 }, reward: { wang: 2 } }
      ]
    },
    description: '玩家支付1只龙虾换1望，或者3只龙虾换2望'
  },
  {
    id: 'marketplace_2',
    name: '书院',
    action: {
      type: 'exchange',
      options: [
        { cost: { seaweed: 2 }, reward: { de: 1 } },
        { cost: { coins: 5 }, reward: { de: 2 } }
      ]
    },
    description: '支付2根海草换1德，或5金币换2德'
  },
  {
    id: 'marketplace_3',
    name: '码头',
    action: {
      type: 'exchange',
      options: [
        { cost: { coins: 3 }, reward: { lobsters: 2 } },
        { cost: { cages: 1 }, reward: { seaweed: 3 } }
      ]
    },
    description: '3金币换2只龙虾，或1个虾笼换3根海草'
  },
  {
    id: 'marketplace_4',
    name: '钱庄',
    action: {
      type: 'exchange',
      options: [
        { cost: { lobsters: 1 }, reward: { coins: 2 } },
        { cost: { de: 1 }, reward: { coins: 5 } }
      ]
    },
    description: '1只龙虾换2金币，或1德换5金币'
  }
]
