#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VGTranslate3 Server

Lightweight OCR + MT server for game screen captures.
Uses modular provider architecture for flexibility.
"""

from __future__ import annotations

import sys
import os
import time
import json
import threading
import re
import base64
import http.server
import http.client
import urllib.parse
from typing import Optional, Tuple, Any, Dict, List
from html import unescape

from PIL import Image, ImageEnhance, ImageDraw

from . import config
from . import imaging
from .util import (
    load_image, image_to_string, fix_neg_width_height, image_to_string_format,
    swap_red_blue, segfill, reduce_to_multi_color, reduce_to_text_color,
    color_hex_to_byte, create_bbox_visualization
)
from . import screen_translate
from . import ocr_providers
from . import translation_providers
from .text_to_speech import TextToSpeech

# Optional imports with graceful fallback
try:
    from .bbox_extractor import extract_bounding_boxes, match_texts_to_boxes
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    def extract_bounding_boxes(*args, **kwargs):
        raise ImportError("OpenCV not installed. Install with: pip install opencv-python-headless")
    def match_texts_to_boxes(*args, **kwargs):
        raise ImportError("OpenCV not installed")

# Web UI imports
try:
    import asyncio
    from .webui.server import WebUIServer, broadcast_to_webui, update_history, websocket_clients
    HAS_WEBUI = True
except ImportError as e:
    HAS_WEBUI = False
    WebUIServer = None
    broadcast_to_webui = None
    update_history = None
    websocket_clients = set()
    print(f"Warning: Web UI not available. Install with: pip install websockets ({e})")

SOUND_FORMATS = {"wav": 1}
IMAGE_FORMATS = {"bmp": 1, "png": 1}

server_thread = None
window_obj = None
httpd_server = None


class APIHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><head><title></title></head></html>")
        self.wfile.write(b"<body>yo!</body></html>")
        
    def do_POST(self):
        print("____")
        print(f"POST request from {self.client_address[0]}:{self.client_address[1]}")
        print(f"Path: {self.path}")
        query = urllib.parse.urlparse(self.path).query
        query_components = dict(qc.split("=") for qc in query.split("&")) if query.strip() else {}
        
        content_length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(content_length)
        print(data[:100])
        print(content_length)
        print(data[-100:])
        body = json.loads(data)
        
        start_time = time.time()
        
        result = self._process_request(body, query_components)
        print("AUTO AUTO")
        print(['Request took: ', time.time() - start_time])
        print(f"Response keys: {list(result.keys())}")
        print(f"Blocks count: {len(result.get('blocks', []))}")
        
        output_str = json.dumps(result, ensure_ascii=False)
        output_bytes = output_str.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(output_bytes)))
        self.end_headers()

        print("Output length:", len(output_bytes))
        self.wfile.write(output_bytes)

    def _process_request(self, body: Dict, query: Dict) -> Dict:
        source_lang = query.get("source_lang")
        target_lang = query.get("target_lang", "en")
        mode = query.get("mode", "fast")
        request_output = query.get("output", "image,sound").lower().split(",")

        request_out_dict = {}
        alpha = False
        error_string = ""

        for entry in request_output:
            if entry == 'image' and 'image' not in request_out_dict:
                request_out_dict['image'] = 'bmp'
            elif entry == 'sound' and 'sound' not in request_out_dict:
                request_out_dict['sound'] = 'wav'
            else:
                if SOUND_FORMATS.get(entry):
                    request_out_dict['sound'] = entry
                else:
                    if entry[-2:] == "-a":
                        request_out_dict['image'] = entry[:-2]
                        alpha = True
                    else:
                        request_out_dict['image'] = entry

        print(request_output)
        pixel_format = "RGB"
        image_data = body.get("image")
        
        start_time = time.time()  # Track start time for metrics
        
        image_object = load_image(image_data).convert("RGB")
        print(f"w: {image_object.width} h: {image_object.height}")
        
        if pixel_format == "BGR":
            image_object = swap_red_blue(image_object)
        
        # Handle legacy providers
        if config.local_server_api_key_type == "free":
            return {"error": "Free tier not implemented"}
        
        elif config.local_server_api_key_type == "ztranslate":
            return self._handle_ztranslate(body, image_object, source_lang, target_lang, mode, request_output)
        
        # Save original image for Web UI
        original_image_data = image_to_string(image_object)
        
        # Modern pipeline with separated providers
        return self._handle_modern_pipeline(
            body, image_object, image_data, original_image_data, source_lang, target_lang,
            mode, request_output, request_out_dict, alpha, pixel_format,
            start_time
        )

    def _handle_ztranslate(self, body: Dict, image_object: Image.Image,
                          source_lang: str, target_lang: str, mode: str,
                          request_output: List[str]) -> Dict:
        """Handle ztranslate.net API calls"""
        if "image" not in request_output and mode != "normal":
            image_object = image_object.convert("LA").convert("RGB")
            image_object = image_object.convert("P", palette=Image.Palette.ADAPTIVE, colors=32)
        else:
            image_object = image_object.convert("P", palette=Image.Palette.ADAPTIVE)

        body_kwargs = {k: v for k, v in body.items() if k != "image"}
        image_data = image_to_string(image_object)
        
        return screen_translate.CallService.call_service(
            image_data, source_lang, target_lang,
            mode=mode, request_output=request_output, body_kwargs=body_kwargs
        )

    def _handle_modern_pipeline(self, body: Dict, image_object: Image.Image,
                               image_data, original_image_data, source_lang: str, target_lang: str,
                               mode: str, request_output: List[str],
                               request_out_dict: Dict, alpha: bool,
                               pixel_format: str, start_time: float) -> Dict:
        """Handle modern pipeline with separated OCR/Translation/TTS providers"""
        
        output_data = {}
        error_string = ""
        
        # Determine providers
        ocr_provider_name = config.ocr_provider
        translation_provider_name = config.translation_provider
        tts_provider_name = config.tts_provider
        
        # Handle legacy config
        if config.local_server_api_key_type == "google":
            ocr_provider_name = "google"
            translation_provider_name = "google"
        elif config.local_server_api_key_type == "yandex":
            ocr_provider_name = "yandex"
            translation_provider_name = "yandex"
        elif config.local_server_api_key_type == "tess_google":
            ocr_provider_name = "tesseract"
            translation_provider_name = "google"
        
        # OCR Stage with retry (max 3 attempts)
        print(f"Using OCR provider: {ocr_provider_name}")
        print(f"Source language: {source_lang or 'auto-detect'}")
        ocr_provider = ocr_providers.get_ocr_provider(ocr_provider_name)
        
        data, raw_output = None, None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data, raw_output = ocr_provider.recognize(image_data, source_lang)
                # Success - exit retry loop
                break
            except (TypeError, KeyError, IndexError) as e:
                print(f"OCR attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait before retry
                else:
                    print(f"OCR failed after {max_retries} attempts")
                    error_string = f"OCR error: {e}"
                    data = {"blocks": []}
                    raw_output = {}
        
        # Update source_lang from OCR result if available
        if raw_output:
            detected_lang = raw_output.get("source_lang") or raw_output.get("detected_language")
            if detected_lang:
                print(f"OCR detected language: {detected_lang}")
                source_lang = detected_lang
        
        if not data.get("blocks"):
            error_string = "No text found."
        
        # Convert to standard format
        if "blocks" in data and ocr_provider_name != "tesseract":
            for block in data["blocks"]:
                if "bbox" in block and "vertices" not in block:
                    bb = block["bbox"]
                    block["boundingBox"] = {
                        "vertices": [
                            {"x": bb.get("x", 0), "y": bb.get("y", 0)},
                            {"x": bb.get("x", 0) + bb.get("width", 0), "y": bb.get("y", 0)},
                            {"x": bb.get("x", 0) + bb.get("width", 0), "y": bb.get("y", 0) + bb.get("height", 0)},
                            {"x": bb.get("x", 0), "y": bb.get("y", 0) + bb.get("height", 0)}
                        ]
                    }
                if "text" in block:
                    block["source_text"] = block["text"]
        
        # Translation Stage
        print(f"Using Translation provider: {translation_provider_name}")
        translation_provider = translation_providers.get_translation_provider(translation_provider_name)
        try:
            data = translation_provider.translate(data.get("blocks", []), target_lang, source_lang)
        except Exception as e:
            print(f"Translation failed: {e}")
            error_string = f"Translation error: {e}"
            data = {"blocks": data.get("blocks", []) if data else []}
        
        # Ensure all blocks have translation in BOTH formats for maximum compatibility
        if data:
            for block in data.get("blocks", []):
                # Get translation text
                if isinstance(block.get("translation"), dict):
                    translation_text = block["translation"].get(target_lang.lower(), block.get("source_text", block.get("text", "")))
                else:
                    translation_text = block.get("translation", block.get("source_text", block.get("text", "")))
                
                # Store BOTH formats:
                # 1. As STRING (for very old VGTranslate that uses translation directly)
                block["translation_str"] = translation_text
                # 2. As DICT (for newer VGTranslate that uses translation[target_lang])
                block["translation"] = {target_lang.lower(): translation_text}
                
                # Store target_lang
                block["target_lang"] = target_lang
                
                # Ensure bounding_box has x,y,w,h format
                if "bounding_box" in block:
                    bb = block["bounding_box"]
                    if "x1" in bb and "x" not in bb:
                        bb["x"] = bb["x1"]
                        bb["y"] = bb["y1"]
                        bb["w"] = bb["x2"] - bb["x1"]
                        bb["h"] = bb["y2"] - bb["y1"]
        
        # TTS Stage (only if enabled in config AND requested)
        if config.tts_enabled and "sound" in request_out_dict and data.get("blocks"):
            try:
                texts = []
                for block in sorted(data['blocks'], key=lambda x: (x.get('bounding_box', {}).get('y', 0), x.get('bounding_box', {}).get('x', 0))):
                    # Support both string and dict translation formats
                    if isinstance(block.get('translation'), dict):
                        text = block['translation'].get(target_lang.lower(), '')
                    else:
                        text = block.get('translation', '')
                    texts.append(text)
                
                text_to_say = " ".join(texts).replace("...", " [] ")
                
                # Check if TTS provider is configured
                if tts_provider_name == "openai" and not config.openai_api_key:
                    print("Warning: OpenAI TTS requested but API key not configured, skipping")
                elif tts_provider_name == "yandex" and not config.yandex_iam_token and not config.yandex_translation_key:
                    print("Warning: Yandex TTS requested but credentials not configured, skipping")
                elif tts_provider_name == "google" and not config.local_server_translation_key:
                    print("Warning: Google TTS requested but API key not configured, skipping")
                else:
                    if tts_provider_name == "openai":
                        wav_data = TextToSpeech.text_to_speech_api(
                            text_to_say, source_lang=target_lang, provider="openai"
                        )
                    elif tts_provider_name == "yandex":
                        wav_data = TextToSpeech.text_to_speech_api(
                            text_to_say, source_lang=target_lang, provider="yandex"
                        )
                    else:
                        # Default to Google
                        wav_data = TextToSpeech.text_to_speech_api(
                            text_to_say, source_lang=target_lang, provider="google"
                        )
                    
                    if isinstance(wav_data, str):
                        wav_data = wav_data.encode("utf-8")
                    
                    wav_data = self._fix_wav_size(wav_data)
                    output_data['sound'] = base64.b64encode(wav_data).decode("ascii")
            except Exception as e:
                print(f"TTS error: {e}")
                output_data['sound'] = ""
        elif "sound" in request_out_dict and not config.tts_enabled:
            print("TTS disabled in config, skipping")
        
        # Image generation
        if window_obj:
            output_image = imaging.ImageModder.write(image_object, data, target_lang)
            window_obj.load_image_object(output_image)
            window_obj.curr_image = imaging.ImageIterator.prev()
        
        if "image" in request_out_dict:
            # Use original image_object, don't replace with transparent
            output_image = imaging.ImageModder.write(image_object, data, target_lang)
            
            # Convert RGBA to RGB with white background if needed
            if output_image.mode == "RGBA":
                # Create white background and composite
                background = Image.new("RGB", output_image.size, (255, 255, 255))
                if output_image.mode == "RGBA":
                    background.paste(output_image, mask=output_image.split()[3])  # Use alpha channel as mask
                output_image = background
            
            if pixel_format == "BGR":
                output_image = output_image.convert("RGB")
                output_image = swap_red_blue(output_image)
            
            output_data["image"] = image_to_string_format(output_image, request_out_dict['image'], mode="RGB")
        
        if error_string:
            output_data['error'] = error_string
        
        # DO NOT send blocks - original VGTranslate generates image on server side
        # and returns only image+sound, not blocks
        
        # Prepare data for Web UI
        if HAS_WEBUI and config.webui_enabled:
            try:
                # Create bbox visualization image
                bbox_image = create_bbox_visualization(image_object, data.get('blocks', []))
                
                webui_data = {
                    'type': 'translation',
                    'timestamp': time.time(),
                    'original_image': 'data:image/png;base64,' + original_image_data,
                    'bbox_image': 'data:image/png;base64,' + image_to_string(bbox_image),
                    'result_image': 'data:image/png;base64,' + output_data.get('image', ''),
                    'blocks': data.get('blocks', []),
                    'metrics': {
                        'total_latency': time.time() - start_time,
                        'ocr_provider': ocr_provider_name,
                        'translation_provider': translation_provider_name,
                        'tts_enabled': config.tts_enabled and 'sound' in output_data
                    }
                }
                
                # Update history and broadcast
                if update_history:
                    update_history(webui_data)
                if broadcast_to_webui and asyncio:
                    asyncio.run(broadcast_to_webui(webui_data))
            except Exception as e:
                print(f"Web UI error: {e}")
        
        return output_data

    def _fix_wav_size(self, wav: bytes) -> bytes:
        """Fix RIFF header size fields"""
        def tb(size: int) -> bytearray:
            return bytearray((size & 0xFF, (size >> 8) & 0xFF, (size >> 16) & 0xFF, (size >> 24) & 0xFF))
        
        s = bytearray(wav)
        s[4:8] = tb(len(wav))
        s[40:44] = tb(len(wav) - 44)
        return bytes(s)


def start_api_server(window_object):
    global server_thread, window_obj
    print("start api server")
    if config.local_server_enabled:
        window_obj = window_object
        server_thread = threading.Thread(target=start_api_server2)
        server_thread.start()

def kill_api_server():
    global httpd_server
    print("kill api server")
    if config.local_server_enabled and httpd_server:
        httpd_server.shutdown()

def start_api_server2():
    global httpd_server
    host = config.local_server_host
    port = config.local_server_port
    server_class = http.server.HTTPServer
    httpd_server = server_class((host, port), APIHandler)
    print("server start")
    try:
        httpd_server.serve_forever()
    except KeyboardInterrupt:
        pass

def main():
    global g_debug_mode
    if not config.load_init():
        return
    
    host = config.local_server_host
    port = config.local_server_port
    print(f"host: {host}")
    print(f"port: {port}")
    
    # Start Web UI server if enabled
    webui_server = None
    if HAS_WEBUI and WebUIServer and config.webui_enabled:
        try:
            webui_server = WebUIServer(host=config.webui_host, port=config.webui_port)
            webui_server.start()
            print(f"Web UI started on http://{config.webui_host}:{config.webui_port}")
            
            # Try to open browser automatically
            try:
                import webbrowser
                webbrowser.open(f"http://{config.webui_host}:{config.webui_port}")
            except:
                pass
        except Exception as e:
            print(f"Failed to start Web UI: {e}")
    
    server_class = http.server.HTTPServer
    httpd = server_class((host, port), APIHandler)
    
    if "--debug-extra" in sys.argv:
        g_debug_mode = 2
    elif "--debug" in sys.argv:
        g_debug_mode = 1

    print("server start")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
    if webui_server:
        webui_server.stop()
    print('end')

if __name__ == "__main__":
    main()
