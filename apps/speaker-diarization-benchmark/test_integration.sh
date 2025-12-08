#!/bin/bash
# =============================================================================
# INTEGRATION TEST: Speaker Diarization Benchmark Services
# =============================================================================
#
# HOW:
#   ./test_integration.sh
#
# WHAT:
#   Tests that all Docker services are working correctly:
#   1. instant-server health and API endpoints
#   2. PostgreSQL connection and data
#   3. End-to-end identification workflow
#
# WHEN:
#   2025-12-08
#
# WHY:
#   Verify the full stack is operational after deployment or changes.
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

INSTANT_SERVER="http://localhost:3001"
POSTGRES_DSN="postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
VIDEO_ID="20dbb029-5729-5072-8c6b-ef1f0a0cab0a"

passed=0
failed=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        passed=$((passed + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        failed=$((failed + 1))
    fi
}

echo ""
echo "========================================"
echo "  Integration Test: Speaker Diarization"
echo "========================================"
echo ""

# =============================================================================
# TEST 1: instant-server health
# =============================================================================
echo -e "${YELLOW}Testing instant-server...${NC}"

response=$(curl -s "$INSTANT_SERVER/health" 2>/dev/null || echo "FAILED")
if echo "$response" | grep -q '"status":"ok"'; then
    test_result 0 "instant-server health check"
else
    test_result 1 "instant-server health check (is it running?)"
fi

# =============================================================================
# TEST 2: List speakers
# =============================================================================
response=$(curl -s "$INSTANT_SERVER/speakers" 2>/dev/null || echo "FAILED")
speaker_count=$(echo "$response" | jq '.speakers | length' 2>/dev/null || echo "0")
if [ "$speaker_count" -gt 0 ]; then
    test_result 0 "List speakers ($speaker_count found)"
else
    test_result 1 "List speakers (none found)"
fi

# =============================================================================
# TEST 3: Get video by ID
# =============================================================================
response=$(curl -s "$INSTANT_SERVER/videos/$VIDEO_ID" 2>/dev/null || echo "FAILED")
video_title=$(echo "$response" | jq -r '.title' 2>/dev/null || echo "")
if [ -n "$video_title" ] && [ "$video_title" != "null" ]; then
    test_result 0 "Get video by ID ($video_title)"
else
    test_result 1 "Get video by ID (video not found)"
fi

# =============================================================================
# TEST 4: Get diarization segments
# =============================================================================
response=$(curl -s "$INSTANT_SERVER/diarization-segments?video_id=$VIDEO_ID&start_time=0&end_time=10" 2>/dev/null || echo "FAILED")
segment_count=$(echo "$response" | jq '.segments | length' 2>/dev/null || echo "0")
if [ "$segment_count" -gt 0 ]; then
    test_result 0 "Get diarization segments ($segment_count in first 10s)"
else
    test_result 1 "Get diarization segments (none found)"
fi

# =============================================================================
# TEST 5: PostgreSQL connection (via docker exec)
# =============================================================================
echo ""
echo -e "${YELLOW}Testing PostgreSQL...${NC}"

pg_result=$(docker exec speaker-diarization-postgres psql -U diarization -d speaker_embeddings -c "SELECT 1" 2>/dev/null | grep -c "1 row" || echo "0")
if [ "$pg_result" -gt 0 ]; then
    test_result 0 "PostgreSQL connection"
else
    test_result 1 "PostgreSQL connection (is container running?)"
fi

# =============================================================================
# TEST 6: Embedding count
# =============================================================================
embedding_count=$(docker exec speaker-diarization-postgres psql -U diarization -d speaker_embeddings -t -c "SELECT COUNT(*) FROM speaker_embeddings" 2>/dev/null | tr -d ' ' || echo "0")
if [ "$embedding_count" -gt 0 ]; then
    test_result 0 "Speaker embeddings in database ($embedding_count)"
else
    test_result 1 "Speaker embeddings (none found - run migration?)"
fi

# =============================================================================
# TEST 7: Speaker distribution in PostgreSQL
# =============================================================================
speaker_dist=$(docker exec speaker-diarization-postgres psql -U diarization -d speaker_embeddings -t -c "SELECT COUNT(DISTINCT speaker_id) FROM speaker_embeddings" 2>/dev/null | tr -d ' ' || echo "0")
if [ "$speaker_dist" -gt 1 ]; then
    test_result 0 "Multiple speakers in embeddings ($speaker_dist distinct)"
else
    test_result 1 "Speaker distribution (only $speaker_dist speaker)"
fi

# =============================================================================
# TEST 8: End-to-end identification (dry run)
# =============================================================================
echo ""
echo -e "${YELLOW}Testing end-to-end workflow...${NC}"

cd "$(dirname "$0")"
identify_output=$(POSTGRES_DSN="$POSTGRES_DSN" uv run scripts/one_off/identify_speakers.py \
    --video-id "$VIDEO_ID" \
    --start-time 0 \
    --end-time 5 \
    --no-cache 2>&1 | tail -20)

if echo "$identify_output" | grep -q "Identified:"; then
    identified=$(echo "$identify_output" | grep "Identified:" | grep -oE '[0-9]+')
    test_result 0 "Identification workflow ($identified segments identified)"
else
    test_result 1 "Identification workflow (script failed)"
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo "========================================"
echo "  Results: $passed passed, $failed failed"
echo "========================================"
echo ""

if [ $failed -gt 0 ]; then
    echo -e "${RED}Some tests failed. Check the services:${NC}"
    echo "  ./start.sh status"
    echo "  ./start.sh logs"
    exit 1
else
    echo -e "${GREEN}All tests passed! ✨${NC}"
    exit 0
fi

