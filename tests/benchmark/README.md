# Benchmark Testing Guide
# Руководство по тестированию производительности

## Purpose / Назначение

This guide provides instructions for manual quality testing of OCR and translation in VGTranslate3.

Это руководство предоставляет инструкции по ручному тестированию качества OCR и перевода в VGTranslate3.

---

## Test Images / Тестовые изображения

### Recommended Test Sets / Рекомендуемые наборы тестов

1. **Japanese Visual Novels / Японские визуальные новеллы**
   - Text: Mixed kanji/hiragana/katakana / Смешанные кандзи/хирагана/катакана
   - Background: Often gradient or patterned / Часто градиентный или узорчатый
   - Font sizes: Variable (12-24px) / Размеры шрифта: переменные

2. **Russian Text / Русский текст**
   - Text: Cyrillic alphabet / Кириллица
   - Common in: RPGs, strategy games / Встречается в: RPG, стратегиях
   - Font: Often condensed or serif / Шрифт: часто узкий или с засечками

3. **English UI / Английский UI**
   - Text: Latin alphabet / Латиница
   - Clean backgrounds / Чистые фоны
   - Standard fonts (Arial, Roboto) / Стандартные шрифты

4. **Chinese Text / Китайский текст**
   - Text: Simplified/traditional characters / Упрощённые/традиционные иероглифы
   - Dense text blocks / Плотные блоки текста
   - Small font sizes / Маленькие размеры шрифта

---

## Quality Metrics / Метрики качества

### OCR Accuracy / Точность OCR

| Score / Оценка | Description / Описание | Criteria / Критерии |
|-------|-------------|----------|
| 5 | Excellent / Отлично | 95-100% characters correct / символов верно |
| 4 | Good / Хорошо | 85-94% characters correct |
| 3 | Acceptable / Приемлемо | 70-84% characters correct |
| 2 | Poor / Плохо | 50-69% characters correct |
| 1 | Unusable / Негодно | <50% characters correct |

### Translation Quality / Качество перевода

| Score / Оценка | Description / Описание | Criteria / Критерии |
|-------|-------------|----------|
| 5 | Excellent / Отлично | Natural, accurate, preserves tone / Естественный, точный, сохраняет тон |
| 4 | Good / Хорошо | Accurate but slightly unnatural / Точный, но немного неестественный |
| 3 | Acceptable / Приемлемо | Understandable but awkward / Понятный, но неуклюжий |
| 2 | Poor / Плохо | Missing meaning, errors / Потеря смысла, ошибки |
| 1 | Unusable / Негодно | Incorrect or gibberish / Неправильный или бессмыслица |

### Bounding Box Alignment / Выравнивание bounding box

| Score / Оценка | Description / Описание | Criteria / Критерии |
|-------|-------------|----------|
| 5 | Perfect / Идеально | Boxes align exactly with text / Box точно совпадает с текстом |
| 4 | Good / Хорошо | Minor offset (<2px) / Небольшое смещение |
| 3 | Acceptable / Приемлемо | Noticeable but usable (2-5px) / Заметно, но пригодно |
| 2 | Poor / Плохо | Significant misalignment (5-10px) / Значительное несовпадение |
| 1 | Unusable / Негодно | Wrong position (>10px) / Неправильная позиция |

---

## Testing Procedure / Процедура тестирования

### 1. Prepare Test Image / Подготовьте тестовое изображение

```bash
# Copy test image to working directory / Скопируйте тестовое изображение
cp tests/benchmark/test_image_jpn.png ./
```

### 2. Run Server / Запустите сервер

```bash
# Load config / Загрузите конфиг
cp config_example/config_openai.json src/vgtranslate3/config.json

# Start server / Запустите сервер
python -m src.vgtranslate3.serve
```

### 3. Make Request / Сделайте запрос

```bash
# Test OCR + translation / Тест OCR + перевода
curl -X POST "http://localhost:4404/?source_lang=jpn&target_lang=en&output=image" \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,..."}' > output.json
```

### 4. Extract Results / Извлеките результаты

```bash
# Parse output / Разберите вывод
python3 -c "
import json
data = json.load(open('output.json'))
print('OCR text:', data.get('blocks', [{}])[0].get('source_text'))
print('Translation:', data.get('blocks', [{}])[0].get('translation', {}).get('en'))
print('Bounding box:', data.get('blocks', [{}])[0].get('bounding_box'))
"
```

### 5. Visual Inspection / Визуальная проверка

```bash
# Save translated image / Сохраните переведённое изображение
python3 -c "
import json, base64
from PIL import Image
data = json.load(open('output.json'))
img_data = base64.b64decode(data['image'])
Image.open(Image.open(img_data)).save('output.png')
"

# Open and compare / Откройте и сравните
# - Check text placement / Проверьте размещение текста
# - Check font readability / Проверьте читаемость шрифта
# - Check background preservation / Проверьте сохранение фона
```

