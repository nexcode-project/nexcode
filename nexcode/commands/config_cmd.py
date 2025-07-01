import click
from ..config import config as app_config
from .. import config as config_module


def interactive_config():
    """启动交互式配置模式"""
    click.echo("🔧 欢迎使用 Nexcode 交互式配置")
    click.echo("=" * 50)
    
    # 获取当前配置
    current_config = dict(app_config)
    
    # API 配置
    click.echo("\n📡 API 配置")
    click.echo("-" * 20)
    
    # API Key
    current_key = current_config.get('api', {}).get('key', '')
    if current_key:
        click.echo(f"当前 API Key: {'*' * (len(current_key) - 8)}{current_key[-8:] if len(current_key) > 8 else current_key}")
    else:
        click.echo("当前 API Key: 未设置")
    
    new_key = click.prompt('请输入 API Key (留空保持不变)', default='', show_default=False)
    if new_key.strip():
        if 'api' not in current_config:
            current_config['api'] = {}
        current_config['api']['key'] = new_key.strip()
    
    # Base URL
    current_base_url = current_config.get('api', {}).get('base_url', '')
    new_base_url = click.prompt('请输入 API Base URL', default=current_base_url or 'http://10.12.160.15/v1')
    if 'api' not in current_config:
        current_config['api'] = {}
    current_config['api']['base_url'] = new_base_url
    
    # 模型配置
    click.echo("\n🤖 模型配置")
    click.echo("-" * 20)
    
    current_model = current_config.get('model', {}).get('name', '')
    new_model = click.prompt('请输入模型名称', default=current_model or 'codedrive-chat')
    if 'model' not in current_config:
        current_config['model'] = {}
    current_config['model']['name'] = new_model
    
    # Commit 温度
    current_commit_temp = current_config.get('model', {}).get('commit_temperature', 0.7)
    new_commit_temp = click.prompt('提交消息生成温度 (0.0-1.0)', default=current_commit_temp, type=float)
    current_config['model']['commit_temperature'] = max(0.0, min(1.0, new_commit_temp))
    
    # Solution 温度
    current_solution_temp = current_config.get('model', {}).get('solution_temperature', 0.5)
    new_solution_temp = click.prompt('解决方案生成温度 (0.0-1.0)', default=current_solution_temp, type=float)
    current_config['model']['solution_temperature'] = max(0.0, min(1.0, new_solution_temp))
    
    # Max tokens
    current_commit_tokens = current_config.get('model', {}).get('max_tokens_commit', 60)
    new_commit_tokens = click.prompt('提交消息最大 tokens', default=current_commit_tokens, type=int)
    current_config['model']['max_tokens_commit'] = max(1, new_commit_tokens)
    
    current_solution_tokens = current_config.get('model', {}).get('max_tokens_solution', 512)
    new_solution_tokens = click.prompt('解决方案最大 tokens', default=current_solution_tokens, type=int)
    current_config['model']['max_tokens_solution'] = max(1, new_solution_tokens)
    
    # Commit 配置
    click.echo("\n📝 提交配置")
    click.echo("-" * 20)
    
    # Commit 风格
    current_style = current_config.get('commit', {}).get('style', 'conventional')
    style_choices = ['conventional', 'semantic', 'simple', 'emoji']
    click.echo(f"可选的提交风格: {', '.join(style_choices)}")
    new_style = click.prompt('请选择提交消息风格', default=current_style, type=click.Choice(style_choices))
    if 'commit' not in current_config:
        current_config['commit'] = {}
    current_config['commit']['style'] = new_style
    
    # 默认检查 bugs
    current_check_bugs = current_config.get('commit', {}).get('check_bugs_by_default', False)
    new_check_bugs = click.confirm('默认启用 bug 检查？', default=current_check_bugs)
    current_config['commit']['check_bugs_by_default'] = new_check_bugs
    
    # 保存配置
    click.echo("\n💾 保存配置...")
    try:
        config_module.save_config(current_config)
        click.echo("✅ 配置已成功保存！")
        
        # 显示保存的配置摘要
        click.echo("\n📋 配置摘要:")
        click.echo("-" * 30)
        click.echo(f"API Base URL: {current_config['api']['base_url']}")
        click.echo(f"模型: {current_config['model']['name']}")
        click.echo(f"提交风格: {current_config['commit']['style']}")
        click.echo(f"默认 bug 检查: {'是' if current_config['commit']['check_bugs_by_default'] else '否'}")
        
    except Exception as e:
        click.echo(f"❌ 保存配置时出错: {e}")


