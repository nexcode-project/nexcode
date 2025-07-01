import yaml
from pathlib import Path
import click
import os

# Define the path for the configuration file
CONFIG_DIR = Path.home() / ".config" / "nexcode"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Local configuration
LOCAL_CONFIG_DIR = ".nexcode"
LOCAL_CONFIG_FILE = "config.yaml"

# Default configuration values
DEFAULT_CONFIG = {
    "api": {
        # Your OpenAI API key.
        # If left blank, the tool will try to use the OPENAI_API_KEY environment variable.
        "key": "",
        "base_url": ""
    },
    "model": {
        # The model to use for generating text.
        "name": "",
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
    },
    "repositories": {
        # Repository-specific configurations
        # Example:
        # "origin": {
        #     "push_command": "git push origin HEAD",
        #     "commit_style": "conventional"
        # }
    }
}

# Default local configuration template with detailed comments
DEFAULT_LOCAL_CONFIG_TEMPLATE = """# Nexcode Local Repository Configuration
# 本地仓库配置文件 - 用于设置特定仓库的推送和提交行为
# 此配置会覆盖全局配置设置
# 
# 配置完成后，使用以下命令测试推送:
#   nexcode push --dry-run

repository:
  # 仓库类型 - 影响默认的推送行为
  # 支持: github, gitlab, gerrit, gitee, bitbucket, custom
  type: github
  
  # 远程仓库名称 (通常是 origin)
  remote: origin
  
  # 目标分支名称 (用于某些推送模板)
  target_branch: main
  
  # 推送命令模板
  # 可用变量: {remote}, {branch}, {target_branch}
  # 
  # 常用模板示例:
  # GitHub/GitLab/Gitee: "git push {remote} {branch}"
  # Gerrit 代码评审:    "git push {remote} HEAD:refs/for/{target_branch}"
  # 强制推送:           "git push --force {remote} {branch}"
  # 推送并设置上游:      "git push --set-upstream {remote} {branch}"
  push_command: "git push {remote} {branch}"

commit:
  # 提交消息风格覆盖 (null 表示使用全局设置)
  # 可选值: conventional, semantic, simple, emoji, null
  style: null
  
  # 是否默认启用 bug 检查 (null 表示使用全局设置)
  # 可选值: true, false, null
  check_bugs_by_default: null

# 示例配置:
#
# Gerrit 仓库配置:
# repository:
#   type: gerrit
#   remote: origin
#   target_branch: dev-yangkewei-impl
#   push_command: "git push {remote} HEAD:refs/for/{target_branch}"
#
# GitLab MR 配置:
# repository:
#   type: gitlab
#   remote: origin
#   target_branch: main
#   push_command: "git push {remote} {branch} -o merge_request.create"
#
# 自定义推送配置:
# repository:
#   type: custom
#   remote: upstream
#   target_branch: develop
#   push_command: "git push --force-with-lease {remote} {branch}"
"""

def get_local_config_path():
    """Get the path to the local config directory in current working directory."""
    return Path.cwd() / LOCAL_CONFIG_DIR

def get_local_config_file_path():
    """Get the path to the local config file."""
    return get_local_config_path() / LOCAL_CONFIG_FILE

def init_local_config():
    """Initialize local configuration directory and file with template."""
    local_config_dir = get_local_config_path()
    local_config_file = get_local_config_file_path()
    
    # Create .nexcode directory
    local_config_dir.mkdir(exist_ok=True)
    
    # Create config.yaml with template if it doesn't exist
    if not local_config_file.exists():
        with open(local_config_file, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_LOCAL_CONFIG_TEMPLATE)
        
        # Add to .gitignore
        add_to_gitignore()
        
        return local_config_file, True  # True means created new file
    else:
        return local_config_file, False  # False means file already exists

def load_local_config():
    """Load local configuration from .nexcode/config.yaml."""
    local_config_file = get_local_config_file_path()
    
    if not local_config_file.exists():
        return {}
    
    try:
        with open(local_config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config is not None else {}
    except Exception as e:
        click.echo(f"Warning: Failed to load local config: {e}")
        return {}

def get_merged_config():
    """Get configuration with local settings merged over global settings."""
    global_config = load_config()
    local_config = load_local_config()
    
    # Deep merge local config over global config
    merged = global_config.copy()
    
    # Merge repository settings
    if 'repository' in local_config:
        # Apply repository-specific overrides
        if 'commit' in local_config:
            commit_overrides = local_config['commit']
            for key, value in commit_overrides.items():
                if value is not None:  # Only override if explicitly set
                    if 'commit' not in merged:
                        merged['commit'] = {}
                    merged['commit'][key] = value
    
    # Store local repository config for easy access
    merged['_local_repository'] = local_config.get('repository', {})
    
    return merged

def add_to_gitignore():
    """Add .nexcode to .gitignore if it's not already there."""
    gitignore_path = Path.cwd() / ".gitignore"
    nexcode_entry = ".nexcode/"
    
    try:
        # Read existing .gitignore
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if .nexcode is already in .gitignore
            if nexcode_entry not in content and ".nexcode" not in content:
                # Add .nexcode to .gitignore
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    if not content.endswith('\n'):
                        f.write('\n')
                    f.write(f"# Nexcode local configuration\n{nexcode_entry}\n")
                return True
        else:
            # Create .gitignore with .nexcode entry
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(f"# Nexcode local configuration\n{nexcode_entry}\n")
            return True
    except Exception as e:
        click.echo(f"Warning: Could not update .gitignore: {e}")
    
    return False

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
    config_path = CONFIG_FILE
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save configuration
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, indent=2)

def get_config_value(key_path):
    """Get a configuration value using dot notation (e.g., 'model.name')."""
    config_data = get_merged_config()  # Use merged config
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
    config_data = get_merged_config()  # Use merged config
    flattened = {}
    
    def flatten_dict(d, parent_key=''):
        for k, v in d.items():
            if k.startswith('_'):  # Skip internal keys
                continue
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
config = get_merged_config() 