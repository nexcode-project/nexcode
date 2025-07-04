"""
Token计数模块
支持OpenAI GPT模型和Qwen3模型的token统计
"""

import tiktoken
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TokenCounter:
    """Token计数器"""
    
    def __init__(self):
        self._encoders: Dict[str, Any] = {}
    
    def get_encoder(self, model_name: str):
        """获取指定模型的encoder"""
        if model_name in self._encoders:
            return self._encoders[model_name]
        
        try:
            # 尝试直接获取模型的编码器
            encoder = tiktoken.encoding_for_model(model_name)
            self._encoders[model_name] = encoder
            return encoder
        except KeyError:
            # 如果模型不存在，使用通用编码器
            logger.warning(f"Model {model_name} not found in tiktoken, using cl100k_base")
            encoder = tiktoken.get_encoding("cl100k_base")
            self._encoders[model_name] = encoder
            return encoder
    
    def count_tokens(self, text: str, model_name: str = "gpt-3.5-turbo") -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            model_name: 模型名称
            
        Returns:
            int: token数量
        """
        if not text:
            return 0
        
        try:
            # 特殊处理Qwen模型
            if "qwen" in model_name.lower():
                return self._count_qwen_tokens(text)
            
            # 处理其他OpenAI兼容模型
            encoder = self.get_encoder(model_name)
            return len(encoder.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens for model {model_name}: {e}")
            # 回退到简单的字符计数估算
            return len(text) // 3
    
    def _count_qwen_tokens(self, text: str) -> int:
        """
        计算Qwen模型的token数量
        使用cl100k_base编码器作为近似
        """
        try:
            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except Exception as e:
            logger.error(f"Error counting Qwen tokens: {e}")
            # 中文文本大约每个字符0.7个token，英文文本每个字符0.25个token
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return int(chinese_chars * 0.7 + other_chars * 0.25)
    
    def count_messages_tokens(self, messages: list, model_name: str = "gpt-3.5-turbo") -> int:
        """
        计算消息列表的token数量（OpenAI格式）
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "text"}]
            model_name: 模型名称
            
        Returns:
            int: 总token数量
        """
        total_tokens = 0
        
        for message in messages:
            # 每个消息的基础开销
            total_tokens += 3  # role + content + message separator
            
            # 计算内容的token
            content = message.get("content", "")
            total_tokens += self.count_tokens(content, model_name)
            
            # role的token
            role = message.get("role", "")
            total_tokens += self.count_tokens(role, model_name)
        
        # 对话结束的token
        total_tokens += 3
        
        return total_tokens
    
    def estimate_completion_tokens(self, prompt_tokens: int, model_name: str = "gpt-3.5-turbo") -> int:
        """
        估算completion的token数量
        
        Args:
            prompt_tokens: prompt的token数量
            model_name: 模型名称
            
        Returns:
            int: 估算的completion token数量
        """
        # 根据不同任务类型返回不同的估算值
        if "commit" in model_name.lower() or prompt_tokens < 100:
            # 提交消息生成通常比较简短
            return min(50, max(10, prompt_tokens // 10))
        elif prompt_tokens < 500:
            # 短文本任务
            return min(200, max(20, prompt_tokens // 5))
        else:
            # 长文本任务
            return min(1000, max(50, prompt_tokens // 3))


# 全局token计数器实例
token_counter = TokenCounter()

def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    """便捷函数：计算文本token数量"""
    return token_counter.count_tokens(text, model_name)

def count_messages_tokens(messages: list, model_name: str = "gpt-3.5-turbo") -> int:
    """便捷函数：计算消息token数量"""
    return token_counter.count_messages_tokens(messages, model_name)

def estimate_total_tokens(prompt: str, model_name: str = "gpt-3.5-turbo") -> Dict[str, int]:
    """
    估算总token使用量
    
    Returns:
        dict: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    """
    prompt_tokens = count_tokens(prompt, model_name)
    completion_tokens = token_counter.estimate_completion_tokens(prompt_tokens, model_name)
    total_tokens = prompt_tokens + completion_tokens
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens
    } 