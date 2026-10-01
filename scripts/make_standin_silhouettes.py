"""
Stand-in portraits for soldiers we have no photograph of: anonymous grey silhouettes of partisans in caps, made
from real portraits in the znaci.org photo gallery, so the poses are the period's own.

Each portrait is reduced to an outline and nothing else: the person is cut out of the photo (DeepLabV3's person
class, then sharpened against the photo's own background around the head, so the cap keeps its shape), mirrored,
smoothed until no face, ear, hair or moustache survives, and traced to a simple path. The site draws it in grey
with a red star on the front of the cap (website/app/components/StandInPortrait.tsx). No photo is shipped.

    python scripts/make_standin_silhouettes.py          # writes website/app/data/silhouettes.ts

Needs torchvision matching the installed torch (pip install --no-deps torchvision==0.18.1) and downloads its
DeepLabV3-MobileNetV3 weights (42 MB) on the first run; the photos are cached under data-extraction/.cache/.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import contourpy
import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image, ImageFile
from scipy import ndimage
from torchvision.models.segmentation import DeepLabV3_MobileNet_V3_Large_Weights, deeplabv3_mobilenet_v3_large

ImageFile.LOAD_TRUNCATED_IMAGES = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import find_unit_photos as F  # noqa: E402

OUT = ROOT / 'website' / 'app' / 'data' / 'silhouettes.ts'
W, H = 300, 400                     # the frame, 3:4

# name, znaci.org photo, the person's box in it (for one person of a group photo; None: found from the photo),
# where the cap's star sits across the cap (0 = the side the figure faces after mirroring… 1 = the other), cap
SOURCES = [
    ('m-titovka-1', 8606, None, 0.6, 'titovka'),
    ('m-titovka-2', 10342, None, 0.55, 'titovka'),
    ('m-titovka-3', 11864, None, 0.5, 'titovka'),
    ('m-sajkaca-1', 14593, None, 0.5, 'sajkaca'),
    ('z-titovka-1', 14661, None, 0.5, 'titovka'),
]

WEIGHTS = DeepLabV3_MobileNet_V3_Large_Weights.DEFAULT
MODEL = deeplabv3_mobilenet_v3_large(weights=WEIGHTS).eval()
PERSON = WEIGHTS.meta['categories'].index('person')


def photo(pid: int) -> Image.Image:
    path = F.CACHE / 'full' / f'{pid}.jpg'
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(F._get(f'{F.BASE}/images/{pid}.jpg'))
    return Image.open(path).convert('RGB')


def person_prob(im: Image.Image, size: int = 640) -> np.ndarray:
    s = size / max(im.size)
    small = im.resize((round(im.width * s), round(im.height * s)), Image.BICUBIC)
    t = TF.normalize(TF.to_tensor(small), [0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    with torch.no_grad():
        p = torch.softmax(MODEL(t.unsqueeze(0))['out'][0], 0)[PERSON].numpy()
    return np.asarray(Image.fromarray((p * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR)) / 255


def largest(mask: np.ndarray, at: tuple[int, int] | None = None) -> np.ndarray:
    lab, n = ndimage.label(mask)
    if not n:
        return mask
    k = lab[at] if at and lab[at] else 1 + int(np.argmax(ndimage.sum(mask, lab, range(1, n + 1))))
    return ndimage.binary_fill_holes(lab == k)


def head_box(im: Image.Image) -> tuple[int, int, int, int]:
    """Head and shoulders, 3:4, from a first pass over the whole photo."""
    m = largest(person_prob(im, 520) > 0.5)
    top = int(np.nonzero(m.any(1))[0].min())
    hx = np.nonzero(m[top:top + im.height // 5].any(0))[0]
    cx = (hx.min() + hx.max()) / 2
    w = min(im.width, round((hx.max() - hx.min()) * 2.6))
    x0 = int(max(0, min(im.width - w, cx - w / 2)))
    y0 = int(max(0, top - 0.08 * w))
    return x0, y0, x0 + w, min(im.height, y0 + round(w * 4 / 3))


def sharpen(gray: np.ndarray, m: np.ndarray) -> np.ndarray:
    """Within a band around the model's soft outline, what differs from the photo's background (estimated from the
    pixels well outside it) is the figure: the cap keeps its edge. Only for the head; the shoulders keep the model's."""
    band = max(6, int(0.05 * gray.shape[1]))
    outer = ~ndimage.binary_dilation(m, iterations=band)
    inner = ndimage.binary_erosion(m, iterations=band)
    sig = 0.04 * gray.shape[1]
    bg = ndimage.gaussian_filter(gray * outer, sig) / np.maximum(ndimage.gaussian_filter(outer.astype(float), sig), 1e-3)
    diff = ndimage.gaussian_filter(np.abs(gray - bg), 1.5)
    ring = ~outer & ~inner
    t = max(18.0, np.percentile(diff[ring], 45)) if ring.any() else 25.0
    fig = ndimage.binary_opening(inner | (ring & (diff > t)), iterations=2)
    fig = largest(fig)
    top = int(np.nonzero(m.any(1))[0].min()) if m.any() else 0
    cut = min(m.shape[0], top + int(0.42 * m.shape[1]))
    out = m.copy()
    out[:cut] = fig[:cut]
    out = ndimage.binary_opening(out, iterations=max(2, int(0.006 * m.shape[1])))
    return largest(out)


