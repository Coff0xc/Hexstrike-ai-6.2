#!/bin/bash
# HexStrike AI - Performance Benchmark Script (v6.1)
# 
# 性能基准测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
SERVER_URL=${1:-"http://localhost:8888"}
TOTAL_REQUESTS=${2:-10000}
CONCURRENCY=${3:-100}

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║   📊 HexStrike AI - Performance Benchmark                                ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}Configuration:${NC}"
echo "  Server URL: $SERVER_URL"
echo "  Total Requests: $TOTAL_REQUESTS"
echo "  Concurrency: $CONCURRENCY"
echo ""

# 检查服务器是否运行
echo -e "${YELLOW}Checking server status...${NC}"
if ! curl -s -f "$SERVER_URL/api/performance/health" > /dev/null; then
    echo -e "${RED}❌ Server is not running at $SERVER_URL${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"
echo ""

# 检查测试工具
echo -e "${YELLOW}Checking benchmark tools...${NC}"

HAS_AB=false
HAS_WRK=false

if command -v ab &> /dev/null; then
    HAS_AB=true
    echo -e "${GREEN}✅ Apache Bench (ab) found${NC}"
else
    echo -e "${YELLOW}⚠️  Apache Bench (ab) not found${NC}"
fi

if command -v wrk &> /dev/null; then
    HAS_WRK=true
    echo -e "${GREEN}✅ wrk found${NC}"
else
    echo -e "${YELLOW}⚠️  wrk not found${NC}"
fi

if [ "$HAS_AB" = false ] && [ "$HAS_WRK" = false ]; then
    echo -e "${RED}❌ No benchmark tools found. Please install ab or wrk.${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install apache2-utils wrk"
    echo "  macOS: brew install wrk"
    exit 1
fi

echo ""

# 创建结果目录
RESULTS_DIR="benchmark_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Test 1: Health Check Endpoint${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"

if [ "$HAS_AB" = true ]; then
    echo -e "${BLUE}Running Apache Bench...${NC}"
    ab -n $TOTAL_REQUESTS -c $CONCURRENCY \
       "$SERVER_URL/api/performance/health" \
       2>&1 | tee "$RESULTS_DIR/health_check_ab.txt"
    echo ""
fi

if [ "$HAS_WRK" = true ]; then
    echo -e "${BLUE}Running wrk (30s test)...${NC}"
    wrk -t4 -c$CONCURRENCY -d30s --latency \
        "$SERVER_URL/api/performance/health" \
        2>&1 | tee "$RESULTS_DIR/health_check_wrk.txt"
    echo ""
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Test 2: Performance Stats Endpoint (with compression)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"

if [ "$HAS_AB" = true ]; then
    echo -e "${BLUE}Running Apache Bench with compression...${NC}"
    ab -n $((TOTAL_REQUESTS/2)) -c $((CONCURRENCY/2)) \
       -H "Accept-Encoding: gzip,br" \
       "$SERVER_URL/api/performance/stats" \
       2>&1 | tee "$RESULTS_DIR/stats_ab_compressed.txt"
    echo ""
fi

if [ "$HAS_WRK" = true ]; then
    echo -e "${BLUE}Running wrk with compression...${NC}"
    wrk -t4 -c$((CONCURRENCY/2)) -d20s --latency \
        -H "Accept-Encoding: gzip,br" \
        "$SERVER_URL/api/performance/stats" \
        2>&1 | tee "$RESULTS_DIR/stats_wrk_compressed.txt"
    echo ""
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Test 3: System Resources Endpoint${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"

if [ "$HAS_AB" = true ]; then
    echo -e "${BLUE}Running Apache Bench...${NC}"
    ab -n $((TOTAL_REQUESTS/5)) -c $((CONCURRENCY/2)) \
       "$SERVER_URL/api/performance/system" \
       2>&1 | tee "$RESULTS_DIR/system_ab.txt"
    echo ""
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Test 4: Rate Limiting Test${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"

echo -e "${BLUE}Testing rate limiter...${NC}"
RATE_LIMIT_ERRORS=0
for i in {1..300}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVER_URL/api/performance/health")
    if [ "$STATUS" = "429" ]; then
        ((RATE_LIMIT_ERRORS++))
    fi
done

echo "Rate limit triggers: $RATE_LIMIT_ERRORS / 300"
if [ $RATE_LIMIT_ERRORS -gt 0 ]; then
    echo -e "${GREEN}✅ Rate limiter is working${NC}"
else
    echo -e "${YELLOW}⚠️  Rate limiter might not be active or threshold is high${NC}"
fi
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Test 5: Compression Effectiveness${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"

echo -e "${BLUE}Testing compression...${NC}"

# 无压缩
NO_COMPRESS_SIZE=$(curl -s "$SERVER_URL/api/performance/stats" | wc -c)
echo "Uncompressed size: $NO_COMPRESS_SIZE bytes"

# Gzip压缩
GZIP_SIZE=$(curl -s -H "Accept-Encoding: gzip" "$SERVER_URL/api/performance/stats" | wc -c)
echo "Gzip compressed size: $GZIP_SIZE bytes"
GZIP_RATIO=$(echo "scale=2; 100 * (1 - $GZIP_SIZE / $NO_COMPRESS_SIZE)" | bc)
echo "Gzip compression ratio: ${GZIP_RATIO}%"

# Brotli压缩
BROTLI_SIZE=$(curl -s -H "Accept-Encoding: br" "$SERVER_URL/api/performance/stats" | wc -c)
echo "Brotli compressed size: $BROTLI_SIZE bytes"
BROTLI_RATIO=$(echo "scale=2; 100 * (1 - $BROTLI_SIZE / $NO_COMPRESS_SIZE)" | bc)
echo "Brotli compression ratio: ${BROTLI_RATIO}%"

echo ""

# 生成报告
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Generating Summary Report${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"

REPORT_FILE="$RESULTS_DIR/summary_report.txt"

{
    echo "HexStrike AI - Performance Benchmark Report"
    echo "==========================================="
    echo ""
    echo "Date: $(date)"
    echo "Server: $SERVER_URL"
    echo "Total Requests: $TOTAL_REQUESTS"
    echo "Concurrency: $CONCURRENCY"
    echo ""
    echo "Compression Test:"
    echo "  Uncompressed: $NO_COMPRESS_SIZE bytes"
    echo "  Gzip: $GZIP_SIZE bytes (${GZIP_RATIO}% reduction)"
    echo "  Brotli: $BROTLI_SIZE bytes (${BROTLI_RATIO}% reduction)"
    echo ""
    echo "Rate Limiting:"
    echo "  Triggers: $RATE_LIMIT_ERRORS / 300"
    echo ""
    echo "Detailed results saved in: $RESULTS_DIR/"
    echo ""
} > "$REPORT_FILE"

cat "$REPORT_FILE"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Benchmark Complete!${NC}"
echo -e "${GREEN}Results saved to: $RESULTS_DIR/${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
