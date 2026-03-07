# VGTranslate3 Installation Guide / Руководство по установке

## Quick Start / Быстрый запуск

### Minimal Installation (Cloud OCR only)
### Минимальная установка (облачный OCR)

For using cloud-based OCR (OpenAI, Google, Yandex):

Для использования облачного OCR (OpenAI, Google, Яндекс):

```bash
# Clone repository / Склонируйте репозиторий
git clone https://github.com/Elveman/VGTranslate3.git
cd VGTranslate3

# Create virtual environment / Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install minimal dependencies / Установите минимальные зависимости
pip install -r requirements.txt

# Configure / Настройте
cp config_example/config_openai.json src/vgtranslate3/config.json
# Edit config.json and add your API key / Отредактируйте config.json и добавьте ключ API

# Run / Запустите
python -m src.vgtranslate3.serve
```

### Full Installation (with Local OCR)
### Полная установка (с локальным OCR)

For using Tesseract and OpenCV (local OCR):

Для использования Tesseract и OpenCV (локальный OCR):

```bash
# Install Tesseract (system package) / Установите Tesseract
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows: скачайте с https://github.com/UB-Mannheim/tesseract/wiki

# Install Python dependencies / Установите зависимости Python
pip install -r requirements.txt
pip install -r requirements-optional.txt

# Or use pyproject.toml / Или через pyproject.toml:
pip install -e ".[full]"
```

---

## Dependency Groups / Группы зависимостей

### Core (Always Required)
### Основные (обязательно)
```txt
pillow>=10,<12      # Image processing / обработка изображений
requests>=2.32,<3.0 # HTTP client / HTTP клиент
```

### Optional: Local OCR
### Опционально: локальный OCR
```txt
pytesseract>=0.3,<0.4          # Tesseract wrapper
opencv-python-headless>=4.10   # Bounding box fallback
numpy>=2.0                     # Image arrays
```

### Optional: Development
### Опционально: разработка
```txt
pytest>=8      # Testing / тесты
black>=24      # Code formatting / форматирование
flake8>=7      # Linting / проверка
mypy>=1        # Type checking / проверка типов
```

---

## Installation Methods / Способы установки

### Method 1: requirements.txt (Recommended)
### Способ 1: requirements.txt (рекомендуется)

```bash
# Minimal / Минимальный
pip install -r requirements.txt

# Full (with local OCR) / Полный (с локальным OCR)
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

### Method 2: pip install with extras
### Способ 2: pip install с extras

```bash
# Install package with local OCR support / Установите пакет с локальным OCR
pip install -e ".[local-ocr]"

# Install full package (all features) / Установите полный пакет
pip install -e ".[full]"

# Install development version / Установите версию для разработки
pip install -e ".[dev]"
```

### Method 3: Docker
### Способ 3: Docker

```bash
# Build image / Создайте образ
docker build -t vgtranslate3 .

# Run / Запустите
docker run --rm -it -p 4404:4404 vgtranslate3
```

---

## Configuration Examples / Примеры конфигураций

### Cloud-Only Setup (Minimal)
### Конфигурация только с облаком (минимальная)

```json
{
    "ocr_provider": "openai",
    "translation_provider": "openai",
    "tts_enabled": false,
    "openai_api_key": "sk-..."
}
```

**Required:** Only `requirements.txt`

**Требуется:** Только `requirements.txt`

### Local OCR Setup
### Конфигурация с локальным OCR

```json
{
    "ocr_provider": "tesseract",
    "translation_provider": "google",
    "tts_enabled": false,
    "local_server_ocr_processor": {...}
}
```

**Required:** `requirements.txt` + `requirements-optional.txt` + Tesseract

**Требуется:** `requirements.txt` + `requirements-optional.txt` + Tesseract

### Hybrid Setup
### Гибридная конфигурация

```json
{
    "ocr_provider": "ollama",
    "translation_provider": "groq",
    "tts_enabled": false
}
```

**Required:** `requirements.txt` + Ollama (installed separately)

**Требуется:** `requirements.txt` + Ollama (устанавливается отдельно)

---

## System Requirements / Системные требования

### Minimal (Cloud OCR)
### Минимальные (облачный OCR)
- Python 3.9+
- 512MB RAM
- 100MB disk space
- Internet connection / Интернет

### Full (Local OCR)
### Полные (локальный OCR)
- Python 3.9+
- 2GB RAM (4GB+ recommended / рекомендуется)
- 500MB disk space
- Tesseract OCR installed
- Internet connection (for translation) / Интернет (для перевода)

### Local LLM (Ollama/vLLM)
### Локальные LLM (Ollama/vLLM)
- Python 3.9+
- 8GB+ RAM (16GB+ recommended / рекомендуется)
- 10GB+ disk space
- GPU recommended (for vLLM) / Рекомендуется GPU
- Ollama or vLLM installed

---

## Troubleshooting / Решение проблем

### "No module named 'PIL'"
```bash
pip install pillow
```

### "No module named 'cv2'"
```bash
pip install opencv-python-headless
```

### "Tesseract not found"
### "Tesseract не найден"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: скачайте с https://github.com/UB-Mannheim/tesseract/wiki
```

