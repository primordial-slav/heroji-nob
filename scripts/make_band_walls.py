"""The home band's walls: the arrangements of the posters, of which components/BandPosters.tsx shows one per page load. Each wall has one
structure, the one the user chose of 2026-11-05 (two rows on each margin, every poster the same height, about 10 px of
overlap, a slight tilt); only the posters and their order differ. Written to website/app/data/bandWalls.json, which the page
loads only on screens wide enough to show it.

python scripts/make_band_walls.py   (reads the prints in website/public/plakati-band: run make_band_posters.py first)

The walls keep the numbers of the user's mockups page, and the posters those of the ranking page. Mockups 13, 14 and 17 are
left out by the user's decision of that day. Makedonka (66, added 2026-11-27) stands second from the column in eight walls.
"""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_write import write_text  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
PRINTS = ROOT / 'website' / 'public' / 'plakati-band'
OUT = ROOT / 'website' / 'app' / 'data' / 'bandWalls.json'

POSTER = {
    1: 'zena-u-borbi', 2: 'miting-zena', 3: 'ni-zrno', 4: 'narod', 5: 'zima', 6: 'bratstvom', 7: 'u-borbu', 8: 'slovenske-zene', 9: 'zgrabimo',
    10: 'svi-u-borbu', 11: 'srbija', 13: 'svi-na-front', 14: 'osmi-mart', 15: 'za-zadnji-udar', 16: 'gradi-zemunice', 17: 'dalmatinka', 18: 'partizanka',
    19: 'ja-se-borim', 22: 'zena-kroz-borbu', 30: 'svi-u-partizane', 33: 'titova-armada', 34: 'ranjenici', 35: 'nov-izdajalce', 43: 'ujedinjeni',
    46: 'smrt-fasizmu', 47: 'za-slobodu-hrvatske', 48: 'vse-za-vojsko', 49: 'daruj-zbiraj', 51: 'ustanak-crna-gora', 53: 'hocemo-trst', 55: 'po-cici-i-zimi',
    56: 'slovenska-zena', 59: 'vstaja', 61: 'na-bunker', 62: 'domovi-sume', 63: 'kroz-sumu', 64: 'uz-prugu', 65: 'kolona-v-snegu',
    66: 'makedonka',  # not on the ranking page: the cover of Makedonka no. 1, the Macedonian piece (the user's yes of 2026-11-27)
}
ASPECT = {}
for n, pid in POSTER.items():
    with Image.open(PRINTS / f'{pid}.webp') as im:
        ASPECT[n] = im.width / im.height

ROWS = {'l': [(-8, 178), (158, 178)], 'r': [(-6, 178), (160, 178)]}
GAP, START = -10, 24
WOBBLE = (-2, 1, -1, 2, 0, -3, 1, 2, -1)


def rows_of(seq, which):
    """A sequence into the two rows: each poster on the row whose edge is nearest the column."""
    cur, rows = [START, START], ([], [])
    for n in seq:
        r = cur.index(min(cur))
        rows[r].append(n)
        cur[r] += round(ROWS[which][r][1] * ASPECT[n]) + GAP
    return rows


def side(which, top, low):
    placed = []
    for r, seq in enumerate((top, low)):
        y, h = ROWS[which][r]
        o = START
        for n in seq:
            w = round(h * ASPECT[n])
            placed.append((o, r, n, y, h, w))
            o += w + GAP
    placed.sort(key=lambda p: (p[0], p[1]))  # the further out, the later it is pasted: on top
    turns = WOBBLE if which == 'l' else WOBBLE[::-1]
    return [(n, o, y, h, w, turns[i % len(turns)]) for i, (o, r, n, y, h, w) in enumerate(placed)]


