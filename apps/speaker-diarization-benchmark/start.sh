#!/bin/bash
# =============================================================================
# HOW:
#   ./start.sh           # Start all services
#   ./start.sh postgres  # Start just PostgreSQL
#   ./start.sh stop      # Stop all services
#   ./start.sh logs      # View all logs
#   ./start.sh status    # Show service status
#
# WHO:
#   Claude AI, User
#
# WHAT:
#   Convenience wrapper around docker compose commands.
#   Automatically includes --env-file flag to load credentials from repo root.
#   Checks for port conflicts and offers to kill interfering processes.
#
# WHEN:
#   2025-12-08
#   Last Modified: 2025-12-09
#   [Change Log:
#     - 2025-12-09: Updated service names (instant-proxy, ground-truth-server)
#     - 2025-12-09: Added port conflict detection and resolution
#   ]
#
# WHERE:
#   apps/speaker-diarization-benchmark/start.sh
#
# WHY:
#   Docker Compose needs the --env-file flag to load INSTANT_APP_ID and
#   INSTANT_ADMIN_SECRET from the repo root .env file. This script makes
#   it easier to run common commands without remembering that flag.
#   It also detects when ports are already in use and offers to kill
#   the conflicting processes.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE="../../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    echo "   Create it with INSTANT_APP_ID and INSTANT_ADMIN_SECRET"
    exit 1
fi

# =============================================================================
# Port conflict detection and resolution
# =============================================================================

# Check if a port is in use and return the PID(s) using it
check_port() {
    local port=$1
    # Use lsof to find processes listening on the port
    lsof -ti :$port 2>/dev/null || true
}

# Get process info for a PID
get_process_info() {
    local pid=$1
    ps -p $pid -o pid=,comm=,args= 2>/dev/null || echo "$pid (process info unavailable)"
}

# Check if a process is Docker-related
is_docker_process() {
    local pid=$1
    local cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "")
    # Check if it's a Docker process
    if [[ "$cmd" == *"docker"* ]] || [[ "$cmd" == *"com.docker"* ]] || [[ "$cmd" == *"containerd"* ]]; then
        return 0  # true - is Docker
    fi
    return 1  # false - not Docker
}

# Check all required ports and handle conflicts
check_port_conflicts() {
    local ports_to_check=("3001:instant-proxy" "8000:ground-truth-server" "5433:postgres")
    local conflicts_found=false
    local pids_to_kill=()
    local docker_ports=()
    
    echo "🔍 Checking for port conflicts..."
    echo ""
    
    for port_info in "${ports_to_check[@]}"; do
        local port="${port_info%%:*}"
        local service="${port_info##*:}"
        local pids=$(check_port $port)
        
        if [ -n "$pids" ]; then
            for pid in $pids; do
                if is_docker_process $pid; then
                    docker_ports+=("$port:$service")
                else
                    conflicts_found=true
                    echo "⚠️  Port $port ($service) is already in use by a non-Docker process:"
                    echo "   PID $pid: $(get_process_info $pid)"
                    pids_to_kill+=("$pid")
                    echo ""
                fi
            done
        fi
    done
    
    # Report Docker-owned ports (informational only)
    if [ ${#docker_ports[@]} -gt 0 ]; then
        echo "ℹ️  Docker is already using these ports (this is fine):"
        for dp in "${docker_ports[@]}"; do
            local port="${dp%%:*}"
            local service="${dp##*:}"
            echo "   Port $port ($service) - managed by Docker"
        done
        echo ""
    fi
    
    if [ "$conflicts_found" = true ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🚨 Non-Docker port conflicts detected!"
        echo ""
        echo "These processes may interfere with Docker Compose services."
        echo -n "Would you like to kill them? [y/N] "
        read -r response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo ""
            for pid in "${pids_to_kill[@]}"; do
                echo "   Killing PID $pid..."
                kill $pid 2>/dev/null || true
            done
            echo ""
            echo "✅ Processes killed. Waiting 2 seconds for ports to be released..."
            sleep 2
        else
            echo ""
            echo "⚠️  Proceeding anyway. Docker may fail to bind to ports."
            echo "   You can manually kill processes with: kill <PID>"
            echo ""
        fi
    elif [ ${#docker_ports[@]} -eq 0 ]; then
        echo "✅ No port conflicts detected."
        echo ""
    fi
}

case "${1:-up}" in
    up|start)
        # Check for port conflicts before starting
        check_port_conflicts
        
        echo "🚀 Starting services..."
        docker compose --env-file "$ENV_FILE" up -d ${2:-}
        echo ""
        echo "📊 Status:"
        docker compose --env-file "$ENV_FILE" ps
        echo ""
        echo "✅ Services started. Health check URLs:"
        echo "   - instant-proxy:       http://localhost:3001/health"
        echo "   - ground-truth-server: http://localhost:8000/"
        echo "   - PostgreSQL:          localhost:5433 (diarization/diarization_dev)"
        echo ""
        echo "🌐 Ground Truth UI: http://localhost:8000/data/clips/ground_truth_instant.html"
        ;;
    down|stop)
        echo "🛑 Stopping services..."
        docker compose --env-file "$ENV_FILE" down ${2:-}
        ;;
    restart)
        echo "🔄 Restarting services..."
        docker compose --env-file "$ENV_FILE" restart ${2:-}
        ;;
    logs)
        docker compose --env-file "$ENV_FILE" logs ${2:--f}
        ;;
    status|ps)
        docker compose --env-file "$ENV_FILE" ps
        ;;
    build)
        echo "🔨 Building services..."
        docker compose --env-file "$ENV_FILE" build ${2:-}
        ;;
    clean)
        echo "🧹 Stopping and removing all data (volumes)..."
        docker compose --env-file "$ENV_FILE" down -v
        ;;
    *)
        echo "Usage: $0 [command] [service]"
        echo ""
        echo "Commands:"
        echo "  up, start    Start services (default)"
        echo "  down, stop   Stop services"
        echo "  restart      Restart services"
        echo "  logs         View logs (follows by default)"
        echo "  status, ps   Show service status"
        echo "  build        Build Docker images"
        echo "  clean        Stop and remove all data (volumes)"
        echo ""
        echo "Services:"
        echo "  postgres            PostgreSQL + pgvector"
        echo "  instant-proxy       TypeScript InstantDB proxy"
        echo "  ground-truth-server Python Ground Truth UI server"
        echo ""
        echo "Examples:"
        echo "  $0                        # Start all services"
        echo "  $0 postgres               # Start just PostgreSQL"
        echo "  $0 up instant-proxy       # Start just InstantDB proxy"
        echo "  $0 logs ground-truth-server  # View Ground Truth server logs"
        echo "  $0 stop                   # Stop all services"
        ;;
esac
