# Tesseract OCR Guide

## Overview

VGTranslate3 now supports **Tesseract OCR** with configurable preprocessing pipelines for better text recognition quality.

## Installation

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus tesseract-ocr-jpn

# Arch Linux
sudo pacman -S tesseract tesseract-data-eng tesseract-data-rus tesseract-data-jpn

# Then install Python package
pip install pytesseract
```

### macOS

```bash
brew install tesseract
brew install tesseract-lang  # for additional languages
pip install pytesseract
```

### Windows

1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location
3. Add to PATH or configure in Python

## Configuration

### Basic Setup (Japanese Games)

```bash
cp config_example/config_tesseract_google.json src/vgtranslate3/config.json
```

Edit `config.json`:
```json
{
    "ocr_provider": "tesseract",
    "translation_provider": "google",
    
    "local_server_ocr_processor": {
        "source_lang": "jpn",
        "psm_mode": 6,
        "min_pixels": 2,
        "pipeline": [
            {
                "action": "reduceToMultiColor",
                "options": {
                    "base": "000000",
                    "colors": [["FFFFFF", "FFFFFF"]],
                    "threshold": 32
                }
            },
            {
                "action": "contrast",
                "options": {
                    "factor": 2.0
                }
            }
        ]
    }
}
```

### Russian Text Setup

```bash
cp config_example/config_tesseract_rus.json src/vgtranslate3/config.json
```

## PSM Modes

Tesseract supports different Page Segmentation Modes (PSM):

| Mode | Description | Best For |
|------|-------------|----------|
| 3 | Fully automatic page segmentation, but no OSD | Clean scans |
| 6 | Uniform block of text | **Game UI (recommended)** |
| 7 | Single text line | Subtitles |
| 13 | Single line of text | HUD elements |

## Preprocessing Pipeline

Available actions:

### 1. reduceToMultiColor
Reduces image to binary (black/white) with color thresholding.

```json
{
    "action": "reduceToMultiColor",
    "options": {
        "base": "000000",           // Background color
        "colors": [                 // Text colors to preserve
            ["FFFFFF", "FFFFFF"]    // White text
        ],
        "threshold": 32             // Color tolerance (0-255)
    }
}
```

### 2. segFill
Segmentation fill - cleans up noise.

```json
{
    "action": "segFill",
    "options": {
        "base": "000000",    // Background color
        "color": "FFFFFF"    // Fill color
    }
}
```

### 3. contrast
Enhances contrast for better recognition.

```json
{
    "action": "contrast",
    "options": {
        "factor": 2.0    // 1.0 = no change, 2.0 = double contrast
    }
}
```

## Example Pipelines

### For Japanese Visual Novels

```json
{
    "source_lang": "jpn",
    "psm_mode": 6,
    "pipeline": [
        {
            "action": "reduceToMultiColor",
            "options": {
                "base": "000000",
                "colors": [["FFFFFF", "FFFFFF"]],
                "threshold": 32
            }
        },
        {
            "action": "contrast",
            "options": {
                "factor": 2.0
            }
        }
    ]
}
```

### For Russian Text with Noise

```json
{
    "source_lang": "rus",
    "psm_mode": 3,
    "min_pixels": 5,
    "pipeline": [
        {
            "action": "reduceToMultiColor",
            "options": {
                "base": "000000",
                "colors": [["FFFFFF", "FFFFFF"]],
                "threshold": 16
            }
        },
        {
            "action": "segFill",
            "options": {
                "base": "000000",
                "color": "FFFFFF"
            }
        }
    ]
}
```

### For English Subtitles

```json
{
    "source_lang": "eng",
    "psm_mode": 7,
    "pipeline": [
        {
            "action": "contrast",
            "options": {
                "factor": 1.5
            }
        }
    ]
}
```

## Language Packs

Install additional languages:

### Ubuntu/Debian
```bash
# All languages
sudo apt-get install tesseract-ocr-all

# Specific languages
sudo apt-get install tesseract-ocr-jpn tesseract-ocr-kor tesseract-ocr-chi-sim
```

### macOS
```bash
brew install tesseract-lang
```

### Windows
Languages included in installer. Additional packs available at:
https://github.com/tesseract-ocr/tessdata

## Performance Tips

1. **Use appropriate PSM mode**: Mode 6 works best for game UI
2. **Reduce colors**: Binary (B/W) images are faster to process
3. **Adjust threshold**: Lower threshold (16-32) for clean text, higher (64+) for anti-aliased text
4. **Enable bbox fallback**: Set `use_bbox_fallback: true` if Tesseract doesn't return boxes
5. **Pre-process images**: Use contrast enhancement for low-contrast text

## Troubleshooting

### "No text found"
- Check Tesseract installation: `tesseract --version`
- Verify language packs: `tesseract --list-langs`
- Adjust threshold in preprocessing pipeline
- Try different PSM mode

### Poor recognition quality
- Increase contrast (factor 2.0-3.0)
- Lower threshold (16-24) for cleaner binary
- Use `segFill` to remove noise
- Try PSM mode 3 instead of 6

### Slow performance
- Reduce image size before OCR
- Use simpler pipeline (fewer steps)
- Consider cloud OCR (OpenAI, Gemini) for speed

## Comparison: Tesseract vs Cloud OCR

| Feature | Tesseract | Cloud (OpenAI/Gemini) |
|---------|-----------|----------------------|
| **Cost** | Free | $0.15-1.00/1K images |
| **Speed** | Fast (local) | Medium (network) |
| **Quality** | Good (clean text) | Excellent (any text) |
| **Languages** | 100+ | 50+ |
| **Privacy** | ✅ Full privacy | ❌ Data sent to cloud |
| **Setup** | Requires installation | API key only |

**Recommendation**: Use Tesseract for development/testing, cloud OCR for production.
