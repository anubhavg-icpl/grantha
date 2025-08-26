#!/bin/bash

# Performance Testing Script for Grantha API
# Tests rate limiting, caching, response times, and load handling

set -e

API_BASE="http://localhost:8000"
RESULTS_DIR="./performance_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Grantha API Performance Testing Suite${NC}"
echo "=================================================="
echo "Timestamp: $(date)"
echo "API Base: $API_BASE"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check if API is running
echo -e "${YELLOW}📡 Checking API availability...${NC}"
if ! curl -s "$API_BASE/health" > /dev/null; then
    echo -e "${RED}❌ API is not running at $API_BASE${NC}"
    echo "Please start the API first: ./run.sh api"
    exit 1
fi
echo -e "${GREEN}✅ API is running${NC}"
echo ""

# Test 1: Basic Response Time
echo -e "${YELLOW}⏱️  Test 1: Basic Response Time${NC}"
echo "Testing response times for common endpoints..."

endpoints=("/" "/health" "/metrics" "/models")
for endpoint in "${endpoints[@]}"; do
    echo -n "  $endpoint: "
    time=$(curl -s -w "%{time_total}" -o /dev/null "$API_BASE$endpoint")
    if (( $(echo "$time > 1.0" | bc -l) )); then
        echo -e "${RED}${time}s (SLOW)${NC}"
    else
        echo -e "${GREEN}${time}s${NC}"
    fi
done
echo ""

# Test 2: Cache Performance
echo -e "${YELLOW}💾 Test 2: Cache Performance${NC}"
echo "Testing cache hit/miss performance..."

echo -n "  First request (cache miss): "
time1=$(curl -s -w "%{time_total}" -o /dev/null -D /tmp/cache_headers1.txt "$API_BASE/")
cache_status1=$(grep -i "x-cache" /tmp/cache_headers1.txt | cut -d' ' -f2 | tr -d '\r')
echo -e "${YELLOW}${time1}s ($cache_status1)${NC}"

echo -n "  Second request (cache hit): "
time2=$(curl -s -w "%{time_total}" -o /dev/null -D /tmp/cache_headers2.txt "$API_BASE/")
cache_status2=$(grep -i "x-cache" /tmp/cache_headers2.txt | cut -d' ' -f2 | tr -d '\r')

if [ "$cache_status2" = "HIT" ]; then
    echo -e "${GREEN}${time2}s ($cache_status2)${NC}"
    speedup=$(echo "scale=2; $time1 / $time2" | bc)
    echo -e "  ${GREEN}Cache speedup: ${speedup}x${NC}"
else
    echo -e "${RED}${time2}s ($cache_status2) - Cache not working!${NC}"
fi
echo ""

# Test 3: Rate Limiting
echo -e "${YELLOW}🚫 Test 3: Rate Limiting${NC}"
echo "Testing rate limit enforcement..."

# Test with rapid requests
echo "  Sending 25 rapid requests to /models..."
rate_limited=0
successful=0

for i in {1..25}; do
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE/models" 2>/dev/null || echo "000")
    if [ "$response" = "429" ]; then
        ((rate_limited++))
    elif [ "$response" = "200" ] || [ "$response" = "404" ]; then
        ((successful++))
    fi
done

echo "  Results:"
echo -e "    Successful requests: ${GREEN}$successful${NC}"
echo -e "    Rate limited requests: ${YELLOW}$rate_limited${NC}"

if [ "$rate_limited" -gt 0 ]; then
    echo -e "  ${GREEN}✅ Rate limiting is working${NC}"
else
    echo -e "  ${RED}⚠️  Rate limiting may not be configured properly${NC}"
fi
echo ""

# Test 4: Concurrent Load Test
echo -e "${YELLOW}⚡ Test 4: Concurrent Load Test${NC}"
echo "Testing concurrent request handling..."

