import subprocess
from typing import Dict, Any

def get_git_info() -> Dict[str, Any]:
    """
    Retrieves the current git commit hash and status.
    Returns a dictionary with 'commit_hash' and 'is_dirty'.
    """
    try:
        # Get commit hash
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        
        # Check for uncommitted changes
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        
        is_dirty = bool(status)
        
        return {
            "commit_hash": commit_hash,
            "is_dirty": is_dirty
        }
    except subprocess.CalledProcessError:
        return {
            "commit_hash": "unknown",
            "is_dirty": False
        }
    except FileNotFoundError:
        # git not found
            "timestamp": "unknown",
            "is_dirty": False
        }


