#!/usr/bin/env python3
"""Simple health check server test."""
import asyncio
import json
from aiohttp import web

async def handle_health(request):
    """Health check endpoint."""
    return web.json_response({
        'status': 'healthy',
        'service': 'test-server',
        'timestamp': asyncio.get_event_loop().time()
    })

async def main():
    app = web.Application()
    app.router.add_get('/health', handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    print("🌐 Test server started on http://0.0.0.0:8080")
    print("   💚 Health: http://localhost:8080/health")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())