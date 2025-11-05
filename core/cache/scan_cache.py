"""
扫描结果缓存系统
支持Redis和内存缓存，避免重复扫描
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目数据类"""
    key: str
    data: Dict[str, Any]
    created_at: float
    expires_at: float
    tool_name: str
    target: str


class ScanResultCache:
    """扫描结果缓存管理器"""
    
    # 默认TTL配置（秒）
    DEFAULT_TTL = {
        'quick_scan': 3600,       # 1小时
        'normal_scan': 7200,      # 2小时
        'deep_scan': 14400,       # 4小时
        'vulnerability_scan': 21600,  # 6小时
        'default': 3600           # 默认1小时
    }
    
    # 工具特定TTL
    TOOL_TTL = {
        'httpx': 1800,      # 30分钟
        'nmap': 7200,       # 2小时
        'nuclei': 21600,    # 6小时（CVE扫描结果相对稳定）
        'sqlmap': 14400,    # 4小时
        'subfinder': 86400, # 24小时（子域名变化较慢）
        'amass': 86400,     # 24小时
        'nikto': 14400,     # 4小时
    }
    
    def __init__(self, use_redis: bool = True, redis_client=None):
        """
        初始化缓存管理器
        
        Args:
            use_redis: 是否使用Redis
            redis_client: Redis客户端实例
        """
        self.use_redis = use_redis
        self.redis_client = redis_client
        self.memory_cache = {}  # 内存缓存作为fallback
        
        if use_redis and redis_client:
            try:
                redis_client.ping()
                logger.info("✅ Redis cache enabled")
            except Exception as e:
                logger.warning(f"⚠️  Redis unavailable, falling back to memory cache: {e}")
                self.use_redis = False
        else:
            logger.info("💾 Using memory cache")
    
    def _generate_cache_key(
        self, 
        tool_name: str, 
        target: str, 
        params: Dict[str, Any]
    ) -> str:
        """
        生成缓存键
        
        Args:
            tool_name: 工具名称
            target: 目标
            params: 参数
            
        Returns:
            str: 缓存键
        """
        # 排序参数以确保一致性
        sorted_params = json.dumps(params, sort_keys=True)
        
        # 组合数据
        data = f"{tool_name}:{target}:{sorted_params}"
        
        # MD5哈希
        hash_key = hashlib.md5(data.encode()).hexdigest()
        
        return f"hexstrike:scan:{tool_name}:{hash_key}"
    
    def get(
        self, 
        tool_name: str, 
        target: str, 
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存结果
        
        Args:
            tool_name: 工具名称
            target: 目标
            params: 参数
            
        Returns:
            Optional[Dict]: 缓存的结果，如果不存在或过期返回None
        """
        params = params or {}
        key = self._generate_cache_key(tool_name, target, params)
        
        try:
            if self.use_redis and self.redis_client:
                # 从Redis获取
                cached = self.redis_client.get(key)
                if cached:
                    data = json.loads(cached)
                    logger.info(f"🎯 Cache HIT (Redis): {tool_name} on {target}")
                    return data
            else:
                # 从内存获取
                entry = self.memory_cache.get(key)
                if entry:
                    # 检查是否过期
                    if time.time() < entry.expires_at:
                        logger.info(f"🎯 Cache HIT (Memory): {tool_name} on {target}")
                        return entry.data
                    else:
                        # 清理过期条目
                        del self.memory_cache[key]
                        logger.debug(f"🗑️  Removed expired cache entry: {key}")
        
        except Exception as e:
            logger.error(f"❌ Cache get error: {e}")
        
        logger.debug(f"❌ Cache MISS: {tool_name} on {target}")
        return None
    
    def set(
        self,
        tool_name: str,
        target: str,
        params: Optional[Dict],
        result: Dict[str, Any],
        ttl: Optional[int] = None,
        scan_type: str = 'default'
    ) -> bool:
        """
        保存结果到缓存
        
        Args:
            tool_name: 工具名称
            target: 目标
            params: 参数
            result: 扫描结果
            ttl: 自定义TTL（秒），None则使用默认值
            scan_type: 扫描类型，用于确定TTL
            
        Returns:
            bool: 是否成功保存
        """
        params = params or {}
        key = self._generate_cache_key(tool_name, target, params)
        
        # 确定TTL
        if ttl is None:
            ttl = self.TOOL_TTL.get(
                tool_name,
                self.DEFAULT_TTL.get(scan_type, self.DEFAULT_TTL['default'])
            )
        
        try:
            # 添加元数据
            cached_data = {
                'result': result,
                'tool_name': tool_name,
                'target': target,
                'cached_at': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            if self.use_redis and self.redis_client:
                # 保存到Redis
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(cached_data)
                )
                logger.info(f"💾 Cached result (Redis): {tool_name} on {target} (TTL: {ttl}s)")
                return True
            else:
                # 保存到内存
                entry = CacheEntry(
                    key=key,
                    data=cached_data,
                    created_at=time.time(),
                    expires_at=time.time() + ttl,
                    tool_name=tool_name,
                    target=target
                )
                self.memory_cache[key] = entry
                logger.info(f"💾 Cached result (Memory): {tool_name} on {target} (TTL: {ttl}s)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Cache set error: {e}")
            return False
    
    def invalidate(
        self,
        tool_name: str,
        target: str,
        params: Optional[Dict] = None
    ) -> bool:
        """
        失效缓存条目
        
        Args:
            tool_name: 工具名称
            target: 目标
            params: 参数
            
        Returns:
            bool: 是否成功失效
        """
        params = params or {}
        key = self._generate_cache_key(tool_name, target, params)
        
        try:
            if self.use_redis and self.redis_client:
                deleted = self.redis_client.delete(key)
                if deleted:
                    logger.info(f"🗑️  Invalidated cache (Redis): {tool_name} on {target}")
                return bool(deleted)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    logger.info(f"🗑️  Invalidated cache (Memory): {tool_name} on {target}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Cache invalidate error: {e}")
            return False
    
    def clear_all(self, pattern: Optional[str] = None) -> int:
        """
        清除所有缓存或匹配pattern的缓存
        
        Args:
            pattern: 键模式（仅Redis支持）
            
        Returns:
            int: 清除的条目数
        """
        count = 0
        
        try:
            if self.use_redis and self.redis_client:
                if pattern:
                    # 使用模式匹配删除
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        count = self.redis_client.delete(*keys)
                else:
                    # 删除所有hexstrike缓存
                    keys = self.redis_client.keys("hexstrike:scan:*")
                    if keys:
                        count = self.redis_client.delete(*keys)
                
                logger.info(f"🗑️  Cleared {count} cache entries (Redis)")
            else:
                # 清除内存缓存
                if pattern:
                    # 简单的模式匹配
                    keys_to_delete = [
                        k for k in self.memory_cache.keys()
                        if pattern.replace('*', '') in k
                    ]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                    count = len(keys_to_delete)
                else:
                    count = len(self.memory_cache)
                    self.memory_cache.clear()
                
                logger.info(f"🗑️  Cleared {count} cache entries (Memory)")
                
        except Exception as e:
            logger.error(f"❌ Cache clear error: {e}")
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 缓存统计
        """
        try:
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys("hexstrike:scan:*")
                
                # 按工具分组统计
                tool_counts = {}
                for key in keys:
                    # 解析工具名称
                    parts = key.decode() if isinstance(key, bytes) else key
                    parts = parts.split(':')
                    if len(parts) >= 3:
                        tool = parts[2]
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
                return {
                    'backend': 'redis',
                    'total_entries': len(keys),
                    'by_tool': tool_counts
                }
            else:
                # 内存缓存统计
                tool_counts = {}
                valid_entries = 0
                now = time.time()
                
                for entry in self.memory_cache.values():
                    if now < entry.expires_at:
                        valid_entries += 1
                        tool = entry.tool_name
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
                return {
                    'backend': 'memory',
                    'total_entries': len(self.memory_cache),
                    'valid_entries': valid_entries,
                    'by_tool': tool_counts
                }
                
        except Exception as e:
            logger.error(f"❌ Cache stats error: {e}")
            return {'error': str(e)}
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存条目（仅内存缓存）
        
        Returns:
            int: 清理的条目数
        """
        if self.use_redis:
            # Redis自动处理过期
            return 0
        
        count = 0
        now = time.time()
        keys_to_delete = []
        
        for key, entry in self.memory_cache.items():
            if now >= entry.expires_at:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1
        
        if count > 0:
            logger.info(f"🗑️  Cleaned up {count} expired cache entries")
        
        return count


class CacheAwareExecutor:
    """支持缓存的工具执行器包装器"""
    
    def __init__(self, cache: ScanResultCache):
        """
        初始化
        
        Args:
            cache: 缓存管理器实例
        """
        self.cache = cache
    
    def execute_with_cache(
        self,
        tool_name: str,
        target: str,
        params: Dict[str, Any],
        executor_func,
        force_refresh: bool = False,
        scan_type: str = 'default'
    ) -> Dict[str, Any]:
        """
        带缓存的工具执行
        
        Args:
            tool_name: 工具名称
            target: 目标
            params: 参数
            executor_func: 执行函数
            force_refresh: 强制刷新缓存
            scan_type: 扫描类型
            
        Returns:
            Dict: 扫描结果
        """
        # 如果不强制刷新，尝试从缓存获取
        if not force_refresh:
            cached = self.cache.get(tool_name, target, params)
            if cached:
                return {
                    **cached.get('result', {}),
                    'from_cache': True,
                    'cached_at': cached.get('cached_at')
                }
        
        # 执行工具
        logger.info(f"🚀 Executing {tool_name} (cache miss or force refresh)")
        result = executor_func(target, params)
        
        # 保存到缓存（仅当成功时）
        if isinstance(result, dict) and result.get('success'):
            self.cache.set(tool_name, target, params, result, scan_type=scan_type)
        
        return {
            **result,
            'from_cache': False
        }


# 尝试初始化Redis客户端
def init_cache(redis_enabled: bool = True) -> ScanResultCache:
    """
    初始化缓存系统
    
    Args:
        redis_enabled: 是否启用Redis
        
    Returns:
        ScanResultCache: 缓存实例
    """
    redis_client = None
    
    if redis_enabled:
        try:
            import redis
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False
            )
            redis_client.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.warning(f"⚠️  Failed to connect to Redis: {e}")
            redis_client = None
    
    return ScanResultCache(
        use_redis=redis_enabled and redis_client is not None,
        redis_client=redis_client
    )


# 全局缓存实例
scan_cache = init_cache()
cache_executor = CacheAwareExecutor(scan_cache)
