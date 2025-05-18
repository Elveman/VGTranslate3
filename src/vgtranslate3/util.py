from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from past.builtins import basestring
from past.utils import old_div
import io
import base64
from io import BytesIO
import colorsys
from PIL import Image, ImageDraw, ImageChops

def swap_red_blue(image):
    print(image.mode)
    print(image.split())
    r,g,b = image.split()
    return Image.merge('RGB', (b,g,r))


def general_index(image_data):
    byte_data = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(byte_data))
    res = image.resize((1,1), Image.ANTIALIAS).convert("RGB")
    r, g, b = res.getpixel((0,0))
    h, s, v = colorsys.rgb_to_hsv(float(r)/255,float(g)/255,float(b)/255)
    return h,s,v

def load_image(image_data):
    if type(image_data) == Image.Image:
        return image_data
    byte_data = base64.b64decode(image_data)
    image = Image.open(BytesIO(byte_data))
    image = image.convert("RGBA")
    return image

def image_to_string(img):
    output = BytesIO()
    img.save(output, format="PNG")
    string = output.getvalue()
    return base64.b64encode(string).decode("ascii")

def image_to_string_format(img, format_type, mode="RGB"):
    output = BytesIO()
    try:
        img.convert(mode).save(output, format=format_type)
    except:
        img.convert(mode).save(output, format="BMP")
    string = output.getvalue()
    return base64.b64encode(string).decode("ascii")

def image_to_string_png(img):
    output = BytesIO()
    img.convert("RGB").save(output, format="PNG")
    string = output.getvalue()
    print(("png length: ", len(string)))
    return base64.b64encode(string).decode("ascii")

def color_hex_to_byte(text_color):
    return (int(text_color[0:2], 16),
            int(text_color[2:4], 16),
            int(text_color[4:6], 16),
            255)

def segfill(image, mark_color, target_color):
    w = image.width
    h = image.height
    mark_color = tuple(color_hex_to_byte(mark_color)[0:3])
    target_color = tuple(color_hex_to_byte(target_color)[0:3])
    image = image.convert("RGB")

    last_red = False
    h_range = list()
    w_range = list()

    for j in range(h):
        sec = image.crop((0,j, w, j+1)).getcolors()
        for num, color in sec:
            if color == target_color:
                h_range.append(j)
                break
    for i in range(w):
        sec = image.crop((i,0, i+1, h)).getcolors()
        for num, color in sec:
            if color == target_color:
                w_range.append(i)
                break
   
    new_w_range = dict()
    new_h_range = dict()
    white_count = 0
    for j in h_range:
        last_red = False
        white_count = 0 
        for i in range(max(min(w_range)-1, 0), max(w_range)):
            pix = image.getpixel((i,j))       
            if last_red == False:
                if pix == mark_color:
                    last_red = True
                    if white_count > 0:
                        for k in range(white_count):
                            image.putpixel((i-1-k,j), mark_color)
                        white_count = 0

                elif pix == target_color:
                    white_count +=1
                    new_w_range[i] = 1
                    new_h_range[j] = 1
                else:
                    white_count = 0
            elif pix == target_color:
                image.putpixel((i,j), mark_color)
                if white_count > 0:
                    for k in range(white_count):
                        image.putpixel((i-1-k,j), mark_color)
                    white_count = 0
            elif pix == mark_color:
                if white_count > 0:
                    for k in range(white_count):
                        image.putpixel((i-1-k,j), mark_color)
                    white_count = 0
            else:             
                white_count = 0
                last_red = False

   
    for entry in list(new_h_range.keys()):
        if entry > 0:
            new_h_range[entry-1] = 1
    new_h_range = sorted(new_h_range.keys())
    new_w_range = sorted(new_w_range.keys())
    white_count = 0
    #vertical pass
    for i in new_w_range:
        last_red = False
        white_count = 0
        for num_j, j in enumerate(new_h_range):
            if num_j == 0 or new_h_range[num_j-1] != j-1:
                white_count = 0

            pix = image.getpixel((i,j))
          
            if last_red == False:
                if pix == mark_color:
                    last_red = True
                    if white_count > 0:
                        for k in range(white_count):
                            image.putpixel((i,j-1-k), mark_color)
                        white_count = 0 
                elif white_count == target_color:
                    white_count += 1
                    pass
                else:
                    white_count = 0
            elif pix == target_color:
                image.putpixel((i,j), mark_color)
                if white_count > 0:
                    for k in range(white_count):
                        image.putpixel((i,j-1-k), mark_color)
                    white_count = 0 
            elif pix == mark_color:
                if white_count > 0:
                    for k in range(white_count):
                        image.putpixel((i,j-1-k), mark_color)
                    white_count = 0 
            else:
                white_count = 0
                last_red = False
    return image.convert("RGBA")


