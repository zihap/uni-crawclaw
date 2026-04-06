<template>
    <view class="room-container">
        <view class="scanline"></view>
        <view class="header">
            <view class="room-info">
                <text class="room-label">房间号</text>
                <text class="room-code">{{ roomId }}</text>
            </view>
            <view class="player-count">
                <text class="count">{{ playerStore.players.length }}/{{ maxPlayers }}</text>
                <text class="label">玩家</text>
            </view>
        </view>

        <view class="players-section">
            <text class="section-title">玩家列表</text>
            <view class="players-list">
                <view
                    v-for="(player, index) in playerStore.players"
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
                                    ? '房主 已准备'
                                    : '已准备'
                                : player.isHost
                                  ? '房主'
                                  : player.isOnline
                                    ? '等待中'
                                    : '离线'
                        }}</text>
                    </view>
                    <view v-if="String(player.id) === String(playerId)" class="me-badge">
                        <text>我</text>
                    </view>
                    <view v-if="player.ready" class="ready-badge">
                        <text class="ready-icon"></text>
                    </view>
                </view>

                <view
                    v-for="i in maxPlayers - playerStore.players.length"
                    :key="'empty-' + i"
                    class="player-card empty"
                >
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
                v-if="isHost && !allPlayersReady && playerStore.players.length >= 1"
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
import { usePlayerStore } from '@stores/player.js'
import socketModule from '@utils/socket.js'
const socketService = socketModule.socketService || socketModule
const playerStore = usePlayerStore()

const roomId = ref('')
const playerId = ref(null)
const maxPlayers = ref(4)
const isReady = ref(false)
const isConnected = ref(false)

const isHost = computed(() => {
    const me = playerStore.players.find((p) => String(p.id) === String(playerId.value))
    return me?.isHost || false
})

const allPlayersReady = computed(() => {
    return playerStore.players.length >= 1 && playerStore.players.every((p) => p.ready)
})

function getPlayerEmoji(index) {
    const emojis = ['🦞', '🦀', '🦐', '🐙']
    return emojis[index % emojis.length]
}

