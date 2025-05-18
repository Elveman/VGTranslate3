from __future__ import print_function
from __future__ import division
from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
from PIL import Image, ImageFont, ImageDraw
import os
import datetime
import time
from .util import color_hex_to_byte
from importlib.resources import files


FONT = "RobotoCondensed-Bold.ttf"
FONT_DIR = files(__package__).joinpath("fonts")
FONTS = list()
FONTS_WH = list()
FONT_SPLIT = " "
OVERRIDE_FONT = False

def measure(draw, text, font):
    """
    Возвращает (width, height) строки `text` с указанным шрифтом.
    Работает на Pillow любых версий.
    """
    if hasattr(draw, "textbbox"):                # Pillow >=8.0, включая 10
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    else:                                        # старые версии (<8.0)
        return measure(draw, text, font=font)

def load_font(font_name, font_split=" ", font_override=False):
    global FONT
    global FONTS
    global FONTS_WH
    global FONT_SPLIT
    global OVERRIDE_FONT
    FONT_SPLIT = font_split
    
    FONT = font_name
    OVERRIDE_FONT = font_override
    print([FONT, OVERRIDE_FONT])
    FONTS = [ImageFont.truetype(str(FONT_DIR / FONT), x+8) for x in range(32)]
    FONTS_WH = list()
    fill_fonts_wh()


def fill_fonts_wh():
    global FONTS_WH
    test = Image.new('RGBA', (100, 100))
    test = test.convert("RGBA")
    draw = ImageDraw.Draw(test)

    largest_char_w_size = 0
    avg_w = 0
    largest_char_h_size = 0
    avg_h = 0

    for i in range(len(FONTS)):
        t = 0
        avg_w = 0
        avg_h = 0
        for char in u"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?!.,;'\"\u624b":
            t+=1
            # Pillow ≥10: textsize() удалён, используем textbbox();
            # Pillow <10: textbbox тоже есть, но на всякий случай добавим fallback
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), char, font=FONTS[i])
                size_x, size_y = bbox[2] - bbox[0], bbox[3] - bbox[1]
            else:  # старые Pillow (до 8.0) — оставляем прежний метод
                size_x, size_y = measure(draw, char, font=FONTS[i])
            avg_w += size_x
            avg_h += size_y

            if size_x > largest_char_w_size:
                largest_char_w_size = size_x 
            if size_y > largest_char_h_size:
                largest_char_h_size = size_y 
        avg_w = int(old_div(avg_w,t))
        avg_h = int(old_div(avg_h,t))

        FONTS_WH.append([avg_w, largest_char_h_size])

    draw = ImageDraw.Draw(test)

def wrap_text(text, font, draw, w):
    if FONT_SPLIT:
        words = text.split(FONT_SPLIT)
    else:
        words = [x for x in text]
    outline = ""
    outtext = ""
    for word in words:
        size = measure(draw, outline+" "+word, font=font)
        if size[0] < w:
            outline+=FONT_SPLIT+word
        else:
            outtext+=outline+"\n"
            outline = word
    outtext+=FONT_SPLIT+outline
    return outtext.strip()

def get_approximate_font(text, w, h):
    best = 0
    for i in range(32):
        curr_x = 0
        curr_y = FONTS_WH[i][1]
        if FONT_SPLIT:
            splitted = text.split(FONT_SPLIT)
        else:
            splitted = [x for x in text]
        for word in splitted:
            curr_x+=len(word)*FONTS_WH[i][0]
            if curr_x > w:
                curr_x = len(word)*FONTS_WH[i][0]
                curr_y+=FONTS_WH[i][1]
        if curr_y > h:
            break    
        best = i
    return best

def fmeasure(font, text="A"):
    """
    Возвращает (width, height) строки `text` по шрифту `font`.
    Поддерживает Pillow как до 10, так и после удаления getsize().
    """
    if hasattr(font, "getbbox"):                 # Pillow >=10
        left, top, right, bottom = font.getbbox(text)
        return right - left, bottom - top
    else:                                        # Pillow <10
        return font.getsize(text)


def get_text_wh(text, font, draw, mw):
    height = fmeasure(font, "A")[1]
    h = len(text.strip().split("\n"))*(height+1)
    w = 0
    for line in text.strip().split("\n"):
        cw, _ = measure(draw, line, font=font)
        if cw > w and cw <= mw:
            w = cw
    return w,h
    
def drawTextBox(draw, text, x,y, w, h, font=None, font_size=None, font_color=None, 
                confid=1, exact_font=None):
    text = text.strip()
    if h < 18:
        h = 18
    c = int(confid*255)
    draw.rectangle([x-2,y, x+w+2, y+h], fill=(0,0,0,255), outline=(255,c,c,c))
    approx_font = get_approximate_font(text, w, h)
    succ = wrap_text(text, FONTS[8], draw, w)
    succ_f = FONTS[8]
    for i in range(32):
        if exact_font is not None:
            i = exact_font

        if i < approx_font and exact_font:
            continue
        outtext = wrap_text(text, FONTS[i], draw, w)
        tw, th = get_text_wh(outtext, FONTS[i], draw, w)

        if th <= h and tw < max(16, 2*w) and exact_font is None:
            #the tw requirement is less strict for cases of vertical text.
            succ = outtext
            succ_f = FONTS[i]
        else:
            break
    outtext = succ
    font_color_byte = (255,255,255,255)
    if font_color:
        font_color_byte = color_hex_to_byte(font_color)
    if font_size:
        succ_f = FONTS[font_size]
    
    draw.multiline_text((x,y), outtext, font_color_byte, font=succ_f, spacing=1)
    return draw

