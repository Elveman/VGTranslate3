from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import object
from past.utils import old_div
import json
import time
import hashlib
import http.client
import base64
from . import config
#import gender_guesser.detector as gender

class TextToSpeech(object):
    @classmethod
    def text_to_speech_api(cls, text, name="", source_lang=None, async_=False):
        voice, pitch, speed = cls.process_name_voice(name)
        print(("LANG", source_lang))
        if source_lang is None:
            source_lang = "en-US"
        t_time = time.time()
        uri = "/v1beta1/text:synthesize?key="
        uri+=config.local_server_ocr_key
        if not text:
            text = "No text found."
        doc = {
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "pitch": pitch,
                "speakingRate": speed
            },
            "input": {
                "text": text
            },
            "voice": {
                "languageCode": source_lang,
            }
        }
        if source_lang == "en-US":
            doc['voice']['name'] = voice
        body = json.dumps(doc)
        print("----------------")
        print(body)
        conn = http.client.HTTPSConnection("texttospeech.googleapis.com", 443)
        conn.request("POST", uri, body)
        rep = conn.getresponse()
        data = rep.read()
        data = json.loads(data)
        print('============')
        print(data)
        #print data
        file_contents = base64.b64decode(data['audioContent'])
        return file_contents

    @classmethod
    def process_name_voice(cls, name):
        #get the gender and number for a name:
        voices = [
            "en-US-Wavenet-A",
            "en-US-Wavenet-B",
            "en-US-Wavenet-C",
            "en-US-Wavenet-D",
            "en-US-Wavenet-E",
            "en-US-Wavenet-F"
        ]
        #d = gender.Detector()
        #res = d.get_gender(name)
        #print ['gender:', res, name]
        res = "unknown"
        if isinstance(name, str):
            name_bytes = name.encode("utf-8")
        else:
            name_bytes = name

        r = int(hashlib.sha256(name_bytes).hexdigest(), 16)
        if res in ["male", "mostly_male", "andy", "unknown"]:
            voice = voices[r%4]
        else:
            voice = voices[r%2+4]
        pitch = (r%13)/13.0
        pitch = -10+20*pitch
        speed = (r%15)/15.0
        speed = -0.15+(0.3*speed)
        if speed < 0:
            speed = old_div(1,(1-speed))
        else:
            speed = 1*(1+speed)
        return voice, pitch, speed



def main():
    name = "Cloud"
    text = "I am a human being, no different from you."
    TextToSpeech.text_to_speech_api(text, name=name, source_lang=None)

if __name__=="__main__":
    main()