function getWaitingTips() {
    if (playerStore.players.length < 1) {
        return '等待玩家加入...'
    }
    if (!allPlayersReady.value) {
        const unreadyCount = playerStore.players.filter((p) => !p.ready).length
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

    socketService.onAction('serverRoomAction', 'roomStateUpdate', (data) => {
        if (data && data.players) {
            playerStore.syncPlayers(data.players)
            const me = data.players.find((p) => String(p.id) === String(playerId.value))
            if (me) {
                isReady.value = me.ready
            }
            if (data.maxPlayers) {
                maxPlayers.value = data.maxPlayers
            }
        }
    })

    socketService.onAction('serverRoomAction', 'playerJoined', (data) => {
        uni.showToast({
            title: `${data.player?.name || '玩家'} 加入了房间`,
            icon: 'none',
            duration: 1500
        })
        if (data.players) {
            playerStore.syncPlayers(data.players)
        }
    })

    socketService.onAction('serverRoomAction', 'playerLeft', (data) => {
        uni.showToast({
            title: `${data.playerName || '玩家'} 离开了房间`,
            icon: 'none',
            duration: 1500
        })
        if (data.players) {
            playerStore.syncPlayers(data.players)
        }
    })

    socketService.onAction('serverRoomAction', 'playerStatusChange', (data) => {
        if (data.players) {
            playerStore.syncPlayers(data.players)
        }
    })

    socketService.onAction('serverRoomAction', 'playerReady', (data) => {
        if (data.players) {
            playerStore.syncPlayers(data.players)
            const me = data.players.find((p) => String(p.id) === String(playerId.value))
            if (me) {
                isReady.value = me.ready
            }
        }
    })

    socketService.onAction('serverRoomAction', 'playerReconnected', (data) => {
        uni.showToast({
            title: `${data.player?.name || '玩家'} 已重新连接`,
            icon: 'success',
            duration: 1500
        })
        if (data.players) {
            playerStore.syncPlayers(data.players)
        }
    })

    socketService.onAction('serverGameAction', 'gameStarted', (gameState) => {
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
    socketService.offAction('serverRoomAction')
    socketService.offAction('serverGameAction')
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

    const savedMaxPlayers = uni.getStorageSync('maxPlayers')
    if (savedMaxPlayers) {
        maxPlayers.value = savedMaxPlayers
        uni.removeStorageSync('maxPlayers')
    }
})

onUnmounted(() => {
    cleanupListeners()
    playerStore.resetPlayers()
})
</script>

<style scoped>
.room-container {
    min-height: 100vh;
    background: #0a0a1a;
    padding: 60rpx 30rpx;
    position: relative;
    overflow: hidden;
}

.room-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
        linear-gradient(rgba(78, 205, 196, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(78, 205, 196, 0.03) 1px, transparent 1px);
    background-size: 40rpx 40rpx;
    pointer-events: none;
}

.scanline {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 200rpx;
    background: linear-gradient(to bottom, transparent, rgba(233, 69, 96, 0.03), transparent);
    animation: scanline 8s linear infinite;
    pointer-events: none;
    z-index: 1;
}

@keyframes scanline {
    0% {
        transform: translateY(-200rpx);
    }
    100% {
        transform: translateY(100vh);
    }
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30rpx;
    position: relative;
    z-index: 2;
}

.room-info {
    text-align: left;
}

.room-label {
    font-size: 24rpx;
    color: #a0a0b0;
}

.room-code {
    display: block;
    font-size: 48rpx;
    font-weight: 800;
    color: #fff;
    letter-spacing: 6rpx;
    text-shadow:
        0 0 10rpx rgba(78, 205, 196, 0.6),
        0 0 30rpx rgba(78, 205, 196, 0.3);
}

.player-count {
    text-align: center;
    background: rgba(26, 26, 46, 0.8);
    padding: 20rpx 30rpx;
    border-radius: 20rpx;
    border: 1rpx solid rgba(78, 205, 196, 0.2);
    backdrop-filter: blur(10rpx);
}

.count {
    display: block;
    font-size: 36rpx;
    font-weight: 700;
    color: #4ecdc4;
    text-shadow: 0 0 10rpx rgba(78, 205, 196, 0.4);
}

.label {
    font-size: 22rpx;
    color: #a0a0b0;
}

.players-section {
    margin-bottom: 40rpx;
    position: relative;
    z-index: 2;
}

.section-title {
    font-size: 28rpx;
    color: #4ecdc4;
    margin-bottom: 20rpx;
    display: block;
    text-shadow: 0 0 8rpx rgba(78, 205, 196, 0.4);
    letter-spacing: 2rpx;
}

.players-list {
    display: flex;
    flex-direction: column;
    gap: 20rpx;
}

.player-card {
    display: flex;
    align-items: center;
    background: #1a1a2e;
    border-radius: 24rpx;
    padding: 24rpx;
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.3);
    position: relative;
    transition: all 0.3s ease;
    border: 1rpx solid rgba(78, 205, 196, 0.1);
}

.player-card.is-me {
    border: 2rpx solid #ffd700;
    box-shadow:
        0 0 20rpx rgba(255, 215, 0, 0.3),
        0 4rpx 20rpx rgba(0, 0, 0, 0.3);
}

.player-card.is-host {
    background: linear-gradient(135deg, rgba(255, 215, 0, 0.08), rgba(26, 26, 46, 0.9));
    border: 2rpx solid rgba(255, 215, 0, 0.4);
}

.player-card.is-ready {
    border: 2rpx solid #4ecdc4;
    background: linear-gradient(135deg, rgba(78, 205, 196, 0.08), rgba(26, 26, 46, 0.9));
    box-shadow: 0 0 15rpx rgba(78, 205, 196, 0.2);
}

.player-card.is-host.is-ready {
    background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(78, 205, 196, 0.05));
    border-color: #ffd700;
}

.player-card.is-offline {
    opacity: 0.5;
    background: #0d0d2b;
    border-color: rgba(255, 255, 255, 0.05);
}

.player-card.empty {
    background: rgba(26, 26, 46, 0.4);
    border: 2rpx dashed rgba(78, 205, 196, 0.2);
    box-shadow: none;
}

