import os
import click
from openai import OpenAI
from ..config import config as app_config


def get_openai_client():
    """Get OpenAI client, initializing it if needed."""
    # Read configuration from config file and environment variables
    api_key = app_config['api']['key'] or os.environ.get("OPENAI_API_KEY")
    base_url = app_config['api']['base_url']
    
    if not api_key:
        click.echo("Error: API key is not configured.")
        click.echo("Please set it in ~/.config/nexcode/config.yaml or as an OPENAI_API_KEY environment variable.")
        return None
    
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        click.echo(f"Error initializing OpenAI client: {e}")
        return None 