import os
from typing import Dict

def parse_netscape_cookies(cookie_file: str) -> Dict[str, str]:
    """
    Parse a Netscape formatted cookies file into a dictionary suitable for requests.
    
    Args:
        cookie_file: Path to the cookie file.
        
    Returns:
        Dict[str, str]: Dictionary of cookie names and values.
    """
    cookies = {}
    if not os.path.exists(cookie_file):
        return cookies
        
    try:
        with open(cookie_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    # Netscape format: domain, flag, path, secure, expiration, name, value
                    name = parts[5]
                    value = parts[6]
                    cookies[name] = value
    except Exception as e:
        print(f"Warning: Failed to parse cookies from {cookie_file}: {e}")
        
    return cookies

def find_cookie_file(provided_path: str = None) -> str:
    """
    Resolve the path to the cookies file.
    
    Args:
        provided_path: Optional path provided by user.
        
    Returns:
        str: Path to the cookie file if found, else None.
    """
    if provided_path and os.path.exists(provided_path):
        return provided_path
        
    # Default locations to check
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming this is in apps/transcriber/lib, go up 3 levels to root
    workspace_root = os.path.abspath(os.path.join(script_dir, "../../../"))
    
    possible_paths = [
        os.path.join(workspace_root, "cookies/halfjew22-youtube-cookies.txt"),
        os.path.join(workspace_root, "cookies.txt"),
        "cookies/halfjew22-youtube-cookies.txt",
        "cookies.txt"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    return None
