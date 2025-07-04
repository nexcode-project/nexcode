import os
import click
import subprocess
from ..config import config as app_config
from ..utils.git import get_git_diff, ensure_git_root, get_current_branch
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

                    # 获取最新commit hash
                    try:
                        hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
                        commit_hash = hash_result.stdout.strip()
                    except subprocess.CalledProcessError:
                        commit_hash = None

                    # 获取当前分支和远程仓库信息
                    branch_name = get_current_branch() or ''
                    try:
                        remote_url_result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], capture_output=True, text=True, check=True)
                        repository_url = remote_url_result.stdout.strip()
                        # 提取仓库名
                        import re, os
                        repo_name_match = re.search(r'([^/]+?)(?:\.git)?$', repository_url)
                        repository_name = repo_name_match.group(1) if repo_name_match else os.path.basename(repository_url)
                    except subprocess.CalledProcessError:
                        repository_url = None
                        repository_name = None

                    # 调用后端API保存commit信息
                    commit_payload = {
                        'repository_url': repository_url,
                        'repository_name': repository_name,
                        'branch_name': branch_name,
                        'commit_hash': commit_hash,
                        'ai_generated_message': commit_message,
                        'final_commit_message': commit_message,
                        'diff_content': diff,
                        'commit_style': used_style,
                        'status': 'committed'
                    }
                    save_result = api_client.create_commit_info(commit_payload)
                    if 'error' in save_result:
                        click.echo(f"⚠️  无法保存Commit信息: {save_result['error']}")
                    else:
                        click.echo("📦 Commit信息已保存到服务器")
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
        # 首先添加所有变更文件
        click.echo("📝 添加变更文件...")
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            click.echo("✅ 变更文件已添加到暂存区")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ 添加文件失败: {e}")
            return
        
        # 获取git diff
        diff = get_git_diff(staged=True)
        if not diff:
            click.echo("❌ 没有发现代码变更")
            return
        
        if message:
            # 使用用户提供的消息
            final_message = message
        else:
            # 生成提交消息
            click.echo("🤖 正在生成智能提交消息...")
            
            suggested_message = api_client.generate_commit_message(
                diff=diff,
                style=style,
                context={}
            )
            
            if suggested_message.startswith("Error"):
                click.echo(f"❌ 生成提交消息失败: {suggested_message}")
                return
            
            # 清理提交消息，确保简洁
            suggested_message = clean_commit_message(suggested_message)
            
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


def clean_commit_message(message):
    """清理提交消息，确保简洁适合Git提交"""
    if not message:
        return "feat: update code"
    
    # 移除可能的JSON标记
    message = message.replace('```json', '').replace('```', '').strip()
    
    # 尝试解析JSON（如果LLM返回了JSON格式）
    import json
    try:
        parsed = json.loads(message)
        if isinstance(parsed, dict) and 'commit_message' in parsed:
            message = parsed['commit_message']
        elif isinstance(parsed, dict) and 'message' in parsed:
            message = parsed['message']
    except:
        pass  # 不是JSON，继续处理纯文本
    
    # 只取第一行作为提交消息
    lines = message.strip().split('\n')
    first_line = lines[0].strip()
    
    # 移除引号和其他格式标记
    first_line = first_line.strip('"\'`')
    
    # 如果包含JSON结构标记，提取实际消息
    if '{' in first_line or '}' in first_line:
        # 尝试提取引号中的内容
        import re
        match = re.search(r'["\']([^"\']+)["\']', first_line)
        if match:
            first_line = match.group(1)
        else:
            # 如果没有找到，使用默认消息
            first_line = "chore: update code"
    
    # 如果第一行太长，截断到合理长度
    if len(first_line) > 72:
        first_line = first_line[:69] + "..."
    
    # 检查是否已有conventional commits格式
    has_conventional_format = any(first_line.startswith(prefix) for prefix in ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:'])
    
    # 如果没有conventional commits格式，尝试添加
    if not has_conventional_format:
        # 简单判断类型
        if 'fix' in first_line.lower() or 'bug' in first_line.lower():
            first_line = f"fix: {first_line}"
        elif 'add' in first_line.lower() or 'new' in first_line.lower():
            first_line = f"feat: {first_line}"
        elif 'update' in first_line.lower() or 'modify' in first_line.lower():
            first_line = f"refactor: {first_line}"
        else:
            first_line = f"chore: {first_line}"
    
    return first_line 