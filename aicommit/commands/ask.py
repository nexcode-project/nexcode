import click
from ..llm.services import ask_ai_about_commits


def handle_ask_command(question, interactive):
    """Implementation of the ask command."""
    
    if interactive:
        # Interactive mode - keep asking questions until user exits
        click.echo("🤖 AI Git Assistant - Interactive Mode")
        click.echo("Ask me anything about Git commits, version control, or development workflows!")
        click.echo("Type 'exit', 'quit', or press Ctrl+C to stop.\n")
        
        while True:
            try:
                user_question = click.prompt("❓ Your question", type=str)
                
                if user_question.lower() in ['exit', 'quit', 'q']:
                    click.echo("👋 Goodbye! Happy coding!")
                    break
                
                if not user_question.strip():
                    click.echo("Please enter a question.")
                    continue
                
                click.echo("\n🤔 Let me think about this...")
                
                # Show a simple progress indicator
                import time
                for i in range(3):
                    click.echo("  " + "." * (i + 1), nl=False)
                    time.sleep(0.3)
                click.echo("")
                
                # Get AI response
                answer = ask_ai_about_commits(user_question)
                
                click.secho("\n💡 AI Assistant Response:", fg="green", bold=True)
                click.echo("=" * 50)
                click.echo(answer)
                click.echo("=" * 50)
                click.echo()
                
            except KeyboardInterrupt:
                click.echo("\n👋 Goodbye! Happy coding!")
                break
            except Exception as e:
                click.echo(f"\nError: {e}")
                continue
    
    else:
        # Single question mode
        if not question:
            click.echo("Error: Please provide a question using --question or use --interactive mode.")
            return
        
        click.echo(f"❓ Question: {question}")
        click.echo("\n🤔 Getting AI response...")
        
        # Show a simple progress indicator
        import time
        for i in range(3):
            click.echo("  " + "." * (i + 1), nl=False)
            time.sleep(0.3)
        click.echo("")
        
        # Get AI response
        answer = ask_ai_about_commits(question)
        
        click.secho("\n💡 AI Assistant Response:", fg="green", bold=True)
        click.echo("=" * 60)
        click.echo(answer)
        click.echo("=" * 60) 