# Benchmark Testing Guide

## Purpose

This guide provides instructions for manual quality testing of OCR and translation in VGTranslate3.

## Test Images

### Recommended Test Sets

1. **Japanese Visual Novels**
   - Text: Mixed kanji/hiragana/katakana
   - Background: Often gradient or patterned
   - Font sizes: Variable (12-24px)

2. **Russian Text**
   - Text: Cyrillic alphabet
   - Common in: RPGs, strategy games
   - Font: Often condensed or serif

3. **English UI**
   - Text: Latin alphabet
   - Clean backgrounds
   - Standard fonts (Arial, Roboto)

4. **Chinese Text**
   - Text: Simplified/traditional characters
   - Dense text blocks
   - Small font sizes

## Quality Metrics

### OCR Accuracy

| Score | Description | Criteria |
|-------|-------------|----------|
| 5 | Excellent | 95-100% characters correct |
| 4 | Good | 85-94% characters correct |
| 3 | Acceptable | 70-84% characters correct |
| 2 | Poor | 50-69% characters correct |
| 1 | Unusable | <50% characters correct |

### Translation Quality

| Score | Description | Criteria |
|-------|-------------|----------|
| 5 | Excellent | Natural, accurate, preserves tone |
| 4 | Good | Accurate but slightly unnatural |
| 3 | Acceptable | Understandable but awkward |
| 2 | Poor | Missing meaning, errors |
| 1 | Unusable | Incorrect or gibberish |

### Bounding Box Alignment

| Score | Description | Criteria |
|-------|-------------|----------|
| 5 | Perfect | Boxes align exactly with text |
| 4 | Good | Minor offset (<2px) |
| 3 | Acceptable | Noticeable but usable (2-5px) |
| 2 | Poor | Significant misalignment (5-10px) |
| 1 | Unusable | Wrong position (>10px) |

## Testing Procedure

### 1. Prepare Test Image

```bash
# Copy test image to working directory
cp tests/benchmark/test_image_jpn.png ./
```

### 2. Run Server

```bash
# Load config
cp config_example/config_openai.json src/vgtranslate3/config.json

# Start server
python -m src.vgtranslate3.serve
```

### 3. Make Request

```bash
# Test OCR + translation
curl -X POST "http://localhost:4404/?source_lang=jpn&target_lang=en&output=image" \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,..."}' > output.json
```

### 4. Extract Results

```bash
# Parse output
python3 -c "
import json
data = json.load(open('output.json'))
print('OCR text:', data.get('blocks', [{}])[0].get('source_text'))
print('Translation:', data.get('blocks', [{}])[0].get('translation', {}).get('en'))
print('Bounding box:', data.get('blocks', [{}])[0].get('bounding_box'))
"
```

### 5. Visual Inspection

```bash
# Save translated image
python3 -c "
import json, base64
from PIL import Image
data = json.load(open('output.json'))
img_data = base64.b64decode(data['image'])
Image.open(Image.open(img_data)).save('output.png')
"

# Open and compare
# - Check text placement
# - Check font readability
# - Check background preservation
```

### 6. Score Quality

Fill in the score sheet:

```
Test: Japanese Visual Novel
Date: 2026-03-07
Provider: OpenAI (gpt-4o-mini)

OCR Accuracy: □5 □4 □3 □2 □1
Translation Quality: □5 □4 □3 □2 □1
Bounding Box: □5 □4 □3 □2 □1

Comments:
- Text detected correctly: [yes/no]
- Kanji recognition: [good/partial/bad]
- Translation naturalness: [natural/awkward/wrong]
```

## Provider Comparison

### Cloud Providers

| Provider | OCR Quality | Translation | Speed | Cost |
|----------|-------------|-------------|-------|------|
| OpenAI gpt-4o | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | $$$ |
| Gemini 1.5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |
| Google Vision | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |
| Yandex OCR | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |

### Local Providers

| Provider | OCR Quality | Translation | Speed | Privacy |
|----------|-------------|-------------|-------|---------|
| Ollama LLaVA:7b | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| Ollama LLaVA:34b | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| vLLM LLaVA-1.5 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Tesseract

| Pipeline | OCR Quality | Speed | Best For |
|----------|-------------|-------|----------|
| Basic (no preprocessing) | ⭐⭐ | ⭐⭐⭐⭐⭐ | Clean text |
| reduceToMultiColor + contrast | ⭐⭐⭐ | ⭐⭐⭐⭐ | Game UI |
| Full pipeline (all steps) | ⭐⭐⭐⭐ | ⭐⭐⭐ | Complex backgrounds |

## Test Checklist

### For Each Provider:

□ Test with Japanese text (kanji/hiragana/katakana)
□ Test with Russian text (cyrillic)
□ Test with English text (latin)
□ Test with Chinese text (if applicable)
□ Test with small font (12px)
□ Test with large font (24px+)
□ Test with gradient background
□ Test with patterned background
□ Test with solid background
□ Test bounding box alignment
□ Test translation quality
□ Test TTS output (if enabled)

## Recording Results

Create a test log:

```markdown
## Test Log: 2026-03-07

### Configuration
- Provider: OpenAI gpt-4o-mini
- Config: config_openai.json
- Image: test_jpn_vn_001.png

### Results
- OCR: 5/5 (all characters correct)
- Translation: 4/5 (natural but slight awkwardness)
- Bounding Box: 5/5 (perfect alignment)
- TTS: N/A

### Notes
- Excellent kanji recognition
- Hiragana detected perfectly
- Some anti-aliasing issues with small text
```

## Automation Hooks

For semi-automated testing:

```bash
# Run benchmark script
python3 tests/benchmark/run_benchmark.py \
  --provider openai \
  --image tests/benchmark/test_jpn_vn_001.png \
  --target en \
  --output results/
```

## Performance Baselines

Expected quality baselines:

- **OpenAI gpt-4o**: OCR 95%, Translation 90%
- **Gemini 1.5**: OCR 93%, Translation 88%
- **Google Vision**: OCR 90%, Translation 85%
- **Ollama LLaVA:7b**: OCR 75%, Translation 70%
- **Tesseract (optimized)**: OCR 80%, N/A

## Reporting Issues

When reporting quality issues:

1. Include test image
2. Specify provider and model
3. Provide OCR output
4. Provide translation output
5. Note bounding box issues
6. Score quality (1-5)
