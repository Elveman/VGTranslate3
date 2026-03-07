# OpenAI-Compatible API Usage Guide

## Quick Start

### 1. Choose Your Provider

#### OpenAI (Official)
```bash
cp config_example/config_openai.json src/vgtranslate3/config.json
# Edit src/vgtranslate3/config.json and add your API key:
# "openai_api_key": "sk-..."
```

#### RouterAI (Russian provider, ruble payments)
```bash
cp config_example/config_routerai.json src/vgtranslate3/config.json
# Add your API key from https://routerai.ru
# "openai_api_key": "ra_..."
```

#### OpenRouter (100+ models)
```bash
cp config_example/config_openrouter.json src/vgtranslate3/config.json
# Add your API key from https://openrouter.ai
# "openai_api_key": "sk-or-..."
```

### 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Server

```bash
python -m src.vgtranslate3.serve
```

Server will start on `http://0.0.0.0:4404`

---

## Configuration Options

### Provider Selection

You can use different providers for different pipeline stages:

```json
{
    "ocr_provider": "openai",           // Vision model for text extraction
    "ocr_model": "gpt-4o-mini",         // Specific model for OCR
    
    "translation_provider": "openai",   // LLM for translation
    "translation_model": "gpt-4o-mini", // Specific model for translation
    
    "tts_provider": "openai",           // TTS provider
    "tts_model": "tts-1",               // TTS model
    "tts_voice": "alloy"                // Voice name
}
```

### Models

**Recommended (fast & cheap):**
- OCR: `gpt-4o-mini`
- Translation: `gpt-4o-mini` or `gpt-4.5-nano`
- TTS: `tts-1`

**High quality:**
- OCR: `gpt-4o`
- Translation: `gpt-4o`
- TTS: `tts-1-hd`

### Bounding Box Fallback

If the vision model doesn't return bounding boxes, the system can use OpenCV heuristics:

```json
{
    "use_bbox_fallback": true
}
```

### Timeouts & Retries

```json
{
    "openai_timeout": 30,        // seconds
    "openai_max_retries": 3      // number of retry attempts
}
```

---

## API Examples

### Using with OpenAI

```bash
curl -X POST "http://localhost:4404/?source_lang=ja&target_lang=en" \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,..."}'
```

### Using with RouterAI

RouterAI supports Russian ruble payments and compliance with  ФЗ-152:

- Base URL: `https://routerai.ru/api/v1`
- Models: `openai/gpt-4o-mini`, `anthropic/claude-3.5-haiku`, etc.
- Payment: Russian cards, bank transfer for legal entities

### Using with OpenRouter

OpenRouter provides access to 100+ models:

- Base URL: `https://openrouter.ai/api/v1`
- Free models: `openai/gpt-4o-mini:free`
- Variants: `:nitro` (fast), `:extended` (long context)

---

## Pipeline Architecture

The system now supports **separate providers for each stage**:

```
Image → OCR → Translation → TTS
        ↓       ↓           ↓
     OpenAI  YandexGPT   Google
     RouterAI OpenAI     Yandex
```

Example configuration:
- OCR: OpenAI Vision (`gpt-4o-mini`)
- Translation: YandexGPT (`yandexgpt-lite`)
- TTS: Google Cloud TTS

---

## Bounding Box Detection

If the vision model doesn't return bounding boxes, the system uses OpenCV-based heuristics:

1. Grayscale conversion
2. Binary threshold (Otsu)
3. Contour detection
4. Area filtering
5. Text-to-box matching

This ensures compatibility even with models that don't support structured output.

---

## Troubleshooting

### "No module named 'PIL'"
```bash
pip install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'imp'"
Update to Python 3.9+ and reinstall dependencies. The `future` library is not compatible with Python 3.13+.

### "Request timeout"
Increase `openai_timeout` in config or check your internet connection.

### "No text found"
- Check that your API key is valid
- Ensure the image has visible text
- Try a different model (e.g., `gpt-4o` instead of `gpt-4o-mini`)

---

## Cost Optimization

**Cheapest setup:**
- OCR: `gpt-4o-mini` (~$0.15/1M tokens)
- Translation: `gpt-4o-mini` or `gpt-4.5-nano`
- TTS: `tts-1` (~$15/1M characters)

**Free tier (OpenRouter):**
- Use `:free` variant: `openai/gpt-4o-mini:free`
- Limited availability, but good for testing

**Russian users:**
- RouterAI: Pay in rubles, ФЗ-152 compliant
- Servers located in Russia
