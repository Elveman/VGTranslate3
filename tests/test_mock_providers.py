#!/usr/bin/env python3
"""
Mock tests for OCR and Translation providers.

These tests use mock data and don't require API keys.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import base64
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vgtranslate3 import config
from vgtranslate3 import ocr_providers
from vgtranslate3 import translation_providers


class TestMockOCRProviders(unittest.TestCase):
    """Test OCR providers with mock data"""
    
    def test_openai_ocr_mock_response(self):
        """Test OpenAI OCR with mocked response"""
        provider = ocr_providers.OpenAIOCRProvider()
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "blocks": [
                            {
                                "text": "こんにちは",
                                "bbox": {"x": 10, "y": 20, "width": 100, "height": 20},
                                "language": "jpn"
                            }
                        ],
                        "detected_language": "jpn"
                    })
                }
            }]
        }
        
        # Create a simple test image (1x1 white pixel)
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        image_data = img_bytes.read()
        
        with patch('http.client.HTTPSConnection') as mock_conn:
            mock_response_obj = Mock()
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_conn.return_value.getresponse.return_value = mock_response_obj
            
            result, raw = provider.recognize(image_data, "jpn")
            
            self.assertIn("blocks", result)
            self.assertEqual(len(result["blocks"]), 1)
            self.assertEqual(result["blocks"][0]["text"], "こんにちは")
            self.assertEqual(result["detected_language"], "jpn")
    
    def test_gemini_ocr_mock_response(self):
        """Test Gemini OCR with mocked response"""
        provider = ocr_providers.GeminiOCRProvider()
        
        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "blocks": [
                                {
                                    "text": "Hello World",
                                    "bbox": {"x": 5, "y": 10, "width": 80, "height": 15}
                                }
                            ],
                            "detected_language": "eng"
                        })
                    }]
                }
            }]
        }
        
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        image_data = img_bytes.read()
        
        with patch('http.client.HTTPSConnection') as mock_conn:
            mock_response_obj = Mock()
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_conn.return_value.getresponse.return_value = mock_response_obj
            
            result, raw = provider.recognize(image_data, "eng")
            
            self.assertIn("blocks", result)
            self.assertEqual(len(result["blocks"]), 1)
            self.assertEqual(result["blocks"][0]["text"], "Hello World")
    
    def test_tesseract_ocr_format(self):
        """Test Tesseract OCR output format"""
        provider = ocr_providers.TesseractOCRProvider()
        
        # Mock config
        config.local_server_ocr_processor = {
            "source_lang": "eng",
            "psm_mode": 6,
            "min_pixels": 1,
            "pipeline": []
        }
        
        # Mock ocr_tools
        mock_data = {
            "blocks": [
                {
                    "text": "Test text",
                    "bounding_box": {"x1": 10, "y1": 20, "x2": 100, "y2": 40}
                }
            ]
        }
        
        with patch('vgtranslate3.ocr_tools.tess_helper_data', return_value=mock_data):
            with patch('vgtranslate3.ocr_providers.load_image') as mock_load:
                from PIL import Image
                mock_load.return_value = Image.new('RGB', (100, 100))
                
                result, raw = provider.recognize(b"fake_image_data", "eng")
                
                self.assertIn("blocks", result)
                self.assertEqual(len(result["blocks"]), 1)
                self.assertEqual(result["blocks"][0]["source_text"], "Test text")
                self.assertIn("bounding_box", result["blocks"][0])


class TestMockTranslationProviders(unittest.TestCase):
    """Test translation providers with mock data"""
    
    def test_openai_translation_mock_response(self):
        """Test OpenAI translation with mocked response"""
        provider = translation_providers.OpenAITranslationProvider()
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {"index": 0, "translation": "Hello"},
                        {"index": 1, "translation": "World"}
                    ])
                }
            }]
        }
        
        blocks = [
            {"source_text": "こんにちは", "translation": {}},
            {"source_text": "世界", "translation": {}}
        ]
        
        with patch('http.client.HTTPSConnection') as mock_conn:
            mock_response_obj = Mock()
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_conn.return_value.getresponse.return_value = mock_response_obj
            
            result = provider.translate(blocks, "en", "ja")
            
            self.assertIn("blocks", result)
            self.assertEqual(len(result["blocks"]), 2)
            self.assertEqual(result["blocks"][0]["translation"]["en"], "Hello")
            self.assertEqual(result["blocks"][1]["translation"]["en"], "World")
    
    def test_deepseek_translation_mock_response(self):
        """Test DeepSeek translation with mocked response"""
        provider = translation_providers.DeepSeekTranslationProvider()
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {"index": 0, "translation": "Привет"}
                    ])
                }
            }]
        }
        
        blocks = [{"source_text": "Hello", "translation": {}}]
        
        with patch('http.client.HTTPSConnection') as mock_conn:
            mock_response_obj = Mock()
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_conn.return_value.getresponse.return_value = mock_response_obj
            
            result = provider.translate(blocks, "ru", "en")
            
            self.assertIn("blocks", result)
            self.assertEqual(result["blocks"][0]["translation"]["ru"], "Привет")
    
    def test_groq_translation_mock_response(self):
        """Test Groq translation with mocked response"""
        provider = translation_providers.GroqTranslationProvider()
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {"index": 0, "translation": "Hallo"}
                    ])
                }
            }]
        }
        
        blocks = [{"source_text": "Hello", "translation": {}}]
        
        with patch('http.client.HTTPSConnection') as mock_conn:
            mock_response_obj = Mock()
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_conn.return_value.getresponse.return_value = mock_response_obj
            
            result = provider.translate(blocks, "de", "en")
            
            self.assertIn("blocks", result)
            self.assertEqual(result["blocks"][0]["translation"]["de"], "Hallo")


class TestProviderFallbacks(unittest.TestCase):
    """Test fallback mechanisms"""
    
    def test_bbox_fallback_with_no_bbox(self):
        """Test bounding box fallback when model doesn't return bbox"""
        from vgtranslate3.bbox_extractor import extract_bounding_boxes
        from PIL import Image
        
        # Create simple test image with clear text region
        img = Image.new('RGB', (200, 50), color='white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 190, 40], fill='black')
        
        boxes = extract_bounding_boxes(img)
        
        # Should detect at least one bounding box
        self.assertGreater(len(boxes), 0)
        self.assertIn("x", boxes[0])
        self.assertIn("y", boxes[0])
        self.assertIn("w", boxes[0])
        self.assertIn("h", boxes[0])
    
    def test_translation_with_empty_blocks(self):
        """Test translation handles empty blocks gracefully"""
        provider = translation_providers.OpenAITranslationProvider()
        
        blocks = []
        
        # Should not crash with empty blocks
        result = provider.translate(blocks, "en", "ja")
        self.assertEqual(result["blocks"], [])
    
    def test_ocr_with_invalid_image(self):
        """Test OCR handles invalid image gracefully"""
        provider = ocr_providers.OpenAIOCRProvider()
        
        # Mock error response
        mock_response = {"error": {"message": "Invalid image"}}
        
        with patch('http.client.HTTPSConnection') as mock_conn:
            mock_response_obj = Mock()
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_conn.return_value.getresponse.return_value = mock_response_obj
            
            result, raw = provider.recognize(b"invalid_image_data", "en")
            
            # Should return empty result, not crash
            self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
