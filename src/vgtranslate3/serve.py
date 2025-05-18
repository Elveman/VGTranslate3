#!/usr/bin/env python2

from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from past.builtins import basestring
from past.utils import old_div
from builtins import object
import http.server
try:
    from html import unescape
except ImportError:                 # очень старый Py3 / Py2
    from html.parser import HTMLParser
    unescape = HTMLParser().unescape
import time
import json
from . import config
import threading
import http.client
import functools
import urllib.parse
import os
import base64
from .util import load_image, image_to_string, fix_neg_width_height,\
                 image_to_string_format, swap_red_blue, segfill,\
                 reduce_to_multi_color, reduce_to_text_color,\
                 color_hex_to_byte
from . import screen_translate
from . import imaging
from . import ocr_tools
from .text_to_speech import TextToSpeech
import sys
import re
from PIL import Image, ImageEnhance, ImageDraw

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

server_thread = None
httpd_server = None
window_obj =  None

g_debug_mode = 0

SOUND_FORMATS = {"wav": 1}
IMAGE_FORMATS = {"bmp": 1, "png": 1}


class ServerOCR(object):
    @classmethod
    def _preprocess_color(cls, image_data, colors="FFFFFF"):
        img = load_image(image_data)
        bg = "000000"
        if colors.lower().strip() == "detect":
            pass
        elif colors:
            print(("Pre process ", colors))
            try:
                colors = [x.strip() for x in re.split(",| |;", colors)]
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
                print("succ=true")
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
        data = self.rfile.read(content_length);
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
                image_object = image_object.convert("P", palette=Image.ADAPTIVE, colors=32)
            else:
                image_object = image_object.convert("P", palette=Image.ADAPTIVE)

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
                image_object = image_object.convert("P", palette=Image.ADAPTIVE, colors=32)
            else:
                image_object = load_image(image_data).convert("P", palette=Image.ADAPTIVE)

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
                                         google_translation_key=api_translation_key)
        
            output_data = {}
            if "sound" in request_out_dict:
                mp3_out = self.text_to_speech(data, target_lang=target_lang, 
                                              format_type=request_out_dict['sound'])
                output_data['sound'] = mp3_out

            if window_obj:
                window_obj.load_image_object(output_image)
                window_obj.curr_image = imaging.ImageItterator.prev()
            
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
            image_object = load_image(image_data).convert("P", palette=Image.ADAPTIVE)
            image_data = image_to_string(image_object)
 

            api_translation_key = config.local_server_translation_key
            ocr_processor = config.local_server_ocr_processor
            data, source_lang = self.tess_ocr(image_data, source_lang, ocr_processor)
            if not data.get("blocks"):
                error_string = "No text found."
            data = self.translate_output(data, target_lang,
                                         source_lang=source_lang,
                                         google_translation_key=api_translation_key)
            if alpha:
                image_object = Image.new("RGBA", 
                                         (image_object.width, image_object.height),
                                         (0,0,0,0))
            output_image = imaging.ImageModder.write(image_object, data, target_lang)
            if window_obj:
                window_obj.load_image_object(output_image)
                window_obj.curr_image = imaging.ImageItterator.prev()
 
            if pixel_format == "BGR": 
                output_image = output_image.convert("RGB")
                output_image = swap_red_blue(output_image)
            return_doc = {"image": image_to_string_format(output_image, request_out_dict['image'], "RGBA")}
            if error_string:
                return_doc['error'] = error_string
            return return_doc

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
            wav_data = TextToSpeech.text_to_speech_api(text_to_say, source_lang=target_lang)

        wav_data = self.fix_wav_size(wav_data)
        # wav_data может прийти как str (unicode) - превращаем в bytes
        if isinstance(wav_data, str):
            wav_data = wav_data.encode("utf-8")

        wav_data = base64.b64encode(wav_data).decode("ascii")
        return wav_data

    def fix_wav_size(self, wav):
        def tb(size):
            bs = size%256, int(old_div(size,256))%256, int(old_div(size,(256**2)))%256, int(old_div(size,(256**3)))%256
            return bytearray(bs)
        size1 = tb(len(wav))
        size2 = tb(len(wav)-44)
        s = bytearray(wav)
        s[4]=size1[0]
        s[5]=size1[1]
        s[6]=size1[2]
        s[7]=size1[3]

        s[40]=size2[0]
        s[41]=size2[1]
        s[42]=size2[2]
        s[43]=size2[3]
        return str(s)


    def google_ocr(self, image_data, source_lang, ocr_api_key):
        doc = {
               "requests": [{
                "image": {"content": image_data},
                "features": [
                  {"type": "DOCUMENT_TEXT_DETECTION"}
                ]
               }]
              }

        #load_image(img_data).show()
        if source_lang:
            doc['requests'][0]['imageContext'] = {"languageHints": [source_lang]}

        body = json.dumps(doc)

        uri = "/v1p1beta1/images:annotate?key="
        uri+= ocr_api_key

        data = self._send_request("vision.googleapis.com", 443, uri, "POST", body)
        output = json.loads(data)
        print("google output")
        print(output)
        if output.get("responses", [{}])[0].get("fullTextAnnotation"):
            return output['responses'][0]['fullTextAnnotation'], output
        else:
            return {}, {}

    def tess_ocr(self, image_data, source_lang, ocr_processor):
        if isinstance(ocr_processor, basestring):
            try:
                f = json.loads(open(ocr_processor).read())
            except:
                raise
        if ocr_processor.get("source_lang") and source_lang is None:
            source_lang = ocr_processor['source_lang']

        image = load_image(image_data).convert("P", palette=Image.ADAPTIVE)
        for step in ocr_processor['pipeline']:
            kwargs = step['options']
            if step['action'] == 'reduceToMultiColor':
                image = reduce_to_multi_color(image, kwargs['base'],
                                              kwargs['colors'],
                                              kwargs['threshold'])
            elif step['action'] == 'segFill':
                image = segfill(image, kwargs['base'], kwargs['color'])
            if g_debug_mode == 2:
                image.show()

        if g_debug_mode == 1:
            image.show()
        data = ocr_tools.tess_helper_data(image, lang=source_lang,
                                          mode=6, min_pixels=1)
        for block in data['blocks']:
            block['source_text'] = block['text']
            block['language'] = source_lang
            block['translation'] = ""
            block['text_colors'] = ["FFFFFF"]
            bb = block['bounding_box']
            nb = dict()
            nb['x'] = bb['x1']
            nb['y'] = bb['y1']
            nb['w'] = bb['x2']-bb['x1']
            nb['h'] = bb['y2']-bb['y1']
            block['bounding_box'] = nb
            

        return data, source_lang

    def process_output(self, data, raw_data, image_data, source_lang=None, confidence=0.6):
        text_colors = list()
        for entry in raw_data.get('responses', []):
            for page in entry['fullTextAnnotation']['pages']:
                for block in page['blocks']:
                    text_colors.append(['ffffff'])

        results = {"blocks": [], "deleted_blocks": []}
        for page in data.get("pages", []):
            for num, block in enumerate(page.get("blocks", [])):
                this_block = {"source_text": [], "language": "", "translation": "",
                              "bounding_box": {"x": 0, "y": 0, "w": 0, "h": 0},
                              "confidence": block.get("confidence"),
                              "text_colors": text_colors[num]
                             }

                if block.get("confidence", 0) <confidence:# and False:
                    continue
                bb = block.get("boundingBox", {}).get("vertices", [])
                this_block['bounding_box']['x'] = bb[0].get('x',0)
                this_block['bounding_box']['y'] = bb[0].get('y', 0)
                this_block['bounding_box']['w'] = bb[2].get('x',0) - bb[0].get('x', 0)
                this_block['bounding_box']['h'] = bb[2].get('y', 0) - bb[0].get('y', 0)
                fix_neg_width_height(this_block['bounding_box'])

                for paragraph in block.get("paragraphs", []):
                    for word in paragraph.get("words", []):
                        for symbol in word.get("symbols", []):
                            if (symbol['text'] == "." and this_block['source_text']\
                                                      and this_block['source_text'][-1] == " "):
                                this_block['source_text'][-1] = "."
                            else:
                                this_block['source_text'].append(symbol['text'])
                        this_block['source_text'].append(" ")
                    this_block['source_text'].append("\n")
                this_block['source_text'] = "".join(this_block['source_text']).replace("\n", " ").strip()
                this_block['original_source_text'] = this_block['source_text']
                results['blocks'].append(this_block)
        return results


    def translate_output(self, data, target_lang, source_lang=None, google_translation_key=None):
        if target_lang:
            translates = self.google_translate([x['source_text'] for x in\
                                                data['blocks']], target_lang,
                                               google_translation_key=google_translation_key)

        else:
            translates = {"data": {"translations": [{"translatedText": x['source_text'], "detectedSourceLanguage": "En"} for x in data['blocks']]}}
            print([x['translatedText'] for x in translates['data']['translations']])
        new_blocks = list()
        for i, block in enumerate(data['blocks']):
            if not 'translation' in block or isinstance(block['translation'], basestring):
                block['translation'] = dict()
            block['translation'][target_lang.lower()] =\
                    translates['data']['translations'][i]['translatedText']
            block['target_lang'] = target_lang
            block['language'] = translates['data']['translations'][i]['detectedSourceLanguage']
            if block['language'] and source_lang and source_lang != lang_2_to_3.get(block['language'], ""):
                continue
            new_blocks.append(block)
        data['blocks'] = new_blocks
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

    def _send_request(self, host, port, uri, method, body=None):
        conn = http.client.HTTPSConnection(host, port)
        if body is not None:
            conn.request(method, uri, body)
        else:
            conn.request(method, uri)
        response = conn.getresponse()
        return response.read()



def start_api_server(window_object):
    global server_thread
    global window_obj
    if config.local_server_enabled:
        #start thread with this server in it:
        window_obj = window_object
        server_thread = threading.Thread(target=start_api_server2)
        server_thread.start()

def kill_api_server():  
    global httpd_server
    if config.local_server_enabled:
        httpd_server.shutdown()

def start_api_server2():
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
