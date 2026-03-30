<template>
    <view v-if="visible" class="modal-overlay" @click="handleOverlayClick">
        <view class="modal-container" @click.stop>
            <view class="modal-header">
                <text class="modal-title">竞技场对决</text>
                <text class="modal-subtitle">{{ getSubtitle() }}</text>
            </view>

            <view class="battle-info">
                <view class="player-info" :class="{ active: isChallenger }">
                    <text class="player-label">挑战者</text>
                    <text class="player-name">{{ challenger?.name }}</text>
                    <view v-if="challengerReady" class="ready-badge">已选择</view>
                </view>
                <text class="vs-text">VS</text>
                <view class="player-info" :class="{ active: isDefender }">
                    <text class="player-label">被挑战者</text>
                    <text class="player-name">{{ defender?.name }}</text>
                    <view v-if="defenderReady" class="ready-badge">已选择</view>
                </view>
            </view>

            <view class="selection-area">
                <!-- 当前玩家是挑战者，显示挑战者的龙虾选择 -->
                <view v-if="isChallenger" class="lobster-selection">
                    <text class="selection-title">选择你的出战龙虾</text>
                    <view class="lobster-list">
                        <view
                            v-for="(lobster, index) in myLobsters"
                            :key="lobster.id"
                            :class="['lobster-item', { selected: selectedIndex === index }]"
                            @click="selectLobster(index)"
                        >
                            <view class="lobster-icon">🦞</view>
                            <text class="lobster-name">{{ lobster.name }}</text>
                        </view>
                        <view v-if="myLobsters.length === 0" class="no-lobster">
                            <text>没有可用的龙虾</text>
                        </view>
                    </view>
                </view>

                <!-- 当前玩家是被挑战者，显示被挑战者的龙虾选择 -->
                <view v-else-if="isDefender" class="lobster-selection">
                    <text class="selection-title">选择你的出战龙虾</text>
                    <view class="lobster-list">
                        <view
                            v-for="(lobster, index) in myLobsters"
                            :key="lobster.id"
                            :class="['lobster-item', { selected: selectedIndex === index }]"
                            @click="selectLobster(index)"
                        >
                            <view class="lobster-icon">🦞</view>
                            <text class="lobster-name">{{ lobster.name }}</text>
                        </view>
                        <view v-if="myLobsters.length === 0" class="no-lobster">
                            <text>没有可用的龙虾</text>
                        </view>
                    </view>
                </view>

                <!-- 观战者视角 -->
                <view v-else class="spectator-view">
                    <text class="spectator-text">你是观战者，请等待双方选择龙虾...</text>
                </view>
            </view>

            <view class="modal-actions">
                <button
                    v-if="isChallenger || isDefender"
                    class="action-btn confirm-btn"
                    :disabled="!canConfirm || hasConfirmed"
                    @click="handleConfirm"
                >
                    {{ hasConfirmed ? '等待对方...' : '确认选择' }}
                </button>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { getLobsterGradeName } from '@utils/gameUtils'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule

const props = defineProps({
    visible: {
        type: Boolean,
        default: false
    },
    challenger: {
        type: Object,
        default: null
    },
    defender: {
        type: Object,
        default: null
    },
    playerId: {
        type: [Number, String],
        default: null
    },
    roomId: {
        type: String,
        default: ''
    }
})

const emit = defineEmits(['confirm', 'cancel', 'bothReady'])

const selectedIndex = ref(-1)
const hasConfirmed = ref(false)
const challengerReady = ref(false)
const defenderReady = ref(false)
const challengerSelectedLobster = ref(null)
const defenderSelectedLobster = ref(null)

// 判断当前玩家身份
const isChallenger = computed(() => {
    console.log('[DEBUG LobsterSelect] props.playerId:', props.playerId, 'props.challenger:', props.challenger?.id)
    if (props.playerId === null || !props.challenger) return false
    return String(props.challenger.id) === String(props.playerId)
})

const isDefender = computed(() => {
    console.log('[DEBUG LobsterSelect] props.playerId:', props.playerId, 'props.defender:', props.defender?.id)
    if (props.playerId === null || !props.defender) return false
    return String(props.defender.id) === String(props.playerId)
})

