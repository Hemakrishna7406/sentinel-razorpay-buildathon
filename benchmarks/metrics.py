import time
import math
from typing import List, Dict, Any

class MetricsCollector:
    def __init__(self):
        self.latencies = []
        self.errors = 0
        self.success = 0
        self.start_time = None
        self.end_time = None
        
    def start(self):
        self.start_time = time.perf_counter()
        
    def stop(self):
        self.end_time = time.perf_counter()
        
    def record(self, latency_ms: float, is_error: bool = False):
        self.latencies.append(latency_ms)
        if is_error:
            self.errors += 1
        else:
            self.success += 1
            
    def compute(self) -> Dict[str, Any]:
        if not self.latencies:
            return {}
            
        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)
        
        def p(pct):
            idx = int(math.ceil(pct / 100.0 * n)) - 1
            idx = max(0, min(idx, n - 1))
            return sorted_lat[idx]
            
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        rps = (self.success + self.errors) / total_time if total_time > 0 else 0
            
        return {
            "total_requests": n,
            "success": self.success,
            "errors": self.errors,
            "rps": round(rps, 2),
            "p50_ms": round(p(50), 2),
            "p95_ms": round(p(95), 2),
            "p99_ms": round(p(99), 2),
            "min_ms": round(sorted_lat[0], 2),
            "max_ms": round(sorted_lat[-1], 2),
            "total_duration_sec": round(total_time, 2)
        }

    def print_summary(self, name: str):
        stats = self.compute()
        print(f"--- {name} ---")
        for k, v in stats.items():
            print(f"{k.ljust(20)}: {v}")
        print()
