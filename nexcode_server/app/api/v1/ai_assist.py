from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

from app.core.dependencies import get_db, get_current_user
from app.core.llm_client import call_llm_api
from app.models.database import User
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class AIAssistRequest(BaseModel):
    message: str
    documentContent: str
    conversationHistory: List[ChatMessage]
    templateId: Optional[int] = None


class AIAssistResponse(BaseModel):
    response: str


class AITemplate(BaseModel):
    id: int
    name: str
    description: str
    system_prompt: str
    user_prompt: str
    category: str
    is_active: bool
    created_at: str
    updated_at: str


class AITemplateCreate(BaseModel):
    name: str
    description: str
    system_prompt: str
    user_prompt: str
    category: str


class AITemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


# 临时存储模板数据（后续应该存储到数据库）
TEMP_TEMPLATES = [
    {
        "id": 1,
        "name": "用户故事生成",
        "description": "根据功能需求生成标准用户故事",
        "category": "用户故事",
        "system_prompt": "你是一个产品经理专家，擅长编写清晰、具体的用户故事。请根据用户提供的功能需求，生成符合INVEST原则的用户故事。格式应包含：作为[角色]，我希望[功能]，以便[价值]。同时提供验收标准。",
        "user_prompt": "请为以下功能需求生成用户故事：\n\n{document}\n\n请包含：\n1. 用户故事描述\n2. 验收标准\n3. 优先级建议",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    },
    {
        "id": 2,
        "name": "需求分析",
        "description": "对文档内容进行需求分析和整理",
        "category": "需求分析",
        "system_prompt": "你是一个业务分析师，擅长分析和整理业务需求。请对用户提供的内容进行深入分析，识别功能需求、非功能需求、约束条件等。",
        "user_prompt": "请对以下内容进行需求分析：\n\n{document}\n\n请提供：\n1. 功能需求列表\n2. 非功能需求\n3. 约束条件\n4. 风险评估\n5. 建议",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    },
    {
        "id": 3,
        "name": "技术文档优化",
        "description": "优化技术文档的结构和内容",
        "category": "技术文档",
        "system_prompt": "你是一个技术写作专家，擅长编写清晰、准确的技术文档。请帮助优化文档结构，提高可读性和准确性。",
        "user_prompt": "请优化以下技术文档：\n\n{document}\n\n请改进：\n1. 文档结构\n2. 内容准确性\n3. 可读性\n4. 添加必要的示例",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
]


def get_template_by_id(template_id: int) -> Optional[dict]:
    """根据ID获取模板"""
    for template in TEMP_TEMPLATES:
        if template["id"] == template_id:
            return template
    return None


def build_messages(request: AIAssistRequest, template: Optional[dict] = None) -> List[dict]:
    """构建发送给LLM的消息列表"""
    messages = []
    
    # 添加系统消息
    if template and template.get("system_prompt"):
        messages.append({
            "role": "system",
            "content": template["system_prompt"]
        })
    else:
        # 默认系统消息
        messages.append({
            "role": "system",
            "content": "你是一个专业的写作助手，能够帮助用户改善文档质量、提供写作建议。请提供清晰、有用的建议。"
        })
    
    # 添加对话历史
    for msg in request.conversationHistory[:-1]:  # 排除最后一条用户消息，因为我们会重新构建
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # 构建最终的用户消息
    if template and template.get("user_prompt"):
        # 使用模板的用户提示，替换{document}占位符
        user_content = template["user_prompt"].replace("{document}", request.documentContent or "")
        # 如果用户有额外的消息，附加到模板后面
        if request.message.strip():
            user_content += f"\n\n用户补充：{request.message}"
    else:
        # 直接使用用户消息
        user_content = request.message
        if request.documentContent:
            user_content += f"\n\n当前文档内容：\n{request.documentContent}"
    
    messages.append({
        "role": "user",
        "content": user_content
    })
    
    return messages


@router.post("/assist", response_model=AIAssistResponse)
async def ai_assist(
    request: AIAssistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI助手接口"""
    try:
        logger.info(f"AI assist request from user {current_user.id}")
        
        # 获取模板（如果指定了templateId）
        template = None
        if request.templateId:
            template = get_template_by_id(request.templateId)
            if not template:
                raise HTTPException(status_code=404, detail="AI模板不存在")
            if not template.get("is_active", True):
                raise HTTPException(status_code=400, detail="AI模板已禁用")
        
        # 构建消息
        messages = build_messages(request, template)
        
        # 提取系统消息和用户消息
        system_content = ""
        user_content = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "user":
                user_content = msg["content"]
        
        # 如果没有找到用户消息，使用最后一条消息
        if not user_content and messages:
            user_content = messages[-1]["content"]
        
        # 调用LLM
        ai_response = call_llm_api(
            system_content=system_content or "你是一个专业的写作助手",
            user_content=user_content
        )
        
        logger.info(f"AI assist completed for user {current_user.id}")
        
        return AIAssistResponse(response=ai_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI assist error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI服务暂时不可用")


@router.get("/templates", response_model=List[AITemplate])
async def get_ai_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取AI模板列表"""
    try:
        # 只返回激活的模板
        active_templates = [t for t in TEMP_TEMPLATES if t.get("is_active", True)]
        return active_templates
    except Exception as e:
        logger.error(f"Get AI templates error: {str(e)}")
        raise HTTPException(status_code=500, detail="获取模板失败")


@router.post("/templates", response_model=AITemplate)
async def create_ai_template(
    template: AITemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建AI模板（管理员功能）"""
    try:
        # 检查用户权限（这里应该检查是否为管理员）
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 生成新ID
        new_id = max([t["id"] for t in TEMP_TEMPLATES], default=0) + 1
        
        new_template = {
            "id": new_id,
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt": template.user_prompt,
            "category": template.category,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        TEMP_TEMPLATES.append(new_template)
        
        return new_template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create AI template error: {str(e)}")
        raise HTTPException(status_code=500, detail="创建模板失败")


@router.put("/templates/{template_id}", response_model=AITemplate)
async def update_ai_template(
    template_id: int,
    updates: AITemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新AI模板（管理员功能）"""
    try:
        # 检查用户权限
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 查找模板
        template = None
        for i, t in enumerate(TEMP_TEMPLATES):
            if t["id"] == template_id:
                template = t
                template_index = i
                break
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 更新模板
        update_data = updates.dict(exclude_unset=True)
        for key, value in update_data.items():
            template[key] = value
        
        template["updated_at"] = "2024-01-01T00:00:00"  # 实际应该是当前时间
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update AI template error: {str(e)}")
        raise HTTPException(status_code=500, detail="更新模板失败")


@router.delete("/templates/{template_id}")
async def delete_ai_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除AI模板（管理员功能）"""
    try:
        # 检查用户权限
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 查找并删除模板
        for i, t in enumerate(TEMP_TEMPLATES):
            if t["id"] == template_id:
                TEMP_TEMPLATES.pop(i)
                return {"message": "模板已删除"}
        
        raise HTTPException(status_code=404, detail="模板不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete AI template error: {str(e)}")
        raise HTTPException(status_code=500, detail="删除模板失败")


@router.get("/templates/admin", response_model=List[AITemplate])
async def get_all_ai_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有AI模板（管理员功能）"""
    try:
        # 检查用户权限
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="权限不足")
        
        return TEMP_TEMPLATES
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all AI templates error: {str(e)}")
        raise HTTPException(status_code=500, detail="获取模板失败") 