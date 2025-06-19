import os
import subprocess
import click
from openai import OpenAI
from .config import config as app_config, get_config_value, set_config_value, list_all_config, reset_config

def get_openai_client():
    """Get OpenAI client, initializing it if needed."""
    # Read configuration from config file and environment variables
    api_key = app_config['api']['key'] or os.environ.get("OPENAI_API_KEY")
    base_url = app_config['api']['base_url']
    
    if not api_key:
        click.echo("Error: API key is not configured.")
        click.echo("Please set it in ~/.config/aicommit/config.yaml or as an OPENAI_API_KEY environment variable.")
        return None
    
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        click.echo(f"Error initializing OpenAI client: {e}")
        return None

# --- AI Helper Function ---
def get_ai_solution_for_git_error(command, error_message):
    """Asks the AI for a solution to a git command error."""
    client = get_openai_client()
    if not client:
        return "Cannot get AI solution: OpenAI client not available."
    
    model_name = app_config['model']['name']
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
            max_tokens=app_config['model']['max_tokens_solution'],
            temperature=app_config['model']['solution_temperature'],
        )
        solution = response.choices[0].message.content.strip()
        return solution
    except Exception as e:
        return f"Failed to get AI help: {e}"

# --- Git Helper Functions ---
def run_git_command(command, dry_run=False):
    """A helper to run a git command and handle errors, with AI assistance."""
    if dry_run:
        click.echo(f"[DRY RUN] Would execute: {' '.join(command)}")
        return True
    
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
def get_commit_style_prompt(style, diff):
    """Generate style-specific prompts for commit messages."""
    
    common_instructions = f"""
    Based on the following git diff, please generate a commit message.
    The message should be concise and descriptive, and should not be too long.
    The message only contains the commit message, no other text.
    The message should be in English.
    The message should be only one line.

    Git Diff:
    ---
    {diff}
    ---
    """
    
    if style == "conventional":
        return f"""
        {common_instructions}
        
        Use the Conventional Commits specification.
        Start with a type like 'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', followed by a short description in lower case.
        Examples:
        - feat: add user authentication
        - fix: resolve database connection issue
        - docs: update installation guide
        """
    
    elif style == "semantic":
        return f"""
        {common_instructions}
        
        Use semantic commit format with clear action words.
        Start with an action verb in present tense, followed by what was changed.
        Examples:
        - Add user authentication system
        - Fix database connection timeout
        - Update documentation for API endpoints
        - Remove deprecated utility functions
        """
    
    elif style == "simple":
        return f"""
        {common_instructions}
        
        Use a simple, direct description of what was changed.
        Be clear and concise without formal prefixes.
        Examples:
        - User authentication added
        - Fixed login bug
        - Updated README
        - Code cleanup
        """
    
    elif style == "emoji":
        return f"""
        {common_instructions}
        
        Use emoji-prefixed commit messages following gitmoji convention.
        Start with an appropriate emoji, then a clear description.
        Examples:
        - ✨ Add user authentication
        - 🐛 Fix database connection issue
        - 📝 Update documentation
        - ♻️ Refactor user service
        - 🎨 Improve code structure
        - 🚀 Deploy new features
        - 🔧 Update configuration
        """
    
    else:
        # Default to conventional if unknown style
        return get_commit_style_prompt("conventional", diff)

def generate_commit_message(diff, style=None):
    """Generates a commit message using the OpenAI API with specified style."""
    if not diff or not diff.strip():
        return "feat: Initial commit or no changes detected"

    client = get_openai_client()
    if not client:
        return None
    
    # Use provided style or fall back to config default
    if style is None:
        style = app_config.get('commit', {}).get('style', 'conventional')
    
    model_name = app_config['model']['name']
    prompt = get_commit_style_prompt(style, diff)
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": f"You are an expert at writing git commit messages in the {style} style."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=app_config['model']['max_tokens_commit'],
            temperature=app_config['model']['commit_temperature'],
        )
        message = response.choices[0].message.content.strip().strip('"`')
        
        # Style-specific post-processing
        if style == "conventional":
            # Ensure conventional commit format
            conventional_prefixes = ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'build', 'ci', 'perf']
            if not any(message.startswith(prefix + ":") for prefix in conventional_prefixes):
                message = "feat: " + message
        elif style == "semantic":
            # Ensure it starts with a verb
            message = message[0].upper() + message[1:] if message else message
        
        return message
    except Exception as e:
        click.echo(f"Error generating commit message from OpenAI: {e}")
        return None