### Import errors with bbox_extractor
```bash
# OpenCV is required for bounding box fallback / OpenCV требуется для bbox fallback
pip install opencv-python-headless numpy
```

---

## Verifying Installation / Проверка установки

```bash
# Test core imports / Проверьте основные импорты
python3 -c "from PIL import Image; import requests; print('✓ Core OK')"

# Test optional imports / Проверьте опциональные импорты
python3 -c "import cv2; print('✓ OpenCV OK')"
python3 -c "import pytesseract; print('✓ Tesseract OK')"

# Run test suite / Запустите тесты
PYTHONPATH=src python3 tests/test_providers.py
```

---

## Upgrade Path /路径 обновления

### From Minimal to Full
### От минимальной к полной

```bash
# Already have requirements.txt installed / Уже установлено requirements.txt
pip install -r requirements-optional.txt

# Verify / Проверьте
python3 -c "import cv2, pytesseract; print('✓ Full installation OK')"
```

### From Old VGTranslate3
### От старой версии VGTranslate3

```bash
# Old version used future library / Старая версия использовала future
# New version doesn't require it for Python 3.9+ / Новая не требует для Python 3.9+

# Clean install recommended: / Рекомендуется чистая установка:
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Platform-Specific Notes / Примечания для платформ

### Linux (Ubuntu/Debian)

```bash
# System dependencies / Системные зависимости
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev

# Python dependencies / Python зависимости
pip3 install -r requirements.txt
```

### macOS

```bash
# System dependencies / Системные зависимости
brew install python tesseract opencv

# Python dependencies / Python зависимости
pip3 install -r requirements.txt
```

### Windows

```powershell
# Install Tesseract / Установите Tesseract
# Download from https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR

# Install Python dependencies / Установите зависимости Python
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

---

## Performance Notes / Примечания о производительности

- **Cloud OCR**: Fast (2-5 sec), requires internet / Быстро (2-5 сек), требуется интернет
- **Local Tesseract**: Medium (1-3 sec), offline / Средняя скорость (1-3 сек), оффлайн
- **Local LLM (Ollama)**: Slow (5-40 sec), offline / Медленно (5-40 сек), оффлайн
- **Local LLM (vLLM GPU)**: Fast (0.5-3 sec), offline / Быстро (0.5-3 сек), оффлайн

---

## Security Considerations / Безопасность

- API keys stored in `config.json` (not in git) / Ключи API в `config.json` (не в git)
- Default server binds to `0.0.0.0` (accessible on network) / По умолчанию `0.0.0.0` (доступно в сети)
- For local-only: set `local_server_host: "127.0.0.1"` / Для локального: `127.0.0.1`
- Use HTTPS proxy for production / Используйте HTTPS для production

---

## Next Steps / Следующие шаги

1. ✅ Installation complete / Установка завершена
2. 📖 Read provider-specific guides: / Читайте руководства:
   - `OPENAI_USAGE.md` — Cloud providers / Облачные провайдеры
   - `TESSERACT_GUIDE.md` — Local OCR / Локальный OCR
   - `LOCAL_MODELS_GUIDE.md` — Ollama/vLLM
3. 🔧 Configure `src/vgtranslate3/config.json`
4. 🚀 Start server: `python -m src.vgtranslate3.serve`
5. 🧪 Run tests: `PYTHONPATH=src python3 tests/test_providers.py`
