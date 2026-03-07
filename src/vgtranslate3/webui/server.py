"""
Web UI Server for VGTranslate3

Provides WebSocket and HTTP endpoints for live translation monitoring.
"""

import asyncio
import websockets
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
from pathlib import Path

# Global state (shared with serve.py)
translation_history = []
websocket_clients = set()


class WebUIHandler(SimpleHTTPRequestHandler):
    """HTTP handler for Web UI static files and API"""
    
    def __init__(self, *args, static_dir=None, **kwargs):
        self.static_dir = static_dir or Path(__file__).parent / 'static'
        super().__init__(*args, directory=str(self.static_dir), **kwargs)
    
    def do_GET(self):
        if self.path == '/api/history':
            self.send_json_response(list(translation_history))
        elif self.path == '/api/status':
            self.send_json_response({
                'connected_clients': len(websocket_clients),
                'history_size': len(translation_history)
            })
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/export':
            self.export_data()
        else:
            self.send_error(404)
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def export_data(self):
        """Export history as ZIP"""
        import zipfile
        import io
        import base64
        from datetime import datetime
        
        zip_buffer = io.BytesIO()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Screenshots
                for i, item in enumerate(translation_history):
                    try:
                        # Original
                        if 'original_image' in item:
                            img_data = base64.b64decode(item['original_image'])
                            zip_file.writestr(f'{i:03d}_original.png', img_data)
                        
                        # BBox visualization
                        if 'bbox_image' in item:
                            img_data = base64.b64decode(item['bbox_image'])
                            zip_file.writestr(f'{i:03d}_bbox.png', img_data)
                        
                        # Result
                        if 'result_image' in item:
                            img_data = base64.b64decode(item['result_image'])
                            zip_file.writestr(f'{i:03d}_result.png', img_data)
                    except Exception as e:
                        print(f"Export error for item {i}: {e}")
                
                # JSON log
                log_data = json.dumps(translation_history, indent=2, ensure_ascii=False)
                zip_file.writestr('translation_log.json', log_data.encode('utf-8'))
            
            zip_buffer.seek(0)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            self.send_header('Content-Disposition', f'attachment; filename="vgtranslate3_export_{timestamp}.zip"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(zip_buffer.read())
        except Exception as e:
            print(f"Export error: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass


class WebUIServer:
    """Web UI HTTP + WebSocket server"""
    
    def __init__(self, host='0.0.0.0', port=4405):
        self.host = host
        self.port = port
        self.http_server = None
        self.ws_server = None
        self.thread = None
        self.ws_thread = None
    
    def start(self):
        """Start HTTP and WebSocket servers in background threads"""
        static_dir = Path(__file__).parent / 'static'
        
        def run_http():
            handler = lambda *args, **kwargs: WebUIHandler(*args, static_dir=static_dir, **kwargs)
            self.http_server = HTTPServer((self.host, self.port), handler)
            print(f"Web UI HTTP server started on http://{self.host}:{self.port}")
            self.http_server.serve_forever()
        
        async def run_websocket():
            """Run WebSocket server"""
            ws_host = self.host
            ws_port = self.port + 1  # WebSocket on port 4406
            print(f"WebSocket server starting on ws://{ws_host}:{ws_port}")
            async with websockets.serve(websocket_handler, ws_host, ws_port):
                await asyncio.Future()  # Run forever
        
        def run_ws_loop():
            """Run asyncio event loop for WebSocket"""
            asyncio.run(run_websocket())
        
        # Start HTTP server
        self.thread = threading.Thread(target=run_http)
        self.thread.daemon = True
        self.thread.start()
        
        # Start WebSocket server
        self.ws_thread = threading.Thread(target=run_ws_loop)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        print(f"WebSocket server started on ws://{self.host}:{self.port + 1}")
    
    def stop(self):
        """Stop HTTP server"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()


async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    websocket_clients.add(websocket)
    print(f"✓ Web UI client connected")
    
    try:
        # Send initial connection message
        await websocket.send(json.dumps({
            'type': 'connected',
            'status': 'ok'
        }))
        
        # Keep connection alive - wait indefinitely
        # Use sleep instead of async for to avoid waiting for messages
        await asyncio.sleep(86400)  # 24 hours
            
    except websockets.exceptions.ConnectionClosed:
        print(f"  Client disconnected")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    finally:
        websocket_clients.discard(websocket)


async def broadcast_to_webui(data):
    """Broadcast data to all connected WebSocket clients"""
    if not websocket_clients:
        return
    
    message = json.dumps(data, ensure_ascii=False)
    
    # Create tasks for all clients
    tasks = []
    for client in websocket_clients.copy():
        try:
            tasks.append(client.send(message))
        except:
            pass
    
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def update_history(data):
    """Add data to translation history"""
    translation_history.append(data)
    # Keep only last 10 items
    while len(translation_history) > 10:
        translation_history.pop(0)


def clear_history():
    """Clear translation history"""
    translation_history.clear()
