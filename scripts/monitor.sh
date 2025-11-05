#!/bin/bash
# HexStrike AI - Real-time Performance Monitor (v6.1)
# 
# 实时性能监控脚本

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
REFRESH_INTERVAL=${2:-5}

clear

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║   📊 HexStrike AI - Real-time Performance Monitor                        ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${BLUE}Server: $SERVER_URL${NC}"
echo -e "${BLUE}Refresh Interval: ${REFRESH_INTERVAL}s${NC}"
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
echo ""

# 检查依赖
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ jq not found. Please install: sudo apt-get install jq${NC}"
    exit 1
fi

# 检查服务器
if ! curl -s -f "$SERVER_URL/api/performance/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running at $SERVER_URL${NC}"
    exit 1
fi

# 监控循环
while true; do
    clear
    
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║         HexStrike AI - Performance Dashboard ($(date +"%H:%M:%S"))              ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    # 获取数据
    DASHBOARD=$(curl -s "$SERVER_URL/api/performance/dashboard")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to fetch performance data${NC}"
        sleep $REFRESH_INTERVAL
        continue
    fi
    
    # 系统状态
    STATUS=$(echo "$DASHBOARD" | jq -r '.dashboard.status')
    if [ "$STATUS" = "operational" ]; then
        STATUS_COLOR=$GREEN
        STATUS_ICON="✅"
    else
        STATUS_COLOR=$YELLOW
        STATUS_ICON="⚠️ "
    fi
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}System Status${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  Status: ${STATUS_COLOR}${STATUS_ICON} $STATUS${NC}"
    echo ""
    
    # 系统资源
    CPU=$(echo "$DASHBOARD" | jq -r '.dashboard.system.cpu_percent')
    MEMORY=$(echo "$DASHBOARD" | jq -r '.dashboard.system.memory_percent')
    DISK=$(echo "$DASHBOARD" | jq -r '.dashboard.system.disk_percent')
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}System Resources${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # CPU条形图
    CPU_INT=$(printf "%.0f" "$CPU")
    CPU_BAR=$(printf '█%.0s' $(seq 1 $((CPU_INT/2))))
    if [ $CPU_INT -gt 80 ]; then
        CPU_COLOR=$RED
    elif [ $CPU_INT -gt 60 ]; then
        CPU_COLOR=$YELLOW
    else
        CPU_COLOR=$GREEN
    fi
    echo -e "  CPU:    ${CPU_COLOR}${CPU_BAR}${NC} ${CPU}%"
    
    # Memory条形图
    MEMORY_INT=$(printf "%.0f" "$MEMORY")
    MEMORY_BAR=$(printf '█%.0s' $(seq 1 $((MEMORY_INT/2))))
    if [ $MEMORY_INT -gt 80 ]; then
        MEMORY_COLOR=$RED
    elif [ $MEMORY_INT -gt 60 ]; then
        MEMORY_COLOR=$YELLOW
    else
        MEMORY_COLOR=$GREEN
    fi
    echo -e "  Memory: ${MEMORY_COLOR}${MEMORY_BAR}${NC} ${MEMORY}%"
    
    # Disk条形图
    DISK_INT=$(printf "%.0f" "$DISK")
    DISK_BAR=$(printf '█%.0s' $(seq 1 $((DISK_INT/2))))
    if [ $DISK_INT -gt 80 ]; then
        DISK_COLOR=$RED
    elif [ $DISK_INT -gt 60 ]; then
        DISK_COLOR=$YELLOW
    else
        DISK_COLOR=$GREEN
    fi
    echo -e "  Disk:   ${DISK_COLOR}${DISK_BAR}${NC} ${DISK}%"
    echo ""
    
    # 连接池统计
    if echo "$DASHBOARD" | jq -e '.dashboard.optimizer.connection_pool' > /dev/null 2>&1; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}Connection Pool${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        CP_REQUESTS=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.connection_pool.requests // 0')
        CP_ERRORS=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.connection_pool.errors // 0')
        CP_AVG_TIME=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.connection_pool.avg_response_time // 0')
        CP_POOL_SIZE=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.connection_pool.pool_size // 0')
        
        echo -e "  Total Requests:   $CP_REQUESTS"
        echo -e "  Errors:           $CP_ERRORS"
        echo -e "  Avg Response:     ${CP_AVG_TIME}s"
        echo -e "  Active Conns:     $CP_POOL_SIZE"
        echo ""
    fi
    
    # 限流器统计
    if echo "$DASHBOARD" | jq -e '.dashboard.optimizer.rate_limiter' > /dev/null 2>&1; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}Rate Limiter${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        RL_ALLOWED=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.rate_limiter.allowed // 0')
        RL_REJECTED=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.rate_limiter.rejected // 0')
        RL_RATE=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.rate_limiter.current_rate // 0')
        
        echo -e "  Allowed:          ${GREEN}$RL_ALLOWED${NC}"
        echo -e "  Rejected:         ${RED}$RL_REJECTED${NC}"
        echo -e "  Success Rate:     $(echo "$RL_RATE * 100" | bc -l | xargs printf "%.1f")%"
        echo ""
    fi
    
    # 工作池统计
    if echo "$DASHBOARD" | jq -e '.dashboard.optimizer.worker_pool' > /dev/null 2>&1; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}Worker Pool${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        WP_SUBMITTED=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.worker_pool.submitted // 0')
        WP_COMPLETED=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.worker_pool.completed // 0')
        WP_FAILED=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.worker_pool.failed // 0')
        WP_QUEUE=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.worker_pool.queue_size // 0')
        WP_WORKERS=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.worker_pool.workers // 0')
        
        echo -e "  Submitted:        $WP_SUBMITTED"
        echo -e "  Completed:        ${GREEN}$WP_COMPLETED${NC}"
        echo -e "  Failed:           ${RED}$WP_FAILED${NC}"
        echo -e "  Queue Size:       $WP_QUEUE"
        echo -e "  Active Workers:   $WP_WORKERS"
        echo ""
    fi
    
    # 熔断器状态
    if echo "$DASHBOARD" | jq -e '.dashboard.optimizer.circuit_breaker_state' > /dev/null 2>&1; then
        CB_STATE=$(echo "$DASHBOARD" | jq -r '.dashboard.optimizer.circuit_breaker_state')
        
        case $CB_STATE in
            "closed")
                CB_COLOR=$GREEN
                CB_ICON="✅"
                ;;
            "half_open")
                CB_COLOR=$YELLOW
                CB_ICON="⚠️ "
                ;;
            "open")
                CB_COLOR=$RED
                CB_ICON="❌"
                ;;
            *)
                CB_COLOR=$NC
                CB_ICON="❓"
                ;;
        esac
        
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}Circuit Breaker${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "  State: ${CB_COLOR}${CB_ICON} $CB_STATE${NC}"
        echo ""
    fi
    
    # 中间件统计
    if echo "$DASHBOARD" | jq -e '.dashboard.middleware.performance' > /dev/null 2>&1; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}Middleware Performance${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        MW_TOTAL=$(echo "$DASHBOARD" | jq -r '.dashboard.middleware.performance.total_requests // 0')
        MW_AVG=$(echo "$DASHBOARD" | jq -r '.dashboard.middleware.performance.avg_time // 0')
        MW_SLOWEST=$(echo "$DASHBOARD" | jq -r '.dashboard.middleware.performance.slowest // 0')
        MW_FASTEST=$(echo "$DASHBOARD" | jq -r '.dashboard.middleware.performance.fastest // 0')
        
        echo -e "  Total Requests:   $MW_TOTAL"
        echo -e "  Avg Time:         ${MW_AVG}s"
        echo -e "  Slowest:          ${MW_SLOWEST}s"
        echo -e "  Fastest:          ${MW_FASTEST}s"
        echo ""
    fi
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Next refresh in ${REFRESH_INTERVAL}s... (Press Ctrl+C to exit)${NC}"
    
    sleep $REFRESH_INTERVAL
done
