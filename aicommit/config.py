import yaml
from pathlib import Path
import click
import os

# Define the path for the configuration file
CONFIG_DIR = Path.home() / ".config" / "aicommit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Default configuration values
DEFAULT_CONFIG = {
    "api": {
        # Your OpenAI API key.
        # If left blank, the tool will try to use the OPENAI_API_KEY environment variable.
        "key": "",
        "base_url": "http://10.12.160.15/v1"
    },
    "model": {
        # The model to use for generating text.
        "name": "codedrive-chat",
        # Temperature for commit message generation (0.0 to 1.0).
        # Higher values mean more creative, lower values mean more deterministic.
        "commit_temperature": 0.7,
        # Temperature for solution generation.
        "solution_temperature": 0.5,
        "max_tokens_commit": 60,
        "max_tokens_solution": 512
    },
    "commit": {
        # Default commit message style: conventional, semantic, simple, emoji
        "style": "conventional",
        # Whether to run bug analysis by default before committing
        "check_bugs_by_default": False
    }
}

def create_default_config():
    """Creates the default YAML configuration file if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # We dump a commented version for user clarity
    header = (
        "# AI Commits Configuration File\n"
        "# You can customize your settings here.\n"
    )
    with open(CONFIG_FILE, 'w') as configfile:
        configfile.write(header)
        yaml.dump(DEFAULT_CONFIG, configfile, default_flow_style=False, sort_keys=False)


def load_config():
    """Loads configuration from the YAML file, creating it if it doesn't exist."""
    if not CONFIG_FILE.is_file():
        create_default_config()
    
    with open(CONFIG_FILE, 'r') as configfile:
        # Use safe_load to avoid arbitrary code execution
        config = yaml.safe_load(configfile)
        # Handle case where file is created but empty
        if config is None:
            return {}
        return config

def save_config(config_dict):
    """Save configuration dictionary to the config file."""
    config_path = get_config_path()
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save configuration
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, indent=2)

def get_config_value(key_path):
    """Get a configuration value using dot notation (e.g., 'model.name')."""
    config_data = load_config()
    keys = key_path.split('.')
    
    current = config_data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

def set_config_value(key_path, value):
    """Set a configuration value using dot notation (e.g., 'model.name', 'gpt-4')."""
    config_data = load_config()
    keys = key_path.split('.')
    
    # Navigate to the parent of the target key
    current = config_data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Convert string values to appropriate types
    final_key = keys[-1]
    if value.lower() in ['true', 'false']:
        value = value.lower() == 'true'
    elif value.replace('.', '').replace('-', '').isdigit():
        value = float(value) if '.' in value else int(value)
    
    current[final_key] = value
    save_config(config_data)
    return True

def list_all_config():
    """List all configuration values in a flattened format."""
    config_data = load_config()
    flattened = {}
    
    def flatten_dict(d, parent_key=''):
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                flatten_dict(v, new_key)
            else:
                flattened[new_key] = v
    
    flatten_dict(config_data)
    return flattened

def reset_config():
    """Reset configuration to default values."""
    save_config(DEFAULT_CONFIG)
    return True

# Load the configuration once when the module is imported
config = load_config() 