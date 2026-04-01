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

    # 房间管理 (通过 action_type 区分具体操作)
    CLIENT_ROOM_ACTION = 'clientRoomAction'

    # 战斗 (通过 action_type 区分具体操作)
    CLIENT_BATTLE_ACTION = 'clientBattleAction'

    # 统一游戏行动 (通过 actionType 区分具体操作)
    CLIENT_GAME_ACTION = 'clientGameAction'


# =============================================================================
# 客户端 → 服务端 行动类型
# =============================================================================

class ClientRoomActionTypes:
    """clientRoomAction 事件中的 action_type 取值"""
    CREATE_ROOM = 'createRoom'
    JOIN_ROOM = 'joinRoom'
    LEAVE_ROOM = 'leaveRoom'
    SET_READY = 'setReady'


class ClientBattleActionTypes:
    """clientBattleAction 事件中的 action_type 取值"""
    BATTLE_START = 'battleStart'
    LOBSTER_SELECTED = 'lobsterSelected'
    SPECTATOR_BET = 'spectatorBet'
    NO_LOBSTER_FORFEIT = 'noLobsterForfeit'


class GameActionTypes:
    """clientGameAction 事件中的 actionType 取值"""

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

    # 房间管理 (通过 actionType 区分具体操作)
    SERVER_ROOM_ACTION = 'serverRoomAction'

    # 游戏流程 (通过 actionType 区分具体操作)
    SERVER_GAME_ACTION = 'serverGameAction'

    # 战斗 (通过 actionType 区分具体操作)
    SERVER_BATTLE_ACTION = 'serverBattleAction'

    # 结算阶段 (通过 actionType 区分具体操作)
    SERVER_AREA_ACTION = 'serverAreaAction'

    # 资源 (独立事件)
    PLAYER_RESOURCE_UPDATE = 'playerResourceUpdate'

    # 错误 (独立事件)
    ERROR = 'error'


# =============================================================================
# 服务端 → 客户端 行动类型
# =============================================================================

class ServerRoomActionTypes:
    """serverRoomAction 事件中的 actionType 取值"""
    ROOM_CREATED = 'roomCreated'
    PLAYER_JOINED = 'playerJoined'
    PLAYER_RECONNECTED = 'playerReconnected'
    PLAYER_STATUS_CHANGE = 'playerStatusChange'
    PLAYER_LEFT = 'playerLeft'
    ROOM_STATE_UPDATE = 'roomStateUpdate'
    PLAYER_READY = 'playerReady'


class ServerGameActionTypes:
    """serverGameAction 事件中的 actionType 取值"""
    GAME_STARTED = 'gameStarted'
    GAME_ENDED = 'gameEnded'
    ROUND_STARTED = 'roundStarted'
    GAME_STATE_UPDATE = 'gameStateUpdate'
    GAME_ACTION = 'gameAction'


class ServerBattleActionTypes:
    """serverBattleAction 事件中的 actionType 取值"""
    BATTLE_START = 'battleStart'
    BATTLE_ACTION = 'battleAction'
    BATTLE_ENDED = 'battleEnded'
    LOBSTER_SELECTED = 'lobsterSelected'
    ARENA_BETTING_START = 'arenaBettingStart'
    ARENA_BETTING_COMPLETE = 'arenaBettingComplete'
    BET_RESULT = 'betResult'


class ServerAreaActionTypes:
    """serverAreaAction 事件中的 actionType 取值"""
    AREA_WAITING_UI = 'areaWaitingUI'
    AREA_SETTLEMENT_START = 'areaSettlementStart'
    AREA_ACTION_COMPLETE = 'areaActionComplete'
    SETTLEMENT_COMPLETE = 'settlementComplete'
