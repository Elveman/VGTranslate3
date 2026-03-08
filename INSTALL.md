# VGTranslate3 Installation Guide / Руководство по установке

## Quick Start / Быстрый запуск

```bash
# Clone repository / Склонируйте репозиторий
git clone https://github.com/Elveman/VGTranslate3.git
cd VGTranslate3

# Create virtual environment / Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies / Установите зависимости
pip install -r requirements.txt

# Configure / Настройте
cp src/vgtranslate3/config_example/config_routerai.json src/vgtranslate3/config.json
# Edit config.json and add your API key / Отредактируйте config.json и добавьте ключ API

# Run / Запустите
python -m src.vgtranslate3.serve
```

## Optional: Local OCR

For Tesseract support:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: https://github.com/UB-Mannheim/tesseract/wiki

# Install Python package
pip install pytesseract opencv-python-headless
```

See `TESSERACT_GUIDE.md` for details.

## System Requirements

- **Python 3.9+**
- **512MB RAM** (2GB+ for local OCR)
- **Internet** (for cloud OCR/translation)

## Docker

```bash
docker build -t vgtranslate3 .
docker run --rm -it -p 4404:4404 vgtranslate3
```

## Troubleshooting

**"No module named 'PIL'"**
```bash
pip install pillow
```

**"No module named 'cv2'"**
```bash
pip install opencv-python-headless
```

**"Tesseract not found"**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract
```

## More Information

- **Tesseract OCR**: See `TESSERACT_GUIDE.md`
- **Local models (Ollama/vLLM)**: See `LOCAL_MODELS_GUIDE.md`
- **Configuration examples**: See `src/vgtranslate3/config_example/`
