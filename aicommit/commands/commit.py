import click
from ..config import config as app_config
from ..utils.git import get_git_diff
from ..llm.services import check_code_for_bugs
from ..prompt.generators import generate_commit_message
from ..llm.services import get_ai_solution_for_git_error


def run_git_command_with_ai(command, dry_run=False):
    """Git command wrapper that includes AI error assistance."""
    from ..utils.git import run_git_command
    return run_git_command(command, dry_run=dry_run, ai_helper_func=get_ai_solution_for_git_error)


def handle_commit_command(dry_run, preview, style, check_bugs, no_check_bugs):
    """Implementation of the commit command."""
    click.echo("› Checking for staged changes...")
    diff = get_git_diff(staged=True)
    
    if not diff:
        click.echo("No staged changes found. Use 'git add <files>' to stage your changes first.")
        return

    # Determine if bug check should be run
    should_check_bugs = check_bugs or (
        app_config.get('commit', {}).get('check_bugs_by_default', False) and not no_check_bugs
    )

    # Run bug check if requested or configured by default
    if should_check_bugs:
        click.echo("› Running bug analysis...")
        analysis = check_code_for_bugs(diff)
        
        click.secho("\n🔍 Bug Analysis Results:", fg="blue", bold=True)
        click.echo("-" * 40)
        click.echo(analysis)
        click.echo("-" * 40)
        
        # Ask user if they want to continue
        if "No significant issues detected" not in analysis:
            if not click.confirm("\nIssues detected. Do you want to continue with the commit?", default=False):
                click.echo("Commit cancelled due to code issues.")
                return
        else:
            click.echo("✅ No significant issues detected!")

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
            result = run_git_command_with_ai(['git', 'commit', '-m', commit_message])
            if result:
                click.echo("✓ Successfully committed.")
        else:
            click.echo("Commit aborted by user.")
    else:
        click.echo("✗ Failed to generate commit message. Aborting.") 