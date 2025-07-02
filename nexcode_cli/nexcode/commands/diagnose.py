import os
import subprocess
import time
import click
from ..utils.git import ensure_git_root
from ..llm.services import get_ai_solution_for_git_error


def get_last_git_error():
    """
    尝试获取最近的Git错误信息
    """
    try:
        # 尝试执行一个简单的git命令来触发错误状态检查
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            return ['git', 'status'], result.stderr.strip()
        
        # 如果没有错误，检查是否有未推送的提交
        result = subprocess.run(['git', 'log', '--oneline', '@{u}..'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            return ['git', 'push'], "You have local commits that haven't been pushed to remote."
        
        # 检查是否有未跟踪的文件
        result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            untracked_files = result.stdout.strip().split('\n')
            return ['git', 'add'], f"You have untracked files: {', '.join(untracked_files[:5])}"
        
        return None, "No recent Git errors detected. Everything seems to be in order."
        
    except Exception as e:
        return ['git', 'status'], f"Error checking Git status: {str(e)}"


def handle_diagnose_command():
    """Implementation of the diagnose command."""
    
    # 确保在Git根目录执行
    git_root, original_cwd = ensure_git_root()
    if git_root is None:
        return
    
    try:
        click.echo("🔍 Diagnosing Git repository status...")
        click.echo("=" * 50)
        
        # 获取最近的Git错误或状态
        last_command, error_message = get_last_git_error()
        
        if last_command is None:
            click.secho("✅ " + error_message, fg="green")
            return
        
        click.echo(f"📋 Last command: {' '.join(last_command)}")
        click.echo(f"⚠️  Issue detected: {error_message}")
        click.echo()
        
        if click.confirm("Do you want AI assistance with this issue?", default=True):
            click.echo("🤖 Getting AI-powered solution...")
            
            # Show progress indicator
            for i in range(3):
                click.echo("  " + "." * (i + 1), nl=False)
                time.sleep(0.5)
            click.echo("")
            
            # Get AI solution
            solution = get_ai_solution_for_git_error(last_command, error_message)
            
            click.secho("\n💡 AI-Powered Solution:", fg="green", bold=True)
            click.echo("=" * 50)
            click.echo(solution)
            click.echo("=" * 50)
        else:
            click.echo("Diagnosis complete. Use 'nexcode ask' if you need help later.")
    
    finally:
        # 切换回原始目录
        if original_cwd and original_cwd != git_root:
            os.chdir(original_cwd) 