from typing import Union, Optional

from future import standard_library
standard_library.install_aliases()
from builtins import object
import http.client
import base64, hashlib, json, http.client, urllib.parse, wave, io
from typing import Tuple, Dict, Any
from . import config
#import gender_guesser.detector as gender

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
        provider = provider or config.tts_provider.lower()

        # ---------- 0. пустая строка → ничего читать ------------ #
        if not text:
            text = "No text found."

        # ---------- 1. общие параметры голоса ------------------ #
        voice, pitch, speed = cls.process_name_voice(name)

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
                                                or config.yandex_api_key)
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
                    *, folder_id: str,
                    iam_token: Optional[str],
                    api_key: Optional[str]) -> bytes:

        # --- выбираем голос ------------------------------------------------
        # SpeechKit имеет фиксированный набор имён; подставим «alena/filipp»
        voice = "alena" if voice_hint.endswith(("E", "F")) else "filipp"

        # --- REST форм-параметры ------------------------------------------
        params = {
            "text": text,
            "lang": lang,          # например 'en-US' или 'ru-RU'
            "voice": voice,
            "format": "lpcm",      # 16-бит PCM, little-endian
            "sampleRateHertz": 48000,
            "speed": "{:.2f}".format(speed),
            "folderId": folder_id,
        }
        body = urllib.parse.urlencode(params)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        if iam_token:
            headers["Authorization"] = f"Bearer {iam_token}"
        elif api_key:
            headers["Authorization"] = f"Api-Key {api_key}"
        else:
            raise ValueError("Need iam_token or api_key for Yandex TTS")

        # --- HTTPS запрос --------------------------------------------------
        conn = http.client.HTTPSConnection("tts.api.cloud.yandex.net", 443)
        conn.request("POST", "/speech/v1/tts:synthesize", body, headers)
        rep = conn.getresponse()
        if rep.status != 200:
            raise RuntimeError(f"Yandex TTS HTTP {rep.status}: {rep.read()[:200]}")
        pcm_data = rep.read()          # RAW 48-kHz little-endian

        # --- оборачиваем в WAV-контейнер ----------------------------------
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)        # 16-bit PCM
            wav.setframerate(48000)
            wav.writeframes(pcm_data)

        return wav_buf.getvalue()

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

