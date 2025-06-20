from ..llm.client import get_openai_client
from ..config import config as app_config


def get_commit_style_prompt(style, diff):
    """Generate style-specific prompts for commit messages."""
    
    common_instructions = f"""
    Based on the following git diff, please generate a commit message.
    The message should be concise and descriptive, and should not be too long.
    The message only contains the commit message, no other text.
    The message should be in English.
    The message should be only one line.

    Git Diff:
    ---
    {diff}
    ---
    """
    
    if style == "conventional":
        return f"""
        {common_instructions}
        
        Use the Conventional Commits specification.
        Start with a type like 'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', followed by a short description in lower case.
        Examples:
        - feat: add user authentication
        - fix: resolve database connection issue
        - docs: update installation guide
        """
    
    elif style == "semantic":
        return f"""
        {common_instructions}
        
        Use semantic commit format with clear action words.
        Start with an action verb in present tense, followed by what was changed.
        Examples:
        - Add user authentication system
        - Fix database connection timeout
        - Update documentation for API endpoints
        - Remove deprecated utility functions
        """
    
    elif style == "simple":
        return f"""
        {common_instructions}
        
        Use a simple, direct description of what was changed.
        Be clear and concise without formal prefixes.
        Examples:
        - User authentication added
        - Fixed login bug
        - Updated README
        - Code cleanup
        """
    
    elif style == "emoji":
        return f"""
        {common_instructions}
        
        Use emoji-prefixed commit messages following gitmoji convention.
        Start with an appropriate emoji, then a clear description.
        Examples:
        - ✨ Add user authentication
        - 🐛 Fix database connection issue
        - 📝 Update documentation
        - ♻️ Refactor user service
        - 🎨 Improve code structure
        - 🚀 Deploy new features
        - 🔧 Update configuration
        """
    
    else:
        # Default to conventional if unknown style
        return get_commit_style_prompt("conventional", diff)


def generate_commit_message(diff, style=None):
    """Generates a commit message using the OpenAI API with specified style."""
    if not diff or not diff.strip():
        return "feat: Initial commit or no changes detected"

    client = get_openai_client()
    if not client:
        return None
    
    # Use provided style or fall back to config default
    if style is None:
        style = app_config.get('commit', {}).get('style', 'conventional')
    
    model_name = app_config['model']['name']
    prompt = get_commit_style_prompt(style, diff)
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": f"You are an expert at writing git commit messages in the {style} style."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=app_config['model']['max_tokens_commit'],
            temperature=app_config['model']['commit_temperature'],
        )
        message = response.choices[0].message.content.strip().strip('"`')
        
        # Style-specific post-processing
        if style == "conventional":
            # Ensure conventional commit format
            conventional_prefixes = ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'build', 'ci', 'perf']
            if not any(message.startswith(prefix + ":") for prefix in conventional_prefixes):
                message = "feat: " + message
        elif style == "semantic":
            # Ensure it starts with a verb
            message = message[0].upper() + message[1:] if message else message
        
        return message
    except Exception as e:
        import click
        click.echo(f"Error generating commit message from OpenAI: {e}")
        return None 