.player-avatar {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #16213e, #0d0d2b);
    border: 2rpx solid rgba(78, 205, 196, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20rpx;
    transition: all 0.3s ease;
}

.avatar-ready {
    background: linear-gradient(135deg, rgba(78, 205, 196, 0.2), rgba(78, 205, 196, 0.1));
    border-color: #4ecdc4;
    box-shadow: 0 0 15rpx rgba(78, 205, 196, 0.4);
}

.avatar-offline {
    background: #0d0d2b;
    border-color: rgba(255, 255, 255, 0.1);
}

.empty-avatar {
    background: rgba(26, 26, 46, 0.5);
    border-color: rgba(78, 205, 196, 0.15);
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
    color: #fff;
}

.player-name.empty-text {
    color: rgba(255, 255, 255, 0.3);
}

.offline-tag {
    font-size: 24rpx;
    color: #666;
    font-weight: normal;
}

.player-status {
    font-size: 24rpx;
    color: #666;
    transition: color 0.3s ease;
}

.status-ready {
    color: #4ecdc4;
    font-weight: 600;
    text-shadow: 0 0 6rpx rgba(78, 205, 196, 0.3);
}

.me-badge {
    position: absolute;
    top: -10rpx;
    right: 20rpx;
    background: linear-gradient(135deg, #ffd700, #e6c200);
    color: #0a0a1a;
    font-size: 20rpx;
    font-weight: 700;
    padding: 4rpx 16rpx;
    border-radius: 20rpx;
    box-shadow: 0 0 10rpx rgba(255, 215, 0, 0.4);
}

.ready-badge {
    width: 48rpx;
    height: 48rpx;
    border-radius: 50%;
    background: #4ecdc4;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 15rpx rgba(78, 205, 196, 0.5);
}

.ready-icon {
    display: block;
    width: 20rpx;
    height: 20rpx;
    border-right: 4rpx solid #0a0a1a;
    border-bottom: 4rpx solid #0a0a1a;
    transform: rotate(45deg);
    margin-top: -4rpx;
}

.waiting-tips {
    text-align: center;
    margin-bottom: 40rpx;
    position: relative;
    z-index: 2;
}

.tips-text {
    font-size: 26rpx;
    color: #a0a0b0;
    text-shadow: 0 0 8rpx rgba(160, 160, 176, 0.2);
}

.action-section {
    display: flex;
    flex-direction: column;
    gap: 20rpx;
    position: relative;
    z-index: 2;
}

.btn-ready {
    width: 100%;
    height: 100rpx;
    background: linear-gradient(135deg, #4ecdc4 0%, #3ba89f 100%);
    border: none;
    border-radius: 50rpx;
    box-shadow:
        0 0 20rpx rgba(78, 205, 196, 0.4),
        0 8rpx 24rpx rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.btn-ready:active {
    box-shadow: 0 0 30rpx rgba(78, 205, 196, 0.6);
    transform: scale(0.98);
}

.btn-ready.ready {
    background: linear-gradient(135deg, #ffd700 0%, #e6c200 100%);
    box-shadow:
        0 0 20rpx rgba(255, 215, 0, 0.4),
        0 8rpx 24rpx rgba(0, 0, 0, 0.3);
}

.btn-ready:disabled {
    background: #1a1a2e;
    box-shadow: none;
    border: 1rpx solid rgba(255, 255, 255, 0.1);
}

.btn-text {
    font-size: 32rpx;
    font-weight: 700;
    color: #0a0a1a;
    text-shadow: none;
}

.btn-ready.ready .btn-text {
    color: #0a0a1a;
}

.btn-force-start {
    width: 100%;
    height: 100rpx;
    background: linear-gradient(135deg, #e94560 0%, #c23152 100%);
    border: none;
    border-radius: 50rpx;
    box-shadow:
        0 0 20rpx rgba(233, 69, 96, 0.4),
        0 8rpx 24rpx rgba(0, 0, 0, 0.3);
}

.btn-force-start:disabled {
    background: #1a1a2e;
    box-shadow: none;
    border: 1rpx solid rgba(255, 255, 255, 0.1);
}

.btn-start {
    width: 100%;
    height: 100rpx;
    background: linear-gradient(135deg, #4ecdc4 0%, #3ba89f 100%);
    border: none;
    border-radius: 50rpx;
    box-shadow:
        0 0 20rpx rgba(78, 205, 196, 0.4),
        0 8rpx 24rpx rgba(0, 0, 0, 0.3);
}

.btn-start:disabled {
    background: #1a1a2e;
    box-shadow: none;
    border: 1rpx solid rgba(255, 255, 255, 0.1);
}

.btn-leave {
    width: 100%;
    height: 80rpx;
    background: transparent;
    border: 2rpx solid rgba(255, 255, 255, 0.15);
    border-radius: 40rpx;
    margin-top: 20rpx;
    transition: all 0.3s ease;
}

.btn-leave:active {
    border-color: #e94560;
    background: rgba(233, 69, 96, 0.1);
}

.btn-text-leave {
    font-size: 28rpx;
    color: #a0a0b0;
}
</style>
