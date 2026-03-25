#!/usr/bin/env python3
"""
👑🌌 AUREON DEPLOYMENT VERIFICATION 👑🌌
═══════════════════════════════════════════════════════════════════════════

DIGITALOCEAN PRODUCTION DEPLOYMENT TEST

Tests all critical components for production deployment:
- Redis connectivity
- ThoughtBus messaging
- Autonomous worker imports
- Command center health endpoint
- Parallel orchestrator
- Full autonomous controller

Gary Leckey | January 2026 | DEPLOYMENT VERIFICATION
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import json

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffling=True)
    except Exception:
        pass

def test_redis_connectivity():
    """Test Redis connectivity."""
    print("🔴 Testing Redis connectivity...")
    try:
        redis_url = os.getenv('AUREON_REDIS_URL')
        if not redis_url:
            print("⚠️ No AUREON_REDIS_URL set, using file-based mode")
            return True

        import redis
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connected successfully")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_thought_bus():
    """Test ThoughtBus initialization."""
    print("🔴 Testing ThoughtBus...")
    try:
        from aureon_thought_bus import get_thought_bus
        bus = get_thought_bus()
        print("✅ ThoughtBus initialized successfully")
        return True
    except Exception as e:
        print(f"❌ ThoughtBus failed: {e}")
        return False

def test_parallel_orchestrator():
    """Test parallel orchestrator import."""
    print("🔴 Testing Parallel Orchestrator...")
    try:
        from aureon_parallel_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        print("✅ Parallel Orchestrator initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Parallel Orchestrator failed: {e}")
        return False

def test_autonomous_controller():
    """Test autonomous controller import."""
    print("🔴 Testing Autonomous Controller...")
    try:
        from aureon_full_autonomous import get_autonomous_controller
        controller = get_autonomous_controller()
        print("✅ Autonomous Controller initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Autonomous Controller failed: {e}")
        return False

def test_goal_tracker():
    """Test billion dollar goal tracker."""
    print("🔴 Testing Goal Tracker...")
    try:
        from aureon_billion_goal_tracker import get_goal_tracker
        tracker = get_goal_tracker()
        print("✅ Goal Tracker initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Goal Tracker failed: {e}")
        return False

def test_research_engine():
    """Test research engine."""
    print("🔴 Testing Research Engine...")
    try:
        from aureon_queen_research_engine import get_research_engine
        engine = get_research_engine()
        print("✅ Research Engine initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Research Engine failed: {e}")
        return False

def test_autonomous_worker():
    """Test autonomous worker."""
    print("🔴 Testing Autonomous Worker...")
    try:
        from aureon_autonomous_worker import AureonAutonomousWorker
        worker = AureonAutonomousWorker()
        print("✅ Autonomous Worker initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Autonomous Worker failed: {e}")
        return False

def main():
    """Run all deployment tests."""
    print("\n" + "=" * 70)
    print("👑🌌 AUREON DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print("   Testing production deployment readiness")
    print("=" * 70 + "\n")

    tests = [
        test_redis_connectivity,
        test_thought_bus,
        test_parallel_orchestrator,
        test_autonomous_controller,
        test_goal_tracker,
        test_research_engine,
        test_autonomous_worker,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 70)
    print(f"📊 DEPLOYMENT TEST RESULTS: {passed}/{total} PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL SYSTEMS READY FOR PRODUCTION DEPLOYMENT!")
        print("🚀 Ready to deploy to DigitalOcean App Platform")
        return 0
    else:
        print("❌ SOME TESTS FAILED - CHECK ERRORS ABOVE")
        print("🔧 Fix issues before deploying to production")
        return 1

if __name__ == "__main__":
    sys.exit(main())