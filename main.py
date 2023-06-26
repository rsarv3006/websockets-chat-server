import json
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


def build_message_json(message: str, client_id: int, message_uuid: uuid.UUID):
    return json.dumps({
        "type": "message",
        "id": str(message_uuid),
        "data": {
            "message": message,
            "client_id": client_id
        }
    })


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    print("Attempted Connection - ", client_id)
    await manager.connect(websocket)
    message_uuid = uuid.uuid4()
    await manager.broadcast(build_message_json(f"Client #{client_id} joined the chat", client_id, message_uuid))
    try:
        while True:
            data = await websocket.receive_text()
            message_uuid = uuid.uuid4()
            # await manager.send_personal_message(build_message_json(data, client_id, message_uuid), websocket)
            await manager.broadcast(build_message_json(data, client_id, message_uuid))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message_uuid = uuid.uuid4()
        await manager.broadcast(build_message_json(f"Client #{client_id} left the chat", client_id, message_uuid))
