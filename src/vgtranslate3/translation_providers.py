"""
Translation Providers Module

Provides unified interface for translation services:
- Google Translate
- Yandex Translate
- OpenAI Chat Completions
- DeepSeek Chat
- Groq Chat
- Gemini Chat
"""

from typing import Dict, Any, Optional
import json
import http.client
from html import unescape

from . import config


class TranslationProvider:
    """Base class for translation providers"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Translate text blocks.
        
        Returns: updated blocks with translations
        """
        raise NotImplementedError


class GoogleTranslationProvider(TranslationProvider):
    """Google Translate provider"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        from .util import lang_2_to_3
        
        texts = [blk["source_text"] for blk in blocks]
        
        uri = "/language/translate/v2?key=" + config.local_server_translation_key
        
        body = '{\n'
        for string in texts:
            body += "'q': " + json.dumps(string) + ",\n"
        body += "'target': '" + target_lang + "'\n"
        body += '}'
        
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        conn = http.client.HTTPSConnection("translation.googleapis.com", 443)
        conn.request("POST", uri, body, headers)
        response = conn.getresponse()
        output = json.loads(response.read())
        conn.close()
        
        if "error" in output:
            print(output['error'])
            return {"blocks": blocks}
        
        for x in output['data']['translations']:
            x['translatedText'] = unescape(x['translatedText'])
        
        new_blocks = []
        for blk, tr in zip(blocks, output['data']['translations']):
            if not isinstance(blk.get("translation"), dict):
                blk["translation"] = {}
            
            blk["translation"][target_lang.lower()] = tr["translatedText"]
            blk["target_lang"] = target_lang
            blk["language"] = tr.get("detectedSourceLanguage", "")
            
            if source_lang and blk["language"]:
                if source_lang != lang_2_to_3.get(blk["language"], ""):
                    continue
            
            new_blocks.append(blk)
        
        return {"blocks": new_blocks}


class YandexTranslationProvider(TranslationProvider):
    """Yandex Translate provider"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        from .util import lang_2_to_3
        
        texts = [blk["source_text"] for blk in blocks]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": (
                f"Bearer {config.yandex_iam_token}" if config.yandex_iam_token
                else f"Api-Key {config.yandex_translation_key}" if config.yandex_translation_key
                else ValueError("Need iam_token or api_key")
            )
        }
        
        body_dict = {
            "folderId": config.yandex_folder_id,
            "texts": texts,
            "targetLanguageCode": target_lang,
            "format": "PLAIN_TEXT"
        }
        if source_lang:
            body_dict["sourceLanguageCode"] = source_lang
        
        body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
        
        conn = http.client.HTTPSConnection("translate.api.cloud.yandex.net", 443)
        conn.request("POST", "/translate/v2/translate", body, headers)
        response = conn.getresponse()
        output = json.loads(response.read())
        conn.close()
        
        if "error" in output:
            print(output["error"])
            return {"blocks": blocks}
        
        for x in output["translations"]:
            x["text"] = unescape(x["text"])
        
        new_blocks = []
        for blk, tr in zip(blocks, output["translations"]):
            if not isinstance(blk.get("translation"), dict):
                blk["translation"] = {}
            
            blk["translation"][target_lang.lower()] = tr["text"]
            blk["target_lang"] = target_lang
            blk["language"] = tr.get("detectedLanguageCode", "")
            
            if source_lang and blk["language"]:
                if source_lang != lang_2_to_3.get(blk["language"], ""):
                    continue
            
            new_blocks.append(blk)
        
        return {"blocks": new_blocks}


class OpenAITranslationProvider(TranslationProvider):
    """OpenAI Chat Completions translation provider"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        # Ensure blocks is a list of dicts, not strings
        if not blocks or not isinstance(blocks, list):
            print(f"Warning: Invalid blocks format: {type(blocks)}")
            return {"blocks": []}
        
        # Extract texts from blocks (support both dict and string formats)
        texts = []
        for blk in blocks:
            if isinstance(blk, dict):
                texts.append(blk.get("source_text", blk.get("text", "")))
            elif isinstance(blk, str):
                texts.append(blk)
            else:
                texts.append(str(blk))
        
        model = config.openai_translation_model or config.openai_model
        detected_source = source_lang or 'auto'
        
        print(f"Translation: {detected_source} → {target_lang} ({len(texts)} blocks)")
        
        texts_json = json.dumps([{"index": i, "text": t} for i, t in enumerate(texts)], ensure_ascii=False)
        
        prompt = f"""Translate these texts from {detected_source} to {target_lang}. Return JSON array in this exact format:
