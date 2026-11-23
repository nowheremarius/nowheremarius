"""Render a responsive, borderless 4+3 monochrome software gallery.

The first four glyphs are localized vendor marks already stored as SVG.
FL Studio and Source Filmmaker are sourced from their recognizable logo art
where available, with bundled drawing fallbacks. MagicaVoxel uses a custom
voxel-cube pictogram: it is not presented as its official logo.
"""
from io import BytesIO
from pathlib import Path
import math
import requests
from PIL import Image, ImageDraw, ImageFont
import cairosvg

ROOT = Path("assets")
BG = (13, 17, 23, 255)
FG = (244, 244, 244, 255)
MUTED = (194, 194, 194, 255)
W, H = 1360, 185
HEADERS = ["Blender", "Adobe Audition", "Adobe Photoshop", "VEGAS Pro",
           "FL Studio", "MagicaVoxel", "Source Filmmaker"]
SVG_SOURCES = ["blender", "audition", "photoshop", "vegas"]
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT = ImageFont.truetype(FONT_PATH, 32)
FONT_SMALL = ImageFont.truetype(FONT_PATH, 29)

def crop_alpha(im):
    im = im.convert("RGBA")
    bbox = im.getchannel("A").point(lambda p: 255 if p > 12 else 0).getbbox()
    if bbox is None:
        raise RuntimeError("Empty logo shape")
    return im.crop(bbox)

def fit(im, size=128):
    im = crop_alpha(im)
    im.thumbnail((size, size), Image.Resampling.LANCZOS)
    return im

def mono(im, tint=(240, 240, 240)):
    im = crop_alpha(im)
    a = im.getchannel("A")
    out = Image.new("RGBA", im.size, tint + (0,))
    out.putalpha(a)
    return fit(out)

def svg_mark(slug):
    blob = cairosvg.svg2png(url=str(ROOT / f"{slug}.svg"), output_width=500)
    return mono(Image.open(BytesIO(blob)).convert("RGBA"))

def remote_image(url):
    r = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0 (profile asset build)"})
    r.raise_for_status()
    if b"<svg" in r.content[:800]:
        data = cairosvg.svg2png(bytestring=r.content, output_width=1200)
        return Image.open(BytesIO(data)).convert("RGBA")
    return Image.open(BytesIO(r.content)).convert("RGBA")

