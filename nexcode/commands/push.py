import click
import shlex
from ..config import config as app_config
from ..utils.git import get_git_diff, smart_git_add
from ..llm.services import check_code_for_bugs
from ..prompt.generators import generate_commit_message
from ..llm.services import get_ai_solution_for_git_error


def run_git_command_with_ai(command, dry_run=False):
    """Git command wrapper that includes AI error assistance."""
    from ..utils.git import run_git_command
    return run_git_command(command, dry_run=dry_run, ai_helper_func=get_ai_solution_for_git_error)


def get_push_command(target_branch, new_branch=None):
    """Get the appropriate push command based on local configuration."""
    # Get local repository configuration
    local_repo_config = app_config.get('_local_repository', {})
    
    if not local_repo_config:
        # No local config, use default GitHub-style push
        remote = 'origin'
        return ['git', 'push', '--set-upstream', remote, target_branch]
    
    # Get configuration values
    remote = local_repo_config.get('remote', 'origin')
    push_template = local_repo_config.get('push_command', 'git push {remote} {branch}')
    target_branch_config = local_repo_config.get('target_branch', 'main')
    repo_type = local_repo_config.get('type', 'github')
    
    # Variables for template substitution
    variables = {
        'remote': remote,
        'branch': target_branch,
        'target_branch': target_branch_config
    }
    
    # Format the push command
    try:
        formatted_command = push_template.format(**variables)
        # Convert to command list
        command_parts = shlex.split(formatted_command)
        return command_parts
    except Exception as e:
        click.echo(f"Warning: Invalid push command template: {e}")
        click.echo(f"Falling back to default push command")
        return ['git', 'push', '--set-upstream', remote, target_branch]


def show_push_preview(target_branch, new_branch=None):
    """Show what push command will be executed."""
    local_repo_config = app_config.get('_local_repository', {})
    
    if local_repo_config:
        repo_type = local_repo_config.get('type', 'github')
        push_command = get_push_command(target_branch, new_branch)
        push_cmd_str = ' '.join(push_command)
        
        click.echo(f"📦 仓库类型: {repo_type}")
        click.echo(f"🚀 推送命令: {push_cmd_str}")
        
        # Show explanation for special repository types
        if repo_type == 'gerrit':
            click.echo("💡 Gerrit 推送说明: 代码将推送到 refs/for/ 等待代码评审")
        elif repo_type == 'gitlab':
            click.echo("💡 GitLab 推送说明: 代码将推送到 GitLab 仓库")
        elif repo_type == 'gitee':
            click.echo("💡 Gitee 推送说明: 代码将推送到 Gitee 仓库")
    else:
        click.echo("📦 使用默认 GitHub 风格推送")
        click.echo(f"🚀 推送命令: git push --set-upstream origin {target_branch}")


def handle_push_command(new_branch, dry_run, style, check_bugs, no_check_bugs):
    """Implementation of the push command."""
    
    if dry_run:
        click.secho("[DRY RUN MODE] Preview of operations:", fg="blue", bold=True)
    
    # 1. Create and switch to a new branch if specified
    if new_branch:
        click.echo(f"› Creating new branch '{new_branch}'...")
        if not run_git_command_with_ai(['git', 'checkout', '-b', new_branch], dry_run):
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

    # Determine if bug check should be run
    should_check_bugs = check_bugs or (
        app_config.get('commit', {}).get('check_bugs_by_default', False) and not no_check_bugs
    )

    # Run bug check if requested or configured by default
    if should_check_bugs and not dry_run:
        click.echo("› Running bug analysis...")
        analysis = check_code_for_bugs(diff)
        
        click.secho("\n🔍 Bug Analysis Results:", fg="blue", bold=True)
        click.echo("-" * 40)
        click.echo(analysis)
        click.echo("-" * 40)
        
        # Ask user if they want to continue
        if "No significant issues detected" not in analysis:
            if not click.confirm("\nIssues detected. Do you want to continue with the push?", default=False):
                click.echo("Push cancelled due to code issues.")
                return
        else:
            click.echo("✅ No significant issues detected!")
    elif should_check_bugs and dry_run:
        click.echo("› [DRY RUN] Would run bug analysis here...")
        
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
    if not run_git_command_with_ai(['git', 'commit', '-m', commit_message], dry_run):
        return
    if not dry_run:
        click.echo("✓ Successfully committed.")

    # 5. Determine target branch
    target_branch = new_branch
    if not target_branch:
        if not dry_run:
            branch_result = run_git_command_with_ai(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            if not branch_result:
                return
            target_branch = branch_result.stdout.strip()
        else:
            target_branch = "current-branch"

    # 6. Show push preview and execute push
    click.echo(f"› Pushing to branch '{target_branch}'...")
    
    # Show push command preview
    show_push_preview(target_branch, new_branch)
    
    # Get the appropriate push command
    push_command = get_push_command(target_branch, new_branch)
    
    if not run_git_command_with_ai(push_command, dry_run):
        return
        
    if not dry_run:
        click.echo(f"✓ Successfully pushed!")
        
        # Show additional info for special repository types
        local_repo_config = app_config.get('_local_repository', {})
        if local_repo_config.get('type') == 'gerrit':
            click.echo("💡 代码已推送到 Gerrit，请查看代码评审页面")
        elif local_repo_config.get('type') == 'gitlab':
            click.echo("💡 代码已推送到 GitLab")
    else:
        click.secho("\n[DRY RUN COMPLETE] No actual changes were made.", fg="blue", bold=True) 