def framed(m: np.ndarray) -> np.ndarray:
    """Mirrored, onto the 300 x 400 frame; the body runs straight down from the chest."""
    m = np.fliplr(m)
    img = Image.fromarray((m * 255).astype(np.uint8)).resize((W, max(1, round(m.shape[0] * W / m.shape[1]))), Image.BILINEAR)
    a = np.asarray(img) / 255.0
    if a.shape[0] < H:
        a = np.vstack([a, np.repeat(a[-1:], H - a.shape[0], 0)])
    a = a[:H].copy()
    if a[0].max() > 0.5:                                  # a little air above a head the photo cut
        a = np.vstack([np.zeros((16, W)), a])[:H]
    widths = (a > 0.5).sum(1)
    low = [r for r in range(H // 2, H) if widths[r] >= 0.6 * widths.max()]
    r0 = min(int(0.8 * H), low[-1] if low else int(0.8 * H))
    row = np.append(a[r0] > 0.5, False)
    runs, start = [], None
    for x, on in enumerate(row):
        if on and start is None:
            start = x
        elif not on and start is not None:
            runs.append((x - start, start, x))
            start = None
    if runs:
        _, x0, x1 = max(runs)
        a[r0:] = 0.0
        a[r0:, x0:x1] = 1.0
    return ndimage.gaussian_filter(a, sigma=3.2)


def rdp(pts: np.ndarray, eps: float) -> np.ndarray:
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    d = np.abs(np.cross(b - a, pts - a)) / (math.hypot(*(b - a)) or 1)
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([rdp(pts[:i + 1], eps)[:-1], rdp(pts[i:], eps)])
    return np.vstack([a, b])


def trace(smooth: np.ndarray) -> str:
    field = np.pad(smooth, 1)
    field[-1, 1:-1] = smooth[-1]                          # the body runs out of the frame's bottom
    parts = []
    for ln in contourpy.contour_generator(z=field).lines(0.5):
        ln = ln - 1
        ln[:, 0] = ln[:, 0].clip(0, W)
        ln[:, 1] = ln[:, 1].clip(0, H)
        area = 0.5 * abs(np.dot(ln[:, 0], np.roll(ln[:, 1], 1)) - np.dot(ln[:, 1], np.roll(ln[:, 0], 1)))
        if len(ln) < 20 or area < 0.02 * W * H:            # specks
            continue
        parts.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in rdp(ln, 0.7)) + ' Z')
    return ' '.join(parts)


def star_at(smooth: np.ndarray, across: float) -> tuple[float, float]:
    """On the cap's front: across its span a little below the top, a little over a third of the way down the cap."""
    inside = smooth > 0.5
    top = int(np.nonzero(inside.any(1))[0].min())
    xs = np.nonzero(inside[min(H - 1, top + int(0.06 * H))])[0]
    x = xs.min() + (xs.max() - xs.min()) * (1 - across)   # mirrored
    ys = np.nonzero(inside[:, int(round(x))])[0]
    return round(float(x) / W * 100, 1), round(float(ys.min() + 0.09 * H) / H * 100, 1)


def main():
    rows = []
    for name, pid, box, across, cap in SOURCES:
        im = photo(pid)
        box = box or head_box(im)
        crop = im.crop(box)
        prob = person_prob(crop)
        m = largest(prob > 0.5, at=(int(crop.height * 0.25), crop.width // 2))
        m = sharpen(np.asarray(crop.convert('L'), dtype=float), m)
        smooth = framed(m)
        x, y = star_at(smooth, across)
        rows.append((name, cap, trace(smooth), x, y))
        print(name, pid, cap, (x, y))
    lines = [
        '// Generated by scripts/make_standin_silhouettes.py: anonymous outlines of partisans in caps (from period',
        '// portraits, mirrored and smoothed), on a 300 x 400 frame; the star is where the cap\'s star goes (percent).',
        "import type { Silhouette } from '@/app/lib/standIn'",
        '',
        'export const silhouettes: Silhouette[] = [',
    ]
    for name, cap, d, x, y in rows:
        lines.append(f"  {{ id: '{name}', woman: {'true' if name.startswith('z-') else 'false'}, cap: '{cap}', "
                     f"star: [{x}, {y}],\n    d: '{d}' }},")
    lines.append(']')
    OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(rows)} silhouettes → {OUT}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
