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
        - 2025-12-02: Fixed --push to check if commit is pushed before amending to avoid divergence]
        - 2025-12-02: Changed to always amend commit so progress.md is included in referenced commit]

WHERE: Used by Agents to track progress.
       Local: ./progress.md
       Global: ~/.agents/progress.md

WHY:   To maintain a running log of work for context and history.
"""

import argparse
import datetime
import os
import re
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

def is_commit_pushed():
    """Check if HEAD has been pushed to origin"""
    try:
        # Get current branch name
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        remote_branch = f'origin/{branch}'
        
        # Check if remote branch exists
        try:
            remote_hash = subprocess.check_output(['git', 'rev-parse', remote_branch], 
                                                 stderr=subprocess.DEVNULL, text=True).strip()
        except subprocess.CalledProcessError:
            # Remote branch doesn't exist, so commit hasn't been pushed
            return False
        
        # Get local commit hash
        local_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        
        # If local == remote, the commit has been pushed
        return local_hash == remote_hash
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If we can't determine, assume it hasn't been pushed to be safe
        return False

def push_changes():
    """Pushes changes to remote, always amending to include progress.md in the referenced commit"""
    try:
        # Add progress.md
        subprocess.check_call(['git', 'add', 'progress.md'])
        
        # Always amend the commit (even if pushed) so progress.md is included in the referenced commit
        # This way the GitHub link shows both the actual changes and the progress.md update
        subprocess.check_call(['git', 'commit', '--amend', '--no-edit'])
        
        # Get the new amended commit hash
        new_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
        
        # Update progress.md with the new commit hash (the amended commit contains both changes and progress.md)
        local_progress = Path("progress.md")
        with open(local_progress, 'r') as f:
            content = f.read()
        # Find and replace the commit reference in the most recent entry
        # Pattern to match commit links/hashes in the format [Commit](url/commit/HASH) or Commit: HASH
        # Match the full URL pattern more carefully
        old_hash_pattern = r'(\[Commit\]\(https?://[^/]+/[^/]+/[^/]+/commit/)([a-f0-9]+)(\))'
        if re.search(old_hash_pattern, content):
            content = re.sub(old_hash_pattern, lambda m: m.group(1) + new_hash + m.group(3), content, count=1)
        else:
            # Fallback to simpler pattern if URL format is different
            old_hash_pattern_simple = r'(\[Commit\]\([^)]+/commit/)([a-f0-9]+)(\))'
            content = re.sub(old_hash_pattern_simple, lambda m: m.group(1) + new_hash + m.group(3), content, count=1)
        old_hash_pattern2 = r'(Commit: )([a-f0-9]+)'
        if re.search(old_hash_pattern2, content) and '[Commit]' not in content.split('\n\n')[1] if len(content.split('\n\n')) > 1 else True:
            content = re.sub(old_hash_pattern2, lambda m: m.group(1) + new_hash, content, count=1)
        with open(local_progress, 'w') as f:
            f.write(content)
        
        # Same for global log
        global_progress = Path("~/.agents/progress.md")
        global_path = global_progress.expanduser()
        if global_path.exists():
            with open(global_path, 'r') as f:
                global_content = f.read()
            if re.search(old_hash_pattern, global_content):
                global_content = re.sub(old_hash_pattern, lambda m: m.group(1) + new_hash + m.group(3), global_content, count=1)
            else:
                old_hash_pattern_simple = r'(\[Commit\]\([^)]+/commit/)([a-f0-9]+)(\))'
                global_content = re.sub(old_hash_pattern_simple, lambda m: m.group(1) + new_hash + m.group(3), global_content, count=1)
            if re.search(old_hash_pattern2, global_content) and '[Commit]' not in global_content.split('\n\n')[1] if len(global_content.split('\n\n')) > 1 else True:
                global_content = re.sub(old_hash_pattern2, lambda m: m.group(1) + new_hash, global_content, count=1)
            with open(global_path, 'w') as f:
                f.write(global_content)
        
        # Re-add and amend again to include the updated commit hash reference
        subprocess.check_call(['git', 'add', 'progress.md'])
        subprocess.check_call(['git', 'commit', '--amend', '--no-edit'])
        
        # Get the final commit hash after second amend
        final_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
        
        # Update progress.md one more time with the final hash
        with open(local_progress, 'r') as f:
            content = f.read()
        # Use the same pattern matching logic
        final_hash_pattern = r'(\[Commit\]\(https?://[^/]+/[^/]+/[^/]+/commit/)([a-f0-9]+)(\))'
        if re.search(final_hash_pattern, content):
            content = re.sub(final_hash_pattern, lambda m: m.group(1) + final_hash + m.group(3), content, count=1)
        else:
            final_hash_pattern_simple = r'(\[Commit\]\([^)]+/commit/)([a-f0-9]+)(\))'
            content = re.sub(final_hash_pattern_simple, lambda m: m.group(1) + final_hash + m.group(3), content, count=1)
        final_hash_pattern2 = r'(Commit: )([a-f0-9]+)'
        if re.search(final_hash_pattern2, content) and '[Commit]' not in content.split('\n\n')[1] if len(content.split('\n\n')) > 1 else True:
            content = re.sub(final_hash_pattern2, lambda m: m.group(1) + final_hash, content, count=1)
        with open(local_progress, 'w') as f:
            f.write(content)
        
        # Same for global log
        if global_path.exists():
            with open(global_path, 'r') as f:
                global_content = f.read()
            if re.search(final_hash_pattern, global_content):
                global_content = re.sub(final_hash_pattern, lambda m: m.group(1) + final_hash + m.group(3), global_content, count=1)
            else:
                final_hash_pattern_simple = r'(\[Commit\]\([^)]+/commit/)([a-f0-9]+)(\))'
                global_content = re.sub(final_hash_pattern_simple, lambda m: m.group(1) + final_hash + m.group(3), global_content, count=1)
            if re.search(final_hash_pattern2, global_content) and '[Commit]' not in global_content.split('\n\n')[1] if len(global_content.split('\n\n')) > 1 else True:
                global_content = re.sub(final_hash_pattern2, lambda m: m.group(1) + final_hash, global_content, count=1)
            with open(global_path, 'w') as f:
                f.write(global_content)
        
        # Final amend to include the correct commit hash reference
        subprocess.check_call(['git', 'add', 'progress.md'])
        subprocess.check_call(['git', 'commit', '--amend', '--no-edit'])
        
        # Push with --force-with-lease for safety (rewrites history if commit was already pushed)
        print("Pushing to origin...")
        subprocess.check_call(['git', 'push', '--force-with-lease'])
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
    
    # Store the commit hash before updating progress.md
    # When pushing, we'll always amend this commit to include progress.md, so the entry will reference
    # the amended commit which contains both the actual changes and progress.md
    commit_hash_for_entry = commit_hash
    
    # Update local
    entry_local = format_entry(args.type, args.message, args.details, commit_hash_for_entry, repo_url, project_root, is_global=False)
    local_progress = Path("progress.md")
    update_file(local_progress, entry_local, "Local Repository")
    print(f"Updated {local_progress}")
    
    # Update global
    entry_global = format_entry(args.type, args.message, args.details, commit_hash_for_entry, repo_url, project_root, is_global=True)
    global_progress = Path("~/.agents/progress.md")
    update_file(global_progress, entry_global, "Global Log (~/.agents/progress.md)")
    print(f"Updated {global_progress}")
    
    if args.push:
        push_changes()

if __name__ == "__main__":
    main()
