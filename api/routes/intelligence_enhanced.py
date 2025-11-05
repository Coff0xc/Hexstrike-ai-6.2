"""
增强的智能扫描路由
集成了工具检查、并行执行、缓存优化和错误处理
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

# 导入新模块
from core.utils.tool_checker import tool_checker
from core.execution.parallel_scanner import ParallelScanner, ScanTask
from core.cache.scan_cache import cache_executor
from core.execution.error_handler import resilient_executor

logger = logging.getLogger(__name__)

# Create blueprint
intelligence_enhanced_bp = Blueprint('intelligence_enhanced', __name__, url_prefix='/api/intelligence/v2')

# Dependencies
decision_engine = None
tool_executors = None


def init_app(dec_engine, executors):
    """Initialize blueprint with dependencies"""
    global decision_engine, tool_executors
    decision_engine = dec_engine
    tool_executors = executors


@intelligence_enhanced_bp.route("/tool-check", methods=["GET"])
def check_tools():
    """检查系统工具可用性"""
    try:
        logger.info("🔍 Checking system tools availability")
        
        report = tool_checker.get_system_report()
        
        logger.info(
            f"✅ Tool check completed: "
            f"{report['available_tools']}/{report['total_tools']} available "
            f"({report['coverage_percentage']:.1f}%)"
        )
        
        return jsonify({
            "success": True,
            "report": report,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Tool check error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@intelligence_enhanced_bp.route("/generate-install-script", methods=["POST"])
def generate_install_script():
    """生成工具安装脚本"""
    try:
        data = request.get_json() or {}
        output_file = data.get('output_file', 'install_missing_tools.sh')
        
        logger.info(f"📝 Generating install script: {output_file}")
        
        script_path = tool_checker.generate_install_script(output_file)
        
        if script_path:
            return jsonify({
                "success": True,
                "script_path": script_path,
                "message": f"Install script generated: {script_path}",
                "usage": f"Run with: ./{script_path}"
            })
        else:
            return jsonify({
                "success": True,
                "message": "All tools are already installed!"
            })
    
    except Exception as e:
        logger.error(f"❌ Script generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@intelligence_enhanced_bp.route("/smart-scan-enhanced", methods=["POST"])
def smart_scan_enhanced():
    """
    增强的智能扫描
    集成工具检查、并行执行、缓存和错误处理
    """
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({"error": "Target is required"}), 400
        
        target = data['target']
        objective = data.get('objective', 'comprehensive')
        max_tools = data.get('max_tools', 5)
        force_refresh = data.get('force_refresh', False)
        max_workers = data.get('max_workers', 5)
        enable_cache = data.get('enable_cache', True)
        enable_retry = data.get('enable_retry', True)
        enable_fallback = data.get('enable_fallback', True)
        
        logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║ 🚀 ENHANCED INTELLIGENT SCAN                                ║
╠══════════════════════════════════════════════════════════════╣
║ Target:          {target:<44} ║
║ Objective:       {objective:<44} ║
║ Max Tools:       {max_tools:<44} ║
║ Cache:           {'Enabled' if enable_cache else 'Disabled':<44} ║
║ Retry:           {'Enabled' if enable_retry else 'Disabled':<44} ║
║ Fallback:        {'Enabled' if enable_fallback else 'Disabled':<44} ║
║ Max Workers:     {max_workers:<44} ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # 1. 分析目标
        logger.info("📊 Step 1/5: Analyzing target...")
        profile = decision_engine.analyze_target(target)
        
        # 2. 选择最优工具
        logger.info("🎯 Step 2/5: Selecting optimal tools...")
        selected_tools = decision_engine.select_optimal_tools(profile, objective)[:max_tools]
        
        # 3. 过滤可用工具
        logger.info("🔍 Step 3/5: Checking tool availability...")
        available_tools = []
        unavailable_tools = []
        
        for tool in selected_tools:
            if tool_checker.is_tool_available(tool):
                available_tools.append(tool)
            else:
                unavailable_tools.append(tool)
                logger.warning(f"⚠️  Tool not available: {tool}")
        
        if not available_tools:
            return jsonify({
                "success": False,
                "error": "No available tools found",
                "unavailable_tools": unavailable_tools,
                "suggestions": [
                    tool_checker.check_tool_or_error(tool)
                    for tool in unavailable_tools
                ]
            }), 400
        
        logger.info(f"✅ Available tools: {len(available_tools)}/{len(selected_tools)}")
        
        # 4. 创建扫描任务
        logger.info("📋 Step 4/5: Creating scan tasks...")
        scanner = ParallelScanner(max_workers=max_workers)
        tasks = []
        
        for tool_name in available_tools:
            # 获取优化的参数
            optimized_params = decision_engine.optimize_parameters(tool_name, profile)
            
            # 创建任务
            task = scanner.create_task_from_selection(
                tool_name=tool_name,
                target=target,
                params=optimized_params,
                priority=1 if 'nmap' in tool_name or 'nuclei' in tool_name else 0
            )
            tasks.append(task)
        
        # 5. 执行扫描（带缓存和错误处理）
        logger.info("🚀 Step 5/5: Executing parallel scan...")
        
        def create_cached_executor(tool_name):
            """为工具创建带缓存的执行器"""
            original_executor = tool_executors.get(tool_name)
            
            if not original_executor:
                return None
            
            def cached_wrapper(target, params):
                if enable_cache and not force_refresh:
                    # 尝试从缓存获取
                    return cache_executor.execute_with_cache(
                        tool_name=tool_name,
                        target=target,
                        params=params,
                        executor_func=original_executor,
                        force_refresh=force_refresh,
                        scan_type=objective
                    )
                else:
                    # 直接执行
                    return original_executor(target, params)
            
            # 如果启用了重试和回退
            if enable_retry or enable_fallback:
                def resilient_wrapper(target, params):
                    return resilient_executor.execute_with_resilience(
                        tool_name=tool_name,
                        target=target,
                        params=params,
                        executor_func=cached_wrapper,
                        tool_executors=tool_executors
                    )
                return resilient_wrapper
            else:
                return cached_wrapper
        
        # 创建增强的执行器字典
        enhanced_executors = {
            tool_name: create_cached_executor(tool_name)
            for tool_name in available_tools
        }
        
        # 进度回调
        progress = {"completed": 0, "total": len(tasks)}
        
        def progress_callback(completed, total, current_tool):
            progress["completed"] = completed
            logger.info(f"📊 Progress: {completed}/{total} ({completed/total*100:.1f}%) - Completed: {current_tool}")
        
        # 执行并行扫描
        results = scanner.execute_parallel(
            tasks=tasks,
            tool_executors=enhanced_executors,
            progress_callback=progress_callback
        )
        
        # 6. 处理结果
        logger.info("📊 Processing results...")
        
        tools_executed = []
        total_vulnerabilities = 0
        successful_tools = []
        failed_tools = []
        cached_results = 0
        
        for tool_name, scan_result in results.items():
            tool_data = {
                "tool": tool_name,
                "success": scan_result.success,
                "execution_time": scan_result.execution_time,
                "timed_out": scan_result.timed_out,
                "error": scan_result.error,
                "from_cache": scan_result.result.get('from_cache', False),
                "used_alternative": scan_result.result.get('used_alternative', False),
                "result": scan_result.result
            }
            
            tools_executed.append(tool_data)
            
            if scan_result.success:
                successful_tools.append(tool_name)
                
                # 统计漏洞
                if 'stdout' in scan_result.result:
                    output = scan_result.result['stdout']
                    vuln_indicators = ['CRITICAL', 'HIGH', 'MEDIUM', 'VULNERABILITY', 'SQL injection', 'XSS']
                    vuln_count = sum(1 for indicator in vuln_indicators if indicator.lower() in output.lower())
                    total_vulnerabilities += vuln_count
            else:
                failed_tools.append(tool_name)
            
            if tool_data.get('from_cache'):
                cached_results += 1
        
        # 生成执行摘要
        total_time = sum(r.execution_time for r in results.values())
        
        response = {
            "success": True,
            "target": target,
            "objective": objective,
            "target_profile": profile.to_dict(),
            "tools_executed": tools_executed,
            "execution_summary": {
                "total_tools": len(tasks),
                "successful_tools": len(successful_tools),
                "failed_tools": len(failed_tools),
                "cached_results": cached_results,
                "unavailable_tools": len(unavailable_tools),
                "total_execution_time": round(total_time, 2),
                "average_time_per_tool": round(total_time / len(tasks), 2) if tasks else 0,
                "successful_tool_names": successful_tools,
                "failed_tool_names": failed_tools,
                "unavailable_tool_names": unavailable_tools
            },
            "vulnerabilities": {
                "total_found": total_vulnerabilities,
                "requires_review": total_vulnerabilities > 0
            },
            "timestamp": datetime.now().isoformat(),
            "enhancements_used": {
                "tool_availability_check": True,
                "parallel_execution": True,
                "result_caching": enable_cache,
                "error_retry": enable_retry,
                "tool_fallback": enable_fallback
            }
        }
        
        logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║ ✅ SCAN COMPLETED                                           ║
╠══════════════════════════════════════════════════════════════╣
║ Successful:      {len(successful_tools)}/{len(tasks):<44} ║
║ Failed:          {len(failed_tools):<44} ║
║ Cached:          {cached_results:<44} ║
║ Vulnerabilities: {total_vulnerabilities:<44} ║
║ Total Time:      {total_time:.2f}s{'':<38} ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"❌ Enhanced smart scan error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@intelligence_enhanced_bp.route("/cache-stats", methods=["GET"])
def get_cache_stats():
    """获取缓存统计信息"""
    try:
        from core.cache.scan_cache import scan_cache
        
        stats = scan_cache.get_stats()
        
        return jsonify({
            "success": True,
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Cache stats error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@intelligence_enhanced_bp.route("/cache-clear", methods=["POST"])
def clear_cache():
    """清除缓存"""
    try:
        from core.cache.scan_cache import scan_cache
        
        data = request.get_json() or {}
        pattern = data.get('pattern')
        
        count = scan_cache.clear_all(pattern)
        
        return jsonify({
            "success": True,
            "cleared_entries": count,
            "message": f"Cleared {count} cache entries",
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Cache clear error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
