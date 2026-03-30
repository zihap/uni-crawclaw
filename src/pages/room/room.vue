<template>
    <view class="room-container">
        <view class="header">
            <view class="room-info">
                <text class="room-label">房间号</text>
                <text class="room-code">{{ roomId }}</text>
            </view>
            <view class="player-count">
                <text class="count">{{ players.length }}/{{ maxPlayers }}</text>
                <text class="label">玩家</text>
            </view>
        </view>

        <view class="players-section">
            <text class="section-title">玩家列表</text>
            <view class="players-list">
                <view
                    v-for="(player, index) in players"
                    :key="player.id"
                    :class="[
                        'player-card',
                        {
                            'is-me': String(player.id) === String(playerId),
                            'is-host': player.isHost,
                            'is-ready': player.ready,
                            'is-offline': !player.isOnline
                        }
                    ]"
                >
                    <view
                        class="player-avatar"
                        :class="{ 'avatar-ready': player.ready, 'avatar-offline': !player.isOnline }"
                    >
                        <text class="avatar-text">{{ getPlayerEmoji(index) }}</text>
                    </view>
                    <view class="player-info">
                        <text class="player-name"
                            >{{ player.name }}<text v-if="!player.isOnline" class="offline-tag"> (离线)</text></text
                        >
                        <text class="player-status" :class="{ 'status-ready': player.ready }">{{
                            player.ready
                                ? player.isHost
                                    ? '👑 房主 ✓ 已准备'
                                    : '✓ 已准备'
                                : player.isHost
                                  ? '👑 房主'
                                  : player.isOnline
                                    ? '等待中'
                                    : '离线'
                        }}</text>
                    </view>
                    <view v-if="String(player.id) === String(playerId)" class="me-badge">
                        <text>我</text>
                    </view>
                    <view v-if="player.ready" class="ready-badge">
                        <text>✓</text>
                    </view>
                </view>

                <view v-for="i in maxPlayers - players.length" :key="'empty-' + i" class="player-card empty">
                    <view class="player-avatar empty-avatar">
                        <text class="avatar-text">?</text>
                    </view>
                    <view class="player-info">
                        <text class="player-name empty-text">等待加入...</text>
                    </view>
                </view>
            </view>
        </view>

        <view class="waiting-tips">
            <text class="tips-text">{{ getWaitingTips() }}</text>
        </view>

        <view class="action-section">
            <button class="btn-ready" :class="{ ready: isReady }" @click="toggleReady" :disabled="!isConnected">
                <text class="btn-text">{{ isReady ? '取消准备' : isHost ? '准备开始' : '准备' }}</text>
            </button>

            <button v-if="isHost && allPlayersReady" class="btn-start" @click="startGame" :disabled="!isConnected">
                <text class="btn-text">开始游戏</text>
            </button>

            <button
                v-if="isHost && !allPlayersReady && players.length >= 1"
                class="btn-force-start"
                @click="forceStart"
                :disabled="!isConnected"
            >
                <text class="btn-text">开始游戏</text>
            </button>

            <button class="btn-leave" @click="leaveRoom">
                <text class="btn-text-leave">离开房间</text>
            </button>
        </view>
    </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import socketModule from '@utils/socket.js'
const socketService = socketModule.socketService || socketModule

const roomId = ref('')
const playerId = ref(null)
const players = ref([])
const maxPlayers = ref(4)
const isReady = ref(false)
const isConnected = ref(false)

const isHost = computed(() => {
    const me = players.value.find((p) => String(p.id) === String(playerId.value))
    return me?.isHost || false
})

const allPlayersReady = computed(() => {
    return players.value.length >= 1 && players.value.every((p) => p.ready)
})

function getPlayerEmoji(index) {
    const emojis = ['🦞', '🦀', '🦐', '🐙']
    return emojis[index % emojis.length]
}

function getWaitingTips() {
    if (players.value.length < 1) {
        return '等待玩家加入...'
    }
    if (!allPlayersReady.value) {
        const unreadyCount = players.value.filter((p) => !p.ready).length
        return `等待 ${unreadyCount} 位玩家准备...`
    }
    if (isHost.value) {
        return '所有玩家已准备，点击开始游戏'
    }
    return '等待房主开始游戏...'
}

function toggleReady() {
    const newReadyState = !isReady.value
    isReady.value = newReadyState
    socketService.setReady(newReadyState, false)
}

function forceStart() {
    isReady.value = true
    socketService.setReady(true, true)
}

function startGame() {
    isReady.value = true
    socketService.setReady(true, false)
}

function leaveRoom() {
    uni.showModal({
        title: '提示',
        content: '确定要离开房间吗？',
        success: (res) => {
            if (res.confirm) {
                socketService.leaveRoom()
                uni.removeStorageSync('roomId')
                uni.removeStorageSync('playerId')
                socketService.disconnect()
                uni.redirectTo({
                    url: '/pages/lobby/lobby'
                })
            }
        }
    })
}