# --- Git Helper Functions (continued) ---
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

def is_tracked(file_path):
    """Check if a file is tracked by git."""
    result = subprocess.run(['git', 'ls-files', '--error-unmatch', file_path],
                          capture_output=True, text=True)
    return result.returncode == 0

def get_changed_files():
    """Get all changed files (modified, added, deleted)."""
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        return []
    
    files = []
    for line in result.stdout.splitlines():
        if len(line) > 3:
            # Extract filename from git status output
            filename = line[3:].strip()
            files.append(filename)
    return files

def should_ignore_file(file_path):
    """Check if a file should be ignored based on .gitignore rules."""
    # For tracked files, we need to check manually if they're in .gitignore
    try:
        with open('.gitignore', 'r') as f:
            ignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        import fnmatch
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(file_path, f"**/{pattern}"):
                return True
        return False
    except FileNotFoundError:
        return False

def smart_git_add(dry_run=False):
    """Intelligently add files respecting .gitignore even for tracked files."""
    changed_files = get_changed_files()
    
    if not changed_files:
        return True
    
    files_to_add = []
    ignored_files = []
    
    for file_path in changed_files:
        if should_ignore_file(file_path):
            ignored_files.append(file_path)
        else:
            files_to_add.append(file_path)
    
    if ignored_files:
        click.echo(f"Ignoring files: {', '.join(ignored_files)}")
    
    if not files_to_add:
        return True  # No files to add
        
    # Add only non-ignored files
    if dry_run:
        click.echo(f"[DRY RUN] Would add files: {', '.join(files_to_add)}")
        return True
    
    try:
        subprocess.run(['git', 'add'] + files_to_add, check=True)
        if files_to_add:
            click.echo(f"Added files: {', '.join(files_to_add)}")
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"Error adding files: {e}")
        return False

# --- CLI Command Definitions ---
@click.group()
def cli():
    """AI Commits: A CLI tool to automate git commits using AI."""
    pass

@cli.command()
@click.option('--dry-run', is_flag=True, help='Preview the commit message without actually committing.')
@click.option('--preview', is_flag=True, help='Only generate and show the commit message.')
@click.option('--style', type=click.Choice(['conventional', 'semantic', 'simple', 'emoji']), 
              help='Commit message style (overrides config default).')
def commit(dry_run, preview, style):
    """Generates a commit message for staged changes and commits them."""
    click.echo("› Checking for staged changes...")
    diff = get_git_diff(staged=True)
    
    if not diff:
        click.echo("No staged changes found. Use 'git add <files>' to stage your changes first.")
        return

    # Show which style is being used
    used_style = style or app_config.get('commit', {}).get('style', 'conventional')
    click.echo(f"› Generating commit message with AI ({used_style} style)...")
    
    commit_message = generate_commit_message(diff, style)

    if commit_message:
        click.echo(f"✓ Generated commit message:\n  {commit_message}")
        
        if preview or dry_run:
            if dry_run:
                click.echo("[DRY RUN] This is what would be committed.")
            return
        
        if click.confirm("Do you want to proceed with this commit?", default=True):
            result = run_git_command(['git', 'commit', '-m', commit_message])
            if result:
                click.echo("✓ Successfully committed.")
        else:
            click.echo("Commit aborted by user.")
    else:
        click.echo("✗ Failed to generate commit message. Aborting.")

@cli.command()
@click.option('--branch', 'new_branch', default=None, help='Create a new branch and push to it.')
@click.option('--dry-run', is_flag=True, help='Preview all operations without actually executing them.')
@click.option('--style', type=click.Choice(['conventional', 'semantic', 'simple', 'emoji']), 
              help='Commit message style (overrides config default).')
