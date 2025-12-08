"""
HOW:
  from ingestion.health import check_services
  
  # Raises SystemExit if services are down
  check_services()
  
  # Or check specific services
  check_services(require_postgres=False)

  [Inputs]
  - require_instant_server: Whether instant-server is required (default: True)
  - require_postgres: Whether PostgreSQL is required (default: True)
  - auto_start: Whether to offer starting services (default: True)

  [Outputs]
  - Returns True if all required services are running
  - Raises SystemExit(1) if services are down and user doesn't want to start

  [Side Effects]
  - HTTP request to instant-server health endpoint
  - PostgreSQL connection test
  - May run ./start.sh if user confirms

WHO:
  Claude AI, User
  (Context: Service health checks for audio ingestion)

WHAT:
  Provides health check functionality to verify required services are running
  before starting any audio ingestion workflow. This prevents confusing errors
  partway through processing.

WHEN:
  2025-12-08

WHERE:
  apps/speaker-diarization-benchmark/ingestion/health.py

WHY:
  The audio ingestion pipeline depends on external services (instant-server for
  InstantDB, PostgreSQL for embeddings). Checking these upfront provides clear
  error messages and offers to start them automatically.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Service configurations
INSTANT_SERVER_URL = "http://localhost:3001/health"
INSTANT_SERVER_PORT = 3001
POSTGRES_DSN = "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
POSTGRES_PORT = 5433


def check_instant_server() -> Tuple[bool, str]:
    """
    Check if instant-server is running and healthy.
    
    Returns:
        Tuple of (is_healthy, message)
    """
    import requests
    
    try:
        resp = requests.get(INSTANT_SERVER_URL, timeout=2)
        if resp.status_code == 200:
            return True, "✅ instant-server healthy"
        else:
            return False, f"❌ instant-server unhealthy (status: {resp.status_code})"
    except requests.exceptions.ConnectionError:
        return False, f"❌ instant-server not running (port {INSTANT_SERVER_PORT})"
    except requests.exceptions.Timeout:
        return False, f"❌ instant-server timeout (port {INSTANT_SERVER_PORT})"


def check_postgres() -> Tuple[bool, str]:
    """
    Check if PostgreSQL is running, accepting connections, and has the expected schema.
    
    Returns:
        Tuple of (is_healthy, message)
    """
    try:
        import psycopg
        
        conn = psycopg.connect(POSTGRES_DSN, connect_timeout=2)
        cursor = conn.cursor()
        
        # Verify the speaker_embeddings table exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'speaker_embeddings'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            conn.close()
            return False, "❌ PostgreSQL connected but speaker_embeddings table missing"
        
        # Get embedding count for extra info
        cursor.execute("SELECT COUNT(*) FROM speaker_embeddings")
        count = cursor.fetchone()[0]
        
        conn.close()
        return True, f"✅ PostgreSQL healthy ({count} embeddings)"
    except Exception as e:
        error_msg = str(e).split('\n')[0]  # First line only
        return False, f"❌ PostgreSQL error (port {POSTGRES_PORT}): {error_msg}"


def check_services(
    require_instant_server: bool = True,
    require_postgres: bool = True,
    auto_start: bool = True,
    interactive: bool = True,
) -> bool:
    """
    Check that required services are running.
    
    Args:
        require_instant_server: Whether instant-server is required
        require_postgres: Whether PostgreSQL is required
        auto_start: Whether to offer starting services if down
        interactive: Whether to prompt user (False for non-interactive mode)
    
    Returns:
        True if all required services are healthy
        
    Raises:
        SystemExit: If services are down and user doesn't want to start them
    """
    issues: List[str] = []
    
    print("🔍 Checking services...")
    
    # Check instant-server
    if require_instant_server:
        healthy, msg = check_instant_server()
        print(f"   {msg}")
        if not healthy:
            issues.append(msg)
    
    # Check PostgreSQL
    if require_postgres:
        healthy, msg = check_postgres()
        print(f"   {msg}")
        if not healthy:
            issues.append(msg)
    
    if not issues:
        print("   All services healthy.\n")
        return True
    
    # Services are down
    print()
    print("❌ Service Health Check Failed:")
    for issue in issues:
        print(f"   {issue}")
    print()
    print("Please start the services:")
    print("   cd apps/speaker-diarization-benchmark")
    print("   ./start.sh")
    print()
    
    if auto_start and interactive:
        try:
            response = input("Would you like me to start them now? [y/N] ")
        except EOFError:
            # Non-interactive environment
            response = "n"
        
        if response.lower() == 'y':
            print("\n🚀 Starting services...")
            script_dir = Path(__file__).parent.parent
            result = subprocess.run(
                ["./start.sh"],
                cwd=script_dir,
                capture_output=False,
            )
            
            if result.returncode == 0:
                print("\n⏳ Waiting for services to start...")
                import time
                time.sleep(3)  # Give services time to fully start
                
                # Re-check
                return check_services(
                    require_instant_server=require_instant_server,
                    require_postgres=require_postgres,
                    auto_start=False,  # Don't offer again
                    interactive=interactive,
                )
            else:
                print("\n❌ Failed to start services")
                sys.exit(1)
    
    sys.exit(1)


if __name__ == "__main__":
    # Quick test
    check_services()

