"""A portrait's gentle tone correction (the user's yes of 2026-11-27 to the proposal of 2026-11-02).

Each step only where its fault shows at the size the print is seen (HEIGHT high), and each only pulls the print towards
the middle of the collection:

1. dots: a book's halftone screen blurred at the dots' own spacing, then the edges given back a little;
2. flat, grey tones spread (at most 1.65 times);
3. a very dark face lifted part of the way;
4. a hard print's pure black and white eased.

Nothing is painted in: what the scan lost stays lost. A very light face is left alone (darkening it looked worse), and
so is a soft print (sharpening only adds artefacts). extract_book_portraits.save() runs it on every new portrait but
those of Wikimedia Commons and Wikipedia, whose licences ask that a change be noted.
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HEIGHT = 240          # the print in the record (extract_book_portraits.HEIGHT)


def box(a, r):
    k = 2 * r + 1
    c = np.cumsum(np.cumsum(np.pad(a, ((r + 1, r), (r + 1, r)), mode='edge'), 0), 1)
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def centre(a):
    h, w = a.shape
    return a[int(h * .06):int(h * .94), int(w * .06):int(w * .94)]


def at_print(a):
    h, w = a.shape
    if h == HEIGHT:
        return a
    im = Image.fromarray(np.uint8(np.clip(a, 0, 255) + .5), 'L')
    return np.asarray(im.resize((max(1, round(w * HEIGHT / h)), HEIGHT), Image.LANCZOS), float)


def grain(a):
    """How strong the fine detail is, and the grain in the print's quietest parts, for the tones it has."""
    c = centre(at_print(a))
    lo, hi = np.percentile(c, [2, 98])
    rng = max(hi - lo, 1.0)
    lap = (np.roll(c, 1, 0) + np.roll(c, -1, 0) + np.roll(c, 1, 1) + np.roll(c, -1, 1) - 4 * c)[2:-2, 2:-2]
    hp = c - box(c, 2)
    return float(np.abs(lap).mean() / rng * 100), float(np.percentile(box(np.abs(hp), 4), 20) / rng * 100)


def screen_freq(a):
    """The frequency of the lowest strong peak of a screen in the spectrum, off the axes and clear of the centre."""
    h, w = a.shape
    pad = max(h, w) // 8
    b = np.pad(a, pad, mode='reflect')
    mag = np.log1p(np.abs(np.fft.rfft2(b - b.mean())))
    small = mag[::2, ::2]
    bg = ndi.median_filter(small, size=max(9, min(small.shape) // 12), mode='nearest')
    bg = ndi.zoom(bg, (mag.shape[0] / bg.shape[0], mag.shape[1] / bg.shape[1]), order=1)
    fy = np.fft.fftfreq(b.shape[0])[:, None]
    fx = np.fft.rfftfreq(b.shape[1])[None, :]
    r = np.hypot(fy, fx)
    on_axis = (np.abs(fy) < .012) | (np.abs(fx) < .012)
    peak = ((mag - bg) > 2.2) & (r > .08) & ~on_axis
    return float(r[peak].min()) if int(peak.sum()) >= 2 else 0.0


def zone(a):
    """Where the face mostly is in a print framed as the site frames it."""
    h, w = a.shape
    return a[int(h * .14):int(h * .55), int(w * .28):int(w * .72)]


def correct(im: Image.Image):
    """The corrected photo (greyscale) and the steps taken, {} where it needs none (then the photo comes back as it was)."""
    if im.mode not in ('L', 'LA', 'P', 'RGB'):
        return im, {}
    a = np.asarray(im.convert('L'), float)
    H = a.shape[0]
    steps = {}
    # 1. dots
    sharp, noise = grain(a)
    if sharp > 30 or noise > 5:
        f0 = screen_freq(a)
        sp = min(.3415 / f0 * HEIGHT / H, 1.9) if f0 else .8      # in the print's pixels
        s = sp * H / HEIGHT
        soft = ndi.gaussian_filter(a, s, mode='reflect')
        a = soft + .5 * (soft - ndi.gaussian_filter(soft, 1.6 * s, mode='reflect'))    # the edges back a little
        steps['dots'] = round(sp, 2)
    # 2. flat tones
    c = centre(a)
    lo, hi = np.percentile(c, [2, 98])
    r = hi - lo
    if r < 125:
        ramp = float(np.clip((125 - r) / 25, 0, 1))
        gain = 1 + (min(1.65, 190 / max(r, 1)) - 1) * ramp
        mid = (hi + lo) / 2
        a = (a - mid) * gain + mid + (128 - mid) * .4 * ramp
        steps['flat'] = round(gain, 2)
    a = np.clip(a, 0, 255)
    # 3. a dark face lifted part of the way
    z = zone(a)
    f = float(np.median(z))
    if 2 < f < 65:
        g = np.log((65 + (f - 65) * .35) / 255) / np.log(f / 255)
        g = float(np.clip(g, .55, 1))
        a = 255 * (a / 255) ** g
        steps['face'] = round(g, 2)
    # 4. a hard print: its pure black and white eased
    c = centre(a)
    pure = ((c < 8).mean() + (c > 247).mean()) * 100
    if pure > 30:
        if 'dots' not in steps:
            a = ndi.gaussian_filter(a, .4 * H / HEIGHT, mode='reflect')
        a = 14 + a * (240 - 14) / 255
        steps['hard'] = round(pure)
    if not steps:
        return im, {}
    return Image.fromarray(np.uint8(np.clip(a, 0, 255) + .5), 'L'), steps


def untouched(credit: str) -> bool:
    """A photo the correction leaves as it is: Wikimedia Commons' and Wikipedia's, whose licences ask that changes be noted."""
    return 'Wikimedia' in credit or 'Wikipedia' in credit
