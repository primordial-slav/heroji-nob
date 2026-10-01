"""
Make the medal images shown next to decorated soldiers (website/public/medalje/).

Two decorations, each in two looks:
  - Orden narodnog heroja (a soldier's entry says "narodni heroj")
  - Partizanska spomenica 1941 (the entry says the soldier held the "spomenica")

  *-foto.webp     the photograph of the real decoration, cut out of its background
                  (the soldier popup and the Spomen-kartica)
  *-gravira.svg   an engraving traced from that photograph: its outline and the shadows
                  of its relief as lines, drawn in the text colour through a CSS mask
                  (search results)

The order's engraving gets a drawn ribbon (red with a white stripe near each edge in
the real one), since the photo's ribbon is a crumpled neck ribbon.

Sources (Wikimedia Commons), downloaded once into data-extraction/.cache/medals/:
  Orden narodnog heroja 1.png - photo by Pinki, CC BY-SA 4.0. Images made from it carry
    the same licence; the Izvori page credits it.
  R45-yo0357-Partizanska-spomenica-1941.png - the WIPO Article 6ter register's image,
    public domain.

Needs numpy, scipy, Pillow and potracer (pip install potracer).
Usage: python scripts/make_medal_images.py   (prints each image's size for Medal.tsx)
"""

import ssl
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import potrace

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data-extraction" / ".cache" / "medals"
OUT = ROOT / "website" / "public" / "medalje"

SOURCES = {
    "heroj": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Orden_narodnog_heroja_1.png",
    "spomenica": "https://upload.wikimedia.org/wikipedia/commons/a/ab/R45-yo0357-Partizanska-spomenica-1941.png",
}

# Photo heights in px: about three times the largest size the site shows them at
PHOTO_HEIGHT = {"heroj": 300, "spomenica": 180}

_SSL = ssl._create_unverified_context()


def source(kind):
    path = CACHE / (kind + ".png")
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(SOURCES[kind], headers={"User-Agent": "Mozilla/5.0 (knjiga-boraca medal images)"})
        with urllib.request.urlopen(req, timeout=60, context=_SSL) as resp:
            path.write_bytes(resp.read())
    return Image.open(path)


def lum(rgb):
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def drop_small(mask, min_area):
    lab, n = ndi.label(mask)
    if n == 0:
        return mask
    keep = np.zeros(n + 1, bool)
    keep[1:] = ndi.sum(mask, lab, range(1, n + 1)) >= min_area
    return keep[lab]


def outline(mask, width):
    return mask & ~ndi.binary_erosion(mask, iterations=width)


def shadows(L, inside, dark, rel, blur, min_area):
    """Pixels in the relief's shadow: dark outright, or much darker than their surroundings"""
    cut = ((L < dark) | (L < ndi.gaussian_filter(L, blur) - rel)) & inside
    return drop_small(cut, min_area)


def hero_lines():
    a = np.asarray(source("heroj").convert("RGBA")).astype(float)
    rgb, alpha = a[..., :3], a[..., 3]
    red = (rgb[..., 0] > rgb[..., 1] + 45) & (rgb[..., 0] > rgb[..., 2] + 45)
    white_ribbon = (lum(rgb) > 200) & (np.abs(rgb[..., 0] - rgb[..., 2]) < 30)
    metal = (alpha > 128) & ~red & ~white_ribbon
    metal[:118] = False  # the ribbon above the suspension ring
    metal = drop_small(metal, 30)
    return outline(metal, 2) | shadows(lum(rgb), metal, 70, 38, 6, 4)


def spomenica_lines():
    rgb = np.asarray(source("spomenica").convert("RGB")).astype(float)
    rgb = ndi.median_filter(rgb, size=(3, 3, 1))  # the register's image is a coarse print scan
    L = lum(rgb)
    star = drop_small(ndi.binary_fill_holes(L < 232), 200)
    leaf = (rgb[..., 0] - rgb[..., 2] > 45) & (L > 120)
    leaf = ndi.binary_opening(ndi.binary_fill_holes(ndi.binary_closing(leaf, iterations=2)), iterations=1)
    leaf = drop_small(leaf, 150) & star
    return outline(star, 2) | outline(leaf, 2) | shadows(L, star & ~leaf, 60, 45, 5, 6)


