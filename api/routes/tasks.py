#!/usr/bin/env python3
"""
HexStrike AI - Task Management API Routes (v6.2)

异步任务管理API端点
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Optional
from celery.result import AsyncResult

from core.celery_app import celery_app, get_worker_status, get_queue_length
from core.tasks.scan_tasks import (
    run_nmap_scan, run_nuclei_scan, run_subdomain_enum,
    run_web_scan, run_directory_scan, run_sqlmap_scan, run_xss_scan
)
from core.tasks.ai_tasks import (
    analyze_scan_results, generate_exploit_suggestions,
    predict_attack_vectors, generate_intelligent_payloads
)

logger = logging.getLogger(__name__)

# Create Blueprint
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


# ============================================================================
# TASK SUBMISSION ENDPOINTS
# ============================================================================

@tasks_bp.route('/scan/nmap', methods=['POST'])
def submit_nmap_scan():
    """提交Nmap扫描任务"""
    try:
        data = request.get_json()
        target = data.get('target')
        options = data.get('options', {})
        
        if not target:
            return jsonify({
                'success': False,
                'error': 'Target is required'
            }), 400
        
        # 提交异步任务
        task = run_nmap_scan.delay(target, options)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': f'Nmap scan task submitted for {target}'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit nmap scan: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/scan/nuclei', methods=['POST'])
def submit_nuclei_scan():
    """提交Nuclei扫描任务"""
    try:
        data = request.get_json()
        target = data.get('target')
        options = data.get('options', {})
        
        if not target:
            return jsonify({
                'success': False,
                'error': 'Target is required'
            }), 400
        
        task = run_nuclei_scan.delay(target, options)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': f'Nuclei scan task submitted for {target}'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit nuclei scan: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/scan/subdomain', methods=['POST'])
def submit_subdomain_enum():
    """提交子域名枚举任务"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        options = data.get('options', {})
        
        if not domain:
            return jsonify({
                'success': False,
                'error': 'Domain is required'
            }), 400
        
        task = run_subdomain_enum.delay(domain, options)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': f'Subdomain enumeration task submitted for {domain}'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit subdomain enum: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/scan/web', methods=['POST'])
def submit_web_scan():
    """提交Web应用扫描任务（综合）"""
    try:
        data = request.get_json()
        url = data.get('url')
        options = data.get('options', {})
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        task = run_web_scan.delay(url, options)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': f'Web scan task submitted for {url}'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit web scan: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# AI TASK SUBMISSION ENDPOINTS
# ============================================================================

@tasks_bp.route('/ai/analyze', methods=['POST'])
def submit_ai_analysis():
    """提交AI分析任务"""
    try:
        data = request.get_json()
        scan_results = data.get('scan_results')
        
        if not scan_results:
            return jsonify({
                'success': False,
                'error': 'Scan results are required'
            }), 400
        
        task = analyze_scan_results.delay(scan_results)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': 'AI analysis task submitted'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit AI analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/ai/exploit-suggestions', methods=['POST'])
def submit_exploit_suggestions():
    """提交利用建议生成任务"""
    try:
        data = request.get_json()
        vulnerability_data = data.get('vulnerability_data')
        
        if not vulnerability_data:
            return jsonify({
                'success': False,
                'error': 'Vulnerability data is required'
            }), 400
        
        task = generate_exploit_suggestions.delay(vulnerability_data)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': 'Exploit suggestions task submitted'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit exploit suggestions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/ai/predict-vectors', methods=['POST'])
def submit_attack_vector_prediction():
    """提交攻击向量预测任务"""
    try:
        data = request.get_json()
        target_info = data.get('target_info')
        
        if not target_info:
            return jsonify({
                'success': False,
                'error': 'Target info is required'
            }), 400
        
        task = predict_attack_vectors.delay(target_info)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': 'Attack vector prediction task submitted'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit attack vector prediction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/ai/generate-payloads', methods=['POST'])
def submit_payload_generation():
    """提交智能Payload生成任务"""
    try:
        data = request.get_json()
        context = data.get('context')
        
        if not context:
            return jsonify({
                'success': False,
                'error': 'Context is required'
            }), 400
        
        task = generate_intelligent_payloads.delay(context)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'submitted',
            'message': 'Payload generation task submitted'
        })
        
    except Exception as e:
        logger.error(f"Failed to submit payload generation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# TASK STATUS ENDPOINTS
# ============================================================================

@tasks_bp.route('/<task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    try:
        task = AsyncResult(task_id, app=celery_app)
        
        response = {
            'task_id': task_id,
            'status': task.state,
            'ready': task.ready(),
            'successful': task.successful() if task.ready() else None,
            'failed': task.failed() if task.ready() else None
        }
        
        if task.state == 'PROGRESS':
            response['progress'] = task.info
        elif task.state == 'SUCCESS':
            response['result'] = task.result
        elif task.state == 'FAILURE':
            response['error'] = str(task.info)
        
        return jsonify({
            'success': True,
            **response
        })
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """获取任务结果"""
    try:
        task = AsyncResult(task_id, app=celery_app)
        
        if not task.ready():
            return jsonify({
                'success': False,
                'error': 'Task not completed yet',
                'status': task.state
            }), 202  # Accepted but not ready
        
        if task.failed():
            return jsonify({
                'success': False,
                'error': str(task.info),
                'status': 'FAILURE'
            }), 500
        
        return jsonify({
            'success': True,
            'status': 'SUCCESS',
            'result': task.result
        })
        
    except Exception as e:
        logger.error(f"Failed to get task result: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    try:
        task = AsyncResult(task_id, app=celery_app)
        task.revoke(terminate=True)
        
        return jsonify({
            'success': True,
            'message': f'Task {task_id} cancelled'
        })
        
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# WORKER MANAGEMENT ENDPOINTS
# ============================================================================

@tasks_bp.route('/workers/status', methods=['GET'])
def get_workers_status():
    """获取Worker状态"""
    try:
        status = get_worker_status()
        
        return jsonify({
            'success': True,
            'workers': status
        })
        
    except Exception as e:
        logger.error(f"Failed to get workers status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/queues/stats', methods=['GET'])
def get_queue_stats():
    """获取队列统计"""
    try:
        queues = ['default', 'scan', 'analysis', 'report', 'ai']
        stats = {}
        
        for queue in queues:
            stats[queue] = get_queue_length(queue)
        
        return jsonify({
            'success': True,
            'queues': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/active', methods=['GET'])
def get_active_tasks():
    """获取活跃任务列表"""
    try:
        inspector = celery_app.control.inspect()
        active = inspector.active()
        
        return jsonify({
            'success': True,
            'active_tasks': active
        })
        
    except Exception as e:
        logger.error(f"Failed to get active tasks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/reserved', methods=['GET'])
def get_reserved_tasks():
    """获取预留任务列表"""
    try:
        inspector = celery_app.control.inspect()
        reserved = inspector.reserved()
        
        return jsonify({
            'success': True,
            'reserved_tasks': reserved
        })
        
    except Exception as e:
        logger.error(f"Failed to get reserved tasks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
