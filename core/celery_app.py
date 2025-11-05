#!/usr/bin/env python3
"""
HexStrike AI - Celery Application Configuration (v6.2)

异步任务队列系统 - 支持长时间运行的扫描任务
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange

logger = logging.getLogger(__name__)

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

# Broker配置（优先使用Redis）
CELERY_BROKER_URL = os.getenv(
    'CELERY_BROKER_URL',
    os.getenv('REDIS_URL', 'redis://localhost:6379/1')
)

# Backend配置（结果存储）
CELERY_RESULT_BACKEND = os.getenv(
    'CELERY_RESULT_BACKEND',
    os.getenv('REDIS_URL', 'redis://localhost:6379/2')
)

# 创建Celery应用
celery_app = Celery(
    'hexstrike',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'core.tasks.scan_tasks',
        'core.tasks.analysis_tasks',
        'core.tasks.report_tasks',
        'core.tasks.ai_tasks'
    ]
)

# ============================================================================
# CELERY SETTINGS
# ============================================================================

celery_app.conf.update(
    # 任务结果设置
    result_expires=3600,  # 结果保存1小时
    result_backend_transport_options={'master_name': 'mymaster'},
    
    # 任务序列化
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    
    # 任务路由
    task_routes={
        'core.tasks.scan_tasks.*': {'queue': 'scan'},
        'core.tasks.analysis_tasks.*': {'queue': 'analysis'},
        'core.tasks.report_tasks.*': {'queue': 'report'},
        'core.tasks.ai_tasks.*': {'queue': 'ai'},
    },
    
    # 队列定义
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('scan', Exchange('scan'), routing_key='scan.#'),
        Queue('analysis', Exchange('analysis'), routing_key='analysis.#'),
        Queue('report', Exchange('report'), routing_key='report.#'),
        Queue('ai', Exchange('ai'), routing_key='ai.#'),
    ),
    
    # Worker设置
    worker_prefetch_multiplier=1,  # 每次只取1个任务
    worker_max_tasks_per_child=1000,  # 每个worker执行1000个任务后重启
    worker_disable_rate_limits=False,
    
    # 任务执行设置
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # worker丢失时拒绝任务
    task_time_limit=3600,  # 任务超时1小时
    task_soft_time_limit=3300,  # 软超时55分钟
    
    # 任务跟踪
    task_track_started=True,  # 跟踪任务开始状态
    task_send_sent_event=True,  # 发送任务发送事件
    
    # 结果后端设置
    result_extended=True,  # 扩展结果信息
    result_backend_max_retries=10,
    
    # 重试设置
    task_default_retry_delay=60,  # 默认重试延迟60秒
    task_max_retries=3,  # 最大重试次数
    
    # 任务优先级
    task_inherit_parent_priority=True,
    task_default_priority=5,
    
    # 监控和日志
    worker_send_task_events=True,  # 发送任务事件（用于监控）
)

# ============================================================================
# PERIODIC TASKS (定时任务)
# ============================================================================

celery_app.conf.beat_schedule = {
    # 清理过期任务结果
    'cleanup-expired-results': {
        'task': 'core.tasks.maintenance_tasks.cleanup_expired_results',
        'schedule': crontab(minute=0, hour='*/6'),  # 每6小时
    },
    
    # 更新CVE数据库
    'update-cve-database': {
        'task': 'core.tasks.maintenance_tasks.update_cve_database',
        'schedule': crontab(minute=0, hour=2),  # 每天凌晨2点
    },
    
    # 系统健康检查
    'system-health-check': {
        'task': 'core.tasks.maintenance_tasks.system_health_check',
        'schedule': crontab(minute='*/15'),  # 每15分钟
    },
    
    # 生成统计报告
    'generate-daily-stats': {
        'task': 'core.tasks.report_tasks.generate_daily_statistics',
        'schedule': crontab(minute=0, hour=0),  # 每天午夜
    },
}

# ============================================================================
# CELERY SIGNALS
# ============================================================================

from celery.signals import (
    task_prerun, task_postrun, task_failure,
    task_success, worker_ready, worker_shutdown
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """任务开始前的处理"""
    logger.info(f"Task {task.name} [{task_id}] starting...")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                         retval=None, state=None, **extra):
    """任务完成后的处理"""
    logger.info(f"Task {task.name} [{task_id}] completed with state: {state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, 
                        kwargs=None, traceback=None, einfo=None, **extra):
    """任务失败的处理"""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")


@task_success.connect
def task_success_handler(sender=None, result=None, **extra):
    """任务成功的处理"""
    logger.info(f"Task {sender.name} succeeded with result: {result}")


@worker_ready.connect
def worker_ready_handler(sender=None, **extra):
    """Worker启动完成"""
    logger.info(f"Worker {sender.hostname} is ready")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **extra):
    """Worker关闭"""
    logger.info(f"Worker {sender.hostname} is shutting down")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_celery_app():
    """获取Celery应用实例"""
    return celery_app


def is_celery_available():
    """检查Celery是否可用"""
    try:
        celery_app.control.inspect().stats()
        return True
    except Exception as e:
        logger.warning(f"Celery not available: {e}")
        return False


def get_worker_status():
    """获取Worker状态"""
    try:
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        active = inspector.active()
        reserved = inspector.reserved()
        
        return {
            'available': True,
            'workers': list(stats.keys()) if stats else [],
            'worker_count': len(stats) if stats else 0,
            'active_tasks': sum(len(tasks) for tasks in active.values()) if active else 0,
            'reserved_tasks': sum(len(tasks) for tasks in reserved.values()) if reserved else 0,
            'stats': stats
        }
    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        return {
            'available': False,
            'error': str(e)
        }


def get_queue_length(queue_name='default'):
    """获取队列长度"""
    try:
        with celery_app.connection_or_acquire() as conn:
            return conn.default_channel.queue_declare(
                queue=queue_name, passive=True
            ).message_count
    except Exception as e:
        logger.error(f"Failed to get queue length: {e}")
        return 0


if __name__ == '__main__':
    # 测试Celery连接
    print("Testing Celery connection...")
    status = get_worker_status()
    print(f"Celery Status: {status}")
