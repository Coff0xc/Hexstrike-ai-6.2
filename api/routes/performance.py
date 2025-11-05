#!/usr/bin/env python3
"""
HexStrike AI - Performance Monitoring API Routes (v6.1)

提供性能监控和统计信息的API端点
"""

from flask import Blueprint, jsonify, request
import logging
import psutil
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Create Blueprint
performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

# Global references (will be set by init_app)
_performance_optimizer = None
_middleware_manager = None
_cache_instance = None
_telemetry_instance = None


def init_app(performance_optimizer, middleware_manager, cache_instance=None, telemetry_instance=None):
    """初始化模块"""
    global _performance_optimizer, _middleware_manager, _cache_instance, _telemetry_instance
    _performance_optimizer = performance_optimizer
    _middleware_manager = middleware_manager
    _cache_instance = cache_instance
    _telemetry_instance = telemetry_instance


# ============================================================================
# PERFORMANCE STATS ENDPOINTS
# ============================================================================

@performance_bp.route('/stats', methods=['GET'])
def get_performance_stats():
    """获取综合性能统计"""
    try:
        if not _performance_optimizer:
            return jsonify({
                'success': False,
                'error': 'Performance optimizer not initialized'
            }), 503
        
        # 获取所有统计信息
        stats = _performance_optimizer.get_all_stats()
        
        # 添加中间件统计
        if _middleware_manager:
            stats['middleware'] = _middleware_manager.get_stats()
        
        # 添加缓存统计
        if _cache_instance and hasattr(_cache_instance, 'get_stats'):
            stats['cache'] = _cache_instance.get_stats()
        
        # 添加遥测统计
        if _telemetry_instance and hasattr(_telemetry_instance, 'get_stats'):
            stats['telemetry'] = _telemetry_instance.get_stats()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/stats/connection-pool', methods=['GET'])
def get_connection_pool_stats():
    """获取连接池统计"""
    try:
        if not _performance_optimizer:
            return jsonify({
                'success': False,
                'error': 'Performance optimizer not initialized'
            }), 503
        
        stats = _performance_optimizer.connection_pool.get_stats()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'connection_pool': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting connection pool stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/stats/rate-limiter', methods=['GET'])
def get_rate_limiter_stats():
    """获取限流器统计"""
    try:
        if not _performance_optimizer:
            return jsonify({
                'success': False,
                'error': 'Performance optimizer not initialized'
            }), 503
        
        stats = _performance_optimizer.rate_limiter.get_stats()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'rate_limiter': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting rate limiter stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/stats/circuit-breaker', methods=['GET'])
