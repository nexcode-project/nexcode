import os
import subprocess
import click
from openai import OpenAI
from .config import config

# --- Configuration ---
# Read configuration from config file and environment variables
api_key = config['api']['key'] or os.environ.get("OPENAI_API_KEY")
base_url = config['api']['base_url']
model_name = config['model']['name']

if not api_key:
    click.echo("Error: API key is not configured.")
    click.echo("Please set it in ~/.config/aicommit/config.yaml or as an OPENAI_API_KEY environment variable.")
    exit(1)

try:
    client = OpenAI(api_key=api_key, base_url=base_url)
except Exception as e:
    click.echo(f"Error initializing OpenAI client: {e}")
    exit(1)

# --- AI Helper Function ---
def get_ai_solution_for_git_error(command, error_message):
    """Asks the AI for a solution to a git command error."""
    prompt = f"""
    I encountered an error while running a git command.

    The command was:
    `{' '.join(command)}`

    The error message was:
    ---
    {error_message}
    ---

    As a senior Git expert, please explain what this error means and provide a step-by-step solution on how to fix it. Provide specific commands if applicable.
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a Git expert who helps resolve errors."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config['model']['max_tokens_solution'],
            temperature=config['model']['solution_temperature'],
        )
        solution = response.choices[0].message.content.strip()
        return solution
    except Exception as e:
        return f"Failed to get AI help: {e}"

# --- Git Helper Functions ---
def run_git_command(command):
    """A helper to run a git command and handle errors, with AI assistance."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result
    except FileNotFoundError:
        click.echo("Error: 'git' command not found. Is Git installed and in your PATH?")
        return None
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip()
        failed_command_str = ' '.join(command)
        
        click.secho(f"\n✗ Git command failed: {failed_command_str}", fg="red")
        click.secho(f"Error: {error_message}", fg="red")

        if click.confirm("\nDo you want to ask AI for a solution?", default=True):
            click.echo("› Asking AI for a solution...")
            solution = get_ai_solution_for_git_error(command, error_message)
            click.secho("\n💡 AI-Powered Solution:", fg="green", bold=True)
            click.echo("-" * 20)
            click.echo(solution)
            click.echo("-" * 20)
        
        return None

def get_git_diff(staged=True, added_only=False):
    """Fetches the git diff, optionally for staged or all changes."""
    command = ['git', 'diff']
    if staged:
        command.append('--staged')
    if added_only:
        command.append('--diff-filter=A') # For push command to see all changes
    
    result = run_git_command(command)
    return result.stdout if result else None

# --- AI Helper Function ---
def generate_commit_message(diff):
    """Generates a commit message using the OpenAI API."""
    if not diff or not diff.strip():
        return "feat: Initial commit or no changes detected"

    prompt = f"""
    Based on the following git diff, please generate a concise and descriptive commit message.
    The message should strictly follow the Conventional Commits specification.
    It should start with a type like 'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', followed by a short description in lower case.
    Example: fix: correct minor typos in documentation

    Git Diff:
    ---
    {diff}
    ---
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert at writing git commit messages according to the Conventional Commits specification."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config['model']['max_tokens_commit'],
            temperature=config['model']['commit_temperature'],
        )
        message = response.choices[0].message.content.strip().strip('"`')
        return message
    except Exception as e:
        click.echo(f"Error generating commit message from OpenAI: {e}")
        return None

# --- CLI Command Definitions ---
@click.group()
def cli():
    """AI Commits: A CLI tool to automate git commits using AI."""
    pass

@cli.command()
def commit():
    """Generates a commit message for staged changes and commits them."""
    click.echo("› Checking for staged changes...")
    diff = get_git_diff(staged=True)
    
    if not diff:
        click.echo("No staged changes found. Use 'git add <files>' to stage your changes first.")
        return

    click.echo("› Generating commit message with AI...")
    commit_message = generate_commit_message(diff)

    if commit_message:
        click.echo(f"✓ Generated commit message:\n  {commit_message}")
        if click.confirm("Do you want to proceed with this commit?", default=True):
            result = run_git_command(['git', 'commit', '-m', commit_message])
            if result:
                click.echo("✓ Successfully committed.")
        else:
            click.echo("Commit aborted by user.")
    else:
        click.echo("✗ Failed to generate commit message. Aborting.")

def get_all_files():
    """Get all files in the repository, including untracked ones."""
    result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '--cached'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.splitlines()
    return []

def is_ignored(file_path):
    """Check if a file is ignored by .gitignore rules."""
    result = subprocess.run(['git', 'check-ignore', file_path],
                          capture_output=True, text=True)
    return result.returncode == 0

def smart_git_add():
    """Intelligently add files respecting .gitignore even for tracked files."""
    # First, get all files
    all_files = get_all_files()
    
    # Filter out ignored files
    files_to_add = [f for f in all_files if not is_ignored(f)]
    
    if not files_to_add:
        return True  # No files to add
        
    # Add only non-ignored files
    try:
        if files_to_add:
            subprocess.run(['git', 'add', '--'] + files_to_add, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@cli.command()
@click.option('--branch', 'new_branch', default=None, help='Create a new branch and push to it.')
def push(new_branch):
    """Adds all changes, commits, and pushes to the remote repository."""
    
    # 1. Create and switch to a new branch if specified
    if new_branch:
        click.echo(f"› Creating new branch '{new_branch}'...")
        if not run_git_command(['git', 'checkout', '-b', new_branch]):
            return # Error is printed by the helper

    # 2. Add all changes
    click.echo("› Staging all changes...")
    if not smart_git_add():
        click.echo("Error: Failed to stage changes.")
        return
    
    # Check if there are any changes to commit after adding
    diff = get_git_diff(staged=True)
    if not diff:
        click.echo("No changes to commit. Working directory is clean.")
        return
        
    # 3. Generate commit message
    click.echo("› Generating commit message with AI...")
    commit_message = generate_commit_message(diff)

    if not commit_message:
        click.echo("✗ Failed to generate commit message. Aborting push.")
        return

    click.echo(f"✓ Generated commit message:\n  {commit_message}")
    
    # 4. Commit
    if not run_git_command(['git', 'commit', '-m', commit_message]):
        return
    click.echo("✓ Successfully committed.")

    # 5. Push to remote
    target_branch = new_branch
    if not target_branch:
        branch_result = run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        if not branch_result:
            return
        target_branch = branch_result.stdout.strip()

    click.echo(f"› Pushing to branch '{target_branch}'...")
    push_command = ['git', 'push', '--set-upstream', 'origin', target_branch]
    if not run_git_command(push_command):
        return
        
    click.echo(f"✓ Successfully pushed to 'origin/{target_branch}'.")

if __name__ == '__main__':
    cli() 