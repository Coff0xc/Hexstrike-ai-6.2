"""
增强的错误处理和工具回退机制
支持自动重试、工具替代、智能错误诊断
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    TOOL_NOT_FOUND = "tool_not_found"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    NETWORK_ERROR = "network_error"
    INVALID_TARGET = "invalid_target"
    WAF_DETECTED = "waf_detected"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """错误上下文"""
    error_type: ErrorType
    tool_name: str
    target: str
    error_message: str
    timestamp: float
    retry_count: int = 0
    suggestions: List[str] = None


class ToolAlternatives:
    """工具替代方案管理器"""
    
    # 工具替代映射
    ALTERNATIVES = {
        # HTTP探测
        'httpx': ['curl', 'wget'],
        
        # 漏洞扫描
        'nuclei': ['nikto', 'wpscan'],
        'nikto': ['nuclei', 'wpscan'],
        
        # XSS扫描
        'dalfox': ['xsser', 'xsstrike'],
        
        # 目录扫描
        'gobuster': ['feroxbuster', 'ffuf', 'dirsearch'],
        'feroxbuster': ['gobuster', 'ffuf', 'dirsearch'],
        'ffuf': ['gobuster', 'feroxbuster', 'dirsearch'],
        'dirsearch': ['gobuster', 'feroxbuster', 'ffuf'],
        
        # 子域名枚举
        'subfinder': ['amass', 'assetfinder', 'sublist3r'],
        'amass': ['subfinder', 'assetfinder'],
        
        # 端口扫描
        'nmap': ['masscan', 'rustscan'],
        'masscan': ['nmap', 'rustscan'],
        'rustscan': ['nmap', 'masscan'],
        
        # SQL注入
        'sqlmap': ['sqliv', 'sqlninja'],
        
        # 参数发现
        'arjun': ['paramspider', 'x8'],
        'paramspider': ['arjun', 'x8'],
        'x8': ['arjun', 'paramspider'],
        
        # Web爬虫
        'katana': ['hakrawler', 'gospider'],
        'hakrawler': ['katana', 'gospider'],
    }
    
    @classmethod
    def get_alternatives(cls, tool_name: str) -> List[str]:
        """
        获取工具的替代方案
        
        Args:
            tool_name: 工具名称
            
        Returns:
            List[str]: 替代工具列表
        """
        return cls.ALTERNATIVES.get(tool_name, [])
    
    @classmethod
    def has_alternatives(cls, tool_name: str) -> bool:
        """
        检查是否有替代工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否有替代方案
        """
        return tool_name in cls.ALTERNATIVES and len(cls.ALTERNATIVES[tool_name]) > 0


class ErrorDiagnostics:
    """错误诊断工具"""
    
    ERROR_PATTERNS = {
        ErrorType.TOOL_NOT_FOUND: [
            'not found',
            'command not found',
            'No such file or directory',
        ],
        ErrorType.TIMEOUT: [
            'timeout',
            'timed out',
            'Time limit exceeded',
        ],
        ErrorType.PERMISSION_DENIED: [
            'permission denied',
            'access denied',
            'Operation not permitted',
        ],
        ErrorType.NETWORK_ERROR: [
            'connection refused',
            'network unreachable',
            'no route to host',
            'Name or service not known',
        ],
        ErrorType.WAF_DETECTED: [
            'WAF',
            'Web Application Firewall',
            'blocked by security',
            'rate limit',
        ],
        ErrorType.RATE_LIMITED: [
            'rate limit',
            'too many requests',
            '429',
        ],
    }
    
    @classmethod
    def diagnose_error(
        cls, 
        error_message: str, 
        stderr: str = "",
        returncode: int = -1
    ) -> ErrorType:
        """
        诊断错误类型
        
        Args:
            error_message: 错误消息
            stderr: 标准错误输出
            returncode: 返回码
            
        Returns:
            ErrorType: 错误类型
        """
        combined_text = f"{error_message} {stderr}".lower()
        
        for error_type, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in combined_text:
                    return error_type
        
        return ErrorType.UNKNOWN
    
    @classmethod
    def get_suggestions(cls, error_type: ErrorType, tool_name: str) -> List[str]:
        """
        根据错误类型获取建议
        
        Args:
            error_type: 错误类型
            tool_name: 工具名称
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        if error_type == ErrorType.TOOL_NOT_FOUND:
            from core.utils.tool_checker import ToolChecker
            check_result = ToolChecker.check_tool_or_error(tool_name)
            if not check_result.get('available'):
                suggestions.append(f"Install {tool_name}: {check_result.get('install_command')}")
            
            # 添加替代工具建议
            alternatives = ToolAlternatives.get_alternatives(tool_name)
            if alternatives:
                suggestions.append(f"Try alternative tools: {', '.join(alternatives)}")
        
        elif error_type == ErrorType.TIMEOUT:
            suggestions.append("Increase timeout value")
            suggestions.append("Check network connectivity")
            suggestions.append("Use faster scan options")
        
        elif error_type == ErrorType.PERMISSION_DENIED:
            suggestions.append(f"Run with sudo: sudo {tool_name}")
            suggestions.append("Check file permissions")
        
        elif error_type == ErrorType.NETWORK_ERROR:
            suggestions.append("Check network connectivity")
            suggestions.append("Verify target is reachable: ping <target>")
            suggestions.append("Check DNS resolution")
        
        elif error_type == ErrorType.WAF_DETECTED:
            suggestions.append("Use WAF bypass techniques")
            suggestions.append("Add delay between requests")
            suggestions.append("Use custom user-agent")
            suggestions.append("Consider using tamper scripts")
        
        elif error_type == ErrorType.RATE_LIMITED:
            suggestions.append("Reduce request rate")
            suggestions.append("Add delay between requests")
            suggestions.append("Use proxy rotation")
        
        return suggestions