[{{"index": 0, "translation": "translated text"}}, ...]

Texts to translate:
{texts_json}"""
        
        req = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional translator. Translate accurately while preserving meaning and tone."},
                {"role": "user", "content": prompt}
            ],
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
        
        for attempt in range(config.openai_max_retries):
            try:
                conn = http.client.HTTPSConnection(host, 443, timeout=config.openai_timeout)
                conn.request("POST", uri, body, headers)
                response = conn.getresponse()
                data = response.read()
                conn.close()
                break
            except Exception as e:
                print(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < config.openai_max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
        else:
            return {"blocks": blocks}
        
        print(f"\n📊 Translation API Response:")
        print(f"  Status: {response.status}")
        output = json.loads(data)
        
        if "error" in output:
            print(f"❌ Translation ERROR: {output['error']}")
            return {"blocks": blocks}
        
        try:
            content = output["choices"][0]["message"]["content"]
            
            # Clean up markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            print(f"\n📄 Translation Raw Response ({len(content)} chars):")
            print("=" * 70)
            print(content[:2000])
            print("=" * 70)
            
            translations = json.loads(content.strip())
            
            # Support different response formats
            if isinstance(translations, dict):
                if "translations" in translations:
                    translations = translations["translations"]
                elif "result" in translations:
                    translations = translations["result"]
                elif "data" in translations:
                    translations = translations["data"]
            
            for tr in translations:
                idx = tr.get("index", 0)
                translated_text = tr.get("translation", "")
                if idx < len(blocks):
                    # Ensure block is a dict
                    if isinstance(blocks[idx], str):
                        blocks[idx] = {"text": blocks[idx]}
                    if not isinstance(blocks[idx].get("translation"), dict):
                        blocks[idx]["translation"] = {}
                    blocks[idx]["translation"][target_lang.lower()] = translated_text
                    blocks[idx]["target_lang"] = target_lang
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Failed to parse translation response: {e}")
            content_str = output.get("choices", [{}])[0].get("message", {}).get("content", "N/A") if output else "No output"
            print(f"Raw content: {content_str[:500]}")
            return {"blocks": blocks}
        
        return {"blocks": blocks}


class DeepSeekTranslationProvider(TranslationProvider):
    """DeepSeek Chat translation provider (OpenAI-compatible)
    
    Uses openai_* settings for API key, timeout, etc.
    Override with deepseek_* settings if specified for backward compatibility.
    """
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        texts = [blk.get("source_text", blk.get("text", "")) for blk in blocks]
        
        # Use deepseek_model if specified, otherwise use openai_translation_model
        model = config.deepseek_model or config.openai_translation_model or "deepseek-chat"
        
        texts_json = json.dumps([{"index": i, "text": t} for i, t in enumerate(texts)], ensure_ascii=False)
        
        prompt = f"""Translate these texts from {source_lang or 'auto'} to {target_lang}. Return JSON array in this exact format:
[{{"index": 0, "translation": "translated text"}}, ...]

