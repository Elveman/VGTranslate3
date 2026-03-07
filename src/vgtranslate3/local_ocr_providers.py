"""
Local OCR Providers Module

Provides offline OCR services:
- Ollama OCR (via LLaVA)
- vLLM OCR (via LLaVA)
"""

from typing import Tuple, Dict, Any, Optional
import json
import base64
import http.client
from PIL import Image

from . import config
from .util import load_image, image_to_string
from .bbox_extractor import extract_bounding_boxes, match_texts_to_boxes


class LocalOCRProvider:
    """Base class for local OCR providers"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        raise NotImplementedError


class OllamaOCRProvider(LocalOCRProvider):
    """Ollama LLaVA OCR provider (lightweight, CPU-friendly)"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("ascii")
        else:
            image_b64 = image_data.split(",", 1)[-1]
        
        # Use LLaVA model for vision OCR
        model = config.ollama_ocr_model or "llava:7b"
        
        prompt = """Extract all text from this image. Return JSON in this exact format:
{
  "blocks": [
    {
      "text": "original text",
      "bbox": {"x": 0, "y": 0, "width": 100, "height": 20},
      "language": "detected language code"
    }
  ],
  "detected_language": "language code"
}

If you cannot detect bounding boxes, omit them. Source language hint: """ + (source_lang or "auto")
        
        req = {
            "model": model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "format": "json"
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        
        base_url = config.ollama_base_url or "http://localhost:11434"
        import urllib.parse
        parsed_url = urllib.parse.urlparse(base_url)
        host = parsed_url.netloc
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
        uri = f"{parsed_url.path.rstrip('/')}/api/generate"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            conn = http.client.HTTPConnection(host, port, timeout=config.ollama_timeout)
            conn.request("POST", uri, body, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            
            output = json.loads(data)
            
            if "error" in output:
                print("Ollama OCR error:", output["error"])
                return {}, output
            
            try:
                content = output.get("response", "")
                result = json.loads(content)
            except (json.JSONDecodeError, KeyError) as e:
                print("Failed to parse Ollama response:", e)
                return {}, output
            
            if "blocks" not in result:
                result = {"blocks": [], "detected_language": source_lang or "unknown"}
            
            has_bbox = any("bbox" in block and block["bbox"].get("width", 0) > 0 
                           for block in result.get("blocks", []))
            
            if not has_bbox and config.use_bbox_fallback:
                try:
                    img = load_image(image_data)
                    fallback_boxes = extract_bounding_boxes(img)
                    texts = [block.get("text", "") for block in result.get("blocks", [])]
                    
                    if texts and fallback_boxes:
                        matched = match_texts_to_boxes(texts, fallback_boxes)
                        for i, block in enumerate(result.get("blocks", [])):
                            if i < len(matched):
                                bb = matched[i]["bbox"]
                                block["bbox"] = {
                                    "vertices": [
                                        {"x": bb["x"], "y": bb["y"]},
                                        {"x": bb["x"] + bb["w"], "y": bb["y"]},
                                        {"x": bb["x"] + bb["w"], "y": bb["y"] + bb["h"]},
                                        {"x": bb["x"], "y": bb["y"] + bb["h"]}
                                    ]
                                }
                except Exception as e:
                    print("Bbox fallback failed:", e)
            
            return result, output
            
        except Exception as e:
            print(f"Ollama connection failed: {e}")
            return {"blocks": [], "detected_language": "unknown"}, {}


class VLLMOCRProvider(LocalOCRProvider):
    """vLLM LLaVA OCR provider (high-performance, GPU)"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("ascii")
        else:
            image_b64 = image_data.split(",", 1)[-1]
        
        # Use LLaVA model for vision OCR
        model = config.vllm_ocr_model or "llava-hf/llava-1.5-7b-hf"
        
        prompt = """Extract all text from this image. Return JSON in this exact format:
{
  "blocks": [
    {
      "text": "original text",
      "bbox": {"x": 0, "y": 0, "width": 100, "height": 20},
      "language": "detected language code"
    }
  ],
  "detected_language": "language code"
}

Source language hint: """ + (source_lang or "auto")
        
        # vLLM uses OpenAI-compatible API
        req = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }],
            "max_tokens": 2000
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        
        base_url = config.vllm_base_url or "http://localhost:8000/v1"
        import urllib.parse
        parsed_url = urllib.parse.urlparse(base_url)
        host = parsed_url.netloc
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
        uri = f"{parsed_url.path.rstrip('/')}/chat/completions"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            conn = http.client.HTTPConnection(host, port, timeout=config.vllm_timeout)
            conn.request("POST", uri, body, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            
            output = json.loads(data)
            
            if "error" in output:
                print("vLLM OCR error:", output["error"])
                return {}, output
            
            try:
                content = output["choices"][0]["message"]["content"]
                result = json.loads(content)
            except (KeyError, json.JSONDecodeError) as e:
                print("Failed to parse vLLM response:", e)
                return {}, output
            
            if "blocks" not in result:
                result = {"blocks": [], "detected_language": source_lang or "unknown"}
            
            has_bbox = any("bbox" in block and block["bbox"].get("width", 0) > 0 
                           for block in result.get("blocks", []))
            
            if not has_bbox and config.use_bbox_fallback:
                try:
                    img = load_image(image_data)
                    fallback_boxes = extract_bounding_boxes(img)
                    texts = [block.get("text", "") for block in result.get("blocks", [])]
                    
                    if texts and fallback_boxes:
                        matched = match_texts_to_boxes(texts, fallback_boxes)
                        for i, block in enumerate(result.get("blocks", [])):
                            if i < len(matched):
                                bb = matched[i]["bbox"]
                                block["bbox"] = {
                                    "vertices": [
                                        {"x": bb["x"], "y": bb["y"]},
                                        {"x": bb["x"] + bb["w"], "y": bb["y"]},
                                        {"x": bb["x"] + bb["w"], "y": bb["y"] + bb["h"]},
                                        {"x": bb["x"], "y": bb["y"] + bb["h"]}
                                    ]
                                }
                except Exception as e:
                    print("Bbox fallback failed:", e)
            
            return result, output
            
        except Exception as e:
            print(f"vLLM connection failed: {e}")
            return {"blocks": [], "detected_language": "unknown"}, {}


def get_local_ocr_provider(provider_name: str) -> LocalOCRProvider:
    """Get local OCR provider by name"""
    providers = {
        "ollama": OllamaOCRProvider,
        "vllm": VLLMOCRProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown local OCR provider: {provider_name}")
    
    return providers[provider_name]()
