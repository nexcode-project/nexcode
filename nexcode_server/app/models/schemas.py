from pydantic import BaseModel
from typing import List, Optional

class GitErrorRequest(BaseModel):
    command: List[str]
    error_message: str
    api_key: Optional[str] = None  # 客户端传递的 API 密钥

class GitErrorResponse(BaseModel):
    solution: str
    
class CodeReviewRequest(BaseModel):
    diff: str
    api_key: Optional[str] = None  # 客户端传递的 API 密钥

class CodeReviewResponse(BaseModel):
    analysis: str
    
class CommitQARequest(BaseModel):
    question: str
    api_key: Optional[str] = None  # 客户端传递的 API 密钥

class CommitQAResponse(BaseModel):
    answer: str 