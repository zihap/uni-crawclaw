/**
 * WebSocket服务器地址
 * 开发环境指向localhost，生产环境应替换为实际服务器地址
 */
const WS_URL = 'ws://localhost:3100'

/**
 * 心跳间隔时间（毫秒）
 * 客户端每20秒向服务器发送一次心跳，以保持连接活跃
 * 服务器可据此检测客户端是否在线
 */
const HEARTBEAT_INTERVAL = 20000

/**
 * 重连延迟时间（毫秒）
 * 断开连接后，等待3秒再尝试重新连接
 */
const RECONNECT_DELAY = 3000

/**
 * 最大重连次数
 * 连续重连失败5次后，停止自动重连并触发reconnectFailed事件
 */
const MAX_RECONNECT_ATTEMPTS = 5

// =============================================================================
// WebSocket服务类
// =============================================================================

/**
 * WebSocketService - WebSocket通信服务类
 *
 * 核心功能:
 * 1. 连接管理：建立/断开WebSocket连接
 * 2. 消息发送：向服务器发送JSON格式消息
 * 3. 消息接收：通过事件订阅机制分发服务器消息
 * 4. 心跳保活：定期发送心跳检测连接状态
 * 5. 自动重连：连接断开时自动尝试重新连接
 * 6. 消息缓存：断线期间的消息会被缓存
 *
 * 状态说明:
 * - _connected: 是否已连接（只读属性）
 * - connecting: 是否正在连接
 * - isManualClose: 是否手动关闭（手动关闭时不触发自动重连）
 */
class WebSocketService {
    /**
     * 构造函数
     *
     * 初始化所有内部状态：
     * - socket: WebSocket实例
     * - listeners: 事件监听器字典 { eventName: [callback1, callback2, ...] }
     * - heartbeatTimer: 心跳定时器ID
     * - reconnectTimer: 重连定时器ID
     * - reconnectAttempts: 当前重连尝试次数
     * - pendingEvents: 离线期间缓存的消息队列
     */
    constructor() {
        this.socket = null // WebSocket实例
        this._connected = false // 连接状态标志
        this.connecting = false // 是否正在连接
        this.listeners = {} // 事件监听器 { eventName: [callbacks] }
        this.actionListeners = {} // 聚合事件监听器 { eventName: { actionType: [callbacks] } }
        this.heartbeatTimer = null // 心跳定时器
        this.reconnectTimer = null // 重连定时器
        this.reconnectAttempts = 0 // 重连尝试次数
        this.currentRoomId = null // 当前房间ID
        this.currentPlayerId = null // 当前玩家ID
        this.pendingEvents = [] // 离线消息队列
        this.userId = null // 用户唯一ID
        this.isManualClose = false // 是否手动关闭
        this._wsUrl = null // 内部存储的WebSocket URL
    }

    /**
     * 连接状态获取器
     * @returns {boolean} 当前是否已连接
     */
    get connected() {
        return this._connected
    }

    /**
     * 设置用户ID
     * @param {string} uid - 用户唯一标识符
     *
     * 用途:
     * - 标识用户身份
     * - 用于断线重连时的用户识别
     */
    setUserId(uid) {
        this.userId = uid
    }

