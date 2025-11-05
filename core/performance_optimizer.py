#!/usr/bin/env python3
"""
HexStrike AI - Performance Optimization Module (v6.1)

性能优化核心模块，提供:
- 连接池管理
- 响应压缩
- 限流和熔断
- 智能缓存预热
- 资源监控优化
- 并发控制
"""

import asyncio
import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import json
import gzip
import brotli
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
import psutil

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# HTTP CONNECTION POOL MANAGER
# ============================================================================

@dataclass
class ConnectionPoolConfig:
    """连接池配置"""
    max_connections: int = 100
    max_keepalive: int = 50
    timeout: int = 30
    retry_count: int = 3
    backoff_factor: float = 0.5


class HTTPConnectionPool:
    """HTTP连接池管理器"""
    
    def __init__(self, config: Optional[ConnectionPoolConfig] = None):
        self.config = config or ConnectionPoolConfig()
        self.session = None
        self.connector = None
        self._lock = threading.Lock()
        self.stats = {
            'requests': 0,
            'errors': 0,
            'avg_response_time': 0.0,
            'pool_size': 0
        }
        
    async def get_session(self) -> 'aiohttp.ClientSession':
        """获取或创建连接池会话"""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not available")
            
        if self.session is None or self.session.closed:
            with self._lock:
                if self.session is None or self.session.closed:
                    self.connector = aiohttp.TCPConnector(
                        limit=self.config.max_connections,
                        limit_per_host=self.config.max_keepalive,
                        ttl_dns_cache=300,
                        force_close=False,
                        enable_cleanup_closed=True
                    )
                    
                    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                    
                    self.session = aiohttp.ClientSession(
                        connector=self.connector,
                        timeout=timeout
                    )
                    
        return self.session
    
    async def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """执行HTTP请求（带重试和统计）"""
        session = await self.get_session()
        start_time = time.time()
        
        for attempt in range(self.config.retry_count):
            try:
                async with session.request(method, url, **kwargs) as response:
                    content = await response.read()
                    
                    # 更新统计
                    elapsed = time.time() - start_time
                    self._update_stats(elapsed, success=True)
                    
                    return {
                        'status': response.status,
                        'headers': dict(response.headers),
                        'content': content,
                        'elapsed': elapsed
                    }
                    
            except Exception as e:
                if attempt == self.config.retry_count - 1:
                    self._update_stats(time.time() - start_time, success=False)
                    raise
                
                # 指数退避
                await asyncio.sleep(self.config.backoff_factor * (2 ** attempt))
    
    def _update_stats(self, elapsed: float, success: bool):
        """更新统计信息"""
        with self._lock:
            self.stats['requests'] += 1
            if not success:
                self.stats['errors'] += 1
            
            # 移动平均
            alpha = 0.1
            self.stats['avg_response_time'] = (
                alpha * elapsed + 
                (1 - alpha) * self.stats['avg_response_time']
            )
            
            if self.connector:
                self.stats['pool_size'] = len(self.connector._conns)
    
    async def close(self):
        """关闭连接池"""
        if self.session and not self.session.closed:
            await self.session.close()
        if self.connector:
            await self.connector.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return self.stats.copy()


# ============================================================================
# RESPONSE COMPRESSION MIDDLEWARE
# ============================================================================

