#!/bin/bash
#
# Database Connectivity Diagnostic Script
# Tests PostgreSQL connectivity from various contexts
#
# Usage: ./test_db_connectivity.sh
#

set -e

echo "=========================================="
echo "PostgreSQL Connectivity Diagnostic"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_connection() {
    local desc="$1"
    local host="$2"
    local port="$3"
    
    echo -n "Testing: $desc ... "
    
    if timeout 2 nc -zv "$host" "$port" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Check if netcat is installed
if ! command -v nc &> /dev/null; then
    echo -e "${RED}ERROR: netcat (nc) is not installed${NC}"
    echo "Install with: sudo apt-get install netcat"
    exit 1
fi

echo "Testing from host (native cron scripts):"
echo "----------------------------------------"
test_connection "localhost:55432 (standard config)" "localhost" "55432"
test_connection "127.0.0.1:55432 (explicit loopback)" "127.0.0.1" "55432"
test_connection "localhost:5432 (restricted port)" "localhost" "5432"
echo ""

echo "Testing from Docker bridge network perspective:"
echo "----------------------------------------------"
test_connection "172.17.0.1:55432 (bridge gateway)" "172.17.0.1" "55432" || true
test_connection "host IP via bridge" "$(ip route get 1 | awk '{print $7}' | head -1)" "55432" || true
echo ""

echo "Checking listening PostgreSQL ports:"
echo "-----------------------------------"
ss -tlnp 2>/dev/null | grep -E "5432|55432" || echo "Could not determine listeners (requires sudo)"
echo ""

echo "Checking running Docker containers:"
echo "-----------------------------------"
docker ps --format "table {{.Names}}\t{{.Networks}}" | head -10
echo ""

echo "Testing container connectivity (if containers are running):"
echo "---------------------------------------------------------"

# Test binance_collector if running
if docker ps --format '{{.Names}}' | grep -q "binance_collector"; then
    echo "Testing from binance_collector container:"
    
    docker exec binance_collector sh -c "command -v nc >/dev/null 2>&1" 2>/dev/null && {
        echo -n "  localhost:55432 ... "
        if docker exec binance_collector nc -zv localhost 55432 >/dev/null 2>&1; then
            echo -e "${GREEN}✓ PASS${NC}"
        else
            echo -e "${RED}✗ FAIL (expected - bridge mode)${NC}"
        fi
        
        echo -n "  172.17.0.1:55432 ... "
        if docker exec binance_collector nc -zv 172.17.0.1 55432 >/dev/null 2>&1; then
            echo -e "${GREEN}✓ PASS${NC}"
        else
            echo -e "${RED}✗ FAIL${NC}"
        fi
    } || echo "  (netcat not available in container)"
else
    echo "  binance_collector: Not running"
fi

# Test collector_manager if running
if docker ps --format '{{.Names}}' | grep -q "collector_manager"; then
    echo "Testing from collector_manager container:"
    
    docker exec collector_manager sh -c "command -v nc >/dev/null 2>&1" 2>/dev/null && {
        echo -n "  localhost:55432 ... "
        if docker exec collector_manager nc -zv localhost 55432 >/dev/null 2>&1; then
            echo -e "${GREEN}✓ PASS${NC}"
        else
            echo -e "${RED}✗ FAIL (expected - bridge mode)${NC}"
        fi
        
        echo -n "  172.17.0.1:55432 ... "
        if docker exec collector_manager nc -zv 172.17.0.1 55432 >/dev/null 2>&1; then
            echo -e "${GREEN}✓ PASS${NC}"
        else
            echo -e "${RED}✗ FAIL${NC}"
        fi
    } || echo "  (netcat not available in container)"
else
    echo "  collector_manager: Not running"
fi

echo ""
echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Host processes (cron scripts) should reach localhost:55432 ✓"
echo "- Bridge-mode containers CANNOT reach localhost:55432 ✗"
echo "- Bridge-mode containers CAN reach 172.17.0.1:55432 ✓"
echo ""
echo "Recommendation:"
echo "- For Docker containers using bridge networking:"
echo "  Change DB_HOST=localhost to DB_HOST=172.17.0.1"
echo "  OR switch to network_mode: host"
echo ""
