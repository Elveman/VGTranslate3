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
    
    def start(self):
        """Start HTTP server in background thread"""
        static_dir = Path(__file__).parent / 'static'
        
        def run_server():
            handler = lambda *args, **kwargs: WebUIHandler(*args, static_dir=static_dir, **kwargs)
            self.http_server = HTTPServer((self.host, self.port), handler)
            print(f"Web UI HTTP server started on http://{self.host}:{self.port}")
            self.http_server.serve_forever()
        
        self.thread = threading.Thread(target=run_server)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop HTTP server"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()


async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    websocket_clients.add(websocket)
    print(f"Web UI client connected. Total clients: {len(websocket_clients)}")
    
    try:
        # Send current history on connect
        if translation_history:
            await websocket.send(json.dumps({
                'type': 'history',
                'data': list(translation_history)
            }))
        
        # Keep connection alive
        async for message in websocket:
            # Handle incoming messages (if needed)
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        websocket_clients.discard(websocket)
        print(f"Web UI client disconnected. Total clients: {len(websocket_clients)}")


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
