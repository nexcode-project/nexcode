import subprocess
import time
import os
import click
from ..utils.git import get_git_diff, ensure_git_root
from ..llm.services import check_code_for_bugs


def handle_check_command(staged, check_all, target_file):
    """Implementation of the check command."""
    
    # 确保在Git根目录执行
    git_root, original_cwd = ensure_git_root()
    if git_root is None:
        return
    
    try:
        if target_file:
            # Check specific file
            click.echo(f"› Analyzing file: {target_file}")
            try:
                result = subprocess.run(['git', 'diff', target_file], 
                                      capture_output=True, text=True, check=True)
                diff = result.stdout
            except subprocess.CalledProcessError:
                click.echo(f"Error: Could not get diff for {target_file}")
                return
        elif check_all:
            # Check all unstaged changes
            click.echo("› Analyzing all unstaged changes...")
            diff = get_git_diff(staged=False)
        else:
            # Check staged changes (default)
            click.echo("› Analyzing staged changes...")
            diff = get_git_diff(staged=True)
        
        if not diff:
            click.echo("No changes found to analyze.")
            return
        
        click.echo("› Running AI-powered bug analysis...")
        
        # Show a simple progress indicator
        for i in range(3):
            click.echo("  " + "." * (i + 1), nl=False)
            time.sleep(0.5)
        click.echo("")
        
        analysis = check_code_for_bugs(diff)
        
        click.secho("\n🔍 Code Analysis Results:", fg="blue", bold=True)
        click.echo("=" * 50)
        click.echo(analysis)
        click.echo("=" * 50)
    
    finally:
        # 切换回原始目录
        if original_cwd and original_cwd != git_root:
            os.chdir(original_cwd) 