def upscale(mask, scale=3, blur=1.6):
    """Smooth the pixel steps before tracing"""
    img = Image.fromarray((mask * 255).astype(np.uint8))
    img = img.resize((img.width * scale, img.height * scale), Image.BICUBIC)
    smooth = ndi.gaussian_filter(np.asarray(img).astype(float), blur * scale / 2) > 127
    ys, xs = np.nonzero(smooth)
    return smooth[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def trace(mask):
    # potrace fills the False pixels
    curves = potrace.Bitmap(~mask).trace(turdsize=6, alphamax=1.0, opticurve=True, opttolerance=0.5)
    pt = lambda p: "%d %d" % (round(p.x), round(p.y))
    d = []
    for c in curves:
        d.append("M" + pt(c.start_point))
        for s in c.segments:
            d.append("L%sL%s" % (pt(s.c), pt(s.end_point)) if s.is_corner
                     else "C%s %s %s" % (pt(s.c1), pt(s.c2), pt(s.end_point)))
        d.append("Z")
    return "".join(d)


def ribbon(width):
    """The order's ribbon above the badge, in outline: a short pentagon with the two stripes"""
    rw = 0.84 * width
    rh = 0.44 * rw
    x0 = (width - rw) / 2
    tip = 0.02 * width
    top = tip - rh
    side = top + 0.66 * rh
    pts = "%.0f,%.0f %.0f,%.0f %.0f,%.0f %.0f,%.0f %.0f,%.0f" % (
        x0, top, x0 + rw, top, x0 + rw, side, width / 2, tip, x0, side)
    stripes = "".join('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f"/>' % (x, top, x, side)
                      for x in (x0 + 0.139 * rw, x0 + rw - 0.139 * rw))
    svg = ('<g fill="none" stroke="#000" stroke-width="%.0f" stroke-linejoin="round"><polygon points="%s"/>%s</g>'
           % (0.025 * width, pts, stripes))
    return svg, int(top) - 4


def write_svg(name, lines, with_ribbon=False):
    m = upscale(lines)
    h, w = m.shape
    body, top = ribbon(w) if with_ribbon else ("", 0)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 %d %d %d">%s<path fill-rule="evenodd" d="%s"/></svg>'
           % (top, w, h - top, body, trace(m)))
    (OUT / name).write_text(svg, encoding="utf-8")
    print("%s  %d x %d  %d bytes" % (name, w, h - top, len(svg)))


def write_photo(kind):
    if kind == "heroj":
        img = source("heroj").convert("RGBA")
        img = img.crop(img.getbbox())
        img = img.crop((0, 40, img.width, img.height))  # keep a short piece of the ribbon
    else:
        rgb = np.asarray(source("spomenica").convert("RGB"))
        L = lum(ndi.median_filter(rgb.astype(float), size=(3, 3, 1)))
        star = drop_small(ndi.binary_fill_holes(L < 232), 200)
        alpha = ndi.gaussian_filter(star * 255.0, 0.7).clip(0, 255).astype(np.uint8)
        img = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
    img = img.crop(img.getbbox())
    height = PHOTO_HEIGHT[kind]
    img = img.resize((round(img.width * height / img.height), height), Image.LANCZOS)
    name = kind + "-foto.webp"
    img.save(OUT / name, "WEBP", quality=88, method=6)
    print("%s  %d x %d  %d bytes" % (name, img.width, img.height, (OUT / name).stat().st_size))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    write_photo("heroj")
    write_photo("spomenica")
    write_svg("heroj-gravira.svg", hero_lines(), with_ribbon=True)
    write_svg("spomenica-gravira.svg", spomenica_lines())


if __name__ == "__main__":
    main()
