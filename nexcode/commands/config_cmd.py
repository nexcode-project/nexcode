import click
from ..config import config as app_config
from .. import config as config_module


def handle_config_command(set_value, get_key, list_all):
    """Implementation of the config command."""
    
    if set_value:
        # Parse key=value format
        if '=' not in set_value:
            click.echo("Error: Use format key=value (e.g. commit.check_bugs_by_default=true)")
            return
            
        key, value = set_value.split('=', 1)
        
        # Parse boolean values
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        
        # Set nested key
        keys = key.split('.')
        config_dict = dict(app_config)
        
        # Navigate to the nested structure
        current = config_dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save to file
        try:
            config_module.save_config(config_dict)
            click.echo(f"✓ Set {key} = {value}")
        except Exception as e:
            click.echo(f"Error saving configuration: {e}")
            
    elif get_key:
        # Get nested key value
        keys = get_key.split('.')
        current = app_config
        
        try:
            for k in keys:
                current = current[k]
            click.echo(f"{get_key} = {current}")
        except KeyError:
            click.echo(f"Configuration key '{get_key}' not found")
            
    elif list_all:
        click.echo("Current configuration:")
        click.echo("-" * 40)
        
        def print_config(config_dict, prefix=""):
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    print_config(value, f"{prefix}{key}.")
                else:
                    click.echo(f"{prefix}{key} = {value}")
        
        print_config(app_config)
        
    else:
        click.echo("Use --list to see all settings, --get key to get a value, or --set key=value to set a value") 