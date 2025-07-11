import subprocess
import click
import fnmatch
import os
import re
from pathlib import Path


def find_git_root(start_path=None):
    """
    查找 Git 项目根目录
    
    Args:
        start_path: 开始搜索的路径，默认为当前目录
    
    Returns:
        Path 对象指向 Git 根目录，如果没有找到则返回 None
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)
    
    current = start_path.resolve()
    
    # 向上查找直到找到 .git 目录
    while current != current.parent:
        git_dir = current / '.git'
        if git_dir.exists():
            return current
        current = current.parent
    
    return None


def ensure_git_root():
    """
    确保当前在 Git 项目根目录
    
    Returns:
        tuple: (git_root_path, original_cwd) 或 (None, None) 如果不在 Git 项目中
    """
    original_cwd = Path.cwd()
    git_root = find_git_root()
    
    if git_root is None:
        click.secho("Error: Not in a Git repository", fg="red")
        return None, None
    
    if git_root != original_cwd:
        click.echo(f"📁 Switching to Git root: {git_root}")
        os.chdir(git_root)
    
    return git_root, original_cwd


def get_current_branch():
    """获取当前Git分支名称"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # 如果上面的命令失败，尝试备用方法
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None


def get_remote_branches():
    """获取所有远程分支列表"""
    try:
        result = subprocess.run(
            ['git', 'branch', '-r'],
            capture_output=True,
            text=True,
            check=True
        )
        branches = []
        for line in result.stdout.splitlines():
            branch = line.strip()
            if branch and not branch.startswith('origin/HEAD'):
                branches.append(branch)
        return branches
    except subprocess.CalledProcessError:
        return []


def run_git_command(command, dry_run=False, ai_helper_func=None):
    """A helper to run a git command and handle errors, with AI assistance."""
    if dry_run:
        click.echo(f"[DRY RUN] Would execute: {' '.join(command)}")
        return True
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
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

        if ai_helper_func and click.confirm("\nDo you want to ask AI for a solution?", default=True):
            click.echo("› Asking AI for a solution...")
            solution = ai_helper_func(command, error_message)
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


def get_repository_info():
    """
    获取当前Git仓库的信息
    
    Returns:
        tuple: (repository_url, repository_name) 或 (None, None) 如果获取失败
    """
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'], 
            capture_output=True, text=True, check=True
        )
        repository_url = result.stdout.strip()
        
        # 提取仓库名
        repo_name_match = re.search(r'([^/]+?)(?:\.git)?$', repository_url)
        repository_name = repo_name_match.group(1) if repo_name_match else os.path.basename(repository_url)
        
        return repository_url, repository_name
    except subprocess.CalledProcessError:
        return None, None


def get_commit_hash():
    """
    获取最新的commit hash
    
    Returns:
        str: commit hash 或 None 如果获取失败
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], 
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None 