# -*- coding: utf-8 -*-
"""
WebSocket 事件常量定义
统一管理所有客户端→服务端和服务端→客户端的事件名
"""


# =============================================================================
# 客户端 → 服务端事件
# =============================================================================

class ClientEvents:
    """客户端发送给服务端的事件名"""

    # 连接层
    HEARTBEAT = 'heartbeat'

    # 房间管理
    CREATE_ROOM = 'createRoom'
    JOIN_ROOM = 'joinRoom'
    LEAVE_ROOM = 'leaveRoom'
    SET_READY = 'setReady'

    # 统一游戏行动 (通过 actionType 区分具体操作)
    GAME_ACTION = 'gameAction'

    # 战斗 (数据量大、实时性要求高，保留独立事件)
    BATTLE_START = 'battleStart'
    BATTLE_ACTION = 'battleAction'
    LOBSTER_SELECTED = 'lobsterSelected'
    SPECTATOR_BET = 'spectatorBet'
    NO_LOBSTER_FORFEIT = 'noLobsterForfeit'


# =============================================================================
# 游戏操作类型 (gameAction 的 actionType)
# =============================================================================

class GameActionTypes:
    """gameAction 事件中的 actionType 取值"""

    USE_SEAWEED = 'useSeaweed'
    PLACE_HEADMAN = 'placeHeadman'
    NEXT_PLAYER = 'nextPlayer'
    NEXT_AREA = 'nextArea'
    EXCHANGE_SIGNALS = 'exchangeSignals'
    BUY_ITEM = 'buyItem'
    SELL_ITEM = 'sellItem'
    CULTIVATE_LOBSTER = 'cultivateLobster'
    SUBMIT_TRIBUTE = 'submitTribute'
    DOWNTOWN_ACTION = 'executeDowntownAction'
    AREA_ACTION = 'areaAction'


# =============================================================================
# 服务端 → 客户端事件
# =============================================================================

class ServerEvents:
    """服务端发送给客户端的事件名"""

    # 连接层
    HEARTBEAT_ACK = 'heartbeatAck'
    PONG = 'pong'

    # 房间管理
    ROOM_CREATED = 'roomCreated'
    PLAYER_JOINED = 'playerJoined'
    PLAYER_RECONNECTED = 'playerReconnected'
    PLAYER_STATUS_CHANGE = 'playerStatusChange'
    PLAYER_LEFT = 'playerLeft'
    ROOM_STATE_UPDATE = 'roomStateUpdate'
    PLAYER_READY = 'playerReady'

    # 游戏流程
    GAME_STARTED = 'gameStarted'
    GAME_ENDED = 'gameEnded'
    ROUND_STARTED = 'roundStarted'
    GAME_STATE_UPDATE = 'gameStateUpdate'
    AREA_SETTLED = 'areaSettled'

    # 战斗
    BATTLE_START = 'battleStart'
    BATTLE_ACTION = 'battleAction'
    BATTLE_ENDED = 'battleEnded'
    LOBSTER_SELECTED = 'lobsterSelected'
    ARENA_BETTING_START = 'arenaBettingStart'
    ARENA_BETTING_COMPLETE = 'arenaBettingComplete'
    BET_RESULT = 'betResult'

    # 结算阶段
    AREA_SETTLEMENT_START = 'areaSettlementStart'
    AREA_WAITING_UI = 'areaWaitingUI'
    AREA_ACTION_COMPLETE = 'areaActionComplete'
    SETTLEMENT_COMPLETE = 'settlementComplete'

    # 资源
    PLAYER_RESOURCE_UPDATE = 'playerResourceUpdate'
    GAME_ACTION = 'gameAction'

    # 错误
    ERROR = 'error'
