from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, usuario_id: int, websocket: WebSocket):
        await websocket.accept()
        if usuario_id not in self.active_connections:
            self.active_connections[usuario_id] = []
        self.active_connections[usuario_id].append(websocket)

    def disconnect(self, usuario_id: int, websocket: WebSocket):
        if usuario_id in self.active_connections:
            self.active_connections[usuario_id].remove(websocket)
            if not self.active_connections[usuario_id]:
                del self.active_connections[usuario_id]

    async def send_to_user(self, usuario_id: int, message: dict):
        if usuario_id in self.active_connections:
            for connection in self.active_connections[usuario_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

# Instancia única global que compartirán los archivos
manager = ConnectionManager()
