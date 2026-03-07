# Local Models Guide (Ollama & vLLM)

## Overview

VGTranslate3 now supports **fully local OCR and translation** using Ollama and vLLM, enabling private, offline processing without cloud APIs.

## Architecture

```
Image → OCR → Translation → TTS
        ↓       ↓           ↓
     Ollama   Ollama     Google
     vLLM     vLLM       Piper
     LLaVA    Llama      (local)
```

## Installation

### Ollama (CPU-friendly, lightweight)

#### Linux/macOS
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llava:7b          # Vision OCR
ollama pull llama3.1:8b       # Translation (lightweight)
ollama pull llama3.1:70b      # Translation (high quality)
ollama pull mistral:7b        # Alternative translation
```

#### Windows
1. Download from https://ollama.ai/download
2. Install and run
3. Pull models via command prompt

### vLLM (GPU, high-performance)

#### Linux (CUDA)
```bash
# Install vLLM
pip install vllm

# Run server
vllm serve llava-hf/llava-1.5-7b-hf \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 4096

# For translation (Llama 3.1)
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 8192
```

#### Requirements
- NVIDIA GPU (8GB+ VRAM for 7B, 24GB+ for 70B)
- CUDA 11.8+
- 32GB+ RAM for 70B models

## Configuration

### Full Local Setup (Ollama)

```bash
cp config_example/config_ollama_local.json src/vgtranslate3/config.json
```

Edit `config.json`:
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

```bash
cp config_example/config_hybrid_ollama_groq.json src/vgtranslate3/config.json
```

```json
{
    "ocr_provider": "ollama",      # Local, private
    "ocr_model": "llava:7b",
    
    "translation_provider": "groq", # Fast, cheap
    "translation_model": "llama-3.1-70b-versatile",
    
    "groq_api_key": "grq_..."
}
```

## Model Recommendations

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

## Performance Comparison

### Ollama (CPU)
- **llava:7b**: ~5-10 seconds per image
- **llama3.1:8b**: ~2-5 seconds per translation
- **llama3.1:70b**: ~20-40 seconds per translation

### vLLM (GPU A100)
- **llava-1.5-7b**: ~0.5-1 seconds per image
- **Llama-3.1-70B**: ~1-3 seconds per translation

### Cloud (for reference)
- **OpenAI gpt-4o**: ~2-3 seconds
- **Groq**: ~0.3-0.5 seconds (fastest)
- **DeepSeek**: ~1-2 seconds

## Troubleshooting

### "Connection refused"
```bash
# Check Ollama is running
ollama list
# Start if needed
ollama serve

# Check vLLM is running
curl http://localhost:8000/v1/models
```

### "Model not found"
```bash
# Pull model
ollama pull llava:7b
# Or for vLLM, ensure model is downloaded:
python -c "from transformers import AutoModel; AutoModel.from_pretrained('llava-hf/llava-1.5-7b-hf')"
```

### Slow performance
- **Ollama**: Use smaller models (8b instead of 70b)
- **vLLM**: Enable quantization (FP8, INT4)
- Increase timeout: `"ollama_timeout": 180`

### Poor OCR quality
- Try larger model: `llava:34b`
- Adjust prompt in provider code
- Enable bbox fallback: `"use_bbox_fallback": true`

## Privacy & Security

### Fully Local
✅ No data sent to cloud
✅ GDPR compliant
✅ Works offline
✅ No API costs

### Hybrid
✅ OCR is local (private)
⚠️ Translation goes to cloud
✅ Faster than full local

### Comparison

| Setup | Privacy | Speed | Cost | Quality |
|-------|---------|-------|------|---------|
| **Full Local** | ✅✅✅ | ⚠️ | ✅ | ⚠️ |
| **Hybrid** | ✅✅ | ✅✅ | ✅✅ | ✅✅ |
| **Full Cloud** | ⚠️ | ✅✅✅ | ⚠️ | ✅✅✅ |

## Advanced Usage

### Custom Ollama Prompts

Edit `local_ocr_providers.py` to customize OCR prompt:
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

### Quantization (reduce VRAM)

```bash
# Ollama (already quantized by default)
ollama pull llama3.1:8b-q4  # 4-bit quantized

# vLLM (AWQ quantization)
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --quantization awq
```

## Testing Without API Keys

Create test config:
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

Test with dummy image:
```bash
python -m src.vgtranslate3.serve &
curl -X POST "http://127.0.0.1:4404/?source_lang=jpn&target_lang=en" \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,..."}'
```

## Cost Comparison

### Full Local
- **Hardware**: $500-2000 (GPU)
- **Running**: $0.05/hour (electricity)
- **Privacy**: ✅ Full

### Cloud OCR+Translation
- **OpenAI**: ~$0.50 per 1000 images
- **Groq**: ~$0.10 per 1000 images
- **DeepSeek**: ~$0.05 per 1000 images

### Break-even
Local setup pays off after ~100,000 images vs cloud.

## Recommendations

### For Development
- **Ollama + llama3.1:8b**: Fast iteration, no costs
- Test locally before deploying

### For Production
- **vLLM + Llama-3.1-70B**: Best quality/speed
- **Hybrid (Ollama + Groq)**: Balance privacy & speed

### For Privacy-Sensitive
- **Full Ollama**: Complete offline processing
- No data leaves your machine
