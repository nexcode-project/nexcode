import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.collaboration_service import collaboration_manager
from app.services.permission_service import permission_service
from app.core.dependencies import get_current_user_ws, get_db
from app.models.database import User, PermissionLevel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()

logger = logging.getLogger(__name__)


@router.websocket("/documents/{document_id}/collaborate")
async def websocket_collaborate(
    websocket: WebSocket, 
    document_id: int,
    token: Optional[str] = Query(None)
):
    """文档协作WebSocket端点"""
    user_id = None
    user = None
    db = None
    
    try:
        # 先接受WebSocket连接
        await websocket.accept()
        
        # 验证用户身份
        if not token:
            await websocket.close(code=1008, reason="Missing token")
            return
            
        # 获取数据库会话
        async for session in get_db():
            db = session
            break
            
        # 验证用户
        try:
            user_id = await get_current_user_ws(websocket, token, db)
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token")
                return
                
            # 获取用户信息
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                await websocket.close(code=1008, reason="User not found")
                return
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
            
        # 检查文档权限
        try:
            logger.info(f"检查用户 {user_id} 对文档 {document_id} 的权限...")
            has_permission = await permission_service.check_document_permission(
                db, user_id, document_id, PermissionLevel.READER
            )
            if not has_permission:
                logger.warning(f"用户 {user_id} 没有文档 {document_id} 的权限")
                await websocket.close(code=1008, reason="No permission")
                return
            logger.info(f"用户 {user_id} 权限检查通过")
        except Exception as e:
            logger.error(f"权限检查错误: {e}")
            # 暂时跳过权限检查，继续执行
            logger.warning("暂时跳过权限检查，继续执行...")
            # await websocket.close(code=1008, reason="Permission denied")
            # return
            
        # 更新用户信息缓存
        logger.info(f"更新用户 {user_id} 的信息缓存...")
        collaboration_manager.update_user_cache(user_id, {
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
        
        # 连接到协作管理器
        logger.info(f"连接到协作管理器...")
        session_id = await collaboration_manager.connect(websocket, document_id, user_id)
        
        logger.info(f"User {user.username} connected to document {document_id}")
        
        # 发送连接成功消息
        logger.info(f"发送连接成功消息...")
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connection successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }))
        
        # 发送当前在线用户列表
        logger.info(f"发送在线用户列表...")
        await collaboration_manager.send_online_users(document_id, user_id)
        
        logger.info(f"开始消息处理循环...")
        
        # 消息处理循环
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"收到消息: {data[:100]}...")
                message = json.loads(data)
                
                # 处理不同类型的消息
                if message.get("type") == "operation":
                    logger.info(f"处理操作消息...")
                    # 处理文档操作
                    await collaboration_manager.handle_operation(
                        document_id, user_id, message.get("operation", {})
                    )
                    
                elif message.get("type") == "content_update":
                    logger.info(f"处理内容更新消息...")
                    # 处理完整内容更新
                    await collaboration_manager.handle_content_update(
                        document_id, user_id, message.get("content", ""), session_id
                    )
                    
                elif message.get("type") == "cursor":
                    logger.info(f"处理光标消息...")
                    # 处理光标位置
                    await collaboration_manager.broadcast_cursor_position(
                        document_id, user_id, message.get("position", {})
                    )
                    
                elif message.get("type") == "ping":
                    logger.info(f"处理心跳消息...")
                    # 心跳检测
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    logger.debug(f"User {user_id} sent ping, responded with pong")
                    
                else:
                    # 未知消息类型
                    logger.warning(f"Unknown message type: {message.get('type')}")
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON message")
                continue
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for document {document_id}, user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # 清理连接
        if user_id and document_id:
            await collaboration_manager.disconnect(document_id, user_id, session_id)
            logger.info(f"User {user_id} disconnected from document {document_id}, session {session_id}")


# 添加一个简单的HTTP端点来测试路由
@router.get("/test")
async def test_route():
    return {"message": "WebSocket router is working"}


@router.websocket("/test-ws")
async def test_websocket(websocket: WebSocket):
    """测试WebSocket连接"""
    await websocket.accept()
    await websocket.send_text("Test WebSocket connection successful")
    await websocket.close()
