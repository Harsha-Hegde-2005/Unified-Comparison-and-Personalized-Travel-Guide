"""
performance_metrics.py
======================
Performance monitoring, latency logging, caching, and parallel tool execution
for the Bengaluru Travel Assistant chatbot.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable, Tuple


class SimpleCache:
    def __init__(self, default_ttl_seconds: float = 300.0):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl = default_ttl_seconds
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                timestamp, val = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    self.hits += 1
                    return val
                else:
                    del self._cache[key]
            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        with self._lock:
            exp = ttl if ttl is not None else self._ttl
            self._cache[key] = (time.time(), value)

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return round((self.hits / total) * 100.0, 1)


class PerformanceMetricsTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PerformanceMetricsTracker, cls).__new__(cls)
                cls._instance._latencies: List[float] = []
                cls._instance._tool_latencies: Dict[str, List[float]] = {}
                cls._instance._query_count = 0
                cls._instance.cache = SimpleCache()
            return cls._instance

    def record_query(self, total_latency_ms: float, tool_timings: Optional[Dict[str, float]] = None):
        with self._lock:
            self._query_count += 1
            self._latencies.append(total_latency_ms)

            # Retain last 500 query latencies
            if len(self._latencies) > 500:
                self._latencies.pop(0)

            if tool_timings:
                for tname, dur in tool_timings.items():
                    if tname not in self._tool_latencies:
                        self._tool_latencies[tname] = []
                    self._tool_latencies[tname].append(dur)
                    if len(self._tool_latencies[tname]) > 500:
                        self._tool_latencies[tname].pop(0)

    def get_metrics_summary(self) -> Dict[str, Any]:
        with self._lock:
            if not self._latencies:
                return {
                    "total_queries": 0,
                    "median_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "cache_hit_rate_pct": self.cache.hit_rate(),
                }

            sorted_lat = sorted(self._latencies)
            n = len(sorted_lat)
            med = sorted_lat[n // 2]
            p95_idx = int(n * 0.95)
            p95 = sorted_lat[min(p95_idx, n - 1)]

            tool_stats = {}
            for tname, vals in self._tool_latencies.items():
                if vals:
                    tool_stats[tname] = round(sum(vals) / len(vals), 2)

            return {
                "total_queries": self._query_count,
                "median_latency_ms": round(med, 2),
                "p95_latency_ms": round(p95, 2),
                "cache_hit_rate_pct": self.cache.hit_rate(),
                "avg_tool_latencies_ms": tool_stats
            }


def run_tools_in_parallel(tool_calls: List[Tuple[str, Callable, Tuple, Dict]]) -> Dict[str, Any]:
    """
    Execute multiple independent tool functions in parallel using ThreadPoolExecutor.
    tool_calls: List of (tool_name, func, args, kwargs)
    Returns dict of {tool_name: result}
    """
    from concurrent.futures import ThreadPoolExecutor

    results = {}
    if not tool_calls:
        return results

    def _exec(call_tuple):
        name, fn, args, kwargs = call_tuple
        st = time.time()
        res = fn(*args, **kwargs)
        dur = (time.time() - st) * 1000.0
        return name, res, dur

    with ThreadPoolExecutor(max_workers=min(len(tool_calls), 6)) as executor:
        futures = [executor.submit(_exec, call) for call in tool_calls]
        for fut in futures:
            try:
                name, res, dur = fut.result(timeout=4.0)
                results[name] = res
            except Exception as e:
                pass
    return results
