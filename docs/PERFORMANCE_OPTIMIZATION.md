# HexStrike AI - 性能优化指南 (v6.1)

## 📊 概述

HexStrike AI v6.1 引入了全面的性能优化系统,大幅提升了系统的并发处理能力、响应速度和资源利用效率。

### 核心优化特性

- ⚡ **连接池管理** - HTTP连接复用,减少连接开销
- 🗜️ **响应压缩** - Gzip/Brotli压缩,减少传输数据量
- ⚖️ **请求限流** - 令牌桶算法,防止系统过载
- 🔌 **熔断器** - 自动故障隔离,提升系统稳定性
- 💾 **Redis缓存** - 分布式缓存支持
- 🔥 **智能预热** - 缓存预热机制
- ⏳ **懒加载** - 按需加载重量级依赖
- 👷 **自适应工作池** - 根据负载动态调整工作进程
- 📈 **性能监控** - 实时性能指标追踪

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装性能优化相关依赖
pip install -r requirements.txt

# 可选：安装Redis（推荐用于生产环境）
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis

# 启动Redis
redis-server
```

### 2. 配置环境变量

创建 `.env` 文件（可从 `.env.example` 复制）:

```bash
# 复制环境变量模板
python3 config/performance.py  # 这会生成 .env.example
cp .env.example .env

# 编辑配置
vim .env
```

### 3. 启动服务器

```bash
# 开发模式（使用Flask内置服务器）
./start_server.sh dev

# 生产模式（使用Gunicorn + Gevent）
./start_server.sh

# 或者使用Python直接启动
python3 hexstrike_server.py
```

---

## ⚙️ 配置说明

### HTTP连接池配置

```bash
# 最大连接数
MAX_CONNECTIONS=100

# 最大keepalive连接数
MAX_KEEPALIVE=50

# 请求超时（秒）
REQUEST_TIMEOUT=30

# 重试次数
RETRY_COUNT=3

# 退避因子
BACKOFF_FACTOR=0.5
```

### 限流配置

```bash
# 每秒请求数限制
RATE_LIMIT_RPS=100.0

# 突发请求容量
RATE_LIMIT_BURST=200

# 时间窗口（秒）
RATE_LIMIT_WINDOW=60
```

### 熔断器配置

```bash
# 失败阈值（连续失败次数）
CB_FAILURE_THRESHOLD=5

# 恢复超时（秒）
CB_RECOVERY_TIMEOUT=60
```

### Redis缓存配置

```bash
# 启用Redis缓存
REDIS_ENABLED=true

# Redis服务器地址
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Redis密码（如果有）
REDIS_PASSWORD=

# 键前缀
REDIS_PREFIX=hexstrike:

# TTL（秒）
REDIS_TTL=3600
```

### 响应压缩配置

```bash
# 启用压缩
COMPRESSION_ENABLED=true

# 最小压缩大小（字节）
COMPRESSION_MIN_SIZE=1024

# 压缩级别（1-9 for gzip, 0-11 for brotli）
COMPRESSION_LEVEL=6

# 优先使用Brotli
PREFER_BROTLI=true
```

### Gunicorn服务器配置

```bash
# Worker进程数（auto = CPU数 * 2 + 1）
GUNICORN_WORKERS=auto

# Worker类型（sync, gevent, eventlet, tornado）
WORKER_CLASS=gevent

# 每个worker的连接数
WORKER_CONNECTIONS=1000

# Worker超时（秒）
WORKER_TIMEOUT=120

# Keepalive时间（秒）
KEEPALIVE=5

# 最大请求数后重启worker
MAX_REQUESTS=10000
MAX_REQUESTS_JITTER=1000
```

---

## 📈 性能监控API

### 获取综合性能统计

```bash
curl http://localhost:8888/api/performance/stats
```

响应示例:
```json
{
  "success": true,
  "timestamp": 1699999999.123,
  "stats": {
    "connection_pool": {
      "requests": 1234,
      "errors": 5,
      "avg_response_time": 0.123,
      "pool_size": 45
    },
    "rate_limiter": {
      "allowed": 9876,
      "rejected": 124,
      "current_rate": 0.98
    },
    "circuit_breaker_state": "closed",
    "worker_pool": {
      "submitted": 5000,
      "completed": 4950,
      "failed": 50,
      "queue_size": 0,
      "workers": 8
    },
    "system": {
      "cpu_percent": 45.2,
      "memory_percent": 62.1,
      "disk_usage": 35.7
    }
  }
}
```

### 系统资源监控

```bash
curl http://localhost:8888/api/performance/system
```

### 健康检查

```bash
curl http://localhost:8888/api/performance/health
```

### 性能仪表板

```bash
curl http://localhost:8888/api/performance/dashboard
```

### 连接池统计

```bash
curl http://localhost:8888/api/performance/stats/connection-pool
```

### 限流器统计

```bash
curl http://localhost:8888/api/performance/stats/rate-limiter
```

### 熔断器状态

```bash
curl http://localhost:8888/api/performance/stats/circuit-breaker
```

### 工作池统计

```bash
curl http://localhost:8888/api/performance/stats/worker-pool
```

### 懒加载统计

```bash
curl http://localhost:8888/api/performance/stats/lazy-imports
```

### 缓存管理

```bash
# 获取缓存统计
curl http://localhost:8888/api/performance/cache/stats

