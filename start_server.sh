#!/bin/bash
# HexStrike AI - Production Server Startup Script (v6.1)
# 
# 使用方法:
#   ./start_server.sh             # 生产模式（使用gunicorn）
#   ./start_server.sh dev         # 开发模式（使用Flask内置服务器）
#   ./start_server.sh test        # 测试性能配置

set -e  # 遇到错误立即退出

# ============================================================================
# 颜色定义
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# 函数定义
# ============================================================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                           ║"
    echo "║   🚀 HexStrike AI - Server Launcher (v6.1)                               ║"
    echo "║                                                                           ║"
    echo "║   ⚡ Performance Optimized Edition                                       ║"
    echo "║                                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_dependencies() {
    echo -e "${BLUE}📦 Checking dependencies...${NC}"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "hexstrike_env" ]; then
        echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
        python3 -m venv hexstrike_env
    fi
    
    # 激活虚拟环境
    source hexstrike_env/bin/activate
    
    # 检查必要的包
    echo -e "${BLUE}📦 Checking required packages...${NC}"
    python3 -c "import flask" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Installing dependencies...${NC}"
        pip install -q -r requirements.txt
    }
    
    echo -e "${GREEN}✅ Dependencies OK${NC}"
}

load_env() {
    # 加载环境变量
    if [ -f ".env" ]; then
        echo -e "${BLUE}📄 Loading environment variables from .env${NC}"
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo -e "${YELLOW}⚠️  No .env file found. Using defaults.${NC}"
    fi
}

start_production() {
    echo -e "${GREEN}🚀 Starting in PRODUCTION mode with Gunicorn...${NC}"
    
    # 检查gunicorn是否安装
    if ! python3 -c "import gunicorn" 2>/dev/null; then
        echo -e "${RED}❌ Gunicorn not installed. Installing...${NC}"
        pip install gunicorn gevent
    fi
    
    # 显示配置
    echo -e "${CYAN}Configuration:${NC}"
    echo -e "  Host: ${HEXSTRIKE_HOST:-0.0.0.0}"
    echo -e "  Port: ${HEXSTRIKE_PORT:-8888}"
    echo -e "  Workers: ${GUNICORN_WORKERS:-auto}"
    echo -e "  Worker Class: ${WORKER_CLASS:-gevent}"
    echo ""
    
    # 启动gunicorn
    exec gunicorn \
        --config gunicorn.conf.py \
        "hexstrike_server:app"
}

start_development() {
    echo -e "${YELLOW}🔧 Starting in DEVELOPMENT mode with Flask...${NC}"
    
    export DEBUG_MODE=1
    export FLASK_ENV=development
    
    # 显示配置
    echo -e "${CYAN}Configuration:${NC}"
    echo -e "  Host: ${HEXSTRIKE_HOST:-127.0.0.1}"
    echo -e "  Port: ${HEXSTRIKE_PORT:-8888}"
    echo -e "  Debug: ON"
    echo ""
    
    # 启动Flask开发服务器
    exec python3 hexstrike_server.py --debug --port ${HEXSTRIKE_PORT:-8888}
}

test_config() {
    echo -e "${BLUE}🧪 Testing performance configuration...${NC}"
    
    # 测试性能配置
    python3 -c "
from config.performance import PerformanceConfig
PerformanceConfig.print_config()
"
    
    echo -e "${GREEN}✅ Configuration test complete${NC}"
}

show_help() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  (none)      - Start in production mode with Gunicorn (default)"
    echo "  dev         - Start in development mode with Flask"
    echo "  test        - Test performance configuration"
    echo "  help        - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  HEXSTRIKE_HOST        - Server host (default: 0.0.0.0 for prod, 127.0.0.1 for dev)"
    echo "  HEXSTRIKE_PORT        - Server port (default: 8888)"
    echo "  GUNICORN_WORKERS      - Number of workers (default: auto)"
    echo "  WORKER_CLASS          - Worker class (default: gevent)"
    echo "  REDIS_ENABLED         - Enable Redis cache (default: false)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start production server"
    echo "  $0 dev                # Start development server"
    echo "  HEXSTRIKE_PORT=9000 $0 dev  # Start on port 9000"
}

cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    # 清理逻辑（如果需要）
    exit 0
}

# ============================================================================
# 主逻辑
# ============================================================================

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 打印banner
print_banner

# 解析参数
MODE=${1:-production}

case $MODE in
    prod|production)
        check_dependencies
        load_env
        start_production
        ;;
    dev|development)
        check_dependencies
        load_env
        start_development
        ;;
    test)
        check_dependencies
        test_config
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown mode: $MODE${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
