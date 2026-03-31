import cardConfig from '../../card_config.json'

// 从 JSON 读取 titleCards，补回函数逻辑
export const titleCards = cardConfig.titleCards.map((card) => {
    if (!card.skill) return card
    const s = { ...card.skill }
    if (s.diceSides != null) s.getDiceSides = () => s.diceSides
    if (s.modifyRule) {
        const rule = s.modifyRule
        s.modifyDice = (value) => (value <= rule.threshold ? rule.to : value)
    }
    if (s.bonusStep) {
        const step = s.bonusStep
        s.apply = (context) => {
            context.bonusSteps = (context.bonusSteps || 0) + step
        }
    }
    return { ...card, skill: s }
})

export const tributeCards = cardConfig.tributeCards

export const marketplaceCards = cardConfig.marketplaceCards

export function getSkill(lobsterId) {
    const card = titleCards.find((c) => c.id === lobsterId)
    if (lobsterId === 'grade3') return { getDiceSides: () => 6 }
    else if (lobsterId === 'grade2') return { getDiceSides: () => 8 }
    else if (lobsterId === 'grade1') return { getDiceSides: () => 10 }
    else if (lobsterId === 'royal') return { getDiceSides: () => 10 }
    else return card?.skill || null
}
