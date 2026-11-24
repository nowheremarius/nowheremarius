"""Create monochrome PNG versions of application icons."""
from io import BytesIO
from pathlib import Path
import requests
from PIL import Image, ImageOps

ROOT = Path("assets")
ROOT.mkdir(exist_ok=True)
SOURCES = {
    "flstudio": [
      "https://commons.wikimedia.org/wiki/Special:FilePath/FL_Studio_Logo_Wordmark.svg",
      "https://icons.iconarchive.com/icons/dakirby309/simply-styled/128/FL-Studio-icon.png"
    ],
    "magicavoxel": [
      "https://raw.githubusercontent.com/ephtracy/ephtracy.github.io/master/favicon.png"
    ],
    "sfm": [
      "https://cdn2.steamgriddb.com/file/sgdb-cdn/icon/64b3ec1fdfacead70c3a9bd77d824306/32/512x512.png",
      "https://commons.wikimedia.org/wiki/Special:FilePath/Source_filmmaker_logo.svg"
    ],
}

def fetch_icon(url):
    response = requests.get(url, timeout=25, headers={"User-Agent": "MonolithProfileAssetGenerator/1.0 (public GitHub profile)"})
    response.raise_for_status()
    raw = response.content
    if raw[:200].find(b"<svg") >= 0 or b"<svg" in raw[:600]:
        import cairosvg
        raw = cairosvg.svg2png(bytestring=raw, output_width=320)
    return Image.open(BytesIO(raw)).convert("RGBA")

def monochrome_icon(source):
    source.thumbnail((112, 112), Image.Resampling.LANCZOS)
    alpha = source.getchannel("A")
    gray = ImageOps.grayscale(source)
    # Opaque images use the corner colour to estimate a foreground mask.
    if alpha.getextrema()[0] == 255:
        extrema = gray.getextrema()
        if extrema[1] - extrema[0] > 15:
            # White shapes on dark tiles: derive mask from deviations from corner color.
            corner = gray.getpixel((0, 0))
            alpha = gray.point(lambda v: min(255, abs(v - corner) * 3))
        else:
            alpha = Image.new("L", gray.size, 255)
    white = Image.new("RGBA", source.size, (240, 240, 240, 0))
    white.putalpha(alpha)
    tile = Image.new("RGBA", (144, 144), (0, 0, 0, 0))
    tile.alpha_composite(white, ((144 - white.width) // 2, (144 - white.height) // 2))
    return tile

for slug, urls in SOURCES.items():
    last = None
    for url in urls:
        try:
            icon = fetch_icon(url)
            output = ROOT / f"{slug}-mark.png"
            monochrome_icon(icon).save(output, optimize=True)
            print(slug, "source:", url, "saved", output.stat().st_size, "bytes")
            break
        except Exception as exc:
            last = exc
            print(slug, "failed source:", url, type(exc).__name__)
    else:
        raise RuntimeError(f"No usable source for {slug}: {last}")
