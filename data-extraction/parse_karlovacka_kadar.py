"""
Parser: Karlovačka udarna brigada (brigade code 94) — its command, a second list.

Source: Josip Lulik Pepo, Đuro Zatezalo, *Karlovačka udarna brigada* (znaci.org 00003/546, its PDF pp. 370-377, book pp.
        371-378)  →  website/public/pdfs/karlovacka-kadar.pdf: "Pregled komandnog kadra Karlovačke udarne brigade",
        made from the archives, SUBNOR's records and the survivors' memories. The staff of the brigade and of its four
        battalions, numbered under each duty, a name in capitals, the days of the post and often what became of him:
    1. FRANJO MOLEK — od 5. 3. do 30. 6. 1944, ranjen 30. 6. kod Petrovine na Žumberku i umro 2. 7. 1944.
        then, by name only, each battalion's company and platoon commanders, commissars and delegates, and the
        companies, platoons and rear units of the brigade, a duty and its men after a dash or under it:
    Komandiri četa
    Vlado Bartolin, Artur Blažević, Franjo Borić, ...
A word in capitals lost its carons ("KATUSlC" = Katušić); a man named in capitals by three words is his given name,
his surname and what he was called, in the order the corpus tells ("RAFKO RAFAEL TABOR", "MILIVOJ GABERŠNIK PUPO"). A
man in several posts is one record with each; his box is around his name at each post on his first post's page. The
lists of the formation and the fallen are the unit's first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of
from parse_6_vojvodjanska_stabovi import respelled
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/karlovacka-kadar.pdf'
UNIT = 'website/public/karlovacka-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_546.pdf'   # znaci.org 00003/546.pdf
PAGES = range(370, 378)
TITLE = 'Pregled komandnog kadra Karlovačke udarne brigade'
SECTIONS = {'stab brigade': ('Štab brigade', 'brigade'), 'štab brigade': ('Štab brigade', 'brigade'),
            'prvi bataljon': ('1. bataljon', '1. bataljona'), 'drugi bataljon': ('2. bataljon', '2. bataljona'),
            'treći bataljon': ('3. bataljon', '3. bataljona'), 'četvrti bataljon': ('4. bataljon', '4. bataljona'),
            'četa za vezu brigade': ('četa za vezu', 'čete za vezu brigade'),
            'prateća četa brigade': ('prateća četa', 'prateće čete brigade'),
            'inžinjerijska četa brigade': ('inžinjerijska četa', 'inžinjerijske čete brigade'),
            'izviđački vod brigade': ('izviđački vod', 'izviđačkog voda brigade'),
            'sanitetski vod': ('sanitetski vod', 'sanitetskog voda brigade'),
            'minerski vod brigade': ('minerski vod', 'minerskog voda brigade'),
            'pozadina brigade': ('pozadina', 'brigade')}
# a duty heading, its first words in small letters -> the duty in the singular (the unit's words follow it)
DUTIES = [('komandanti', 'komandant'), ('politkomesari', 'politički komesar'), ('pomoćnici komesara četa', 'pomoćnik komesara čete'),
          ('pomoćnici komesara čete', 'pomoćnik komesara'), ('pomoćnik komesara čete', 'pomoćnik komesara'),
          ('pomoćnici komesara', 'pomoćnik komesara'), ('načelnici štaba', 'načelnik štaba'),
          ('operativni oficir', 'operativni oficir'), ('obavještajni oficir', 'obavještajni oficir'),
          ('informativni oficir', 'informativni oficir'), ('intendant', 'intendant'), ('referent', 'referent saniteta'),
          ('opunomoćenik ozn-e', 'opunomoćenik OZN-e'), ('tehničari', 'tehničar u kancelariji štaba'),
          ('komesari četa', 'komesar čete'), ('komesari čete', 'komesar'), ('komesari bataljona', 'komesar'),
          ('rukovodi', 'rukovodilac SKOJ-a'), ('komandiri četa', 'komandir čete'), ('komandiri čete', 'komandir'),
          ('komandiri vod', 'komandir voda'), ('politdelegati', 'politički delegat voda'),
          ('komandir prateće čete', 'komandir'), ('komandiri provijant komore', 'komandir provijant komore'),
          ('komesar provijant komore', 'komesar provijant komore'), ('komandir bojne komore', 'komandir bojne komore'),
          ('komesar bojne komore', 'komesar bojne komore'), ('kuriri', 'kurir pri štabu'), ('komandiri', 'komandir')]
FIX = {'Mati ja': 'Matija', 'Po • dvorac': 'Podvorac', 'Ka tana': 'Katana', 'Nikolu': 'Nikola', 'Simun': 'Šimun',
       'Zivan': 'Živan', 'Zivić': 'Živić', 'Duro': 'Đuro', 'Cavlović': 'Čavlović', 'Zeljeznjak': 'Željeznjak',
       'Sepelj': 'Šepelj', 'Seketa': 'Šeketa', 'Sebalj': 'Šebalj', 'Spehar': 'Špehar', 'Stupnjanac': 'Stupnjanac'}
CAPS_FIX = {'5KALJAC': 'ŠKALJAC', 'BORTiS': 'BORIS', 'GAŠPARiOVlC': 'GAŠPAROVIĆ', 'PEĆANie': 'PEČANIĆ',
            'KRCEVSK1': 'KRČEVSKI', 'BENilC': 'BENIĆ', 'RU2A': 'RUŽA', 'PRUNES': 'PRUNER', 'STEINFL': 'STEINFEL',
            'ZUNAC': 'ŽUNAC', 'ZUNlC': 'ŽUNIĆ', 'BALAS': 'BALAŠ', 'BLAZ': 'BLAŽ', 'KRCEVSKI': 'KRČEVSKI',
            'KATUSIN': 'KATUŠIN'}
# the print's slips in the days, read from the page
DAYS = {'9. U. 1944': '9. 11. 1944', '9. 1,1. 1944': '9. 11. 1944', '2. 4. 11945': '2. 4. 1945', 'do 26, 10.': 'do 26. 10.'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in PAGES:
        w.add_page(r.pages[i - 1])
    with open(PDF, 'wb') as f:
        w.write(f)


def duty_of(label: str) -> str:
    low = re.sub(r'\s+', ' ', label).strip().lower()
    return next(d for p, d in DUTIES if low.startswith(p))


def is_duty(t: str) -> bool:
    low = t.lower()
    return any(low.startswith(p) for p, _ in DUTIES) and not re.search(r',', t.split('—')[0])


def caps_name(words: list[str]) -> tuple[str, str, str]:
    """['RAFKO', 'RAFAEL', 'TABOR'] -> ('Rafael', 'Tabor', 'Rafko')."""
    words = [CAPS_FIX.get(w, w) for w in words]
    joined = []
    for w in words:                                                      # "BELA VIC": a surname the OCR spaced
        if joined and len(w) <= 3 and w.isupper() and k8.known(respelled(joined[-1] + w, 'last_name')):
            joined[-1] += w
        else:
            joined.append(w)
    names = [respelled(w, 'first_name', 'last_name') for w in joined]
    if len(names) == 2:
        return names[0], names[1], ''
    if names[:2] == ['Georgije', 'Juraj']:
        return 'Georgije Juraj', names[2], ''
    last = max(names, key=lambda n: k8.known(n, 'last_name') - 3 * k8.known(n, 'first_name'))
    rest = [n for n in names if n is not last]
    given = max(rest, key=lambda n: k8.known(n, 'first_name'))
    nick = ' '.join(n for n in rest if n is not given)
    return given, last, nick


def title_names(words: list[dict]) -> list[tuple]:
    """The run of 'Given Surname' after a duty -> [(given, surname, nick, father, words)]."""
    toks = []
    for w in words:
        t = w['text']
        if toks and toks[-1][0].endswith('-') and toks[-1][0][:-1].isalpha():
            toks[-1] = (toks[-1][0][:-1] + t, toks[-1][1] + [w])         # "Dragiče-" / "vić"
        else:
            toks.append((t, [w]))
    text = ' '.join(t for t, _ in toks)
    for a, b in FIX.items():
        if ' ' in a:
            text = text.replace(a, b)
    items, cur, wcur = [], [], []
    flat = [(t, ws) for t, ws in toks]
    # rebuild tokens after the spaced fixes: map by position is not needed, the boxes take each item's words
    i = 0
    while i < len(flat):
        t, ws = flat[i]
        pair = f"{t} {flat[i + 1][0].rstrip(',.;')}" if i + 1 < len(flat) else ''
        if pair in FIX:                                                  # "Mati ja", "Po • dvorac"
            t, ws, i = FIX[pair] + (flat[i + 1][0][-1] if flat[i + 1][0][-1] in ',.' else ''), ws + flat[i + 1][1], i + 1
        i += 1
        if t in ('i', '•'):
            if cur:
                items.append((cur, wcur))
            cur, wcur = [], []
            continue
        cur.append(t)
        wcur += ws
        if t.endswith((',', '.', ';')) and not re.fullmatch(r'[A-ZČĆŽŠĐ]\.', t):
            items.append((cur, wcur))
            cur, wcur = [], []
    if cur:
        items.append((cur, wcur))
    out = []
    for texts, ws in items:
        texts = [FIX.get(x.strip(',.;'), x.strip(',.;')) for x in texts]
        texts = [x for x in texts if x]
        father = next((x for x in texts if re.fullmatch(r'[A-ZČĆŽŠĐ]', x)), '')    # "Ivan F. Ivasić"
        texts = [x for x in texts if x != father]
        father = father + '.' if father else ''
        if not texts or not all(re.fullmatch(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+', x) for x in texts):
            if texts and not all(x.islower() or x[:1].isdigit() for x in texts):
                print(f'  not a name: {texts!r}')
            continue
        if texts[:2] == ['Georgije', 'Juraj']:
            out.append(('Georgije Juraj', texts[2], '', father, ws))
        elif len(texts) >= 2:
            out.append((texts[0], texts[1], ' '.join(texts[2:]), father, ws))
    return out


def tail_text(t: str) -> str:
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'(\w)- (\w)', r'\1\2', t)                                # "2um- berku"
    t = re.sub(r'\b2(?=[a-z])', 'Ž', t)                                  # "2umberku": the OCR's Ž
    t = re.sub(r'\bZumberk', 'Žumberk', t)
    for a, b in DAYS.items():
        t = t.replace(a, b)
    return t.replace(' ,', ' ').replace('  ', ' ').rstrip('.').strip()


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        rows = [r for n, page in enumerate(pdf.pages, 1)
                for r in rows_of([{**w, 'page': n} for w in viewer_words(page)])]
    unit, of, duty = 'Štab brigade', 'brigade', ''
    entries = []                                                         # [kind, unit, of, duty, words, tail]
    for r in rows:
        t = re.sub(r'\s+', ' ', ' '.join(w['text'] for w in r)).strip()
        low = t.lower()
        if t.startswith('NAPOMENA'):
            break
        if t.startswith(('Pregled komandnog', 'Karlovačke udarne')) or re.fullmatch(r'\d{3}', t):
            continue
        if low in SECTIONS:
            unit, of = SECTIONS[low]
            duty = ''
            continue
        m = re.match(r'^(\d+)\s*[.,]?\s+([A-ZČĆŽŠĐ0-9][A-ZČĆŽŠĐa-z0-9 ]*?)\s+[—-]+\s*(.*)$', t)
        n = re.match(r'^([A-ZČĆŽŠĐ]{2,}(?: [A-ZČĆŽŠĐ]{2,})+)\s+[—-]+\s+(.*)$', t)
        if m or n and duty:                                              # a numbered man in capitals, or one unnumbered
            name = (m or n).group(2 if m else 1)
            k = len(name.split()) + (1 if m else 0)
            entries.append(['caps', unit, of, duty, r[1 if m else 0:k], (m or n).group(3 if m else 2)])
            continue
        if is_duty(t):
            left, _, right = t.partition('—')
            duty = duty_of(left.strip() if right else t)
            if right:                                                    # "Komesari čete — Marija Babić, ..."
                k = len(left.split()) + 1
                rest = r[k:]
                if '—' in right:                                         # "— Josip Erdeljac — od 5. 3. 1944. ..."
                    nm, _, tl = right.partition('—')
                    j = len(nm.split())
                    entries.append(['title', unit, of, duty, rest[:j], tl])
                else:
                    entries.append(['title', unit, of, duty, rest, ''])
            continue
        if entries and (entries[-1][0] == 'caps' or entries[-1][5]) and \
                not re.search(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+ [A-ZČĆŽŠĐ][a-zčćžšđ]+,', t):
            entries[-1][5] += ' ' + t                                    # the numbered man's days and fate, run on
            continue
        if entries and entries[-1][0] == 'title' and entries[-1][3] == duty and entries[-1][1] == unit \
                and not entries[-1][5]:
            entries[-1][4] = entries[-1][4] + r
        else:
            entries.append(['title', unit, of, duty, list(r), ''])
    for kind, unit_, of_, duty_, ws, tail in entries:
        if of_.split()[0].endswith('og') and of_.split()[1] == 'voda' and duty_.endswith(' voda'):
            duty_ = duty_[:-5]                                           # the platoon's own: "komandir sanitetskog voda"
        post = duty_ if duty_.endswith(('štabu', 'brigade')) and of_ == 'brigade' else f'{duty_} {of_}'
        if duty_ == 'kurir pri štabu':
            post = 'kurir pri štabu brigade'
        tail = tail_text(tail)
        if kind == 'caps':
            given, last, nick = caps_name([w['text'] for w in ws])
            POSTS.append({'given': given, 'last': last, 'nick': nick, 'father': '', 'unit': unit_, 'page': ws[0]['page'],
                          'post': f'{post}, {tail}' if tail else post, 'words': ws})
            continue
        for given, last, nick, father, w in title_names(ws):
            POSTS.append({'given': respelled(given, 'first_name'), 'last': respelled(last, 'last_name'), 'nick': nick,
                          'father': father, 'unit': unit_, 'page': w[0]['page'],
                          'post': f'{post}, {tail}' if tail else post, 'words': w})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], p['father'], '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (k8.fold(p['last']), k8.fold(p['given']))
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['father'] and not man.get('middle_name'):
            man['middle_name'] = p['father']
        if p['post'] not in man['_posts']:
            man['_posts'].append(p['post'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            for line in rows_of(p['words']):                            # a name broken over two lines
                man['_rects'].append([round(min(w['x0'] for w in line), 1), round(min(w['top'] for w in line), 1),
                                      round(max(w['x1'] for w in line), 1), round(max(w['bottom'] for w in line), 1)])
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=94, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
