#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations   # если хотите «отложенные» аннотации (Py ≥ 3.7)

# — стандартная библиотека —
import sys
import os
import time
import json
import threading
import re
import base64
import http.server
import http.client
import urllib.parse
from html import unescape
from typing import Optional, Tuple, Any, Dict, List

# — сторонние пакеты —
from PIL import Image, ImageEnhance, ImageDraw

# — внутренние модули проекта —
from . import config
from .util import (
    load_image, image_to_string, fix_neg_width_height, image_to_string_format,
    swap_red_blue, segfill, reduce_to_multi_color, reduce_to_text_color,
    color_hex_to_byte
)
from . import screen_translate
from . import imaging
from . import ocr_tools
from .text_to_speech import TextToSpeech

#dictionary going from ISO-639-1 to ISO-639-2/T language codes (mostly):
lang_2_to_3 = {
  "ja": "jpn",
  "de": "deu", 
  "en": "eng",
  "es": "spa",
  "fr": "fra",
  "zh": "zho",
  "zh-CN": "zho",#BCP-47
  "zh-TW": "zho",#BCP-47
  "nl": "nld",
  "it": "ita",
  "pt": "por",
  "ru": "rus"
}

USE_ESPEAK = False

g_debug_mode = 0

SOUND_FORMATS = {"wav": 1}
IMAGE_FORMATS = {"bmp": 1, "png": 1}

server_thread = None
window_obj = None
httpd_server = None

class ServerOCR(object):
    @classmethod
    def _preprocess_color(cls, image_data, colors="FFFFFF"):
        img = load_image(image_data)
        bg = "000000"
        if colors.lower().strip() == "detect":
            pass
        elif colors:
            try:
                colors = [x.strip() for x in re.split("[, ;]", colors)]
                new_colors = list()
                for color in colors:
                    if not color:
                        continue
                    if color[:2].lower() == "bg":
                        bg = color[2:8]
                    else:
                        c = color[:6]
                        if len(color)>6:
                            try:
                                num = int(color[6:])
                            except:
                                num = 32
                        else:
                            num = 32
                        new_colors.append([color, num])
                img = reduce_to_text_color(img, new_colors, bg)
            except:
                raise
        return bg, image_to_string(img.convert("RGBA"))
    @classmethod
    def _preprocess_image(cls, image_data, contrast=2.0):
        img = load_image(image_data)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
        return image_to_string(img)

    @classmethod
    def _preprocess_box(cls, image_data, box, bg):
        try:
            box2 = [int(x) for x in box.split(",")]
            box = {"x1": box2[0], "y1": box2[1],
                   "x2": box2[2], "y2": box2[3]}
        except:
            return image_data

        img = load_image(image_data).convert("RGB")
        draw = ImageDraw.Draw(img)
        bg = color_hex_to_byte(bg)
        fill_color = bg

        recs = [[0,0,img.width, box['y1']-1],
                [0,box['y2'], img.width, img.height],
                [0,0, box['x1']-1, img.height],
                [box['x2'], 0, img.width, img.height]]

        for rec in recs:
            if rec[0] < 0:
                rec[0] = 0
            if rec[0] > img.width:
                rec[0] = img.width
            if rec[1] < 0:
                rec[1] = 0
            if rec[1] > img.height:
                rec[1] = img.height

            if rec[2] < 0:
                rec[2] = 0
            if rec[2] > img.width:
                rec[2] = img.width
            if rec[3] < 0:
                rec[3] = 0
            if rec[3] > img.height:
                rec[3] = img.height
            draw.rectangle(rec, fill=fill_color)
        return image_to_string(img)



class APIHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<html><head><title></title></head></html>")
        self.wfile.write("<body>yo!</body></html>")
        
    def do_POST(self):
        print("____")
        query = urllib.parse.urlparse(self.path).query
        if query.strip():
            query_components = dict(qc.split("=") for qc in query.split("&"))
        else:
            query_components = {}
        content_length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(content_length)
        print(data[:100])
        print(content_length)
        print(data[-100:])
        data = json.loads(data)
        
        start_time = time.time()
        
        result = self._process_request(data, query_components)
        #result['auto'] = 'auto'
        print("AUTO AUTO")
        print(['Request took: ', time.time()-start_time])
        output_str   = json.dumps(result, ensure_ascii=False)
        output_bytes = output_str.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(output_bytes)))
        self.end_headers()

        print("Output length:", len(output_bytes))
        self.wfile.write(output_bytes)

    def _process_request(self, body, query):
        source_lang = query.get("source_lang")
        target_lang = query.get("target_lang", "en")
        mode = query.get("mode", "fast")
        request_output = query.get("output", "image,sound").lower()
        request_output = request_output.split(",")

        request_out_dict = dict()
        alpha = False
        error_string = ""

        for entry in request_output:
            if entry =='image' and not 'image' in request_out_dict:
                request_out_dict['image'] = 'bmp'
            elif entry == 'sound' and not 'sound' in request_out_dict:
                request_out_dict['sound'] = 'wav'
            else:
                if SOUND_FORMATS.get(entry):
                     request_out_dict['sound'] = entry
                else:
                     if entry[-2:] == "-a":
                         request_out_dict['image'] = entry[:-2]
                         alpha = True
                     else:
                         request_out_dict['image'] = entry

        print(request_output)
        pixel_format = "RGB"
        image_data = body.get("image")
        
        image_object = load_image(image_data).convert("RGB")
        print("w: "+str(image_object.width)+" h: "+str(image_object.height))
        if pixel_format == "BGR": 
            image_object = image_object.convert("RGB")
            image_object = swap_red_blue(image_object)
        
        result = {}
        if window_obj and config.local_server_api_key_type == "free":
            #TODO
            pass
        elif config.local_server_api_key_type == "ztranslate":
            image_object = load_image(image_data)

            if "image" not in request_out_dict and mode != "normal":
                image_object = image_object.convert("LA").convert("RGB")
                image_object = image_object.convert("P", palette=Image.Palette.ADAPTIVE, colors=32)
            else:
                image_object = image_object.convert("P", palette=Image.Palette.ADAPTIVE)

            #pass the call onto the ztranslate service api...

            body_kwargs = dict()
            for key in body:
                if key != "image":
                    body_kwargs[key] = body[key]
            
            image_data = image_to_string(image_object)
            output = screen_translate.CallService.call_service(image_data, 
                                                               source_lang, target_lang,
                                                               mode=mode,
                                                               request_output=request_output, body_kwargs=body_kwargs)
            return output
        elif config.local_server_api_key_type == "google":
            print("using google......")
            if "image" not in request_out_dict:
                image_object = load_image(image_data).convert("LA").convert("RGB")
                image_object = image_object.convert("P", palette=Image.Palette.ADAPTIVE, colors=32)
            else:
                image_object = load_image(image_data).convert("P", palette=Image.Palette.ADAPTIVE)

            image_data = image_to_string(image_object)
            confidence = config.ocr_confidence
            if confidence is None:
                confidence = 0.6
            bg="000000"
            if config.ocr_color:
                bg, image_data = ServerOCR._preprocess_color(image_data, config.ocr_color)
            if config.ocr_contrast and abs(config.ocr_contrast-1.0)> 0.0001:
                image_data = ServerOCR._preprocess_image(image_data, config.ocr_contrast)
            if config.ocr_box:
                image_data = ServerOCR._preprocess_box(image_data, config.ocr_box, bg)

            print(len(image_data))

            api_ocr_key = config.local_server_ocr_key
            api_translation_key = config.local_server_translation_key
            
            data, raw_output = self.google_ocr(image_data, source_lang, api_ocr_key)
            if not data:
                error_string = "No text found."

            data = self.process_output(data, raw_output, image_data,
                                       source_lang, confidence=confidence)
            data = self.translate_output(data, target_lang,
                                         source_lang=source_lang,
                                         google_api_key=api_translation_key)
        
            output_data = {}
            if "sound" in request_out_dict:
                mp3_out = self.text_to_speech(data, target_lang=target_lang, 
                                              format_type=request_out_dict['sound'])
                output_data['sound'] = mp3_out

            if window_obj:
                output_image = imaging.ImageModder.write(image_object, data, target_lang)
                window_obj.load_image_object(output_image)
                window_obj.curr_image = imaging.ImageIterator.prev()
            
            if "image" in request_out_dict:
                if alpha:
                    image_object = Image.new("RGBA", 
                                             (image_object.width, image_object.height),
                                             (0,0,0,0))
                output_image = imaging.ImageModder.write(image_object, data, target_lang)
 
                if pixel_format == "BGR": 
                    output_image = output_image.convert("RGB")
                    output_image = swap_red_blue(output_image)
                
                output_data["image"] = image_to_string_format(output_image, request_out_dict['image'],mode="RGBA")

            if error_string:
                output_data['error'] = error_string
            return output_data

        elif config.local_server_api_key_type == "yandex":
            print("using yandex......")
            if "image" not in request_out_dict:
                image_object = load_image(image_data).convert("LA").convert("RGB")
                image_object = image_object.convert("P", palette=Image.Palette.ADAPTIVE, colors=32)
            else:
                image_object = load_image(image_data).convert("P", palette=Image.Palette.ADAPTIVE)

            image_data = image_to_string(image_object)
            confidence = config.ocr_confidence
            if confidence is None:
                confidence = 0.6
            bg="000000"
            if config.ocr_color:
                bg, image_data = ServerOCR._preprocess_color(image_data, config.ocr_color)
            if config.ocr_contrast and abs(config.ocr_contrast-1.0)> 0.0001:
                image_data = ServerOCR._preprocess_image(image_data, config.ocr_contrast)
            if config.ocr_box:
                image_data = ServerOCR._preprocess_box(image_data, config.ocr_box, bg)


            api_ocr_key = config.yandex_ocr_key
            api_translation_key = config.yandex_translation_key
            iam_token = config.yandex_iam_token
            folder_id = config.yandex_folder_id

            output_data = {}

            if not folder_id:
                error_string = "No folder id found."
                output_data['error'] = error_string
                return output_data

            data, raw_output = self.yandex_ocr(image_data, source_lang, folder_id, iam_token, api_ocr_key)
            if not data:
                error_string = "No text found."

            data = self.process_output(data, raw_output, image_data,
                                       source_lang, confidence=confidence)
            data = self.translate_output(data, target_lang,
                                         source_lang=source_lang,
                                         yandex_api_key=api_translation_key,
                                         yandex_iam_token=iam_token,
                                         yandex_folder_id=folder_id,
                                         provider="yandex")

            if "sound" in request_out_dict:
                mp3_out = self.text_to_speech(data, target_lang=target_lang,
                                              format_type=request_out_dict['sound'])
                output_data['sound'] = mp3_out

            if window_obj:
                output_image = imaging.ImageModder.write(image_object, data, target_lang)
                window_obj.load_image_object(output_image)
                window_obj.curr_image = imaging.ImageIterator.prev()

            if "image" in request_out_dict:
                if alpha:
                    image_object = Image.new("RGBA",
                                             (image_object.width, image_object.height),
                                             (0,0,0,0))
                output_image = imaging.ImageModder.write(image_object, data, target_lang)

                if pixel_format == "BGR":
                    output_image = output_image.convert("RGB")
                    output_image = swap_red_blue(output_image)

                output_data["image"] = image_to_string_format(output_image, request_out_dict['image'],mode="RGBA")

            if error_string:
                output_data['error'] = error_string
            return output_data

        elif config.local_server_api_key_type == "tess_google":
            image_object = load_image(image_data).convert("P", palette=Image.Palette.ADAPTIVE)
            image_data = image_to_string(image_object)
            output_data = {}
 

            api_translation_key = config.local_server_translation_key
            ocr_processor = config.local_server_ocr_processor
            data, source_lang = self.tess_ocr(image_data, source_lang, ocr_processor)
            if not data.get("blocks"):
                error_string = "No text found."
            data = self.translate_output(data, target_lang,
                                         source_lang=source_lang,
                                         google_api_key=api_translation_key)
            if alpha:
                image_object = Image.new("RGBA", 
                                         (image_object.width, image_object.height),
                                         (0,0,0,0))
            output_image = imaging.ImageModder.write(image_object, data, target_lang)
            if window_obj:
                window_obj.load_image_object(output_image)
                window_obj.curr_image = imaging.ImageIterator.prev()
 
            if pixel_format == "BGR":
                output_image = output_image.convert("RGB")
                output_image = swap_red_blue(output_image)
            output_data["image"] = image_to_string_format(output_image, request_out_dict['image'],mode="RGBA")
            if error_string:
                output_data['error'] = error_string
            return output_data

    def text_to_speech(self, data, target_lang=None, format_type=None):
        texts = list()
        texts2 = list()
        i = 0
        for block in sorted(data['blocks'], key=lambda x: (x['bounding_box']['y'], x['bounding_box']['x'])):
            i+=1
            text = block['translation'][block['target_lang'].lower()]
            this_text = "Textbox "+str(i)+": "+"[] "*3 + text + " "+"[] "*6
            texts.append(this_text)
            texts2.append(text)

        if USE_ESPEAK:
            text_to_say = "".join(texts).replace('"', " [] ")
            cmd = "espeak "+'"'+text_to_say+'"'+" --stdout > tts_out.wav"
            os.system(cmd)#, shell=True)
            wav_data = open("tts_out.wav").read()
        else:
            text_to_say = " ".join(texts2).replace("...", " [] ").replace(" ' s ", "'s ").replace(" ' t ", "'t ").replace(" ' re ", "'re ").replace(" ' m ", "'m ").replace("' ", "").replace(" !", "!").replace('"', " [] ")
            print([text_to_say])
            wav_data = TextToSpeech.text_to_speech_api(
                text_to_say,
                source_lang=target_lang,
                provider=config.local_server_api_key_type   # "google" | "yandex"
            )

        wav_data = self.fix_wav_size(wav_data)
        # wav_data может прийти как str (unicode) - превращаем в bytes
        if isinstance(wav_data, str):
            wav_data = wav_data.encode("utf-8")

        wav_data = base64.b64encode(wav_data).decode("ascii")
        return wav_data



    def fix_wav_size(self, wav: bytes) -> bytes:
        """Правит поля RIFF-заголовка (bytes 4-7 и 40-43) со
        сводным и фактическим размером WAV-данных."""
        def tb(size: int) -> bytearray:
            # little-endian разложение на 4 байта
            return bytearray((
                size & 0xFF,
                (size >> 8)  & 0xFF,
                (size >> 16) & 0xFF,
                (size >> 24) & 0xFF
            ))

        size1 = tb(len(wav))        # RIFF chunk size
        size2 = tb(len(wav) - 44)   # data sub-chunk size

        s = bytearray(wav)
        s[4:8]   = size1            # bytes 4-7
        s[40:44] = size2            # bytes 40-43
        return bytes(s)



    def google_ocr(
            self,
            image_data: bytes | str,
            source_lang: str | None,
            ocr_api_key: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        OCR через Google Vision v1 (REST).
        Возвращает (fullTextAnnotation | {}, сырой JSON-ответ).
        """
        # 1. Готовим base64-строку
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode("ascii")
        else:                       # уже str; убираем data-URI при необходимости
            image_b64 = image_data.split(",", 1)[-1]

        # 2. Собираем тело запроса
        req: Dict[str, Any] = {
            "requests": [{
                "image": {"content": image_b64},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
            }]
        }
        if source_lang:
            req["requests"][0]["imageContext"] = {"languageHints": [source_lang]}

        body = json.dumps(req, ensure_ascii=False).encode("utf-8")

        # 3. Отправляем POST /v1/images:annotate
        uri = f"/v1/images:annotate?key={ocr_api_key}"
        headers = {"Content-Type": "application/json; charset=utf-8"}

        data = self._send_request(
            "vision.googleapis.com", 443, uri, "POST", body, headers
        )
        output: Dict[str, Any] = json.loads(data)

        # 4. Разбираем ответ / ошибки
        if "error" in output:
            print("Google Vision error:", output["error"])
            return {}, output

        annotation = (
            output.get("responses", [{}])[0].get("fullTextAnnotation", {})
        )
        return annotation, output



    def yandex_ocr(
            self,
            image_data: bytes | str,
            source_lang: str | None,
            folder_id: str,                # каталог облака, обязателен
            iam_token: str | None = None,  # либо
            api_key:  str | None = None,   # один из двух способов auth
            mime_type: str | None = None,   # можно указать явно
            model: str | None = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Синхронное распознавание текста через REST-метод
        POST https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText
        Подробнее: Vision OCR REST API :contentReference[oaicite:0]{index=0}
        """

        # --------------------------------------------------------------
        # 1. base64-кодирование
        # --------------------------------------------------------------
        if isinstance(image_data, bytes):
            img_b64 = base64.b64encode(image_data).decode("ascii")
        else:                                   # строка -> убираем data: URI
            img_b64 = image_data.split(",", 1)[-1]

        # пытаемся угадать MIME по сигнатуре/расширению, если не передали
        if not mime_type:
            mime_type = "image/png"             # значение «по умолчанию»
        mime_type = mime_type or "image/png"

        if not model:
            model = "page"
        model = model or "page"
        # --------------------------------------------------------------
        # 2. собираем JSON-тело
        # --------------------------------------------------------------
        spec: Dict[str, Any] = {
            "content":   img_b64,
            "mimeType":  mime_type,
            "model": model,
        }
        if source_lang:
            spec["languageCodes"] = [source_lang]
        else:
            spec["languageCodes"] = ["*"]        # распознавать все языки

        body_dict = spec
        body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")

        # --------------------------------------------------------------
        # 3. маршрут и заголовки
        # --------------------------------------------------------------
        host   = "ocr.api.cloud.yandex.net"
        port   = 443
        uri    = "/ocr/v1/recognizeText"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": (
                f"Bearer {iam_token}" if iam_token
                else f"Api-Key {api_key}" if api_key
                else ValueError("нужен iam_token или api_key")
            ),
            "x-folder-id": folder_id,
            "x-data-logging-enabled": "true",
        }

        # --------------------------------------------------------------
        # 4. HTTP-запрос
        # --------------------------------------------------------------
        data = self._send_request(host, port, uri, "POST", body, headers)
        output: Dict[str, Any] = json.loads(data)

        # --------------------------------------------------------------
        # 5. разбор результата / ошибок
        # --------------------------------------------------------------
        if "error" in output:
            print("Yandex OCR error:", output["error"])
            return {}, output

        # по спецификации результат лежит в result.textAnnotation
        annotation = (
            output.get("result", {})
            .get("textAnnotation", {})        # может отсутствовать
        )
        return annotation, output




    def tess_ocr(self, image_data, source_lang, ocr_processor):
        # 1. Загружаем JSON, если передан путь
        if isinstance(ocr_processor, str):
            with open(ocr_processor, "r", encoding="utf-8") as fh:
                ocr_processor = json.load(fh)

        # 2. Обновляем язык, если задан в конфиге
        if not source_lang and ocr_processor.get("source_lang"):
            source_lang = ocr_processor["source_lang"]

        # 3. Готовим изображение
        palette = Image.Palette.ADAPTIVE
        image = load_image(image_data).convert("P", palette=palette)

        # 4. Пайплайн фильтров
        for step in ocr_processor["pipeline"]:
            kwargs = step["options"]
            action = step["action"]

            if action == "reduceToMultiColor":
                image = reduce_to_multi_color(
                    image,
                    kwargs["base"],
                    kwargs["colors"],
                    int(kwargs["threshold"])
                )
            elif action == "segFill":
                image = segfill(image, kwargs["base"], kwargs["color"])

            if g_debug_mode == 2:
                image.show()

        if g_debug_mode == 1:
            image.show()

        # 5. Запуск Tesseract-OCR helper
        data = ocr_tools.tess_helper_data(
            image,
            lang=source_lang,
            mode=6,
            min_pixels=1
        )

        # 6. Пост-обработка блоков
        for block in data["blocks"]:
            block["source_text"]  = block["text"]
            block["language"]     = source_lang
            block["translation"]  = ""
            block["text_colors"]  = ["FFFFFF"]

            bb = block["bounding_box"]
            block["bounding_box"] = {
                "x": bb["x1"],
                "y": bb["y1"],
                "w": bb["x2"] - bb["x1"],
                "h": bb["y2"] - bb["y1"],
            }

        return data, source_lang


    def process_output(
            self,
            data: Dict[str, Any],
            raw_data: Dict[str, Any],
            image_data,                         # не используется внутри – просто прокидываем
            source_lang: str | None = None,
            confidence: float = 0.6
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Преобразует JSON-ответ OCR-сервиса в унифицированный формат
        проекта. Поддерживаются два источника:

        • Google Vision  v1/images:annotate  →  raw_data["responses"][…]
        • Yandex Vision v1/recognizeText     →  raw_data["result"]["textAnnotation"]

        Выход: {"blocks":[…], "deleted_blocks":[]}
        """

        # ------------------------------------------------------------------
        # 0. Выявляем провайдера
        # ------------------------------------------------------------------
        if "responses" in raw_data:                      # Google
            src_blocks = (
                raw_data.get("responses", [{}])[0]
                .get("fullTextAnnotation", {})
                .get("pages", [])[0]
                .get("blocks", [])
            )
        elif "result" in raw_data:                       # Yandex
            src_blocks = (
                raw_data["result"]["textAnnotation"]
                .get("blocks", [])
            )
        else:
            return {"blocks": [], "deleted_blocks": []}  # неизвестный формат

        # Цвета – пока просто белый для каждого блока
        text_colors = [["ffffff"] for _ in src_blocks]

        results: Dict[str, List[Dict[str, Any]]] = {
            "blocks": [],
            "deleted_blocks": []
        }

        # ------------------------------------------------------------------
        # 1. Итерация по блокам
        # ------------------------------------------------------------------
        for idx, block in enumerate(src_blocks):
            # ---- confidence (у Yandex его нет – принимаем =1.0) -----------
            block_conf = float(block.get("confidence", 1.0))
            if block_conf < confidence:
                continue

            # ---- Bounding-box --------------------------------------------
            bb_vertices = block.get("boundingBox", {}).get("vertices", [])
            if len(bb_vertices) < 3:
                continue                      # повреждённый блок

            def v(i, key):
                val = bb_vertices[i].get(key, 0)
                return int(val) if isinstance(val, str) else val

            bbox = {
                "x": v(0, "x"),
                "y": v(0, "y"),
                "w": v(2, "x") - v(0, "x"),
                "h": v(2, "y") - v(0, "y"),
            }
            fix_neg_width_height(bbox)

            # ---- Текст ----------------------------------------------------
            words: List[str] = []

            if "paragraphs" in block:                     # Google
                for paragraph in block["paragraphs"]:
                    for word in paragraph.get("words", []):
                        for symbol in word.get("symbols", []):
                            txt = symbol.get("text", "")
                            # корректируем « .» → «.»
                            if txt == "." and words and words[-1] == " ":
                                words[-1] = "."
                            else:
                                words.append(txt)
                        words.append(" ")
            elif "lines" in block:                        # Yandex
                for line in block["lines"]:
                    # самый простой вариант – взять поле "text" строки
                    words.append(line.get("text", ""))
                    words.append(" ")
            else:
                continue

            src_text = "".join(words).replace("\n", " ").strip()

            # ---- формируем результат -------------------------------------
            this_block = {
                "source_text":          src_text,
                "original_source_text": src_text,
                "language":             source_lang or "",
                "translation":          "",
                "bounding_box":         bbox,
                "confidence":           block_conf,
                "text_colors":          text_colors[idx],
            }
            results["blocks"].append(this_block)
        return results



    def translate_output(
            self,
            data: dict,
            target_lang: Optional[str],
            source_lang: Optional[str] = None,
            provider: str = "google",
            # Google
            google_api_key: Optional[str] = None,
            # Yandex
            yandex_folder_id: Optional[str] = None,
            yandex_iam_token: Optional[str] = None,
            yandex_api_key: Optional[str] = None,
    ) -> dict:
        """
        Обновляет data['blocks'][i]['translation'][target_lang] переводом
        от Google Cloud Translation v2 или Yandex Cloud Translate v2 (REST).
        """
        # ------------------------------------------------------------------ #
        # 1. Готовим тексты
        # ------------------------------------------------------------------ #
        texts = [blk["source_text"] for blk in data["blocks"]]

        # ------------------------------------------------------------------ #
        # 2. Получаем переводы (или эхо-ответ, если target_lang не задан)
        # ------------------------------------------------------------------ #
        if not target_lang:
            # echo: «перевод» == исходный текст
            translations = [{
                "translatedText": t,
                "detectedSourceLanguage": "und"  # undefined
            } for t in texts]
        else:
            if provider.lower() == "google":
                out = self.google_translate(
                    texts, target_lang, google_translation_key=google_api_key)
                # приведение к единому виду
                translations = [{
                    "translatedText": item["translatedText"],
                    "detectedSourceLanguage": item.get("detectedSourceLanguage", "")
                } for item in out["data"]["translations"]]

            elif provider.lower() == "yandex":
                out = self.yandex_translate(
                    texts, target_lang,
                    folder_id=yandex_folder_id,
                    iam_token=yandex_iam_token,
                    api_key=yandex_api_key)
                # у Яндекса другие названия полей
                translations = [{
                    "translatedText": item["text"],
                    "detectedSourceLanguage": item.get("detectedLanguageCode", "")
                } for item in out["translations"]]

            else:
                raise ValueError(f"Unknown provider '{provider}'")

            # для отладки — печать полученных переводов
            print([tr["translatedText"] for tr in translations])

        # ------------------------------------------------------------------ #
        # 3. Обновляем блоки
        # ------------------------------------------------------------------ #
        new_blocks: list[dict] = []
        for blk, tr in zip(data["blocks"], translations):
            # нормализуем контейнер для переводов
            if not isinstance(blk.get("translation"), dict):
                blk["translation"] = {}

            # сохраняем перевод
            if target_lang:
                blk["translation"][target_lang.lower()] = tr["translatedText"]
            blk["target_lang"] = target_lang
            blk["language"] = tr["detectedSourceLanguage"]

            # фильтрация по исходному языку, если указан source_lang
            if source_lang and blk["language"]:
                if source_lang != lang_2_to_3.get(blk["language"], ""):
                    continue  # пропускаем, язык не совпадает

            new_blocks.append(blk)

        data["blocks"] = new_blocks
        return data


    def google_translate(self, strings, target_lang, google_translation_key):
        uri = "/language/translate/v2?key="
        uri+= google_translation_key
        for s in strings:
            try:
                print(s)
            except:
                pass
        body = '{\n'
        for string in strings:
            body += "'q': "+json.dumps(string)+",\n"
        body += "'target': '"+target_lang+"'\n"
        body +='}'

        data = self._send_request("translation.googleapis.com", 443, uri, "POST", body)
        output = json.loads(data)
        print("===========")

        if "error" in output:
            print(output['error'])
            return {}

        for x in output['data']['translations']:
            x['translatedText'] = unescape(x['translatedText'])
            try:
                print(x['translatedText'])
            except:
                pass
        
        pairs = [[strings[i], output['data']['translations'][i]['translatedText']] for i in range(len(strings))]
        for intext, outtext in pairs:
            doc = {"target_lang": target_lang,
                   "text": intext,
                   "translation": outtext,
                   "auto": True,
                  }
        return output

    def yandex_translate(self, strings, target_lang, folder_id,
                         iam_token=None, api_key=None, source_lang=None):
        """
        Перевод списка строк через REST-энд-поинт
        https://translate.api.cloud.yandex.net/translate/v2/translate

        :param strings:     iterable[str] — тексты для перевода
        :param target_lang: str           — код целевого языка (например, 'ru')
        :param folder_id:   str           — ID каталога Yandex Cloud
        :param iam_token:   str|None      — краткоживущий IAM-токен (Bearer)
        :param api_key:     str|None      — долгоживущий API-ключ (Api-Key)
        :param source_lang: str|None      — код исходного языка (опционально)

        :return: dict — полный JSON-ответ сервиса
        """
        print(strings)
        print(target_lang)

        if not (iam_token or api_key):
            raise ValueError("нужен iam_token или api_key")
        if not folder_id:
            raise ValueError("folder_id обязателен для Yandex Cloud Translate")

        # --- 1. Маршрут и заголовки --------------------------------------------
        host = "translate.api.cloud.yandex.net"
        port = 443
        uri  = "/translate/v2/translate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{'Bearer' if iam_token else 'Api-Key'} "
                             f"{iam_token or api_key}"
        }

        # --- 2. Тело запроса ----------------------------------------------------
        body_dict = {
            "folderId": folder_id,
            "texts": list(strings),
            "targetLanguageCode": target_lang,
            "format": "PLAIN_TEXT"
        }
        if source_lang:
            body_dict["sourceLanguageCode"] = source_lang

        body = json.dumps(body_dict, ensure_ascii=False)

        # --- 3. Отправка --------------------------------------------------------
        raw = self._send_request(host, port, uri, "POST", body, headers)
        output = json.loads(raw)

        # --- 4. Обработка ошибок API -------------------------------------------
        if "error" in output:
            # формат { "error": { "code": int, "message": str } }
            print(output["error"])
            return {}

        # --- 5. Печать и post-processing ---------------------------------------
        print("Yandex Translate output:")
        print(json.dumps(output, indent=2))

        for x in output["translations"]:
            x["text"] = unescape(x["text"])
            try:
                print(x["text"])
            except Exception:
                pass

        # Пример связи вход<->выход (если нужно):
        # pairs = list(zip(strings, (t["text"] for t in output["translations"])))

        return output

    def _send_request(self, host, port, uri, method, body=None, headers=None):
        """
        Thin wrapper over http.client.HTTPSConnection that supports headers.
        """
        conn = http.client.HTTPSConnection(host, port)
        if body is not None:
            conn.request(method, uri, body=body, headers=headers or {})
        else:
            conn.request(method, uri, headers=headers or {})
        response = conn.getresponse()
        return response.read()



def start_api_server(window_object):
    global server_thread
    global window_obj
    print("start api server")
    if config.local_server_enabled:
        #start thread with this server in it:
        window_obj = window_object
        server_thread = threading.Thread(target=start_api_server2)
        server_thread.start()

def kill_api_server():
    print("kill api server")
    global httpd_server
    if config.local_server_enabled:
        httpd_server.shutdown()

def start_api_server2():
    print("start api server2")
    global httpd_server
    host = config.local_server_host
    port = config.local_server_port      
    server_class = http.server.HTTPServer
    httpd_server = server_class((host, port), APIHandler)
    print("server start")
    try:
        httpd_server.serve_forever()
    except KeyboardInterrupt:
        pass

 
def main():
    global g_debug_mode
    if not config.load_init():
        return
    host = config.local_server_host
    port = config.local_server_port 
    print("host", host)
    print("port", port)
    server_class = http.server.HTTPServer
    httpd = server_class((host, port), APIHandler)
    if "--debug-extra" in sys.argv:
        g_debug_mode = 2
    elif "--debug" in sys.argv:
        g_debug_mode = 1

    print("server start")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
    print('end')

if __name__=="__main__":
    main()
