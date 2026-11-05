"""The wartime posters as prints for the home band's margins. The band's own: each poster in grey with its paper, for the
wall of components/BandPosters.tsx (public/plakati-band, committed). The local mockup's (/predlog/plakati, public/plakati-mockup):
the same larger, each poster's ink lifted off its paper into an alpha channel, whatever the paper's stain, so that the page
can print it in any colour, and details cut from them for the mosaic and the lettering.

python scripts/make_band_posters.py   (reads the local plakati/: the user's copies, commons/ and thumbs-960/)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
PLAKATI = ROOT / 'plakati'
BAND_OUT = ROOT / 'website' / 'public' / 'plakati-band'
OUT = ROOT / 'website' / 'public' / 'plakati-mockup'
DATA = ROOT / 'website' / 'app' / '(sr)' / 'predlog' / 'plakati' / 'prints.json'
THUMBS = PLAKATI / 'thumbs-960'
HEIGHT = 520      # the mockup's print at twice the largest size it is drawn
BAND_HEIGHT = 400  # the band's, likewise

# The posters on the band: scripts/make_band_walls.py places them. A print of any other poster is removed from the band's folder.
BAND = ['zena-u-borbi', 'miting-zena', 'ni-zrno', 'narod', 'zima', 'bratstvom', 'u-borbu', 'slovenske-zene', 'zgrabimo', 'svi-u-borbu', 'srbija',
        'svi-na-front', 'osmi-mart', 'za-zadnji-udar', 'gradi-zemunice', 'dalmatinka', 'partizanka', 'ja-se-borim', 'zena-kroz-borbu',
        'svi-u-partizane', 'titova-armada', 'ranjenici', 'nov-izdajalce', 'ujedinjeni', 'smrt-fasizmu', 'za-slobodu-hrvatske', 'vse-za-vojsko', 'daruj-zbiraj',
        'ustanak-crna-gora', 'hocemo-trst', 'po-cici-i-zimi', 'slovenska-zena', 'vstaja', 'na-bunker', 'domovi-sume', 'kroz-sumu', 'uz-prugu', 'kolona-v-snegu']
BRIGHTER = {'domovi-sume'}  # the user's wish: this linocut's blacks lifted a little
NOVI = PLAKATI / 'novi' / 'thumbs'  # the small copies of 2026-11-05 (500 px wide): enough for a print 400 px high

# id: (file, [left, top, right, bottom] of the poster inside the scan, language, a woman on it, title, author, year)
POSTERS = {
    'ni-zrno': (PLAKATI / 'ni-zrno-zita-okupatoru-mraz-1943.jpg', (.07, .08, .93, .91), 'sh', False, 'Ni zrno žita okupatoru', 'Franjo Mraz', '1943'),
    'partizanka': (PLAKATI / 'partizanka-pirnat-1944.jpg', None, '', True, 'Partizanka', 'Nikolaj Pirnat', '1944'),
    'u-borbu': (PLAKATI / 'u-borbu-protiv-okupatora-vuksanovic-1941.jpg', None, 'sr', True, 'У борбу против окупатора', 'Dragoljub Vuksanović', '1941'),
    'ja-se-borim': (PLAKATI / 'commons' / 'ja-se-borim-a-ti.jpg', None, 'sr', False, 'Ја се борим, а ти?', 'Dragoljub Vuksanović', '1941'),
    'dan-zena': (PLAKATI / 'commons' / 'dan-zena.jpg', None, 'sr', True, 'Дан жена', '', '1944'),
    'dalmatinka': (PLAKATI / 'commons' / 'dalmatinka-u-borbi.jpg', None, 'sh', True, 'Dalmatinka u borbi', '', '1944'),
    'dosla-je': (PLAKATI / 'commons' / 'dosla-je-bratska-crvena-armija.png', None, 'sh', False, 'Došla je bratska Crvena armija', 'Zlatko Prica', '1944'),
    'gradi-zemunice': (PLAKATI / 'commons' / 'gradi-zemunice.jpg', None, 'sh', False, 'Gradi zemunice', 'Franjo Mraz', '1943'),
    'svi-na-front': (PLAKATI / 'commons' / 'vasilij-petrovic-antipov-svi-na-front-sve-za-front.jpg', None, 'sh', False, 'Svi na front, sve za front!', 'Vasilij Petrović-Antipov', '1944'),
    'rujan': (PLAKATI / 'commons' / '15-rujan-je-zadnji-rok.jpg', (0, 0, 1, .72), 'sh', False, '15. rujan je zadnji rok', 'Ivan Lovrenčić', '1944'),
    'bratstvom': (PLAKATI / 'commons' / 'bratstvom-i-jedinstvom-omladina-izgradjuje-svoj-novi-zivot.jpg', None, 'sh', False, 'Bratstvom i jedinstvom', 'Vlado Kristl', '1944'),
    'muslimanska': (PLAKATI / 'commons' / 'godisnjica-16-muslimanske-brigade.jpg', None, 'sh', False, 'Godišnjica XVI muslimanske brigade', 'Ismet Mujezinović', '1944'),
    'zena-u-borbi': (THUMBS / 'zena-u-borbi.jpg', None, 'sh', True, 'Žena u borbi', '', '1943'),
    'zena-kroz-borbu': (THUMBS / 'zena-kroz-borbu.jpg', None, 'sh', True, 'Žena kroz borbu', '', '1941-45'),
    'zene-steber': (THUMBS / 'zene-steber.jpg', None, 'sl', True, 'Žene steber našega zaledja', '', '1945'),
    'slovenske-zene': (THUMBS / 'slovenske-zene.jpg', None, 'sl', True, 'Slovenske žene nadomestimo', 'Vito Globočnik', '1945'),
    'miting-zena': (THUMBS / 'miting-zena.jpg', None, 'sr', True, 'Први антифашистички митинг жена Србије', 'Đorđe Andrejević-Kun', '1945'),
    'osmi-mart': (THUMBS / 'osmi-mart.jpg', None, 'sr', True, 'Живео 8. март', 'Ismet Mujezinović', '1945'),
    'titova-armada': (THUMBS / 'titova-armada.jpg', None, 'sl', False, 'Titova armada na pohodu v svobodo', 'Janez Vidic', '1944'),
    'zima': (THUMBS / 'zima.jpg', None, 'sl', False, 'Zima! Vsi vse za naše borce', 'Ivan Seljak', '1944'),
    'narod': (THUMBS / 'narod-si-bo-pisal.jpg', None, 'sl', False, 'Narod si bo pisal svobodo sam', 'France Mihelič', '1943'),
    'proletarca': (THUMBS / 'proletarca.jpg', None, '', False, 'Proletarca na jurišu', 'Nikolaj Pirnat', '1944'),
    'zgrabimo': (THUMBS / 'zgrabimo.jpg', None, 'sl', False, 'Zgrabimo za orožje vsi', 'Nikolaj Pirnat', '1941-45'),
    'za-zadnji-udar': (THUMBS / 'za-zadnji-udar.jpg', None, 'sl', False, 'Za zadnji udar vsi - vse!', 'Nikolaj Pirnat', '1945'),
    'svi-u-novj': (THUMBS / 'svi-u-novj.jpg', None, 'sh', False, 'Svi u NOVJ', 'Andro Lušićić', '1943'),
    'svi-u-partizane': (THUMBS / 'svi-u-partizane.png', None, 'sh', False, 'Svi u partizane', 'Andro Lušićić', '1943'),
    'svi-u-borbu': (THUMBS / 'svi-u-borbu.jpg', None, 'sh', False, 'Svi u borbu protiv NDH', 'Edo Murtić', '1944'),
    'pazi': (THUMBS / 'pazi-petokolonas.jpg', None, 'sr', False, 'Пази, петоколонаш вреба', 'Pivo Karamatijević, Bora Baruh', '1941'),
    'srbija': (THUMBS / 'srbija.jpg', None, 'sr', False, 'Србија се умирит не може', '', '1941'),
    'ranjenici': (PLAKATI / 'ranjenici-jakac-1944.jpg', None, '', False, 'Ranjenici', 'Božidar Jakac', '1944'),
    'nov-izdajalce': (PLAKATI / 'commons' / 'narodno-osvobodilna-vojska-unicuje-izdajalce.jpg', None, 'sl', False, 'Narodno osvobodilna vojska uničuje izdajalce', 'Janez Vidic', '1944'),
    'ujedinjeni': (NOVI / '04.img', None, 'sh', False, 'Ujedinjeni', '', '1944'),
    'smrt-fasizmu': (NOVI / '10.img', None, 'sr', False, 'Смрт фашизму, слобода народу', '', '1941'),
    'za-slobodu-hrvatske': (NOVI / '12.img', None, 'sh', False, 'Svi u borbu za slobodu Hrvatske!', '', '1944'),
    'vse-za-vojsko': (NOVI / '13.img', None, 'sl', True, 'Vse za našo vojsko', 'Janez Vidic', '1941-45'),
    'daruj-zbiraj': (NOVI / '14.img', None, 'sl', False, 'Daruj, zbiraj, vse za našo vojsko!', '', '1944'),
    'ustanak-crna-gora': (NOVI / '16.img', None, '', False, 'Uprising Day in Montenegro', 'Pivo Karamatijević', '1943'),
    'hocemo-trst': (NOVI / '18.img', None, 'sl', True, 'Hočemo Trst v Titovi Jugoslaviji', 'Janez Vidic', '1944'),
    'po-cici-i-zimi': (NOVI / '24.img', None, 'sr', False, 'По цичи и зими наши борци стоје на стражи', '', '1941-45'),
    'slovenska-zena': (NOVI / '26.img', None, 'sl', True, 'Slovenska žena si je sama priborila volilno pravico!', '', '1945'),
    'vstaja': (NOVI / '39.img', None, '', False, 'Vstaja slovenskega naroda', 'Nikolaj Pirnat', '1944'),
    'na-bunker': (NOVI / '33.img', None, '', False, 'Na bunker', 'Nikolaj Pirnat', '1944'),
    'domovi-sume': (NOVI / '43.img', None, '', False, 'Iz ciklusa Domovi, šume, tamnice', 'Nikolaj Pirnat', '1944'),
    'kroz-sumu': (NOVI / '38.img', None, '', False, 'Kroz šumu', 'Branko Šotra', '1943'),
    'uz-prugu': (NOVI / '34.img', None, '', False, 'Uz prugu', 'Nande Vidmar', '1943'),
    'kolona-v-snegu': (NOVI / '36.img', None, '', False, 'Kolona v snegu', 'France Mihelič', '1944'),
}

# Details cut from the posters: id, poster, [left, top, right, bottom]: the lettering in each language, and figures
DETAILS = {
    'd-ni-zrno': ('ni-zrno', (.12, .045, .86, .145)),
    'd-okupatoru': ('ni-zrno', (.22, .70, .92, .88)),
    'd-zena': ('zena-u-borbi', (.03, .48, .98, .84)),
    'd-uborbi': ('dalmatinka', (.03, .68, .97, .96)),
    'd-dalmatinka': ('dalmatinka', (.03, .03, .97, .13)),
    'd-dan-zena': ('dan-zena', (.08, .82, .92, .97)),
    'd-8-mart': ('dan-zena', (.62, .02, .98, .12)),
    'd-u-borbu': ('u-borbu', (.34, .68, 1, 1)),
    'd-ja-se': ('ja-se-borim', (.02, .01, .98, .15)),
    'd-svi-u-partizane': ('svi-u-partizane', (.04, .02, .96, .14)),
    'd-bratstvom': ('bratstvom', (.28, .01, .99, .32)),
    'd-zima': ('zima', (.05, .02, .95, .42)),
    'd-vsi': ('zima', (.05, .52, .95, .92)),
    'd-za-zadnji': ('za-zadnji-udar', (.05, .68, .95, .97)),
    'd-narod': ('narod', (.03, .02, .97, .2)),
    'd-srbija': ('srbija', (.03, .05, .97, .95)),
    'd-pazi': ('pazi', (.02, .55, .98, 1)),
    'd-slovenske': ('slovenske-zene', (.02, .01, .75, .22)),
    'd-steber': ('zene-steber', (.52, .50, .98, .76)),
    'd-zene': ('zene-steber', (.05, .0, .5, .12)),
    'd-mraz-figure': ('ni-zrno', (.32, .28, .78, .72)),
    'd-partizanka-glava': ('partizanka', (.22, .12, .62, .52)),
    'd-zastava': ('partizanka', (.55, .0, 1, .5)),
    'd-majka': ('u-borbu', (.0, .0, .72, .6)),
    'd-zena-kroz': ('zena-kroz-borbu', (.1, .1, .8, .75)),
    'd-dan-zena-lica': ('dan-zena', (.2, .02, .85, .55)),
    'd-dosla': ('dosla-je', (.2, .25, .95, .65)),
    'd-proleter': ('proletarca', (.15, .1, .85, .7)),
    'd-muslimanska': ('muslimanska', (.2, .25, .78, .8)),
    'd-gradi': ('gradi-zemunice', (.05, .28, .95, .75)),
}


def to_gray(path):
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA', 'PA') or 'transparency' in im.info:  # transparent paper is white paper
        im = im.convert('RGBA')
        white = Image.new('RGBA', im.size, 'white')
        white.alpha_composite(im)
        im = white
    return im.convert('L')


def cut(im, box):
    if not box:
        return im
    w, h = im.size
    return im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))


def ink_alpha(a):
    """How much ink stands on each point: the paper's own tone, stain and all, taken away. What the paper's grain leaves
    under a fifth of full ink goes, and the solid blacks are full."""
    k = max(9, min(a.shape) // 14)
    paper = ndi.grey_closing(a[::2, ::2], size=(k, k))
    paper = ndi.gaussian_filter(paper, k / 2)
    paper = ndi.zoom(paper, (a.shape[0] / paper.shape[0], a.shape[1] / paper.shape[1]), order=1)
    black = np.percentile(a, 1)
    ink = (paper - a) / np.maximum(paper - black, 40)
    ink = np.clip((ink - .16) / (.82 - .16), 0, 1)
    return ink ** .85


def save_ink(im, name, height=HEIGHT):
    if im.height != height:
        im = im.resize((max(1, round(im.width * height / im.height)), height), Image.LANCZOS)
    a = np.asarray(im, float)
    alpha = np.uint8(ink_alpha(a) * 255 + .5)
    rgba = np.zeros((*alpha.shape, 4), np.uint8)
    rgba[..., 3] = alpha
    Image.fromarray(rgba, 'RGBA').save(OUT / f'{name}.webp', quality=62, alpha_quality=62, method=6)
    return im.width, im.height


OUT.mkdir(parents=True, exist_ok=True)
BAND_OUT.mkdir(parents=True, exist_ok=True)
prints, details, grays = {}, {}, {}
missing = []
for pid, (path, box, lang, woman, title, author, year) in POSTERS.items():
    if not path.exists():
        missing.append(pid)
        continue
    g = cut(to_gray(path), box)
    grays[pid] = g
    w, h = save_ink(g, pid)
    small = g.resize((max(1, round(g.width * HEIGHT / g.height)), HEIGHT), Image.LANCZOS)
    small.save(OUT / f'{pid}-papir.webp', quality=58, method=6)
    if pid in BAND:
        printed = g.resize((max(1, round(g.width * BAND_HEIGHT / g.height)), BAND_HEIGHT), Image.LANCZOS)
        if pid in BRIGHTER:
            lifted = .075 + (1 - .075) * (np.asarray(printed, float) / 255) ** .85
            printed = Image.fromarray(np.uint8(lifted * 255 + .5))
        printed.save(BAND_OUT / f'{pid}.webp', quality=58, method=6)
    prints[pid] = {'w': w, 'h': h, 'lang': lang, 'woman': woman, 'title': title, 'author': author, 'year': year}
for did, (pid, box) in DETAILS.items():
    if pid not in grays:
        continue
    g = cut(grays[pid], box)
    height = min(320, max(120, g.height))
    w, h = save_ink(g, did, height)
    details[did] = {'w': w, 'h': h, 'from': pid}
DATA.parent.mkdir(parents=True, exist_ok=True)
DATA.write_text(json.dumps({'prints': prints, 'details': details}, ensure_ascii=False, indent=1), encoding='utf-8')
assert not missing, missing  # else the walls would point at prints that aren't there
for old in BAND_OUT.glob('*.webp'):
    if old.stem not in BAND:
        old.unlink()
total = sum(p.stat().st_size for p in OUT.iterdir())
band = sum(p.stat().st_size for p in BAND_OUT.iterdir())
print(len(prints), 'prints,', len(details), 'details,', round(total / 1024), 'KB; the band:', len(list(BAND_OUT.iterdir())), 'files,', round(band / 1024), 'KB; missing:', missing)
