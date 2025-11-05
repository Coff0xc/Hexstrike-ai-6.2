#!/usr/bin/env python3
"""
HexStrike AI - Advanced Penetration Testing Framework Server

Enhanced with AI-Powered Intelligence & Automation
🚀 Bug Bounty | CTF | Red Team | Security Research

RECENT ENHANCEMENTS (v6.2):
✅ Celery-based async task queue for long-running scans
✅ Intelligent AI-powered vulnerability analysis
✅ Automated exploit suggestion generation
✅ Attack vector prediction using ML
✅ Smart payload generation with WAF bypass
✅ Task progress tracking and cancellation
✅ Distributed worker management
✅ Periodic maintenance tasks (CVE updates, cleanup)

v6.1 ENHANCEMENTS:
✅ Performance optimization with connection pooling and compression
✅ Rate limiting and circuit breaker patterns
✅ Redis cache support for distributed deployments

Architecture: Two-script system (hexstrike_server.py + hexstrike_mcp.py)
Framework: FastMCP integration for AI agent communication
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import traceback
import threading
import time
import hashlib
import pickle
import base64
import queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import OrderedDict
import shutil
import venv
import zipfile
from pathlib import Path
from flask import Flask, request, jsonify
import psutil
import signal
import requests
import re
import socket
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Tuple
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

# Optional imports for advanced web testing features
try:
    import selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import mitmproxy
    from mitmproxy import http as mitmhttp
    from mitmproxy.tools.dump import DumpMaster
    from mitmproxy.options import Options as MitmOptions
    MITMPROXY_AVAILABLE = True
except ImportError:
    MITMPROXY_AVAILABLE = False

# ============================================================================
# LOGGING CONFIGURATION (MUST BE FIRST)
# ============================================================================

# Configure logging with fallback for permission issues
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('hexstrike.log')
        ]
    )
except PermissionError:
    # Fallback to console-only logging if file creation fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# API Configuration
API_PORT = int(os.environ.get('HEXSTRIKE_PORT', 8888))
API_HOST = os.environ.get('HEXSTRIKE_HOST', '127.0.0.1')

# ============================================================================
# REFACTORED IMPORTS - Phase 1 Modularization
# ============================================================================
# Import core modules from new modular architecture
from core.visual import ModernVisualEngine
from core.cache import HexStrikeCache
from core.telemetry import TelemetryCollector

# Performance optimization modules (v6.1)
from core.performance_optimizer import (
    PerformanceOptimizer,
    HTTPConnectionPool,
    TokenBucketRateLimiter,
    CircuitBreaker,
    CompressionMiddleware,
    CacheWarmer,
    RedisCache,
    AdaptiveWorkerPool,
    LazyImportManager
)
from config.performance import PerformanceConfig
from api.middleware import (
    MiddlewareManager,
    FlaskCompressionMiddleware,
    FlaskRateLimitMiddleware,
    FlaskPerformanceMiddleware,
    FlaskCORSMiddleware,
    FlaskSecurityHeadersMiddleware,
    FlaskRequestIDMiddleware
)

# Phase 5C Batch 1: Core System Classes
from core.degradation import GracefulDegradation
from core.process_pool import ProcessPool
from core.enhanced_process import EnhancedProcessManager
from core.command_executor import EnhancedCommandExecutor
from core.file_manager import FileOperationsManager
from core.file_upload_testing import FileUploadTestingFramework

# Phase 5C Batch 3: Workflow & Support Classes
from core.process_manager import ProcessManager
from core.advanced_cache import AdvancedCache
from core.resource_monitor import ResourceMonitor
from core.performance import PerformanceDashboard
from core.python_env_manager import PythonEnvironmentManager
from core.logging_formatter import ColoredFormatter
from core.http_testing_framework import HTTPTestingFramework

# Import agents modules
from agents.bugbounty import BugBountyWorkflowManager, BugBountyTarget
from agents.ctf import CTFWorkflowManager, CTFChallenge, CTFToolManager
from agents.cve import CVEIntelligenceManager
from agents.decision_engine import IntelligentDecisionEngine, TargetProfile, AttackChain
from agents.ai_payload_generator import AIPayloadGenerator, ai_payload_generator
from agents.browser_agent import BrowserAgent

# Phase 5C Batch 2: Exploit Generation System
from agents.cve.exploit_ai import AIExploitGenerator
from agents.cve.exploits import (
    SQLiExploit, XSSExploit, FileReadExploit, RCEExploit,
    XXEExploit, DeserializationExploit, AuthBypassExploit,
    BufferOverflowExploit, GenericExploit
)

# Phase 5C Batch 3: CTF Agent Classes
from agents.ctf.automator import CTFChallengeAutomator
from agents.ctf.coordinator import CTFTeamCoordinator
from agents.cve.correlator import VulnerabilityCorrelator
from core.error_handler import IntelligentErrorHandler, ErrorType, RecoveryAction

# Phase 5C Batch 4: Command Execution & Tool Factory
from core.execution import (
    execute_command,
    execute_command_with_recovery
)
from core.tool_factory import create_tool_executor

# Phase 2: Tool Abstraction Layer
from tools.network.nmap import NmapTool
from tools.network.httpx import HttpxTool
from tools.network.masscan import MasscanTool
from tools.network.dnsenum import DNSEnumTool
from tools.network.fierce import FierceTool
from tools.network.dnsx import DNSxTool
from tools.web.nuclei import NucleiTool
from tools.web.gobuster import GobusterTool
from tools.web.sqlmap import SQLMapTool
from tools.web.nikto import NiktoTool
from tools.web.feroxbuster import FeroxbusterTool
from tools.web.ffuf import FfufTool
from tools.web.katana import KatanaTool
from tools.web.wpscan import WpscanTool
from tools.web.arjun import ArjunTool
from tools.web.dalfox import DalfoxTool
from tools.web.whatweb import WhatwebTool
from tools.web.dirsearch import DirsearchTool
from tools.web.paramspider import ParamSpiderTool
from tools.web.x8 import X8Tool
from tools.recon.amass import AmassTool
from tools.recon.subfinder import SubfinderTool
from tools.recon.waybackurls import WaybackURLsTool
from tools.recon.gau import GAUTool
from tools.recon.hakrawler import HakrawlerTool
from tools.security.testssl import TestSSLTool
from tools.security.sslscan import SSLScanTool
from tools.security.jaeles import JaelesTool
from tools.security.zap import ZAPTool
from tools.security.burpsuite import BurpSuiteTool


# ============================================================================
# INTELLIGENT DECISION ENGINE (v6.0 ENHANCEMENT)
# ============================================================================


# Global decision engine instance
decision_engine = IntelligentDecisionEngine()

# Global error handler and degradation manager instances
error_handler = IntelligentErrorHandler()
degradation_manager = GracefulDegradation()

# ============================================================================
# BUG BOUNTY HUNTING SPECIALIZED WORKFLOWS (v6.0 ENHANCEMENT)
# ============================================================================
# NOTE: BugBountyTarget and BugBountyWorkflowManager moved to agents/bugbounty/workflow_manager.py

# ============================================================================
# CTF COMPETITION EXCELLENCE FRAMEWORK (v6.0 ENHANCEMENT)
# ============================================================================

# ============================================================================
# CTF COMPETITION EXCELLENCE FRAMEWORK (v6.0 ENHANCEMENT)
# ============================================================================
# NOTE: CTFChallenge, CTFWorkflowManager, and CTFToolManager moved to agents/ctf/workflow_manager.py



# ============================================================================
# ADVANCED PARAMETER OPTIMIZATION AND INTELLIGENCE (v9.0 ENHANCEMENT)
# ============================================================================
# NOTE: Optimization classes moved to core/optimizer.py
from core.optimizer import (
    TechnologyDetector,
    RateLimitDetector,
    FailureRecoverySystem,
    PerformanceMonitor,
    ParameterOptimizer
)


# ============================================================================
# ADVANCED PROCESS MANAGEMENT AND MONITORING (v10.0 ENHANCEMENT)
# ============================================================================






# Global instances
tech_detector = TechnologyDetector()
rate_limiter = RateLimitDetector()
failure_recovery = FailureRecoverySystem()
performance_monitor = PerformanceMonitor()
parameter_optimizer = ParameterOptimizer()
enhanced_process_manager = EnhancedProcessManager()

# Global CTF framework instances
ctf_manager = CTFWorkflowManager()
ctf_tools = CTFToolManager()
ctf_automator = CTFChallengeAutomator()
ctf_coordinator = CTFTeamCoordinator()

# Global Bug Bounty framework instance
bugbounty_manager = BugBountyWorkflowManager()

# Global Web Testing Framework instances
http_testing_framework = HTTPTestingFramework()
browser_agent = BrowserAgent()

# ============================================================================
# PROCESS MANAGEMENT FOR COMMAND TERMINATION (v5.0 ENHANCEMENT)
# ============================================================================

# Process management for command termination
active_processes = {}  # pid -> process info
process_lock = threading.Lock()



# Global environment manager
env_manager = PythonEnvironmentManager()

# ============================================================================
# ADVANCED VULNERABILITY INTELLIGENCE SYSTEM (v6.0 ENHANCEMENT)
# ============================================================================

# ============================================================================
# CVE INTELLIGENCE AND VULNERABILITY MANAGEMENT
# ============================================================================
# NOTE: CVEIntelligenceManager moved to agents/cve/intelligence_manager.py


# Enhanced logging setup
def setup_logging():
    """Setup enhanced logging with colors and formatting"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(
        "[🔥 HexStrike AI] %(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(console_handler)

    return logger