# Mockup number: left margin's top and lower row, right margin's, each from the column outward
WALLS = {
    1: (*rows_of([3, 62, 66, 18, 59, 7, 63, 48, 61, 17, 13, 49, 9, 33, 51, 16, 1, 8], 'l'), *rows_of([15, 64, 10, 65, 4, 46, 30, 11, 55, 47, 35, 56, 5, 19, 6, 2, 14, 43, 34, 22], 'r')),
    2: ([3, 18, 48, 17, 9, 16], [59, 63, 61, 13, 33, 51], [15, 30, 11, 55, 56, 19], [62, 65, 46, 10, 5, 6]),      # the strongest comments first
    3: ([10, 4, 17, 3, 18, 13], [62, 65, 34, 8, 59, 51], [48, 66, 55, 30, 7, 15, 49], [64, 63, 61, 2, 14, 33]),        # paper on top, black prints below
    4: ([65, 61, 59, 34, 6, 51], [7, 30, 18, 14, 8, 2], [64, 63, 62, 33, 49, 19], [55, 10, 48, 3, 15, 13]),        # black prints on top, paper below
    5: ([48, 61, 4, 59, 17, 9], [65, 30, 34, 13, 51, 8], [55, 62, 10, 63, 3, 49], [64, 18, 15, 46, 2, 11]),        # paper and black in turn
    6: ([4, 17, 30, 3, 55], [64, 59, 7, 63, 47], [10, 18, 35, 15, 11], [65, 61, 48, 46, 62]),                      # only rank 1s
    7: ([13, 18, 5, 3, 6, 43], [63, 9, 64, 2, 48, 16], [49, 66, 4, 56, 10, 33, 19], [61, 65, 7, 30, 15, 51]),          # some rank 2s up front
    8: ([18, 66, 59, 48, 3, 8, 13], [7, 14, 63, 2, 16, 33], [1, 15, 56, 10, 30, 5], [17, 62, 53, 61, 55, 6]),          # women forward
    9: ([10, 59, 30, 15, 33, 6], [61, 13, 63, 62, 47, 5], [55, 43, 49, 3, 35, 9], [34, 64, 65, 11, 46, 51]),       # soldiers forward
    10: ([30, 48, 3, 49, 5, 51], [47, 55, 59, 13, 63, 6], [15, 56, 35, 4, 17, 9], [46, 11, 62, 7, 18, 33]),        # slogans first
    11: ([59, 18, 13, 3, 17, 16], [63, 64, 34, 7, 51, 8], [10, 66, 61, 43, 53, 48, 19], [62, 65, 30, 2, 4, 33]),       # figures first
    12: ([3, 66, 48, 18, 13, 49, 6], [7, 47, 2, 9, 19, 16], [15, 10, 30, 55, 56, 5], [4, 11, 17, 46, 14, 8]),          # no black prints
    15: ([7, 48, 17, 18, 30, 5], [59, 46, 4, 13, 61, 9], [55, 66, 10, 15, 3, 56, 16], [47, 62, 14, 63, 49, 2]),        # languages evenly mixed
    16: ([1, 3, 59, 18, 13, 9], [14, 62, 48, 7, 33, 19], [53, 15, 10, 30, 17, 6], [61, 4, 63, 8, 55, 49]),         # the ones liked at rank 3
}

used = sorted({n for rows in WALLS.values() for row in rows for n in row})
assert set(used) == set(POSTER), set(used) ^ set(POSTER)
ids = [POSTER[n] for n in used]
at = {n: i for i, n in enumerate(used)}
walls = []
for v, (lt, ll, rt, rl) in WALLS.items():
    assert len(lt + ll + rt + rl) == len(set(lt + ll + rt + rl)), v
    walls.append({'v': v, 'left': [[at[n], *rest] for n, *rest in side('l', lt, ll)], 'right': [[at[n], *rest] for n, *rest in side('r', rt, rl)]})
write_text(OUT, json.dumps({'ids': ids, 'walls': walls}, ensure_ascii=False, separators=(',', ':')) + '\n')
print(len(walls), 'walls,', len(ids), 'posters,', OUT.stat().st_size, 'bytes')
