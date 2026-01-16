#!/usr/bin/env python3
"""Test if asyncio works on Windows and if the system reaches the run loop."""

import sys
import os
import asyncio
import time

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
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

async def test_loop():
    """Test infinite async loop."""
    print("\n" + "="*70)
    print("🧪 TESTING ASYNC LOOP ON WINDOWS")
    print("="*70)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print(f"Asyncio: {asyncio.__version__ if hasattr(asyncio, '__version__') else 'Unknown'}")
    print("="*70)
    
    print("\n✅ Starting infinite loop (5 iterations then exit)...")
    
    for i in range(5):
        print(f"   Loop iteration {i+1}/5 at {time.strftime('%H:%M:%S')}")
        await asyncio.sleep(1)
    
    print("\n✅ Loop completed successfully!")
    print("🎯 If you see this, asyncio works on Windows!")

async def main():
    print("🚀 Starting main() function...")
    await test_loop()
    print("✅ main() completed!")

if __name__ == "__main__":
    print("🔬 Test script starting...")
    try:
        asyncio.run(main())
        print("✅ asyncio.run() completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 Test complete!")
