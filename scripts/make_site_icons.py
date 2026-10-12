"""The site's icons and its share image, in website/public/.

- icon.svg, favicon.ico (16, 32, 48 px), apple-icon.png (180 px): a white five-pointed star on Partisan red, square
  corners (DESIGN.md).
- og.jpg (1200 x 630): the home band as a link preview shows it: the 2. krajiška photograph (BandPhoto.tsx) in
  grey, multiplied into the red at the band's opacity.

Usage: python scripts/make_site_icons.py
"""
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageOps

PUBLIC = Path(__file__).resolve().parent.parent / 'website' / 'public'
RED = (0x9a, 0x22, 0x26)
BAND_PHOTO = PUBLIC / 'images' / '2-krajiska-brigada.jpg'
BAND_OPACITY = 0.6                 # --band-photo-opacity, light theme
STAR_RADIUS = 0.36                 # of the side: the star's outer points


def star(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    inner = r * math.sin(math.radians(18)) / math.sin(math.radians(126))
    points = []
    for i in range(10):
        a = math.radians(-90 + 36 * i)
        rr = r if i % 2 == 0 else inner
        points.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return points


def icon(size: int) -> Image.Image:
    scale = 8                                          # drawn large, then scaled down for smooth edges
    s = size * scale
    im = Image.new('RGB', (s, s), RED)
    ImageDraw.Draw(im).polygon(star(s / 2, s * 0.53, s * STAR_RADIUS), fill='white')
    return im.resize((size, size), Image.LANCZOS)


def svg() -> str:
    points = ' '.join(f'{x:.2f},{y:.2f}' for x, y in star(50, 53, 100 * STAR_RADIUS))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<rect width="100" height="100" fill="#9a2226"/><polygon points="{points}" fill="#fff"/></svg>\n')


def share_image() -> Image.Image:
    photo = ImageOps.fit(Image.open(BAND_PHOTO).convert('L'), (1200, 630), Image.LANCZOS, centering=(0.5, 0.48))
    photo = ImageEnhance.Contrast(photo).enhance(1.1).convert('RGB')
    red = Image.new('RGB', photo.size, RED)
    # multiply, then mix with the plain red at the band's opacity
    return Image.blend(red, ImageChops.multiply(red, photo), BAND_OPACITY)


def main() -> None:
    (PUBLIC / 'icon.svg').write_text(svg(), encoding='utf-8')
    icon(48).save(PUBLIC / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    icon(180).save(PUBLIC / 'apple-icon.png', optimize=True)
    share_image().save(PUBLIC / 'og.jpg', quality=85, optimize=True, progressive=True)
    for name in ('icon.svg', 'favicon.ico', 'apple-icon.png', 'og.jpg'):
        print(f'{name}: {(PUBLIC / name).stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