class CompressionMiddleware:
    """响应压缩中间件（支持gzip和brotli）"""
    
    # 需要压缩的内容类型
    COMPRESSIBLE_TYPES = {
        'text/html', 'text/css', 'text/javascript', 'text/plain',
        'application/json', 'application/javascript', 'application/xml',
        'text/xml'
    }
    
    # 最小压缩大小（字节）
    MIN_COMPRESS_SIZE = 1024
    
    @staticmethod
    def should_compress(content_type: str, content_length: int) -> bool:
        """判断是否需要压缩"""
        if content_length < CompressionMiddleware.MIN_COMPRESS_SIZE:
            return False
        
        for ct in CompressionMiddleware.COMPRESSIBLE_TYPES:
            if ct in content_type.lower():
                return True
        
        return False
    
    @staticmethod
    def compress_response(data: bytes, encoding: str = 'gzip') -> tuple[bytes, str]:
        """压缩响应数据"""
        if encoding == 'br' and brotli:
            # Brotli压缩（更高压缩率）
            compressed = brotli.compress(data, quality=4)
            return compressed, 'br'
        elif encoding == 'gzip':
            # Gzip压缩（更通用）
            compressed = gzip.compress(data, compresslevel=6)
            return compressed, 'gzip'
        
        return data, 'identity'
    
    @staticmethod
    def get_accepted_encoding(accept_encoding: str) -> str:
        """获取客户端支持的最佳压缩方式"""
        if not accept_encoding:
            return 'identity'
        
        encodings = accept_encoding.lower().split(',')
        encodings = [e.strip() for e in encodings]
        
        # 优先使用brotli（如果可用）
        if 'br' in encodings and brotli:
            return 'br'
        elif 'gzip' in encodings:
            return 'gzip'
        
        return 'identity'


# ============================================================================
# RATE LIMITER AND CIRCUIT BREAKER
# ============================================================================

@dataclass
class RateLimitConfig:
    """限流配置"""
    requests_per_second: float = 100.0
    burst_size: int = 200
    window_size: int = 60  # 秒


class TokenBucketRateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.tokens = self.config.burst_size
        self.last_update = time.time()
        self._lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'allowed': 0,
            'rejected': 0,
            'current_rate': 0.0
        }
    
    def allow_request(self) -> bool:
        """检查是否允许请求"""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # 添加新令牌
            self.tokens = min(
                self.config.burst_size,
                self.tokens + elapsed * self.config.requests_per_second
            )
            self.last_update = now
            
            # 尝试消耗令牌
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                self.stats['allowed'] += 1
                return True
            
            self.stats['rejected'] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = self.stats['allowed'] + self.stats['rejected']
            if total > 0:
                self.stats['current_rate'] = self.stats['allowed'] / total
            return self.stats.copy()


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception


