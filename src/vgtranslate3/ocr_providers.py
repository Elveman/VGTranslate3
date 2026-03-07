"""
OCR Providers Module

Provides unified interface for OCR services:
- Google Vision
- Yandex Vision
- OpenAI Vision
- Gemini Vision
- Tesseract
"""

from typing import Tuple, Dict, Any, Optional
import json
import base64
import http.client
from PIL import Image

from . import config
from .util import load_image, image_to_string
from .bbox_extractor import extract_bounding_boxes, match_texts_to_boxes


class OCRProvider:
    """Base class for OCR providers"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Perform OCR on image.
        
        Returns: (structured_data, raw_response)
        """
        raise NotImplementedError


class GoogleOCRProvider(OCRProvider):
    """Google Vision OCR provider"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("ascii")
        else:
            image_b64 = image_data.split(",", 1)[-1]
        
        req = {
            "requests": [{
                "image": {"content": image_b64},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
            }]
        }
        if source_lang:
            req["requests"][0]["imageContext"] = {"languageHints": [source_lang]}
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        uri = f"/v1/images:annotate?key={config.local_server_ocr_key}"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        conn = http.client.HTTPSConnection("vision.googleapis.com", 443)
        conn.request("POST", uri, body, headers)
        response = conn.getresponse()
        output = json.loads(response.read())
        conn.close()
        
        if "error" in output:
            print("Google Vision error:", output["error"])
            return {}, output
        
        annotation = output.get("responses", [{}])[0].get("fullTextAnnotation", {})
        return annotation, output


class YandexOCRProvider(OCRProvider):
    """Yandex Vision OCR provider"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if isinstance(image_data, bytes):
            img_b64 = base64.b64encode(image_data).decode("ascii")
        else:
            img_b64 = image_data.split(",", 1)[-1]
        
        mime_type = "image/png"
        model = "page"
        
        spec = {
            "content": img_b64,
            "mimeType": mime_type,
            "model": model,
        }
        if source_lang:
            spec["languageCodes"] = [source_lang]
        else:
            spec["languageCodes"] = ["*"]
        
        body = json.dumps(spec, ensure_ascii=False).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": (
                f"Bearer {config.yandex_iam_token}" if config.yandex_iam_token
                else f"Api-Key {config.yandex_ocr_key}" if config.yandex_ocr_key
                else ValueError("Need iam_token or api_key")
            ),
            "x-folder-id": config.yandex_folder_id,
            "x-data-logging-enabled": "true",
        }
        
        conn = http.client.HTTPSConnection("ocr.api.cloud.yandex.net", 443)
        conn.request("POST", "/ocr/v1/recognizeText", body, headers)
        response = conn.getresponse()
        output = json.loads(response.read())
        conn.close()
        
        if "error" in output:
            print("Yandex OCR error:", output["error"])
            return {}, output
        
        annotation = output.get("result", {}).get("textAnnotation", {})
        return annotation, output


class OpenAIOCRProvider(OCRProvider):
    """OpenAI Vision OCR provider"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("ascii")
        else:
            image_b64 = image_data.split(",", 1)[-1]
        
        model = config.openai_ocr_model or config.openai_model
        
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
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }],
            "response_format": {"type": "json_object"},
            "max_tokens": 2000
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        
        import urllib.parse
        parsed_url = urllib.parse.urlparse(config.openai_base_url)
        host = parsed_url.netloc
        base_path = parsed_url.path.rstrip("/")
        uri = f"{base_path}/chat/completions"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {config.openai_api_key}"
        }
        
        if "routerai.ru" in config.openai_base_url:
            headers["X-Title"] = "VGTranslate3"
        
        conn = http.client.HTTPSConnection(host, 443, timeout=config.openai_timeout)
        conn.request("POST", uri, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        
        output = json.loads(data)
        
        if "error" in output:
            print("OpenAI Vision error:", output["error"])
            return {}, output
        
        try:
            content = output["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (KeyError, json.JSONDecodeError) as e:
            print("Failed to parse OpenAI response:", e)
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


class TesseractOCRProvider(OCRProvider):
    """Tesseract OCR provider with configurable pipeline"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        from . import ocr_tools
        from .util import reduce_to_multi_color, segfill
        
        ocr_processor = config.local_server_ocr_processor
        
        # Load processor config from file or dict
        if isinstance(ocr_processor, str):
            with open(ocr_processor, "r", encoding="utf-8") as fh:
                ocr_processor = json.load(fh)
        
        # Get language from config or parameter
        if not source_lang and ocr_processor.get("source_lang"):
            source_lang = ocr_processor["source_lang"]
        
        # Get PSM mode (default 6 - Uniform block of text)
        psm_mode = ocr_processor.get("psm_mode", 6)
        
        # Load and preprocess image
        palette = Image.Palette.ADAPTIVE
        image = load_image(image_data).convert("P", palette=palette)
        
        # Apply preprocessing pipeline
        for step in ocr_processor.get("pipeline", []):
            kwargs = step.get("options", {})
            action = step.get("action")
            
            if action == "reduceToMultiColor":
                image = reduce_to_multi_color(
                    image,
                    kwargs.get("base", "000000"),
                    kwargs.get("colors", [["FFFFFF", "FFFFFF"]]),
                    int(kwargs.get("threshold", 32))
                )
            elif action == "segFill":
                image = segfill(image, kwargs.get("base"), kwargs.get("color"))
            elif action == "contrast":
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(kwargs.get("factor", 2.0))
        
        # Get OCR data from Tesseract
        data = ocr_tools.tess_helper_data(
            image,
            lang=source_lang,
            mode=psm_mode,
            min_pixels=ocr_processor.get("min_pixels", 1)
        )
        
        # Convert to standard format
        blocks = []
        for block in data.get("blocks", []):
            # Convert bounding box format
            bb = block.get("bounding_box", {})
            bbox = {
                "x": bb.get("x1", 0),
                "y": bb.get("y1", 0),
                "width": bb.get("x2", 0) - bb.get("x1", 0),
                "height": bb.get("y2", 0) - bb.get("y1", 0)
            }
            
            blocks.append({
                "text": block.get("text", ""),
                "source_text": block.get("text", ""),
                "bounding_box": bbox,
                "language": source_lang or "unknown",
                "translation": {},
                "text_colors": ["FFFFFF"],
                "confidence": block.get("confidence", 1.0)
            })
        
        result = {
            "blocks": blocks,
            "detected_language": source_lang or "unknown"
        }
        
        return result, {"source_lang": source_lang}


class GeminiOCRProvider(OCRProvider):
    """Google Gemini Vision OCR provider"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("ascii")
        else:
            image_b64 = image_data.split(",", 1)[-1]
        
        api_key = config.gemini_api_key
        
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
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": image_b64}}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "max_output_tokens": 2000
            }
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        
        model = config.gemini_model or "gemini-1.5-flash"
        uri = f"/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        conn = http.client.HTTPSConnection("generativelanguage.googleapis.com", 443, timeout=config.openai_timeout)
        conn.request("POST", uri, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        
        output = json.loads(data)
        
        if "error" in output:
            print("Gemini Vision error:", output["error"])
            return {}, output
        
        try:
            content = output["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(content)
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            print("Failed to parse Gemini response:", e)
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


def get_ocr_provider(provider_name: str) -> OCRProvider:
    """Get OCR provider by name"""
    providers = {
        "google": GoogleOCRProvider,
        "yandex": YandexOCRProvider,
        "openai": OpenAIOCRProvider,
        "gemini": GeminiOCRProvider,
        "tesseract": TesseractOCRProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown OCR provider: {provider_name}")
    
    return providers[provider_name]()
