<template>
    <view class="lobby-container">
        <view class="header">
            <text class="title">🎮 联机对战</text>
            <text class="subtitle">与好友一起斗龙虾</text>
        </view>

        <view class="mode-tabs">
            <view :class="['tab', { active: mode === 'create' }]" @click="mode = 'create'">
                <text class="tab-text">创建房间</text>
            </view>
            <view :class="['tab', { active: mode === 'join' }]" @click="mode = 'join'">
                <text class="tab-text">加入房间</text>
            </view>
        </view>

        <view class="content-card">
            <view v-if="mode === 'create'" class="create-section">
                <view class="input-group">
                    <text class="input-label">你的昵称</text>
                    <input class="input-field" v-model="playerName" placeholder="请输入昵称" maxlength="10" />
                </view>
                <view class="input-group">
                    <text class="input-label">玩家数量</text>
                    <view class="player-count-selector">
                        <view
                            v-for="count in [2, 3, 4]"
                            :key="count"
                            :class="['count-btn', { active: playerCount === count }]"
                            @click="playerCount = count"
                        >
                            <text>{{ count }}人</text>
                        </view>
                    </view>
                </view>
                <button class="btn-create" @click="createRoom" :disabled="!playerName.trim() || loading">
                    <text v-if="loading" class="btn-text">创建中...</text>
                    <text v-else class="btn-text">创建房间</text>
                </button>
                <view class="room-code-box" v-if="createdRoomId">
                    <text class="room-code-label">房间号</text>
                    <text class="room-code">{{ createdRoomId }}</text>
                    <text class="room-code-hint">分享给好友让他们加入</text>
                </view>
            </view>

            <view v-else class="join-section">
                <view class="input-group">
                    <text class="input-label">你的昵称</text>
                    <input class="input-field" v-model="playerName" placeholder="请输入昵称" maxlength="10" />
                </view>
                <view class="input-group">
                    <text class="input-label">房间号</text>
                    <input class="input-field" v-model="roomId" placeholder="请输入6位房间号" maxlength="6" />
                </view>
                <button class="btn-join" @click="joinRoom" :disabled="!playerName.trim() || !roomId.trim() || loading">
                    <text v-if="loading" class="btn-text">加入中...</text>
                    <text v-else class="btn-text">加入房间</text>
                </button>
            </view>

            <view class="error-box" v-if="errorMessage">
                <text class="error-text">{{ errorMessage }}</text>
            </view>
        </view>

        <view class="back-btn" @click="goBack">
            <text class="back-text">返回</text>
        </view>
    </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import socketModule from '../../utils/socket.js'
const socketService = socketModule.socketService || socketModule

const mode = ref('create')
const playerName = ref('')
const playerCount = ref(4)
const roomId = ref('')
const createdRoomId = ref('')
const loading = ref(false)
const errorMessage = ref('')

const playerId = ref(null)
const userId = ref(uni.getStorageSync('userId') || '')

function generateUserId() {
    if (!userId.value) {
        userId.value = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
        uni.setStorageSync('userId', userId.value)
    }
    return userId.value
}

function createRoom() {
    if (!playerName.value.trim()) {
        errorMessage.value = '请输入昵称'
        return
    }

    loading.value = true
    errorMessage.value = ''
    createdRoomId.value = ''

    socketService.setUserId(generateUserId())

    const onConnect = () => {
        socketService.off('connect', onConnect)
        socketService.createRoom(playerName.value.trim(), userId.value, playerCount.value)
    }

    // 检查当前连接是否是大厅端点，如果不是则先断开
    const isConnectedToLobby = socketService.connected && socketService._wsUrl === 'ws://localhost:3100/ws/lobby'

    if (isConnectedToLobby) {
        onConnect()
    } else {
        if (socketService.connected) {
            socketService.disconnect()
        }
        socketService.on('connect', onConnect)
        socketService.connect()
    }
}

function joinRoom() {
    if (!playerName.value.trim()) {
        errorMessage.value = '请输入昵称'
        return
    }
    if (!roomId.value.trim()) {
        errorMessage.value = '请输入房间号'
        return
    }

    loading.value = true
    errorMessage.value = ''

    socketService.setUserId(generateUserId())

    const onConnect = () => {
        socketService.off('connect', onConnect)
        socketService.joinRoom(roomId.value.trim().toUpperCase(), playerName.value.trim(), userId.value)
    }

    // 检查当前连接是否是大厅端点，如果不是则先断开
    const isConnectedToLobby = socketService.connected && socketService._wsUrl === 'ws://localhost:3100/ws/lobby'

    if (isConnectedToLobby) {
        onConnect()
    } else {
        if (socketService.connected) {
            socketService.disconnect()
        }
        socketService.on('connect', onConnect)
        socketService.connect()
    }
}

