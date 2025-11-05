#!/usr/bin/env python3
"""
HexStrike AI - Flask Middleware (v6.1)

Flask中间件集成性能优化功能:
- 响应压缩
- 请求限流
- 熔断保护
- 性能监控
"""

import time
import logging
from functools import wraps
from typing import Optional
from flask import request, Response, jsonify, g
import gzip

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# COMPRESSION MIDDLEWARE
# ============================================================================

class FlaskCompressionMiddleware:
    """Flask响应压缩中间件"""
    
    def __init__(self, app=None, min_size=1024, compresslevel=6):
        self.app = app
        self.min_size = min_size
        self.compresslevel = compresslevel
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.after_request(self.compress_response)
    
    def compress_response(self, response: Response) -> Response:
        """压缩响应"""
        # 检查是否需要压缩
        if not self._should_compress(response):
            return response
        
        # 获取客户端支持的压缩方式
        accept_encoding = request.headers.get('Accept-Encoding', '').lower()
        
        # 压缩响应
        if 'br' in accept_encoding and BROTLI_AVAILABLE:
            response = self._compress_brotli(response)
        elif 'gzip' in accept_encoding:
            response = self._compress_gzip(response)
        
        return response
    
    def _should_compress(self, response: Response) -> bool:
        """判断是否需要压缩"""
        # 检查响应状态
        if response.status_code < 200 or response.status_code >= 300:
            return False
        
        # 检查内容类型
        content_type = response.content_type or ''
        compressible_types = {
            'text/', 'application/json', 'application/javascript',
            'application/xml', 'application/xml+rss'
        }
        
        if not any(ct in content_type for ct in compressible_types):
            return False
        
        # 检查大小
        if response.content_length is not None and response.content_length < self.min_size:
            return False
        
        # 检查是否已压缩
        if 'Content-Encoding' in response.headers:
            return False
        
        return True
    
    def _compress_gzip(self, response: Response) -> Response:
        """使用Gzip压缩"""
        try:
            data = response.get_data()
            compressed = gzip.compress(data, compresslevel=self.compresslevel)
            
            response.set_data(compressed)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(compressed)
            response.headers['Vary'] = 'Accept-Encoding'
            
            logger.debug(f"Gzip compression: {len(data)} -> {len(compressed)} bytes "
                        f"({100 * (1 - len(compressed)/len(data)):.1f}% reduction)")
        except Exception as e:
            logger.error(f"Gzip compression failed: {e}")
        
        return response
    
    def _compress_brotli(self, response: Response) -> Response:
        """使用Brotli压缩"""
        try:
            data = response.get_data()
            # 使用质量级别4（平衡速度和压缩率）
            compressed = brotli.compress(data, quality=4)
            
            response.set_data(compressed)
            response.headers['Content-Encoding'] = 'br'
            response.headers['Content-Length'] = len(compressed)
            response.headers['Vary'] = 'Accept-Encoding'
            
            logger.debug(f"Brotli compression: {len(data)} -> {len(compressed)} bytes "
                        f"({100 * (1 - len(compressed)/len(data)):.1f}% reduction)")
        except Exception as e:
            logger.error(f"Brotli compression failed: {e}")
        
        return response


# ============================================================================
# RATE LIMITING MIDDLEWARE
# ============================================================================

class FlaskRateLimitMiddleware:
    """Flask限流中间件"""
    
    def __init__(self, app=None, rate_limiter=None):
        self.app = app
        self.rate_limiter = rate_limiter
        
        if app is not None and rate_limiter is not None:
            self.init_app(app, rate_limiter)
    
    def init_app(self, app, rate_limiter):
        """初始化应用"""
        self.rate_limiter = rate_limiter
        app.before_request(self.check_rate_limit)
    
    def check_rate_limit(self):
        """检查请求是否超过限流"""
        if self.rate_limiter and not self.rate_limiter.allow_request():
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }), 429


# ============================================================================
# PERFORMANCE MONITORING MIDDLEWARE
# ============================================================================

