import os
import shlex
import subprocess
import click
from typing import List, Optional, Tuple

from ..api.client import api_client
from ..config import config as app_config
from ..utils.git import (
    get_git_diff, smart_git_add, ensure_git_root, get_current_branch, 
    get_remote_branches, get_repository_info, get_commit_hash, run_git_command
)


def get_available_branches() -> Tuple[List[str], List[str]]:
    """获取本地和远程分支列表"""
    try:
        # 获取本地分支
        local_result = subprocess.run(
            ['git', 'branch', '--format=%(refname:short)'], 
            capture_output=True, text=True, check=True
        )
        local_branches = [b.strip() for b in local_result.stdout.strip().split('\n') if b.strip()]
        
        # 获取远程分支
        remote_result = subprocess.run(
            ['git', 'branch', '-r', '--format=%(refname:short)'], 
            capture_output=True, text=True, check=True
        )
        remote_branches = []
        for branch in remote_result.stdout.strip().split('\n'):
            if branch.strip() and not branch.startswith('origin/HEAD'):
                # 移除 origin/ 前缀
                clean_branch = branch.replace('origin/', '').strip()
                if clean_branch not in remote_branches:
                    remote_branches.append(clean_branch)
        
        return local_branches, remote_branches
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 获取分支信息失败: {e}")
        return [], []


def select_branch(branches: List[str], prompt: str, allow_new: bool = True) -> str:
    """让用户选择分支或输入新分支名"""
    if not branches:
        if allow_new:
            return click.prompt(prompt)
        else:
            click.echo("❌ 没有可用的分支")
            return ""
    
    # 显示分支列表
    click.echo(f"\n📋 {prompt}:")
    for i, branch in enumerate(branches, 1):
        click.echo(f"  {i}. {branch}")
    
    if allow_new:
        click.echo(f"  {len(branches) + 1}. 输入新分支名")
    
    while True:
        try:
            choice = click.prompt("请选择分支", type=int)
            if 1 <= choice <= len(branches):
                return branches[choice - 1]
            elif choice == len(branches) + 1 and allow_new:
                return click.prompt("请输入新分支名")
            else:
                click.echo("❌ 无效选择，请重试")
        except ValueError:
            click.echo("❌ 请输入数字")
        except click.Abort:
            return ""


def create_and_switch_branch(branch_name: str, dry_run: bool = False) -> bool:
    """创建并切换到新分支"""
    try:
        if dry_run:
            click.echo(f"[DRY RUN] 将创建并切换到分支: {branch_name}")
            return True
        
        # 创建并切换到新分支
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        click.echo(f"✅ 已创建并切换到分支: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 创建分支失败: {e}")
        return False


def merge_branch(source_branch: str, target_branch: str, dry_run: bool = False) -> bool:
    """合并分支"""
    try:
        if dry_run:
            click.echo(f"[DRY RUN] 将合并 {source_branch} 到 {target_branch}")
            return True
        
        # 切换到目标分支
        subprocess.run(['git', 'checkout', target_branch], check=True)
        click.echo(f"✅ 已切换到目标分支: {target_branch}")
        
        # 拉取最新代码
        subprocess.run(['git', 'pull', 'origin', target_branch], check=True)
        click.echo(f"✅ 已拉取 {target_branch} 最新代码")
        
        # 合并源分支
        subprocess.run(['git', 'merge', source_branch], check=True)
        click.echo(f"✅ 已成功合并 {source_branch} 到 {target_branch}")
        
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 合并失败: {e}")
        return False


def push_branch(branch_name: str, remote: str = 'origin', dry_run: bool = False) -> bool:
    """推送分支到远程"""
    try:
        if dry_run:
            click.echo(f"[DRY RUN] 将推送 {branch_name} 到 {remote}")
            return True
        
        # 推送分支
        subprocess.run(['git', 'push', remote, branch_name], check=True)
        click.echo(f"✅ 已推送 {branch_name} 到 {remote}")
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 推送失败: {e}")
        return False


