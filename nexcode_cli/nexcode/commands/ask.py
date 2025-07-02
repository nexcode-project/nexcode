import click
from ..api.client import api_client

@click.command()
@click.argument('question', required=True)
@click.option('--category', default='general', 
              help='Question category: git, code, workflow, best_practices, or general')
def ask(question, category):
    """向NexCode AI助手提问"""
    click.echo(f"🤔 正在处理您的问题: {question}")
    
    try:
        # 调用API服务进行智能问答
        result = api_client.ask_question(question, category)
        
        if 'error' in result:
            click.echo(f"❌ 问答失败: {result['error']}")
            return
        
        # 显示回答
        answer = result.get('answer', '抱歉，无法获取答案')
        click.echo(f"\n💬 回答:\n{answer}")
        
        # 显示相关主题
        related_topics = result.get('related_topics', [])
        if related_topics:
            click.echo(f"\n🔗 相关主题:")
            for i, topic in enumerate(related_topics, 1):
                click.echo(f"  {i}. {topic}")
        
        # 显示建议操作
        suggested_actions = result.get('suggested_actions', [])
        if suggested_actions:
            click.echo(f"\n💡 建议操作:")
            for i, action in enumerate(suggested_actions, 1):
                click.echo(f"  {i}. {action}")
        
    except Exception as e:
        click.echo(f"❌ 处理问题时出现错误: {str(e)}")
        raise click.ClickException(str(e)) 