def push(new_branch, dry_run, style):
    """Adds all changes, commits, and pushes to the remote repository."""
    
    if dry_run:
        click.secho("[DRY RUN MODE] Preview of operations:", fg="blue", bold=True)
    
    # 1. Create and switch to a new branch if specified
    if new_branch:
        click.echo(f"› Creating new branch '{new_branch}'...")
        if not run_git_command(['git', 'checkout', '-b', new_branch], dry_run):
            return # Error is printed by the helper

    # 2. Add all changes
    click.echo("› Staging all changes...")
    if not smart_git_add(dry_run):
        click.echo("Error: Failed to stage changes.")
        return
    
    # Check if there are any changes to commit after adding
    if not dry_run:
        diff = get_git_diff(staged=True)
        if not diff:
            click.echo("No changes to commit. Working directory is clean.")
            return
    else:
        # In dry run, simulate having changes
        click.echo("[DRY RUN] Simulating changes for demonstration...")
        diff = "simulated diff for dry run"
        
    # 3. Generate commit message
    used_style = style or app_config.get('commit', {}).get('style', 'conventional')
    click.echo(f"› Generating commit message with AI ({used_style} style)...")
    
    if not dry_run:
        commit_message = generate_commit_message(diff, style)
    else:
        # Generate example message based on style for dry run
        style_examples = {
            'conventional': "[DRY RUN] feat: example conventional commit",
            'semantic': "[DRY RUN] Add example feature implementation",
            'simple': "[DRY RUN] Example feature added",
            'emoji': "[DRY RUN] ✨ Add example feature"
        }
        commit_message = style_examples.get(used_style, "[DRY RUN] feat: example commit message")

    if not commit_message:
        click.echo("✗ Failed to generate commit message. Aborting push.")
        return

    click.echo(f"✓ Generated commit message:\n  {commit_message}")
    
    # 4. Commit
    if not run_git_command(['git', 'commit', '-m', commit_message], dry_run):
        return
    if not dry_run:
        click.echo("✓ Successfully committed.")

    # 5. Push to remote
    target_branch = new_branch
    if not target_branch:
        if not dry_run:
            branch_result = run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            if not branch_result:
                return
            target_branch = branch_result.stdout.strip()
        else:
            target_branch = "current-branch"

    click.echo(f"› Pushing to branch '{target_branch}'...")
    push_command = ['git', 'push', '--set-upstream', 'origin', target_branch]
    if not run_git_command(push_command, dry_run):
        return
        
    if not dry_run:
        click.echo(f"✓ Successfully pushed to 'origin/{target_branch}'.")
    else:
        click.secho("\n[DRY RUN COMPLETE] No actual changes were made.", fg="blue", bold=True)

@cli.command()
@click.option('--list', 'list_config', is_flag=True, help='List all configuration values.')
@click.option('--get', 'get_key', help='Get a specific configuration value (e.g., model.name).')
@click.option('--set', 'set_key', help='Set a configuration key (use with --value).')
@click.option('--value', help='Value to set (use with --set).')
@click.option('--reset', is_flag=True, help='Reset configuration to defaults.')
def config(list_config, get_key, set_key, value, reset):
    """Manage aicommit configuration."""
    
    if reset:
        if click.confirm("Are you sure you want to reset all configuration to defaults?"):
            reset_config()
            click.echo("✓ Configuration reset to defaults.")
        return
    
    if list_config:
        config_items = list_all_config()
        click.echo("Current configuration:")
        click.echo("-" * 30)
        for key, val in config_items.items():
            if key == 'api.key' and val:
                # Hide API key for security
                displayed_val = val[:8] + "..." if len(val) > 8 else "***"
            else:
                displayed_val = val
            click.echo(f"{key}: {displayed_val}")
        return
    
    if get_key:
        value = get_config_value(get_key)
        if value is not None:
            if get_key == 'api.key' and value:
                # Hide API key for security
                displayed_val = value[:8] + "..." if len(value) > 8 else "***"
            else:
                displayed_val = value
            click.echo(f"{get_key}: {displayed_val}")
        else:
            click.echo(f"Configuration key '{get_key}' not found.")
        return
    
    if set_key:
        if not value:
            click.echo("Error: --value is required when using --set.")
            return
        
        if set_config_value(set_key, value):
            click.echo(f"✓ Set {set_key} = {value}")
        else:
            click.echo(f"✗ Failed to set {set_key}")
        return
    
    # If no options provided, show help
    click.echo("Use --help to see available configuration options.")

if __name__ == '__main__':
    cli() 