class ResilientExecutor:
    """弹性工具执行器 - 支持重试和回退"""
    
    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: int = 2,
        enable_fallback: bool = True
    ):
        """
        初始化弹性执行器
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            enable_fallback: 是否启用工具回退
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_fallback = enable_fallback
        self.execution_history = []
    
    def execute_with_resilience(
        self,
        tool_name: str,
        target: str,
        params: Dict[str, Any],
        executor_func: Callable,
        tool_executors: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        弹性执行：支持重试和工具回退
        
        Args:
            tool_name: 工具名称
            target: 目标
            params: 参数
            executor_func: 执行函数
            tool_executors: 所有工具执行器（用于回退）
            
        Returns:
            Dict: 执行结果
        """
        retry_count = 0
        last_error = None
        
        # 首先尝试主工具
        while retry_count <= self.max_retries:
            try:
                logger.info(f"🔧 Executing {tool_name} (attempt {retry_count + 1}/{self.max_retries + 1})")
                
                result = executor_func(target, params)
                
                # 检查结果
                if isinstance(result, dict) and result.get('success'):
                    if retry_count > 0:
                        logger.info(f"✅ {tool_name} succeeded after {retry_count} retries")
                    return result
                
                # 失败，诊断错误
                error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else 'Execution failed'
                stderr = result.get('stderr', '') if isinstance(result, dict) else ''
                returncode = result.get('return_code', -1) if isinstance(result, dict) else -1
                
                error_type = ErrorDiagnostics.diagnose_error(error_msg, stderr, returncode)
                
                # 记录错误上下文
                error_context = ErrorContext(
                    error_type=error_type,
                    tool_name=tool_name,
                    target=target,
                    error_message=error_msg,
                    timestamp=time.time(),
                    retry_count=retry_count,
                    suggestions=ErrorDiagnostics.get_suggestions(error_type, tool_name)
                )
                
                last_error = error_context
                
                # 某些错误不值得重试
                if error_type in [ErrorType.TOOL_NOT_FOUND, ErrorType.INVALID_TARGET]:
                    logger.warning(f"⚠️  {tool_name} failed with non-retryable error: {error_type.value}")
                    break
                
                retry_count += 1
                
                if retry_count <= self.max_retries:
                    logger.warning(f"⚠️  {tool_name} failed, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"❌ {tool_name} raised exception: {str(e)}")
                
                error_context = ErrorContext(
                    error_type=ErrorType.UNKNOWN,
                    tool_name=tool_name,
                    target=target,
                    error_message=str(e),
                    timestamp=time.time(),
                    retry_count=retry_count,
                    suggestions=["Check tool installation", "Review error logs"]
                )
                
                last_error = error_context
                retry_count += 1
                
                if retry_count <= self.max_retries:
                    time.sleep(self.retry_delay)
        
        # 主工具失败，尝试回退
        if self.enable_fallback and last_error:
            return self._try_fallback(
                tool_name,
                target,
                params,
                tool_executors,
                last_error
            )
        
        # 所有尝试都失败
        return self._create_failure_result(tool_name, target, last_error)
    
    def _try_fallback(
        self,
        original_tool: str,
        target: str,
        params: Dict[str, Any],
        tool_executors: Dict[str, Callable],
        error_context: ErrorContext
    ) -> Dict[str, Any]:
        """
        尝试使用替代工具
        
        Args:
            original_tool: 原始工具名称
            target: 目标
            params: 参数
            tool_executors: 工具执行器字典
            error_context: 错误上下文
            
        Returns:
            Dict: 执行结果
        """
        alternatives = ToolAlternatives.get_alternatives(original_tool)
        
        if not alternatives:
            logger.warning(f"⚠️  No alternatives available for {original_tool}")
            return self._create_failure_result(original_tool, target, error_context)
        
        logger.info(f"🔄 Trying alternatives for {original_tool}: {alternatives}")
        
        # 尝试每个替代工具
        for alt_tool in alternatives:
            # 检查替代工具是否可用
            from core.utils.tool_checker import ToolChecker
            if not ToolChecker.is_tool_available(alt_tool):
                logger.debug(f"⏭️  Skipping {alt_tool} (not installed)")
                continue
            
            # 获取替代工具的执行器
            alt_executor = tool_executors.get(alt_tool)
            if not alt_executor:
                logger.debug(f"⏭️  Skipping {alt_tool} (no executor)")
                continue
            
            try:
                logger.info(f"🔄 Trying alternative: {alt_tool}")
                result = alt_executor(target, params)
                
                if isinstance(result, dict) and result.get('success'):
                    logger.info(f"✅ Alternative {alt_tool} succeeded")
                    return {
                        **result,
                        'used_alternative': True,
                        'original_tool': original_tool,
                        'alternative_tool': alt_tool
                    }
            
            except Exception as e:
                logger.warning(f"⚠️  Alternative {alt_tool} failed: {str(e)}")
                continue
        
        # 所有替代工具都失败
        logger.error(f"❌ All alternatives failed for {original_tool}")
        return self._create_failure_result(original_tool, target, error_context)
    
    def _create_failure_result(
        self,
        tool_name: str,
        target: str,
        error_context: Optional[ErrorContext]
    ) -> Dict[str, Any]:
        """
        创建失败结果
        
        Args:
            tool_name: 工具名称
            target: 目标
            error_context: 错误上下文
            
        Returns:
            Dict: 失败结果
        """
        if error_context:
            return {
                'success': False,
                'tool': tool_name,
                'target': target,
                'error': error_context.error_message,
                'error_type': error_context.error_type.value,
                'retry_count': error_context.retry_count,
                'suggestions': error_context.suggestions or [],
                'timestamp': error_context.timestamp
            }
        else:
            return {
                'success': False,
                'tool': tool_name,
                'target': target,
                'error': 'Unknown error',
                'suggestions': ['Review error logs', 'Check tool installation']
            }


# 全局实例
resilient_executor = ResilientExecutor(
    max_retries=2,
    retry_delay=2,
    enable_fallback=True
)
