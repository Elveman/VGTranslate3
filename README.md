# VGTranslate3

Lightweight server for doing OCR and machine translation on game screen captures. Suitable as an endpoint for real time usage, and can act as an open-source alternative to the ztranslate client. Based on the original VGTranslate. Uses python 3.9. Licensed under GNU GPLv3.

---

Легковесный сервер для оптического распознавания текста (OCR) и машинного перевода скриншотов из игр. Подходит для использования в реальном времени и может выступать как открытая альтернатива клиенту ztranslate. Основан на оригинальном VGTranslate. Использует Python 3.9. Лицензия: GNU GPLv3.

---

# Installation / Установка

1. Download this repo and extract it. If you have git you can do: `git clone https://github.com/Elveman/VGTranslate3.git` instead.
2. Copy any of JSONs in `config_example` folder to `config.json` (in the `src/vgtranslate3` folder) and modify the configuration to point to the OCR/MT apis you want to use (see the Examples section below).
3. Install python (v3.9 or higher) to your system.
4. Run `python -m venv .venv` to create a new Python environment then `source .venv/bin/activate` to switch to it.
5. Run `python -m pip install -r requirements.txt` in the base folder to install the required packages (in a virtualenv).
6. Run `python -m src.vgtranslate3.serve` to launch the server.

---

1. Скачайте репозиторий и распакуйте его. Если у вас есть git, выполните: `git clone https://github.com/Elveman/VGTranslate3.git`
2. Скопируйте любой JSON из папки `config_example` в `config.json` (в папке `src/vgtranslate3`) и измените конфигурацию, указав нужные API для OCR/перевода (см. примеры ниже).
3. Установите Python (версии 3.9 или выше).
4. Выполните `python -m venv .venv` для создания виртуального окружения, затем `source .venv/bin/activate` для активации.
5. Выполните `python -m pip install -r requirements.txt` для установки зависимостей.
6. Выполните `python -m src.vgtranslate3.serve` для запуска сервера.

---

# Example configurations / Примеры конфигураций

You can use either use Google API keys yourself to run vgtranslate3, or use an account with the ztranslate.net service. The ZTranslate service in this case basically acts like a standalone vgtranslate3 server that's setup with it's own Google API keys. The main purpose being that you can try out vgtranslate3 without having to sign up to Google Cloud first, and getting some savings with a volume discount on the Google Cloud api calls. To get an API key for ZTranslate, go to https://ztranslate.net , sign up, and go to the Settings page. The ZTranslate API key will be at the bottom.

As of writing, ztranslate.net allows 20,000 calls per month (for free), while if you sign up for Google Cloud, you get $300 worth of API credits. Each vgtranslate3 call costs about 0.2-0.3 cents, so it makes sense to use the Google API keys directly instead of pooling than with ZTranslate, at least at first.

See: https://cloud.google.com/billing/docs/how-to/manage-billing-account about how to create a Google Cloud account and https://cloud.google.com/docs/authentication/api-keys about creating Google Cloud API keys

If using Google Cloud keys, be sure to set the API key to not have restricted APIs at all, or at least include the Cloud Vision API, Cloud Translation API, and Cloud Text-to-Speech API in the list of allowed APIs.

Вы можете использовать ключи Google API напрямую или воспользоваться сервисом ztranslate.net. ZTranslate действует как отдельный сервер vgtranslate3 с собственными ключами Google API. Это позволяет попробовать vgtranslate3 без регистрации в Google Cloud и получить скидку за объём. Чтобы получить ключ ZTranslate, зарегистрируйтесь на https://ztranslate.net и перейдите на страницу настроек.

На момент написания, ztranslate.net позволяет 20 000 вызовов в месяц бесплатно, а Google Cloud предоставляет $300 кредитов. Каждый вызов vgtranslate3 стоит около 0,2-0,3 цента, поэтому использование Google API напрямую выгоднее.

См.: https://cloud.google.com/billing/docs/how-to/manage-billing-account о создании аккаунта Google Cloud и https://cloud.google.com/docs/authentication/api-keys о создании ключей API.

При использовании ключей Google Cloud убедитесь, что API ключ не имеет ограничений, или включите Cloud Vision API, Cloud Translation API и Cloud Text-to-Speech API.

### Using ztranslate.net / Использование ztranslate.net
```
config_example/config_ztranslate.json
```

### Using Google OCR and translation / Использование Google OCR и перевода
```
config_example/config_google.json
```

### Using Yandex OCR and translation / Использование Яндекс OCR и перевода
```
config_example/config_yandex.json
```

### Using tesseract locally, and then Google translate (experimental):
### Использование Tesseract локально + Google перевод (экспериментально):
```
config_example/config_tesseract_google.json
```

### Using OpenAI Vision and Translation:
### Использование OpenAI Vision и перевода:
```
config_example/config_openai.json
```

### Using RouterAI (Russian provider, OpenAI-compatible):
### Использование RouterAI (российский провайдер, OpenAI-совместимый):
```
config_example/config_routerai.json
```

### Using OpenRouter (100+ models):
### Использование OpenRouter (100+ моделей):
```
config_example/config_openrouter.json
```

