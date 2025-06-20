from .client import get_openai_client
from ..config import config as app_config


def get_ai_solution_for_git_error(command, error_message):
    """Asks the AI for a solution to a git command error."""
    client = get_openai_client()
    if not client:
        return "Cannot get AI solution: OpenAI client not available."
    
    model_name = app_config['model']['name']
    prompt = f"""
    I encountered an error while running a git command.

    The command was:
    `{' '.join(command)}`

    The error message was:
    ---
    {error_message}
    ---

    As a senior Git expert, please explain what this error means and provide a step-by-step solution on how to fix it. Provide specific commands if applicable.
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a Git expert who helps resolve errors."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=app_config['model']['max_tokens_solution'],
            temperature=app_config['model']['solution_temperature'],
        )
        solution = response.choices[0].message.content.strip()
        return solution
    except Exception as e:
        return f"Failed to get AI help: {e}"


def check_code_for_bugs(diff):
    """Analyzes code changes for potential bugs and issues."""
    if not diff or not diff.strip():
        return "No code changes to analyze."

    client = get_openai_client()
    if not client:
        return "Cannot perform bug check: OpenAI client not available."
    
    model_name = app_config['model']['name']
    prompt = f"""
    As a senior software engineer and code reviewer, please analyze the following git diff for potential bugs, security issues, and code quality problems.

    Focus on:
    1. Logic errors and potential bugs
    2. Security vulnerabilities
    3. Performance issues
    4. Code quality and best practices
    5. Edge cases that might not be handled
    6. Resource leaks or memory issues
    7. Error handling problems

    For each issue found, provide:
    - Severity level (HIGH/MEDIUM/LOW)
    - Description of the issue
    - Suggested fix or improvement
    - Line reference if possible

    If no significant issues are found, say "No significant issues detected."

    Git Diff:
    ---
    {diff}
    ---
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a senior software engineer who specializes in code review and bug detection."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=app_config['model']['max_tokens_solution'],
            temperature=0.3,  # Lower temperature for more focused analysis
        )
        analysis = response.choices[0].message.content.strip()
        return analysis
    except Exception as e:
        return f"Error during bug analysis: {e}"


def ask_ai_about_commits(question):
    """Ask AI about git commit related questions."""
    if not question or not question.strip():
        return "Please provide a question to ask about."

    client = get_openai_client()
    if not client:
        return "Cannot get AI response: OpenAI client not available."
    
    model_name = app_config['model']['name']
    prompt = f"""
    As a senior Git expert and software development consultant, please help answer the following question about Git commits, version control, or software development workflow.

    User Question:
    ---
    {question}
    ---

    Please provide:
    1. A clear and detailed explanation
    2. Specific commands or examples if applicable
    3. Best practices or recommendations
    4. Common pitfalls to avoid (if relevant)

    Make your response practical and actionable.
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a senior Git expert and software development consultant who provides helpful, accurate, and practical advice about version control, commits, and development workflows."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=app_config['model']['max_tokens_solution'],
            temperature=0.7,  # Slightly higher temperature for more conversational responses
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        return f"Error getting AI response: {e}" 