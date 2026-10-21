"""Title-card thumbnails for Sources entries whose scans are in the Poreklo library, which only its members can open (as
knjazevac-pomenik.jpg): 843 x 1193, beige, Georgia, the title's lines, a red rule, the author, place and year at the
foot. Usage: python scripts/make_title_cards.py [key ...] (website/public/images/pdf-thumbs/<key>.jpg)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / 'website' / 'public' / 'images' / 'pdf-thumbs'
W, H = 843, 1193
BG, INK, RED = (238, 230, 218), (40, 32, 30), (160, 40, 30)
FONT = 'C:/Windows/Fonts/georgia.ttf'

CARDS = {
    'ostrvica': (['ОСТРВИЦА', 'СЕЛО ОСТРВИЦА', 'КОД ГОСПИЋА'], ['Јован Д. Панџић'], 'Београд\n2003.'),
    'divoselo': (['ДИВОСЕЛО,', 'ЧИТЛУК И ОРНИЦЕ', 'У ВРЕМЕНУ', 'И ТРАЈАЊУ'], [], ''),
    'mogoric': (['МОГОРИЋ', '(ЛИКА)'], [], ''),
    'vrebac': (['ВРЕБАЦ', 'ЗАВОЂЕ', 'ПАВЛОВАЦ', 'Корени вековног трајања'], [], ''),
    'licko-petrovo-selo': (['DA SE NE PONOVI', 'Ratna kronika ranije', 'općine', 'LIČKO PETROVO SELO'], ['Miloš Pužić'], '1985.'),
    'bosansko-grahovo': (['БОСАНСКО ГРАХОВО', 'У НОР-у', '1941–1945'], [], ''),
    'staromajdansko': (['STAROMAJDANSKO', 'PODRUČJE U NOB', '1941–1945. godine'], [], ''),
    'otocac-brinje': (['OTOČAC I BRINJE', 'U NOB', '1941–1945'], [], ''),
    'han-pijesak': (['ХАН ПИЈЕСАК', 'простор – вријеме – људи'], [], ''),
    'skakavac': (['СКАКАВАЦ', 'И СКАКАВЧАНИ', 'код Петровца'], [], ''),
    'zitoradje': (['ЖИТОРАЂЕ', 'кроз историју'], [], ''),
    'brod-crna-trava': (['БРОД', 'село код Црне Траве'], [], ''),
    'revolucionarno-grahovo': (['РЕВОЛУЦИОНАРНО', 'ГРАХОВО'], [], ''),
    'kolasin': (['КОЛАШИН'], [], ''),
    'bozice': (['ВАСОЈЕВИЋКО СЕЛО', 'БОЖИЋЕ', 'И БОЖИЋАНИ'], ['Владимир Радованов Дубак'], ''),
}


def card(key, title, authors, foot):
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    sizes = [62 if i == 0 or line.isupper() and len(line) < 14 else 42 for i, line in enumerate(title)]
    fonts = [ImageFont.truetype(FONT, s) for s in sizes]
    y = 330
    for line, f in zip(title, fonts):
        while d.textlength(line, font=f) > W - 120:
            f = ImageFont.truetype(FONT, f.size - 2)
        d.text(((W - d.textlength(line, font=f)) / 2, y), line, font=f, fill=INK)
        y += f.size + 30
    y += 20
    d.line([(W / 2 - 90, y), (W / 2 + 90, y)], fill=RED, width=4)
    y += 50
    fa = ImageFont.truetype(FONT, 36)
    for a in authors:
        d.text(((W - d.textlength(a, font=fa)) / 2, y), a, font=fa, fill=INK)
        y += 50
    ff = ImageFont.truetype(FONT, 32)
    fy = H - 90 - 45 * foot.count('\n')
    for line in foot.split('\n'):
        if line:
            d.text(((W - d.textlength(line, font=ff)) / 2, fy), line, font=ff, fill=INK)
        fy += 45
    img.save(OUT / f'{key}.jpg', quality=88)
    print('wrote', key)


if __name__ == '__main__':
    for key in sys.argv[1:] or CARDS:
        card(key, *CARDS[key])