function setupSocketListeners() {
    socketService.on('connect', () => {
        isConnected.value = true
    })

    socketService.on('disconnect', () => {
        isConnected.value = false
    })

    socketService.on('connectError', () => {
        isConnected.value = false
    })

    socketService.on('reconnecting', () => {
        isConnected.value = false
    })

    socketService.on('reconnectFailed', () => {
        isConnected.value = false
        uni.showToast({
            title: '重连失败，请检查网络',
            icon: 'none',
            duration: 2000
        })
    })

    socketService.on('roomStateUpdate', (data) => {
        if (data && data.players) {
            players.value = data.players
            const me = data.players.find((p) => String(p.id) === String(playerId.value))
            if (me) {
                isReady.value = me.ready
            }
            if (data.maxPlayers) {
                maxPlayers.value = data.maxPlayers
            }
        }
    })

    socketService.on('playerJoined', (data) => {
        uni.showToast({
            title: `${data.player?.name || '玩家'} 加入了房间`,
            icon: 'none',
            duration: 1500
        })
        if (data.players) {
            players.value = data.players
        }
    })

    socketService.on('playerLeft', (data) => {
        uni.showToast({
            title: `${data.playerName || '玩家'} 离开了房间`,
            icon: 'none',
            duration: 1500
        })
        if (data.players) {
            players.value = data.players
        }
    })

    socketService.on('playerOnline', (data) => {
        if (data.players) {
            players.value = data.players
        }
    })

    socketService.on('playerOffline', (data) => {
        if (data.players) {
            players.value = data.players
        }
    })

    socketService.on('playerReady', (data) => {
        if (data.players) {
            players.value = data.players
            const me = data.players.find((p) => String(p.id) === String(playerId.value))
            if (me) {
                isReady.value = me.ready
            }
        }
    })

    socketService.on('playerReconnected', (data) => {
        uni.showToast({
            title: `${data.player?.name || '玩家'} 已重新连接`,
            icon: 'success',
            duration: 1500
        })
        if (data.players) {
            players.value = data.players
        }
    })

    socketService.on('gameStarted', (gameState) => {
        const gameStateStr = encodeURIComponent(JSON.stringify(gameState))
        uni.redirectTo({
            url: `/pages/online-game/onlineGame?roomId=${roomId.value}&playerId=${playerId.value}&gameState=${gameStateStr}`
        })
    })

    socketService.on('error', (data) => {
        uni.showToast({
            title: data.message || '发生错误',
            icon: 'none'
        })
    })
}

function cleanupListeners() {
    socketService.off('connect')
    socketService.off('disconnect')
    socketService.off('connectError')
    socketService.off('reconnecting')
    socketService.off('reconnectFailed')
    socketService.off('roomStateUpdate')
    socketService.off('playerJoined')
    socketService.off('playerLeft')
    socketService.off('playerOnline')
    socketService.off('playerOffline')
    socketService.off('playerReady')
    socketService.off('playerReconnected')
    socketService.off('gameStarted')
    socketService.off('error')
}

onMounted(async () => {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    const options = currentPage.options || {}

    roomId.value = options.roomId || uni.getStorageSync('roomId') || ''
    playerId.value = parseInt(options.playerId) || uni.getStorageSync('playerId')

    if (!roomId.value || playerId.value === null) {
        uni.redirectTo({
            url: '/pages/lobby/lobby'
        })
        return
    }

    const isAlreadyConnected = socketService.connected && socketService.currentRoomId === roomId.value

    if (!isAlreadyConnected) {
        socketService.disconnect()
        socketService.clearRoomContext()

        setupSocketListeners()

        setTimeout(() => {
            socketService.setRoomContext(roomId.value, playerId.value)
            socketService.connect(roomId.value, playerId.value)
        }, 100)
    } else {
        setupSocketListeners()
        socketService.setRoomContext(roomId.value, playerId.value)
    }

    const savedPlayers = uni.getStorageSync('roomPlayers')
    if (savedPlayers) {
        players.value = JSON.parse(savedPlayers)
        const me = players.value.find((p) => String(p.id) === String(playerId.value))
        if (me) {
            isReady.value = me.ready
        }
        uni.removeStorageSync('roomPlayers')
    }

    const savedMaxPlayers = uni.getStorageSync('maxPlayers')
    if (savedMaxPlayers) {
        maxPlayers.value = savedMaxPlayers
        uni.removeStorageSync('maxPlayers')
    }
})

onUnmounted(() => {
    cleanupListeners()
})
</script>

<style scoped>
.room-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 60rpx 30rpx;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30rpx;
}

.room-info {
    text-align: left;
}

.room-label {
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.7);
}

.room-code {
    display: block;
    font-size: 48rpx;
    font-weight: 800;
    color: white;
    letter-spacing: 4rpx;
}

