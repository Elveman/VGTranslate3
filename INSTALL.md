# VGTranslate3 Installation Guide

## Quick Start

### Minimal Installation (Cloud OCR only)

For using cloud-based OCR (OpenAI, Google, Yandex):

```bash
# Clone repository
git clone https://github.com/Elveman/VGTranslate3.git
cd VGTranslate3

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install minimal dependencies
pip install -r requirements.txt

# Configure
cp config_example/config_openai.json src/vgtranslate3/config.json
# Edit config.json and add your API key

# Run
python -m src.vgtranslate3.serve
```

### Full Installation (with Local OCR)

For using Tesseract and OpenCV (local OCR):

```bash
# Install Tesseract (system package)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows:
# Download from https://github.com/UB-Mannheim/tesseract/wiki

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-optional.txt

# Or use pyproject.toml:
pip install -e ".[full]"
```

## Dependency Groups

### Core (Always Required)
```txt
pillow>=10,<12      # Image processing
requests>=2.32,<3.0 # HTTP client
```

### Optional: Local OCR
```txt
pytesseract>=0.3,<0.4          # Tesseract wrapper
opencv-python-headless>=4.10   # Bounding box fallback
numpy>=2.0                     # Image arrays
```

### Optional: Development
```txt
pytest>=8      # Testing
black>=24      # Code formatting
flake8>=7      # Linting
mypy>=1        # Type checking
```

## Installation Methods

### Method 1: requirements.txt (Recommended)

```bash
# Minimal
pip install -r requirements.txt

# Full (with local OCR)
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

### Method 2: pip install with extras

```bash
# Install package with local OCR support
pip install -e ".[local-ocr]"

# Install full package (all features)
pip install -e ".[full]"

# Install development version
pip install -e ".[dev]"
```

### Method 3: Docker

```bash
# Build image
docker build -t vgtranslate3 .

# Run
docker run --rm -it -p 4404:4404 vgtranslate3
```

## Configuration Examples

### Cloud-Only Setup (Minimal)

```json
{
    "ocr_provider": "openai",
    "translation_provider": "openai",
    "tts_enabled": false,
    "openai_api_key": "sk-..."
}
```

**Required:** Only `requirements.txt`

### Local OCR Setup

```json
{
    "ocr_provider": "tesseract",
    "translation_provider": "google",
    "tts_enabled": false,
    "local_server_ocr_processor": {...}
}
```

**Required:** `requirements.txt` + `requirements-optional.txt` + Tesseract

### Hybrid Setup

```json
{
    "ocr_provider": "ollama",
    "translation_provider": "groq",
    "tts_enabled": false
}
```

**Required:** `requirements.txt` + Ollama (installed separately)

## System Requirements

### Minimal (Cloud OCR)
- Python 3.9+
- 512MB RAM
- 100MB disk space
- Internet connection

### Full (Local OCR)
- Python 3.9+
- 2GB RAM (4GB+ recommended)
- 500MB disk space
- Tesseract OCR installed
- Internet connection (for translation)

### Local LLM (Ollama/vLLM)
- Python 3.9+
- 8GB+ RAM (16GB+ recommended)
- 10GB+ disk space
- GPU recommended (for vLLM)
- Ollama or vLLM installed

## Troubleshooting

### "No module named 'PIL'"
```bash
pip install pillow
```

### "No module named 'cv2'"
```bash
pip install opencv-python-headless
```

### "Tesseract not found"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from https://github.com/UB-Mannheim/tesseract/wiki
```

### Import errors with bbox_extractor
```bash
# OpenCV is required for bounding box fallback
pip install opencv-python-headless numpy
```

## Verifying Installation

```bash
# Test core imports
python3 -c "from PIL import Image; import requests; print('✓ Core OK')"

# Test optional imports
python3 -c "import cv2; print('✓ OpenCV OK')"
python3 -c "import pytesseract; print('✓ Tesseract OK')"

# Run test suite
PYTHONPATH=src python3 tests/test_providers.py
```

## Upgrade Path

### From Minimal to Full

```bash
# Already have requirements.txt installed
pip install -r requirements-optional.txt

# Verify
python3 -c "import cv2, pytesseract; print('✓ Full installation OK')"
```

### From Old VGTranslate3

```bash
# Old version used future library
# New version doesn't require it for Python 3.9+

# Clean install recommended:
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Platform-Specific Notes

### Linux (Ubuntu/Debian)

```bash
# System dependencies
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev

# Python dependencies
pip3 install -r requirements.txt
```

### macOS

```bash
# System dependencies
brew install python tesseract opencv

# Python dependencies
pip3 install -r requirements.txt
```

### Windows

```powershell
# Install Tesseract
# Download from https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

## Performance Notes

- **Cloud OCR**: Fast (2-5 sec), requires internet
- **Local Tesseract**: Medium (1-3 sec), offline
- **Local LLM (Ollama)**: Slow (5-40 sec), offline
- **Local LLM (vLLM GPU)**: Fast (0.5-3 sec), offline

## Security Considerations

- API keys stored in `config.json` (not in git)
- Default server binds to `0.0.0.0` (accessible on network)
- For local-only: set `local_server_host: "127.0.0.1"`
- Use HTTPS proxy for production

## Next Steps

1. ✅ Installation complete
2. 📖 Read provider-specific guides:
   - `OPENAI_USAGE.md` - Cloud providers
   - `TESSERACT_GUIDE.md` - Local OCR
   - `LOCAL_MODELS_GUIDE.md` - Ollama/vLLM
3. 🔧 Configure `src/vgtranslate3/config.json`
4. 🚀 Start server: `python -m src.vgtranslate3.serve`
5. 🧪 Run tests: `PYTHONPATH=src python3 tests/test_providers.py`
