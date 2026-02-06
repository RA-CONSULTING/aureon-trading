
import http.server
import socketserver
import os
import threading
import time
import json
from http import HTTPStatus

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    """
    A simple health check handler that responds with 200 OK on /health
    and provides a basic status page on /.
    """
    def do_GET(self):
        if self.path == '/health':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'timestamp': time.time()}).encode('utf-8'))
        elif self.path == '/':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <html>
                <head><title>Aureon Health</title></head>
                <body>
                    <h1>Aureon Standalone Health Checker</h1>
                    <p>Status: OK</p>
                    <p>Timestamp: {time.time()}</p>
                    <p>PORT: {os.environ.get("PORT", "Not Set")}</p>
                </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

def run_health_server():
    """
    Runs the health check server in a separate thread.
    """
    port = int(os.environ.get("PORT", 8080))
    
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            print(f"Health check server started on port {port}", flush=True)
            httpd.serve_forever()
    except OSError as e:
        print(f"Error starting health check server on port {port}: {e}", flush=True)
        # Exit if we can't bind to the port, as the container won't be healthy
        os._exit(1)

if __name__ == "__main__":
    # Run the server in a background thread so the main app can start
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    # Keep the main thread alive to simulate the main application running
    print("Main application thread running...", flush=True)
    while True:
        time.sleep(60)
        print("Main application heartbeat.", flush=True)
