#!/usr/bin/env python3
"""
🏥 AUREON PRO DASHBOARD - HEALTH CHECK
═══════════════════════════════════════════════════════════════════════════
Comprehensive diagnostic checklist for the dashboard.
"""

import sys
import os
import json

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check(name, condition, details=""):
    """Print a check result."""
    if condition:
        print(f"  {GREEN}✅ {name}{RESET}")
        if details:
            print(f"     {BLUE}{details}{RESET}")
        return True
    else:
        print(f"  {RED}❌ {name}{RESET}")
        if details:
            print(f"     {YELLOW}{details}{RESET}")
        return False

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🏥 AUREON PRO DASHBOARD - HEALTH CHECK{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    passed = 0
    failed = 0
    warnings = 0
    
    # 1. File System Checks
    print(f"{BLUE}📁 FILE SYSTEM CHECKS{RESET}")
    if check("Dashboard file exists", os.path.exists('aureon_pro_dashboard.py')):
        passed += 1
        with open('aureon_pro_dashboard.py', 'r') as f:
            lines = len(f.readlines())
            check("Dashboard file readable", True, f"{lines:,} lines")
            passed += 1
    else:
        failed += 2
    
    if check("Intelligence enhancements exists", os.path.exists('dashboard_intelligence_enhancements.py')):
        passed += 1
    else:
        warnings += 1
    
    if check("Integration guide exists", os.path.exists('DASHBOARD_INTEGRATION_GUIDE.md')):
        passed += 1
    else:
        warnings += 1
    
    # 2. Python Dependencies
    print(f"\n{BLUE}🐍 PYTHON DEPENDENCIES{RESET}")
    
    deps = [
        ('aiohttp', 'Web server framework'),
        ('asyncio', 'Async runtime'),
        ('json', 'JSON handling'),
        ('logging', 'Logging'),
        ('datetime', 'Time handling')
    ]
    
    for dep, desc in deps:
        try:
            __import__(dep)
            check(f"{dep}", True, desc)
            passed += 1
        except ImportError:
            check(f"{dep}", False, f"MISSING: {desc}")
            failed += 1
    
    # 3. Environment Variables
    print(f"\n{BLUE}🔐 ENVIRONMENT VARIABLES{RESET}")
    
    env_vars = [
        ('BINANCE_API_KEY', 'Binance exchange access'),
        ('BINANCE_API_SECRET', 'Binance exchange secret'),
        ('KRAKEN_API_KEY', 'Kraken exchange access'),
        ('KRAKEN_API_SECRET', 'Kraken exchange secret'),
        ('ALPACA_API_KEY', 'Alpaca trading access'),
        ('ALPACA_SECRET_KEY', 'Alpaca trading secret'),
    ]
    
    for var, desc in env_vars:
        value = os.getenv(var)
        if value:
            check(f"{var}", True, f"SET ({len(value)} chars) - {desc}")
            passed += 1
        else:
            check(f"{var}", False, f"NOT SET - {desc} (Dashboard will have limited data)")
            warnings += 1
    
    # 4. Aureon Module Imports
    print(f"\n{BLUE}🧠 AUREON INTELLIGENCE MODULES{RESET}")
    
    modules = [
        ('queen_cognitive_narrator', 'AI commentary'),
        ('aureon_ocean_scanner', 'Market scanning'),
        ('aureon_harmonic_liquid_aluminium', 'Harmonic field'),
        ('unified_market_cache', 'Price caching'),
        ('binance_client', 'Binance API'),
        ('kraken_client', 'Kraken API'),
        ('alpaca_client', 'Alpaca API'),
        ('live_position_viewer', 'Position viewer'),
    ]
    
    for module, desc in modules:
        try:
            __import__(module)
            check(f"{module}", True, desc)
            passed += 1
        except ImportError as e:
            check(f"{module}", False, f"{desc} - {str(e)[:50]}")
            warnings += 1
    
    # 5. State Files
    print(f"\n{BLUE}💾 STATE FILES (DATA SOURCES){RESET}")
    
    state_files = [
        ('dashboard_snapshot.json', 'Portfolio cache'),
        ('cost_basis_history.json', 'Cost basis tracking'),
        ('7day_pending_validations.json', 'Timeline validations'),
        ('7day_anchored_timelines.json', 'Anchored timelines'),
        ('7day_current_plan.json', '7-day plan'),
        ('active_position.json', 'Active position'),
        ('elephant_memory.json', 'Elephant memory'),
    ]
    
    for filename, desc in state_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    size = len(json.dumps(data))
                    check(f"{filename}", True, f"{desc} ({size} bytes)")
                    passed += 1
            except Exception as e:
                check(f"{filename}", False, f"{desc} - CORRUPTED: {str(e)[:50]}")
                warnings += 1
        else:
            check(f"{filename}", False, f"{desc} - File not found (will be created)")
            warnings += 1
    
    # 6. Dashboard Configuration
    print(f"\n{BLUE}⚙️ DASHBOARD CONFIGURATION{RESET}")
    
    try:
        # Check if we can import the dashboard class
        sys.path.insert(0, '.')
        from aureon_pro_dashboard import AureonProDashboard
        check("AureonProDashboard class", True, "Class definition found")
        passed += 1
        
        # Check port configuration
        port = int(os.getenv('PORT', '14000'))
        check(f"Port configuration", True, f"Port {port}")
        passed += 1
        
    except Exception as e:
        check("AureonProDashboard class", False, str(e)[:100])
        failed += 1
    
    # 7. API Endpoints Check
    print(f"\n{BLUE}🔌 API ENDPOINTS{RESET}")
    
    try:
        from aureon_pro_dashboard import AureonProDashboard
        dashboard = AureonProDashboard()
        
        endpoints = [
            ('/', 'Main dashboard HTML'),
            ('/health', 'Health check'),
            ('/api/status', 'Diagnostic status'),
            ('/api/portfolio', 'Portfolio data'),
            ('/api/prices', 'Price data'),
            ('/api/balances', 'Exchange balances'),
            ('/api/ocean', 'Ocean scanner'),
            ('/ws', 'WebSocket stream'),
        ]
        
        for route, desc in endpoints:
            # Check if route exists in app.router
            found = any(r.resource.canonical == route for r in dashboard.app.router.routes())
            check(f"{route}", found, desc)
            if found:
                passed += 1
            else:
                failed += 1
                
    except Exception as e:
        print(f"  {RED}❌ Could not check endpoints: {str(e)[:100]}{RESET}")
        failed += len(endpoints)
    
    # 8. Background Loops
    print(f"\n{BLUE}🔄 BACKGROUND LOOPS{RESET}")
    
    loops = [
        ('queen_commentary_loop', 'AI commentary'),
        ('data_refresh_loop', 'Data polling'),
        ('ocean_data_loop', 'Ocean scanning'),
        ('harmonic_field_loop', 'Field streaming'),
    ]
    
    try:
        from aureon_pro_dashboard import AureonProDashboard
        dashboard = AureonProDashboard()
        
        for loop_name, desc in loops:
            if hasattr(dashboard, loop_name):
                check(f"{loop_name}", True, desc)
                passed += 1
            else:
                check(f"{loop_name}", False, f"{desc} - Method not found")
                failed += 1
    except Exception as e:
        print(f"  {RED}❌ Could not check loops: {str(e)[:100]}{RESET}")
        failed += len(loops)
    
    # 9. Intelligence Enhancements
    print(f"\n{BLUE}🎯 INTELLIGENCE ENHANCEMENTS (NEW){RESET}")
    
    try:
        from dashboard_intelligence_enhancements import IntelligenceHub
        check("IntelligenceHub class", True, "Enhancement module available")
        passed += 1
        
        hub = IntelligenceHub()
        
        methods = [
            ('refresh_predator_data', 'Predator detection'),
            ('refresh_sniper_data', 'IRA sniper scope'),
            ('refresh_quantum_data', 'Quantum systems'),
            ('refresh_timeline_data', 'Timeline oracle'),
            ('refresh_intelligence_health', 'Intelligence health'),
            ('refresh_whale_data', 'Whale tracker'),
            ('refresh_stealth_data', 'Stealth execution'),
        ]
        
        for method_name, desc in methods:
            if hasattr(hub, method_name):
                check(f"{method_name}", True, desc)
                passed += 1
            else:
                check(f"{method_name}", False, f"{desc} - Method not found")
                warnings += 1
                
    except ImportError:
        check("IntelligenceHub", False, "Enhancement module not available (not integrated yet)")
        warnings += 1
    except Exception as e:
        check("IntelligenceHub", False, str(e)[:100])
        warnings += 1
    
    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}📊 SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    total = passed + failed + warnings
    print(f"  {GREEN}✅ Passed: {passed}/{total}{RESET}")
    print(f"  {RED}❌ Failed: {failed}/{total}{RESET}")
    print(f"  {YELLOW}⚠️  Warnings: {warnings}/{total}{RESET}")
    
    # Overall Status
    print(f"\n{BLUE}{'='*70}{RESET}")
    if failed == 0:
        if warnings == 0:
            print(f"{GREEN}✨ DASHBOARD STATUS: PERFECT - ALL SYSTEMS GO! ✨{RESET}")
        else:
            print(f"{GREEN}✅ DASHBOARD STATUS: OPERATIONAL{RESET}")
            print(f"{YELLOW}   ⚠️  {warnings} warning(s) - dashboard will work but may have limited features{RESET}")
    else:
        print(f"{RED}⚠️  DASHBOARD STATUS: ISSUES DETECTED{RESET}")
        print(f"{RED}   ❌ {failed} critical issue(s) - dashboard may not start properly{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    # Recommendations
    if failed > 0 or warnings > 0:
        print(f"{YELLOW}💡 RECOMMENDATIONS:{RESET}")
        if warnings > 0 and 'API_KEY' in str(warnings):
            print(f"  • Set missing API keys in .env file for full functionality")
        if failed > 0:
            print(f"  • Install missing dependencies: pip install -r requirements.txt")
            print(f"  • Check module imports for syntax errors")
        print()
    
    # Quick Start
    print(f"{BLUE}🚀 QUICK START:{RESET}")
    print(f"  python aureon_pro_dashboard.py")
    print(f"  Then open: http://localhost:14000\n")

if __name__ == '__main__':
    main()