    /**
     * 连接到WebSocket服务器
     *
     * @param {string} roomId - 房间ID（可选）
     * @param {number|null} playerId - 玩家ID（可选）
     *
     * 连接逻辑:
     * 1. 如果正在连接中，直接返回
     * 2. 如果已连接且URL相同，不重复连接
     * 3. 如果已连接但URL不同，先断开再连接
     * 4. 根据参数决定连接大厅还是游戏房间
     *
     * URL规则:
     * - 大厅连接: ws://localhost:3100/ws/lobby
     * - 游戏房间: ws://localhost:3100/ws/{roomId}/{playerId}
     *
     * 潜在风险:
     * - 服务器不可用时会导致连接失败
     * - 需要处理网络异常情况
     */
    connect(roomId, playerId) {
        const self = this

        // 防止重复连接
        if (this.connecting) {
            return
        }

        // 已连接时检查URL是否相同
        if (this._connected && this.socket) {
            const oldUrl = this._wsUrl
            const newUrl = WS_URL + '/ws/' + roomId + '/' + playerId
            if (oldUrl !== newUrl) {
                this.disconnect()
            } else {
                return
            }
        }

        // 根据参数决定连接URL
        this._wsUrl = roomId && playerId !== null ? WS_URL + '/ws/' + roomId + '/' + playerId : WS_URL + '/ws/lobby'
        this.isManualClose = false
        this.connecting = true

        const wsUrl = this._wsUrl

        console.log('Connecting to WebSocket:', wsUrl, 'playerId:', playerId, 'playerId type:', typeof playerId)

        // 使用微信小程序API连接WebSocket
        this.socket = wx.connectSocket({
            url: wsUrl,
            success: function () {},
            fail: function (err) {
                console.error('WebSocket connect failed:', err)
                self.connecting = false
                self._emit('connectError', { error: err.errMsg })
                self._scheduleReconnect()
            }
        })

        // 注册事件回调
        this.socket.onOpen(function () {
            self._connected = true
            self.connecting = false
            self.reconnectAttempts = 0
            self._emit('connect', { roomId: self.currentRoomId, playerId: self.currentPlayerId })
            self._startHeartbeat()
            self._flushPendingEvents()
        })

        this.socket.onError(function (err) {
            console.error('WebSocket error:', err)
            self._connected = false
            self.connecting = false
            self._emit('connectError', { error: err.errMsg || 'Unknown error' })
        })

        this.socket.onClose(function (res) {
            self._connected = false
            self.connecting = false
            self._stopHeartbeat()
            self._emit('disconnect', { code: res.code, reason: res.reason })

            // 非手动关闭时触发自动重连
            if (!self.isManualClose) {
                self._scheduleReconnect()
            }
        })

        this.socket.onMessage(function (res) {
            try {
                const message = JSON.parse(res.data)
                const event = message.event
                const data = message.data
                console.log('WebSocket message:', event, data)

                // 聚合事件分发: 检查是否为 serverRoomAction / serverGameAction / serverBattleAction / serverAreaAction
                if (event && data && data.actionType) {
                    const actionCbs = self.actionListeners[event]
                    if (actionCbs) {
                        const typeCbs = actionCbs[data.actionType]
                        if (typeCbs && typeCbs.length > 0) {
                            typeCbs.forEach(function (cb) {
                                cb(data)
                            })
                        }
                    }
                }

                self._emit(event, data)
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e)
            }
        })
    }

    /**
     * 启动心跳定时器
     *
     * 心跳机制:
     * - 每隔HEARTBEAT_INTERVAL毫秒发送一次心跳消息
     * - 心跳消息包含时间戳和房间ID
     * - 用于检测连接是否仍然活跃
     *
     * 设计考量:
     * - 心跳间隔不宜过短（增加服务器负担）
     * - 心跳间隔不宜过长（无法及时检测断线）
     */
    _startHeartbeat() {
        const self = this
        this._stopHeartbeat()
        this.heartbeatTimer = setInterval(function () {
            if (self._connected) {
                self._send('heartbeat', { timestamp: Date.now(), roomId: self.currentRoomId })
            }
        }, HEARTBEAT_INTERVAL)
    }

    /**
     * 停止心跳定时器
     */
    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer)
            this.heartbeatTimer = null
        }
    }

    /**
     * 安排自动重连
     *
     * 重连策略:
     * 1. 检查是否超过最大重连次数
     * 2. 清除之前的重连定时器
     * 3. 增加重连计数
     * 4. 触发reconnecting事件（通知UI显示重连状态）
     * 5. 等待RECONNECT_DELAY后尝试重新连接
     *
     * 注意事项:
     * - 重连时使用之前保存的roomId和playerId
     * - 如果超过最大重连次数，触发reconnectFailed事件
     */
    _scheduleReconnect() {
        const self = this

        // 超过最大重连次数，停止重连
        if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            this._emit('reconnectFailed', {})
            return
        }

        this._clearReconnectTimer()
        this.reconnectAttempts++

        // 通知UI正在重连
        this._emit('reconnecting', { attemptNumber: this.reconnectAttempts })

        // 延迟重连
        this.reconnectTimer = setTimeout(function () {
            self.connect(self.currentRoomId, self.currentPlayerId)
        }, RECONNECT_DELAY)
    }

    /**
     * 清除重连定时器
     */
    _clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer)
            this.reconnectTimer = null
        }
    }

    /**
     * 发送离线期间缓存的消息
     *
     * 当重新连接后，将离线期间缓存的消息按顺序发送
     * 使用shift()逐个取出并发送
     *
     * 设计考量:
     * - 离线期间用户操作不丢失
     * - 消息按顺序发送，保证一致性
     */
    _flushPendingEvents() {
        const self = this
        while (this.pendingEvents.length > 0) {
            const event = this.pendingEvents.shift()
            this._send(event.name, event.data)
        }
    }

    /**
     * 发送消息到服务器
     *
     * @param {string} event - 事件名称
     * @param {object} data - 消息数据
     *
     * 发送逻辑:
     * 1. 如果已连接，序列化为JSON并发送
     * 2. 如果未连接，将消息加入待发送队列
     *
     * 消息格式:
     * ```json
     * { "event": "事件名", "data": { ... } }
     * ```
     */
    _send(event, data) {
        if (this._connected && this.socket) {
            const message = JSON.stringify({ event: event, data: data })
            try {
                this.socket.send({
                    data: message,
                    success: function () {},
                    fail: function (err) {
                        console.error('WebSocket send failed:', err)
                    }
                })
            } catch (e) {
                console.error('WebSocket send exception:', e)
            }
        } else {
            // 离线时缓存消息
            this.pendingEvents.push({ name: event, data: data })
        }
    }

    /**
     * 设置房间上下文
     *
     * @param {string} roomId - 房间ID
     * @param {number} playerId - 玩家ID
     *
     * 用途:
     * - 保存当前房间信息
     * - 用于重连时恢复连接
     */
    setRoomContext(roomId, playerId) {
        this.currentRoomId = roomId
        this.currentPlayerId = playerId
    }

    /**
     * 清除房间上下文
     *
     * 用途:
     * - 离开房间时调用
     * - 清空房间ID、玩家ID和待发送消息
     */
    clearRoomContext() {
        this.currentRoomId = null
        this.currentPlayerId = null
        this.pendingEvents = []
    }

    /**
     * 触发事件
     *
     * @param {string} event - 事件名称
     * @param {object} data - 事件数据
     *
     * 内部方法，被所有发送消息的事件调用
     * 将事件分发给所有订阅的回调函数
     */
    _emit(event, data) {
        const cbs = this.listeners[event]
        if (cbs) {
            if (Array.isArray(cbs)) {
                cbs.forEach(function (cb) {
                    cb(data)
                })
            } else {
                cbs(data)
            }
        }
    }

    /**
     * 订阅事件
     *
     * @param {string} event - 事件名称
     * @param {function} callback - 回调函数
     *
     * 使用示例:
     * ```javascript
     * socketService.on('gameStarted', (data) => {
     *   // 处理游戏开始事件
     * })
     * ```
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = []
        }
        this.listeners[event].push(callback)
    }

    /**
     * 取消订阅事件
     *
     * @param {string} event - 事件名称
     * @param {function} callback - 回调函数（可选）
     *
     * 说明:
     * - 如果提供callback，只移除该回调
     * - 如果不提供callback，移除该事件的所有回调
     */
    off(event, callback) {
        if (this.listeners[event]) {
            if (callback) {
                this.listeners[event] = this.listeners[event].filter(function (cb) {
                    return cb !== callback
                })
            } else {
                delete this.listeners[event]
            }
        }
    }

    /**
     * 订阅聚合事件的特定 actionType
     *
     * @param {string} event - 聚合事件名称 (如 serverRoomAction)
     * @param {string} actionType - 行动类型 (如 roomCreated)
     * @param {function} callback - 回调函数
     *
     * 使用示例:
     * ```javascript
     * socketService.onAction('serverRoomAction', 'roomCreated', (data) => {
     *   // 处理房间创建
     * })
     * ```
     */
    onAction(event, actionType, callback) {
        if (!this.actionListeners[event]) {
            this.actionListeners[event] = {}
        }
        if (!this.actionListeners[event][actionType]) {
            this.actionListeners[event][actionType] = []
        }
        this.actionListeners[event][actionType].push(callback)
    }

    /**
     * 取消订阅聚合事件的特定 actionType
     *
     * @param {string} event - 聚合事件名称
     * @param {string} actionType - 行动类型（可选，不提供则移除该事件所有 actionType 监听）
     */
    offAction(event, actionType) {
        if (!this.actionListeners[event]) return
        if (actionType) {
            delete this.actionListeners[event][actionType]
        } else {
            delete this.actionListeners[event]
        }
    }

    /**
     * 断开WebSocket连接
     *
     * 断开逻辑:
     * 1. 设置手动关闭标志（阻止自动重连）
     * 2. 清除心跳和重连定时器
     * 3. 清空待发送消息队列
     * 4. 关闭WebSocket连接
     * 5. 重置所有状态
     */
    disconnect() {
        this.isManualClose = true
        this._clearReconnectTimer()
        this._stopHeartbeat()
        this.pendingEvents = []

        if (this.socket) {
            this.socket.close({
                success: function () {},
                fail: function (err) {
                    console.error('WebSocket close failed:', err)
                }
            })
            this.socket = null
        }

        this._connected = false
        this.connecting = false
        this.currentRoomId = null
        this.currentPlayerId = null
        this._wsUrl = null
    }

    // ===========================================================================
    // 房间管理方法
    // ===========================================================================

    /**
     * 创建房间
     *
     * @param {string} playerName - 玩家名称
     * @param {string} userId - 用户唯一ID
     * @param {number} maxPlayers - 最大玩家数（默认4人）
     *
     * 发送事件: createRoom
     *
     * 响应处理:
     * - roomCreated: 房间创建成功，返回roomId和playerId
     * - error: 创建失败，返回错误信息
     */
    createRoom(playerName, userId, maxPlayers) {
        maxPlayers = maxPlayers || 4
        this.userId = userId
        this._send('clientRoomAction', {
            action_type: 'createRoom',
            playerName: playerName,
            userId: userId,
            maxPlayers: maxPlayers
        })
    }

    /**
     * 加入房间
     *
     * @param {string} roomId - 房间ID
     * @param {string} playerName - 玩家名称
     * @param {string} userId - 用户唯一ID
     *
     * 发送事件: joinRoom
     *
     * 响应处理:
     * - playerJoined: 加入成功
     * - playerReconnected: 断线重连
     * - error: 加入失败（房间不存在/已满/游戏已开始）
     */
    joinRoom(roomId, playerName, userId) {
        this.userId = userId
        this._send('clientRoomAction', {
            action_type: 'joinRoom',
            roomId: roomId,
            playerName: playerName,
            userId: userId
        })
    }

    /**
     * 离开房间
     *
     * 发送事件: leaveRoom
     *
     * 清理操作:
     * - 发送离开消息
     * - 清空房间上下文
     */
    leaveRoom() {
        if (this.currentRoomId && this.currentPlayerId !== null) {
            this._send('clientRoomAction', {
                action_type: 'leaveRoom',
                roomId: this.currentRoomId,
                playerId: this.currentPlayerId
            })
        }
        this.clearRoomContext()
    }

    /**
     * 设置准备状态
     *
     * @param {boolean} ready - 是否准备
     * @param {boolean} forceStart - 是否强制开始（房主专用）
     *
     * 发送事件: setReady
     *
     * 游戏开始条件:
     * - 所有玩家都准备（ready=true）
     * - 或房主强制开始（forceStart=true）
     */
    setReady(ready, forceStart) {
        forceStart = forceStart || false
        if (this.currentRoomId && this.currentPlayerId !== null) {
            this._send('clientRoomAction', {
                action_type: 'setReady',
                roomId: this.currentRoomId,
                playerId: this.currentPlayerId,
                ready: ready,
                forceStart: forceStart
            })
        }
    }

    clientBattleAction(actionType, battleData, senderId) {
        if (this.currentRoomId && this.currentPlayerId !== null) {
            this._send('clientBattleAction', {
                action_type: actionType,
                roomId: this.currentRoomId,
                playerId: this.currentPlayerId,
                senderId: senderId,
                battleData: battleData
            })
        }
    }

    clientGameAction(actionType, payload) {
        if (this.currentRoomId && this.currentPlayerId !== null) {
            this._send('clientGameAction', {
                actionType: actionType,
                roomId: this.currentRoomId,
                playerId: this.currentPlayerId,
                payload: payload || {}
            })
        }
    }
}

/**
 * WebSocket服务单例实例
 *
 * 使用方式:
 * ```javascript
 * import { socketService } from '@/services/socket'
 * // 或
 * import socketService from '@/services/socket'
 * ```
 */
const socketService = new WebSocketService()

export { socketService }
export default { socketService }