DEFAULT_FONT = "RobotoCondensed-Bold.ttf"
CJK_FONT = "NotoSansCJKtc-Black.ttf"

def try_switch_font(target_lang):
    if OVERRIDE_FONT is False:
        if target_lang.lower() in ['zh', 'zh-cn', 'zh-tw', 'ko', 'ja']:
            if FONT != CJK_FONT:
                load_font(CJK_FONT, "")
        else:
            if FONT != DEFAULT_FONT:
                load_font(DEFAULT_FONT, " ")

class ImageModder(object):
    @classmethod
    def write(cls, image_object, ocr_data, target_lang="en"):

        t_time = time.time()
        img = image_object.convert("RGBA")
        draw = ImageDraw.Draw(img)
        #font_name = "RobotoCondensed-Bold.ttf"

        try_switch_font(target_lang)
        font_name = FONT
        if "ocr_results" in ocr_data:
            ocr_data = ocr_data['ocr_results']
        
        for block in ocr_data['blocks']:
            for key in block['bounding_box']:
                if not type(block['bounding_box'][key]) == int:
                    block['bounding_box'][key] = int(block['bounding_box'][key])
            draw = drawTextBox(draw, block['translation'][target_lang.lower()], 
                              block['bounding_box']['x']+2,
                              block['bounding_box']['y'],
                              block['bounding_box']['w']-2,
                              block['bounding_box']['h'],
                              font_name)
        return img


IMAGES_DIRECTORY = "screenshots"

if os.name == "nt":
    dir_sep = "\\"
else:
    dir_sep = "/"


class ImageSaver(object):
    @classmethod
    def save_image(cls, image_object, image_source=None):
        try:
            os.mkdir(IMAGES_DIRECTORY)
        except:
            pass

        if image_source is not None:
            new_loc = image_source.split(".")
            new_loc[-2] = new_loc[-2]+"_t"
            new_loc = ".".join(new_loc)
        else:
            dt = datetime.datetime.now()
            extension = ".png"
            create_parts = [dt.year, dt.month, dt.day,
                            dt.hour, dt.minute, dt.second,
                            0, extension]
            dir_set = set(os.listdir(IMAGES_DIRECTORY))
            while cls.list_to_filename(create_parts) in dir_set:
                create_parts[-2]+=1
            create_filename = cls.list_to_filename(create_parts)
            new_loc = os.path.join(IMAGES_DIRECTORY, create_filename)
        image_object.save(new_loc)
        return new_loc

    @classmethod
    def list_to_filename(cls, list_obj):
        rval = [str(x) for x in list_obj]
        return "-".join(rval[0:6])+rval[6]+rval[7]

    @classmethod
    def copy(cls, org, new):
        new_file = open(new, "w")
        old_data = open(org).read()
        new_file.write(old_data)



class ImageItterator(object):
    @classmethod
    def next(cls, baseline=None, image_type=None):
        filename = cls._next_prev(baseline, image_type, pre_next="next")
        if filename:
            return os.path.join(IMAGES_DIRECTORY, filename)
        return None 

    @classmethod
    def prev(cls, baseline=None, image_type=None):
        filename = cls._next_prev(baseline, image_type, pre_next="prev")   
        if filename:
            return os.path.join(IMAGES_DIRECTORY, filename)
        return None

    @classmethod
    def date_order_convert(cls, date):
        orders = list()
        data = date.split("-")
        try:
            orders.append(int(data[0]))#year
            orders.append(int(data[1]))#month
            orders.append(int(data[2]))#day
            orders.append(int(data[3]))#hour
            orders.append(int(data[4]))#minute
            if "_" in data[5]:
                orders.append(int(data[5].partition("_")[0]))#seconds
                orders.append("_t.png")
            else:
                orders.append(int(data[5].partition(".")[0]))#seconds
                orders.append(".png")             
        except:
            print(date, len(orders))
            while len(orders) < 6:
                orders.append(0)
            if "_" in date:
                orders.append("_t.png")
            else:
                orders.append(".png")
        
        return tuple(orders)

    @classmethod
    def _next_prev(cls, baseline=None, image_type=None, pre_next="prev"):
        try:
            file_list = os.listdir(IMAGES_DIRECTORY)
        except:
            return None
        if baseline and dir_sep in baseline:
            baseline = baseline.split(dir_sep)[-1]        

        file_list = sorted(file_list, key=lambda x: cls.date_order_convert(x))
        if pre_next == "prev":
            itterator = file_list[::-1]
        else:
            itterator = file_list[::]
    
        min_date = ""
        max_date = cls.date_order_convert("200000-12-12-12-12-12.png")
        if pre_next == "next" and baseline != None:
            min_date = cls.date_order_convert(baseline)
        if pre_next == "prev" and baseline != None:
            max_date = cls.date_order_convert(baseline)
        #just get the latest image
        for filename in itterator:
            if baseline:
                if min_date >= cls.date_order_convert(filename) or max_date <= cls.date_order_convert(filename):
                    continue
            if not filename.endswith(".png"):
                continue
            stripped = filename.replace("_t.png", "").replace(".png", "")
            if not stripped.replace("-", "").isdigit():
                continue
            if filename.endswith("_t.png"):
                if image_type != "screenshot":
                    return filename
                continue
            elif image_type != "translate":
                return filename
        return None
    