Texts to translate:
{texts_json}"""
        
        req = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional translator. Translate accurately while preserving meaning and tone."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 2000
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        
        # Use deepseek_base_url if specified, otherwise use openai_base_url
        base_url = config.deepseek_base_url or config.openai_base_url
        import urllib.parse
        parsed_url = urllib.parse.urlparse(base_url)
        host = parsed_url.netloc
        base_path = parsed_url.path.rstrip("/")
        uri = f"{base_path}/chat/completions"
        
        # Use deepseek_api_key if specified, otherwise use openai_api_key
        api_key = config.deepseek_api_key or config.openai_api_key
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {api_key}"
        }
        
        for attempt in range(config.openai_max_retries):
            try:
                conn = http.client.HTTPSConnection(host, 443, timeout=config.openai_timeout)
                conn.request("POST", uri, body, headers)
                response = conn.getresponse()
                data = response.read()
                conn.close()
                break
            except Exception as e:
                print(f"DeepSeek attempt {attempt + 1} failed: {e}")
                if attempt < config.openai_max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
        else:
            return {"blocks": blocks}
        
        output = json.loads(data)
        
        if "error" in output:
            print("DeepSeek error:", output["error"])
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
            print("Failed to parse DeepSeek response:", e)
        
        return {"blocks": blocks}


class GroqTranslationProvider(TranslationProvider):
    """Groq Chat translation provider (OpenAI-compatible, ultra-fast)
    
    Uses openai_* settings for API key, timeout, etc.
    Override with groq_* settings if specified for backward compatibility.
    """
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        texts = [blk.get("source_text", blk.get("text", "")) for blk in blocks]
        
        # Use groq_model if specified, otherwise use openai_translation_model
        model = config.groq_model or config.openai_translation_model or "llama-3.1-70b-versatile"
        
        texts_json = json.dumps([{"index": i, "text": t} for i, t in enumerate(texts)], ensure_ascii=False)
        
        prompt = f"""Translate these texts from {source_lang or 'auto'} to {target_lang}. Return JSON array in this exact format:
[{{"index": 0, "translation": "translated text"}}, ...]

Texts to translate:
{texts_json}"""
        
        req = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional translator. Translate accurately while preserving meaning and tone."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 2000
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        
        # Use groq_base_url if specified, otherwise use openai_base_url
        base_url = config.groq_base_url or config.openai_base_url
        import urllib.parse
        parsed_url = urllib.parse.urlparse(base_url)
        host = parsed_url.netloc
        base_path = parsed_url.path.rstrip("/")
        uri = f"{base_path}/chat/completions"
        
        # Use groq_api_key if specified, otherwise use openai_api_key
        api_key = config.groq_api_key or config.openai_api_key
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {api_key}"
        }
        
        for attempt in range(config.openai_max_retries):
            try:
                conn = http.client.HTTPSConnection(host, 443, timeout=config.openai_timeout)
                conn.request("POST", uri, body, headers)
                response = conn.getresponse()
                data = response.read()
                conn.close()
                break
            except Exception as e:
                print(f"Groq attempt {attempt + 1} failed: {e}")
                if attempt < config.openai_max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
        else:
            return {"blocks": blocks}
        
        output = json.loads(data)
        
        if "error" in output:
            print("Groq error:", output["error"])
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
            print("Failed to parse Groq response:", e)
        
        return {"blocks": blocks}


class GeminiTranslationProvider(TranslationProvider):
    """Google Gemini translation provider"""
    
    def translate(self, blocks: list, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        from .util import lang_2_to_3
        
        texts = [blk.get("source_text", blk.get("text", "")) for blk in blocks]
        
        api_key = config.gemini_api_key
        model = config.gemini_model or "gemini-1.5-flash"
        
        texts_formatted = "\n".join([f"{i}: {t}" for i, t in enumerate(texts)])
        
        prompt = f"""Translate these texts from {source_lang or 'auto'} to {target_lang}. Return JSON array in this exact format:
[{{"index": 0, "translation": "translated text"}}, ...]

Texts to translate:
{texts_formatted}"""
        
        req = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "max_output_tokens": 2000
            }
        }
        
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        uri = f"/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        conn = http.client.HTTPSConnection("generativelanguage.googleapis.com", 443, timeout=config.openai_timeout)
        conn.request("POST", uri, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        
        output = json.loads(data)
        
        if "error" in output:
            print("Gemini error:", output["error"])
            return {"blocks": blocks}
        
        try:
            content = output["candidates"][0]["content"]["parts"][0]["text"]
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
                    blocks[idx]["language"] = source_lang or "unknown"
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            print("Failed to parse Gemini response:", e)
        
        return {"blocks": blocks}


def get_translation_provider(provider_name: str) -> TranslationProvider:
    """Get translation provider by name"""
    providers = {
        "google": GoogleTranslationProvider,
        "yandex": YandexTranslationProvider,
        "openai": OpenAITranslationProvider,
        "deepseek": DeepSeekTranslationProvider,
        "groq": GroqTranslationProvider,
        "gemini": GeminiTranslationProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown translation provider: {provider_name}")
    
    return providers[provider_name]()
