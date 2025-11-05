"""
Cache module for HexStrike AI
Handles scan caching and result storage
"""

# Import from scan_cache in this directory
from .scan_cache import cache_executor

# Import HexStrikeCache from parent cache.py file
import sys
import os
import importlib.util

# Load HexStrikeCache from the cache.py file in core directory
cache_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache.py')
spec = importlib.util.spec_from_file_location("cache_module", cache_file)
cache_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_module)
HexStrikeCache = cache_module.HexStrikeCache

__all__ = ['cache_executor', 'HexStrikeCache']
