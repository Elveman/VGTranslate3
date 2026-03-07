# Tesseract OCR Guide
# Руководство по использованию Tesseract OCR

## Overview / Обзор

VGTranslate3 now supports **Tesseract OCR** with configurable preprocessing pipelines for better text recognition quality.

VGTranslate3 теперь поддерживает **Tesseract OCR** с конфигурируемыми пайплайнами предобработки для лучшего качества распознавания текста.

---

## Installation / Установка

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus tesseract-ocr-jpn

# Arch Linux
sudo pacman -S tesseract tesseract-data-eng tesseract-data-rus tesseract-data-jpn

# Then install Python package / Установите Python пакет
pip install pytesseract
```

### macOS

```bash
brew install tesseract
brew install tesseract-lang  # for additional languages / для дополнительных языков
pip install pytesseract
```

### Windows

1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki / Скачайте установитель
2. Install to default location / Установите в стандартное расположение
3. Add to PATH or configure in Python / Добавьте в PATH или настройте в Python

---

## Configuration / Конфигурация

### Basic Setup (Japanese Games)
### Базовая настройка (для японских игр)

```bash
cp config_example/config_tesseract_google.json src/vgtranslate3/config.json
```

Edit `config.json` / Отредактируйте `config.json`:
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

### Russian Text Setup / Настройка для русского текста

```bash
cp config_example/config_tesseract_rus.json src/vgtranslate3/config.json
```

---

## PSM Modes / Режимы PSM

Tesseract supports different Page Segmentation Modes (PSM):

Tesseract поддерживает разные режимы сегментации страниц (PSM):

| Mode | Description / Описание | Best For / Лучше для |
|------|----------------------|---------------------|
| 3 | Fully automatic page segmentation, but no OSD | Clean scans / Чистые сканы |
| 6 | Uniform block of text / Uniform блок текста | **Game UI (recommended)** / **Игровой UI (рекомендуется)** |
| 7 | Single text line / Одна строка текста | Subtitles / Субтитры |
| 13 | Single line of text / Одна строка текста | HUD elements / HUD элементы |

---

## Preprocessing Pipeline / Пайплайн предобработки

Available actions / Доступные действия:

### 1. reduceToMultiColor
Reduces image to binary (black/white) with color thresholding.

Преобразует изображение в бинарное (черно-белое) с цветовым порогом.

```json
{
    "action": "reduceToMultiColor",
    "options": {
        "base": "000000",           // Background color / Цвет фона
        "colors": [                 // Text colors to preserve / Цветы текста для сохранения
            ["FFFFFF", "FFFFFF"]    // White text / Белый текст
        ],
        "threshold": 32             // Color tolerance (0-255) / Порог цвета
    }
}
```

### 2. segFill
Segmentation fill - cleans up noise.

Заполнение сегментации - очищает шум.

```json
{
    "action": "segFill",
    "options": {
        "base": "000000",    // Background color / Цвет фона
        "color": "FFFFFF"    // Fill color / Цвет заполнения
    }
}
```

### 3. contrast
Enhances contrast for better recognition.

Улучшает контраст для лучшего распознавания.

```json
{
    "action": "contrast",
    "options": {
        "factor": 2.0    // 1.0 = no change, 2.0 = double contrast / 1.0 = без изменений, 2.0 = двойной контраст
    }
}
```

---

## Example Pipelines / Примеры пайплайнов

### For Japanese Visual Novels
### Для японских визуальных новелл

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
### Для русского текста с шумом

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
### Для английских субтитров

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

---

## Language Packs / языковые пакеты

Install additional languages / Установите дополнительные языки:

### Ubuntu/Debian
```bash
# All languages / Все языки
sudo apt-get install tesseract-ocr-all

# Specific languages / конкретные языки
sudo apt-get install tesseract-ocr-jpn tesseract-ocr-kor tesseract-ocr-chi-sim
```

### macOS
```bash
brew install tesseract-lang
```

### Windows
Languages included in installer. Additional packs available at:
https://github.com/tesseract-ocr/tessdata

Языки включены в установитель. Дополнительные пакеты доступны на:
https://github.com/tesseract-ocr/tessdata

---

## Performance Tips / Советы по производительности

1. **Use appropriate PSM mode**: Mode 6 works best for game UI
   **Используйте подходящий PSM режим**: Режим 6 лучше всего для игрового UI

2. **Reduce colors**: Binary (B/W) images are faster to process
   **Уменьшите цвета**: Бинарные (Ч/Б) изображения обрабатываются быстрее

3. **Adjust threshold**: Lower threshold (16-32) for clean text, higher (64+) for anti-aliased text
   **Настройте порог**: Меньший порог (16-32) для чистого текста, больший (64+) для anti-aliased текста

4. **Enable bbox fallback**: Set `use_bbox_fallback: true` if Tesseract doesn't return boxes
   **Включите bbox fallback**: Установите `use_bbox_fallback: true`, если Tesseract не возвращает boxes

5. **Pre-process images**: Use contrast enhancement for low-contrast text
   **Предварительно обработайте изображения**: Используйте улучшение контраста для низко-контрастного текста

---

## Troubleshooting / Решение проблем

### "No text found" / Текст не найден
- Check Tesseract installation: `tesseract --version` / Проверьте установку
- Verify language packs: `tesseract --list-langs` / Проверьте языковые пакеты
- Adjust threshold in preprocessing pipeline / Настройте порог в пайплайне
- Try different PSM mode / Попробуйте другой PSM режим

### Poor recognition quality / Плохое качество распознавания
- Increase contrast (factor 2.0-3.0) / Увеличьте контраст
- Lower threshold (16-24) for cleaner binary / Уменьшите порог
- Use `segFill` to remove noise / Используйте `segFill` для удаления шума
- Try PSM mode 3 instead of 6 / Попробуйте режим 3 вместо 6

### Slow performance / Медленная производительность
- Reduce image size before OCR / Уменьшите размер изображения
- Use simpler pipeline (fewer steps) / Используйте проще пайплайн
- Consider cloud OCR (OpenAI, Gemini) for speed / Рассмотрите облачный OCR для скорости

---

## Comparison: Tesseract vs Cloud OCR
## Сравнение: Tesseract vs облачный OCR

| Feature / Особенность | Tesseract | Cloud (OpenAI/Gemini) |
|---------|-----------|----------------------|
| **Cost** / Стоимость | Free / Бесплатно | $0.15-1.00/1K images |
| **Speed** / Скорость | Fast (local) / Быстро (локально) | Medium (network) / Средняя (сеть) |
| **Quality** / Качество | Good (clean text) / Хорошо (чистый текст) | Excellent (any text) / Отлично (любой текст) |
| **Languages** / Языки | 100+ | 50+ |
| **Privacy** / Приватность | ✅ Full privacy / Полная приватность | ❌ Data sent to cloud / Данные в облако |
| **Setup** / Установка | Requires installation / Требуется установка | API key only / Только ключ API |

**Recommendation**: Use Tesseract for development/testing, cloud OCR for production.

**Рекомендация**: Используйте Tesseract для разработки/тестирования, облачный OCR для production.
