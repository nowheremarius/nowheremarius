"""Generate the profile banner from the GitHub avatar."""
from io import BytesIO
from pathlib import Path
import random
import requests
from PIL import Image, ImageEnhance, ImageOps

AVATAR = "https://avatars.githubusercontent.com/u/171191281?v=4&size=1024"
OUT = Path("assets/monolith-banner.jpg")

resp = requests.get(AVATAR, timeout=30, headers={"User-Agent": "github-profile-asset-builder"})
resp.raise_for_status()
portrait = Image.open(BytesIO(resp.content)).convert("RGB")
W, H = 1600, 480
base = Image.new("RGB", (W, H), (6, 6, 6))
left_w = 810
ratio = max(left_w / portrait.width, H / portrait.height)
portrait = portrait.resize((round(portrait.width * ratio), round(portrait.height * ratio)), Image.Resampling.LANCZOS)
ox = max(0, (portrait.width - left_w) // 2)
oy = max(0, (portrait.height - H) // 2)
portrait = portrait.crop((ox, oy, ox + left_w, oy + H))
portrait = ImageOps.grayscale(portrait)
portrait = ImageEnhance.Contrast(portrait).enhance(1.26)
# Fade the portrait into the right-side black background.
fade = Image.new("L", (left_w, H))
pixels = fade.load()
for y in range(H):
    for x in range(left_w):
        if x < 510:
            v = 255
        else:
            t = (x - 510) / (left_w - 510)
            v = round(255 * (1 - t) ** 1.75)
        pixels[x, y] = v
base.paste(portrait.convert("RGB"), (0, 0), fade)
rnd = random.Random(1337)
noise = Image.new("L", (W, H))
noise.putdata([rnd.randrange(10, 36) for _ in range(W * H)])
grain = Image.merge("RGB", (noise, noise, noise))
base = Image.blend(base, Image.blend(base, grain, .23), .32)
OUT.parent.mkdir(exist_ok=True)
base.save(OUT, quality=86, optimize=True, subsampling=0)
print(f"Created {OUT}: {W}x{H}, {OUT.stat().st_size} bytes")