def color_dist(color1, color2):
    rr = color1[0] - color2[0]
    gg = color1[1] - color2[1]
    bb = color1[2] - color2[2]
    return rr**2+gg**2+bb**2


def reduce_to_multi_color(img, bg, colors_map, threshold):
    def vdot(a,b):
        return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]

    def vnorm(b):
        return vdot(b,b)**0.5

    def vscale(b, s):
        return [b[0]*s, b[1]*s, b[2]*s]

    def vsub(a, b):
        return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]
    img = img.convert("P", palette=Image.ADAPTIVE)
    new_palette = list()
    p = img.getpalette()
    if bg is not None:
        bg = color_hex_to_byte(bg)

    for i in range(256):
        r = p[3*i]
        g = p[3*i+1]
        b = p[3*i+2]
        closest = 1000000000
        close = color_hex_to_byte("000000")

        for entry in colors_map:
            if type(entry) in (list, tuple):
                tc, tc_map = entry
            else:
                tc, tc_map = entry, entry

            if isinstance(tc, basestring):           
                tc = color_hex_to_byte(tc)

                rr = r-tc[0]
                gg = g-tc[1]
                bb = b-tc[2]
                d = rr**2+gg**2+bb**2
                if d < closest:
                    closest = d
                    close = color_hex_to_byte(tc_map)
            else: 
                tc = [color_hex_to_byte(tc[0]),
                      color_hex_to_byte(tc[1])]
                #color range vector
                crv = [tc[1][0]-tc[0][0],
                       tc[1][1]-tc[0][1],
                       tc[1][2]-tc[0][2]]
                #relative palette vector
                rpv = [r-tc[0][0],
                       g-tc[0][1],
                       b-tc[0][2]]

                #formula to use vector dot product to get distance
                #to line segment.
                vb = crv
                va = rpv
                va1 = vdot(va, vscale(vb, old_div(1,vnorm(vb))))

                if va1 < 0 or va1 > vnorm(vb):
                    continue

                va2 = vscale(vb, old_div(va1,vnorm(vb)))
                va3 = vsub(va, va2)
                #print va3
                d = vnorm(va3)
                if d**2 < closest:
                    closest = d**2
                    if type(tc_map) in [tuple, list]:
                        if old_div(va1,vnorm(vb)) <0.5:
                            close = color_hex_to_byte(tc_map[0])
                        else:
                            close = color_hex_to_byte(tc_map[1])
                    else:
                        close = color_hex_to_byte(tc_map)
      
        if close is not None and closest <= threshold**2:
            new_palette.extend(close[:3])
        elif bg is None:
            new_palette.extend([r,g,b])
        else:
            new_palette.extend(bg[:3])
    img.putpalette(new_palette)
    return img
    


def reduce_to_colors(img, colors, threshold):
    new_palette = list()
    p = img.getpalette()
    for i in range(256):
        r = p[3*i]
        g = p[3*i+1]
        b = p[3*i+2]
        vals = list()
        for tc in colors:
            tc = color_hex_to_byte(tc)
            rr = r-tc[0]
            gg = g-tc[1]
            bb = b-tc[2]
            vals.append(rr**2+gg**2+bb**2)

        if vals and min(vals) <= threshold**2:
            new_palette.extend([255,255,255])
        else:
            new_palette.extend([0,0,0])
    img.putpalette(new_palette)
    return img