def delete_branch(branch_name: str, remote: bool = False, dry_run: bool = False) -> bool:
    """删除分支"""
    try:
        if dry_run:
            click.echo(f"[DRY RUN] 将删除{'远程' if remote else '本地'}分支: {branch_name}")
            return True
        
        if remote:
            subprocess.run(['git', 'push', 'origin', '--delete', branch_name], check=True)
            click.echo(f"✅ 已删除远程分支: {branch_name}")
        else:
            subprocess.run(['git', 'branch', '-d', branch_name], check=True)
            click.echo(f"✅ 已删除本地分支: {branch_name}")
        
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 删除分支失败: {e}")
        return False


def analyze_push_strategy(diff: str, current_branch: str, target_branch: str, repository_type: str = "github"):
    """分析推送策略"""
    try:
        result = api_client.analyze_push_strategy(
            diff=diff,
            target_branch=target_branch,
            current_branch=current_branch,
            repository_type=repository_type
        )
        
        if 'error' in result:
            click.echo(f"❌ 推送策略分析失败: {result['error']}")
            return None
        
        return result
    except Exception as e:
        click.echo(f"❌ 推送策略分析异常: {e}")
        return None


def clean_commit_message(message: str) -> str:
    """清理提交消息"""
    if not message:
        return "feat: update code"
    
    # 移除可能的JSON标记
    message = message.replace('```json', '').replace('```', '').strip()
    
    # 尝试解析JSON
    import json
    try:
        parsed = json.loads(message)
        if isinstance(parsed, dict) and 'commit_message' in parsed:
            message = parsed['commit_message']
        elif isinstance(parsed, dict) and 'message' in parsed:
            message = parsed['message']
    except:
        pass
    
    return message


def clean_user_commit_message(message: str) -> str:
    """清理用户编辑的提交消息"""
    if not message or message.strip() == "":
        return ""
    
    cleaned = message.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
    
    if cleaned.startswith("{") and cleaned.endswith("}"):
        try:
            import json
            data = json.loads(cleaned)
            if "commit_message" in data:
                cleaned = data["commit_message"]
        except:
            pass
    
    return cleaned


