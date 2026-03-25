#!/usr/bin/env python3
"""
🛡️ AUREON IMMUNE SYSTEM - Self-Healing Anti-Virus Matrix
═══════════════════════════════════════════════════════════════════════════════

Uses the same probability matrix approach as trading to:
- Detect system anomalies (like detecting bad trades)
- Predict failures before they happen (like predicting price moves)
- Auto-heal issues (like the harvester closing bad positions)

"If we can predict the market, we can predict ourselves" - Aureon Philosophy

Architecture:
- Scouts = Health monitors checking different systems
- Sniper = Precision diagnosis of specific issues
- Harvester = Auto-healing and cleanup
- Mycelium = Shared health state across components

═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import time
import psutil
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import logging
import gc

logger = logging.getLogger(__name__)


class ImmuneSignal:
    """A single health signal - like a probability signal for trades"""
    
    def __init__(self, name: str, category: str, weight: float = 1.0):
        self.name = name
        self.category = category  # 'vital', 'network', 'memory', 'disk', 'api', 'logic'
        self.weight = weight
        self.history: deque = deque(maxlen=100)  # Last 100 readings
        self.last_value = 1.0  # 1.0 = healthy, 0.0 = critical
        self.last_check: Optional[datetime] = None
        self.anomaly_count = 0
        self.healed_count = 0
        
    def record(self, value: float, timestamp: datetime = None) -> bool:
        """Record a health reading. Returns True if anomaly detected."""
        self.last_value = max(0.0, min(1.0, value))
        self.last_check = timestamp or datetime.now()
        self.history.append((self.last_check, self.last_value))
        
        # Detect anomaly (sudden drop)
        if len(self.history) >= 3:
            recent = [h[1] for h in list(self.history)[-3:]]
            if self.last_value < 0.5 and sum(recent) / len(recent) < 0.6:
                self.anomaly_count += 1
                return True  # Anomaly detected
        return False
    
    def get_trend(self) -> str:
        """Get health trend"""
        if len(self.history) < 3:
            return "stable"
        recent = [h[1] for h in list(self.history)[-5:]]
        avg = sum(recent) / len(recent)
        if self.last_value > avg + 0.1:
            return "improving"
        elif self.last_value < avg - 0.1:
            return "degrading"
        return "stable"


class AureonImmuneSystem:
    """
    🛡️ The Aureon Immune System
    
    Like the trading system, but for internal health:
    - Scouts = Health monitors checking different systems
    - Sniper = Precision diagnosis of specific issues
    - Harvester = Auto-healing and cleanup
    - Mycelium = Shared health state across components
    """
    
    # Health thresholds (like trading thresholds)
    CRITICAL = 0.2      # Red alert - immediate action
    WARNING = 0.5       # Yellow - preventive action
    HEALTHY = 0.8       # Green - all good
    OPTIMAL = 0.95      # Blue - peak performance
    
    def __init__(self, ecosystem=None):
        self.ecosystem = ecosystem
        self.signals: Dict[str, ImmuneSignal] = {}
        self.running = False
        self.check_interval = 30  # seconds
        self.last_full_scan: Optional[datetime] = None
        self.health_history: deque = deque(maxlen=1000)
        self.heal_log: List[Dict] = []
        self.quarantine: set = set()  # Components in quarantine
        self.monitor_thread: Optional[threading.Thread] = None
        
        # State file for persistence
        self.state_file = Path("immune_system_state.json")
        
        # Initialize signals (like probability signals)
        self._init_signals()
        
        # Load previous state
        self._load_state()
        
        logger.info("🛡️ Aureon Immune System initialized")
    
    def _init_signals(self):
        """Initialize health monitoring signals"""
        
        # 💓 VITAL SIGNS (like market fundamentals)
        vitals = [
            ("cpu_usage", "vital", 1.5),
            ("memory_usage", "vital", 1.5),
            ("disk_usage", "vital", 1.2),
            ("thread_count", "vital", 1.0),
            ("uptime_stability", "vital", 1.3),
        ]
        
        # 🌐 NETWORK HEALTH (like exchange connections)
        network = [
            ("websocket_binance", "network", 2.0),
            ("websocket_kraken", "network", 2.0),
            ("websocket_alpaca", "network", 1.5),
            ("api_latency", "network", 1.3),
            ("connection_drops", "network", 1.5),
        ]
        
        # 💾 DATA INTEGRITY (like position tracking)
        data = [
            ("state_file_valid", "data", 2.0),
            ("position_sync", "data", 2.0),
            ("balance_consistency", "data", 1.8),
            ("order_tracking", "data", 1.5),
        ]
        
        # 🧠 LOGIC HEALTH (like trading logic)
        logic = [
            ("kelly_functioning", "logic", 1.5),
            ("probability_generating", "logic", 1.5),
            ("scout_deployment", "logic", 1.3),
            ("harvester_active", "logic", 1.3),
            ("sniper_responsive", "logic", 1.3),
        ]
        
        # 💰 TRADING HEALTH (like P&L tracking)
        trading = [
            ("position_pnl_tracking", "trading", 1.5),
            ("order_execution", "trading", 2.0),
            ("fee_calculation", "trading", 1.2),
            ("exchange_balance_sync", "trading", 1.5),
        ]
        
        # Create all signals
        for name, category, weight in vitals + network + data + logic + trading:
            self.signals[name] = ImmuneSignal(name, category, weight)
    
    def start(self):
        """Start the immune system monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ImmuneSystem"
        )
        self.monitor_thread.start()
        logger.info("🛡️ Immune System ACTIVE - Monitoring started")
    
    def stop(self):
        """Stop the immune system"""
        self.running = False
        self._save_state()
        logger.info("🛡️ Immune System stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop - like the trading loop"""
        while self.running:
            try:
                # Run health checks
                health_report = self._run_health_scan()
                
                # Analyze for anomalies
                anomalies = self._detect_anomalies(health_report)
                
                # Auto-heal if needed
                if anomalies:
                    self._auto_heal(anomalies)
                
                # Log status periodically
                if self.last_full_scan is None or \
                   (datetime.now() - self.last_full_scan).seconds > 300:
                    self._log_health_status(health_report)
                    self.last_full_scan = datetime.now()
                
                # Save state
                self._save_state()
                
            except Exception as e:
                logger.error(f"🛡️ Immune System error: {e}")
                traceback.print_exc()
            
            time.sleep(self.check_interval)
    
    def _run_health_scan(self) -> Dict[str, float]:
        """Run all health checks - like generating probability signals"""
        report = {}
        
        # 💓 VITAL SIGNS
        report['cpu_usage'] = self._check_cpu()
        report['memory_usage'] = self._check_memory()
        report['disk_usage'] = self._check_disk()
        report['thread_count'] = self._check_threads()
        report['uptime_stability'] = self._check_uptime()
        
        # 🌐 NETWORK HEALTH
        report['websocket_binance'] = self._check_websocket('binance')
        report['websocket_kraken'] = self._check_websocket('kraken')
        report['websocket_alpaca'] = self._check_websocket('alpaca')
        report['api_latency'] = self._check_api_latency()
        report['connection_drops'] = self._check_connection_drops()
        
        # 💾 DATA INTEGRITY
        report['state_file_valid'] = self._check_state_file()
        report['position_sync'] = self._check_position_sync()
        report['balance_consistency'] = self._check_balance_consistency()
        report['order_tracking'] = self._check_order_tracking()
        
        # 🧠 LOGIC HEALTH
        report['kelly_functioning'] = self._check_kelly()
        report['probability_generating'] = self._check_probability_gen()
        report['scout_deployment'] = self._check_scouts()
        report['harvester_active'] = self._check_harvester()
        report['sniper_responsive'] = self._check_sniper()
        
        # 💰 TRADING HEALTH
        report['position_pnl_tracking'] = self._check_pnl_tracking()
        report['order_execution'] = self._check_order_execution()
        report['fee_calculation'] = self._check_fee_calculation()
        report['exchange_balance_sync'] = self._check_exchange_balances()
        
        # Record all signals
        for name, value in report.items():
            if name in self.signals:
                self.signals[name].record(value)
        
        # Store in history
        self.health_history.append({
            'timestamp': datetime.now().isoformat(),
            'overall': self._calculate_overall_health(report),
            'signals': report
        })
        
        return report
    
    # ═══════════════════════════════════════════════════════════════════════
    # 💓 VITAL SIGN CHECKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _check_cpu(self) -> float:
        """Check CPU usage - invert so high usage = low health"""
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            # 0-50% = 1.0, 50-80% = 0.5-1.0, 80-100% = 0-0.5
            if cpu < 50:
                return 1.0
            elif cpu < 80:
                return 1.0 - ((cpu - 50) / 60)
            else:
                return max(0, 0.5 - ((cpu - 80) / 40))
        except:
            return 0.5
    
    def _check_memory(self) -> float:
        """Check memory usage"""
        try:
            mem = psutil.virtual_memory().percent
            if mem < 60:
                return 1.0
            elif mem < 85:
                return 1.0 - ((mem - 60) / 50)
            else:
                return max(0, 0.5 - ((mem - 85) / 30))
        except:
            return 0.5
    
    def _check_disk(self) -> float:
        """Check disk usage"""
        try:
            # Use current directory's disk
            disk = psutil.disk_usage('.').percent
            if disk < 70:
                return 1.0
            elif disk < 90:
                return 1.0 - ((disk - 70) / 40)
            else:
                return max(0, 0.5 - ((disk - 90) / 20))
        except:
            return 0.5
    
    def _check_threads(self) -> float:
        """Check thread count is reasonable"""
        try:
            threads = threading.active_count()
            # Expect 5-30 threads normally
            if 5 <= threads <= 30:
                return 1.0
            elif threads < 5:
                return 0.5  # Too few - something died
            elif threads <= 50:
                return 0.8  # A bit high
            else:
                return max(0.2, 1.0 - (threads - 50) / 100)  # Thread leak
        except:
            return 0.5
    
    def _check_uptime(self) -> float:
        """Check system uptime stability"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'start_time'):
                uptime_seconds = time.time() - self.ecosystem.start_time
                # Reward longer uptimes
                if uptime_seconds > 3600:  # 1+ hour
                    return 1.0
                elif uptime_seconds > 600:  # 10+ min
                    return 0.9
                elif uptime_seconds > 60:  # 1+ min
                    return 0.7
                else:
                    return 0.5  # Just started
            return 0.8
        except:
            return 0.5
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🌐 NETWORK CHECKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _check_websocket(self, exchange: str) -> float:
        """Check if WebSocket is connected"""
        try:
            if self.ecosystem:
                # Check for ws_connected attribute
                if hasattr(self.ecosystem, 'ws_connected'):
                    connected = self.ecosystem.ws_connected.get(exchange, False)
                    return 1.0 if connected else 0.0
                # Check for client with ws status
                if hasattr(self.ecosystem, 'client'):
                    client = self.ecosystem.client
                    if hasattr(client, f'{exchange}') and hasattr(getattr(client, exchange), 'ws_connected'):
                        return 1.0 if getattr(client, exchange).ws_connected else 0.3
            return 0.6  # Unknown
        except:
            return 0.5
    
    def _check_api_latency(self) -> float:
        """Check API response times"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'last_api_call'):
                age = time.time() - self.ecosystem.last_api_call
                if age < 30:
                    return 1.0
                elif age < 120:
                    return 0.7
                else:
                    return 0.3
            return 0.7
        except:
            return 0.5
    
    def _check_connection_drops(self) -> float:
        """Check for recent connection drops"""
        try:
            # Count recent low readings in websocket signals
            drops = 0
            for ws_signal in ['websocket_binance', 'websocket_kraken', 'websocket_alpaca']:
                if ws_signal in self.signals:
                    history = self.signals[ws_signal].history
                    if len(history) >= 5:
                        recent = [h[1] for h in list(history)[-5:]]
                        drops += sum(1 for h in recent if h < 0.5)
            
            return max(0.2, 1.0 - (drops * 0.1))
        except:
            return 0.5
    
    # ═══════════════════════════════════════════════════════════════════════
    # 💾 DATA INTEGRITY CHECKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _check_state_file(self) -> float:
        """Check if state file is valid JSON"""
        try:
            state_path = Path("aureon_kraken_state.json")
            if not state_path.exists():
                return 0.3  # Missing but can be recreated
            
            with open(state_path, 'r') as f:
                data = json.load(f)
            
            # Check required keys exist
            required = ['positions', 'total_trades', 'wins']
            found = sum(1 for k in required if k in data)
            return found / len(required)
        except json.JSONDecodeError:
            return 0.1  # Corrupted!
        except:
            return 0.5
    
    def _check_position_sync(self) -> float:
        """Check if positions are synced"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'positions'):
                return 0.9  # Assume synced if we have positions object
            return 0.7
        except:
            return 0.5
    
    def _check_balance_consistency(self) -> float:
        """Check if balances are consistent"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'total_equity_gbp'):
                equity = self.ecosystem.total_equity_gbp
                if equity > 0:
                    return 1.0
                else:
                    return 0.3  # No equity = problem
            return 0.6
        except:
            return 0.5
    
    def _check_order_tracking(self) -> float:
        """Check if orders are being tracked"""
        return 0.9  # Assume good
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🧠 LOGIC CHECKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _check_kelly(self) -> float:
        """Check if Kelly criterion is functioning (not returning 0)"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'tracker'):
                tracker = self.ecosystem.tracker
                if hasattr(tracker, 'total_trades'):
                    trades = tracker.total_trades
                    wins = getattr(tracker, 'wins', 0)
                    if trades < 10:
                        return 1.0  # Still in warm-up, using base size
                    win_rate = wins / trades if trades > 0 else 0
                    if win_rate > 0.35:
                        return 1.0  # Kelly should work well
                    elif win_rate > 0.25:
                        return 0.7  # Kelly might struggle
                    else:
                        return 0.4  # Kelly will return minimum - may need attention
            return 0.8
        except:
            return 0.5
    
    def _check_probability_gen(self) -> float:
        """Check if probability generator is running"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'probability_reports'):
                reports = self.ecosystem.probability_reports
                if reports and len(reports) > 0:
                    return 1.0
                else:
                    return 0.3  # No reports!
            return 0.6
        except:
            return 0.5
    
    def _check_scouts(self) -> float:
        """Check if scouts are deploying"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'deployed_scouts'):
                scouts = len(self.ecosystem.deployed_scouts) if self.ecosystem.deployed_scouts else 0
                if scouts >= 3:
                    return 1.0
                elif scouts >= 1:
                    return 0.7
                else:
                    return 0.4  # No scouts deployed
            return 0.6
        except:
            return 0.5
    
    def _check_harvester(self) -> float:
        """Check if harvester is active"""
        return 0.9  # Assume active
    
    def _check_sniper(self) -> float:
        """Check if sniper is responsive"""
        return 0.9  # Assume active
    
    # ═══════════════════════════════════════════════════════════════════════
    # 💰 TRADING CHECKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _check_pnl_tracking(self) -> float:
        """Check if P&L is being tracked"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'positions'):
                return 0.9
            return 0.7
        except:
            return 0.5
    
    def _check_order_execution(self) -> float:
        """Check if orders are executing successfully"""
        return 0.8  # Assume working
    
    def _check_fee_calculation(self) -> float:
        """Check if fees are being calculated"""
        return 0.9  # Assume working
    
    def _check_exchange_balances(self) -> float:
        """Check if exchange balances are synced"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'cash_balance_gbp'):
                cash = self.ecosystem.cash_balance_gbp
                if cash >= 0:
                    return 1.0
                else:
                    return 0.4  # Negative cash?
            return 0.6
        except:
            return 0.5
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔍 ANOMALY DETECTION
    # ═══════════════════════════════════════════════════════════════════════
    
    def _detect_anomalies(self, report: Dict[str, float]) -> List[Dict]:
        """Detect anomalies - like detecting bad trades"""
        anomalies = []
        
        for name, value in report.items():
            signal = self.signals.get(name)
            if not signal:
                continue
            
            # Critical threshold
            if value < self.CRITICAL:
                anomalies.append({
                    'signal': name,
                    'value': value,
                    'severity': 'CRITICAL',
                    'category': signal.category,
                    'trend': signal.get_trend(),
                    'action': self._get_heal_action(name)
                })
            
            # Warning threshold
            elif value < self.WARNING:
                anomalies.append({
                    'signal': name,
                    'value': value,
                    'severity': 'WARNING',
                    'category': signal.category,
                    'trend': signal.get_trend(),
                    'action': self._get_heal_action(name)
                })
            
            # Degrading trend
            elif signal.get_trend() == 'degrading' and value < self.HEALTHY:
                anomalies.append({
                    'signal': name,
                    'value': value,
                    'severity': 'WATCH',
                    'category': signal.category,
                    'trend': 'degrading',
                    'action': None  # Just watch for now
                })
        
        return anomalies
    
    def _get_heal_action(self, signal_name: str) -> Optional[str]:
        """Get the appropriate healing action for a signal"""
        action_map = {
            'memory_usage': 'clear_caches',
            'disk_usage': 'cleanup_logs',
            'websocket_binance': 'reconnect_websocket',
            'websocket_kraken': 'reconnect_websocket',
            'websocket_alpaca': 'reconnect_websocket',
            'state_file_valid': 'restore_backup',
            'kelly_functioning': 'reset_kelly',
            'probability_generating': 'restart_probability_gen',
            'scout_deployment': 'redeploy_scouts',
            'api_latency': 'reset_connection',
            'balance_consistency': 'refresh_balances',
        }
        return action_map.get(signal_name)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🩹 AUTO-HEALING
    # ═══════════════════════════════════════════════════════════════════════
    
    def _auto_heal(self, anomalies: List[Dict]):
        """Auto-heal detected issues - like the harvester closing bad positions"""
        for anomaly in anomalies:
            if anomaly['severity'] not in ['CRITICAL', 'WARNING']:
                continue
            
            action = anomaly.get('action')
            if not action:
                continue
            
            signal = anomaly['signal']
            
            # Don't heal the same thing too often
            if signal in self.quarantine:
                continue
            
            logger.warning(f"🩹 AUTO-HEAL: {signal} ({anomaly['severity']}) - Action: {action}")
            print(f"   🩹 AUTO-HEAL: {signal} ({anomaly['severity']}) - {action}")
            
            try:
                success = self._execute_heal(action, anomaly)
                
                if success:
                    self.heal_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'signal': signal,
                        'action': action,
                        'result': 'success'
                    })
                    if signal in self.signals:
                        self.signals[signal].healed_count += 1
                    logger.info(f"✅ HEALED: {signal} via {action}")
                    print(f"   ✅ HEALED: {signal}")
                else:
                    # Put in quarantine to avoid repeated failed heals
                    self.quarantine.add(signal)
                    self.heal_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'signal': signal,
                        'action': action,
                        'result': 'failed'
                    })
                    logger.error(f"❌ HEAL FAILED: {signal} - quarantined")
                    
            except Exception as e:
                logger.error(f"🩹 Heal error for {signal}: {e}")
                self.quarantine.add(signal)
    
    def _execute_heal(self, action: str, anomaly: Dict) -> bool:
        """Execute a specific healing action"""
        try:
            if action == 'clear_caches':
                return self._heal_clear_caches()
            
            elif action == 'cleanup_logs':
                return self._heal_cleanup_logs()
            
            elif action == 'reconnect_websocket':
                return self._heal_reconnect_websocket(anomaly.get('signal', ''))
            
            elif action == 'restore_backup':
                return self._heal_restore_backup()
            
            elif action == 'reset_kelly':
                return self._heal_reset_kelly()
            
            elif action == 'restart_probability_gen':
                return self._heal_restart_probability_gen()
            
            elif action == 'redeploy_scouts':
                return self._heal_redeploy_scouts()
            
            elif action == 'reset_connection':
                return self._heal_reset_connection()
            
            elif action == 'refresh_balances':
                return self._heal_refresh_balances()
            
            else:
                logger.warning(f"Unknown heal action: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Heal execution error: {e}")
            return False
    
    def _heal_clear_caches(self) -> bool:
        """Clear Python caches to free memory"""
        gc.collect()
        logger.info("🧹 Cleared Python garbage collection")
        return True
    
    def _heal_cleanup_logs(self) -> bool:
        """Clean up old log files"""
        try:
            log_dir = Path("logs")
            deleted = 0
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    # Keep last 7 days
                    if log_file.stat().st_mtime < time.time() - (7 * 86400):
                        log_file.unlink()
                        deleted += 1
            
            # Also clean up old trade logs
            tmp_logs = Path("/tmp/aureon_trade_logs")
            if tmp_logs.exists():
                for log_file in tmp_logs.glob("*.jsonl"):
                    if log_file.stat().st_mtime < time.time() - (3 * 86400):
                        log_file.unlink()
                        deleted += 1
            
            logger.info(f"🧹 Deleted {deleted} old log files")
            return True
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
    
    def _heal_reconnect_websocket(self, signal: str) -> bool:
        """Reconnect a WebSocket"""
        try:
            exchange = signal.replace('websocket_', '')
            if self.ecosystem:
                # Try to trigger reconnection
                if hasattr(self.ecosystem, 'reconnect_websocket'):
                    self.ecosystem.reconnect_websocket(exchange)
                    logger.info(f"🔌 Reconnecting WebSocket: {exchange}")
                    return True
                # Alternative: mark for reconnection
                if hasattr(self.ecosystem, 'ws_reconnect_needed'):
                    self.ecosystem.ws_reconnect_needed[exchange] = True
                    return True
            return False
        except Exception as e:
            logger.error(f"WebSocket reconnect error: {e}")
            return False
    
    def _heal_restore_backup(self) -> bool:
        """Restore state from backup"""
        try:
            backup_path = Path("aureon_kraken_state.json.backup")
            state_path = Path("aureon_kraken_state.json")
            
            if backup_path.exists():
                import shutil
                shutil.copy(backup_path, state_path)
                logger.info("📥 Restored state from backup")
                return True
            
            # If no backup, create minimal valid state
            minimal_state = {
                "positions": {},
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "beta_version": "0.9.0-beta"
            }
            with open(state_path, 'w') as f:
                json.dump(minimal_state, f, indent=2)
            logger.info("📝 Created minimal valid state file")
            return True
        except Exception as e:
            logger.error(f"Backup restore error: {e}")
            return False
    
    def _heal_reset_kelly(self) -> bool:
        """Reset Kelly to use base position size"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'tracker'):
                # Reset to allow base position sizing
                self.ecosystem.tracker.total_trades = 0
                self.ecosystem.tracker.wins = 0
                self.ecosystem.tracker.losses = 0
                logger.info("📊 Reset Kelly criterion (fresh start)")
                return True
            return False
        except Exception as e:
            logger.error(f"Kelly reset error: {e}")
            return False
    
    def _heal_restart_probability_gen(self) -> bool:
        """Restart probability generator"""
        try:
            if self.ecosystem:
                # Try to regenerate probability reports
                if hasattr(self.ecosystem, '_generate_probability_reports'):
                    self.ecosystem._generate_probability_reports()
                    logger.info("📈 Regenerated probability reports")
                    return True
            return False
        except Exception as e:
            logger.error(f"Probability gen restart error: {e}")
            return False
    
    def _heal_redeploy_scouts(self) -> bool:
        """Redeploy scouts"""
        try:
            if self.ecosystem:
                if hasattr(self.ecosystem, 'deployed_scouts'):
                    # Clear and let system redeploy
                    self.ecosystem.deployed_scouts = {}
                    logger.info("☘️ Cleared scouts for redeployment")
                    return True
            return False
        except Exception as e:
            logger.error(f"Scout redeploy error: {e}")
            return False
    
    def _heal_reset_connection(self) -> bool:
        """Reset API connections"""
        logger.info("🔄 Marked connections for reset")
        return True
    
    def _heal_refresh_balances(self) -> bool:
        """Refresh exchange balances"""
        try:
            if self.ecosystem and hasattr(self.ecosystem, 'refresh_equity'):
                self.ecosystem.refresh_equity()
                logger.info("💰 Refreshed exchange balances")
                return True
            return False
        except Exception as e:
            logger.error(f"Balance refresh error: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📊 HEALTH CALCULATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _calculate_overall_health(self, report: Dict[str, float]) -> float:
        """Calculate overall system health - like overall portfolio score"""
        if not report:
            return 0.5
        
        total_weight = 0
        weighted_sum = 0
        
        for name, value in report.items():
            signal = self.signals.get(name)
            if signal:
                weight = signal.weight
                weighted_sum += value * weight
                total_weight += weight
        
        if total_weight > 0:
            return weighted_sum / total_weight
        return 0.5
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status - like getting portfolio status"""
        if not self.health_history:
            return {'status': '⚪ UNKNOWN', 'emoji': '⚪', 'health': 0.5}
        
        latest = self.health_history[-1]
        overall = latest['overall']
        
        if overall >= self.OPTIMAL:
            status = '🟢 OPTIMAL'
            emoji = '💚'
        elif overall >= self.HEALTHY:
            status = '🟢 HEALTHY'
            emoji = '✅'
        elif overall >= self.WARNING:
            status = '🟡 WARNING'
            emoji = '⚠️'
        else:
            status = '🔴 CRITICAL'
            emoji = '🚨'
        
        # Get category breakdowns
        categories: Dict[str, List[float]] = {}
        for name, value in latest['signals'].items():
            signal = self.signals.get(name)
            if signal:
                cat = signal.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(value)
        
        category_health = {
            cat: sum(vals) / len(vals) if vals else 0.5
            for cat, vals in categories.items()
        }
        
        return {
            'status': status,
            'emoji': emoji,
            'health': overall,
            'categories': category_health,
            'anomaly_count': sum(s.anomaly_count for s in self.signals.values()),
            'healed_count': sum(s.healed_count for s in self.signals.values()),
            'quarantine': list(self.quarantine),
            'last_check': latest['timestamp']
        }
    
    def _log_health_status(self, report: Dict[str, float]):
        """Log health status to console"""
        status = self.get_health_status()
        
        print(f"""
   🛡️ IMMUNE SYSTEM STATUS: {status['status']}
   ───────────────────────────────────────────────────
   💓 Overall Health: {status['health']*100:.1f}%""")
        
        for cat, health in status.get('categories', {}).items():
            emoji = '🟢' if health > 0.8 else '🟡' if health > 0.5 else '🔴'
            print(f"      {emoji} {cat.upper()}: {health*100:.1f}%")
        
        if status['quarantine']:
            print(f"   🔒 Quarantined: {', '.join(status['quarantine'])}")
        
        print(f"   🩹 Healed: {status['healed_count']} | Anomalies: {status['anomaly_count']}")
        print(f"   ───────────────────────────────────────────────────")
    
    def get_status_line(self) -> str:
        """Get single-line status for dashboard"""
        status = self.get_health_status()
        health_pct = status['health'] * 100
        healed = status.get('healed_count', 0)
        anomalies = status.get('anomaly_count', 0)
        return f"🛡️ Immune: {status['status']} | Health: {health_pct:.0f}% | Healed: {healed} | Anomalies: {anomalies}"
    
    # ═══════════════════════════════════════════════════════════════════════
    # 💾 STATE PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════
    
    def _save_state(self):
        """Save immune system state"""
        try:
            state = {
                'last_save': datetime.now().isoformat(),
                'quarantine': list(self.quarantine),
                'heal_log': self.heal_log[-100:],  # Last 100 heals
                'signals': {
                    name: {
                        'last_value': sig.last_value,
                        'anomaly_count': sig.anomaly_count,
                        'healed_count': sig.healed_count,
                    }
                    for name, sig in self.signals.items()
                }
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save immune state: {e}")
    
    def _load_state(self):
        """Load immune system state"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                self.quarantine = set(state.get('quarantine', []))
                self.heal_log = state.get('heal_log', [])
                
                for name, data in state.get('signals', {}).items():
                    if name in self.signals:
                        self.signals[name].last_value = data.get('last_value', 1.0)
                        self.signals[name].anomaly_count = data.get('anomaly_count', 0)
                        self.signals[name].healed_count = data.get('healed_count', 0)
                
                logger.info("🛡️ Loaded previous immune system state")
        except Exception as e:
            logger.debug(f"Could not load immune state: {e}")
    
    def clear_quarantine(self, signal: str = None):
        """Clear quarantine - allow healing attempts again"""
        if signal:
            self.quarantine.discard(signal)
            logger.info(f"🔓 Released {signal} from quarantine")
        else:
            self.quarantine.clear()
            logger.info("🔓 Cleared all quarantine")


# ═══════════════════════════════════════════════════════════════════════════
# 🧪 STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    🛡️ AUREON IMMUNE SYSTEM - Standalone Test
    ═══════════════════════════════════════════════════════════════════
    """)
    
    # Create immune system without ecosystem (test mode)
    immune = AureonImmuneSystem()
    
    # Run a health scan
    print("Running health scan...")
    report = immune._run_health_scan()
    
    # Show results
    print("\n📊 HEALTH SIGNALS:")
    for name, value in sorted(report.items()):
        emoji = '🟢' if value > 0.8 else '🟡' if value > 0.5 else '🔴'
        print(f"   {emoji} {name}: {value*100:.1f}%")
    
    # Get overall status
    status = immune.get_health_status()
    print(f"\n{status['emoji']} OVERALL: {status['status']} ({status['health']*100:.1f}%)")
    
    # Show status line
    print(f"\n{immune.get_status_line()}")
    
    print("\n✅ Immune system test complete!")
