"""
并行扫描执行器
支持多工具并行执行，提高扫描效率
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScanTask:
    """扫描任务数据类"""
    tool_name: str
    target: str
    params: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300
    priority: int = 0  # 优先级：数值越大优先级越高


@dataclass
class ScanResult:
    """扫描结果数据类"""
    tool_name: str
    target: str
    success: bool
    result: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None
    timed_out: bool = False


class ParallelScanner:
    """并行扫描执行器"""
    
    # 工具默认超时时间（秒）
    DEFAULT_TIMEOUTS = {
        'httpx': 30,
        'nuclei': 300,
        'nmap': 120,
        'nmap-advanced': 300,
        'sqlmap': 600,
        'nikto': 300,
        'gobuster': 180,
        'feroxbuster': 180,
        'ffuf': 180,
        'amass': 600,
        'subfinder': 60,
        'katana': 120,
        'dalfox': 300,
        'arjun': 120,
        'masscan': 180,
    }
    
    def __init__(self, max_workers: int = 5):
        """
        初始化并行扫描器
        
        Args:
            max_workers: 最大并行工作线程数
        """
        self.max_workers = max_workers
        logger.info(f"🚀 Parallel scanner initialized with {max_workers} workers")
    
    def execute_single_task(
        self, 
        task: ScanTask, 
        executor_func: Callable
    ) -> ScanResult:
        """
        执行单个扫描任务
        
        Args:
            task: 扫描任务
            executor_func: 工具执行函数
            
        Returns:
            ScanResult: 扫描结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔧 Executing {task.tool_name} on {task.target}")
            
            # 执行工具
            result = executor_func(task.target, task.params)
            
            execution_time = time.time() - start_time
            
            # 检查是否成功
            success = result.get('success', False) if isinstance(result, dict) else False
            
            return ScanResult(
                tool_name=task.tool_name,
                target=task.target,
                success=success,
                result=result,
                execution_time=execution_time,
                timed_out=result.get('timed_out', False) if isinstance(result, dict) else False
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {task.tool_name} failed: {str(e)}")
            
            return ScanResult(
                tool_name=task.tool_name,
                target=task.target,
                success=False,
                result={},
                execution_time=execution_time,
                error=str(e)
            )
    
    def execute_parallel(
        self, 
        tasks: List[ScanTask],
        tool_executors: Dict[str, Callable],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, ScanResult]:
        """
        并行执行多个扫描任务
        
        Args:
            tasks: 扫描任务列表
            tool_executors: 工具执行器字典 {tool_name: executor_func}
            progress_callback: 进度回调函数(completed, total, current_tool)
            
        Returns:
            Dict[str, ScanResult]: 工具名称到扫描结果的映射
        """
        if not tasks:
            logger.warning("⚠️  No tasks to execute")
            return {}
        
        # 按优先级排序任务
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        results = {}
        total_tasks = len(sorted_tasks)
        completed_tasks = 0
        
        logger.info(f"🚀 Starting parallel execution of {total_tasks} tasks")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {}
            
            for task in sorted_tasks:
                # 获取工具执行器
                executor_func = tool_executors.get(task.tool_name)
                
                if not executor_func:
                    logger.error(f"❌ No executor found for {task.tool_name}")
                    results[task.tool_name] = ScanResult(
                        tool_name=task.tool_name,
                        target=task.target,
                        success=False,
                        result={},
                        execution_time=0,
                        error=f"No executor found for {task.tool_name}"
                    )
                    continue
                
                # 提交任务
                future = executor.submit(
                    self.execute_single_task,
                    task,
                    executor_func
                )
                future_to_task[future] = task
            
            # 等待任务完成
            for future in as_completed(future_to_task, timeout=None):
                task = future_to_task[future]
                
                try:
                    # 获取结果（带超时）
                    result = future.result(timeout=task.timeout)
                    results[task.tool_name] = result
                    
                    completed_tasks += 1
                    
                    if result.success:
                        logger.info(
                            f"✅ [{completed_tasks}/{total_tasks}] "
                            f"{task.tool_name} completed in {result.execution_time:.2f}s"
                        )
                    else:
                        logger.warning(
                            f"⚠️  [{completed_tasks}/{total_tasks}] "
                            f"{task.tool_name} failed"
                        )
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(completed_tasks, total_tasks, task.tool_name)
                    
                except FutureTimeoutError:
                    logger.error(f"⏱️  {task.tool_name} timed out after {task.timeout}s")
                    results[task.tool_name] = ScanResult(
                        tool_name=task.tool_name,
                        target=task.target,
                        success=False,
                        result={},
                        execution_time=task.timeout,
                        error=f"Timeout after {task.timeout}s",
                        timed_out=True
                    )
                    completed_tasks += 1
                    
                except Exception as e:
                    logger.error(f"❌ {task.tool_name} raised exception: {str(e)}")
                    results[task.tool_name] = ScanResult(
                        tool_name=task.tool_name,
                        target=task.target,
                        success=False,
                        result={},
                        execution_time=0,
                        error=str(e)
                    )
                    completed_tasks += 1
        
        # 生成执行摘要
        successful = sum(1 for r in results.values() if r.success)
        failed = len(results) - successful
        total_time = sum(r.execution_time for r in results.values())
        
        logger.info(f"""
┌────────────────────────────────────────────┐
│ 🎯 Parallel Scan Execution Summary        │
├────────────────────────────────────────────┤
│ Total Tasks:     {total_tasks:4d}                    │
│ Successful:      {successful:4d} ✅                  │
│ Failed:          {failed:4d} ❌                  │
│ Total Time:      {total_time:6.2f}s                │
│ Avg Time/Task:   {total_time/total_tasks if total_tasks > 0 else 0:6.2f}s                │
└────────────────────────────────────────────┘
        """)
        
        return results
    
    def get_default_timeout(self, tool_name: str) -> int:
        """
        获取工具的默认超时时间
        
        Args:
            tool_name: 工具名称
            
        Returns:
            int: 超时时间（秒）
        """
        return self.DEFAULT_TIMEOUTS.get(tool_name, 300)
    
    def create_task_from_selection(
        self, 
        tool_name: str, 
        target: str, 
        params: Optional[Dict] = None,
        priority: int = 0
    ) -> ScanTask:
        """
        从工具选择创建扫描任务
        
        Args:
            tool_name: 工具名称
            target: 目标
            params: 参数
            priority: 优先级
            
        Returns:
            ScanTask: 扫描任务
        """
        return ScanTask(
            tool_name=tool_name,
            target=target,
            params=params or {},
            timeout=self.get_default_timeout(tool_name),
            priority=priority
        )


class SmartParallelScanner(ParallelScanner):
    """智能并行扫描器 - 增强版"""
    
    def __init__(self, max_workers: int = 5):
        super().__init__(max_workers)
        self.execution_history = []
    
    def execute_with_retry(
        self,
        tasks: List[ScanTask],
        tool_executors: Dict[str, Callable],
        max_retries: int = 2,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, ScanResult]:
        """
        带重试机制的并行执行
        
        Args:
            tasks: 扫描任务列表
            tool_executors: 工具执行器字典
            max_retries: 最大重试次数
            progress_callback: 进度回调
            
        Returns:
            Dict[str, ScanResult]: 扫描结果
        """
        all_results = {}
        remaining_tasks = tasks.copy()
        retry_count = 0
        
        while remaining_tasks and retry_count <= max_retries:
            if retry_count > 0:
                logger.info(f"🔄 Retry attempt {retry_count}/{max_retries} for {len(remaining_tasks)} tasks")
            
            # 执行当前批次
            results = self.execute_parallel(
                remaining_tasks,
                tool_executors,
                progress_callback
            )
            
            # 更新总结果
            all_results.update(results)
            
            # 找出失败的任务（非超时）
            failed_tasks = [
                task for task in remaining_tasks
                if task.tool_name in results 
                and not results[task.tool_name].success
                and not results[task.tool_name].timed_out
            ]
            
            if not failed_tasks or retry_count >= max_retries:
                break
            
            remaining_tasks = failed_tasks
            retry_count += 1
            
            # 短暂延迟后重试
            time.sleep(2)
        
        return all_results
    
    def execute_with_dependencies(
        self,
        task_groups: List[List[ScanTask]],
        tool_executors: Dict[str, Callable],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, ScanResult]:
        """
        按依赖顺序执行任务组
        每组内并行执行，组间串行执行
        
        Args:
            task_groups: 任务组列表，按依赖顺序排列
            tool_executors: 工具执行器字典
            progress_callback: 进度回调
            
        Returns:
            Dict[str, ScanResult]: 所有扫描结果
        """
        all_results = {}
        
        for group_idx, task_group in enumerate(task_groups, 1):
            logger.info(f"📋 Executing task group {group_idx}/{len(task_groups)}")
            
            # 并行执行当前组
            group_results = self.execute_parallel(
                task_group,
                tool_executors,
                progress_callback
            )
            
            all_results.update(group_results)
            
            # 检查组内是否有关键任务失败
            critical_failures = [
                task.tool_name for task in task_group
                if not group_results.get(task.tool_name, ScanResult(
                    tool_name=task.tool_name,
                    target=task.target,
                    success=False,
                    result={},
                    execution_time=0
                )).success
            ]
            
            if critical_failures:
                logger.warning(
                    f"⚠️  Group {group_idx} has failed tasks: {', '.join(critical_failures)}"
                )
        
        return all_results


# 全局实例
parallel_scanner = ParallelScanner(max_workers=5)
smart_scanner = SmartParallelScanner(max_workers=5)