def reduce_to_text_color(img, color_thresh, bg):
    img = img.convert("RGB")
    img = img.convert("P", palette=Image.ADAPTIVE)
    p = img.getpalette()
    nc = [(color_hex_to_byte(x[0]),x[1]) for x in color_thresh]

    bg = color_hex_to_byte(bg)

    new_palette = list()
    for i in range(256):
        r = p[3*i]
        g = p[3*i+1]
        b = p[3*i+2]
        close = None
        closest = 1000000000
        for tc,thr in nc:
            rr = r-tc[0]
            gg = g-tc[1]
            bb = b-tc[2]
            d = rr**2+gg**2+bb**2
            if d < closest and d < thr**2:
                closest = d
                t = 1-(old_div(d,(thr**2.0)))
                close = [int(t*(tc[0]-bg[0])+bg[0]),
                         int(t*(tc[1]-bg[1])+bg[1]),
                         int(t*(tc[2]-bg[2])+bg[2])]
            else:
                pass
        if close:
            new_palette.extend([close[0], close[1], close[2]])
        else:
            new_palette.extend([bg[0],bg[1],bg[2]])
    img.putpalette(new_palette)
    return img





def get_color_counts(img, text_colors, threshold):
    if img.mode != "P":
        img = img.convert("P", palette=Image.ADAPTIVE)
    tc = [color_hex_to_byte(x) for x in text_colors]
    img = reduce_to_colors(img, text_colors, threshold)
    pixel_count = 0
    for c in img.convert("RGBA").getcolors():
        if c[1] == (255,255,255,255):
            pixel_count = c[0]
    return pixel_count

def get_color_counts_simple(img, text_colors, threshold):
    test_image = img.convert("P", palette=Image.ADAPTIVE).convert("RGBA")
    tc = [color_hex_to_byte(x) for x in text_colors]
    total = 0
    for num, color in test_image.getcolors():
        for pix in tc:
            if (pix[0]-color[0])**2+(pix[1]-color[1])**2+\
               (pix[2]-color[2])**2 <  threshold**2:
                total+=num
    return total

def convert_to_absolute_box(bb):
    if "x" in bb:
        return {"x1": int(bb['x']), 'y1': int(bb['y']), 
                'x2': int(bb['x'])+int(bb['w']),
                "y2": int(bb['y'])+int(bb['h'])}
    else:
        return bb  

def fix_bounding_box(img, bounding_box):
    w = img.width
    h = img.height
    for key in bounding_box:
        if isinstance(bounding_box[key], basestring):
            bounding_box[key] = int(bounding_box[key])
    if 'w' in bounding_box:
        if bounding_box['x'] < 0:
            bounding_box['x'] = 0
        elif bounding_box['x'] > w-1:
            bounding_box['x'] = w-1
        if bounding_box['y'] < 0:
            bounding_box['y'] = 0
        elif bounding_box['y'] > h-1:
            bounding_box['y'] = h-1

        if bounding_box['w'] < 0:
            bounding_box['w'] = 0
        elif bounding_box['x']+bounding_box['w'] > w-1:
            bounding_box['w'] = w-1-bounding_box['x']
        if bounding_box['h'] < 0:
            bounding_box['h'] = 0
        elif bounding_box['y']+bounding_box['h'] > h-1:
            bounding_box['h'] = h-1-bounding_box['y']

        if bounding_box['w'] ==0:
            bounding_box['w'] = 1
        if bounding_box['h'] == 0:
            bounding_box['h'] = 1 
    else:
        if bounding_box['x1'] < 0:
            bounding_box['x1'] = 0
        elif bounding_box['x1'] > w-1:
            bounding_box['x1'] = w-1
        if bounding_box['y1'] < 0:
            bounding_box['y1'] = 0
        elif bounding_box['y1'] > h-1:
            bounding_box['y1'] = h-1

        if bounding_box['x2'] < bounding_box['x1']:
            bounding_box['x2'] = bounding_box['x1']
        elif bounding_box['x2'] > w-1:
            bounding_box['x2'] = w-1
        if bounding_box['y2'] < bounding_box['y1']:
            bounding_box['y2'] = bounding_box['y1']
        elif bounding_box['y2'] > h-1:
            bounding_box['y2'] = h-1

        if bounding_box['x1']==bounding_box['x2']:
            bounding_box['x2']+=1
        if bounding_box['y1']==bounding_box['y2']:
            bounding_box['y2']+=1
    return bounding_box

