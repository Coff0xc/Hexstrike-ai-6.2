#!/usr/bin/env python3
"""
HexStrike AI - Performance Configuration (v6.1)

性能优化配置文件
"""

import os
import multiprocessing as mp
from typing import Dict, Any


# ============================================================================
# PERFORMANCE OPTIMIZATION CONFIGURATION
# ============================================================================

class PerformanceConfig:
    """性能优化配置类"""
    
    # ========================================================================
    # HTTP CONNECTION POOL
    # ========================================================================
    CONNECTION_POOL = {
        'max_connections': int(os.getenv('MAX_CONNECTIONS', '100')),
        'max_keepalive': int(os.getenv('MAX_KEEPALIVE', '50')),
        'timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
        'retry_count': int(os.getenv('RETRY_COUNT', '3')),
        'backoff_factor': float(os.getenv('BACKOFF_FACTOR', '0.5'))
    }
    
    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    RATE_LIMIT = {
        'requests_per_second': float(os.getenv('RATE_LIMIT_RPS', '100.0')),
        'burst_size': int(os.getenv('RATE_LIMIT_BURST', '200')),
        'window_size': int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    }
    
    # ========================================================================
    # CIRCUIT BREAKER
    # ========================================================================
    CIRCUIT_BREAKER = {
        'failure_threshold': int(os.getenv('CB_FAILURE_THRESHOLD', '5')),
        'recovery_timeout': int(os.getenv('CB_RECOVERY_TIMEOUT', '60'))
    }
    
    # ========================================================================
    # WORKER POOL
    # ========================================================================
    WORKER_POOL = {
        'min_workers': int(os.getenv('MIN_WORKERS', '2')),
        'max_workers': int(os.getenv('MAX_WORKERS', str(mp.cpu_count() * 2))),
        'worker_type': os.getenv('WORKER_TYPE', 'thread')  # 'thread' or 'process'
    }
    
    # ========================================================================
    # REDIS CACHE (OPTIONAL)
    # ========================================================================
    REDIS = {
        'enabled': os.getenv('REDIS_ENABLED', 'false').lower() in ('true', '1', 'yes'),
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'password': os.getenv('REDIS_PASSWORD'),
        'prefix': os.getenv('REDIS_PREFIX', 'hexstrike:'),
        'ttl': int(os.getenv('REDIS_TTL', '3600'))
    }
    
    # ========================================================================
    # COMPRESSION
    # ========================================================================
    COMPRESSION = {
        'enabled': os.getenv('COMPRESSION_ENABLED', 'true').lower() in ('true', '1', 'yes'),
        'min_size': int(os.getenv('COMPRESSION_MIN_SIZE', '1024')),
        'level': int(os.getenv('COMPRESSION_LEVEL', '6')),  # 1-9 for gzip, 0-11 for brotli
        'prefer_brotli': os.getenv('PREFER_BROTLI', 'true').lower() in ('true', '1', 'yes')
    }
    
    # ========================================================================
    # CACHE WARMUP
    # ========================================================================
    CACHE_WARMUP = {
        'enabled': os.getenv('CACHE_WARMUP_ENABLED', 'true').lower() in ('true', '1', 'yes'),
        'on_startup': os.getenv('CACHE_WARMUP_ON_STARTUP', 'true').lower() in ('true', '1', 'yes'),
        'interval': int(os.getenv('CACHE_WARMUP_INTERVAL', '3600'))  # seconds
    }
    
    # ========================================================================
    # SERVER CONFIGURATION
    # ========================================================================
    SERVER = {
        'workers': int(os.getenv('GUNICORN_WORKERS', str(mp.cpu_count() * 2 + 1))),
        'worker_class': os.getenv('WORKER_CLASS', 'gevent'),  # sync, gevent, uvicorn
        'worker_connections': int(os.getenv('WORKER_CONNECTIONS', '1000')),
        'timeout': int(os.getenv('WORKER_TIMEOUT', '120')),
        'keepalive': int(os.getenv('KEEPALIVE', '5')),
        'max_requests': int(os.getenv('MAX_REQUESTS', '10000')),
        'max_requests_jitter': int(os.getenv('MAX_REQUESTS_JITTER', '1000'))
    }
    
    # ========================================================================
    # LAZY LOADING
    # ========================================================================
    LAZY_LOADING = {
        'enabled': os.getenv('LAZY_LOADING_ENABLED', 'true').lower() in ('true', '1', 'yes'),
        # 需要懒加载的模块列表
        'modules': [
            'selenium',
            'mitmproxy',
            'angr',
            'pwntools'
        ]
    }
    
    # ========================================================================
    # MONITORING
    # ========================================================================
    MONITORING = {
        'enabled': os.getenv('MONITORING_ENABLED', 'true').lower() in ('true', '1', 'yes'),
        'interval': int(os.getenv('MONITORING_INTERVAL', '60')),
        'log_performance': os.getenv('LOG_PERFORMANCE', 'true').lower() in ('true', '1', 'yes')
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取完整配置字典"""
        return {
            'connection_pool': cls.CONNECTION_POOL,
            'rate_limit': cls.RATE_LIMIT,
            'circuit_breaker': cls.CIRCUIT_BREAKER,
            'min_workers': cls.WORKER_POOL['min_workers'],
            'max_workers': cls.WORKER_POOL['max_workers'],
            'worker_type': cls.WORKER_POOL['worker_type'],
            'redis_enabled': cls.REDIS['enabled'],
            'redis_host': cls.REDIS['host'],
            'redis_port': cls.REDIS['port'],
            'redis_db': cls.REDIS['db'],
            'redis_password': cls.REDIS['password'],
            'redis_prefix': cls.REDIS['prefix']
        }
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("\n" + "="*80)
        print("🚀 HexStrike AI Performance Configuration (v6.1)")
        print("="*80)
        
        print("\n📊 Connection Pool:")
        for key, value in cls.CONNECTION_POOL.items():
            print(f"  • {key}: {value}")
        
        print("\n⚡ Rate Limiting:")
        for key, value in cls.RATE_LIMIT.items():
            print(f"  • {key}: {value}")
        
        print("\n🔌 Circuit Breaker:")
        for key, value in cls.CIRCUIT_BREAKER.items():
            print(f"  • {key}: {value}")
        
        print("\n👷 Worker Pool:")
        for key, value in cls.WORKER_POOL.items():
            print(f"  • {key}: {value}")
        
        print("\n💾 Redis Cache:")
        print(f"  • enabled: {cls.REDIS['enabled']}")
        if cls.REDIS['enabled']:
            print(f"  • host: {cls.REDIS['host']}:{cls.REDIS['port']}")
            print(f"  • db: {cls.REDIS['db']}")
            print(f"  • prefix: {cls.REDIS['prefix']}")
        
        print("\n🗜️  Compression:")
        for key, value in cls.COMPRESSION.items():
            print(f"  • {key}: {value}")
        
        print("\n🔥 Cache Warmup:")
        for key, value in cls.CACHE_WARMUP.items():
            print(f"  • {key}: {value}")
        
        print("\n🌐 Server:")
        for key, value in cls.SERVER.items():
            print(f"  • {key}: {value}")
        
        print("\n⏳ Lazy Loading:")
        print(f"  • enabled: {cls.LAZY_LOADING['enabled']}")
        if cls.LAZY_LOADING['enabled']:
            print(f"  • modules: {', '.join(cls.LAZY_LOADING['modules'])}")
        
        print("\n📈 Monitoring:")
        for key, value in cls.MONITORING.items():
            print(f"  • {key}: {value}")
        
        print("\n" + "="*80 + "\n")


# ============================================================================
# ENVIRONMENT TEMPLATE
# ============================================================================

ENV_TEMPLATE = """# HexStrike AI Performance Configuration
# Copy this to .env and customize as needed

# HTTP Connection Pool
MAX_CONNECTIONS=100
MAX_KEEPALIVE=50
REQUEST_TIMEOUT=30
RETRY_COUNT=3
BACKOFF_FACTOR=0.5

# Rate Limiting
RATE_LIMIT_RPS=100.0
RATE_LIMIT_BURST=200
RATE_LIMIT_WINDOW=60

# Circuit Breaker
CB_FAILURE_THRESHOLD=5
CB_RECOVERY_TIMEOUT=60

# Worker Pool
MIN_WORKERS=2
MAX_WORKERS=auto  # Will use CPU count * 2
WORKER_TYPE=thread  # thread or process

# Redis Cache (Optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_PREFIX=hexstrike:
REDIS_TTL=3600

# Response Compression
COMPRESSION_ENABLED=true
COMPRESSION_MIN_SIZE=1024
COMPRESSION_LEVEL=6
PREFER_BROTLI=true

# Cache Warmup
CACHE_WARMUP_ENABLED=true
CACHE_WARMUP_ON_STARTUP=true
CACHE_WARMUP_INTERVAL=3600

# Server Configuration (for production deployment)
GUNICORN_WORKERS=auto  # Will use (CPU * 2) + 1
WORKER_CLASS=gevent  # sync, gevent, or uvicorn
WORKER_CONNECTIONS=1000
WORKER_TIMEOUT=120
KEEPALIVE=5
MAX_REQUESTS=10000
MAX_REQUESTS_JITTER=1000

# Lazy Loading
LAZY_LOADING_ENABLED=true

# Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=60
LOG_PERFORMANCE=true
"""


def create_env_template(output_path: str = '.env.example'):
    """创建环境变量模板文件"""
    with open(output_path, 'w') as f:
        f.write(ENV_TEMPLATE)
    print(f"✅ Environment template created: {output_path}")


if __name__ == "__main__":
    # 打印当前配置
    PerformanceConfig.print_config()
    
    # 创建环境变量模板
    create_env_template()