### Using DeepSeek (OpenAI-compatible):
### Использование DeepSeek (OpenAI-совместимый):
```
config_example/config_deepseek.json
```

### Using Groq (OpenAI-compatible, ultra-fast):
### Использование Groq (OpenAI-совместимый, ультра-быстрый):
```
config_example/config_groq.json
```

### Using Gemini (unique API):
### Использование Gemini (уникальный API):
```
config_example/config_gemini.json
```

### Using Ollama (local models):
### Использование Ollama (локальные модели):
```
config_example/config_ollama_local.json
```

### Using vLLM (local models, GPU):
### Использование vLLM (локальные модели, GPU):
```
config_example/config_vllm_local.json
```

### Hybrid (local OCR + cloud translation):
### Гибридная схема (локальный OCR + облачный перевод):
```
config_example/config_hybrid_ollama_groq.json
```

### Without TTS:
### Без TTS:
```
config_example/config_openai_no_tts.json
```

⚠️ **Note / Примечание:** By default the server address is `0.0.0.0`, making it accessible to anyone using the same local network. To use the server with the local RetroArch build, change the address to `127.0.0.1` or `localhost`.

По умолчанию сервер доступен по адресу `0.0.0.0`, что делает его доступным для всех в локальной сети. Для использования с RetroArch измените адрес на `127.0.0.1` или `localhost`.

---

# Docker

To build / Для сборки:
```bash
docker build -t vgtranslate3 .
```

To run with the default port (4404) / Запуск на порту 4404:
```bash
docker run --rm -it -p 4404:4404 docker.io/library/vgtranslate3
```

To run with custom port / Запуск на自定义 порту:
```bash
docker run --rm -it -e VGTRANSLATE3_PORT=5000 -p 5000:5000 docker.io/library/vgtranslate3
```

⚠️ The Docker build requires `config.json` to be placed in the `src/vgtranslate3` folder.

Docker-сборка требует размещения `config.json` в папке `src/vgtranslate3`.

---

# Documentation / Документация

- **[INSTALL.md](INSTALL.md)** — Installation guide / Руководство по установке
- **[OPENAI_COMPATIBLE.md](OPENAI_COMPATIBLE.md)** — OpenAI/RouterAI/OpenRouter usage / Использование OpenAI
- **[TESSERACT_GUIDE.md](TESSERACT_GUIDE.md)** — Tesseract OCR setup / Настройка Tesseract
- **[LOCAL_MODELS_GUIDE.md](LOCAL_MODELS_GUIDE.md)** — Ollama/vLLM local models / Локальные модели Ollama/vLLM

---

# Testing / Тестирование

Run provider tests / Запуск тестов провайдеров:
```bash
PYTHONPATH=src python3 tests/test_providers.py
```

Run mock tests (no API keys required) / Запуск mock-тестов (без ключей API):
```bash
PYTHONPATH=src python3 tests/test_mock_providers.py
```

Manual testing guide / Руководство по ручному тестированию:
- **[tests/benchmark/README.md](tests/benchmark/README.md)**

---

# Note / Примечание

This is, mostly, a PoC now and a pet project made for personal benefits (like playing JP-only Atlus titles with comfort) since there's tons of progress in AI image recognition and text translation and the original project hasn't been updated for quite a while even though there's a lot of potential here. Please note that while I'm a programmer, Python is not my field of expertise. I'm a C/C++ programmer with some Python knowledge and some common sense, so AI coding helpers are used (within reason).

Это, в основном, PoC и пет-проект, созданный для личных целей (например, комфортной игры в японские игры Atlus), поскольку в области распознавания изображений и перевода текста наблюдается огромный прогресс, а оригинальный проект давно не обновлялся. Обратите внимание: я программист, но Python — не моя основная специализация. Я C/C++ разработчик с некоторым знанием Python и здравым смыслом, поэтому используются AI-помощники для написания кода (в разумных пределах).

---

# Roadmap / План развития

- [x] Python 3 port / Порт на Python 3
- [x] Proper config files (pyproject.toml, requirements.txt) / Правильные конфиги
- [x] Docker support / Поддержка Docker
- [x] Proper TTS testing / Тестирование TTS
- [x] Yandex Translate support / Поддержка Яндекс.Перевода
- [x] OpenAI API support (Vision + Translation + TTS) / Поддержка OpenAI API
- [x] OpenAI-compatible API (RouterAI, OpenRouter) / OpenAI-совместимый API
- [x] Other REST services support (DeepSeek, Groq, Gemini) / Другие REST сервисы
- [x] Proper Tesseract support / Поддержка Tesseract
- [x] Full on-device translation support (Ollama, vLLM) / Локальный перевод
- [x] Refactoring / Рефакторинг
- [ ] Local TTS (Piper, Coqui) / Локальный TTS
- [x] Web UI / Веб-интерфейс

---

# Credits / Благодарности

[This awesome person](https://gitlab.com/spherebeaker/vgtranslate) did most of the work developing the original VGTranslate. I'm just building on top of it.

[Этот замечательный человек](https://gitlab.com/spherebeaker/vgtranslate) проделал большую часть работы над оригинальным VGTranslate. Я лишь развиваю его дальше.

---

# License / Лицензия

GNU GPLv3


