"""
Local Translation Providers Module

Provides offline translation services:
- Ollama LLM (Llama, Mistral, Gemma)
- vLLM (high-performance)
"""

from typing import Dict, Any, Optional
import json
import http.client

from . import config


class LocalTranslationProvider:
    """Base class for local translation providers"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError


class OllamaTranslationProvider(LocalTranslationProvider):
    """Ollama LLM translation provider (CPU-friendly, lightweight)"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        texts = [blk.get("source_text", blk.get("text", "")) for blk in blocks]
        
        model = config.ollama_translation_model or "llama3.1:8b"
        
        texts_formatted = "\n".join([f"{i}: {t}" for i, t in enumerate(texts)])
        
        prompt = f"""Translate these texts from {source_lang or 'auto'} to {target_lang}. Return JSON array in this exact format:
[{{"index": 0, "translation": "translated text"}}, ...]

Texts to translate:
{texts_formatted}

Translate accurately while preserving meaning and tone."""
        
        req = {
            "model": model,
            "prompt": prompt,
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
        
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        try:
            conn = http.client.HTTPConnection(host, port, timeout=config.ollama_timeout)
            conn.request("POST", uri, body, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            
            output = json.loads(data)
            
            if "error" in output:
                print("Ollama translation error:", output["error"])
                return {"blocks": blocks}
            
            try:
                content = output.get("response", "")
                translations = json.loads(content)
                
                if isinstance(translations, dict) and "translations" in translations:
                    translations = translations["translations"]
                
                for tr in translations:
                    idx = tr.get("index", 0)
                    translated_text = tr.get("translation", "")
                    if idx < len(blocks):
                        if not isinstance(blocks[idx].get("translation"), dict):
                            blocks[idx]["translation"] = {}
                        blocks[idx]["translation"][target_lang.lower()] = translated_text
                        blocks[idx]["target_lang"] = target_lang
            except (KeyError, json.JSONDecodeError) as e:
                print("Failed to parse Ollama translation:", e)
            
            return {"blocks": blocks}
            
        except Exception as e:
            print(f"Ollama connection failed: {e}")
            return {"blocks": blocks}


class VLLMTranslationProvider(LocalTranslationProvider):
    """vLLM translation provider (GPU, high-performance)"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        texts = [blk.get("source_text", blk.get("text", "")) for blk in blocks]
        
        model = config.vllm_translation_model or "meta-llama/Llama-3.1-70B-Instruct"
        
        texts_formatted = "\n".join([f"{i}: {t}" for i, t in enumerate(texts)])
        
        prompt = f"""Translate these texts from {source_lang or 'auto'} to {target_lang}. Return JSON array in this exact format:
[{{"index": 0, "translation": "translated text"}}, ...]

Texts to translate:
{texts_formatted}

Translate accurately while preserving meaning and tone."""
        
        # vLLM uses OpenAI-compatible API
        req = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional translator."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        
        base_url = config.vllm_base_url or "http://localhost:8000/v1"
        import urllib.parse
        parsed_url = urllib.parse.urlparse(base_url)
        host = parsed_url.netloc
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
        uri = f"{parsed_url.path.rstrip('/')}/chat/completions"
        
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        try:
            conn = http.client.HTTPConnection(host, port, timeout=config.vllm_timeout)
            conn.request("POST", uri, body, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            
            output = json.loads(data)
            
            if "error" in output:
                print("vLLM translation error:", output["error"])
                return {"blocks": blocks}
            
            try:
                content = output["choices"][0]["message"]["content"]
                translations = json.loads(content)
                
                if isinstance(translations, dict) and "translations" in translations:
                    translations = translations["translations"]
                
                for tr in translations:
                    idx = tr.get("index", 0)
                    translated_text = tr.get("translation", "")
                    if idx < len(blocks):
                        if not isinstance(blocks[idx].get("translation"), dict):
                            blocks[idx]["translation"] = {}
                        blocks[idx]["translation"][target_lang.lower()] = translated_text
                        blocks[idx]["target_lang"] = target_lang
            except (KeyError, json.JSONDecodeError) as e:
                print("Failed to parse vLLM translation:", e)
            
            return {"blocks": blocks}
            
        except Exception as e:
            print(f"vLLM connection failed: {e}")
            return {"blocks": blocks}


def get_local_translation_provider(provider_name: str) -> LocalTranslationProvider:
    """Get local translation provider by name"""
    providers = {
        "ollama": OllamaTranslationProvider,
        "vllm": VLLMTranslationProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown local translation provider: {provider_name}")
    
    return providers[provider_name]()
