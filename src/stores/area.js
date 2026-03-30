import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 区域状态管理Store
 * 负责管理游戏区域的通用状态和操作
 */
export const useAreaStore = defineStore('area', () => {
    // 区域列表
    const areas = ref([])

    // 当前激活的区域
    const currentArea = ref(null)

    // 计算属性：获取所有区域
    const allAreas = computed(() => areas.value)

    // 计算属性：获取区域数量
    const areaCount = computed(() => areas.value.length)

    /**
     * 初始化区域
     * @param {Array} areaList - 区域列表
     */
    const initAreas = (areaList) => {
        areas.value = areaList
    }

    /**
     * 设置当前区域
     * @param {Object} area - 区域对象
     */
    const setCurrentArea = (area) => {
        currentArea.value = area
    }

    /**
     * 获取指定区域
     * @param {string} areaId - 区域ID
     * @returns {Object|null} 区域对象
     */
    const getAreaById = (areaId) => {
        return areas.value.find((area) => area.id === areaId) || null
    }

    /**
     * 更新区域状态
     * @param {string} areaId - 区域ID
     * @param {Object} updates - 更新的属性
     */
    const updateArea = (areaId, updates) => {
        const area = getAreaById(areaId)
        if (area) {
            Object.assign(area, updates)
        }
    }

    /**
     * 重置区域状态
     */
    const resetAreas = () => {
        areas.value = []
        currentArea.value = null
    }

    return {
        // 状态
        areas,
        currentArea,

        // 计算属性
        allAreas,
        areaCount,

        // 方法
        initAreas,
        setCurrentArea,
        getAreaById,
        updateArea,
        resetAreas
    }
})