# Configuration (using existing API_PORT from top of file)
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes", "y")
COMMAND_TIMEOUT = 300  # 5 minutes default timeout
CACHE_SIZE = 1000
CACHE_TTL = 3600  # 1 hour

# End of HexStrikeCache and TelemetryCollector classes - now in core/cache.py and core/telemetry.py

# Global instances using imported classes
cache = HexStrikeCache()
telemetry = TelemetryCollector()

# ============================================================================
# PERFORMANCE OPTIMIZATION INITIALIZATION (v6.1)
# ============================================================================

# 初始化性能优化器
performance_config = PerformanceConfig.get_config()
performance_optimizer = PerformanceOptimizer(performance_config)

# 初始化限流器
rate_limiter = performance_optimizer.rate_limiter

# 初始化中间件管理器
middleware_config = {
    'compression_enabled': PerformanceConfig.COMPRESSION['enabled'],
    'compression_min_size': PerformanceConfig.COMPRESSION['min_size'],
    'compression_level': PerformanceConfig.COMPRESSION['level'],
    'cors_enabled': True,
    'security_headers_enabled': True,
    'request_id_enabled': True,
    'rate_limiter': rate_limiter
}
middleware_manager = MiddlewareManager()

# 初始化懒加载管理器
lazy_loader = performance_optimizer.lazy_import_manager

