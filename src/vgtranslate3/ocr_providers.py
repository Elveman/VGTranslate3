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
    """OpenAI Vision OCR provider - compatible with RouterAI API"""
    
    def recognize(self, image_data: bytes | str, source_lang: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("ascii")
            mime_type = "image/png"  # Default, will be detected below
        else:
            image_b64 = image_data.split(",", 1)[-1]
            mime_type = "image/png"
        
        # Detect actual MIME type from image bytes
        if isinstance(image_data, bytes):
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_data))
                if img.format:
                    if img.format.lower() == "jpeg":
                        mime_type = "image/jpeg"
                    elif img.format.lower() == "webp":
                        mime_type = "image/webp"
                    elif img.format.lower() == "gif":
                        mime_type = "image/gif"
            except:
                pass
        
        model = config.openai_ocr_model or config.openai_model
        
        # Get image dimensions for accurate bbox coordinates
        img_width = 0
        img_height = 0
        if isinstance(image_data, bytes):
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_data))
                img_width, img_height = img.width, img.height
            except:
                pass
        
        # Improved prompt for better OCR results with RouterAI vision models
        prompt = f"""You are an OCR expert. Extract ALL text from this image with high accuracy.

Image dimensions: {img_width}x{img_height} pixels

Return ONLY valid JSON in this exact format:
{{
  "blocks": [
    {{
      "text": "exact text from image",
      "bbox": {{"x": 0, "y": 0, "width": 100, "height": 20}},
      "language": "3-letter ISO code (e.g., eng, jpn, rus)"
    }}
  ],
  "detected_language": "primary 3-letter ISO code"
}}

CRITICAL REQUIREMENTS:
- Bounding box coordinates MUST be in PIXELS relative to the original image ({img_width}x{img_height})
- Do NOT use relative coordinates (0-1) or percentages
- Do NOT scale coordinates - use exact pixel values
- Preserve original text EXACTLY (no corrections)
- Include ALL text blocks visible in the image
- Use 3-letter ISO 639-3 language codes (eng, jpn, rus, chi, kor, etc.)
- If bounding boxes cannot be determined, omit bbox field
- Detected source language: """ + (source_lang or "auto") + """

Return ONLY the JSON, no explanations before or after.
Start and end your answer with requested JSON's brackets.
If no text is detected, return an empty JSON.
Treat it as a function return. Any additional data not related to JSON is garbage data."""
        
        req = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
                ]
            }],
            "response_format": {"type": "json_object"},
            "max_tokens": 3000
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
        
        print(f"\n📊 OCR API Response:")
        print(f"  Status: {response.status}")
        output = json.loads(data)
        
        # Log full API response for debugging
        if "error" in output:
            print(f"❌ OpenAI Vision ERROR: {output['error']}")
        else:
            print(f"✓ OCR API call successful")
            # Log the raw content for inspection
            try:
                content = output.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"\n📄 OCR Raw Response ({len(content)} chars):")
                print("=" * 70)
                print(content[:3000])  # First 3000 chars
                print("=" * 70)
            except Exception as e:
                print(f"Failed to extract content: {e}")
        
        if "error" in output:
            print("OpenAI Vision error:", output["error"])
            return {}, output
        
        try:
            content = output["choices"][0]["message"]["content"]
            result = json.loads(content)
            print(f"\n✓ OCR parsed {len(result.get('blocks', []))} text blocks")
        except (KeyError, json.JSONDecodeError) as e:
            print("Failed to parse OpenAI response:", e)
            return {}, output
        
        if "blocks" not in result:
            result = {"blocks": [], "detected_language": source_lang or "unknown"}
        
        # Normalize bbox field names to bounding_box for compatibility
        for block in result.get("blocks", []):
            if "bbox" in block and "bounding_box" not in block:
                bbox = block["bbox"]
                # Skip blocks with None or empty bbox
                if not bbox:
                    continue
                # Support different bbox formats
                if "width" in bbox:
                    # Check if coordinates need to be scaled down
                    # RouterAI/Gemini may scale images internally (e.g., to 1024x1024)
                    x = bbox.get("x", 0)
                    y = bbox.get("y", 0)
                    w = bbox.get("width", 0)
                    h = bbox.get("height", 0)
                    
                    # Detect if coordinates are scaled (much larger than original image)
                    if img_width > 0 and img_height > 0:
                        # If bbox width is larger than image width, coordinates are scaled
                        if w > img_width * 1.5:
                            scale_x = w / img_width
                            scale_y = h / img_height if h > img_height else scale_x
                            print(f"Detected scaled coordinates (scale: ~{scale_x:.2f}x), converting back to original size")
                            x = int(x / scale_x)
                            y = int(y / scale_y)
                            w = int(w / scale_x)
                            h = int(h / scale_y)
                        # Also check for relative coordinates (0-1 range)
                        elif isinstance(x, float) and x < 1.0:
                            x = int(x * img_width)
                            y = int(y * img_height)
                            w = int(w * img_width)
                            h = int(h * img_height)
                    
                    block["bounding_box"] = {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h
                    }
                elif "vertices" in bbox:
                    # Format: {vertices: [{x,y}, ...]}
                    verts = bbox["vertices"]
                    if len(verts) >= 4:
                        x1 = min(v["x"] for v in verts)
                        y1 = min(v["y"] for v in verts)
                        x2 = max(v["x"] for v in verts)
                        y2 = max(v["y"] for v in verts)
                        
                        # Convert relative to absolute if needed
                        if img_width > 0 and img_height > 0:
                            if isinstance(x1, float) and x1 < 1.0:
                                x1 = int(x1 * img_width)
                                y1 = int(y1 * img_height)
                                x2 = int(x2 * img_width)
                                y2 = int(y2 * img_height)
                        
                        block["bounding_box"] = {
                            "x1": x1, "y1": y1, "x2": x2, "y2": y2
                        }
                elif "x1" in bbox:
                    # Already in bounding_box format
                    block["bounding_box"] = bbox
        
        # Add image dimensions to result for client-side scaling
        if img_width > 0 and img_height > 0:
            result["image_size"] = {"width": img_width, "height": img_height}
        
        has_bbox = any("bounding_box" in block and block["bounding_box"].get("w", 0) > 0 
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
