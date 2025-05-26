from typing import Union, Optional
import http.client
import base64, hashlib, json, http.client
from typing import Tuple, Dict, Any, Optional
from . import config

# ────────────────────────────────────────────────────────────────────────
#  Блок констант – можно вынести в config.py
# ────────────────────────────────────────────────────────────────────────
_YANDEX_ENDPOINT   = "/tts/v3/utteranceSynthesis"
_YANDEX_HOST       = "tts.api.cloud.yandex.net"
_TTS_MODEL         = ""          # Nothing
_TTS_SAMPLE_RATE   = 48000              # Гц
_TTS_CONTAINER     = "WAV"              # просим сразу WAV

class TextToSpeech(object):
    # ----------------------------------------------------------
    # ПУБЛИЧНЫЙ API (осталось имя как раньше)
    # ----------------------------------------------------------
    @classmethod
    def text_to_speech_api(cls, text: str,
                           name: str = "",
                           source_lang: Optional[str] = None,
                           provider: Optional[str] = "google",
                           **auth) -> bytes:
        """
        :param provider: "google" (default) | "yandex"
        :param auth:     ключи для конкретного провайдера –
                         google_api_key / iam_token / api_key / folder_id
        :return: WAV-файл (bytes)
        """

        # ---------- 0. пустая строка → ничего читать ------------ #
        if not text:
            text = "No text found."

        # ---------- 1. общие параметры голоса ------------------ #
        voice, pitch, speed = cls.process_name_voice(name)
        print(f"voice: {voice}, pitch: {pitch}, speed: {speed}")

        # ---------- 2. Google vs Yandex ------------------------ #
        if provider == "google":
            audio = cls._google_tts(text, source_lang or "en-US",
                                    voice, pitch, speed,
                                    api_key=auth.get("google_api_key")
                                            or config.local_server_translation_key)

        elif provider == "yandex":
            audio = cls._yandex_tts(text, source_lang or "en-US",
                                    voice, speed,
                                    folder_id = auth.get("folder_id")
                                                or config.yandex_folder_id,
                                    iam_token = auth.get("iam_token")
                                                or config.yandex_iam_token,
                                    api_key   = auth.get("api_key")
                                                or config.yandex_translation_key)
        else:
            raise ValueError(f"Unknown TTS provider: {provider}")

        return audio

    # ----------------------------------------------------------
    #  GOOGLE Cloud Text-to-Speech (как раньше, только вынесено)
    # ----------------------------------------------------------
    @classmethod
    def _google_tts(cls, text: str, lang: str,
                    voice: str, pitch: float, speed: float,
                    *, api_key: str) -> bytes:

        uri = f"/v1/text:synthesize?key={api_key}"

        doc = {
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "pitch": pitch,
                "speakingRate": speed
            },
            "input": {"text": text},
            "voice": {"languageCode": lang}
        }
        if lang == "en-US":
            doc["voice"]["name"] = voice

        body = json.dumps(doc).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}

        conn = http.client.HTTPSConnection("texttospeech.googleapis.com", 443)
        conn.request("POST", uri, body, headers)
        rep = conn.getresponse()
        data: Dict[str, Any] = json.loads(rep.read())

        if "error" in data:
            raise RuntimeError(f"Google TTS error: {data['error']}")

        return base64.b64decode(data["audioContent"])

    # ----------------------------------------------------------
    #  YANDEX SpeechKit v3 (REST, /speech/v1/tts:synthesize)
    # ----------------------------------------------------------
    @classmethod
    def _yandex_tts(cls, text: str, lang: str,
                    voice_hint: str, speed: float,
                    folder_id: str,
                    iam_token: Optional[str],
                    api_key:  Optional[str]) -> bytes:
        """
        Синтез речи через Yandex SpeechKit v3 (JSON-stream).
        Возвращает уже готовый WAV-файл (bytes).
        """

        # 1. выбор голоса ──────────────────────────────────────────────
        voice = "john" if lang.startswith(("E", "e")) else "filipp"

        # 2. собираем JSON-тело запроса ────────────────────────────────
        req_body = {
            "model": _TTS_MODEL,
            "text":  text,
            "hints": [{
                "voice": voice,
                "speed": f"{speed:.2f}",
                "volume": "1.0"
            }],
            "outputAudioSpec": {
                "containerAudio": {
                    "containerAudioType": _TTS_CONTAINER
                }
            },
            "loudnessNormalizationType" : "MAX_PEAK"
        }

        body = json.dumps(req_body).encode("utf-8")

        # 3. заголовки (auth + folder) ─────────────────────────────────
        headers = {
            "Content-Type": "application/json",
            "X-Folder-Id":  folder_id,          # v3 принято передавать именно так
        }
        if iam_token:
            headers["Authorization"] = f"Bearer {iam_token}"
        elif api_key:
            headers["Authorization"] = f"Api-Key {api_key}"
        else:
            raise ValueError("Need iam_token or api_key for Yandex TTS")

        # 4. HTTPS-запрос ──────────────────────────────────────────────
        conn = http.client.HTTPSConnection(_YANDEX_HOST, 443)
        conn.request("POST", _YANDEX_ENDPOINT, body, headers)
        rep = conn.getresponse()

        if rep.status != 200:
            raise RuntimeError(f"Yandex TTS HTTP {rep.status}: {rep.read()[:200]}")
        # 5. собираем поток JSON-строк с чанками звука ────────────────
        audio_data = bytearray()
        while True:
            # Сервисы Яндекс-Vision / SpeechKit шлют \n-разделённые JSON-объекты.
            line = rep.readline()
            if not line:
                break
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue                     # пропускаем пустые keep-alive
            if "result" in obj:              # это чанк звука
                if "audioChunk" in obj["result"]:
                    audio_data.extend(base64.b64decode(obj["result"]["audioChunk"]["data"]))
            # опционально: можно обработать textChunk / timestamps и т.п.

        print(f"TTS: {len(audio_data)} bytes")
        # 6. готовый WAV-контейнер ────────────────────────────────────
        return bytes(audio_data)


    # ----------------------------------------------------------
    #  выбор голоса (оставляем как было, но убираем old_div)
    # ----------------------------------------------------------
    @classmethod
    def process_name_voice(cls, name: Union[str, bytes]) -> Tuple[str, float, float]:
        voices = [
            "en-US-Wavenet-A",
            "en-US-Wavenet-B",
            "en-US-Wavenet-C",
            "en-US-Wavenet-D",
            "en-US-Wavenet-E",
            "en-US-Wavenet-F",
        ]

        if isinstance(name, str):
            name_bytes = name.encode("utf-8")
        else:
            name_bytes = name or b""

        r = int(hashlib.sha256(name_bytes).hexdigest(), 16)
        voice = voices[r % 4] if r & 1 else voices[r % 2 + 4]

        pitch = -10 + 20 * ((r % 13) / 13.0)
        speed = 1.0 + 0.3 * ((r % 15) / 15.0 - 0.5)
        return voice, pitch, speed



def main():
    name = "Cloud"
    text = "I am a human being, no different from you."
    TextToSpeech.text_to_speech_api(text, name=name, source_lang=None)

if __name__=="__main__":
    main()