@click.command()
@click.option('--source-branch', '-s', help='源分支 (默认为当前分支)')
@click.option('--target-branch', '-t', help='目标分支')
@click.option('--new-branch', '-n', help='创建新分支名')
@click.option('--message', '-m', help='提交消息')
@click.option('--auto-commit', is_flag=True, help='自动生成提交消息并提交')
@click.option('--merge', is_flag=True, help='推送后合并到目标分支')
@click.option('--delete-source', is_flag=True, help='推送后删除源分支')
@click.option('--dry-run', is_flag=True, help='仅显示将要执行的操作，不实际执行')
@click.option('--debug', is_flag=True, help='显示详细的调试信息')
def push_enhanced(source_branch, target_branch, new_branch, message, auto_commit, merge, delete_source, dry_run, debug):
    """增强版智能推送代码 - 支持分支推送和合并选择"""
    
    # 确保在Git根目录执行
    git_root, original_cwd = ensure_git_root()
    if git_root is None:
        return
    
    try:
        if dry_run:
            click.secho("[DRY RUN MODE] 预览操作:", fg="blue", bold=True)
        
        # 获取当前分支
        current_branch = get_current_branch()
        if not current_branch:
            click.echo("❌ 无法获取当前分支信息")
            return
        
        # 获取可用分支
        local_branches, remote_branches = get_available_branches()
        all_branches = list(set(local_branches + remote_branches))
        
        # 确定源分支
        source_branch = source_branch or current_branch
        if source_branch not in local_branches:
            click.echo(f"❌ 源分支 '{source_branch}' 不存在")
            return
        
        # 如果指定了创建新分支
        if new_branch:
            if not create_and_switch_branch(new_branch, dry_run):
                return
            source_branch = new_branch
            current_branch = new_branch
        
        # 添加所有变更文件
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
        
        # 确定目标分支
        if not target_branch:
            if merge:
                # 如果选择合并，让用户选择目标分支
                target_branch = select_branch(all_branches, "选择要合并到的目标分支", allow_new=False)
                if not target_branch:
                    click.echo("❌ 未选择目标分支")
                    return
            else:
                # 默认推送到同名远程分支
                target_branch = source_branch
        
        # 分析推送策略
        click.echo(f"🚀 正在分析推送策略...")
        click.echo(f"源分支: {source_branch}")
        click.echo(f"目标分支: {target_branch}")
        
        if debug:
            click.secho("\n🐛 DEBUG: 推送策略分析", fg="yellow", bold=True)
            click.echo(f"Diff长度: {len(diff)} 字符")
            click.echo(f"源分支: {source_branch}")
            click.echo(f"目标分支: {target_branch}")
        
        # 调用API分析推送策略
        strategy_result = analyze_push_strategy(diff, source_branch, target_branch)
        if not strategy_result:
            # 使用默认策略
            suggested_message = "feat: update code"
            push_command = f"git push origin {source_branch}"
            pre_push_checks = ["检查代码质量", "运行测试"]
            warnings = []
        else:
            suggested_message = clean_commit_message(strategy_result.get('commit_message', 'feat: update code'))
            push_command = strategy_result.get('push_command', f'git push origin {source_branch}')
            pre_push_checks = strategy_result.get('pre_push_checks', [])
            warnings = strategy_result.get('warnings', [])
        
        # 显示推送策略
        click.echo(f"\n📋 推送策略:")
        click.echo(f"建议提交消息: {suggested_message}")
        click.echo(f"推送命令: {push_command}")
        
        if pre_push_checks:
            click.echo(f"\n✅ 推送前检查项:")
            for i, check in enumerate(pre_push_checks, 1):
                click.echo(f"  {i}. {check}")
        
        if warnings:
            click.echo(f"\n⚠️  警告:")
            for warning in warnings:
                click.echo(f"  • {warning}")
        
        if dry_run:
            click.echo(f"\n🏃 Dry Run模式 - 不会实际执行")
            return
        
        # 处理提交
        if auto_commit or not message:
            final_message = message or suggested_message
            
            if not auto_commit:
                click.echo(f"\n📝 建议的提交消息: {suggested_message}")
                if click.confirm("是否使用建议的提交消息?"):
                    final_message = suggested_message
                else:
                    custom_message = click.prompt("请输入提交消息", default=suggested_message)
                    if custom_message and custom_message.strip():
                        final_message = clean_user_commit_message(custom_message.strip())
                    else:
                        final_message = suggested_message
            
            # 执行提交
            try:
                subprocess.run(['git', 'commit', '-m', final_message], check=True, encoding='utf-8')
                click.echo(f"✅ 代码已提交: {final_message}")
                
                # 保存Commit信息到服务器
                commit_hash = get_commit_hash()
                repository_url, repository_name = get_repository_info()
                
                commit_payload = {
                    'repository_url': repository_url,
                    'repository_name': repository_name,
                    'branch_name': source_branch,
                    'commit_hash': commit_hash,
                    'ai_generated_message': suggested_message,
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
        
        # 推送分支
        if click.confirm(f"推送分支 {source_branch} 到远程吗?"):
            if not push_branch(source_branch, dry_run=dry_run):
                return
        
        # 合并分支（如果选择）
        if merge and source_branch != target_branch:
            if click.confirm(f"合并 {source_branch} 到 {target_branch} 吗?"):
                if not merge_branch(source_branch, target_branch, dry_run=dry_run):
                    return
                
                # 推送合并后的目标分支
                if click.confirm(f"推送合并后的 {target_branch} 到远程吗?"):
                    if not push_branch(target_branch, dry_run=dry_run):
                        return
        
        # 删除源分支（如果选择）
        if delete_source and source_branch != target_branch:
            if click.confirm(f"删除源分支 {source_branch} 吗?"):
                # 删除本地分支
                if not delete_branch(source_branch, remote=False, dry_run=dry_run):
                    return
                
                # 删除远程分支
                if click.confirm(f"删除远程分支 {source_branch} 吗?"):
                    if not delete_branch(source_branch, remote=True, dry_run=dry_run):
                        return
        
        click.echo("✅ 推送操作完成!")
        
    except Exception as e:
        click.echo(f"❌ 推送过程中出现错误: {str(e)}")
        raise click.ClickException(str(e))
    
    finally:
        # 切换回原始目录
        if original_cwd and original_cwd != git_root:
            os.chdir(original_cwd)


if __name__ == "__main__":
    push_enhanced() 