# 清空缓存
curl -X POST http://localhost:8888/api/performance/cache/clear

# 触发缓存预热
curl -X POST http://localhost:8888/api/performance/cache/warmup
```

### Redis统计（如果启用）

```bash
curl http://localhost:8888/api/performance/redis/stats
```

---

## 🏭 生产部署建议

### 1. 使用Gunicorn + Gevent

推荐配置:
```bash
# 工作进程数 = (CPU核心数 * 2) + 1
GUNICORN_WORKERS=auto

# 使用Gevent协程工作器（适合I/O密集型）
WORKER_CLASS=gevent

# 每个worker处理1000个并发连接
WORKER_CONNECTIONS=1000
```

启动命令:
```bash
./start_server.sh
# 或者
gunicorn --config gunicorn.conf.py hexstrike_server:app
```

### 2. 启用Redis缓存

```bash
# 在.env中设置
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. 启用响应压缩

```bash
COMPRESSION_ENABLED=true
PREFER_BROTLI=true
COMPRESSION_LEVEL=6
```

### 4. 配置适当的限流

```bash
# 根据服务器性能调整
RATE_LIMIT_RPS=100.0
RATE_LIMIT_BURST=200
```

### 5. 使用反向代理

推荐使用Nginx作为反向代理:

```nginx
upstream hexstrike {
    server 127.0.0.1:8888;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://hexstrike;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
```

---

## 📊 性能基准测试

### 使用Apache Bench测试

```bash
# 测试并发性能
ab -n 10000 -c 100 http://localhost:8888/api/performance/health

# 测试压缩效果
ab -n 1000 -c 50 -H "Accept-Encoding: gzip,br" http://localhost:8888/api/performance/stats
```

### 使用wrk测试

```bash
# 安装wrk
# Ubuntu: sudo apt-get install wrk
# macOS: brew install wrk

# 测试高并发
wrk -t12 -c400 -d30s http://localhost:8888/api/performance/health

# 测试吞吐量
wrk -t4 -c100 -d30s --latency http://localhost:8888/api/performance/stats
```

---

## 🔍 性能优化技巧

### 1. 调整工作进程数

```bash
# CPU密集型任务
GUNICORN_WORKERS=$(($(nproc) + 1))

# I/O密集型任务（使用gevent）
GUNICORN_WORKERS=$(($(nproc) * 2 + 1))
WORKER_CLASS=gevent
```

### 2. 优化缓存策略

```python
# 在代码中使用缓存装饰器
from core.cache import HexStrikeCache

cache = HexStrikeCache()

@cache.cached(ttl=3600)
def expensive_operation(params):
    # 耗时操作
    return result
```

### 3. 使用懒加载

```python
# 对于可选的重量级依赖
if lazy_loader.is_loaded('selenium'):
    selenium = lazy_loader.get('selenium')
else:
    # 不使用selenium功能
    pass
```

### 4. 监控和告警

```bash
# 定期检查健康状态
*/5 * * * * curl -s http://localhost:8888/api/performance/health | jq '.health.status'

# 监控资源使用
*/1 * * * * curl -s http://localhost:8888/api/performance/system | jq '.system.cpu.percent'
```

---

## 🐛 故障排查

### 问题1: 连接池耗尽

**症状**: 请求超时或失败率上升

**解决方案**:
```bash
# 增加连接池大小
MAX_CONNECTIONS=200
MAX_KEEPALIVE=100
```

### 问题2: 内存使用过高

**症状**: 内存占用持续增长

**解决方案**:
```bash
# 启用worker重启
MAX_REQUESTS=5000
MAX_REQUESTS_JITTER=500

# 减少worker数量
GUNICORN_WORKERS=4
```

### 问题3: 请求被限流

**症状**: 收到429状态码

**解决方案**:
```bash
# 调整限流参数
RATE_LIMIT_RPS=200.0
RATE_LIMIT_BURST=400
```

### 问题4: 熔断器打开

**症状**: 所有请求失败，提示"Circuit breaker is OPEN"

**解决方案**:
```bash
# 检查后端服务健康状态
curl http://localhost:8888/api/performance/health

# 调整熔断器参数
CB_FAILURE_THRESHOLD=10
CB_RECOVERY_TIMEOUT=30
```

---

## 📚 相关文档

- [架构设计](./ARCHITECTURE.md)
- [API文档](./API.md)
- [部署指南](./DEPLOYMENT.md)
- [变更日志](../CHANGELOG.md)

---

## 💡 最佳实践

1. **生产环境必须启用Redis缓存**
2. **使用Gunicorn + Gevent进行生产部署**
3. **配置适当的限流参数，防止DDoS**
4. **启用响应压缩，减少带宽使用**
5. **定期监控性能指标，及时发现问题**
6. **使用Nginx作为反向代理，提升安全性**
7. **配置合理的超时和重试参数**
8. **定期清理缓存，防止内存泄漏**

---

## 📞 技术支持

如有问题或建议，请:
- 提交Issue到GitHub仓库
- 查看详细日志: `tail -f hexstrike.log`
- 使用性能监控API诊断问题

---

**HexStrike AI v6.1** - 性能优化版本 🚀
