# VGTranslate3

Lightweight server for doing OCR and machine translation on game screen captures. Suitable as an endpoint for real time usage, and can act as an open-source alternative to the ztranslate client. Based on the original VGTranslate. Uses python 3.9. Licensed under GNU GPLv3.

---

Легковесный сервер для оптического распознавания текста (OCR) и машинного перевода скриншотов из игр. Подходит для использования в реальном времени и может выступать как открытая альтернатива клиенту ztranslate. Основан на оригинальном VGTranslate. Использует Python 3.9. Лицензия: GNU GPLv3.

---

# Installation / Установка

```bash
# Clone / Склонируйте
git clone https://github.com/Elveman/VGTranslate3.git
cd VGTranslate3

# Create venv / Создайте окружение
python3 -m venv .venv
source .venv/bin/activate

# Install / Установите
pip install -r requirements.txt

# Configure / Настройте
cp src/vgtranslate3/config_example/config_routerai.json src/vgtranslate3/config.json
# Edit config.json / Отредактируйте

# Run / Запустите
python -m src.vgtranslate3.serve
```

**See `INSTALL.md` for detailed installation guide.**

**Подробное руководство в `INSTALL.md`.**

---

# Quick Configuration / Быстрая настройка

## OpenAI-Compatible Providers

All OpenAI-compatible providers (RouterAI, DeepSeek, Groq, OpenRouter, etc.) use unified settings:

Все OpenAI-совместимые провайдеры используют единые настройки:

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

**Example configs:**
- `config_routerai.json` — RouterAI (Russian provider)
- `config_openrouter.json` — OpenRouter (100+ models)

**For other providers:** Copy `config_routerai.json` and change `openai_base_url` + models.

**Для других провайдеров:** Скопируйте `config_routerai.json` и измените `openai_base_url` + модели.

## Other Providers

| Provider | Config | Notes |
|----------|--------|-------|
| **Google** | `config_google.json` | Cloud Vision + Translate |
| **Yandex** | `config_yandex.json` | Yandex Cloud API |
| **Gemini** | `config_gemini.json` | Google Gemini API |
| **Tesseract** | `config_tesseract_google.json` | Local OCR + Google translate |
| **Ollama** | `config_ollama_local.json` | Fully local (CPU) |
| **vLLM** | `config_vllm_local.json` | Fully local (GPU) |
| **Hybrid** | `config_hybrid_ollama_groq.json` | Local OCR + Groq translation |
| **ztranslate** | `config_ztranslate.json` | Legacy ztranslate.net |

---

# Docker

```bash
# Build / Сборка
docker build -t vgtranslate3 .

# Run (port 4404) / Запуск (порт 4404)
docker run --rm -it -p 4404:4404 vgtranslate3

# Custom port / Своё порт
docker run --rm -it -e VGTRANSLATE3_PORT=5000 -p 5000:5000 vgtranslate3
```

⚠️ **Note:** `config.json` must be in `src/vgtranslate3` folder.

---

# Testing / Тестирование

```bash
# Provider tests / Тесты провайдеров
PYTHONPATH=src python3 tests/test_providers.py

# Mock tests (no API keys) / Mock-тесты (без ключей)
PYTHONPATH=src python3 tests/test_mock_providers.py

# Benchmark / Бенчмарк
cd tests/benchmark && python benchmark.py
```

---

# Documentation / Документация

- **[INSTALL.md](INSTALL.md)** — Installation guide / Руководство по установке
- **[TESSERACT_GUIDE.md](TESSERACT_GUIDE.md)** — Tesseract OCR setup / Настройка Tesseract
- **[LOCAL_MODELS_GUIDE.md](LOCAL_MODELS_GUIDE.md)** — Ollama/vLLM local models / Локальные модели

---

# RetroArch Integration / Интеграция с RetroArch

1. Configure VGTranslate3 server / Настройте сервер
2. Set server address in RetroArch to your PC's IP / Укажите IP компьютера в RetroArch
3. Enable overlay translation / Включите оверлей перевода

**Note:** Server binds to `0.0.0.0` by default (accessible on local network). For local-only: set `local_server_host: "127.0.0.1"`.

**Примечание:** Сервер по умолчанию доступен в локальной сети (`0.0.0.0`). Для локального доступа: `127.0.0.1`.

---

# Note / Примечание

This is a PoC and pet project for playing JP-only titles comfortably. I'm a C/C++ developer with Python knowledge, using AI coding helpers within reason.

Это пет-проект для комфортной игры в японские игры. Я C/C++ разработчик с знанием Python, использую AI-помощники в разумных пределах.

---

# License / Лицензия

GNU GPLv3

---

# Credits / Благодарности

[Original VGTranslate](https://gitlab.com/spherebeaker/vgtranslate) by spherebeaker — most of the work was done there.

[Оригинальный VGTranslate](https://gitlab.com/spherebeaker/vgtranslate) от spherebeaker — большая часть работы сделана там.
