#!/usr/bin/env python3
"""
HexStrike AI - Scan Tasks (v6.2)

扫描相关的异步任务
"""

import logging
import time
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from celery import Task

from core.celery_app import celery_app
from core.execution import execute_command

logger = logging.getLogger(__name__)


# ============================================================================
# BASE SCAN TASK
# ============================================================================

class BaseScanTask(Task):
    """扫描任务基类"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"Scan task {task_id} failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc),
            'task_id': task_id
        }
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        logger.info(f"Scan task {task_id} completed successfully")
    
    def update_progress(self, current, total, message=''):
        """更新任务进度"""
        self.update_state(
            state='PROGRESS',
            meta={
                'current': current,
                'total': total,
                'percent': int((current / total) * 100) if total > 0 else 0,
                'message': message
            }
        )


# ============================================================================
# NMAP SCAN TASKS
# ============================================================================

@celery_app.task(
    base=BaseScanTask,
    bind=True,
    name='core.tasks.scan_tasks.run_nmap_scan',
    max_retries=3,
    default_retry_delay=60
)
def run_nmap_scan(self, target: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    异步执行Nmap扫描
    
    Args:
        target: 目标地址
        options: 扫描选项
        
    Returns:
        扫描结果
    """
    try:
        self.update_progress(0, 100, 'Initializing Nmap scan...')
        
        options = options or {}
        scan_type = options.get('scan_type', 'quick')
        ports = options.get('ports', '1-1000')
        
        # 构建nmap命令
        cmd_parts = ['nmap']
        
        if scan_type == 'quick':
            cmd_parts.extend(['-T4', '-F'])
        elif scan_type == 'full':
            cmd_parts.extend(['-T4', '-p-'])
        elif scan_type == 'stealth':
            cmd_parts.extend(['-sS', '-T2'])
        
        cmd_parts.extend(['-p', ports, target])
        
        self.update_progress(10, 100, 'Starting Nmap scan...')
        
        # 执行扫描
        result = execute_command(' '.join(cmd_parts), timeout=options.get('timeout', 600))
        
        self.update_progress(90, 100, 'Parsing scan results...')
        
        # 解析结果
        scan_result = {
            'task_id': self.request.id,
            'target': target,
            'scan_type': scan_type,
            'status': 'completed',
            'output': result.get('output', ''),
            'error': result.get('error', ''),
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat(),
            'duration': result.get('elapsed_time', 0)
        }
        
        self.update_progress(100, 100, 'Scan completed')
        
        return scan_result
        
    except Exception as e:
        logger.error(f"Nmap scan failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseScanTask,
    bind=True,
    name='core.tasks.scan_tasks.run_nuclei_scan',
    max_retries=2
)
def run_nuclei_scan(self, target: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    异步执行Nuclei扫描
    
    Args:
        target: 目标URL
        options: 扫描选项
        
    Returns:
        扫描结果
    """
    try:
        self.update_progress(0, 100, 'Initializing Nuclei scan...')
        
        options = options or {}
        severity = options.get('severity', 'medium,high,critical')
        tags = options.get('tags', '')
        
        # 构建nuclei命令
        cmd_parts = ['nuclei', '-u', target, '-severity', severity]
        
        if tags:
            cmd_parts.extend(['-tags', tags])
        
        if options.get('json_output', True):
            cmd_parts.append('-json')
        
        self.update_progress(10, 100, 'Running Nuclei templates...')
        
        # 执行扫描
        result = execute_command(' '.join(cmd_parts), timeout=options.get('timeout', 300))
        
        self.update_progress(90, 100, 'Processing results...')
        
        # 解析JSON输出
        vulnerabilities = []
        if result.get('success') and result.get('output'):
            for line in result['output'].split('\n'):
                if line.strip():
                    try:
                        vuln = json.loads(line)
                        vulnerabilities.append(vuln)
                    except json.JSONDecodeError:
                        pass
        
        scan_result = {
            'task_id': self.request.id,
            'target': target,
            'status': 'completed',
            'vulnerabilities': vulnerabilities,
            'vulnerability_count': len(vulnerabilities),
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat(),
            'duration': result.get('elapsed_time', 0)
        }
        
        self.update_progress(100, 100, 'Scan completed')
        
        return scan_result
        
    except Exception as e:
        logger.error(f"Nuclei scan failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseScanTask,
    bind=True,
    name='core.tasks.scan_tasks.run_subdomain_enum',
    max_retries=2
)
def run_subdomain_enum(self, domain: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    异步执行子域名枚举
    
    Args:
        domain: 目标域名
        options: 枚举选项
        
    Returns:
        枚举结果
    """
    try:
        self.update_progress(0, 100, 'Starting subdomain enumeration...')
        
        options = options or {}
        tools = options.get('tools', ['subfinder', 'amass'])
        subdomains = set()
        
        # Subfinder
        if 'subfinder' in tools:
            self.update_progress(20, 100, 'Running Subfinder...')
            result = execute_command(f'subfinder -d {domain} -silent', timeout=300)
            if result.get('success'):
                subdomains.update(result.get('output', '').split('\n'))
        
        # Amass
        if 'amass' in tools:
            self.update_progress(60, 100, 'Running Amass...')
            result = execute_command(f'amass enum -passive -d {domain}', timeout=600)
            if result.get('success'):
                subdomains.update(result.get('output', '').split('\n'))
        
        self.update_progress(90, 100, 'Consolidating results...')
        
        # 清理和去重
        subdomains = sorted([s.strip() for s in subdomains if s.strip()])
        
        enum_result = {
            'task_id': self.request.id,
            'domain': domain,
            'status': 'completed',
            'subdomains': subdomains,
            'count': len(subdomains),
            'timestamp': datetime.now().isoformat(),
            'tools_used': tools
        }
        
        self.update_progress(100, 100, 'Enumeration completed')
        
        return enum_result
        
    except Exception as e:
        logger.error(f"Subdomain enumeration failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseScanTask,
    bind=True,
    name='core.tasks.scan_tasks.run_web_scan',
    max_retries=2
)
def run_web_scan(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    异步执行Web应用扫描（综合多个工具）
    
    Args:
        url: 目标URL
        options: 扫描选项
        
    Returns:
        扫描结果
    """
    try:
        self.update_progress(0, 100, 'Starting web application scan...')
        
        options = options or {}
        scan_results = {
            'task_id': self.request.id,
            'url': url,
            'status': 'in_progress',
            'scans': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. 目录扫描
        if options.get('directory_scan', True):
            self.update_progress(10, 100, 'Running directory scan...')
            dir_task = run_directory_scan.delay(url, options.get('dir_options', {}))
            scan_results['scans']['directory'] = dir_task.id
        
        # 2. 漏洞扫描
        if options.get('vuln_scan', True):
            self.update_progress(30, 100, 'Running vulnerability scan...')
            vuln_task = run_nuclei_scan.delay(url, options.get('nuclei_options', {}))
            scan_results['scans']['vulnerabilities'] = vuln_task.id
        
        # 3. SQL注入测试
        if options.get('sqli_scan', True):
            self.update_progress(50, 100, 'Running SQL injection scan...')
            sqli_task = run_sqlmap_scan.delay(url, options.get('sqlmap_options', {}))
            scan_results['scans']['sqli'] = sqli_task.id
        
        # 4. XSS扫描
        if options.get('xss_scan', True):
            self.update_progress(70, 100, 'Running XSS scan...')
            xss_task = run_xss_scan.delay(url, options.get('xss_options', {}))
            scan_results['scans']['xss'] = xss_task.id
        
        self.update_progress(100, 100, 'All scans initiated')
        scan_results['status'] = 'completed'
        
        return scan_results
        
    except Exception as e:
        logger.error(f"Web scan failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseScanTask,
    bind=True,
    name='core.tasks.scan_tasks.run_directory_scan'
)
def run_directory_scan(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """目录扫描任务"""
    try:
        self.update_progress(0, 100, 'Starting directory scan...')
        
        options = options or {}
        wordlist = options.get('wordlist', '/usr/share/wordlists/dirb/common.txt')
        
        cmd = f'gobuster dir -u {url} -w {wordlist} -q'
        
        if options.get('extensions'):
            cmd += f' -x {options["extensions"]}'
        
        self.update_progress(10, 100, 'Scanning directories...')
        
        result = execute_command(cmd, timeout=options.get('timeout', 300))
        
        self.update_progress(100, 100, 'Directory scan completed')
        
        return {
            'task_id': self.request.id,
            'url': url,
            'status': 'completed',
            'output': result.get('output', ''),
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Directory scan failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseScanTask,
    bind=True,
    name='core.tasks.scan_tasks.run_sqlmap_scan'
)
def run_sqlmap_scan(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """SQLMap扫描任务"""
    try:
        self.update_progress(0, 100, 'Starting SQLMap scan...')
        
        options = options or {}
        cmd = f'sqlmap -u "{url}" --batch --threads=5'
        
        if options.get('level'):
            cmd += f' --level={options["level"]}'
        
        if options.get('risk'):
            cmd += f' --risk={options["risk"]}'
        
        self.update_progress(10, 100, 'Testing for SQL injection...')
        
        result = execute_command(cmd, timeout=options.get('timeout', 600))
        
        self.update_progress(100, 100, 'SQLMap scan completed')
        
        return {
            'task_id': self.request.id,
            'url': url,
            'status': 'completed',
            'output': result.get('output', ''),
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"SQLMap scan failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseScanTask,
    bind=True,
    name='core.tasks.scan_tasks.run_xss_scan'
)
def run_xss_scan(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """XSS扫描任务"""
    try:
        self.update_progress(0, 100, 'Starting XSS scan...')
        
        options = options or {}
        cmd = f'dalfox url {url} --silence'
        
        self.update_progress(10, 100, 'Testing for XSS vulnerabilities...')
        
        result = execute_command(cmd, timeout=options.get('timeout', 300))
        
        self.update_progress(100, 100, 'XSS scan completed')
        
        return {
            'task_id': self.request.id,
            'url': url,
            'status': 'completed',
            'output': result.get('output', ''),
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"XSS scan failed: {e}")
        raise self.retry(exc=e)
