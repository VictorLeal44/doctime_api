from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from routes.auth import router as auth_router
from routes.citas import router as citas_router
from routes.users import router as users_router
from routes.websocket_manager import manager  # <--- Importación limpia

app = FastAPI()

@app.websocket("/ws/notifications/{usuario_id}")
async def websocket_endpoint(websocket: WebSocket, usuario_id: int):
    await manager.connect(usuario_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(usuario_id, websocket)

app.include_router(citas_router, prefix="/v1", tags=["citas"])
app.include_router(users_router, prefix="/v1", tags=["users"])
app.include_router(auth_router, prefix="/v1", tags=["auth"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
