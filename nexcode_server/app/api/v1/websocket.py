from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.collaboration_service import collaboration_manager
from app.core.dependencies import get_current_user_ws

router = APIRouter()

@router.websocket("/documents/{document_id}/collaborate")
async def websocket_collaborate(
    websocket: WebSocket,
    document_id: int,
    user_id: int = Depends(get_current_user_ws)
):
    """文档协作WebSocket端点"""
    await collaboration_manager.connect(websocket, document_id, user_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'operation':
                await collaboration_manager.handle_operation(
                    document_id, user_id, message['operation']
                )
            elif message['type'] == 'cursor':
                await collaboration_manager.broadcast_cursor_position(
                    document_id, user_id, message['position']
                )
                
    except WebSocketDisconnect:
        await collaboration_manager.disconnect(document_id, user_id)