def intersect_area(bb,tb):
    dx = min(bb['x2'], tb['x2'])-max(bb['x1'], tb['x1'])
    dy = min(bb['y2'], tb['y2'])-max(bb['y1'], tb['y1'])
    if dx >= 0 and dy>=0:
        return dx*dy
    return 0

def get_bounding_box_area(bb):
    return intersect_area(bb,bb)   

def chop_to_box(image, tb, bb):
    chop = [0,0,image.width,image.height]
    if tb['x1'] < bb['x']:
        chop[0] = bb['x']-tb['x1']
    if tb['y1'] < bb['y']:
        chop[1] = bb['y']-tb['y1']
    if tb['x2'] > bb['x']+bb['w']:
        chop[2] = image.width-tb['x2']+bb['x']+bb['w'] 
    if tb['y2'] > bb['y']+bb['h']:
        chop[3] = image.height-tb['y2']+bb['y']+bb['h'] 
    image= image.crop(chop)
    return image

def get_best_text_color(image, text_colors, threshold):
    test_image = image.convert("P", palette=Image.ADAPTIVE).convert("RGBA")
    tc = [[x,color_hex_to_byte(x)] for x in text_colors]
    totals = {}
  
    for num, color in test_image.getcolors():
        for c, pix in tc:
            if (pix[0]-color[0])**2+(pix[1]-color[1])**2+\
               (pix[2]-color[2])**2 <  threshold**2:
                totals[c]=totals.get(c,0)+num
    if totals:
        for num, colors  in test_image.getcolors():
            for c, pix in tc:
                totals[c] = totals.get(c,0)+num
    best = max(totals, key=totals.get)
    return best
    

def tint_image(image, color, border=2):
    byte_color = color_hex_to_byte(color)
    image = image.convert("RGBA")

    tint_image = Image.new("RGBA", image.size, (255,255,255,255))
    draw = ImageDraw.Draw(tint_image)
    draw.rectangle([1,1, image.width-1,image.height-1],
                   fill=byte_color, 
                   outline=(255,255,255,255))
    new_image = ImageChops.multiply(image, tint_image)
    return new_image


def black_expand(image, mark_color, target_colors):
    w = image.width
    h = image.height
    if isinstance(target_colors, basestring):
        target_colors = [target_colors]

    mark_color = tuple(color_hex_to_byte(mark_color)[0:3])
    target_colors = [tuple(color_hex_to_byte(x)[0:3]) for x in target_colors]

    image = image.convert("RGB")
    t_time=time.time()
    h_range = list()
    w_range = list()

    #expand horizontally first:
    for j in range(h):
        sec = image.crop((0,j, w, j+1)).getcolors()
        for num, color in sec:
            if color == mark_color:
                #there is a black pixel on this line
                for i in range(w):
                    if image.getpixel((i,j)) == mark_color:#in target_colors:
                        if i > 0 and image.getpixel((i-1, j)) in target_colors:
                            image.putpixel((i-1,j), mark_color)
                        if i < w-1 and image.getpixel((i+1, j)) in target_colors:
                            image.putpixel((i+1,j), mark_color)
                break
    #expand vertical first:
    for i in range(w):
        sec = image.crop((i,0, i+1, h)).getcolors()
        for num, color in sec:
            if color == mark_color:
                #there is a black pixel on this line
                for j in range(h):
                    if image.getpixel((i,j)) == mark_color:#in target_colors:
                        if j > 0 and image.getpixel((i, j-1)) in target_colors:
                            image.putpixel((i,j-1), mark_color)
                        if j < h-1 and image.getpixel((i, j+1)) in target_colors:
                            image.putpixel((i,j+1), mark_color)
                break
    print("Black expand took: "+str(time.time()-t_time))
    return image