# 注册需要懒加载的模块
if PerformanceConfig.LAZY_LOADING['enabled']:
    for module_name in PerformanceConfig.LAZY_LOADING['modules']:
        try:
            if module_name == 'selenium':
                lazy_loader.register('selenium', lambda: __import__('selenium'))
            elif module_name == 'mitmproxy':
                lazy_loader.register('mitmproxy', lambda: __import__('mitmproxy'))
            elif module_name == 'angr':
                lazy_loader.register('angr', lambda: __import__('angr'))
            elif module_name == 'pwntools':
                lazy_loader.register('pwntools', lambda: __import__('pwn'))
        except Exception as e:
            logger.warning(f"Failed to register lazy module {module_name}: {e}")


# ============================================================================
# DUPLICATE CLASSES REMOVED - Using the first definitions above
# ============================================================================

# ============================================================================
# AI-POWERED EXPLOIT GENERATION SYSTEM (v6.0 ENHANCEMENT)
# ============================================================================
#
# This section contains advanced AI-powered exploit generation capabilities
# for automated vulnerability exploitation and proof-of-concept development.
#
# Features:
# - Automated exploit template generation from CVE data
# - Multi-architecture support (x86, x64, ARM)
# - Evasion technique integration
# - Custom payload generation
# - Exploit effectiveness scoring
#
# ============================================================================





# Global intelligence managers
cve_intelligence = CVEIntelligenceManager()
exploit_generator = AIExploitGenerator()
vulnerability_correlator = VulnerabilityCorrelator()





