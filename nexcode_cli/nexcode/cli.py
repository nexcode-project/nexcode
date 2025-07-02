import click
from .commands.commit import commit
from .commands.push import push
from .commands.config_cmd import handle_config_command
from .commands.check import check
from .commands.ask import ask
from .commands.diagnose import diagnose
from .commands.status import status


@click.group()
def cli():
    """NexCode AI Assistant: 智能Git代码助手"""
    pass


# 注册新的命令
cli.add_command(commit)
cli.add_command(push)
cli.add_command(check)
cli.add_command(ask)
cli.add_command(diagnose)
cli.add_command(status)


# Config命令仍然使用旧的handle函数模式
@cli.command()
@click.option('--set', 'config_set', help='设置配置值 (格式: key=value)')
@click.option('--get', 'config_get', help='获取配置值')
@click.option('--list', 'list_config', is_flag=True, help='列出所有配置值')
@click.option('-i', '--interactive', is_flag=True, help='启动交互式配置模式')
@click.option('--init-local', is_flag=True, help='初始化本地仓库配置')
def config(config_set, config_get, list_config, interactive, init_local):
    """管理NexCode配置"""
    handle_config_command(config_set, config_get, list_config, interactive, init_local)


if __name__ == '__main__':
    cli() 