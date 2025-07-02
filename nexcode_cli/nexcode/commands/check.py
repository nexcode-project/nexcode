import subprocess
import time
import click
from ..utils.git import get_git_diff
from ..llm.services import check_code_for_bugs


def handle_check_command(staged, check_all, target_file):
    """Implementation of the check command."""
    
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