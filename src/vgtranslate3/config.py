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
local_server_host = "0.0.0.0"
local_server_port = 4404
local_server_ocr_key = ""
local_server_translation_key = ""
local_server_api_key_type = "google"
local_server_ocr_processor = ""

yandex_ocr_key = ""
yandex_translation_key = ""
yandex_iam_token = ""
yandex_folder_id = ""

# OpenAI-compatible settings
openai_api_key = ""
openai_base_url = "https://api.openai.com/v1"
openai_model = "gpt-4o-mini"
openai_ocr_model = None
openai_translation_model = None
openai_tts_model = "tts-1"
openai_tts_voice = "alloy"
openai_timeout = 30
openai_max_retries = 3

# YandexGPT settings
yandex_llm_api_key = ""
yandex_llm_folder_id = ""
yandex_llm_model = "yandexgpt-lite"

# Provider separation
ocr_provider = "openai"
translation_provider = "openai"
tts_provider = "google"

# Bounding boxes fallback
use_bbox_fallback = True

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
    global yandex_ocr_key
    global yandex_translation_key
    global yandex_iam_token
    global yandex_folder_id
    
    global openai_api_key
    global openai_base_url
    global openai_model
    global openai_ocr_model
    global openai_translation_model
    global openai_tts_model
    global openai_tts_voice
    global openai_timeout
    global openai_max_retries
    
    global yandex_llm_api_key
    global yandex_llm_folder_id
    global yandex_llm_model
    
    global ocr_provider
    global translation_provider
    global tts_provider
    
    global use_bbox_fallback
    
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

    local_server_port = int(
        os.getenv(
            "VGTRANSLATE3_PORT",
            os.getenv(
                "PORT",
                local_server_port
            )
        )
    )

    if "local_server_ocr_key" in config_file:
        local_server_ocr_key = config_file['local_server_ocr_key']
    if "local_server_translation_key" in config_file:
        local_server_translation_key = config_file['local_server_translation_key']
    if "local_server_api_key_type" in config_file:
        local_server_api_key_type = config_file['local_server_api_key_type']

    if "local_server_ocr_processor" in config_file:
        local_server_ocr_processor = config_file['local_server_ocr_processor']

    if "yandex_ocr_key" in config_file:
        yandex_ocr_key = config_file['yandex_ocr_key']
    if "yandex_translation_key" in config_file:
        yandex_translation_key = config_file['yandex_translation_key']
    if "yandex_iam_token" in config_file:
        yandex_iam_token = config_file['yandex_iam_token']
    if "yandex_folder_id" in config_file:
        yandex_folder_id = config_file['yandex_folder_id']

    if "openai_api_key" in config_file:
        openai_api_key = config_file['openai_api_key']
    if "openai_base_url" in config_file:
        openai_base_url = config_file['openai_base_url']
    if "openai_model" in config_file:
        openai_model = config_file['openai_model']
    if "openai_ocr_model" in config_file:
        openai_ocr_model = config_file['openai_ocr_model']
    if "openai_translation_model" in config_file:
        openai_translation_model = config_file['openai_translation_model']
    if "openai_tts_model" in config_file:
        openai_tts_model = config_file['openai_tts_model']
    if "openai_tts_voice" in config_file:
        openai_tts_voice = config_file['openai_tts_voice']
    if "openai_timeout" in config_file:
        openai_timeout = config_file['openai_timeout']
    if "openai_max_retries" in config_file:
        openai_max_retries = config_file['openai_max_retries']
    
    if "yandex_llm_api_key" in config_file:
        yandex_llm_api_key = config_file['yandex_llm_api_key']
    if "yandex_llm_folder_id" in config_file:
        yandex_llm_folder_id = config_file['yandex_llm_folder_id']
    if "yandex_llm_model" in config_file:
        yandex_llm_model = config_file['yandex_llm_model']
    
    if "ocr_provider" in config_file:
        ocr_provider = config_file['ocr_provider']
    if "translation_provider" in config_file:
        translation_provider = config_file['translation_provider']
    if "tts_provider" in config_file:
        tts_provider = config_file['tts_provider']
    
    if "use_bbox_fallback" in config_file:
        use_bbox_fallback = config_file['use_bbox_fallback']

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

