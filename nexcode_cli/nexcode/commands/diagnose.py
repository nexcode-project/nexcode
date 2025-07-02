import click
import subprocess
import sys
from ..api.client import api_client

@click.command()
@click.argument('git_command', nargs=-1, required=False)
@click.option('--error', help='直接提供错误信息进行分析')
def diagnose(git_command, error):
    """诊断Git命令错误"""
    
    if error:
        # 直接分析提供的错误信息
        command = ["git", "unknown"]
        error_message = error
    elif git_command:
        # 执行用户提供的Git命令并捕获错误
        try:
            cmd = ["git"] + list(git_command)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            click.echo("✅ Git命令执行成功:")
            click.echo(result.stdout)
            return
        except subprocess.CalledProcessError as e:
            command = cmd
            error_message = e.stderr
        except FileNotFoundError:
            click.echo("❌ 错误: 未找到git命令")
            return
    else:
        click.echo("❌ 请提供Git命令或使用--error选项提供错误信息")
        return
    
    if not error_message.strip():
        click.echo("❌ 没有捕获到错误信息")
        return
    
    click.echo(f"🔍 正在分析Git错误...")
    click.echo(f"命令: {' '.join(command)}")
    click.echo(f"错误信息: {error_message}")
    click.echo()
    
    try:
        # 调用API服务进行Git错误分析
        result = api_client.analyze_git_error(command, error_message)
        
        if 'error' in result:
            click.echo(f"❌ 分析失败: {result['error']}")
            return
        
        # 显示解决方案
        solution = result.get('solution', '未找到解决方案')
        click.echo("💡 解决方案:")
        click.echo("=" * 50)
        click.echo(solution)
        click.echo("=" * 50)
        
    except Exception as e:
        click.echo(f"❌ 分析过程中出现错误: {str(e)}")
        raise click.ClickException(str(e))


 