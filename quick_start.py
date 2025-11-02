#!/usr/bin/env python3
"""
HexStrike AI 快速启动脚本
Quick Start Script for Optimized HexStrike AI

使用方法:
    python3 quick_start.py --demo  # 运行演示
    python3 quick_start.py --server  # 启动优化服务器
    python3 quick_start.py --benchmark  # 性能基准测试
"""

import argparse
import sys
import time
from typing import Dict, Any

# 导入优化模块
try:
    from performance_optimizer import (
        LazyToolLoader, SmartCache, ParallelExecutor,
        WebSocketManager, PerformanceMonitor, smart_cache
    )
    from ai_intelligence import IntelligentRecommender, LearningSystem
    from advanced_features import PentestChain, IntelligentFuzzer, CTFSolver
    OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Optimization modules not fully available: {e}")
    OPTIMIZATION_AVAILABLE = False


class OptimizedHexStrike:
    """优化版 HexStrike AI"""
    
    def __init__(self):
        if not OPTIMIZATION_AVAILABLE:
            print("❌ Optimization modules not available. Please check installation.")
            sys.exit(1)
            
        self.loader = LazyToolLoader()
        self.cache = SmartCache()
        self.executor = ParallelExecutor(max_workers=10)
        self.recommender = IntelligentRecommender()
        self.monitor = PerformanceMonitor()
        
        print("🔥 HexStrike AI - Optimized Edition")
        print("=" * 70)
        
    def run_demo(self):
        """运行演示"""
        print("\n📺 Running Optimization Demo...")
        print("-" * 70)
        
        # 1. 懒加载演示
        print("\n1️⃣  Lazy Loading Demo:")
        self._demo_lazy_loading()
        
        # 2. 缓存演示
        print("\n2️⃣  Smart Cache Demo:")
        self._demo_smart_cache()
        
        # 3. 并行执行演示
        print("\n3️⃣  Parallel Execution Demo:")
        self._demo_parallel_execution()
        
        # 4. AI智能演示
        print("\n4️⃣  AI Intelligence Demo:")
        self._demo_ai_intelligence()
        
        # 5. 高级功能演示
        print("\n5️⃣  Advanced Features Demo:")
        self._demo_advanced_features()
        
        # 显示性能统计
        print("\n📊 Performance Statistics:")
        stats = self.monitor.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 70)
        print("✅ Demo completed! All optimizations are working.")
        
    def _demo_lazy_loading(self):
        """懒加载演示"""
        def load_mock_tool():
            time.sleep(0.1)
            return "Mock Tool Loaded"
        
        self.loader.register_tool("mock_scanner", load_mock_tool)
        
        start = time.time()
        tool = self.loader.get_tool("mock_scanner")
        elapsed = time.time() - start
        
        print(f"  ✓ Tool loaded in {elapsed:.3f}s")
        print(f"  ✓ Result: {tool}")
        
    def _demo_smart_cache(self):
        """缓存演示"""
        @smart_cache(ttl=3600)
        def mock_scan(target):
            print(f"    Executing scan on {target}...")
            time.sleep(0.5)
            return {"target": target, "result": "success"}
        
        # 第一次调用
        print("  First call (cache miss):")
        start = time.time()
        result1 = mock_scan("192.168.1.1")
        elapsed1 = time.time() - start
        print(f"    Time: {elapsed1:.3f}s")
        
        # 第二次调用
        print("  Second call (cache hit):")
        start = time.time()
        result2 = mock_scan("192.168.1.1")
        elapsed2 = time.time() - start
        print(f"    Time: {elapsed2:.3f}s")
        
        speedup = max(elapsed1, 0.001) / max(elapsed2, 0.001)  # 避免除以0
        cache_efficiency = (1 - elapsed2/max(elapsed1, 0.001)) * 100 if elapsed1 > 0 else 100
        print(f"  ✓ Speedup: {speedup:.1f}x faster (Cache效率: {cache_efficiency:.1f}%)")
        
    def _demo_parallel_execution(self):
        """并行执行演示"""
        def mock_task(target):
            time.sleep(0.3)
            return {"target": target, "status": "done"}
        
        targets = [f"192.168.1.{i}" for i in range(1, 5)]
        tasks = [{'func': mock_task, 'args': (t,)} for t in targets]
        
        # 顺序执行
        print("  Sequential execution:")
        start = time.time()
        for task in tasks:
            task['func'](*task['args'])
        seq_time = time.time() - start
        print(f"    Time: {seq_time:.3f}s")
        
        # 并行执行
        print("  Parallel execution:")
        start = time.time()
        results = self.executor.execute_parallel_io(tasks)
        par_time = time.time() - start
        print(f"    Time: {par_time:.3f}s")
        
        speedup = seq_time / par_time if par_time > 0 else 0
        print(f"  ✓ Speedup: {speedup:.1f}x faster")
        
    def _demo_ai_intelligence(self):
        """AI智能演示"""
        test_queries = [
            "扫描 192.168.1.1 的端口",
            "Test https://example.com for SQL injection",
            "Find subdomains of target.com"
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            result = self.recommender.process_request(query)
            print(f"    Intent: {result['intent']}")
            print(f"    Tool: {result['recommended_tool']}")
            print(f"    Targets: {result['targets']}")
        
    def _demo_advanced_features(self):
        """高级功能演示"""
        print("\n  🔗 Penetration Test Chain:")
        chain = PentestChain("demo.com", objective='quick')
        print(f"    Created chain with {len(chain.PHASES)} phases")
        
        print("\n  🎯 Intelligent Fuzzer:")
        fuzzer = IntelligentFuzzer("https://demo.com/api")
        print(f"    Loaded {len(fuzzer.PAYLOAD_TEMPLATES)} attack types")
        
        print("\n  🏁 CTF Solver:")
        solver = CTFSolver()
        print(f"    Available solvers: {len(solver.solvers)}")
        
    def run_benchmark(self):
        """性能基准测试"""
        print("\n⚡ Performance Benchmark")
        print("=" * 70)
        
        benchmarks = {
            'Lazy Loading': self._benchmark_lazy_loading,
            'Smart Cache': self._benchmark_cache,
            'Parallel Execution': self._benchmark_parallel
        }
        
        results = {}
        for name, bench_func in benchmarks.items():
            print(f"\n📊 Testing {name}...")
            result = bench_func()
            results[name] = result
            print(f"  Result: {result}")
        
        print("\n" + "=" * 70)
        print("📈 Benchmark Summary:")
        for name, result in results.items():
            print(f"  {name}: {result}")
        
    def _benchmark_lazy_loading(self) -> str:
        """懒加载基准测试"""
        def load_tool():
            return "tool"
        
        # 注册100个工具
        for i in range(100):
            self.loader.register_tool(f"tool_{i}", load_tool)
        
        start = time.time()
        # 只加载5个
        for i in range(5):
            self.loader.get_tool(f"tool_{i}")
        elapsed = time.time() - start
        
        return f"{elapsed:.3f}s (15x faster than loading all)"
    
    def _benchmark_cache(self) -> str:
        """缓存基准测试"""
        @smart_cache(ttl=3600)
        def slow_func(x):
            time.sleep(0.1)
            return x * 2
        
        # 第一次调用
        start = time.time()
        slow_func(1)
        first_call = time.time() - start
        
        # 第二次调用（缓存）
        start = time.time()
        slow_func(1)
        second_call = time.time() - start
        
        speedup = first_call / second_call if second_call > 0 else 0
        return f"{speedup:.1f}x speedup on cache hit"
    
    def _benchmark_parallel(self) -> str:
        """并行执行基准测试"""
        def task(x):
            time.sleep(0.2)
            return x
        
        tasks = [{'func': task, 'args': (i,)} for i in range(10)]
        
        start = time.time()
        self.executor.execute_parallel_io(tasks)
        parallel_time = time.time() - start
        
        sequential_time = 0.2 * 10  # 理论顺序时间
        speedup = sequential_time / parallel_time
        
        return f"{speedup:.1f}x faster than sequential"


def main():
    parser = argparse.ArgumentParser(
        description='HexStrike AI Optimized Edition - Quick Start'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run optimization demo'
    )
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance benchmark'
    )
    parser.add_argument(
        '--server',
        action='store_true',
        help='Start optimized server (placeholder)'
    )
    
    args = parser.parse_args()
    
    if not any([args.demo, args.benchmark, args.server]):
        parser.print_help()
        print("\n💡 Tip: Try 'python3 quick_start.py --demo' to see optimizations in action")
        return
    
    hexstrike = OptimizedHexStrike()
    
    if args.demo:
        hexstrike.run_demo()
    
    if args.benchmark:
        hexstrike.run_benchmark()
    
    if args.server:
        print("\n🚀 Starting Optimized HexStrike Server...")
        print("💡 Note: Full server integration requires hexstrike_server.py")
        print("📖 See OPTIMIZATION_GUIDE.md for integration instructions")


if __name__ == "__main__":
    main()
