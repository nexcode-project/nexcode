import click
from ..config import config as app_config
from ..utils.git import get_git_diff, smart_git_add
from ..llm.services import check_code_for_bugs
from ..prompt.generators import generate_commit_message
from ..llm.services import get_ai_solution_for_git_error


def run_git_command_with_ai(command, dry_run=False):
    """Git command wrapper that includes AI error assistance."""
    from ..utils.git import run_git_command
    return run_git_command(command, dry_run=dry_run, ai_helper_func=get_ai_solution_for_git_error)


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

    # 5. Push to remote
    target_branch = new_branch
    if not target_branch:
        if not dry_run:
            branch_result = run_git_command_with_ai(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            if not branch_result:
                return
            target_branch = branch_result.stdout.strip()
        else:
            target_branch = "current-branch"

    click.echo(f"› Pushing to branch '{target_branch}'...")
    push_command = ['git', 'push', '--set-upstream', 'origin', target_branch]
    if not run_git_command_with_ai(push_command, dry_run):
        return
        
    if not dry_run:
        click.echo(f"✓ Successfully pushed to 'origin/{target_branch}'.")
    else:
        click.secho("\n[DRY RUN COMPLETE] No actual changes were made.", fg="blue", bold=True) 