# File Operations Manager

# Global file operations manager
file_manager = FileOperationsManager()

# ============================================================================
# REGISTER API BLUEPRINTS
# ============================================================================
from api.routes.files import files_bp
from api.routes.visual import visual_bp
from api.routes.error_handling import error_handling_bp
from api.routes.intelligence import intelligence_bp
from api.routes.intelligence_enhanced import intelligence_enhanced_bp
from api.routes.processes import processes_bp
from api.routes.bugbounty import bugbounty_bp
from api.routes.ctf import ctf_bp
from api.routes.vuln_intel import vuln_intel_bp
from api.routes.core import core_bp
from api.routes.ai import ai_bp
from api.routes.python_env import python_env_bp
from api.routes.process_workflows import process_workflows_bp
from api.routes.tools_cloud import tools_cloud_bp
from api.routes.tools_web import tools_web_bp
from api.routes.tools_network import tools_network_bp
from api.routes.tools_web_advanced import tools_web_advanced_bp
from api.routes.tools_exploit import tools_exploit_bp
from api.routes.tools_binary import tools_binary_bp
from api.routes.tools_api import tools_api_bp
from api.routes.tools_parameters import tools_parameters_bp
from api.routes.tools_forensics import tools_forensics_bp
from api.routes.tools_web_frameworks import tools_web_frameworks_bp
from api.routes.performance import performance_bp
from api.routes.tasks import tasks_bp
import api.routes.files as files_routes
import api.routes.error_handling as error_handling_routes
import api.routes.intelligence as intelligence_routes
import api.routes.processes as processes_routes
import api.routes.bugbounty as bugbounty_routes
import api.routes.ctf as ctf_routes
import api.routes.vuln_intel as vuln_intel_routes
import api.routes.core as core_routes
import api.routes.ai as ai_routes
import api.routes.python_env as python_env_routes
import api.routes.process_workflows as process_workflows_routes
import api.routes.tools_cloud as tools_cloud_routes
import api.routes.tools_web as tools_web_routes
import api.routes.tools_web_advanced as tools_web_advanced_routes
import api.routes.tools_network as tools_network_routes
import api.routes.tools_exploit as tools_exploit_routes
import api.routes.tools_binary as tools_binary_routes
import api.routes.tools_api as tools_api_routes
import api.routes.tools_parameters as tools_parameters_routes
import api.routes.tools_forensics as tools_forensics_routes
import api.routes.tools_web_frameworks as tools_web_frameworks_routes
import api.routes.performance as performance_routes

