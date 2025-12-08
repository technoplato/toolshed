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
#
# WHEN:
#   2025-12-08
#
# WHERE:
#   apps/speaker-diarization-benchmark/start.sh
#
# WHY:
#   Docker Compose needs the --env-file flag to load INSTANT_APP_ID and
#   INSTANT_ADMIN_SECRET from the repo root .env file. This script makes
#   it easier to run common commands without remembering that flag.
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

case "${1:-up}" in
    up|start)
        echo "🚀 Starting services..."
        docker compose --env-file "$ENV_FILE" up -d ${2:-}
        echo ""
        echo "📊 Status:"
        docker compose --env-file "$ENV_FILE" ps
        echo ""
        echo "✅ Services started. Health check URLs:"
        echo "   - instant-server: http://localhost:3001/health"
        echo "   - PostgreSQL:     localhost:5433 (diarization/diarization_dev)"
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
        echo "  postgres       PostgreSQL + pgvector"
        echo "  instant-server TypeScript InstantDB wrapper"
        echo ""
        echo "Examples:"
        echo "  $0              # Start all services"
        echo "  $0 postgres     # Start just PostgreSQL"
        echo "  $0 logs         # View logs"
        echo "  $0 stop         # Stop all services"
        ;;
esac

