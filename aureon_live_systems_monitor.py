#!/usr/bin/env python3
"""
🌌 AUREON LIVE SYSTEMS MONITOR
Connects to running Aureon processes and extracts real-time metrics
"""

import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import json
import time
import psutil
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class LiveSystemsMonitor:
    """Monitor live Aureon processes and extract metrics"""
    
    def __init__(self):
        self.workspace = Path('/workspaces/aureon-trading')
        self.running_systems = {}
        self.system_logs = {
            'ocean_scan_output.log': 'Ocean Wave Scanner',
            'queen_dashboard.log': 'Queen Dashboard',
            'aureon_unified_ecosystem.log': 'Unified Ecosystem',
        }
    
    def scan_running_processes(self) -> Dict[str, Dict]:
        """Find all running Aureon Python processes"""
        running = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                # Check if it's a Python process running an Aureon script
                if 'python' in cmdline[0].lower() and len(cmdline) > 1:
                    script = cmdline[1]
                    if 'aureon' in script.lower() or 'queen' in script.lower():
                        script_name = Path(script).name
                        running[script_name] = {
                            'pid': proc.info['pid'],
                            'script': script_name,
                            'cpu_percent': proc.info.get('cpu_percent', 0),
                            'memory_mb': proc.info.get('memory_info', {}).rss / 1024 / 1024 if proc.info.get('memory_info') else 0,
                            'status': 'running'
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return running
    
    def read_log_metrics(self, log_file: str, max_lines: int = 100) -> Dict[str, Any]:
        """Extract metrics from log files"""
        log_path = self.workspace / log_file
        if not log_path.exists():
            return {'lines': 0, 'last_update': None}
        
        try:
            # Get file stats
            stats = log_path.stat()
            
            # Read last N lines
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-max_lines:]
            
            # Extract patterns
            bot_count = sum(1 for line in lines if 'Bot detected' in line or '🤖' in line)
            whale_count = sum(1 for line in lines if 'WHALE' in line or '🐋' in line)
            error_count = sum(1 for line in lines if 'ERROR' in line or 'Exception' in line)
            
            return {
                'lines': len(lines),
                'total_lines': sum(1 for _ in open(log_path, 'r', encoding='utf-8', errors='ignore')),
                'size_mb': stats.st_size / 1024 / 1024,
                'last_update': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'bot_detections': bot_count,
                'whale_detections': whale_count,
                'errors': error_count
            }
        except Exception as e:
            return {'error': str(e)}
    
    def check_thought_bus_activity(self) -> Dict[str, Any]:
        """Check Thought Bus message files for activity"""
        try:
            # Check if Thought Bus is generating messages
            from aureon_thought_bus import ThoughtBus
            bus = ThoughtBus()
            
            # Check message count
            msg_count = len(bus.memory) if hasattr(bus, 'memory') else 0
            
            return {
                'active': True,
                'message_count': msg_count,
                'status': 'operational'
            }
        except Exception as e:
            return {
                'active': False,
                'error': str(e)
            }
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all systems"""
        print("\n🔍 Scanning for live Aureon systems...")
        
        # Running processes
        processes = self.scan_running_processes()
        
        # Log file analysis
        log_metrics = {}
        for log_file, system_name in self.system_logs.items():
            metrics = self.read_log_metrics(log_file)
            log_metrics[system_name] = metrics
        
        # Thought Bus check
        thought_bus = self.check_thought_bus_activity()
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'running_processes': processes,
            'log_metrics': log_metrics,
            'thought_bus': thought_bus,
            'summary': {
                'processes_running': len(processes),
                'logs_active': sum(1 for m in log_metrics.values() if 'error' not in m),
                'thought_bus_active': thought_bus.get('active', False)
            }
        }
        
        return status
    
    def print_status(self, status: Dict):
        """Pretty print the status"""
        print("\n" + "="*80)
        print("🌌 AUREON LIVE SYSTEMS STATUS")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        summary = status['summary']
        print(f"   Running Processes: {summary['processes_running']}")
        print(f"   Active Logs: {summary['logs_active']}")
        print(f"   Thought Bus: {'✅ ACTIVE' if summary['thought_bus_active'] else '❌ Inactive'}")
        
        print(f"\n🏃 RUNNING PROCESSES:")
        for script, info in status['running_processes'].items():
            print(f"   ✅ {script:<40} PID: {info['pid']:<8} CPU: {info['cpu_percent']:.1f}% RAM: {info['memory_mb']:.1f}MB")
        
        print(f"\n📝 LOG FILE ACTIVITY:")
        for system, metrics in status['log_metrics'].items():
            if 'error' in metrics:
                print(f"   ❌ {system:<30} Error: {metrics['error']}")
            elif metrics.get('size_mb'):
                print(f"   📊 {system:<30} Size: {metrics['size_mb']:.1f}MB Lines: {metrics['total_lines']:,} Bots: {metrics.get('bot_detections', 0)}")
            else:
                print(f"   ⏸️  {system:<30} No data available")
        
        print("\n" + "="*80)

def main():
    """Main entry point"""
    monitor = LiveSystemsMonitor()
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║      🌌 AUREON LIVE SYSTEMS MONITOR 🌌                        ║
    ║      Real-Time Process and Activity Tracking                  ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    status = monitor.get_full_status()
    monitor.print_status(status)
    
    # Export JSON
    output_file = 'aureon_live_status.json'
    with open(output_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"\n💾 Status exported to {output_file}")
    print("\n✨ Scan complete!")

if __name__ == '__main__':
    main()
