"""
Execution module for HexStrike AI
Handles parallel scanning and task execution
"""

# Import from the parallel_scanner module in this directory
from .parallel_scanner import ParallelScanner, ScanTask
from .error_handler import *

# Import execute_command functions from the parent execution.py file
import sys
import os
# Add parent directory to path to import from core.execution module (the file, not this package)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import from the execution.py file in core directory
try:
    from core.execution import execute_command, execute_command_with_recovery
except ImportError:
    # Fallback: try direct import from execution module
    import importlib.util
    execution_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'execution.py')
    spec = importlib.util.spec_from_file_location("execution_module", execution_file)
    execution_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(execution_module)
    execute_command = execution_module.execute_command
    execute_command_with_recovery = execution_module.execute_command_with_recovery

__all__ = ['ParallelScanner', 'ScanTask', 'execute_command', 'execute_command_with_recovery']
