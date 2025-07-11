import os
import subprocess
import time

import click

from ..api.client import api_client
from ..utils.git import get_git_diff, ensure_git_root

@click.command()
@click.option('--type', 'check_type', default='all', 
              help='Check type: bugs, security, performance, style, or all')
@click.option('--files', default=None, 
              help='Specific files to check (comma-separated)')
def check(check_type, files):
    """检查代码质量"""
    click.echo("🔍 正在进行代码质量检查...")
    
    try:
        # 获取git diff
        diff = get_git_diff()
        if not diff:
            click.echo("❌ 没有发现代码变更")
            return
        
        # 处理文件列表
        file_list = []
        if files:
            file_list = [f.strip() for f in files.split(',')]
        
        # 处理检查类型
        check_types = []
        if check_type == 'all':
            check_types = ['bugs', 'security', 'performance', 'style']
        else:
            check_types = [check_type]
        
        # 调用API服务进行代码质量检查
        result = api_client.check_code_quality(diff, file_list, check_types)
        
        if 'error' in result:
            click.echo(f"❌ 检查失败: {result['error']}")
            return
        
        # 显示检查结果
        click.echo(f"\n📊 代码质量评分: {result.get('overall_score', 0):.1f}/10")
        click.echo(f"📝 总结: {result.get('summary', '检查完成')}")
        
        # 显示问题列表
        issues = result.get('issues', [])
        if issues:
            click.echo(f"\n❗ 发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                issue_type = issue.get('type', 'unknown')
                message = issue.get('message', 'No message')
                click.echo(f"  {i}. [{issue_type.upper()}] {message}")
        
        # 显示建议
        suggestions = result.get('suggestions', [])
        if suggestions:
            click.echo(f"\n💡 建议:")
            for i, suggestion in enumerate(suggestions, 1):
                click.echo(f"  {i}. {suggestion}")
        
        if not issues and not suggestions:
            click.echo("\n✅ 代码质量良好，没有发现问题！")
        
    except Exception as e:
        click.echo(f"❌ 检查过程中出现错误: {str(e)}")
        raise click.ClickException(str(e))


def handle_check_command(staged, check_all, target_file):
    """Implementation of the check command."""
    
    # 确保在Git根目录执行
    git_root, original_cwd = ensure_git_root()
    if git_root is None:
        return
    
    try:
        if target_file:
            # Check specific file
            click.echo(f"› Analyzing file: {target_file}")
            try:
                result = subprocess.run(['git', 'diff', target_file], 
                                      capture_output=True, text=True, check=True)
                diff = result.stdout
                files = [target_file]
            except subprocess.CalledProcessError:
                click.echo(f"Error: Could not get diff for {target_file}")
                return
        elif check_all:
            # Check all unstaged changes
            click.echo("› Analyzing all unstaged changes...")
            diff = get_git_diff(staged=False)
            files = []
        else:
            # Check staged changes (default)
            click.echo("› Analyzing staged changes...")
            diff = get_git_diff(staged=True)
            files = []
        
        if not diff:
            click.echo("No changes found to analyze.")
            return
        
        click.echo("› Running comprehensive code quality analysis...")
        
        # Show a simple progress indicator
        for i in range(3):
            click.echo("  " + "." * (i + 1), nl=False)
            time.sleep(0.5)
        click.echo("")
        
        # 使用专门的代码质量检查服务
        analysis_result = api_client.check_code_quality(
            diff=diff,
            files=files,
            check_types=["bugs", "security", "performance", "style"]
        )
        
        # 显示分析结果
        click.secho("\n🔍 Code Quality Analysis Results:", fg="blue", bold=True)
        click.echo("=" * 60)
        
        # 显示总体评分
        overall_score = analysis_result.get("overall_score", 0.0)
        if overall_score >= 8.0:
            score_color = "green"
            score_icon = "✅"
        elif overall_score >= 6.0:
            score_color = "yellow"
            score_icon = "⚠️"
        else:
            score_color = "red"
            score_icon = "❌"
        
        click.secho(f"{score_icon} Overall Quality Score: {overall_score}/10.0", 
                   fg=score_color, bold=True)
        
        # 显示详细分析
        summary = analysis_result.get("summary", "No detailed analysis available.")
        click.echo(f"\n📋 Analysis Summary:")
        click.echo(summary)
        
        # 显示问题列表
        issues = analysis_result.get("issues", [])
        if issues:
            click.echo(f"\n⚠️  Issues Found ({len(issues)}):")
            for i, issue in enumerate(issues[:5], 1):  # 只显示前5个问题
                click.echo(f"  {i}. {issue}")
            if len(issues) > 5:
                click.echo(f"  ... and {len(issues) - 5} more issues")
        
        # 显示建议
        suggestions = analysis_result.get("suggestions", [])
        if suggestions:
            click.echo(f"\n💡 Suggestions:")
            for suggestion in suggestions[:3]:  # 只显示前3个建议
                click.echo(f"  • {suggestion}")
        
        click.echo("=" * 60)
        
        # 根据评分给出建议
        if overall_score < 6.0:
            click.secho("❌ Consider reviewing and fixing issues before committing.", fg="red")
        elif overall_score < 8.0:
            click.secho("⚠️  Code quality is acceptable but could be improved.", fg="yellow")
        else:
            click.secho("✅ Excellent code quality! Ready to commit.", fg="green")
    
    finally:
        # 切换回原始目录
        if original_cwd and original_cwd != git_root:
            os.chdir(original_cwd) 