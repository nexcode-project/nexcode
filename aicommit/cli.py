import click
from .commands.commit import handle_commit_command
from .commands.push import handle_push_command
from .commands.config_cmd import handle_config_command
from .commands.check import handle_check_command
from .commands.ask import handle_ask_command


@click.group()
def cli():
    """AI Commits: A CLI tool to automate git commits using AI."""
    pass


@cli.command()
@click.option('--dry-run', is_flag=True, help='Preview the commit message without actually committing.')
@click.option('--preview', is_flag=True, help='Only generate and show the commit message.')
@click.option('--style', type=click.Choice(['conventional', 'semantic', 'simple', 'emoji']), 
              help='Commit message style (overrides config default).')
@click.option('--check-bugs', is_flag=True, help='Run bug analysis before committing.')
@click.option('--no-check-bugs', is_flag=True, help='Skip bug analysis (overrides config default).')
def commit(dry_run, preview, style, check_bugs, no_check_bugs):
    """Generates a commit message for staged changes and commits them."""
    handle_commit_command(dry_run, preview, style, check_bugs, no_check_bugs)


@cli.command()
@click.option('--branch', 'new_branch', default=None, help='Create a new branch and push to it.')
@click.option('--dry-run', is_flag=True, help='Preview all operations without actually executing them.')
@click.option('--style', type=click.Choice(['conventional', 'semantic', 'simple', 'emoji']), 
              help='Commit message style (overrides config default).')
@click.option('--check-bugs', is_flag=True, help='Run bug analysis before committing.')
@click.option('--no-check-bugs', is_flag=True, help='Skip bug analysis (overrides config default).')
def push(new_branch, dry_run, style, check_bugs, no_check_bugs):
    """Adds all changes, commits, and pushes to the remote repository."""
    handle_push_command(new_branch, dry_run, style, check_bugs, no_check_bugs)


@cli.command()
@click.option('--set', 'set_value', help='Set a configuration value (format: key=value, e.g. commit.check_bugs_by_default=true)')
@click.option('--get', 'get_key', help='Get a configuration value')
@click.option('--list', 'list_all', is_flag=True, help='List all configuration values')
def config(set_value, get_key, list_all):
    """Manage aicommit configuration."""
    handle_config_command(set_value, get_key, list_all)


@cli.command()
@click.option('--staged', is_flag=True, default=True, help='Check staged changes (default).')
@click.option('--all', 'check_all', is_flag=True, help='Check all unstaged changes.')
@click.option('--file', 'target_file', help='Check specific file.')
def check(staged, check_all, target_file):
    """Analyze code changes for potential bugs and issues."""
    handle_check_command(staged, check_all, target_file)


@cli.command()
@click.option('--question', '-q', help='Ask a specific question about Git commits or workflows.')
@click.option('--interactive', '-i', is_flag=True, help='Start interactive Q&A session with AI.')
def ask(question, interactive):
    """Ask AI assistant about Git commits, version control, or development workflows."""
    handle_ask_command(question, interactive)


if __name__ == '__main__':
    cli() 