// 获取当前玩家的龙虾列表
const myLobsters = computed(() => {
    if (isChallenger.value || isDefender.value) {
        const player = isChallenger.value ? props.challenger : props.defender

        // 过滤普通龙虾 (id = 'normal')
        const validLobsters = player?.lobsters?.filter((l) => l && l.id && l.id !== 'normal') || []

        // 添加 titleCards 作为参战选项
        const titleCards = player?.titleCards?.filter((t) => t && t.id) || []

        // 合并两个列表
        return [...validLobsters, ...titleCards]
    }
    return []
})

const canConfirm = computed(() => {
    return selectedIndex.value >= 0
})

const getSubtitle = () => {
    if (isChallenger.value) return '你是挑战者，请选择出战龙虾'
    if (isDefender.value) return '你是被挑战者，请选择出战龙虾'
    return '观战模式'
}

const selectLobster = (index) => {
    if (hasConfirmed.value) return // 已确认后不能再更改
    selectedIndex.value = index
}

const handleConfirm = () => {
    if (!canConfirm.value || hasConfirmed.value) return

    const selectedLobster = myLobsters.value[selectedIndex.value]
    hasConfirmed.value = true

    console.log('[LobsterSelect] 发送选择结果:', {
        roomId: props.roomId,
        playerId: props.playerId,
        lobster: selectedLobster
    })

    // 发送选择结果到服务器
    socketService._send('lobsterSelected', {
        roomId: props.roomId,
        playerId: props.playerId,
        lobster: selectedLobster
    })

    // 本地标记自己已选择
    if (isChallenger.value) {
        challengerReady.value = true
        challengerSelectedLobster.value = selectedLobster
    } else if (isDefender.value) {
        defenderReady.value = true
        defenderSelectedLobster.value = selectedLobster
    }

    checkBothReady()
}

const handleCancel = () => {
    emit('cancel')
}

const handleOverlayClick = () => {
    // 点击遮罩层不关闭，必须点取消按钮
}

// 检查双方是否都已准备好
const checkBothReady = () => {
    if (challengerReady.value && defenderReady.value) {
        // 双方都已选择，触发进入竞技场
        emit('bothReady', {
            challenger: props.challenger,
            defender: props.defender,
            challengerLobster: challengerSelectedLobster.value,
            defenderLobster: defenderSelectedLobster.value
        })
    }
}

// 处理对手的选择结果（从服务器接收）
const handleOpponentSelected = (data) => {
    console.log('[LobsterSelect] 收到选择事件:', data)
    console.log('[LobsterSelect] 当前玩家ID:', props.playerId)
    console.log('[LobsterSelect] 挑战者ID:', props.challenger?.id)
    console.log('[LobsterSelect] 被挑战者ID:', props.defender?.id)

    // 忽略自己的选择（自己已经本地标记了）
    if (String(data.playerId) === String(props.playerId)) {
        console.log('[LobsterSelect] 忽略自己的选择')
        return
    }

    if (String(data.playerId) === String(props.challenger?.id)) {
        console.log('[LobsterSelect] 挑战者已选择')
        challengerReady.value = true
        challengerSelectedLobster.value = data.lobster
    } else if (String(data.playerId) === String(props.defender?.id)) {
        console.log('[LobsterSelect] 被挑战者已选择')
        defenderReady.value = true
        defenderSelectedLobster.value = data.lobster
    }
    checkBothReady()
}

// 注册WebSocket监听
const setupListeners = () => {
    console.log('[LobsterSelect] 注册监听器')
    socketService.on('lobsterSelected', handleOpponentSelected)
}

const cleanupListeners = () => {
    console.log('[LobsterSelect] 清理监听器')
    socketService.off('lobsterSelected', handleOpponentSelected)
}

// 当弹窗打开时重置状态
watch(
    () => props.visible,
    (newVal) => {
        if (newVal) {
            selectedIndex.value = -1
            hasConfirmed.value = false
            challengerReady.value = false
            defenderReady.value = false
            challengerSelectedLobster.value = null
            defenderSelectedLobster.value = null
            setupListeners()
        } else {
            cleanupListeners()
        }
    }
)

// 组件挂载时也注册监听器（防止弹窗已打开时没有注册）
onMounted(() => {
    if (props.visible) {
        setupListeners()
    }
})

onUnmounted(() => {
    cleanupListeners()
})

// 暴露方法供外部调用（处理对手选择）
defineExpose({
    handleOpponentSelected
})
</script>
