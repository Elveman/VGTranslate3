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
    color_hex_to_byte
)
from . import screen_translate
from . import ocr_providers
from . import translation_providers
from .text_to_speech import TextToSpeech


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
        
        image_object = load_image(image_data).convert("RGB")
        print(f"w: {image_object.width} h: {image_object.height}")
        
        if pixel_format == "BGR":
            image_object = swap_red_blue(image_object)
        
        # Handle legacy providers
        if config.local_server_api_key_type == "free":
            return {"error": "Free tier not implemented"}
        
        elif config.local_server_api_key_type == "ztranslate":
            return self._handle_ztranslate(body, image_object, source_lang, target_lang, mode, request_output)
        
        # Modern pipeline with separated providers
        return self._handle_modern_pipeline(
            body, image_object, image_data, source_lang, target_lang,
            mode, request_output, request_out_dict, alpha, pixel_format
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
                               image_data, source_lang: str, target_lang: str,
                               mode: str, request_output: List[str],
                               request_out_dict: Dict, alpha: bool,
                               pixel_format: str) -> Dict:
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
        
        # OCR Stage
        print(f"Using OCR provider: {ocr_provider_name}")
        ocr_provider = ocr_providers.get_ocr_provider(ocr_provider_name)
        
        if ocr_provider_name == "tesseract":
            data, raw_output = ocr_provider.recognize(image_data, source_lang)
            source_lang = raw_output.get("source_lang", source_lang)
        else:
            data, raw_output = ocr_provider.recognize(image_data, source_lang)
        
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
        data = translation_provider.translate(data.get("blocks", []), target_lang, source_lang)
        
        # TTS Stage
        if "sound" in request_out_dict and data.get("blocks"):
            try:
                texts = []
                for block in sorted(data['blocks'], key=lambda x: (x.get('bounding_box', {}).get('y', 0), x.get('bounding_box', {}).get('x', 0))):
                    text = block.get('translation', {}).get(target_lang.lower(), '')
                    texts.append(text)
                
                text_to_say = " ".join(texts).replace("...", " [] ")
                
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
        
        # Image generation
        if window_obj:
            output_image = imaging.ImageModder.write(image_object, data, target_lang)
            window_obj.load_image_object(output_image)
            window_obj.curr_image = imaging.ImageIterator.prev()
        
        if "image" in request_out_dict:
            if alpha:
                image_object = Image.new("RGBA", (image_object.width, image_object.height), (0, 0, 0, 0))
            
            output_image = imaging.ImageModder.write(image_object, data, target_lang)
            
            if pixel_format == "BGR":
                output_image = output_image.convert("RGB")
                output_image = swap_red_blue(output_image)
            
            output_data["image"] = image_to_string_format(output_image, request_out_dict['image'], mode="RGBA")
        
        if error_string:
            output_data['error'] = error_string
        
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
    print('end')

if __name__ == "__main__":
    main()
