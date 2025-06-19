#!/usr/bin/env python3

import subprocess
import fnmatch

def get_changed_files():
    """Get all changed files (modified, added, deleted)."""
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        return []
    
    files = []
    for line in result.stdout.splitlines():
        if len(line) > 3:
            # Extract filename from git status output
            filename = line[3:].strip()
            files.append(filename)
    return files

def should_ignore_file(file_path):
    """Check if a file should be ignored based on .gitignore rules."""
    try:
        with open('.gitignore', 'r') as f:
            ignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(file_path, f"**/{pattern}"):
                return True
        return False
    except FileNotFoundError:
        return False

def main():
    print("Testing smart git add logic...")
    
    changed_files = get_changed_files()
    print(f"Changed files: {changed_files}")
    
    files_to_add = []
    ignored_files = []
    
    for file_path in changed_files:
        if should_ignore_file(file_path):
            ignored_files.append(file_path)
        else:
            files_to_add.append(file_path)
    
    print(f"Files to add: {files_to_add}")
    print(f"Files to ignore: {ignored_files}")

if __name__ == "__main__":
    main() 