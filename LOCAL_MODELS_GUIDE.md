# Local Models Guide (Ollama & vLLM)
# Руководство по локальным моделям (Ollama и vLLM)

## Overview / Обзор

VGTranslate3 now supports **fully local OCR and translation** using Ollama and vLLM, enabling private, offline processing without cloud APIs.

VGTranslate3 теперь поддерживает **полностью локальный OCR и перевод** с помощью Ollama и vLLM, обеспечивая приватную оффлайн-обработку без облачных API.

---

## Architecture / Архитектура

```
Image → OCR → Translation → TTS
        ↓       ↓           ↓
     Ollama   Ollama     Google
     vLLM     vLLM       Piper
     LLaVA    Llama      (local)
```

---

## Installation / Установка

### Ollama (CPU-friendly, lightweight)
### Ollama (дружелюбный к CPU, легковесный)

#### Linux/macOS
```bash
# Install Ollama / Установите Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models / Загрузите модели
ollama pull llava:7b          # Vision OCR
ollama pull llama3.1:8b       # Translation (lightweight)
ollama pull llama3.1:70b      # Translation (high quality)
ollama pull mistral:7b        # Alternative translation
```

#### Windows
1. Download from https://ollama.ai/download / Скачайте с сайта
2. Install and run / Установите и запустите
3. Pull models via command prompt / Загрузите модели через командную строку

### vLLM (GPU, high-performance)
### vLLM (GPU, высокая производительность)

#### Linux (CUDA)
```bash
# Install vLLM / Установите vLLM
pip install vllm

# Run server / Запустите сервер
vllm serve llava-hf/llava-1.5-7b-hf \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 4096

# For translation (Llama 3.1) / Для перевода
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 8192
```

#### Requirements / Требования
- NVIDIA GPU (8GB+ VRAM for 7B, 24GB+ for 70B)
- CUDA 11.8+
- 32GB+ RAM for 70B models

---

## Configuration / Конфигурация

### Full Local Setup (Ollama)
### Полная локальная настройка (Ollama)

```bash
cp config_example/config_ollama_local.json src/vgtranslate3/config.json
```

Edit `config.json` / Отредактируйте `config.json`:
```json
{
    "ocr_provider": "ollama",
    "ocr_model": "llava:7b",
    
    "translation_provider": "ollama",
    "translation_model": "llama3.1:8b",
    
    "ollama_base_url": "http://localhost:11434",
    "ollama_timeout": 120
}
```

### High-Performance Local (vLLM)
### Высокопроизводительная локальная (vLLM)

```bash
cp config_example/config_vllm_local.json src/vgtranslate3/config.json
```

```json
{
    "ocr_provider": "vllm",
    "ocr_model": "llava-hf/llava-1.5-7b-hf",
    
    "translation_provider": "vllm",
    "translation_model": "meta-llama/Llama-3.1-70B-Instruct",
    
    "vllm_base_url": "http://localhost:8000/v1",
    "vllm_timeout": 60
}
```

### Hybrid Setup (Local OCR + Cloud Translation)
### Гибридная настройка (локальный OCR + облачный перевод)

```bash
cp config_example/config_hybrid_ollama_groq.json src/vgtranslate3/config.json
```

```json
{
    "ocr_provider": "ollama",      # Local, private / Локально, приватно
    "ocr_model": "llava:7b",
    
    "translation_provider": "groq", # Fast, cheap / Быстро, дёшево
    "translation_model": "llama-3.1-70b-versatile",
    
    "groq_api_key": "grq_..."
}
```

---

## Model Recommendations / Рекомендации моделей

### OCR (Vision)

| Model | Size | Quality | Speed | VRAM | Best For |
|-------|------|---------|-------|------|----------|
| **llava:7b** | 7B | Good | Fast | 8GB | General use |
| **llava:34b** | 34B | Better | Medium | 24GB | High quality |
| **llava-hf/llava-1.5-7b** | 7B | Good | Fast | 8GB | vLLM deployment |

### Translation (LLM)

| Model | Size | Quality | Speed | VRAM | Best For |
|-------|------|---------|-------|------|----------|
| **llama3.1:8b** | 8B | Good | Very Fast | 6GB | Lightweight |
| **llama3.1:70b** | 70B | Excellent | Medium | 40GB | High quality |
| **mistral:7b** | 7B | Good | Fast | 6GB | Alternative |
| **gemma2:9b** | 9B | Good | Fast | 8GB | Google model |

---

## Performance Comparison / Сравнение производительности

### Ollama (CPU)
- **llava:7b**: ~5-10 seconds per image
- **llama3.1:8b**: ~2-5 seconds per translation
- **llama3.1:70b**: ~20-40 seconds per translation

### vLLM (GPU A100)
- **llava-1.5-7b**: ~0.5-1 seconds per image
- **Llama-3.1-70B**: ~1-3 seconds per translation

### Cloud (for reference) / Облако (для сравнения)
- **OpenAI gpt-4o**: ~2-3 seconds
- **Groq**: ~0.3-0.5 seconds (fastest)
- **DeepSeek**: ~1-2 seconds

---

## Troubleshooting / Решение проблем

