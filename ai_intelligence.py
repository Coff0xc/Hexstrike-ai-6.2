#!/usr/bin/env python3
"""
HexStrike AI 智能决策系统
AI Intelligence & Learning Module

功能:
1. AI 对话 - 自然语言理解渗透测试需求
2. 决策引擎 - 智能选择最优工具和参数
3. 学习系统 - 从历史扫描中学习优化策略
4. 智能推荐 - 基于上下文推荐最佳方案
"""

import json
import os
import pickle
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests


# ============================================================================
# 1. AI 对话系统 - 自然语言理解
# ============================================================================

class NLPIntentClassifier:
    """自然语言意图分类器"""
    
    # 意图关键词映射
    INTENT_PATTERNS = {
        'port_scan': [
            'port', 'scan', 'nmap', 'masscan', 'open ports', '端口扫描',
            'service detection', '服务探测', '扫描', '端口', '探测'
        ],
        'web_scan': [
            'web', 'website', 'http', 'https', 'url', 'gobuster', 'nikto',
            'directory', '目录扫描', 'web漏洞', '网站', '网页'
        ],
        'vuln_scan': [
            'vulnerability', 'vuln', 'nuclei', 'cve', '漏洞扫描',
            'security scan', '安全扫描'
        ],
        'subdomain': [
            'subdomain', 'amass', 'subfinder', '子域名', 'dns'
        ],
        'sql_injection': [
            'sql', 'sqlmap', 'injection', 'database', 'sqli', 'SQL注入'
        ],
        'xss': [
            'xss', 'cross-site', 'dalfox', '跨站脚本'
        ],
        'password': [
            'password', 'brute', 'hydra', 'john', '密码破解', '暴力破解'
        ],
        'ctf': [
            'ctf', 'flag', 'capture the flag', 'pwn', 'crypto', 'misc'
        ]
    }
    
    def classify(self, user_input: str) -> Dict[str, Any]:
        """分类用户意图"""
        user_input = user_input.lower()
        
        # 计算每个意图的匹配分数
        scores = defaultdict(int)
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in user_input:
                    scores[intent] += 1
        
        # 获取最高分意图
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = scores[best_intent] / len(self.INTENT_PATTERNS[best_intent])
            
            return {
                'intent': best_intent,
                'confidence': min(confidence, 1.0),
                'all_scores': dict(scores)
            }
        
        return {
            'intent': 'unknown',
            'confidence': 0.0,
            'all_scores': {}
        }
    
    def extract_targets(self, user_input: str) -> List[str]:
        """提取目标信息"""
        import re
        
        targets = []
        
        # 提取 IP 地址
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, user_input)
        targets.extend(ips)
        
        # 提取域名
        domain_pattern = r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, user_input)
        targets.extend(domains)
        
        # 提取 URL
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, user_input)
        targets.extend(urls)
        
        return list(set(targets))


# ============================================================================
# 2. 智能决策引擎
# ============================================================================

