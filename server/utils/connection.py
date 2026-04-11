# -*- coding: utf-8 -*-
"""
WebSocket连接管理器
"""

import time
from typing import Dict
from fastapi import WebSocket
from utils.logger import log_info, log_debug


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.lobby_connections: Dict[str, WebSocket] = {}
        self.user_rooms: Dict[str, str] = {}
        self.heartbeat_timestamps: Dict[str, float] = {}

    async def lobby_connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.lobby_connections[user_id] = websocket
        self.heartbeat_timestamps[id(websocket)] = time.time()
        log_info(f"Lobby client connected: {user_id}")

    def lobby_disconnect(self, user_id: str, fingerprint):
        self.lobby_connections.pop(user_id, None)
        self.heartbeat_timestamps.pop(fingerprint, None)
        self.user_rooms.pop(user_id, None)
        log_info(f"Lobby client disconnected: {user_id}")

    def set_user_room(self, user_id: str, room_id: str):
        self.user_rooms[user_id] = room_id

    async def broadcast_to_room_members(self, room_id: str, event: str, data: dict):
        disconnected = []

        if room_id in self.active_connections:
            for player_id, ws in self.active_connections[room_id].items():
                try:
                    await ws.send_json({"event": event, "data": data})
                except Exception:
                    disconnected.append(player_id)

            for player_id in disconnected:
                self.active_connections[room_id].pop(player_id, None)

        lobby_disconnected = []
        for user_id, ws in list(self.lobby_connections.items()):
            if self.user_rooms.get(user_id) == room_id:
                try:
                    await ws.send_json({"event": event, "data": data})
                except Exception:
                    lobby_disconnected.append(user_id)

        for user_id in lobby_disconnected:
            self.lobby_connections.pop(user_id, None)
            self.user_rooms.pop(user_id, None)

    async def connect(self, websocket: WebSocket, room_id: str, player_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][str(player_id)] = websocket
        self.heartbeat_timestamps[id(websocket)] = time.time()
        log_info(f"Client {player_id} connected to room {room_id}")

    def disconnect(self, room_id: str, player_id: int, fingerprint):
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(str(player_id), None)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        self.heartbeat_timestamps.pop(fingerprint, None)

        for uid in list(self.user_rooms.keys()):
            if self.user_rooms[uid] == room_id:
                self.user_rooms.pop(uid, None)

        log_info(f"Client {player_id} disconnected from room {room_id}")

    async def send_to_room(self, room_id: str, event: str, data: dict):
        if room_id in self.active_connections:
            disconnected = []
            for player_id, ws in self.active_connections[room_id].items():
                try:
                    await ws.send_json({"event": event, "data": data})
                except Exception:
                    disconnected.append(player_id)
            for player_id in disconnected:
                self.active_connections[room_id].pop(player_id, None)
                log_debug(f"Removed disconnected player {player_id} from room {room_id}")

    async def send_to_player(self, room_id: str, player_id: int, event: str, data: dict):
        if room_id in self.active_connections:
            ws = self.active_connections[room_id].get(str(player_id))
            if ws:
                try:
                    await ws.send_json({"event": event, "data": data})
                except Exception:
                    pass

    async def send_to_except_player(self, room_id: str, except_player_id: int, event: str, data: dict):
        """发送给房间内除指定玩家外的所有人"""
        if room_id in self.active_connections:
            disconnected = []
            except_player_id_str = str(except_player_id)
            for player_id, ws in self.active_connections[room_id].items():
                if player_id == except_player_id_str:
                    continue
                try:
                    await ws.send_json({"event": event, "data": data})
                except Exception:
                    disconnected.append(player_id)
            for player_id in disconnected:
                self.active_connections[room_id].pop(player_id, None)
                log_debug(f"Removed disconnected player {player_id} from room {room_id}")
