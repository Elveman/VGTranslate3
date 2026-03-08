# OpenAI-Compatible Providers

All OpenAI-compatible providers (DeepSeek, Groq, RouterAI, OpenRouter, etc.) use the same unified settings:

Все OpenAI-совместимые провайдеры (DeepSeek, Groq, RouterAI, OpenRouter и др.) используют единые настройки:

## Quick Start / Быстрый старт

```json
{
  "ocr_provider": "openai",
  "translation_provider": "openai",
  
  "openai_api_key": "your-api-key",
  "openai_base_url": "https://provider.com/v1",
  "openai_ocr_model": "model-for-ocr",
  "openai_translation_model": "model-for-translation"
}
```

## Provider URLs / URL провайдеров

| Provider | Base URL | Example Models |
|----------|----------|----------------|
| OpenAI | `https://api.openai.com/v1` | gpt-4o, gpt-4o-mini |
| RouterAI | `https://routerai.ru/api/v1` | ministral-14b, ministral-3b |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-vl2, deepseek-chat |
| Groq | `https://api.groq.com/openai/v1` | llava-1.5, llama-3.1-70b |
| OpenRouter | `https://openrouter.ai/api/v1` | 100+ models |

## Configuration Priority / Приоритет конфигурации

1. Provider-specific settings (e.g., `deepseek_api_key`) - **deprecated**
2. Universal `openai_*` settings - **recommended**

Example for DeepSeek:

```json
{
  // ✅ Recommended (universal settings)
  "openai_api_key": "sk-deepseek-...",
  "openai_base_url": "https://api.deepseek.com/v1",
  "openai_ocr_model": "deepseek-vl2",
  "openai_translation_model": "deepseek-chat",
  
  // ❌ Deprecated (still works, but not recommended)
  "deepseek_api_key": "",
  "deepseek_base_url": "",
  "deepseek_model": ""
}
```

## Benefits / Преимущества

- ✅ **Simpler configuration** - one set of settings for all providers
- ✅ **Easy to switch** - just change `base_url` and models
- ✅ **Consistent API** - same timeout, retry logic, error handling
- ✅ **Future-proof** - new OpenAI-compatible providers work out of the box

- ✅ **Проще конфигурация** - один набор настроек для всех провайдеров
- ✅ **Легко переключаться** - просто измените `base_url` и модели
- ✅ **Единый API** - одинаковые таймауты, повторные попытки, обработка ошибок
- ✅ **На будущее** - новые OpenAI-совместимые провайдеры работают сразу

## Exceptions / Исключения

Some providers have unique APIs and require separate settings:

Некоторые провайдеры имеют уникальный API и требуют отдельных настроек:

- **Gemini** - `gemini_api_key`, `gemini_model` (unique API)
- **Ollama** - `ollama_base_url`, `ollama_ocr_model` (local)
- **vLLM** - `vllm_base_url`, `vllm_ocr_model` (local)
- **Yandex** - `yandex_*` (unique API)
