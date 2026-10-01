"""
Smaller copies of the unit photos, so the home page cards, the masthead band and the record dialog
load only what they draw (website/app/lib/unitImage.ts gives them to the img as a srcset).

For every `image: '/images/<file>'` in website/app/data/units.ts, writes JPEG copies 640, 960 and
1280 px wide (only the widths below the original's) to website/public/images/w640/, w960/ and w1280/,
under the original's file name, and the copies' widths and each original's width and height to
website/app/data/unitImageSizes.json.
The originals are never changed. A copy newer than its original is kept as it is; copies of photos
no unit uses any more are removed.

Re-run after adding a unit or changing a unit's photo:
    python scripts/make_unit_image_sizes.py
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
UNITS_TS = ROOT / 'website' / 'app' / 'data' / 'units.ts'
IMAGES = ROOT / 'website' / 'public' / 'images'
SIZES_JSON = ROOT / 'website' / 'app' / 'data' / 'unitImageSizes.json'
WIDTHS = (640, 960, 1280)
QUALITY = 80


def unit_images():
    """The /images/<file> paths of the unit photos, in the order units.ts lists them."""
    paths = re.findall(r"image:\s*'(/images/[^']+)'", UNITS_TS.read_text(encoding='utf-8'))
    return list(dict.fromkeys(paths))


def write_copy(original, copy, width):
    with Image.open(original) as im:
        # The browser turns a photo by its EXIF orientation, so the copies are turned the same way
        im = ImageOps.exif_transpose(im)
        height = round(im.height * width / im.width)
        small = im.convert('RGB').resize((width, height), Image.LANCZOS)
    copy.parent.mkdir(parents=True, exist_ok=True)
    small.save(copy, 'JPEG', quality=QUALITY, progressive=True, optimize=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sizes = {}
    wanted = {width: set() for width in WIDTHS}
    before = 0
    after = {w: 0 for w in WIDTHS}
    written = 0

    for path in unit_images():
        name = path[len('/images/'):]
        original = IMAGES / name
        if '/' in name or not original.is_file():
            print(f'  skipped {path}: not a file in website/public/images/')
            continue
        with Image.open(original) as im:
            width, height = ImageOps.exif_transpose(im).size
            is_jpeg = im.format == 'JPEG'
        sizes[path] = [width, height]
        size = original.stat().st_size
        before += size
        # What each width of screen loads: the smallest file at least that wide, else the original
        chosen = {w: size for w in WIDTHS}
        if not is_jpeg:
            print(f'  {name}: not a JPEG, no copies')
        else:
            for w in WIDTHS:
                if w >= width:
                    continue
                copy = IMAGES / f'w{w}' / name
                wanted[w].add(name)
                if not copy.exists() or copy.stat().st_mtime < original.stat().st_mtime:
                    write_copy(original, copy, w)
                    written += 1
                chosen[w] = copy.stat().st_size
        for w in WIDTHS:
            after[w] += chosen[w]

    # Copies of photos no unit uses any more
    for w in WIDTHS:
        folder = IMAGES / f'w{w}'
        if folder.is_dir():
            for copy in folder.iterdir():
                if copy.is_file() and copy.name not in wanted[w]:
                    copy.unlink()
                    print(f'  removed w{w}/{copy.name}')

    index = {'widths': list(WIDTHS), 'photos': sizes}
    SIZES_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    mb = lambda n: f'{n / 1_000_000:.2f} MB'
    print(f'{len(sizes)} unit photos, {written} copies written')
    print(f'  originals:            {mb(before)}')
    for w in WIDTHS:
        print(f'  {w} px (or smaller):'.ljust(24) + mb(after[w]))
    print(f'Wrote {SIZES_JSON.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
