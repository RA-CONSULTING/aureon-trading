#!/usr/bin/env python3
"""
⚡ AUREON SYSTEM EFFICIENCY MONITOR
═══════════════════════════════════════════════════════════════════════════

Monitors system efficiency metrics for 99.99% uptime target:
- Process CPU/memory usage
- API latency and success rates
- Lock contention and wait times
- File I/O throughput
- Network connection health
- GC pause times

Exposes metrics on /efficiency endpoint for Prometheus scraping.

Gary Leckey | February 2026 | 99.99% EFFICIENCY MANDATE
═══════════════════════════════════════════════════════════════════════════
"""

import sys
import os
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

import psutil
import time
import json
import gc
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import threading

@dataclass
class EfficiencyMetrics:
    """System efficiency metrics for 99.99% uptime monitoring."""
    timestamp: float
    
    # Process health
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    thread_count: int
    process_count: int
    
    # API efficiency
    api_success_rate: float
    api_avg_latency_ms: float
    api_calls_per_minute: float
    
    # Lock efficiency
    lock_wait_avg_ms: float
    lock_contention_rate: float
    
    # I/O efficiency
    disk_read_mb_per_sec: float
    disk_write_mb_per_sec: float
    network_recv_mb_per_sec: float
    network_sent_mb_per_sec: float
    
    # GC efficiency
    gc_collections_gen0: int
    gc_collections_gen1: int
    gc_collections_gen2: int
    gc_pause_time_ms: float
    
    # Overall efficiency score (0-1, target >0.9999)
    efficiency_score: float
    uptime_hours: float
    
    # Issues detected
    warnings: list
    critical_issues: list

