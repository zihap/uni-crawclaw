#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙争虾斗 - 服务端游戏逻辑服务器
"""

import os
import sys
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils.connection import ConnectionManager
from utils.constants import AREAS
from services.game import broadcast_room_state
from controllers.websocket import handle_lobby_websocket, handle_game_websocket

app = FastAPI(
    title="龙争虾斗游戏服务器",
    description="回合制工人放置类桌游的后端服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rooms: Dict[str, dict] = {}
manager = ConnectionManager()


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """获取房间信息"""
    game_state = rooms.get(room_id)
    if not game_state:
        raise HTTPException(status_code=404, message="房间不存在")

    return {
        'success': True,
        'room': {
            'players': game_state['players'],
            'gameStarted': game_state['status'] == 'playing',
            'status': game_state['status'],
            'maxPlayers': game_state.get('maxPlayers', 4)
        }
    }


@app.websocket("/ws/lobby")
async def websocket_lobby_endpoint(websocket: WebSocket):
    """大厅WebSocket端点"""
    await handle_lobby_websocket(websocket, rooms, manager)


@app.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: int):
    """游戏房间WebSocket端点"""
    await handle_game_websocket(websocket, room_id, player_id, rooms, manager)


if __name__ == '__main__':
    import uvicorn

    port = int(os.environ.get('PORT', 3100))
    uvicorn.run(app, host='0.0.0.0', port=port)