class CircuitBreaker:
    """熔断器模式实现"""
    
    class State:
        CLOSED = "closed"  # 正常状态
        OPEN = "open"      # 熔断状态
        HALF_OPEN = "half_open"  # 半开状态（尝试恢复）
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.State.CLOSED
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数调用（带熔断保护）"""
        with self._lock:
            # 检查是否需要尝试恢复
            if self.state == self.State.OPEN:
                if self._should_attempt_reset():
                    self.state = self.State.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置"""
        if self.last_failure_time is None:
            return False
        
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _on_success(self):
        """成功回调"""
        with self._lock:
            self.failure_count = 0
            if self.state == self.State.HALF_OPEN:
                self.state = self.State.CLOSED
    
    def _on_failure(self):
        """失败回调"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = self.State.OPEN
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> str:
        """获取当前状态"""
        with self._lock:
            return self.state


# ============================================================================
# INTELLIGENT CACHE WARMER
# ============================================================================

class CacheWarmer:
    """智能缓存预热器"""
    
    def __init__(self, cache_instance, warmup_tasks: Optional[List[Dict[str, Any]]] = None):
        self.cache = cache_instance
        self.warmup_tasks = warmup_tasks or []
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.stats = {
            'warmed': 0,
            'failed': 0,
            'last_warmup': None
        }
    
    def add_warmup_task(self, key: str, func: Callable, *args, **kwargs):
        """添加预热任务"""
        self.warmup_tasks.append({
            'key': key,
            'func': func,
            'args': args,
            'kwargs': kwargs
        })
    
    def warmup(self, background: bool = True):
        """执行缓存预热"""
        if background:
            self.executor.submit(self._do_warmup)
        else:
            self._do_warmup()
    
    def _do_warmup(self):
        """执行预热逻辑"""
        logger.info(f"Starting cache warmup with {len(self.warmup_tasks)} tasks")
        start_time = time.time()
        
        for task in self.warmup_tasks:
            try:
                result = task['func'](*task['args'], **task['kwargs'])
                self.cache.set(task['key'], result)
                self.stats['warmed'] += 1
            except Exception as e:
                logger.error(f"Cache warmup failed for {task['key']}: {e}")
                self.stats['failed'] += 1
        
        elapsed = time.time() - start_time
        self.stats['last_warmup'] = datetime.now().isoformat()
        logger.info(f"Cache warmup completed in {elapsed:.2f}s: {self.stats['warmed']} warmed, {self.stats['failed']} failed")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


# ============================================================================
# REDIS CACHE ADAPTER
# ============================================================================

class RedisCache:
    """Redis缓存适配器"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, prefix: str = 'hexstrike:'):
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis not available. Install with: pip install redis")
        
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False
        )
        self.prefix = prefix
        
    def _make_key(self, key: str) -> str:
        """生成完整的键名"""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            data = self.redis.get(self._make_key(key))
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        try:
            data = json.dumps(value)
            self.redis.setex(self._make_key(key), ttl, data)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """删除缓存值"""
        try:
            self.redis.delete(self._make_key(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    def clear(self):
        """清空所有缓存"""
        try:
            keys = self.redis.keys(f"{self.prefix}*")
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Redis统计信息"""
        try:
            info = self.redis.info()
            return {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {}


# ============================================================================
# ADVANCED WORKER POOL
# ============================================================================

class AdaptiveWorkerPool:
    """自适应工作池（根据负载动态调整）"""
    
    def __init__(self, min_workers: int = 2, max_workers: int = None, 
                 worker_type: str = 'thread'):
        self.min_workers = min_workers
        self.max_workers = max_workers or (mp.cpu_count() * 2)
        self.worker_type = worker_type
        self.current_workers = min_workers
        
        if worker_type == 'process':
            self.executor = ProcessPoolExecutor(max_workers=min_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=min_workers)
        
        self.pending_tasks = deque()
        self.stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'queue_size': 0,
            'workers': self.current_workers
        }
        self._lock = threading.Lock()
        
        # 启动监控线程
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def submit(self, func: Callable, *args, **kwargs):
        """提交任务"""
        with self._lock:
            self.stats['submitted'] += 1
            future = self.executor.submit(func, *args, **kwargs)
            future.add_done_callback(self._task_done_callback)
            return future
    
    def _task_done_callback(self, future):
        """任务完成回调"""
        with self._lock:
            if future.exception():
                self.stats['failed'] += 1
            else:
                self.stats['completed'] += 1
    
    def _monitor_loop(self):
        """监控循环（动态调整工作者数量）"""
        while True:
            time.sleep(5)
            self._adjust_workers()
    
    def _adjust_workers(self):
        """根据负载调整工作者数量"""
        with self._lock:
            queue_size = self.stats['submitted'] - self.stats['completed']
            self.stats['queue_size'] = queue_size
            
            # 简单的调整策略
            if queue_size > self.current_workers * 2 and self.current_workers < self.max_workers:
                # 增加工作者
                new_workers = min(self.current_workers + 2, self.max_workers)
                logger.info(f"Increasing workers from {self.current_workers} to {new_workers}")
                self.current_workers = new_workers
                # Note: ThreadPoolExecutor不支持动态调整，这里只是记录
            
            elif queue_size == 0 and self.current_workers > self.min_workers:
                # 减少工作者（当队列为空时）
                new_workers = max(self.current_workers - 1, self.min_workers)
                logger.info(f"Decreasing workers from {self.current_workers} to {new_workers}")
                self.current_workers = new_workers
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return self.stats.copy()
    
    def shutdown(self, wait: bool = True):
        """关闭工作池"""
        self.executor.shutdown(wait=wait)


# ============================================================================
# LAZY IMPORT MANAGER
# ============================================================================

class LazyImportManager:
    """懒加载导入管理器"""
    
    def __init__(self):
        self._modules = {}
        self._load_times = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, import_func: Callable):
        """注册懒加载模块"""
        with self._lock:
            self._modules[name] = {
                'import_func': import_func,
                'module': None,
                'loaded': False
            }
    
    def get(self, name: str) -> Any:
        """获取模块（按需加载）"""
        if name not in self._modules:
            raise ValueError(f"Module {name} not registered")
        
        module_info = self._modules[name]
        
        if not module_info['loaded']:
            with self._lock:
                if not module_info['loaded']:  # Double-check
                    start_time = time.time()
                    try:
                        module_info['module'] = module_info['import_func']()
                        module_info['loaded'] = True
                        elapsed = time.time() - start_time
                        self._load_times[name] = elapsed
                        logger.info(f"Lazy loaded module '{name}' in {elapsed:.3f}s")
                    except Exception as e:
                        logger.error(f"Failed to lazy load module '{name}': {e}")
                        raise
        
        return module_info['module']
    
    def is_loaded(self, name: str) -> bool:
        """检查模块是否已加载"""
        return name in self._modules and self._modules[name]['loaded']
    
    def get_stats(self) -> Dict[str, Any]:
        """获取加载统计"""
        with self._lock:
            return {
                'registered': len(self._modules),
                'loaded': sum(1 for m in self._modules.values() if m['loaded']),
                'load_times': self._load_times.copy()
            }


# ============================================================================
# PERFORMANCE OPTIMIZER FACADE
# ============================================================================

class PerformanceOptimizer:
    """性能优化器门面类（统一管理所有优化组件）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 初始化各个组件
        self.connection_pool = HTTPConnectionPool(
            ConnectionPoolConfig(**self.config.get('connection_pool', {}))
        )
        
        self.rate_limiter = TokenBucketRateLimiter(
            RateLimitConfig(**self.config.get('rate_limit', {}))
        )
        
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(**self.config.get('circuit_breaker', {}))
        )
        
        self.worker_pool = AdaptiveWorkerPool(
            min_workers=self.config.get('min_workers', 2),
            max_workers=self.config.get('max_workers', mp.cpu_count() * 2),
            worker_type=self.config.get('worker_type', 'thread')
        )
        
        self.lazy_import_manager = LazyImportManager()
        
        # Redis缓存（可选）
        self.redis_cache = None
        if self.config.get('redis_enabled', False):
            try:
                self.redis_cache = RedisCache(
                    host=self.config.get('redis_host', 'localhost'),
                    port=self.config.get('redis_port', 6379),
                    db=self.config.get('redis_db', 0),
                    password=self.config.get('redis_password'),
                    prefix=self.config.get('redis_prefix', 'hexstrike:')
                )
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
        
        # 缓存预热器
        self.cache_warmer = None
    
    def init_cache_warmer(self, cache_instance):
        """初始化缓存预热器"""
        self.cache_warmer = CacheWarmer(cache_instance)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有性能统计"""
        stats = {
            'connection_pool': self.connection_pool.get_stats(),
            'rate_limiter': self.rate_limiter.get_stats(),
            'circuit_breaker_state': self.circuit_breaker.get_state(),
            'worker_pool': self.worker_pool.get_stats(),
            'lazy_imports': self.lazy_import_manager.get_stats(),
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        }
        
        if self.redis_cache:
            stats['redis'] = self.redis_cache.get_stats()
        
        if self.cache_warmer:
            stats['cache_warmer'] = self.cache_warmer.get_stats()
        
        return stats
    
    async def cleanup(self):
        """清理资源"""
        await self.connection_pool.close()
        self.worker_pool.shutdown()


# ============================================================================
# DECORATORS FOR EASY INTEGRATION
# ============================================================================

def with_rate_limit(limiter: TokenBucketRateLimiter):
    """限流装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.allow_request():
                raise Exception("Rate limit exceeded")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_circuit_breaker(breaker: CircuitBreaker):
    """熔断器装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def with_compression(accept_encoding: str = 'gzip'):
    """压缩装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, bytes):
                compressed, encoding = CompressionMiddleware.compress_response(
                    result, accept_encoding
                )
                return compressed, encoding
            return result
        return wrapper
    return decorator
