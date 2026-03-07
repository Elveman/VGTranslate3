import json, base64, pathlib, subprocess, time, requests, sys, os
import threading
from unittest.mock import patch, MagicMock

# Setup path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

PNG = base64.b64encode(pathlib.Path("tests/hello.png").read_bytes()).decode()

def wait_for_server(url, timeout=5):
    """Wait for server to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.1)
    return False

def test_serve_hello():
    """Test server with mocked OCR and Translation providers"""
    from vgtranslate3 import config
    from vgtranslate3.serve import APIHandler
    from vgtranslate3 import imaging
    import http.server
    
    # Initialize fonts to prevent imaging.py from crashing
    try:
        imaging.load_font("RobotoCondensed-Bold.ttf")
    except Exception:
        pass
    
    # Mock config to avoid requiring actual API keys
    config.local_server_enabled = True
    config.local_server_host = "localhost"
    config.local_server_port = 4404
    config.local_server_api_key_type = "mock"
    config.ocr_provider = "mock"
    config.translation_provider = "mock"
    config.tts_enabled = False
    
    # Create mock providers
    mock_ocr_provider = MagicMock()
    mock_ocr_provider.recognize.return_value = ({
        "blocks": [{
            "text": "Hello",
            "source_text": "Hello",
            "bounding_box": {"x": 0, "y": 0, "w": 100, "h": 20}
        }]
    }, {"source_lang": "en"})
    
    mock_trans_provider = MagicMock()
    mock_trans_provider.translate.return_value = {
        "blocks": [{
            "source_text": "Hello",
            "translation": {"en": "Hello"},
            "bounding_box": {"x": 0, "y": 0, "w": 100, "h": 20},
            "target_lang": "en"
        }]
    }
    
    server = None
    try:
        with patch('vgtranslate3.ocr_providers.get_ocr_provider', return_value=mock_ocr_provider), \
             patch('vgtranslate3.translation_providers.get_translation_provider', return_value=mock_trans_provider):
            
            server = http.server.HTTPServer(("localhost", 4404), APIHandler)
            server.timeout = 1
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            
            # Wait for server to start
            if not wait_for_server("http://localhost:4404"):
                raise RuntimeError("Server did not start")
            
            r = requests.post("http://localhost:4404/service?target_lang=en",
                              data=json.dumps({"image": PNG}), timeout=10)
            assert r.status_code == 200
            payload = r.json()
            assert any(k in payload for k in ("blocks", "image"))
    finally:
        if server:
            server.shutdown()