def fruit_fallback():
    a = Image.new("RGBA", (190, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(a)
    d.ellipse((45, 45, 140, 160), fill="#eeeeee")
    d.ellipse((52, 19, 104, 71), fill="#bcbcbc")
    d.ellipse((91, 13, 157, 69), fill="#d8d8d8")
    d.line([(112, 30), (139, 4)], fill="#eeeeee", width=9)
    return a

def fruit_mark():
    urls = [
      "https://commons.wikimedia.org/wiki/Special:FilePath/FL_Studio_Logo_Wordmark.svg",
      "https://image.pngaaa.com/264/352264-middle.png"
    ]
    for url in urls:
        try:
            img = remote_image(url)
            if "Wordmark.svg" in url:
                img = img.crop((0, 0, round(img.width * .24), img.height))
            img = crop_alpha(img)
            # Preserve a recognizable difference between fruit and leaves,
            # even after the colour logo is rendered in grayscale.
            r, g, b, a = img.split()
            pix = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    red, green, blue, alpha = pix[x, y]
                    if alpha < 8:
                        continue
                    leaf = green > red * 1.06 and green > blue * 1.07
                    pix[x, y] = ((179, 179, 179, alpha) if leaf
                                  else (245, 245, 245, alpha))
            print("FL Studio source:", url)
            return fit(img)
        except Exception as e:
            print("FL Studio source unavailable:", type(e).__name__, str(e)[:110])
    print("FL Studio fallback: vector fruit silhouette")
    return fit(fruit_fallback())

def voxel_mark():
    # Purpose-designed legible isometric cube based on voxel modeling motifs.
    im = Image.new("RGBA", (190, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(95, 14), (169, 56), (95, 99), (21, 56)], fill="#f2f2f2")
    d.polygon([(21, 56), (95, 99), (95, 177), (21, 134)], fill="#bcbcbc")
    d.polygon([(95, 99), (169, 56), (169, 134), (95, 177)], fill="#e0e0e0")
    # Inset voxel details create recognizably cubic, not amorphous, artwork.
    d.polygon([(95, 42), (133, 62), (95, 84), (57, 62)], fill=BG)
    d.polygon([(43, 84), (72, 100), (72, 133), (43, 116)], fill=BG)
    d.polygon([(119, 106), (147, 89), (147, 119), (119, 136)], fill=BG)
    return fit(im)

def reel_fallback():
    im = Image.new("RGBA", (190, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((17, 20, 172, 170), radius=44, fill="#e8e8e8")
    d.ellipse((34, 37, 157, 157), fill=BG)
    for i in range(5):
        rad = 2 * math.pi * i / 5 - math.pi / 2
        x = 95 + math.cos(rad) * 40
        y = 97 + math.sin(rad) * 40
        d.ellipse((x-14,y-14,x+14,y+14), fill="#e8e8e8")
    d.ellipse((85,87,105,107), fill="#e8e8e8")
    d.ellipse((137,29,160,52), fill=BG)
    return fit(im)

def sfm_mark():
    try:
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/Source_filmmaker_logo.svg"
        im = remote_image(url)
        im = im.crop((0, 0, round(im.width*.32), im.height))
        im = mono(im)
        print("Source Filmmaker source:", url)
        return im
    except Exception as e:
        print("Source Filmmaker fallback:", type(e).__name__, str(e)[:110])
        return reel_fallback()

def draw_line(image, entries, positions, dst):
    # Editorial scale: compact 80px marks with full-size captions.
    # Preserve 1360px artwork width for consistent responsive GitHub rendering.
    d = ImageDraw.Draw(image)
    for (label, icon), x in zip(entries, positions):
        icon = fit(icon, 80)
        y = 16 + (80 - icon.height)//2
        image.alpha_composite(icon, (round(x - icon.width/2), y))
        font = FONT_SMALL if len(label) > 14 else FONT
        b = d.textbbox((0,0), label, font=font)
        d.text((x - (b[2]-b[0])/2, 126), label, font=font, fill=MUTED)
    image.convert("RGB").save(dst, optimize=True)
    print("Saved",dst,image.size,Path(dst).stat().st_size)

def vegas_icon():
    # App icon instead of the extremely wide VEGAS wordmark (optically too small).
    try:
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/Vegas_Pro_21_logo.svg"
        im = remote_image(url)
        im = fit(im, 128)
        print("VEGAS icon source:", url)
        if im.size[0] > 0:
            pix = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    r,g,b,a = pix[x,y]
                    # VEGAS brand-blue square -> charcoal; white V -> white.
                    if a < 10: continue
                    blue = b > r*1.2 and b > g*.9 and r < 160
                    pix[x,y] = (68,68,68,a) if blue else (246,246,246,a)
        return im
    except Exception as e:
        print("VEGAS icon source unavailable, use wordmark:",type(e).__name__,str(e)[:100])
        return svg_mark("vegas")

marks = [svg_mark(s) for s in SVG_SOURCES[:3]] + [vegas_icon()]
marks.extend([fruit_mark(), voxel_mark(), sfm_mark()])
assert len(marks) == 7
for n,m in zip(HEADERS, marks):
    assert m.getchannel("A").getbbox() is not None, n
    print("Icon ready", n, m.size)

im1 = Image.new("RGBA",(W,H),BG)
draw_line(im1, list(zip(HEADERS[:4],marks[:4])), [170,510,850,1190], ROOT/"software-row-1.png")
im2 = Image.new("RGBA",(W,H),BG)
draw_line(im2, list(zip(HEADERS[4:],marks[4:])), [260,680,1100], ROOT/"software-row-2.png")