### 6. Score Quality / Оцените качество

Fill in the score sheet / Заполните лист оценки:

```
Test: Japanese Visual Novel / Японская визуальная новелла
Date: 2026-03-07
Provider: OpenAI (gpt-4o-mini)

OCR Accuracy: □5 □4 □3 □2 □1 / Точность OCR
Translation Quality: □5 □4 □3 □2 □1 / Качество перевода
Bounding Box: □5 □4 □3 □2 □1 / Выравнивание

Comments / Комментарии:
- Text detected correctly: [yes/no] / Текст распознан верно
- Kanji recognition: [good/partial/bad] / Распознавание кандзи
- Translation naturalness: [natural/awkward/wrong] / Естественность перевода
```

---

## Provider Comparison / Сравнение провайдеров

### Cloud Providers / Облачные провайдеры

| Provider | OCR Quality | Translation | Speed | Cost |
|----------|-------------|-------------|-------|------|
| OpenAI gpt-4o | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | $$$ |
| Gemini 1.5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |
| Google Vision | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |
| Yandex OCR | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |

### Local Providers / Локальные провайдеры

| Provider | OCR Quality | Translation | Speed | Privacy |
|----------|-------------|-------------|-------|---------|
| Ollama LLaVA:7b | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| Ollama LLaVA:34b | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| vLLM LLaVA-1.5 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Tesseract

| Pipeline | OCR Quality | Speed | Best For |
|----------|-------------|-------|----------|
| Basic (no preprocessing) | ⭐⭐ | ⭐⭐⭐⭐⭐ | Clean text / Чистый текст |
| reduceToMultiColor + contrast | ⭐⭐⭐ | ⭐⭐⭐⭐ | Game UI / Игровой UI |
| Full pipeline (all steps) | ⭐⭐⭐⭐ | ⭐⭐⭐ | Complex backgrounds / Сложные фоны |

---

## Test Checklist / Контрольный список тестов

### For Each Provider / Для каждого провайдера:

□ Test with Japanese text (kanji/hiragana/katakana) / Японский текст
□ Test with Russian text (cyrillic) / Русский текст
□ Test with English text (latin) / Английский текст
□ Test with Chinese text (if applicable) / Китайский текст
□ Test with small font (12px) / Маленький шрифт
□ Test with large font (24px+) / Большой шрифт
□ Test with gradient background / Градиентный фон
□ Test with patterned background / Узорчатый фон
□ Test with solid background / Сплошной фон
□ Test bounding box alignment / Выравнивание bounding box
□ Test translation quality / Качество перевода
□ Test TTS output (if enabled) / TTS вывод

---

## Recording Results / Запись результатов

Create a test log / Создайте журнал тестов:

```markdown
## Test Log: 2026-03-07

### Configuration / Конфигурация
- Provider: OpenAI gpt-4o-mini
- Config: config_openai.json
- Image: test_jpn_vn_001.png

### Results / Результаты
- OCR: 5/5 (all characters correct / все символы верны)
- Translation: 4/5 (natural but slight awkwardness / естественный, но немного неуклюжий)
- Bounding Box: 5/5 (perfect alignment / идеальное выравнивание)
- TTS: N/A

### Notes / Примечания
- Excellent kanji recognition / Отличное распознавание кандзи
- Hiragana detected perfectly / Хирагана распознана идеально
- Some anti-aliasing issues with small text / Проблемы anti-aliasing с маленьким текстом
```

---

## Automation Hooks / Хуки автоматизации

For semi-automated testing / Для полуавтоматического тестирования:

```bash
# Run benchmark script / Запустите benchmark скрипт
python3 tests/benchmark/run_benchmark.py \
  --provider openai \
  --image tests/benchmark/test_jpn_vn_001.png \
  --target en \
  --output results/
```

---

## Performance Baselines / Базовые показатели

Expected quality baselines / Ожидаемые базовые показатели:

- **OpenAI gpt-4o**: OCR 95%, Translation 90%
- **Gemini 1.5**: OCR 93%, Translation 88%
- **Google Vision**: OCR 90%, Translation 85%
- **Ollama LLaVA:7b**: OCR 75%, Translation 70%
- **Tesseract (optimized)**: OCR 80%, N/A

---

## Reporting Issues / Сообщение о проблемах

When reporting quality issues / При сообщении о проблемах качества:

1. Include test image / Приложите тестовое изображение
2. Specify provider and model / Укажите провайдера и модель
3. Provide OCR output / Предоставьте вывод OCR
4. Provide translation output / Предоставьте вывод перевода
5. Note bounding box issues / Отметьте проблемы bounding box
6. Score quality (1-5) / Оцените качество (1-5)
