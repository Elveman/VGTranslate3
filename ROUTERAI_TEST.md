# Тестирование RouterAI OCR

## Быстрая проверка

1. **Настройте API ключ** в `src/vgtranslate3/config.json`:
   ```json
   {
     "openai_api_key": "ra_ваш_ключ_от_routerai",
     "openai_ocr_model": "google/gemini-2.5-flash",
     "openai_base_url": "https://routerai.ru/api/v1"
   }
   ```

2. **Запустите тестовый скрипт**:
   ```bash
   python3 test_routerai_ocr.py tests/hello.png
   ```

3. **Или отправьте запрос через curl**:
   ```bash
   # Запустить сервер
   python3 -m src.vgtranslate3.serve
   
   # Отправить картинку
   curl -X POST "http://localhost:4404/service?target_lang=en" \
     -H "Content-Type: application/json" \
     -d '{"image": "'$(base64 -w0 tests/hello.png)'"}'
   ```

## Совместимость с RouterAI API

Код полностью совместим с документацией RouterAI:

✅ **Endpoint**: `/api/v1/chat/completions`
✅ **Формат изображений**: Base64 data URL (`data:image/png;base64,...`)
✅ **Поддерживаемые типы**: PNG, JPEG, WebP, GIF (авто-определение)
✅ **Структура запроса**: `messages[].content[]` с `type: "image_url"`
✅ **Порядок**: Текст перед изображением (рекомендуется RouterAI)
✅ **Заголовки**: `X-Title: VGTranslate3` для routerai.ru

## Рекомендуемые модели RouterAI для OCR

| Модель | Описание | Цена |
|--------|----------|------|
| `google/gemini-2.5-flash` | Лучшая для OCR | $ |
| `google/gemini-2.0-flash` | Быстрая и точная | $ |
| `openai/gpt-4o-mini` | Хорошее качество | $$ |
| `anthropic/claude-3.5-haiku` | Отлично для текста | $$ |

## Проверка без сервера

```bash
python3 test_routerai_ocr.py tests/hello.png
```

Скрипт:
- Загружает конфиг
- Кодирует изображение в base64
- Определяет MIME тип (PNG/JPEG/WebP)
- Отправляет запрос напрямую в RouterAI
- Показывает распознанный текст и bounding boxes

## Структура ответа

```json
{
  "blocks": [
    {
      "text": "こんにちは",
      "bbox": {"x": 10, "y": 20, "width": 100, "height": 20},
      "language": "jpn"
    }
  ],
  "detected_language": "jpn"
}
```
