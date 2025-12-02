#!/usr/bin/env -S uv run python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
WHO:   Cursor Agent, User
       (Context: Created to standardize progress tracking across local and global logs)

WHAT:  Updates progress.md in the local repository and a global log in ~/.agents/progress.md.
       
       This script creates formatted progress entries with timestamps, emojis, commit links,
       and optional details. It can optionally amend the current commit to include progress.md
       and push to the remote repository.
       
       [Inputs]
       - --type: Type of progress entry (feature, bug, chore, doc, wip, test, question, answer, decision, release)
       - --message: Short summary of the change (required)
       - --details: Additional details as positional arguments (optional, multiple allowed)
       - --push: If provided, amends current commit to include progress.md and pushes to remote
       
       [Outputs]
       - Updates ./progress.md with new entry at the top
       - Updates ~/.agents/progress.md with new entry (includes project context)
       - Prints status messages
       
       [Side Effects]
       - Modifies filesystem (writes to progress.md files)
       - If --push is used: amends git commit, rewrites history, pushes to remote
       
       [How to run]
       # Basic usage (updates files only)
       ./scripts/update_progress.py --type feature --message "Added new script" --details "Fixed bug X" "Added test Y"
       
       # With --push flag (amends commit and pushes)
       ./scripts/update_progress.py --type feature --message "Added new script" --push "Detail 1" "Detail 2"
       
       # Workflow:
       # 1. Make your changes and commit them
       # 2. Run this script with --push to document the changes
       # 3. The script will amend your commit to include progress.md and push
       
       [--push Flag Behavior]
       When --push is used, the script:
       1. Adds progress.md to staging
       2. Amends the current commit (HEAD) to include progress.md
       3. Updates the commit hash reference in the progress entry
       4. Amends again to include the updated hash reference
       5. Pushes with --force-with-lease (safe force push)
       
       This ensures that:
       - The commit referenced in progress.md includes both your actual changes AND progress.md
       - Clicking the GitHub link shows everything in one commit
       - No manual git intervention is needed
       
       Note: The script always amends, even if the commit was already pushed. This rewrites
       history, so use with caution in shared branches. The --force-with-lease flag prevents
       accidental overwrites if someone else has pushed in the meantime.

WHEN:  2025-12-02
       2025-12-02
       [Change Log:
        - 2025-12-02: Initial creation]
        - 2025-12-02: Updated to use gh CLI and enforce uv]
        - 2025-12-02: Updated date format and added --push option]
        - 2025-12-02: Changed filename from PROGRESS.md to progress.md]
        - 2025-12-02: Fixed --push to always amend commit so progress.md is included in referenced commit]
        - 2025-12-02: Simplified push logic and added comprehensive documentation]

WHERE: Used by Agents to track progress.
       Local: ./progress.md
       Global: ~/.agents/progress.md

WHY:   To maintain a running log of work for context and history. The --push flag ensures
       that progress entries are always linked to commits that include both the actual changes
       and the progress documentation, making it easy to see what changed and why.
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
    """
    Retrieves git information for the current repository.
    
    Returns:
        tuple: (commit_hash, repo_url, project_root)
            - commit_hash: Short commit hash of HEAD (7 characters)
            - repo_url: Repository URL from GitHub CLI or git remote (without .git extension)
            - project_root: Absolute path to the git repository root
            
    Uses GitHub CLI (gh) if available, otherwise falls back to git remote.
    Returns None for any values that cannot be determined.
    """
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
    """
    Generates a human-readable date string with ordinal suffixes.
    
    Returns:
        str: Formatted date string like 'December 1st, 2025 at 9:16:52 p.m.'
        
    Handles ordinal suffixes correctly (1st, 2nd, 3rd, 4th, etc.) and formats
    time in 12-hour format with a.m./p.m. notation.
    """
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
    """
    Formats a progress log entry with all relevant information.
    
    Args:
        entry_type: Type of entry (maps to emoji via EMOJI_MAP)
        message: Main message/summary of the entry
        details: List of additional detail strings
        commit_hash: Git commit hash to reference
        repo_url: Repository URL for creating commit links
        project_root: Path to project root (for global log context)
        is_global: If True, adds project context for global log entries
        
    Returns:
        str: Formatted markdown entry with date, emoji, message, commit link, and details
    """
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
    """
    Updates a progress log file with a new entry.
    
    Args:
        file_path: Path to the progress log file (supports ~ expansion)
        entry: Formatted entry string to add
        location_desc: Description of file location (for header if file doesn't exist)
        
    Behavior:
        - Creates file with header if it doesn't exist
        - Inserts new entry after the "---" separator if present
        - Otherwise prepends entry to existing content
        - Ensures entries are always added at the top of the log
    """
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
    """
    Amends the current commit to include progress.md and pushes to remote.
    
    This function handles the --push flag workflow:
    1. Stages progress.md
    2. Amends HEAD commit to include progress.md (creates commit A)
    3. Updates the commit hash reference in progress.md to point to commit A
    4. Amends again to include the updated hash reference (creates commit B)
    5. Pushes with --force-with-lease
    
    The final commit (B) includes:
    - Your original changes
    - progress.md with the entry
    - A commit hash reference pointing to commit A (which also includes everything)
    
    This ensures that clicking the GitHub link shows both the actual changes
    and the progress.md update in a single commit view.
    
    Raises:
        subprocess.CalledProcessError: If any git command fails
    """
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
        # This creates a commit that includes: actual changes + progress.md + hash reference
        subprocess.check_call(['git', 'add', 'progress.md'])
        subprocess.check_call(['git', 'commit', '--amend', '--no-edit'])
        
        # Get the final commit hash after the second amend - this is what will be pushed
        final_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
        
        # Update progress.md one final time with the hash that will actually be pushed
        with open(local_progress, 'r') as f:
            content = f.read()
        # Update the hash reference to the final commit
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
        
        # Final amend to include the correct hash reference (the one that will be pushed)
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
