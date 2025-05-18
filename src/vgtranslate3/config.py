from __future__ import print_function
import json
import os, pathlib
from . import imaging

_DEFAULT_CFG = pathlib.Path(__file__).with_name("config.json")
CFG_PATH = pathlib.Path(os.getenv("VGTRANSLATE3_CONFIG", _DEFAULT_CFG))

server_host = "ztranslate"
server_port = 8888
user_api_key = ""
default_target = "en"

local_server_enabled = False
local_server_host = "localhost"
local_server_port = 4404
local_server_ocr_key = ""
local_server_translation_key = ""
local_server_api_key_type = "google"
local_server_ocr_processor = ""

ocr_confidence = 0.6
ocr_contrast = 2.0
ocr_color = None
ocr_box = None

font = "RobotoCondensed-Bold.ttf"
font_split = " "
font_override = False

def load_init():
    global server_host
    global server_port
    global user_api_key
    global default_target
    global local_server_enabled
    global local_server_host
    global local_server_port
    global local_server_ocr_key
    global local_server_translation_key
    global local_server_api_key_type
    global local_server_ocr_processor
    global font
    global font_split
    global font_override

    global ocr_confidence
    global ocr_contrast
    global ocr_color
    global ocr_box

    try:
        config_file = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print("Invalid config file specification:")
        print(e)
        return False

    if "server_host" in config_file:
        server_host = config_file['server_host']    
    if "server_port" in config_file:
        server_port = config_file['server_port']    
    if "user_api_key" in config_file:
        user_api_key = config_file['user_api_key']    
    if "default_target" in config_file:
        default_target = config_file['default_target']    

    if "local_server_enabled" in config_file:
        local_server_enabled = config_file['local_server_enabled']
    if "local_server_host" in config_file:
        local_server_host = config_file['local_server_host']
    if "local_server_port" in config_file:
        local_server_port = config_file['local_server_port']

    if "local_server_ocr_key" in config_file:
        local_server_ocr_key = config_file['local_server_ocr_key']
    if "local_server_translation_key" in config_file:
        local_server_translation_key = config_file['local_server_translation_key']
    if "local_server_api_key_type" in config_file:
        local_server_api_key_type = config_file['local_server_api_key_type']

    if "local_server_ocr_processor" in config_file:
        local_server_ocr_processor = config_file['local_server_ocr_processor']

    if "font" in config_file:
        font = config_file['font']
    if "font_split" in config_file:
        font_split = config_file['font_split']
    if "font_override" in config_file:
        font_override = config_file['font_override']

    if "ocr_confidence" in config_file:
        ocr_confidence = config_file['ocr_confidence']
    if "ocr_contrast" in config_file:
        ocr_contrast = config_file['ocr_contrast']
    if "ocr_color" in config_file:
        ocr_color = config_file['ocr_color']
    if "ocr_box" in config_file:
        ocr_box = config_file['ocr_box']

    print("using font: "+font)
    imaging.load_font(font, font_split, font_override)
    print("config loaded")
    print("====================")
    #print user_api_key
    return True

def write_init():
    obj = {"server_host": server_host,
           "server_port": server_port,
           "user_api_key": user_api_key,
           "default_target": default_target,
           "local_server_enabled": local_server_enabled,
           "local_server_host": local_server_host,
           "local_server_port": local_server_port,
           "local_server_ocr_key": local_server_ocr_key,
           "local_server_translation_key": local_server_translation_key,
           "local_server_api_key_type": local_server_api_key_type,
           "font": font
    }
    config_file = open("./config.json", "w")
    config_file.write(json.dumps(obj, indent=4))

