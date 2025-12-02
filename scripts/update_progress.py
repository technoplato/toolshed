#!/usr/bin/env -S uv run python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
WHO:   Cursor Agent, User
       (Context: Created to standardize progress tracking across local and global logs)

WHAT:  Updates progress.md in the local repository and a global log in ~/.agents/progress.md.
       [Inputs] --type (progress type), --message (description), --details (optional list)
       [Outputs] Updates files, prints status.
       [Side Effects] Modifies filesystem.
       [How to run]
       # Run with uv (recommended)
       ./scripts/update_progress.py --type feature --message "Added new script" --details "Fixed bug X" "Added test Y"
       
       # Or via python directly if dependencies are met
       python3 scripts/update_progress.py ...

WHEN:  2025-12-02
       2025-12-02
       [Change Log:
        - 2025-12-02: Initial creation]
        - 2025-12-02: Updated to use gh CLI and enforce uv]
        - 2025-12-02: Updated date format and added --push option]
        - 2025-12-02: Changed filename from PROGRESS.md to progress.md]

WHERE: Used by Agents to track progress.
       Local: ./progress.md
       Global: ~/.agents/progress.md

WHY:   To maintain a running log of work for context and history.
"""

import argparse
import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Mapping of types to emojis
EMOJI_MAP = {
    'feature': '✨',
    'bug': '🐛',
    'chore': '🧹',
    'doc': '📝',
    'wip': '🚧',
    'test': '✅',
    'question': '❓',
    'answer': '🗣️',
    'decision': '🧠',
    'release': '🚀',
}

HEADER_TEMPLATE = """WHO:   Cursor Agent, User
       (Context: Progress Log)

WHAT:  Running log of project progress.

WHERE: {location}

WHY:   To maintain context and history of decisions and changes.

---
"""

def get_git_info():
    """Returns (commit_hash, repo_url, project_root)"""
    # Get commit hash
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit_hash = None

    # Get project root
    try:
        project_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        project_root = str(Path.cwd())

    # Get repo URL using gh CLI if available, else git remote
    repo_url = None
    if shutil.which('gh'):
        try:
            repo_url = subprocess.check_output(['gh', 'repo', 'view', '--json', 'url', '-q', '.url'], text=True).strip()
        except subprocess.CalledProcessError:
            pass
            
    if not repo_url:
        try:
            repo_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
    return commit_hash, repo_url, project_root

def get_ordinal_date_string():
    """Returns formatted date string like 'December 1st, 2025 at 9:16:52 p.m.'"""
    now = datetime.datetime.now()
    
    # Ordinal suffix
    day = now.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    
    # Format components
    month = now.strftime("%B")
    year = now.strftime("%Y")
    time_str = now.strftime("%-I:%M:%S") # %-I for no-pad hour (platform specific, usually works on Unix)
    if os.name == 'nt': # Fallback for Windows
        time_str = now.strftime("%I:%M:%S").lstrip('0')
        
    am_pm = now.strftime("%p").lower().replace("am", "a.m.").replace("pm", "p.m.")
    
    return f"{month} {day}{suffix}, {year} at {time_str} {am_pm}"

def format_entry(entry_type, message, details, commit_hash, repo_url, project_root, is_global=False):
    emoji = EMOJI_MAP.get(entry_type, 'wb')
    date_str = get_ordinal_date_string()
    
    # Construct commit link
    commit_link = ""
    if commit_hash and repo_url:
        commit_link = f"[Commit]({repo_url}/commit/{commit_hash})"
    elif commit_hash:
        commit_link = f"Commit: {commit_hash}"

    # Add project context for global log
    project_context = ""
    if is_global:
        project_name = Path(project_root).name
        project_context = f" **[{project_name}]**"

    entry = f"### {date_str}{project_context}\n"
    entry += f"\n{emoji} {message}\n"
    
    if commit_link:
        entry += f"\n{commit_link}\n"
    
    # Add project path to details if global
    if is_global:
         entry += f"- Project: `{project_root}`\n"

    if details:
        entry += "\n"
        for detail in details:
            entry += f"- {detail}\n"
            
    return entry

def update_file(file_path, entry, location_desc):
    path = Path(file_path).expanduser()
    
    if not path.exists():
        # Create directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        # Create file with header
        header = HEADER_TEMPLATE.format(location=location_desc)
        with open(path, 'w') as f:
            f.write(f"{header}\n{entry}\n")
    else:
        with open(path, 'r') as f:
            content = f.read()
        
        # Insert after separator "---" if present
        if "---" in content:
            parts = content.split("---", 1)
            # parts[0] is header, parts[1] is existing log
            # We want: Header + --- + New Entry + Existing Log
            new_content = parts[0] + "---\n\n" + entry + "\n" + parts[1]
        else:
            # No separator, prepend to content
            new_content = entry + "\n" + content
            
        with open(path, 'w') as f:
            f.write(new_content)

def push_changes():
    """Pushes changes to remote"""
    try:
        # Add progress.md
        subprocess.check_call(['git', 'add', 'progress.md'])
        
        # Amend commit (no edit) to include PROGRESS.md
        # Check if there is a previous commit to amend?
        # Only amend if the user hasn't pushed yet?
        # The prompt implies "update progress should push the commit", assuming we are adding to the last commit
        subprocess.check_call(['git', 'commit', '--amend', '--no-edit'])
        
        # Push
        print("Pushing to origin...")
        subprocess.check_call(['git', 'push'])
        print("Successfully pushed.")
    except subprocess.CalledProcessError as e:
        print(f"Error during push: {e}")

def main():
    parser = argparse.ArgumentParser(description="Update progress logs")
    parser.add_argument("--type", choices=EMOJI_MAP.keys(), default='wip', help="Type of update")
    parser.add_argument("--message", required=True, help="Short summary of the change")
    parser.add_argument("details", nargs="*", help="Additional details")
    parser.add_argument("--push", action="store_true", help="Add progress.md, amend commit, and push")
    
    args = parser.parse_args()
    
    commit_hash, repo_url, project_root = get_git_info()
    
    # Update local
    entry_local = format_entry(args.type, args.message, args.details, commit_hash, repo_url, project_root, is_global=False)
    local_progress = Path("progress.md")
    update_file(local_progress, entry_local, "Local Repository")
    print(f"Updated {local_progress}")
    
    # Update global
    entry_global = format_entry(args.type, args.message, args.details, commit_hash, repo_url, project_root, is_global=True)
    global_progress = Path("~/.agents/progress.md")
    update_file(global_progress, entry_global, "Global Log (~/.agents/progress.md)")
    print(f"Updated {global_progress}")
    
    if args.push:
        push_changes()

if __name__ == "__main__":
    main()