def init_local_config():
    """初始化本地仓库配置"""
    click.echo("🏠 初始化本地仓库配置")
    click.echo("=" * 50)
    
    try:
        config_file, is_new = config_module.init_local_config()
        
        if is_new:
            click.echo("✅ 已创建本地配置文件！")
            click.echo("✅ 已将 .nexcode/ 添加到 .gitignore")
        else:
            click.echo("ℹ️  本地配置文件已存在")
        
        click.echo(f"\n📁 配置文件位置: {config_file}")
        click.echo("\n📝 请编辑配置文件以设置仓库特定的推送行为:")
        click.echo(f"   {config_file}")
        
        click.echo("\n💡 配置示例:")
        click.echo("   - GitHub 标准推送: git push {remote} {branch}")
        click.echo("   - Gerrit 代码评审: git push {remote} HEAD:refs/for/{target_branch}")
        click.echo("   - GitLab MR 创建: git push {remote} {branch} -o merge_request.create")
        
        click.echo("\n🧪 配置完成后，使用以下命令测试:")
        click.echo("   nexcode push --dry-run")
        
    except Exception as e:
        click.echo(f"❌ 初始化本地配置时出错: {e}")


def handle_config_command(set_value, get_key, list_all, interactive, init_local):
    """Implementation of the config command."""
    
    # 初始化本地配置
    if init_local:
        init_local_config()
        return
    
    # 如果没有提供任何选项，启动交互式配置
    if not any([set_value, get_key, list_all, interactive]):
        interactive_config()
        return
    
    # 如果明确指定了交互式模式
    if interactive:
        interactive_config()
        return
    
    if set_value:
        # Parse key=value format
        if '=' not in set_value:
            click.echo("Error: Use format key=value (e.g. commit.check_bugs_by_default=true)")
            return
            
        key, value = set_value.split('=', 1)
        
        # Parse boolean values
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        
        # Set nested key
        keys = key.split('.')
        config_dict = dict(app_config)
        
        # Navigate to the nested structure
        current = config_dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save to file
        try:
            config_module.save_config(config_dict)
            click.echo(f"✓ Set {key} = {value}")
        except Exception as e:
            click.echo(f"Error saving configuration: {e}")
            
    elif get_key:
        # Get nested key value
        keys = get_key.split('.')
        current = app_config
        
        try:
            for k in keys:
                current = current[k]
            click.echo(f"{get_key} = {current}")
        except KeyError:
            click.echo(f"Configuration key '{get_key}' not found")
            
    elif list_all:
        click.echo("Current configuration:")
        click.echo("-" * 40)
        
        # Check if we have local config
        local_config_exists = config_module.get_local_config_file_path().exists()
        if local_config_exists:
            click.echo("📝 配置来源: 全局配置 + 本地配置覆盖")
        else:
            click.echo("📝 配置来源: 全局配置")
        
        click.echo()
        
        def print_config(config_dict, prefix=""):
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    print_config(value, f"{prefix}{key}.")
                else:
                    click.echo(f"{prefix}{key} = {value}")
        
        print_config(app_config)
        
        if local_config_exists:
            click.echo("\n🏠 本地配置文件:")
            click.echo(f"   {config_module.get_local_config_file_path()}")
            
            local_config = config_module.load_local_config()
            if local_config.get('repository'):
                repo_config = local_config['repository']
                click.echo(f"\n📦 本地仓库设置:")
                click.echo(f"   类型: {repo_config.get('type', 'N/A')}")
                click.echo(f"   推送命令: {repo_config.get('push_command', 'N/A')}")
        else:
            click.echo(f"\n💡 要为此仓库创建本地配置，请运行:")
            click.echo(f"   nexcode config --init-local") 