.player-count {
    text-align: center;
    background: rgba(255, 255, 255, 0.2);
    padding: 20rpx 30rpx;
    border-radius: 20rpx;
}

.count {
    display: block;
    font-size: 36rpx;
    font-weight: 700;
    color: white;
}

.label {
    font-size: 22rpx;
    color: rgba(255, 255, 255, 0.7);
}

.players-section {
    margin-bottom: 40rpx;
}

.section-title {
    font-size: 28rpx;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 20rpx;
    display: block;
}

.players-list {
    display: flex;
    flex-direction: column;
    gap: 20rpx;
}

.player-card {
    display: flex;
    align-items: center;
    background: white;
    border-radius: 24rpx;
    padding: 24rpx;
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
    position: relative;
    transition: all 0.3s ease;
}

.player-card.is-me {
    border: 4rpx solid #ffd700;
}

.player-card.is-host {
    background: linear-gradient(135deg, #fff9e6 0%, #fff5cc 100%);
    border: 4rpx solid #faad14;
}

.player-card.is-ready {
    border: 4rpx solid #52c41a;
    background: linear-gradient(135deg, #f6ffed 0%, #e6fffb 100%);
}

.player-card.is-host.is-ready {
    background: linear-gradient(135deg, #f6ffed 0%, #fff9e6 100%);
}

.player-card.is-offline {
    opacity: 0.6;
    background: #f5f5f5;
}

.player-card.empty {
    background: rgba(255, 255, 255, 0.2);
    border: 2rpx dashed rgba(255, 255, 255, 0.4);
}

.player-avatar {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20rpx;
    transition: all 0.3s ease;
}

.avatar-ready {
    background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
    box-shadow: 0 4rpx 12rpx rgba(82, 196, 26, 0.4);
}

.avatar-offline {
    background: linear-gradient(135deg, #999 0%, #666 100%);
}

.empty-avatar {
    background: rgba(255, 255, 255, 0.3);
}

.avatar-text {
    font-size: 40rpx;
}

.player-info {
    flex: 1;
}

.player-name {
    display: block;
    font-size: 32rpx;
    font-weight: 700;
    color: #333;
}

.player-name.empty-text {
    color: rgba(255, 255, 255, 0.6);
}

.offline-tag {
    font-size: 24rpx;
    color: #999;
    font-weight: normal;
}

.player-status {
    font-size: 24rpx;
    color: #999;
    transition: color 0.3s ease;
}

.status-ready {
    color: #52c41a;
    font-weight: 600;
}

.me-badge {
    position: absolute;
    top: -10rpx;
    right: 20rpx;
    background: #ffd700;
    color: #333;
    font-size: 20rpx;
    font-weight: 700;
    padding: 4rpx 16rpx;
    border-radius: 20rpx;
}

.ready-badge {
    width: 48rpx;
    height: 48rpx;
    border-radius: 50%;
    background: #52c41a;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28rpx;
    font-weight: 700;
}

.waiting-tips {
    text-align: center;
    margin-bottom: 40rpx;
}

.tips-text {
    font-size: 26rpx;
    color: rgba(255, 255, 255, 0.8);
}

.action-section {
    display: flex;
    flex-direction: column;
    gap: 20rpx;
}

.btn-ready {
    width: 100%;
    height: 100rpx;
    background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
    border: none;
    border-radius: 50rpx;
    box-shadow: 0 8rpx 24rpx rgba(82, 196, 26, 0.4);
}

.btn-ready.ready {
    background: linear-gradient(135deg, #faad14 0%, #d48806 100%);
    box-shadow: 0 8rpx 24rpx rgba(250, 173, 20, 0.4);
}

.btn-ready:disabled {
    background: #d9d9d9;
    box-shadow: none;
}

.btn-text {
    font-size: 32rpx;
    font-weight: 700;
    color: white;
}

.btn-force-start {
    width: 100%;
    height: 100rpx;
    background: linear-gradient(135deg, #f5222d 0%, #cf1322 100%);
    border: none;
    border-radius: 50rpx;
    box-shadow: 0 8rpx 24rpx rgba(245, 34, 45, 0.4);
}

.btn-force-start:disabled {
    background: #d9d9d9;
    box-shadow: none;
}

.btn-start {
    width: 100%;
    height: 100rpx;
    background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
    border: none;
    border-radius: 50rpx;
    box-shadow: 0 8rpx 24rpx rgba(82, 196, 26, 0.4);
}

.btn-start:disabled {
    background: #d9d9d9;
    box-shadow: none;
}

.btn-leave {
    width: 100%;
    height: 80rpx;
    background: transparent;
    border: 2rpx solid rgba(255, 255, 255, 0.5);
    border-radius: 40rpx;
    margin-top: 20rpx;
}

.btn-text-leave {
    font-size: 28rpx;
    color: rgba(255, 255, 255, 0.8);
}
</style>