function setupListeners() {
    socketService.on('connectError', (data) => {
        loading.value = false
        errorMessage.value = '连接服务器失败，请检查网络'
    })

    socketService.onAction('serverRoomAction', 'roomCreated', (data) => {
        loading.value = false
        createdRoomId.value = data.roomId
        playerId.value = data.playerId

        uni.setStorageSync('roomId', data.roomId)
        uni.setStorageSync('playerId', data.playerId)
        if (data.gameState && data.gameState.players) {
            uni.setStorageSync('roomPlayers', JSON.stringify(data.gameState.players))
        }
        if (data.gameState && data.gameState.maxPlayers) {
            uni.setStorageSync('maxPlayers', data.gameState.maxPlayers)
        }

        uni.redirectTo({
            url: `/pages/room/room?roomId=${data.roomId}&playerId=${data.playerId}`
        })
    })

    socketService.onAction('serverRoomAction', 'playerReconnected', (data) => {
        loading.value = false
        if (data.player) {
            playerId.value = data.player.id
            uni.setStorageSync('roomId', roomId.value.trim().toUpperCase())
            uni.setStorageSync('playerId', data.player.id)
            if (data.players) {
                uni.setStorageSync('roomPlayers', JSON.stringify(data.players))
            }
            uni.showToast({
                title: '重新连接成功',
                icon: 'success'
            })
            setTimeout(() => {
                uni.redirectTo({
                    url: `/pages/room/room?roomId=${roomId.value.trim().toUpperCase()}&playerId=${data.player.id}`
                })
            }, 500)
        }
    })

    socketService.onAction('serverRoomAction', 'playerJoined', (data) => {
        loading.value = false
        playerId.value = data.playerId

        const targetRoomId = roomId.value.trim().toUpperCase()
        uni.setStorageSync('roomId', targetRoomId)
        uni.setStorageSync('playerId', data.playerId)
        if (data.gameState && data.gameState.players) {
            uni.setStorageSync('roomPlayers', JSON.stringify(data.gameState.players))
        }
        if (data.gameState && data.gameState.maxPlayers) {
            uni.setStorageSync('maxPlayers', data.gameState.maxPlayers)
        }

        uni.redirectTo({
            url: `/pages/room/room?roomId=${targetRoomId}&playerId=${data.playerId}`
        })
    })

    socketService.onAction('serverGameAction', 'gameStarted', (gameState) => {
        uni.redirectTo({
            url: `/pages/online-game/onlineGame?roomId=${gameState.gameId}&playerId=${playerId.value}`
        })
    })

    socketService.on('error', (data) => {
        loading.value = false
        errorMessage.value = data.message || '发生错误'
    })
}

onMounted(() => {
    setupListeners()
})

onUnmounted(() => {
    socketService.offAction('serverRoomAction')
    socketService.offAction('serverGameAction')
    socketService.off('error')
    socketService.off('connect')
    socketService.off('disconnect')
    socketService.off('connectError')
})

function goBack() {
    uni.navigateBack()
}
</script>

<style scoped>
.lobby-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 60rpx 30rpx;
}

.header {
    text-align: center;
    margin-bottom: 60rpx;
}

.title {
    display: block;
    font-size: 56rpx;
    font-weight: 800;
    color: white;
    margin-bottom: 10rpx;
}

.subtitle {
    font-size: 28rpx;
    color: rgba(255, 255, 255, 0.9);
}

.mode-tabs {
    display: flex;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 40rpx;
    padding: 8rpx;
    margin-bottom: 40rpx;
}

.tab {
    flex: 1;
    padding: 24rpx;
    border-radius: 32rpx;
    text-align: center;
    transition: all 0.3s ease;
}

.tab.active {
    background: white;
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.tab-text {
    font-size: 28rpx;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.8);
}

.tab.active .tab-text {
    color: #667eea;
}

.content-card {
    background: white;
    border-radius: 32rpx;
    padding: 40rpx;
    box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.15);
}

.input-group {
    margin-bottom: 30rpx;
}

.input-label {
    display: block;
    font-size: 26rpx;
    color: #666;
    margin-bottom: 12rpx;
}

.input-field {
    width: 100%;
    height: 88rpx;
    padding: 0 30rpx;
    background: #f5f5f5;
    border-radius: 16rpx;
    font-size: 30rpx;
    border: none;
}

.btn-create,
.btn-join {
    width: 100%;
    height: 96rpx;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 48rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.4);
    margin-top: 20rpx;
}

.btn-create:disabled,
.btn-join:disabled {
    opacity: 0.6;
}

.btn-text {
    font-size: 32rpx;
    font-weight: 700;
    color: white;
}

.room-code-box {
    margin-top: 40rpx;
    padding: 30rpx;
    background: #f8f6ff;
    border-radius: 20rpx;
    text-align: center;
}

.room-code-label {
    font-size: 24rpx;
    color: #666;
}

.room-code {
    display: block;
    font-size: 56rpx;
    font-weight: 800;
    color: #667eea;
    letter-spacing: 8rpx;
    margin: 10rpx 0;
}

.room-code-hint {
    font-size: 22rpx;
    color: #999;
}

.error-box {
    margin-top: 30rpx;
    padding: 20rpx;
    background: #fff2f2;
    border-radius: 12rpx;
    text-align: center;
}

.error-text {
    font-size: 26rpx;
    color: #e53935;
}

.back-btn {
    margin-top: 40rpx;
    text-align: center;
}

.back-text {
    font-size: 28rpx;
    color: rgba(255, 255, 255, 0.8);
    padding: 20rpx;
}

.player-count-selector {
    display: flex;
    gap: 20rpx;
    margin-top: 16rpx;
}

.count-btn {
    flex: 1;
    padding: 20rpx;
    border-radius: 16rpx;
    text-align: center;
    background: #f5f5f5;
    border: 2rpx solid #e8e8e8;
}

.count-btn.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-color: #667eea;
}

.count-btn text {
    font-size: 28rpx;
    color: #666;
    font-weight: 600;
}

.count-btn.active text {
    color: white;
}
</style>