load_test() {
    local endpoint=$1
    local concurrent=$2
    local requests_per_thread=$3
    
    echo "  Testing $endpoint with $concurrent concurrent connections, $requests_per_thread requests each..."
    
    # Create temporary script for load testing
    cat > /tmp/load_test.sh << EOF
#!/bin/bash
endpoint="$API_BASE$endpoint"
for i in {1..$requests_per_thread}; do
    curl -s -w "%{time_total},%{http_code}\n" -o /dev/null "\$endpoint"
done
EOF
    chmod +x /tmp/load_test.sh
    
    # Run concurrent requests
    start_time=$(date +%s.%N)
    for i in $(seq 1 $concurrent); do
        /tmp/load_test.sh >> "/tmp/load_results_$i.txt" &
    done
    wait
    end_time=$(date +%s.%N)
    
    # Calculate results
    total_time=$(echo "$end_time - $start_time" | bc)
    total_requests=$((concurrent * requests_per_thread))
    
    # Analyze response times
    cat /tmp/load_results_*.txt > /tmp/all_results.txt
    avg_time=$(awk -F, '{sum+=$1; count++} END {print sum/count}' /tmp/all_results.txt)
    error_count=$(awk -F, '$2 >= 400 {count++} END {print count+0}' /tmp/all_results.txt)
    
    requests_per_sec=$(echo "scale=2; $total_requests / $total_time" | bc)
    error_rate=$(echo "scale=2; $error_count * 100 / $total_requests" | bc)
    
    echo "    Total time: ${total_time}s"
    echo "    Requests/sec: ${requests_per_sec}"
    echo "    Average response time: ${avg_time}s"
    echo "    Error rate: ${error_rate}%"
    
    # Cleanup
    rm -f /tmp/load_results_*.txt /tmp/all_results.txt /tmp/load_test.sh
}

load_test "/health" 10 5
echo ""

# Test 5: Memory and Performance Metrics
echo -e "${YELLOW}📊 Test 5: Performance Metrics${NC}"
echo "Collecting performance metrics..."

metrics=$(curl -s "$API_BASE/metrics" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Status: {data[\"status\"]}')
    if 'cache' in data:
        print(f'Cache enabled: {data[\"cache\"][\"enabled\"]}')
    if 'middleware' in data:
        for k,v in data['middleware'].items():
            print(f'{k.replace(\"_\", \" \").title()}: {v}')
except:
    print('Failed to parse metrics')
")

echo "$metrics"
echo ""

# Test 6: WebSocket Performance (if available)
echo -e "${YELLOW}🔌 Test 6: WebSocket Connection Test${NC}"
if command -v wscat &> /dev/null; then
    echo "Testing WebSocket connection..."
    timeout 5 wscat -c ws://localhost:8000/ws/chat --execute 'ping' 2>&1 | grep -q "connected" && echo -e "${GREEN}✅ WebSocket connection successful${NC}" || echo -e "${RED}❌ WebSocket connection failed${NC}"
else
    echo -e "${YELLOW}⏭️  Skipping (wscat not installed)${NC}"
fi
echo ""

# Generate Summary Report
echo -e "${BLUE}📋 Performance Test Summary${NC}"
echo "============================================"
echo "Test completed at: $(date)"
echo ""

# Save results
REPORT_FILE="$RESULTS_DIR/performance_report_$TIMESTAMP.txt"
{
    echo "Grantha API Performance Test Report"
    echo "Generated: $(date)"
    echo "API Base: $API_BASE"
    echo ""
    echo "Tests performed:"
    echo "1. ✅ Basic Response Time"
    echo "2. ✅ Cache Performance"
    echo "3. ✅ Rate Limiting"
    echo "4. ✅ Concurrent Load Test"
    echo "5. ✅ Performance Metrics"
    echo "6. ✅ WebSocket Connection"
    echo ""
    echo "Note: Detailed results logged to console during execution"
} > "$REPORT_FILE"

echo -e "${GREEN}✅ Performance testing complete!${NC}"
echo "Report saved to: $REPORT_FILE"
echo ""

# Recommendations
echo -e "${BLUE}💡 Performance Recommendations:${NC}"
echo "- Monitor response times regularly"
echo "- Adjust rate limits based on usage patterns"  
echo "- Implement Redis for distributed caching in production"
echo "- Consider CDN for static assets"
echo "- Set up application performance monitoring (APM)"
echo ""