import os
import shlex
import subprocess

import click

from ..api.client import api_client
from ..config import config as app_config
from ..utils.git import get_git_diff, smart_git_add, ensure_git_root, get_current_branch, get_remote_branches, get_repository_info, get_commit_hash


def run_git_command_with_ai(command, dry_run=False):
    """Git command wrapper that includes AI error assistance."""
    from ..utils.git import run_git_command
    
    def ai_helper(cmd, error_msg):
        return api_client.git_error_analysis(cmd, error_msg)
    
    return run_git_command(command, dry_run=dry_run, ai_helper_func=ai_helper)


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


def handle_push_command(new_branch, dry_run, style, check_bugs, no_check_bugs, debug=False):
    """Implementation of the push command."""
    
    # 确保在Git根目录执行
    git_root, original_cwd = ensure_git_root()
    if git_root is None:
        return
    
    try:
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
        
        # 获取git diff (检查暂存区的更改)
        diff = get_git_diff(staged=True)  # 检查暂存区的更改，因为已经执行了git add .
        if not diff:
            click.echo("❌ 没有发现代码变更")
            return

        # Determine if bug check should be run
        should_check_bugs = check_bugs or (
            app_config.get('commit', {}).get('check_bugs_by_default', False) and not no_check_bugs
        )

        # Run bug check if requested or configured by default
        if should_check_bugs and not dry_run:
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
                if not click.confirm("\nCode quality issues detected. Do you want to continue with the push?", default=False):
                    click.echo("Push cancelled due to code quality issues.")
                    return
            else:
                click.echo("✅ Code quality looks good!")
        elif should_check_bugs and dry_run:
            click.echo("› [DRY RUN] Would run bug analysis here...")
            
        # 3. Generate commit message
        used_style = style or app_config.get('commit', {}).get('style', 'conventional')
        click.echo(f"› Generating commit message with AI ({used_style} style)...")
        
        # Debug信息输出
        if debug:
            click.secho("\n🐛 DEBUG: LLM输入信息", fg="yellow", bold=True)
            click.echo("=" * 60)
            
            # 显示基本配置
            click.echo(f"提交风格: {used_style}")
            click.echo(f"模型配置: {app_config.get('model', {})}")
            click.echo(f"API服务器: {app_config.get('api_server', {})}")
            
            # 显示diff信息
            click.echo(f"\nDiff长度: {len(diff)} 字符")
            if len(diff) > 1000:
                click.echo("Diff预览 (前500字符):")
                click.echo(diff[:500])
                click.echo(f"... (还有 {len(diff) - 500} 字符)")
            else:
                click.echo("完整Diff内容:")
                click.echo(diff)
            
            # 显示上下文信息
            try:
                current_branch = get_current_branch()
                remote_url_result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                                                 capture_output=True, text=True, check=True)
                repository_url = remote_url_result.stdout.strip()
                
                context_info = {
                    'repository_url': repository_url,
                    'branch_name': current_branch,
                    'commit_style': used_style
                }
                click.echo(f"\n上下文信息: {context_info}")
            except:
                click.echo("\n上下文信息: 无法获取")
            
            click.echo("=" * 60)
            click.echo()
        
        if not dry_run:
            # 使用服务端API生成提交消息
            commit_message = api_client.generate_commit_message(diff, used_style)
        else:
            # Generate example message based on style for dry run
            style_examples = {
                'conventional': "[DRY RUN] feat: example conventional commit",
                'semantic': "[DRY RUN] Add example feature implementation",
                'simple': "[DRY RUN] Example feature added",
                'emoji': "[DRY RUN] ✨ Add example feature"
            }
            commit_message = style_examples.get(used_style, "[DRY RUN] feat: example commit message")

        if not commit_message or commit_message.startswith("Failed to connect") or commit_message.startswith("Error"):
            if not dry_run:
                click.echo(f"✗ Failed to generate commit message: {commit_message}")
                click.echo("Please check your server connection and configuration.")
                return
            # For dry run, continue with example message

        click.echo(f"✓ Generated commit message:\n  {commit_message}")
        
        # 4. Commit
        if not run_git_command_with_ai(['git', 'commit', '-m', commit_message], dry_run):
            return
        if not dry_run:
            click.echo("✓ Successfully committed.")

            # 保存Commit信息到服务器
            try:
                # 获取最新commit hash
                hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
                commit_hash = hash_result.stdout.strip()
            except subprocess.CalledProcessError:
                commit_hash = None

            # 获取仓库信息
            branch_name = target_branch
            try:
                remote_url_result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], capture_output=True, text=True, check=True)
                repository_url = remote_url_result.stdout.strip()
                import re, os
                repo_name_match = re.search(r'([^/]+?)(?:\.git)?$', repository_url)
                repository_name = repo_name_match.group(1) if repo_name_match else os.path.basename(repository_url)
            except subprocess.CalledProcessError:
                repository_url = None
                repository_name = None

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
    
    finally:
        # 切换回原始目录
        if original_cwd and original_cwd != git_root:
            os.chdir(original_cwd) 