### "Connection refused" / "Соединение отклонено"
```bash
# Check Ollama is running / Проверьте, запущен ли Ollama
ollama list
# Start if needed / Запустите при необходимости
ollama serve

# Check vLLM is running / Проверьте, запущен ли vLLM
curl http://localhost:8000/v1/models
```

### "Model not found" / "Модель не найдена"
```bash
# Pull model / Загрузите модель
ollama pull llava:7b
# Or for vLLM, ensure model is downloaded:
# Или для vLLM убедитесь, что модель загружена:
python -c "from transformers import AutoModel; AutoModel.from_pretrained('llava-hf/llava-1.5-7b-hf')"
```

### Slow performance / Медленная производительность
- **Ollama**: Use smaller models (8b instead of 70b) / Используйте меньшие модели
- **vLLM**: Enable quantization (FP8, INT4) / Включите квантование
- Increase timeout: `"ollama_timeout": 180` / Увеличьте таймаут

### Poor OCR quality / Плохое качество OCR
- Try larger model: `llava:34b` / Попробуйте большую модель
- Adjust prompt in provider code / Настройте промпт в коде провайдера
- Enable bbox fallback: `"use_bbox_fallback": true` / Включите bbox fallback

---

## Privacy & Security / Приватность и безопасность

### Fully Local / Полностью локально
✅ No data sent to cloud / Данные не отправляются в облако
✅ GDPR compliant / Соответствие GDPR
✅ Works offline / Работает оффлайн
✅ No API costs / Нет затрат на API

### Hybrid / Гибридно
✅ OCR is local (private) / OCR локальный (приватный)
⚠️ Translation goes to cloud / Перевод отправляется в облако
✅ Faster than full local / Быстрее полностью локального

### Comparison / Сравнение

| Setup / Конфигурация | Privacy / Приватность | Speed / Скорость | Cost / Стоимость | Quality / Качество |
|-------|---------|-------|------|---------|
| **Full Local** | ✅✅✅ | ⚠️ | ✅ | ⚠️ |
| **Hybrid** | ✅✅ | ✅✅ | ✅✅ | ✅✅ |
| **Full Cloud** | ⚠️ | ✅✅✅ | ⚠️ | ✅✅✅ |

---

## Advanced Usage / Продвинутое использование

### Custom Ollama Prompts / Пользовательские промпты Ollama

Edit `local_ocr_providers.py` to customize OCR prompt:

Отредактируйте `local_ocr_providers.py` для настройки промпта OCR:

```python
prompt = """Extract all text from this image.
Focus on:
1. Japanese characters (kanji, hiragana, katakana)
2. UI elements (menus, dialogs)
3. Subtitles

Return JSON format..."""
```

### Multi-GPU vLLM

```bash
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 2 \
    --max-model-len 8192
```

### Quantization (reduce VRAM) / Квантование (уменьшение VRAM)

```bash
# Ollama (already quantized by default) / Уже квантовано по умолчанию
ollama pull llama3.1:8b-q4  # 4-bit quantized

# vLLM (AWQ quantization)
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --quantization awq
```

---

## Testing Without API Keys / Тестирование без ключей API

Create test config / Создайте тестовый конфиг:
```json
{
    "ocr_provider": "ollama",
    "translation_provider": "ollama",
    "tts_provider": "google",
    
    "ollama_base_url": "http://localhost:11434",
    "ollama_ocr_model": "llava:7b",
    "ollama_translation_model": "llama3.1:8b",
    
    "local_server_host": "127.0.0.1",
    "local_server_port": 4404,
    "local_server_enabled": true
}
```

Test with dummy image / Протестируйте с тестовым изображением:
```bash
python -m src.vgtranslate3.serve &
curl -X POST "http://127.0.0.1:4404/?source_lang=jpn&target_lang=en" \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,..."}'
```

---

## Cost Comparison / Сравнение затрат

### Full Local / Полностью локально
- **Hardware**: $500-2000 (GPU)
- **Running**: $0.05/hour (electricity) / Электричество
- **Privacy**: ✅ Full / Полная

### Cloud OCR+Translation / Облачный OCR+Перевод
- **OpenAI**: ~$0.50 per 1000 images
- **Groq**: ~$0.10 per 1000 images
- **DeepSeek**: ~$0.05 per 1000 images

### Break-even / Точка безубыточности
Local setup pays off after ~100,000 images vs cloud.

Локальная настройка окупается после ~100 000 изображений по сравнению с облаком.

---

## Recommendations / Рекомендации

### For Development / Для разработки
- **Ollama + llama3.1:8b**: Fast iteration, no costs / Быстрая итерация, без затрат
- Test locally before deploying / Тестируйте локально перед развёртыванием

### For Production / Для production
- **vLLM + Llama-3.1-70B**: Best quality/speed / Лучшее качество/скорость
- **Hybrid (Ollama + Groq)**: Balance privacy & speed / Баланс приватности и скорости

### For Privacy-Sensitive / Для приватных данных
- **Full Ollama**: Complete offline processing / Полная оффлайн-обработка
- No data leaves your machine / Данные не покидают вашу машину
