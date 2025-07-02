import os
import httpx
from ..config import config as app_config





def get_api_server_url():
    """获取API服务端URL"""
    return app_config.get('api_server', {}).get('url', 'http://localhost:8000')


def get_api_server_token():
    """获取API服务端Token"""
    return app_config.get('api_server', {}).get('token', '')


def get_client_api_key():
    """获取客户端的OpenAI API密钥，用于传递给服务端"""
    # 先尝试从配置文件获取
    api_key = app_config.get('api', {}).get('key', '')
    if api_key:
        return api_key
    
    # 如果配置文件中没有，尝试从环境变量获取
    return os.getenv('OPENAI_API_KEY', '')


def call_api_server(endpoint: str, data: dict) -> str:
    """
    调用API服务端的统一方法
    
    Args:
        endpoint: API端点路径（如 '/v1/git-error/'）
        data: 请求数据
    
    Returns:
        str: API响应内容
    """
    try:
        server_url = get_api_server_url()
        token = get_api_server_token()
        url = f"{server_url.rstrip('/')}{endpoint}"
        
        # 准备请求头
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            # 根据不同的端点返回相应的字段
            if 'solution' in result:
                return result['solution']
            elif 'analysis' in result:
                return result['analysis']
            elif 'answer' in result:
                return result['answer']
            else:
                return str(result)
                
    except httpx.RequestError as e:
        return f"Failed to connect to API server: {e}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return f"Authentication failed: Please check your API token configuration. Use 'nexcode config set api_server.token your-token' to set the token."
        return f"API server error ({e.response.status_code}): {e.response.text}"
    except Exception as e:
        return f"Unexpected error: {e}"





def get_ai_solution_for_git_error(command, error_message):
    """Asks the AI for a solution to a git command error."""
    data = {
        "command": command,
        "error_message": error_message,
        "api_key": get_client_api_key()  # 传递客户端的API密钥
    }
    return call_api_server("/v1/git-error/", data)





def check_code_for_bugs(diff):
    """Analyzes code changes for potential bugs and issues."""
    if not diff or not diff.strip():
        return "No code changes to analyze."
    
    data = {
        "diff": diff,
        "api_key": get_client_api_key()  # 传递客户端的API密钥
    }
    return call_api_server("/v1/code-review/", data)





def ask_ai_about_commits(question):
    """Ask AI about git commit related questions."""
    if not question or not question.strip():
        return "Please provide a question to ask about."
    
    data = {
        "question": question,
        "api_key": get_client_api_key()  # 传递客户端的API密钥
    }
    return call_api_server("/v1/commit-qa/", data) 