@click.command()
@click.option('--branch', default=None, help='目标分支 (默认为origin/main)')
@click.option('--message', '-m', default=None, help='提交消息')
@click.option('--auto-commit', is_flag=True, help='自动生成提交消息并提交')
@click.option('--dry-run', is_flag=True, help='仅显示将要执行的操作，不实际执行')
@click.option('--debug', is_flag=True, help='显示详细的LLM输入调试信息')
def push(branch, message, auto_commit, dry_run, debug):
    """智能推送代码"""
    
    try:
        # 首先添加所有变更文件
        click.echo("📝 添加变更文件...")
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            click.echo("✅ 变更文件已添加到暂存区")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ 添加文件失败: {e}")
            return
        
        # 获取当前分支
        current_branch = get_current_branch()
        if not current_branch:
            click.echo("❌ 无法获取当前分支信息")
            return
        
        # 确定目标分支
        target_branch = branch or "main"
        
        # 获取git diff (检查暂存区的更改)
        diff = get_git_diff(staged=True)  # 检查暂存区的更改，因为已经执行了git add .
        if not diff:
            click.echo("❌ 没有发现代码变更")
            return
        
        click.echo(f"🚀 正在分析推送策略...")
        click.echo(f"当前分支: {current_branch}")
        click.echo(f"目标分支: {target_branch}")
        
        # Debug信息输出
        if debug:
            click.secho("\n🐛 DEBUG: LLM推送策略分析输入", fg="yellow", bold=True)
            click.echo("=" * 60)
            
            # 显示基本配置
            click.echo(f"模型配置: {app_config.get('model', {})}")
            click.echo(f"API服务器: {app_config.get('api_server', {})}")
            click.echo(f"当前分支: {current_branch}")
            click.echo(f"目标分支: {target_branch}")
            click.echo(f"仓库类型: github")
            
            # 显示diff信息
            click.echo(f"\nDiff长度: {len(diff)} 字符")
            if len(diff) > 1000:
                click.echo("Diff预览 (前500字符):")
                click.echo(diff[:500])
                click.echo(f"... (还有 {len(diff) - 500} 字符)")
            else:
                click.echo("完整Diff内容:")
                click.echo(diff)
            
            # 显示上下文信息
            try:
                remote_url_result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                                                 capture_output=True, text=True, check=True)
                repository_url = remote_url_result.stdout.strip()
                
                context_info = {
                    'repository_url': repository_url,
                    'current_branch': current_branch,
                    'target_branch': target_branch,
                    'repository_type': 'github'
                }
                click.echo(f"\n完整请求参数: {context_info}")
            except:
                click.echo("\n仓库信息: 无法获取")
            
            click.echo("=" * 60)
            click.echo()
        
        # 调用API服务进行推送策略分析
        result = api_client.analyze_push_strategy(
            diff=diff,
            target_branch=target_branch,
            current_branch=current_branch,
            repository_type="github"  # 可以从配置中获取
        )
        
        if 'error' in result:
            click.echo(f"❌ 推送策略分析失败: {result['error']}")
            return
        
        # 获取推荐的提交消息
        suggested_message = result.get('commit_message', 'Auto-generated commit message')
        
        # 清理提交消息，确保简洁
        suggested_message = clean_commit_message(suggested_message)
        
        push_command = result.get('push_command', f'git push origin {current_branch}')
        pre_push_checks = result.get('pre_push_checks', [])
        warnings = result.get('warnings', [])
        
        # 显示推送策略
        click.echo(f"\n📋 推送策略:")
        click.echo(f"建议提交消息: {suggested_message}")
        click.echo(f"推送命令: {push_command}")
        
        # 显示预检查项
        if pre_push_checks:
            click.echo(f"\n✅ 推送前检查项:")
            for i, check in enumerate(pre_push_checks, 1):
                click.echo(f"  {i}. {check}")
        
        # 显示警告
        if warnings:
            click.echo(f"\n⚠️  警告:")
            for warning in warnings:
                click.echo(f"  • {warning}")
        
        if dry_run:
            click.echo(f"\n🏃 Dry Run模式 - 不会实际执行推送")
            return
        
        # 处理提交
        if auto_commit or not message:
            final_message = message or suggested_message
            
            # 确认提交消息
            if not auto_commit:
                if not click.confirm(f"使用建议的提交消息吗?\n消息: {final_message}"):
                    final_message = click.prompt("请输入提交消息")
            
            # 执行提交
            try:
                # 确保提交消息是UTF-8编码
                final_message = final_message.encode('utf-8').decode('utf-8')
                subprocess.run(['git', 'commit', '-m', final_message], 
                             check=True, encoding='utf-8')
                click.echo(f"✅ 代码已提交: {final_message}")
                
                # 保存Commit信息到服务器
                commit_hash = get_commit_hash()
                repository_url, repository_name = get_repository_info()

                commit_payload = {
                    'repository_url': repository_url,
                    'repository_name': repository_name,
                    'branch_name': current_branch,
                    'commit_hash': commit_hash,
                    'ai_generated_message': final_message,
                    'final_commit_message': final_message,
                    'diff_content': diff,
                    'commit_style': 'conventional',
                    'status': 'committed'
                }
                save_result = api_client.create_commit_info(commit_payload)
                if 'error' in save_result:
                    click.echo(f"⚠️  无法保存Commit信息: {save_result['error']}")
                else:
                    click.echo("📦 Commit信息已保存到服务器")
                    
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ 提交失败: {e}")
                return
        
        # 确认推送
        if click.confirm(f"执行推送吗?\n命令: {push_command}"):
            try:
                # 解析推送命令并执行
                cmd_parts = push_command.split()
                subprocess.run(cmd_parts, check=True)
                click.echo("✅ 代码推送成功!")
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ 推送失败: {e}")
                return
        else:
            click.echo("推送已取消")
        
    except Exception as e:
        click.echo(f"❌ 推送过程中出现错误: {str(e)}")
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
    
    # 如果没有conventional commits格式，尝试添加
    if not any(first_line.startswith(prefix) for prefix in ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:']):
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