class FlaskPerformanceMiddleware:
    """Flask性能监控中间件"""
    
    def __init__(self, app=None):
        self.app = app
        self.stats = {
            'total_requests': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'slowest': 0.0,
            'fastest': float('inf')
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """请求前记录时间"""
        g.start_time = time.time()
    
    def after_request(self, response: Response) -> Response:
        """请求后计算耗时"""
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            
            # 更新统计
            self.stats['total_requests'] += 1
            self.stats['total_time'] += elapsed
            self.stats['avg_time'] = self.stats['total_time'] / self.stats['total_requests']
            self.stats['slowest'] = max(self.stats['slowest'], elapsed)
            self.stats['fastest'] = min(self.stats['fastest'], elapsed)
            
            # 添加响应头
            response.headers['X-Response-Time'] = f"{elapsed:.4f}s"
            
            # 记录慢请求
            if elapsed > 1.0:  # 超过1秒
                logger.warning(f"Slow request: {request.method} {request.path} took {elapsed:.4f}s")
        
        return response
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()


# ============================================================================
# CORS MIDDLEWARE (ENHANCED)
# ============================================================================

class FlaskCORSMiddleware:
    """Flask CORS中间件（增强版）"""
    
    def __init__(self, app=None, origins='*', methods=None, headers=None, 
                 max_age=86400, allow_credentials=True):
        self.origins = origins
        self.methods = methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
        self.headers = headers or ['Content-Type', 'Authorization', 'X-Requested-With']
        self.max_age = max_age
        self.allow_credentials = allow_credentials
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.after_request(self.add_cors_headers)
    
    def add_cors_headers(self, response: Response) -> Response:
        """添加CORS头"""
        response.headers['Access-Control-Allow-Origin'] = self.origins
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.headers)
        response.headers['Access-Control-Max-Age'] = str(self.max_age)
        
        if self.allow_credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response


# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================

class FlaskSecurityHeadersMiddleware:
    """Flask安全头中间件"""
    
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.after_request(self.add_security_headers)
    
    def add_security_headers(self, response: Response) -> Response:
        """添加安全头"""
        # 防止XSS
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CSP (Content Security Policy)
        # 注意：根据实际需求调整
        # response.headers['Content-Security-Policy'] = "default-src 'self'"
        
        # HSTS (HTTP Strict Transport Security)
        # 仅在HTTPS时启用
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


# ============================================================================
# REQUEST ID MIDDLEWARE
# ============================================================================

class FlaskRequestIDMiddleware:
    """Flask请求ID中间件（用于追踪）"""
    
    def __init__(self, app=None, header_name='X-Request-ID'):
        self.header_name = header_name
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.add_request_id)
        app.after_request(self.add_response_id)
    
    def add_request_id(self):
        """添加请求ID"""
        import uuid
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        g.request_id = request_id
    
    def add_response_id(self, response: Response) -> Response:
        """在响应中添加请求ID"""
        if hasattr(g, 'request_id'):
            response.headers[self.header_name] = g.request_id
        return response


# ============================================================================
# MIDDLEWARE MANAGER
# ============================================================================

class MiddlewareManager:
    """中间件管理器（统一管理所有中间件）"""
    
    def __init__(self, app=None):
        self.app = app
        self.middlewares = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app, config: Optional[dict] = None):
        """初始化所有中间件"""
        config = config or {}
        
        # 压缩中间件
        if config.get('compression_enabled', True):
            self.middlewares['compression'] = FlaskCompressionMiddleware(
                app,
                min_size=config.get('compression_min_size', 1024),
                compresslevel=config.get('compression_level', 6)
            )
            logger.info("✅ Compression middleware enabled")
        
        # 性能监控中间件
        self.middlewares['performance'] = FlaskPerformanceMiddleware(app)
        logger.info("✅ Performance monitoring middleware enabled")
        
        # CORS中间件
        if config.get('cors_enabled', True):
            self.middlewares['cors'] = FlaskCORSMiddleware(app)
            logger.info("✅ CORS middleware enabled")
        
        # 安全头中间件
        if config.get('security_headers_enabled', True):
            self.middlewares['security'] = FlaskSecurityHeadersMiddleware(app)
            logger.info("✅ Security headers middleware enabled")
        
        # 请求ID中间件
        if config.get('request_id_enabled', True):
            self.middlewares['request_id'] = FlaskRequestIDMiddleware(app)
            logger.info("✅ Request ID middleware enabled")
        
        # 限流中间件（如果提供了rate_limiter）
        if 'rate_limiter' in config:
            self.middlewares['rate_limit'] = FlaskRateLimitMiddleware(
                app, config['rate_limiter']
            )
            logger.info("✅ Rate limiting middleware enabled")
    
    def get_middleware(self, name: str):
        """获取指定中间件"""
        return self.middlewares.get(name)
    
    def get_stats(self) -> dict:
        """获取所有中间件统计"""
        stats = {}
        
        if 'performance' in self.middlewares:
            stats['performance'] = self.middlewares['performance'].get_stats()
        
        return stats


# ============================================================================
# DECORATORS
# ============================================================================

def require_rate_limit(rate_limiter):
    """装饰器：为单个路由添加限流"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not rate_limiter.allow_request():
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded'
                }), 429
            return func(*args, **kwargs)
        return wrapper
    return decorator


def track_performance(func):
    """装饰器：追踪函数性能"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start_time
            logger.debug(f"{func.__name__} took {elapsed:.4f}s")
    return wrapper