def expand_vertical(img, bg_color, target_color):
    def cache_get(img, xy, cache):
        if xy not in cache:
            cache[xy] = img.getpixel(xy)
        return cache[xy]
       
    t_time = time.time()
    bg = color_hex_to_byte(bg_color)[:3]
    target = color_hex_to_byte(target_color)[:3]
   
    w = img.width
    h = img.height
    image = img.convert("RGB")

    h_range = list()
    for j in range(h):
        sec = image.crop((0,j, w, j+1)).getcolors()
        for num, color in sec:
            if color == target:
                if j > 0:
                    h_range.append(j-1)
                if j < h-1:
                    h_range.append(j+1)
                h_range.append(j)
                break
    h_range = list(set(h_range))
    h_range.sort()
   
    for i in range(w):
        sec = image.crop((i,0, i+1, h)).getcolors()
        for num, color in sec:
            if color == target:
                upset = dict()
                cache = dict()
                for j in h_range:
                    pix = cache_get(image, (i,j), cache)#.getpixel((i,j))
                    if pix == bg:
                        if (j > 0 and cache_get(image,(i,j-1), cache) == target) or\
                                (j < h-1 and cache_get(image, (i,j+1), cache) == target):
                            upset[j] = 1
                for key in upset:
                    image.putpixel((i, key), target)
    print("vert expand ", time.time()-t_time)
    return image
   

def expand_horizontal(img, bg_color, target_color):
    def cache_get(img, xy, cache):
        if xy not in cache:
            cache[xy] = img.getpixel(xy)
        return cache[xy]
       
    t_time = time.time()
    bg = color_hex_to_byte(bg_color)[:3]
    target = color_hex_to_byte(target_color)[:3]
   
    w = img.width
    h = img.height
    image = img.convert("RGB")

    w_range = list()
    for i in range(w):
        sec = image.crop((i, 0, i+1, h)).getcolors()
        for num, color in sec:
            if color == target:
                if i > 0:
                    w_range.append(i-1)
                if i < w-1:
                    w_range.append(i+1)
                w_range.append(i)
                break

    w_range = list(set(w_range))
    w_range.sort()
   
    for j in range(h):
        sec = image.crop((0,j, h, j+1)).getcolors()

        for num, color in sec:
            if color == target:
                upset = dict()
                cache = dict()
                for i in w_range:

                    pix = cache_get(image, (i,j), cache)#.getpixel((i,j))
                    if pix == bg:
                        if (i > 0 and cache_get(image,(i-1,j), cache) == target) or\
                                (i < w-1 and cache_get(image, (i+1,j), cache) == target):
                            upset[i] = 1
                for key in upset:
                    image.putpixel((key, j), target)
    print("horizontal expand ", time.time()-t_time)
    return image

def draw_solid_box(image, color, bb):
    draw = ImageDraw.Draw(image)
    byte_color = color_hex_to_byte(color)
    draw.rectangle([bb['x1'], bb['y1'], bb['x2'], bb['y2']],
                   fill=byte_color)
    return image

def fix_neg_width_height(bb):
    if bb['w'] < 0:
         new_x = bb['x']+bb['w']
         new_w = -1*bb['w']
         bb['x'] = new_x
         bb['w'] = new_w
    if bb['h'] < 0:
         new_y = bb['y']+bb['h']
         new_h = -1*bb['h']
         bb['y'] = new_y
         bb['h'] = new_h
    return bb

