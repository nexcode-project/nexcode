"""
服务端状态检查命令
"""

import click
from ..api.client import api_client
from ..config import get_merged_config

@click.command()
def status():
    """检查NexCode配置和服务状态"""
    click.echo("🔍 正在检查NexCode状态...")
    
    # 检查配置
    config = get_merged_config()
    click.echo("\n📋 配置状态:")
    
    # API服务器配置
    api_server = config.get('api_server', {})
    server_url = api_server.get('url', '未配置')
    server_token = api_server.get('token', '未配置')
    
    click.echo(f"  服务端URL: {server_url}")
    click.echo(f"  认证Token: {'已配置' if server_token != '未配置' else '未配置'}")
    
    # API配置（将传递给服务端）
    api_config = config.get('api', {})
    openai_config = config.get('openai', {})  # 兼容旧配置
    model_config = config.get('model', {})
    
    api_key = api_config.get('key') or openai_config.get('api_key') or '未配置'
    api_base_url = api_config.get('base_url') or openai_config.get('api_base_url') or '未配置'
    model = model_config.get('name') or openai_config.get('model') or '未配置'
    
    click.echo(f"  API密钥: {'已配置' if api_key != '未配置' else '未配置'}")
    click.echo(f"  API基础URL: {api_base_url}")
    click.echo(f"  模型名称: {model}")
    
    # 检查服务端连接
    click.echo("\n🌐 服务端连接:")
    try:
        result = api_client.health_check()
        
        if 'error' in result:
            click.echo(f"  ❌ 连接失败: {result['error']}")
            click.echo("\n💡 解决建议:")
            click.echo("  1. 检查服务端是否启动")
            click.echo("  2. 检查服务端URL配置是否正确")
            click.echo("  3. 检查网络连接")
        else:
            click.echo("  ✅ 服务端连接正常")
            click.echo(f"  状态: {result.get('status', 'unknown')}")
            click.echo(f"  版本: {result.get('version', 'unknown')}")
            
            # 显示可用服务
            services = result.get('services', {})
            if services:
                click.echo("  可用服务:")
                for service, status in services.items():
                    click.echo(f"    • {service}: {status}")
    
    except Exception as e:
        click.echo(f"  ❌ 连接检查失败: {str(e)}")
    
    # 配置建议
    click.echo("\n⚙️  配置状态总结:")
    
    issues = []
    if server_url == '未配置':
        issues.append("服务端URL未配置")
    if server_token == '未配置':
        issues.append("认证Token未配置")
    if api_key == '未配置':
        issues.append("API密钥未配置")
    
    if issues:
        click.echo("  ⚠️  发现配置问题:")
        for issue in issues:
            click.echo(f"    • {issue}")
        
        click.echo("\n💡 配置建议:")
        click.echo("  1. 设置服务端URL: nexcode config set api_server.url http://localhost:8000")
        click.echo("  2. 设置认证Token: nexcode config set api_server.token your-token")
        click.echo("  3. 设置API密钥: nexcode config set api.key your-api-key")
        click.echo("  4. 设置API基础URL: nexcode config set api.base_url your-api-base-url")
        click.echo("  5. 设置模型名称: nexcode config set model.name your-model-name")
    else:
        click.echo("  ✅ 所有必要配置均已就绪")
        
    click.echo("\n📚 架构说明:")
    click.echo("  CLI传递API配置 → 服务端 → LLM API")
    click.echo("  服务端将复用CLI传递的API密钥和配置") 