# OpenAI-Compatible API Usage Guide
# Руководство по использованию OpenAI-совместимого API

## Quick Start / Быстрый запуск

### 1. Choose Your Provider / Выберите провайдера

#### OpenAI (Official) / Официальный OpenAI
```bash
cp config_example/config_openai.json src/vgtranslate3/config.json
# Edit src/vgtranslate3/config.json and add your API key:
# Отредактируйте config.json и добавьте ключ API:
# "openai_api_key": "sk-..."
```

#### RouterAI (Russian provider, ruble payments)
#### RouterAI (российский провайдер, оплата в рублях)
```bash
cp config_example/config_routerai.json src/vgtranslate3/config.json
# Add your API key from https://routerai.ru
# Добавьте ключ API с https://routerai.ru
# "openai_api_key": "ra_..."
```

#### OpenRouter (100+ models) / OpenRouter (100+ моделей)
```bash
cp config_example/config_openrouter.json src/vgtranslate3/config.json
# Add your API key from https://openrouter.ai
# Добавьте ключ API с https://openrouter.ai
# "openai_api_key": "sk-or-..."
```

### 2. Install Dependencies / Установите зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Server / Запустите сервер

```bash
python -m src.vgtranslate3.serve
```

Server will start on `http://0.0.0.0:4404`

Сервер запустится на `http://0.0.0.0:4404`

---

## Configuration Options / Опции конфигурации

### Provider Selection / Выбор провайдера

You can use different providers for different pipeline stages:

Вы можете использовать разных провайдеров для разных этапов пайплайна:

```json
{
    "ocr_provider": "openai",           // Vision model for text extraction / Vision модель для распознавания
    "ocr_model": "gpt-4o-mini",         // Specific model for OCR / Модель для OCR
    
    "translation_provider": "openai",   // LLM for translation / LLM для перевода
    "translation_model": "gpt-4o-mini", // Specific model for translation / Модель для перевода
    
    "tts_provider": "openai",           // TTS provider / TTS провайдер
    "tts_model": "tts-1",               // TTS model / TTS модель
    "tts_voice": "alloy"                // Voice name / Имя голоса
}
```

### Models / Модели

**Recommended (fast & cheap) / Рекомендованные (быстрые и дешёвые):**
- OCR: `gpt-4o-mini`
- Translation: `gpt-4o-mini` or `gpt-4.5-nano`
- TTS: `tts-1`

**High quality / Высокое качество:**
- OCR: `gpt-4o`
- Translation: `gpt-4o`
- TTS: `tts-1-hd`

### Bounding Box Fallback / Резервное определение bounding boxes

If the vision model doesn't return bounding boxes, the system can use OpenCV heuristics:

Если vision модель не возвращает bounding boxes, система использует эвристики OpenCV:

```json
{
    "use_bbox_fallback": true
}
```

### Timeouts & Retries / Таймауты и попытки

```json
{
    "openai_timeout": 30,        // seconds / секунды
    "openai_max_retries": 3      // number of retry attempts / количество попыток
}
```

---

## API Examples / Примеры API

### Using with OpenAI / Использование с OpenAI

```bash
curl -X POST "http://localhost:4404/?source_lang=ja&target_lang=en" \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,..."}'
```

### Using with RouterAI / Использование с RouterAI

RouterAI supports Russian ruble payments and compliance with ФЗ-152:

RouterAI поддерживает оплату в рублях и соответствие ФЗ-152:

- Base URL: `https://routerai.ru/api/v1`
- Models: `openai/gpt-4o-mini`, `anthropic/claude-3.5-haiku`, etc.
- Payment: Russian cards, bank transfer for legal entities / Российские карты, безнал для юрлиц

### Using with OpenRouter / Использование с OpenRouter

OpenRouter provides access to 100+ models:

OpenRouter предоставляет доступ к 100+ моделям:

- Base URL: `https://openrouter.ai/api/v1`
- Free models: `openai/gpt-4o-mini:free` / Бесплатные модели
- Variants: `:nitro` (fast), `:extended` (long context)

---

## Pipeline Architecture / Архитектура пайплайна

The system now supports **separate providers for each stage**:

Система поддерживает **раздельных провайдеров для каждого этапа**:

```
Image → OCR → Translation → TTS
        ↓       ↓           ↓
     OpenAI  YandexGPT   Google
     RouterAI OpenAI     Yandex
```

Example configuration / Пример конфигурации:
- OCR: OpenAI Vision (`gpt-4o-mini`)
- Translation: YandexGPT (`yandexgpt-lite`)
- TTS: Google Cloud TTS

---

## Bounding Box Detection / Определение bounding boxes

If the vision model doesn't return bounding boxes, the system uses OpenCV-based heuristics:

Если vision модель не возвращает bounding boxes, система использует эвристики на основе OpenCV:

1. Grayscale conversion / Преобразование в оттенки серого
2. Binary threshold (Otsu) / Бинарный порог (Otsu)
3. Contour detection / Поиск контуров
4. Area filtering / Фильтрация по площади
5. Text-to-box matching / Сопоставление текста с bounding box

This ensures compatibility even with models that don't support structured output.

Это обеспечивает совместимость даже с моделями, которые не поддерживают структурированный вывод.

---

## Troubleshooting / Решение проблем

### "No module named 'PIL'"
```bash
pip install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'imp'"
Update to Python 3.9+ and reinstall dependencies. The `future` library is not compatible with Python 3.13+.

Обновитесь до Python 3.9+ и переустановите зависимости. Библиотека `future` не совместима с Python 3.13+.

### "Request timeout" / Таймаут запроса
Increase `openai_timeout` in config or check your internet connection.

Увеличьте `openai_timeout` в конфиге или проверьте интернет-соединение.

### "No text found" / Текст не найден
- Check that your API key is valid / Проверьте действительность ключа API
- Ensure the image has visible text / Убедитесь, что на изображении есть текст
- Try a different model (e.g., `gpt-4o` instead of `gpt-4o-mini`) / Попробуйте другую модель

---

## Cost Optimization / Оптимизация затрат

**Cheapest setup / Самая дешёвая конфигурация:**
- OCR: `gpt-4o-mini` (~$0.15/1M tokens)
- Translation: `gpt-4o-mini` or `gpt-4.5-nano`
- TTS: `tts-1` (~$15/1M characters)

**Free tier (OpenRouter) / Бесплатный уровень:**
- Use `:free` variant: `openai/gpt-4o-mini:free`
- Limited availability, but good for testing / Ограниченная доступность, но хорошо для тестов

**Russian users / Пользователям из России:**
- RouterAI: Pay in rubles, ФЗ-152 compliant / Оплата в рублях, соответствие ФЗ-152
- Servers located in Russia / Серверы в России