files_routes.init_app(file_manager)
error_handling_routes.init_app(error_handler, degradation_manager, execute_command_with_recovery)
processes_routes.init_app(ProcessManager)
bugbounty_routes.init_app(bugbounty_manager, None, BugBountyTarget)  # fileupload_framework=None (not implemented)
ctf_routes.init_app(ctf_manager, ctf_tools, ctf_automator, ctf_coordinator)
vuln_intel_routes.init_app(cve_intelligence, exploit_generator, vulnerability_correlator)
core_routes.init_app(execute_command, cache, telemetry, file_manager)
python_env_routes.init_app(env_manager, file_manager, execute_command)
process_workflows_routes.init_app(enhanced_process_manager)
tools_cloud_routes.init_app(execute_command)
tools_web_routes.init_app(execute_command)
tools_web_advanced_routes.init_app(execute_command)
tools_network_routes.init_app(execute_command, execute_command_with_recovery)
tools_exploit_routes.init_app(execute_command)
tools_binary_routes.init_app(execute_command)
tools_api_routes.init_app(execute_command)
tools_parameters_routes.init_app(execute_command)
tools_forensics_routes.init_app(execute_command)
tools_web_frameworks_routes.init_app(http_testing_framework, browser_agent)
ai_routes.init_app(ai_payload_generator, execute_command)
performance_routes.init_app(performance_optimizer, middleware_manager, cache, telemetry)
app.register_blueprint(files_bp)
app.register_blueprint(visual_bp)
app.register_blueprint(error_handling_bp)
app.register_blueprint(processes_bp)
app.register_blueprint(bugbounty_bp)
app.register_blueprint(ctf_bp)
app.register_blueprint(vuln_intel_bp)
app.register_blueprint(core_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(python_env_bp)
app.register_blueprint(process_workflows_bp)
app.register_blueprint(tools_cloud_bp)
app.register_blueprint(tools_web_advanced_bp)
app.register_blueprint(tools_web_bp)
app.register_blueprint(tools_network_bp)
app.register_blueprint(tools_exploit_bp)
app.register_blueprint(tools_binary_bp)
app.register_blueprint(tools_api_bp)
app.register_blueprint(tools_parameters_bp)
app.register_blueprint(tools_forensics_bp)
app.register_blueprint(tools_web_frameworks_bp)
app.register_blueprint(performance_bp)
app.register_blueprint(tasks_bp)

# Create tool_executors dictionary for intelligence engine
# Each executor wraps a tool class and provides a simple (target, params) -> result interface

tool_executors = {
    # Network scanning tools
    'nmap': create_tool_executor(NmapTool, execute_command),
    'nmap-advanced': create_tool_executor(NmapTool, execute_command),  # Alias for advanced scans
    'httpx': create_tool_executor(HttpxTool, execute_command),
    'masscan': create_tool_executor(MasscanTool, execute_command),
    'dnsenum': create_tool_executor(DNSEnumTool, execute_command),
    'fierce': create_tool_executor(FierceTool, execute_command),
    'dnsx': create_tool_executor(DNSxTool, execute_command),
    
    # Web scanning tools
    'nuclei': create_tool_executor(NucleiTool, execute_command),
    'gobuster': create_tool_executor(GobusterTool, execute_command),
    'sqlmap': create_tool_executor(SQLMapTool, execute_command),
    'nikto': create_tool_executor(NiktoTool, execute_command),
    'feroxbuster': create_tool_executor(FeroxbusterTool, execute_command),
    'ffuf': create_tool_executor(FfufTool, execute_command),
    'katana': create_tool_executor(KatanaTool, execute_command),
    'wpscan': create_tool_executor(WpscanTool, execute_command),
    'arjun': create_tool_executor(ArjunTool, execute_command),
    'dalfox': create_tool_executor(DalfoxTool, execute_command),
    'whatweb': create_tool_executor(WhatwebTool, execute_command),
    'dirsearch': create_tool_executor(DirsearchTool, execute_command),
    'paramspider': create_tool_executor(ParamSpiderTool, execute_command),
    'x8': create_tool_executor(X8Tool, execute_command),
    
    # Reconnaissance tools
    'amass': create_tool_executor(AmassTool, execute_command),
    'subfinder': create_tool_executor(SubfinderTool, execute_command),
    'waybackurls': create_tool_executor(WaybackURLsTool, execute_command),
    'gau': create_tool_executor(GAUTool, execute_command),
    'hakrawler': create_tool_executor(HakrawlerTool, execute_command),
    
    # Security testing tools
    'testssl': create_tool_executor(TestSSLTool, execute_command),
    'sslscan': create_tool_executor(SSLScanTool, execute_command),
    'jaeles': create_tool_executor(JaelesTool, execute_command),
    'zap': create_tool_executor(ZAPTool, execute_command),
    'burpsuite': create_tool_executor(BurpSuiteTool, execute_command),
}

# Initialize and register intelligence blueprints
intelligence_routes.init_app(decision_engine, tool_executors)
app.register_blueprint(intelligence_bp)

# Register enhanced intelligence blueprint (v2 with caching, parallel execution, error handling)
from api.routes import intelligence_enhanced
intelligence_enhanced.init_app(decision_engine, tool_executors)
app.register_blueprint(intelligence_enhanced_bp)
logger.info("✅ Enhanced intelligence engine v2 registered")

# ============================================================================
# INITIALIZE MIDDLEWARE (v6.1)
# ============================================================================

# 初始化所有中间件
middleware_manager.init_app(app, middleware_config)
logger.info("✅ Performance middleware initialized")

# 初始化缓存预热器
if PerformanceConfig.CACHE_WARMUP['enabled']:
    performance_optimizer.init_cache_warmer(cache)
    logger.info("✅ Cache warmer initialized")

# ============================================================================
# SERVER STARTUP
# ============================================================================

# Create the banner after all classes are defined
BANNER = ModernVisualEngine.create_banner()

if __name__ == "__main__":
    # Display the beautiful new banner
    print(BANNER)

    parser = argparse.ArgumentParser(description="Run the HexStrike AI API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Port for the API server (default: {API_PORT})")
    args = parser.parse_args()

    if args.debug:
        DEBUG_MODE = True
        logger.setLevel(logging.DEBUG)

    if args.port != API_PORT:
        API_PORT = args.port

    # Enhanced startup messages with beautiful formatting
    redis_status = "✅ Active" if PerformanceConfig.REDIS['enabled'] else "❌ Disabled"
    compression_status = "✅ Active" if PerformanceConfig.COMPRESSION['enabled'] else "❌ Disabled"
    lazy_loading_status = "✅ Active" if PerformanceConfig.LAZY_LOADING['enabled'] else "❌ Disabled"
    
    startup_info = f"""
{ModernVisualEngine.COLORS['MATRIX_GREEN']}{ModernVisualEngine.COLORS['BOLD']}╭─────────────────────────────────────────────────────────────────────────────╮{ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['NEON_BLUE']}🚀 Starting HexStrike AI Tools API Server (v6.2){ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}├─────────────────────────────────────────────────────────────────────────────┤{ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['CYBER_ORANGE']}🌐 Port:{ModernVisualEngine.COLORS['RESET']} {API_PORT}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['WARNING']}🔧 Debug Mode:{ModernVisualEngine.COLORS['RESET']} {DEBUG_MODE}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['ELECTRIC_PURPLE']}💾 Cache Size:{ModernVisualEngine.COLORS['RESET']} {CACHE_SIZE} | TTL: {CACHE_TTL}s
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['TERMINAL_GRAY']}⏱️  Command Timeout:{ModernVisualEngine.COLORS['RESET']} {COMMAND_TIMEOUT}s
{ModernVisualEngine.COLORS['BOLD']}├─────────────────────────────────────────────────────────────────────────────┤{ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['MATRIX_GREEN']}⚡ PERFORMANCE OPTIMIZATION (v6.1){ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['NEON_BLUE']}🔌 Connection Pool:{ModernVisualEngine.COLORS['RESET']} Max {PerformanceConfig.CONNECTION_POOL['max_connections']} connections
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['CYBER_ORANGE']}⚖️  Rate Limiter:{ModernVisualEngine.COLORS['RESET']} {PerformanceConfig.RATE_LIMIT['requests_per_second']} req/s
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['ELECTRIC_PURPLE']}🗜️  Compression:{ModernVisualEngine.COLORS['RESET']} {compression_status}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['WARNING']}💾 Redis Cache:{ModernVisualEngine.COLORS['RESET']} {redis_status}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['TERMINAL_GRAY']}⏳ Lazy Loading:{ModernVisualEngine.COLORS['RESET']} {lazy_loading_status}
{ModernVisualEngine.COLORS['BOLD']}├─────────────────────────────────────────────────────────────────────────────┤{ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['ELECTRIC_PURPLE']}🤖 AI & ASYNC TASKS (v6.2 - NEW!){ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['CYBER_ORANGE']}⚙️  Celery Workers:{ModernVisualEngine.COLORS['RESET']} Ready for async tasks
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['NEON_BLUE']}🧠 AI Analysis:{ModernVisualEngine.COLORS['RESET']} Intelligent vulnerability insights
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['MATRIX_GREEN']}💡 Smart Payloads:{ModernVisualEngine.COLORS['RESET']} WAF bypass generation
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['WARNING']}🎯 Attack Vectors:{ModernVisualEngine.COLORS['RESET']} ML-powered prediction
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['MATRIX_GREEN']}✨ Enhanced Visual Engine:{ModernVisualEngine.COLORS['RESET']} Active
{ModernVisualEngine.COLORS['MATRIX_GREEN']}{ModernVisualEngine.COLORS['BOLD']}╰─────────────────────────────────────────────────────────────────────────────╯{ModernVisualEngine.COLORS['RESET']}
"""

    for line in startup_info.strip().split('\n'):
        if line.strip():
            logger.info(line)

    app.run(host="0.0.0.0", port=API_PORT, debug=DEBUG_MODE)

