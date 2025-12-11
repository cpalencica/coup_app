from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # map game_id -> list[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str):
        await websocket.accept()
        self.active_connections.setdefault(game_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, game_id: str):
        conns = self.active_connections.get(game_id)
        if not conns:
            return
        try:
            conns.remove(websocket)
        except ValueError:
            pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, game_id: str):
        conns = self.active_connections.get(game_id, [])
        for connection in list(conns):
            try:
                await connection.send_text(message)
            except Exception:
                # ignore send errors for now
                pass