def get_circuit_breaker_stats():
    """获取熔断器状态"""
    try:
        if not _performance_optimizer:
            return jsonify({
                'success': False,
                'error': 'Performance optimizer not initialized'
            }), 503
        
        state = _performance_optimizer.circuit_breaker.get_state()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'circuit_breaker': {
                'state': state
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting circuit breaker stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/stats/worker-pool', methods=['GET'])
def get_worker_pool_stats():
    """获取工作池统计"""
    try:
        if not _performance_optimizer:
            return jsonify({
                'success': False,
                'error': 'Performance optimizer not initialized'
            }), 503
        
        stats = _performance_optimizer.worker_pool.get_stats()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'worker_pool': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting worker pool stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/stats/lazy-imports', methods=['GET'])
def get_lazy_imports_stats():
    """获取懒加载模块统计"""
    try:
        if not _performance_optimizer:
            return jsonify({
                'success': False,
                'error': 'Performance optimizer not initialized'
            }), 503
        
        stats = _performance_optimizer.lazy_import_manager.get_stats()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'lazy_imports': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting lazy imports stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# SYSTEM RESOURCES ENDPOINTS
# ============================================================================

@performance_bp.route('/system', methods=['GET'])
def get_system_resources():
    """获取系统资源使用情况"""
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存信息
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        # 网络信息
        network = psutil.net_io_counters()
        
        # 进程信息
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'system': {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent
                },
                'swap': {
                    'total_gb': swap.total / (1024**3),
                    'used_gb': swap.used / (1024**3),
                    'percent': swap.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'process': {
                    'rss_mb': process_memory.rss / (1024**2),
                    'vms_mb': process_memory.vms / (1024**2),
                    'cpu_percent': process.cpu_percent(interval=0.1),
                    'num_threads': process.num_threads()
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 基本健康检查
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {}
        }
        
        # 检查性能优化器
        if _performance_optimizer:
            health_status['checks']['performance_optimizer'] = 'ok'
        else:
            health_status['checks']['performance_optimizer'] = 'unavailable'
            health_status['status'] = 'degraded'
        
        # 检查CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 90:
            health_status['checks']['cpu'] = 'warning'
            health_status['status'] = 'degraded'
        else:
            health_status['checks']['cpu'] = 'ok'
        
        # 检查内存使用率
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 90:
            health_status['checks']['memory'] = 'warning'
            health_status['status'] = 'degraded'
        else:
            health_status['checks']['memory'] = 'ok'
        
        # 检查磁盘使用率
        disk_percent = psutil.disk_usage('/').percent
        if disk_percent > 90:
            health_status['checks']['disk'] = 'warning'
            health_status['status'] = 'degraded'
        else:
            health_status['checks']['disk'] = 'ok'
        
        # 检查熔断器状态
        if _performance_optimizer:
            breaker_state = _performance_optimizer.circuit_breaker.get_state()
            if breaker_state == 'open':
                health_status['checks']['circuit_breaker'] = 'open'
                health_status['status'] = 'degraded'
            else:
                health_status['checks']['circuit_breaker'] = breaker_state
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return jsonify({
            'success': True,
            'health': health_status
        }), status_code
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'success': False,
            'health': {
                'status': 'unhealthy',
                'error': str(e)
            }
        }), 503


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@performance_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """获取缓存统计"""
    try:
        if not _cache_instance:
            return jsonify({
                'success': False,
                'error': 'Cache not initialized'
            }), 503
        
        if hasattr(_cache_instance, 'get_stats'):
            stats = _cache_instance.get_stats()
        else:
            stats = {'message': 'Cache stats not available'}
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'cache': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """清空缓存"""
    try:
        if not _cache_instance:
            return jsonify({
                'success': False,
                'error': 'Cache not initialized'
            }), 503
        
        if hasattr(_cache_instance, 'clear'):
            _cache_instance.clear()
            logger.info("Cache cleared successfully")
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_bp.route('/cache/warmup', methods=['POST'])
def trigger_cache_warmup():
    """触发缓存预热"""
    try:
        if not _performance_optimizer or not _performance_optimizer.cache_warmer:
            return jsonify({
                'success': False,
                'error': 'Cache warmer not initialized'
            }), 503
        
        # 触发异步预热
        _performance_optimizer.cache_warmer.warmup(background=True)
        
        return jsonify({
            'success': True,
            'message': 'Cache warmup triggered'
        })
        
    except Exception as e:
        logger.error(f"Error triggering cache warmup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# REDIS CACHE ENDPOINTS
# ============================================================================

@performance_bp.route('/redis/stats', methods=['GET'])
def get_redis_stats():
    """获取Redis统计（如果启用）"""
    try:
        if not _performance_optimizer or not _performance_optimizer.redis_cache:
            return jsonify({
                'success': False,
                'error': 'Redis cache not enabled'
            }), 503
        
        stats = _performance_optimizer.redis_cache.get_stats()
        
        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'redis': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting Redis stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# DASHBOARD ENDPOINT
# ============================================================================

@performance_bp.route('/dashboard', methods=['GET'])
def get_performance_dashboard():
    """获取性能仪表板数据（汇总所有指标）"""
    try:
        dashboard = {
            'timestamp': time.time(),
            'status': 'operational'
        }
        
        # 系统资源
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        dashboard['system'] = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent
        }
        
        # 性能优化器统计
        if _performance_optimizer:
            dashboard['optimizer'] = _performance_optimizer.get_all_stats()
        
        # 中间件统计
        if _middleware_manager:
            dashboard['middleware'] = _middleware_manager.get_stats()
        
        # 健康状态
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            dashboard['status'] = 'warning'
        
        return jsonify({
            'success': True,
            'dashboard': dashboard
        })
        
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
