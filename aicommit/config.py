import yaml
from pathlib import Path

# Define the path for the configuration file
CONFIG_DIR = Path.home() / ".config" / "aicommit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"



def load_config():
    """Loads configuration from the YAML file, creating it if it doesn't exist."""
    
    with open(CONFIG_FILE, 'r') as configfile:
        # Use safe_load to avoid arbitrary code execution
        config = yaml.safe_load(configfile)
        # Handle case where file is created but empty
        if config is None:
            return {}
        return config

# Load the configuration once when the module is imported
config = load_config() 