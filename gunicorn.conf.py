#!/usr/bin/env python3
"""
HexStrike AI - Gunicorn Configuration (v6.1)

生产环境Gunicorn配置文件
优化了并发性能、工作进程管理和资源使用
"""

import multiprocessing
import os

# ============================================================================
# SERVER SOCKET
# ============================================================================

bind = f"{os.getenv('HEXSTRIKE_HOST', '0.0.0.0')}:{os.getenv('HEXSTRIKE_PORT', '8888')}"
backlog = 2048

# ============================================================================
# WORKER PROCESSES
# ============================================================================

# 工作进程数量: (CPU核心数 * 2) + 1
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# 工作进程类型
# - sync: 同步工作进程（默认）
# - gevent: 基于协程的异步工作进程（推荐用于I/O密集型）
# - eventlet: 另一种协程实现
# - tornado: Tornado异步工作进程
worker_class = os.getenv('WORKER_CLASS', 'gevent')

# 每个工作进程的线程数（仅用于sync worker）
threads = int(os.getenv('WORKER_THREADS', '1'))

# 每个worker的最大并发连接数（用于gevent/eventlet）
worker_connections = int(os.getenv('WORKER_CONNECTIONS', '1000'))

# Worker超时时间（秒）
timeout = int(os.getenv('WORKER_TIMEOUT', '120'))

# Keepalive时间（秒）
keepalive = int(os.getenv('KEEPALIVE', '5'))

# ============================================================================
# WORKER LIFECYCLE
# ============================================================================

# 最大请求数后重启worker（防止内存泄漏）
max_requests = int(os.getenv('MAX_REQUESTS', '10000'))
max_requests_jitter = int(os.getenv('MAX_REQUESTS_JITTER', '1000'))

# Worker优雅重启超时
graceful_timeout = int(os.getenv('GRACEFUL_TIMEOUT', '30'))

# ============================================================================
# LOGGING
# ============================================================================

# 访问日志
accesslog = os.getenv('ACCESS_LOG', '-')  # '-' 表示stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 错误日志
errorlog = os.getenv('ERROR_LOG', '-')
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# 捕获标准输出
capture_output = True

# 启用访问日志
disable_redirect_access_to_syslog = False

# ============================================================================
# PROCESS NAMING
# ============================================================================

proc_name = 'hexstrike_ai'

# ============================================================================
# SERVER MECHANICS
# ============================================================================

# Daemon模式
daemon = False

# PID文件
pidfile = os.getenv('PIDFILE', '/tmp/hexstrike_ai.pid')

# 用户和组
# user = 'hexstrike'
# group = 'hexstrike'

# 临时目录
tmp_upload_dir = None

# ============================================================================
# SSL (HTTPS支持)
# ============================================================================

# 如果需要HTTPS，取消注释并配置
# keyfile = os.getenv('SSL_KEY_FILE', '/path/to/key.pem')
# certfile = os.getenv('SSL_CERT_FILE', '/path/to/cert.pem')
# ssl_version = 2  # SSL_PROTOCOL_TLSv1_2
# cert_reqs = 0  # ssl.CERT_NONE
# ca_certs = None
# ciphers = None

# ============================================================================
# SERVER HOOKS
# ============================================================================

def on_starting(server):
    """服务器启动时"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   🚀 HexStrike AI - Starting Server (v6.1)                               ║
║                                                                           ║
║   ⚡ Performance Optimized Edition                                       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")
    print(f"🌐 Binding to: {bind}")
    print(f"👷 Workers: {workers} ({worker_class})")
    print(f"🔌 Worker connections: {worker_connections}")
    print(f"⏱️  Timeout: {timeout}s")
    print(f"🔄 Max requests: {max_requests} (±{max_requests_jitter})")
    print(f"📝 Log level: {loglevel}")
    print("═" * 79)


def on_reload(server):
    """配置重载时"""
    print("🔄 Reloading configuration...")


def when_ready(server):
    """服务器准备就绪时"""
    print("✅ Server is ready to accept connections")


def worker_int(worker):
    """Worker被中断时"""
    print(f"⚠️  Worker {worker.pid} interrupted")


def worker_abort(worker):
    """Worker被终止时"""
    print(f"❌ Worker {worker.pid} aborted")


def pre_fork(server, worker):
    """Fork worker之前"""
    pass


def post_fork(server, worker):
    """Fork worker之后"""
    print(f"✨ Worker {worker.pid} spawned")


def pre_exec(server):
    """重新执行之前"""
    print("🔄 Forking new master process...")


def pre_request(worker, req):
    """处理请求之前"""
    # 可以在这里添加请求级别的初始化
    pass


def post_request(worker, req, environ, resp):
    """处理请求之后"""
    # 可以在这里添加请求级别的清理
    pass


def child_exit(server, worker):
    """Worker退出时"""
    print(f"👋 Worker {worker.pid} exited")


def worker_exit(server, worker):
    """Worker退出时（清理）"""
    pass


def nworkers_changed(server, new_value, old_value):
    """Worker数量改变时"""
    print(f"👷 Workers changed: {old_value} -> {new_value}")


def on_exit(server):
    """服务器退出时"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   👋 HexStrike AI - Server Shutdown                                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")


# ============================================================================
# DEVELOPMENT SETTINGS (开发模式)
# ============================================================================

# 如果是开发模式，覆盖某些设置
if os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG_MODE', '0') == '1':
    reload = True  # 代码改动时自动重载
    workers = 2  # 开发模式使用较少的worker
    loglevel = 'debug'
    accesslog = '-'
    errorlog = '-'
    print("⚠️  Running in DEVELOPMENT mode")
