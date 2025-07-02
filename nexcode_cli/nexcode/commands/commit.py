import os
import click
import subprocess
from ..config import config as app_config
from ..utils.git import get_git_diff, ensure_git_root
from ..api.client import api_client



def run_git_command_with_ai(command, dry_run=False):
    """Git command wrapper that includes AI error assistance."""
    from ..utils.git import run_git_command
    
    def ai_helper(cmd, error_msg):
        return api_client.git_error_analysis(cmd, error_msg)
    
    return run_git_command(command, dry_run=dry_run, ai_helper_func=ai_helper)


def handle_commit_command(dry_run, preview, style, check_bugs, no_check_bugs):
    """Implementation of the commit command."""
    
    # 确保在Git根目录执行
    git_root, original_cwd = ensure_git_root()
    if git_root is None:
        return
    
    try:
        click.echo("› Checking for staged changes...")
        # run git add .
        run_git_command_with_ai(['git', 'add', '.'])
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
            click.echo("› Running comprehensive code quality analysis...")
            quality_result = api_client.code_quality_check(diff)
            
            click.secho("\n🔍 Code Quality Analysis Results:", fg="blue", bold=True)
            click.echo("-" * 40)
            analysis = quality_result.get("summary", "No analysis available")
            click.echo(analysis)
            overall_score = quality_result.get("overall_score", 0.0)
            click.echo(f"\nOverall Quality Score: {overall_score}/10.0")
            click.echo("-" * 40)
            
            # Ask user if they want to continue based on score
            if overall_score < 6.0:
                if not click.confirm("\nCode quality issues detected. Do you want to continue with the commit?", default=False):
                    click.echo("Commit cancelled due to code quality issues.")
                    return
            else:
                click.echo("✅ Code quality looks good!")

        # Show which style is being used
        used_style = style or app_config.get('commit', {}).get('style', 'conventional')
        click.echo(f"› Generating commit message with AI ({used_style} style)...")
        
        # 使用服务端API生成提交消息
        commit_message = api_client.generate_commit_message(diff, used_style)

        if commit_message and not commit_message.startswith("Failed to connect") and not commit_message.startswith("Error"):
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
            click.echo(f"✗ Failed to generate commit message: {commit_message}")
            click.echo("Please check your server connection and configuration.")
    
    finally:
        # 切换回原始目录
        if original_cwd and original_cwd != git_root:
            os.chdir(original_cwd)


@click.command()
@click.option('--message', '-m', help='直接指定提交消息')
@click.option('--style', default='conventional', 
              help='提交消息风格: conventional, simple, detailed')
@click.option('--auto', is_flag=True, help='自动生成消息并提交')
def commit(message, style, auto):
    """智能生成提交消息并提交代码"""
    
    try:
        # 获取git diff
        diff = get_git_diff()
        if not diff:
            click.echo("❌ 没有发现代码变更")
            return
        
        if message:
            # 使用用户提供的消息
            final_message = message
        else:
            # 生成提交消息
            click.echo("🤖 正在生成智能提交消息...")
            
            result = api_client.generate_commit_message(
                diff=diff,
                style=style,
                context={}
            )
            
            if 'error' in result:
                click.echo(f"❌ 生成提交消息失败: {result['error']}")
                return
            
            suggested_message = result.get('message', 'Auto-generated commit message')
            click.echo(f"💡 建议的提交消息: {suggested_message}")
            
            if auto:
                final_message = suggested_message
            else:
                if click.confirm("使用这个提交消息吗?"):
                    final_message = suggested_message
                else:
                    final_message = click.prompt("请输入自定义提交消息")
        
        # 执行提交
        try:
            # 添加所有变更文件
            subprocess.run(['git', 'add', '.'], check=True)
            
            # 提交
            subprocess.run(['git', 'commit', '-m', final_message], check=True)
            
            click.echo(f"✅ 代码已成功提交!")
            click.echo(f"📝 提交消息: {final_message}")
            
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ 提交失败: {e}")
            return
        
    except Exception as e:
        click.echo(f"❌ 提交过程中出现错误: {str(e)}")
        raise click.ClickException(str(e)) 