class IntelligentDecisionEngine:
    """智能决策引擎 - 选择最优工具和参数"""
    
    # 工具能力映射
    TOOL_CAPABILITIES = {
        'port_scan': {
            'tools': ['nmap', 'rustscan', 'masscan'],
            'priority': {
                'nmap': {'accuracy': 10, 'speed': 6, 'features': 10},
                'rustscan': {'accuracy': 8, 'speed': 10, 'features': 7},
                'masscan': {'accuracy': 7, 'speed': 10, 'features': 5}
            }
        },
        'web_scan': {
            'tools': ['gobuster', 'feroxbuster', 'ffuf', 'dirsearch'],
            'priority': {
                'gobuster': {'accuracy': 8, 'speed': 8, 'features': 7},
                'feroxbuster': {'accuracy': 9, 'speed': 9, 'features': 8},
                'ffuf': {'accuracy': 10, 'speed': 10, 'features': 10}
            }
        },
        'vuln_scan': {
            'tools': ['nuclei', 'nikto', 'wpscan'],
            'priority': {
                'nuclei': {'accuracy': 10, 'speed': 9, 'features': 10},
                'nikto': {'accuracy': 7, 'speed': 6, 'features': 7}
            }
        },
        'subdomain': {
            'tools': ['subfinder', 'amass', 'assetfinder'],
            'priority': {
                'subfinder': {'accuracy': 9, 'speed': 10, 'features': 8},
                'amass': {'accuracy': 10, 'speed': 6, 'features': 10}
            }
        },
        'sql_injection': {
            'tools': ['sqlmap'],
            'priority': {
                'sqlmap': {'accuracy': 10, 'speed': 7, 'features': 10}
            }
        },
        'password': {
            'tools': ['hydra', 'john', 'hashcat'],
            'priority': {
                'hydra': {'accuracy': 8, 'speed': 8, 'features': 9},
                'hashcat': {'accuracy': 10, 'speed': 10, 'features': 10}
            }
        }
    }
    
    def __init__(self):
        self.learning_data = self._load_learning_data()
        
    def _load_learning_data(self) -> Dict[str, Any]:
        """加载学习数据"""
        data_file = './ai_learning_data.json'
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                return json.load(f)
        return {'tool_success_rate': {}, 'tool_avg_time': {}}
    
    def select_best_tool(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """选择最佳工具"""
        if intent not in self.TOOL_CAPABILITIES:
            return {
                'tool': None,
                'reason': f"No tools available for intent: {intent}"
            }
        
        tools = self.TOOL_CAPABILITIES[intent]['tools']
        priorities = self.TOOL_CAPABILITIES[intent]['priority']
        
        # 根据优先级和学习数据评分
        scores = {}
        for tool in tools:
            if tool in priorities:
                priority = priorities[tool]
                
                # 基础分数（准确性、速度、功能）
                base_score = (
                    priority['accuracy'] * 0.4 +
                    priority['speed'] * 0.3 +
                    priority['features'] * 0.3
                )
                
                # 学习加成
                success_rate = self.learning_data['tool_success_rate'].get(tool, 0.5)
                learning_bonus = success_rate * 2  # 最多+2分
                
                scores[tool] = base_score + learning_bonus
        
        # 选择最高分工具
        best_tool = max(scores, key=scores.get)
        
        return {
            'tool': best_tool,
            'score': scores[best_tool],
            'all_scores': scores,
            'reason': f"Selected based on accuracy, speed, features and historical success rate"
        }
    
    def optimize_parameters(self, tool: str, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化工具参数"""
        params = {}
        
        # 基于工具类型优化参数
        if tool == 'nmap':
            params = self._optimize_nmap(target, context)
        elif tool == 'gobuster':
            params = self._optimize_gobuster(target, context)
        elif tool == 'nuclei':
            params = self._optimize_nuclei(target, context)
        # ... 其他工具
        
        return params
    
    def _optimize_nmap(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化 Nmap 参数"""
        params = {
            'scan_type': '-sV',  # 版本探测
            'additional_args': ''
        }
        
        # 根据时间要求调整
        if context.get('speed') == 'fast':
            params['scan_type'] = '-sS'
            params['additional_args'] = '-T4 --top-ports 1000'
        elif context.get('speed') == 'thorough':
            params['scan_type'] = '-sV -sC'
            params['additional_args'] = '-T4 -p-'
        
        return params
    
    def _optimize_gobuster(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化 Gobuster 参数"""
        params = {
            'mode': 'dir',
            'wordlist': '/usr/share/wordlists/dirb/common.txt'
        }
        
        # 根据目标类型选择字典
        if 'wordpress' in context.get('tech_stack', []):
            params['wordlist'] = '/usr/share/wordlists/wfuzz/webservices/ws-dirs.txt'
        
        return params
    
    def _optimize_nuclei(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化 Nuclei 参数"""
        params = {
            'severity': 'critical,high,medium',
            'tags': ''
        }
        
        # 根据技术栈添加标签
        tech_stack = context.get('tech_stack', [])
        if 'apache' in tech_stack:
            params['tags'] = 'apache'
        elif 'nginx' in tech_stack:
            params['tags'] = 'nginx'
        
        return params


# ============================================================================
# 3. 学习系统 - 从历史中学习
# ============================================================================

class LearningSystem:
    """学习系统 - 从扫描历史中学习优化策略"""
    
    def __init__(self, data_file: str = './learning_data.pkl'):
        self.data_file = data_file
        self.history = self._load_history()
        
    def _load_history(self) -> Dict[str, List]:
        """加载历史数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'rb') as f:
                return pickle.load(f)
        return {
            'scans': [],
            'tool_performance': defaultdict(list),
            'success_patterns': []
        }
    
    def _save_history(self):
        """保存历史数据"""
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.history, f)
    
    def record_scan(self, scan_data: Dict[str, Any]):
        """记录扫描结果"""
        scan_data['timestamp'] = datetime.now().isoformat()
        self.history['scans'].append(scan_data)
        
        # 记录工具性能
        tool = scan_data.get('tool')
        success = scan_data.get('success', False)
        duration = scan_data.get('duration', 0)
        
        if tool:
            self.history['tool_performance'][tool].append({
                'success': success,
                'duration': duration,
                'timestamp': scan_data['timestamp']
            })
        
        # 识别成功模式
        if success:
            pattern = {
                'tool': tool,
                'target_type': scan_data.get('target_type'),
                'parameters': scan_data.get('parameters')
            }
            self.history['success_patterns'].append(pattern)
        
        self._save_history()
    
    def analyze_tool_effectiveness(self, tool: str) -> Dict[str, Any]:
        """分析工具有效性"""
        performances = self.history['tool_performance'].get(tool, [])
        
        if not performances:
            return {
                'success_rate': 0.0,
                'avg_duration': 0.0,
                'total_uses': 0
            }
        
        successes = sum(1 for p in performances if p['success'])
        total = len(performances)
        avg_duration = sum(p['duration'] for p in performances) / total
        
        return {
            'success_rate': successes / total,
            'avg_duration': avg_duration,
            'total_uses': total,
            'recent_trend': self._get_recent_trend(performances)
        }
    
    def _get_recent_trend(self, performances: List[Dict]) -> str:
        """获取最近趋势"""
        if len(performances) < 10:
            return 'insufficient_data'
        
        recent = performances[-10:]
        older = performances[-20:-10] if len(performances) >= 20 else performances[:-10]
        
        recent_success = sum(1 for p in recent if p['success']) / len(recent)
        older_success = sum(1 for p in older if p['success']) / len(older)
        
        if recent_success > older_success + 0.1:
            return 'improving'
        elif recent_success < older_success - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def recommend_workflow(self, intent: str, target: str) -> List[Dict[str, Any]]:
        """推荐工作流"""
        # 基于成功模式推荐
        relevant_patterns = [
            p for p in self.history['success_patterns']
            if p.get('target_type') == self._classify_target(target)
        ]
        
        if not relevant_patterns:
            # 使用默认工作流
            return self._get_default_workflow(intent)
        
        # 统计最常见的成功模式
        tool_counts = defaultdict(int)
        for pattern in relevant_patterns:
            tool_counts[pattern['tool']] += 1
        
        # 构建推荐工作流
        workflow = []
        for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            workflow.append({
                'tool': tool,
                'confidence': count / len(relevant_patterns),
                'reason': f'Successful in {count}/{len(relevant_patterns)} similar scans'
            })
        
        return workflow
    
    def _classify_target(self, target: str) -> str:
        """分类目标类型"""
        import re
        
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', target):
            return 'ip'
        elif target.startswith('http'):
            return 'url'
        else:
            return 'domain'
    
    def _get_default_workflow(self, intent: str) -> List[Dict[str, Any]]:
        """获取默认工作流"""
        workflows = {
            'port_scan': [
                {'tool': 'rustscan', 'reason': 'Fast initial scan'},
                {'tool': 'nmap', 'reason': 'Detailed service detection'}
            ],
            'web_scan': [
                {'tool': 'httpx', 'reason': 'Probe web services'},
                {'tool': 'nuclei', 'reason': 'Vulnerability scanning'},
                {'tool': 'gobuster', 'reason': 'Directory enumeration'}
            ],
            'subdomain': [
                {'tool': 'subfinder', 'reason': 'Passive enumeration'},
                {'tool': 'httpx', 'reason': 'Validate subdomains'}
            ]
        }
        
        return workflows.get(intent, [])


# ============================================================================
# 4. 智能推荐系统
# ============================================================================

class IntelligentRecommender:
    """智能推荐系统"""
    
    def __init__(self):
        self.nlp = NLPIntentClassifier()
        self.decision_engine = IntelligentDecisionEngine()
        self.learning_system = LearningSystem()
        
    def process_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户请求"""
        if context is None:
            context = {}
        
        # 1. 理解意图
        intent_result = self.nlp.classify(user_input)
        intent = intent_result['intent']
        
        # 2. 提取目标
        targets = self.nlp.extract_targets(user_input)
        
        # 3. 选择最佳工具
        tool_selection = self.decision_engine.select_best_tool(intent, context)
        
        # 4. 推荐工作流
        workflow = self.learning_system.recommend_workflow(intent, targets[0] if targets else '')
        
        # 5. 优化参数
        if tool_selection['tool'] and targets:
            parameters = self.decision_engine.optimize_parameters(
                tool_selection['tool'],
                targets[0],
                context
            )
        else:
            parameters = {}
        
        return {
            'intent': intent,
            'confidence': intent_result['confidence'],
            'targets': targets,
            'recommended_tool': tool_selection['tool'],
            'tool_reason': tool_selection.get('reason'),
            'parameters': parameters,
            'workflow': workflow,
            'suggestions': self._generate_suggestions(intent, targets)
        }
    
    def _generate_suggestions(self, intent: str, targets: List[str]) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if intent == 'port_scan' and targets:
            suggestions.append(f"Start with fast scan on {targets[0]}")
            suggestions.append("Follow up with detailed service detection")
        elif intent == 'web_scan' and targets:
            suggestions.append(f"Check {targets[0]} for common vulnerabilities")
            suggestions.append("Enumerate directories and files")
        elif intent == 'vuln_scan' and targets:
            suggestions.append(f"Run comprehensive vulnerability scan on {targets[0]}")
            suggestions.append("Focus on critical and high severity issues")
        
        return suggestions


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("🧠 HexStrike AI Intelligence System")
    print("=" * 60)
    
    recommender = IntelligentRecommender()
    
    # 测试不同的用户输入
    test_inputs = [
        "Scan ports on 192.168.1.1",
        "Find subdomains for example.com",
        "Test https://target.com for vulnerabilities",
        "对 test.com 进行 web 漏洞扫描",
        "使用 nmap 扫描 10.0.0.1"
    ]
    
    for user_input in test_inputs:
        print(f"\n📝 User Input: {user_input}")
        print("-" * 60)
        
        result = recommender.process_request(user_input)
        
        print(f"🎯 Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
        print(f"🔍 Targets: {result['targets']}")
        print(f"🛠️  Recommended Tool: {result['recommended_tool']}")
        print(f"📋 Parameters: {result['parameters']}")
        print(f"🔄 Workflow: {len(result['workflow'])} steps")
        
        for i, step in enumerate(result['workflow'], 1):
            print(f"   {i}. {step['tool']} - {step.get('reason', 'N/A')}")
        
        print(f"💡 Suggestions:")
        for suggestion in result['suggestions']:
            print(f"   - {suggestion}")
    
    print("\n" + "=" * 60)
    print("✅ AI Intelligence tests completed!")
