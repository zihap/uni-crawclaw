import { LOBSTER_GRADES } from '@stores/game.js'

export const shuffleArray = (array) => {
    const newArray = [...array]
    for (let i = newArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[newArray[i], newArray[j]] = [newArray[j], newArray[i]]
    }
    return newArray
}

export const getRandomItem = (array) => {
    return array[Math.floor(Math.random() * array.length)]
}

export const getLobsterGradeName = (grade) => {
    const gradeNames = {
        [LOBSTER_GRADES.NORMAL]: '普通',
        [LOBSTER_GRADES.GRADE3]: '三品',
        [LOBSTER_GRADES.GRADE2]: '二品',
        [LOBSTER_GRADES.GRADE1]: '一品',
        [LOBSTER_GRADES.ROYAL]: '皇家'
    }
    return gradeNames[grade] || '未知'
}

export const getNextLobsterGrade = (currentGrade) => {
    const grades = [
        LOBSTER_GRADES.NORMAL,
        LOBSTER_GRADES.GRADE3,
        LOBSTER_GRADES.GRADE2,
        LOBSTER_GRADES.GRADE1,
        LOBSTER_GRADES.ROYAL
    ]
    const currentIndex = grades.indexOf(currentGrade)
    if (currentIndex < grades.length - 1) {
        return grades[currentIndex + 1]
    }
    return currentGrade
}

export const createLobster = (grade = LOBSTER_GRADES.NORMAL) => {
    return {
        id: Math.random().toString(36).substring(2, 11),
        grade,
        title: null
    }
}

export const checkLobsterGradeRequirement = (lobster, minGrade) => {
    const grades = [
        LOBSTER_GRADES.NORMAL,
        LOBSTER_GRADES.GRADE3,
        LOBSTER_GRADES.GRADE2,
        LOBSTER_GRADES.GRADE1,
        LOBSTER_GRADES.ROYAL
    ]
    const lobsterGradeIndex = grades.indexOf(lobster.grade)
    const minGradeIndex = grades.indexOf(minGrade)
    return lobsterGradeIndex >= minGradeIndex
}

export const getMarketPrice = (marketLobsterCount) => {
    if (marketLobsterCount > 5) {
        return {
            lobster: 1,
            cage: 4,
            seaweed: 1,
            seaweedBulk: 4
        }
    } else if (marketLobsterCount > 3) {
        return {
            lobster: 2,
            cage: 3,
            seaweed: 1,
            seaweedBulk: 4
        }
    } else {
        return {
            lobster: 3,
            cage: 2,
            seaweed: 1,
            seaweedBulk: 4
        }
    }
}

export const formatNumber = (num) => {
    return num.toString()
}

export const delay = (ms) => {
    return new Promise((resolve) => setTimeout(resolve, ms))
}
