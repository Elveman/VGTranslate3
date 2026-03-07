#!/usr/bin/env python3
"""
Test script to verify provider functionality with and without API keys.

Usage:
    python test_providers.py [--all] [--local] [--cloud]
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vgtranslate3 import config
from vgtranslate3 import ocr_providers
from vgtranslate3 import translation_providers
from vgtranslate3 import local_ocr_providers
from vgtranslate3 import local_translation_providers


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.status = "pending"
        self.error = None
    
    def success(self):
        self.status = "✓ PASS"
    
    def fail(self, error: str):
        self.status = "✗ FAIL"
        self.error = error
    
    def skip(self, reason: str):
        self.status = "⊘ SKIP"
        self.error = reason
    
    def __str__(self):
        result = f"{self.status}: {self.name}"
        if self.error:
            result += f" ({self.error})"
        return result


def test_config_loading():
    """Test that config loads without errors"""
    result = TestResult("Config loading")
    try:
        # Check that config module loads
        assert hasattr(config, 'openai_api_key')
        assert hasattr(config, 'ollama_base_url')
        assert hasattr(config, 'vllm_base_url')
        result.success()
    except Exception as e:
        result.fail(str(e))
    return result


def test_ocr_providers_availability():
    """Test that OCR providers can be instantiated"""
    results = []
    
    providers = ['google', 'yandex', 'openai', 'gemini', 'tesseract']
    for provider_name in providers:
        result = TestResult(f"OCR Provider: {provider_name}")
        try:
            provider = ocr_providers.get_ocr_provider(provider_name)
            result.success()
        except Exception as e:
            result.fail(str(e))
        results.append(result)
    
    return results


def test_translation_providers_availability():
    """Test that translation providers can be instantiated"""
    results = []
    
    providers = ['google', 'yandex', 'openai', 'deepseek', 'groq', 'gemini']
    for provider_name in providers:
        result = TestResult(f"Translation Provider: {provider_name}")
        try:
            provider = translation_providers.get_translation_provider(provider_name)
            result.success()
        except Exception as e:
            result.fail(str(e))
        results.append(result)
    
    return results


def test_local_ocr_providers_availability():
    """Test that local OCR providers can be instantiated"""
    results = []
    
    providers = ['ollama', 'vllm']
    for provider_name in providers:
        result = TestResult(f"Local OCR Provider: {provider_name}")
        try:
            provider = local_ocr_providers.get_local_ocr_provider(provider_name)
            result.success()
        except Exception as e:
            result.fail(str(e))
        results.append(result)
    
    return results


def test_local_translation_providers_availability():
    """Test that local translation providers can be instantiated"""
    results = []
    
    providers = ['ollama', 'vllm']
    for provider_name in providers:
        result = TestResult(f"Local Translation Provider: {provider_name}")
        try:
            provider = local_translation_providers.get_local_translation_provider(provider_name)
            result.success()
        except Exception as e:
            result.fail(str(e))
        results.append(result)
    
    return results


def test_api_keys_configured():
    """Test which API keys are configured"""
    results = []
    
    # Cloud providers
    cloud_keys = {
        'OpenAI': config.openai_api_key,
        'DeepSeek': config.deepseek_api_key,
        'Groq': config.groq_api_key,
        'Gemini': config.gemini_api_key,
        'Google OCR': config.local_server_ocr_key,
        'Google Translate': config.local_server_translation_key,
        'Yandex OCR': config.yandex_ocr_key,
        'Yandex Translate': config.yandex_translation_key,
        'Yandex IAM': config.yandex_iam_token,
    }
    
    for provider, key in cloud_keys.items():
        result = TestResult(f"API Key: {provider}")
        if key and key not in ["", "YOUR_API_KEY_HERE", "sk-...", "sk-or-...", "ra_", "grq_"]:
            result.success()
        else:
            result.skip("Not configured")
        results.append(result)
    
    # Local providers (check if servers are accessible would require network calls)
    local_configs = {
        'Ollama URL': config.ollama_base_url,
        'vLLM URL': config.vllm_base_url,
    }
    
    for provider, url in local_configs.items():
        result = TestResult(f"Local Config: {provider}")
        if url:
            result.success()
        else:
            result.skip("Not configured")
        results.append(result)
    
    return results


def test_config_files_exist():
    """Test that example config files exist"""
    results = []
    
    config_dir = Path(__file__).parent.parent / "config_example"
    expected_configs = [
        'config_openai.json',
        'config_routerai.json',
        'config_openrouter.json',
        'config_deepseek_gemini.json',
        'config_groq_gemini.json',
        'config_tesseract_google.json',
        'config_tesseract_rus.json',
        'config_ollama_local.json',
        'config_vllm_local.json',
        'config_hybrid_ollama_groq.json',
    ]
    
    for config_file in expected_configs:
        result = TestResult(f"Config file: {config_file}")
        if (config_dir / config_file).exists():
            result.success()
        else:
            result.fail("File not found")
        results.append(result)
    
    return results


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r.status == "✓ PASS")
    failed = sum(1 for r in results if r.status == "✗ FAIL")
    skipped = sum(1 for r in results if r.status == "⊘ SKIP")
    
    for result in results:
        print(result)
    
    print("\n" + "="*60)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print("="*60)
    
    return failed == 0


def main():
    print("VGTranslate3 Provider Tests")
    print("="*60)
    
    all_results = []
    
    # Basic tests
    all_results.append(test_config_loading())
    all_results.extend(test_config_files_exist())
    
    # Provider availability tests
    all_results.extend(test_ocr_providers_availability())
    all_results.extend(test_translation_providers_availability())
    all_results.extend(test_local_ocr_providers_availability())
    all_results.extend(test_local_translation_providers_availability())
    
    # API key tests
    all_results.extend(test_api_keys_configured())
    
    # Print summary
    success = print_summary(all_results)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
