"""
Translation Providers Module

Provides unified interface for translation services:
- Google Translate
- Yandex Translate
- OpenAI Chat Completions
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
        texts = [blk.get("source_text", blk.get("text", "")) for blk in blocks]
        
        model = config.openai_translation_model or config.openai_model
        
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
        
        output = json.loads(data)
        
        if "error" in output:
            print("OpenAI Translation error:", output["error"])
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
            print("Failed to parse translation response:", e)
        
        return {"blocks": blocks}


def get_translation_provider(provider_name: str) -> TranslationProvider:
    """Get translation provider by name"""
    providers = {
        "google": GoogleTranslationProvider,
        "yandex": YandexTranslationProvider,
        "openai": OpenAITranslationProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown translation provider: {provider_name}")
    
    return providers[provider_name]()