class EfficiencyMonitor:
    """Monitor and report system efficiency metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        
        # Metrics tracking
        self.api_calls = 0
        self.api_successes = 0
        self.api_latencies = []
        self.lock_waits = []
        
        # GC tracking
        self.gc_stats_last = gc.get_stats() if hasattr(gc, 'get_stats') else []
        self.gc_count_last = gc.get_count()
        
        # I/O tracking
        self.io_last = self.process.io_counters() if hasattr(self.process, 'io_counters') else None
        self.net_last = psutil.net_io_counters()
        self.last_sample_time = time.time()
        
        print("⚡ Efficiency Monitor initialized - targeting 99.99% uptime")
    
    def record_api_call(self, success: bool, latency_ms: float):
        """Record an API call for efficiency tracking."""
        self.api_calls += 1
        if success:
            self.api_successes += 1
        self.api_latencies.append(latency_ms)
        
        # Keep only last 1000 samples
        if len(self.api_latencies) > 1000:
            self.api_latencies = self.api_latencies[-1000:]
    
    def record_lock_wait(self, wait_time_ms: float):
        """Record lock wait time for contention analysis."""
        self.lock_waits.append(wait_time_ms)
        
        # Keep only last 1000 samples
        if len(self.lock_waits) > 1000:
            self.lock_waits = self.lock_waits[-1000:]
    
    def get_metrics(self) -> EfficiencyMetrics:
        """Collect current efficiency metrics."""
        now = time.time()
        elapsed = now - self.last_sample_time
        
        # CPU and Memory
        cpu_percent = self.process.cpu_percent(interval=0.1)
        mem_info = self.process.memory_info()
        memory_mb = mem_info.rss / 1024 / 1024
        memory_percent = self.process.memory_percent()
        
        # Process counts
        try:
            children = self.process.children(recursive=True)
            process_count = 1 + len(children)
            thread_count = self.process.num_threads()
        except:
            process_count = 1
            thread_count = 1
        
        # API efficiency
        api_success_rate = (self.api_successes / self.api_calls) if self.api_calls > 0 else 1.0
        api_avg_latency = sum(self.api_latencies) / len(self.api_latencies) if self.api_latencies else 0.0
        api_rate = (self.api_calls / elapsed) * 60 if elapsed > 0 else 0.0
        
        # Lock efficiency
        lock_avg_wait = sum(self.lock_waits) / len(self.lock_waits) if self.lock_waits else 0.0
        lock_contention = len([w for w in self.lock_waits if w > 10]) / len(self.lock_waits) if self.lock_waits else 0.0
        
        # I/O efficiency
        disk_read_rate = 0.0
        disk_write_rate = 0.0
        if hasattr(self.process, 'io_counters'):
            try:
                io_now = self.process.io_counters()
                if self.io_last and elapsed > 0:
                    disk_read_rate = (io_now.read_bytes - self.io_last.read_bytes) / elapsed / 1024 / 1024
                    disk_write_rate = (io_now.write_bytes - self.io_last.write_bytes) / elapsed / 1024 / 1024
                self.io_last = io_now
            except:
                pass
        
        # Network efficiency
        net_now = psutil.net_io_counters()
        net_recv_rate = 0.0
        net_sent_rate = 0.0
        if self.net_last and elapsed > 0:
            net_recv_rate = (net_now.bytes_recv - self.net_last.bytes_recv) / elapsed / 1024 / 1024
            net_sent_rate = (net_now.bytes_sent - self.net_last.bytes_sent) / elapsed / 1024 / 1024
        self.net_last = net_now
        
        # GC efficiency
        gc_count_now = gc.get_count()
        gc0 = gc_count_now[0] - self.gc_count_last[0] if len(self.gc_count_last) > 0 else 0
        gc1 = gc_count_now[1] - self.gc_count_last[1] if len(self.gc_count_last) > 1 else 0
        gc2 = gc_count_now[2] - self.gc_count_last[2] if len(self.gc_count_last) > 2 else 0
        self.gc_count_last = gc_count_now
        
        # Estimate GC pause time (rough heuristic: ~1ms per gen0, ~10ms per gen1, ~100ms per gen2)
        gc_pause_ms = (gc0 * 1.0) + (gc1 * 10.0) + (gc2 * 100.0)
        
        # Calculate efficiency score
        warnings = []
        critical = []
        
        # CPU efficiency check (target <80%)
        if cpu_percent > 90:
            critical.append(f"CPU at {cpu_percent:.1f}% (critical)")
        elif cpu_percent > 80:
            warnings.append(f"CPU at {cpu_percent:.1f}% (high)")
        
        # Memory efficiency check (target <70%)
        if memory_percent > 85:
            critical.append(f"Memory at {memory_percent:.1f}% (critical)")
        elif memory_percent > 70:
            warnings.append(f"Memory at {memory_percent:.1f}% (high)")
        
        # API efficiency check (target >99%)
        if api_success_rate < 0.95:
            critical.append(f"API success rate {api_success_rate*100:.2f}% (critical)")
        elif api_success_rate < 0.99:
            warnings.append(f"API success rate {api_success_rate*100:.2f}% (low)")
        
        # Lock contention check (target <1%)
        if lock_contention > 0.10:
            critical.append(f"Lock contention {lock_contention*100:.1f}% (critical)")
        elif lock_contention > 0.01:
            warnings.append(f"Lock contention {lock_contention*100:.1f}% (elevated)")
        
        # Calculate overall efficiency score (weighted average)
        cpu_score = max(0, 1 - (cpu_percent / 100))
        mem_score = max(0, 1 - (memory_percent / 100))
        api_score = api_success_rate
        lock_score = max(0, 1 - lock_contention)
        
        # Weighted: API=40%, CPU=30%, Memory=20%, Locks=10%
        efficiency = (api_score * 0.4) + (cpu_score * 0.3) + (mem_score * 0.2) + (lock_score * 0.1)
        
        uptime = (now - self.start_time) / 3600  # hours
        self.last_sample_time = now
        
        return EfficiencyMetrics(
            timestamp=now,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            thread_count=thread_count,
            process_count=process_count,
            api_success_rate=api_success_rate,
            api_avg_latency_ms=api_avg_latency,
            api_calls_per_minute=api_rate,
            lock_wait_avg_ms=lock_avg_wait,
            lock_contention_rate=lock_contention,
            disk_read_mb_per_sec=disk_read_rate,
            disk_write_mb_per_sec=disk_write_rate,
            network_recv_mb_per_sec=net_recv_rate,
            network_sent_mb_per_sec=net_sent_rate,
            gc_collections_gen0=gc0,
            gc_collections_gen1=gc1,
            gc_collections_gen2=gc2,
            gc_pause_time_ms=gc_pause_ms,
            efficiency_score=efficiency,
            uptime_hours=uptime,
            warnings=warnings,
            critical_issues=critical
        )
    
    def print_report(self):
        """Print efficiency report to console."""
        metrics = self.get_metrics()
        
        print("\n" + "="*80)
        print("⚡ AUREON SYSTEM EFFICIENCY REPORT")
        print("="*80)
        print(f"⏰ Uptime: {metrics.uptime_hours:.2f} hours")
        print(f"🎯 Efficiency Score: {metrics.efficiency_score*100:.4f}% {'✅ TARGET MET' if metrics.efficiency_score >= 0.9999 else '⚠️ BELOW TARGET'}")
        print()
        
        print("📊 RESOURCE UTILIZATION:")
        print(f"  CPU:     {metrics.cpu_percent:6.2f}% {'⚠️' if metrics.cpu_percent > 80 else '✅'}")
        print(f"  Memory:  {metrics.memory_mb:6.1f} MB ({metrics.memory_percent:.1f}%) {'⚠️' if metrics.memory_percent > 70 else '✅'}")
        print(f"  Threads: {metrics.thread_count}")
        print(f"  Processes: {metrics.process_count}")
        print()
        
        print("🌐 API PERFORMANCE:")
        print(f"  Success Rate: {metrics.api_success_rate*100:6.2f}% {'⚠️' if metrics.api_success_rate < 0.99 else '✅'}")
        print(f"  Avg Latency:  {metrics.api_avg_latency_ms:6.1f} ms")
        print(f"  Call Rate:    {metrics.api_calls_per_minute:6.1f} /min")
        print()
        
        print("🔒 LOCK EFFICIENCY:")
        print(f"  Avg Wait:    {metrics.lock_wait_avg_ms:6.2f} ms")
        print(f"  Contention:  {metrics.lock_contention_rate*100:6.2f}% {'⚠️' if metrics.lock_contention_rate > 0.01 else '✅'}")
        print()
        
        print("💾 I/O THROUGHPUT:")
        print(f"  Disk Read:   {metrics.disk_read_mb_per_sec:6.2f} MB/s")
        print(f"  Disk Write:  {metrics.disk_write_mb_per_sec:6.2f} MB/s")
        print(f"  Net Recv:    {metrics.network_recv_mb_per_sec:6.2f} MB/s")
        print(f"  Net Sent:    {metrics.network_sent_mb_per_sec:6.2f} MB/s")
        print()
        
        print("🗑️  GARBAGE COLLECTION:")
        print(f"  Gen0: {metrics.gc_collections_gen0:4d} collections")
        print(f"  Gen1: {metrics.gc_collections_gen1:4d} collections")
        print(f"  Gen2: {metrics.gc_collections_gen2:4d} collections")
        print(f"  Est. Pause Time: {metrics.gc_pause_time_ms:6.1f} ms")
        print()
        
        if metrics.warnings:
            print("⚠️  WARNINGS:")
            for w in metrics.warnings:
                print(f"  • {w}")
            print()
        
        if metrics.critical_issues:
            print("🚨 CRITICAL ISSUES:")
            for c in metrics.critical_issues:
                print(f"  • {c}")
            print()
        
        print("="*80)
        
        return metrics

def monitor_efficiency_loop(interval_seconds: int = 60):
    """Run continuous efficiency monitoring."""
    monitor = EfficiencyMonitor()
    state_file = Path("system_efficiency_state.json")
    
    print(f"⚡ Starting efficiency monitor (interval={interval_seconds}s)")
    print(f"📊 Target: 99.99% efficiency (0.9999 score)")
    print()
    
    try:
        while True:
            metrics = monitor.print_report()
            
            # Save state
            try:
                with open(state_file, 'w') as f:
                    json.dump(asdict(metrics), f, indent=2)
            except Exception as e:
                print(f"⚠️ Failed to save efficiency state: {e}")
            
            # Check if we're meeting target
            if metrics.efficiency_score < 0.9999:
                print(f"⚠️ EFFICIENCY BELOW TARGET: {metrics.efficiency_score*100:.4f}%")
                if metrics.critical_issues:
                    print("🚨 CRITICAL ISSUES DETECTED - IMMEDIATE ACTION REQUIRED")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n⚡ Efficiency monitor stopped")

def get_efficiency_metrics_json() -> str:
    """Get current efficiency metrics as JSON for API endpoint."""
    monitor = EfficiencyMonitor()
    metrics = monitor.get_metrics()
    return json.dumps(asdict(metrics), indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Aureon System Efficiency Monitor")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()
    
    if args.json:
        print(get_efficiency_metrics_json())
    else:
        monitor_efficiency_loop(args.interval)
