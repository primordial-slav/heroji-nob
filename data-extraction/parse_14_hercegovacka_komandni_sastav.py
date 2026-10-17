"""
Parser: 14. hercegovačka (omladinska) NOU brigada (brigade code 81) — its command, a second list.

Source: "Četrnaesta hercegovačka omladinska brigada" (znaci.org 00001/268_5.pdf, its pp. 29-37, book pp. 234-242,
        Prilog 4, before the lists on the site)  →  website/public/pdfs/14-hercegovacka-komandni-sastav.pdf:
        "Komandni sastav 14. hercegovačke (omladinske) brigade", the brigade staff, each battalion's staff, company
        commands, escort platoon and platoon commanders and delegates, two columns, a name a line under each duty,
        given name first, the days on the next line:
    Komandanti
      Radovan Sakotić
      (5. 9. 44—7. 5. 45)
A heading across the page ("Štab 2. bataljona") starts a staff for both columns below it, so a page is read band by
band, the left column before the right. A man in several posts is one record with each; his box is around his name
at each post on his first post's page. The carons the print lost come back where the corpus prints the name so. The
fighters and the fallen are the unit's first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/14-hercegovacka-komandni-sastav.pdf'
UNIT = 'website/public/14-hercegovacka-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_268_5.pdf'   # znaci.org 00001/268_5.pdf
FIRST_PAGE, LAST_PAGE = 29, 37
TITLE = 'Komandni sastav 14. hercegovačke (omladinske) brigade'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SPLIT = 185                                         # the columns: left < SPLIT <= right
HEAD = re.compile(r'^(Komandant|Komandir|Politički|Zamjenik|Zamjenici|Pomoćnik|Pomoćnici|Načelni|Operativni|Obavještajni|'
                  r'Intendant|Omladinski|Referent|Bolničar|Ekonom|Komesar|Opunomoćenik|Šef|Prateći|Komanda|Štab)')
DUTIES = [(r'^komandanti?$', 'komandant'), (r'^politički komesari?$', 'politički komesar'),
          (r'^zamjeni(k|ci) komandanta$', 'zamjenik komandanta'),
          (r'^pomoćni(k|ci) (političk\w+ )?komesara$', 'pomoćnik političkog komesara'),
          (r'^načelni(k|ci) štaba$', 'načelnik štaba'), (r'^operativni oficir', 'operativni oficir'),
          (r'^obavještajni oficir', 'obavještajni oficir'), (r'^intendanti?$', 'intendant'),
          (r'^zamjeni(k|ci) intendanta$', 'zamjenik intendanta'), (r'^načelnik veze$', 'načelnik veze'),
          (r'^načelnik saniteta$', 'načelnik saniteta'), (r'^omladinski rukovod', 'omladinski rukovodilac'),
          (r'^opunomoćenik ozne$', 'opunomoćenik OZN-e'), (r'^šef naoružanja$', 'šef naoružanja'),
          (r'^referenti? saniteta$', 'referent saniteta'), (r'^zamjeni(k|ci) referenta saniteta$', 'zamjenik referenta saniteta'),
          (r'^komandiri?$', 'komandir'), (r'^komesari?$', 'politički komesar'),
          (r'^zamjeni(k|ci) komandira$', 'zamjenik komandira'), (r'^bolničark[ae]$', 'bolničarka'), (r'^bolničari?$', 'bolničar'),
          (r'^ekonomi?$', 'ekonom'), (r'^politički delegati?$', 'politički delegat'),
          (r'^komandiri vodova', 'komandir voda'), (r'^politički delegati vodova', 'politički delegat voda')]
NAME_FIXES = {'Milićević Risto': 'Risto Milićević',   # the names printed surname first
              'Ibrulj Abdulrahman': 'Abdulrahman Ibrulj'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


ADDS = {('c', 'č'), ('c', 'ć'), ('s', 'š'), ('z', 'ž'), ('d', 'đ')}


def spelled(word: str, field: str) -> str:
    """The corpus's spelling where only carons the print lost differ ("Zivana" = Živana); the print's marks stay."""
    out = []
    for part in word.split('-'):
        best = k8.respell(part, field)
        ok = len(best) == len(part) and all(a == b or (a.lower(), b.lower()) in ADDS for a, b in zip(part, best))
        out.append(best if ok else part)
    return '-'.join(out)


def rows_of(words: list[dict]) -> list[list[dict]]:
    rows: list = []
    for w in sorted(words, key=lambda w: (round(w['top']), w['x0'])):
        if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def lines_in_order(pdf) -> list[tuple]:
    """('section', text) or ('line', words, page): the bands between the headings across the page, each band's left
    column before its right."""
    out = []
    for n, page in enumerate(pdf.pages, 1):
        words = [w for w in viewer_words(page, extra_attrs=['size']) if w['size'] >= 9]
        rows = rows_of(words)
        cuts = []
        for r in rows:
            t = ' '.join(w['text'] for w in r)
            if re.fullmatch(r'\d{3}', t) or n == 1 and r[0]['top'] < 130:
                for w in r:
                    words.remove(w)
            elif 100 < r[0]['x0'] < SPLIT and re.match(r'(Štab|Komanda|Prištapske) ', t):   # "Štab 2. bataljona", across
                cuts.append((r[0]['top'], t))
                for w in r:
                    words.remove(w)
        bands = [-1.0] + [c[0] for c in cuts] + [1e9]
        for i in range(len(bands) - 1):
            if i:
                out.append(('section', cuts[i - 1][1]))
            band = [w for w in words if bands[i] < w['top'] < bands[i + 1]]
            for col in ([w for w in band if w['x0'] < SPLIT], [w for w in band if w['x0'] >= SPLIT]):
                for r in rows_of(col):
                    out.append(('line', [{**w, 'page': n} for w in r]))
    return out


def duty_of(head: str) -> str:
    h = head.lower()
    d = next((d for p, d in DUTIES if re.search(p, h)), None)
    if d is None:
        raise ValueError(f'duty {head!r}')
    return d


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        lines = lines_in_order(pdf)
    unit, of, bat = 'Štab brigade', 'brigade', 0
    duty, duty_of_unit, head_x, person, broken = '', None, 0, None, ''
    for kind, *rest in lines:
        if kind == 'section':
            t = rest[0]
            m = re.match(r'Štab (\d)\. bataljona', t)
            if m:
                bat = int(m.group(1))
                unit, of = f'{bat}. bataljon', f'{bat}. bataljona'
            elif t.startswith(('Štab brigade', 'Prištapske jedinice')):
                unit, of = 'Štab brigade', 'brigade'
            duty, person = '', None
            continue
        ws = rest[0]
        t = ' '.join(w['text'] for w in ws)
        x = ws[0]['x0']
        if broken:                                                       # "Politički delegati vodova 2. bataljo-" / "na"
            t, broken = broken[:-1] + t, ''
        elif HEAD.match(t) and t.endswith('-'):
            broken = t
            continue
        m = re.match(r'^(Omladinski vod|Vod za vezu|Izviđački vod)$', t)  # the platoons at the brigade staff
        if m:
            unit, of = 'Štab brigade', {'Omladinski vod': 'omladinskog voda', 'Vod za vezu': 'voda za vezu',
                                        'Izviđački vod': 'izviđačkog voda'}[t]
            duty, person = '', None
            continue
        if t.startswith('('):                                            # the days, or a note on the duty
            note = t.strip('()')
            if person is not None:
                person['when'] = (person['when'] + ' ' if person['when'] else '') + note
            else:
                duty_note = note
                duty = f'{duty} ({duty_note})'
            continue
        if re.match(r'^\d\. bataljona$', t):                               # "Politički delegati vodova" / "1. bataljona"
            duty_of_unit = t
            continue
        m = re.match(r'^Komanda (\d)\. čete(?: (\d)\. bataljona)?$', t)
        if m:
            c, b = m.group(1), m.group(2) or bat
            unit, of = f'{c}. četa, {b}. bataljon', f'{c}. čete {b}. bataljona'
            duty, person = '', None
            continue
        m = re.match(r'^Prateći vod(?: (\d)\. bataljona)?$', t)
        if m:
            b = m.group(1) or bat
            unit, of = f'prateći vod, {b}. bataljon', f'pratećeg voda {b}. bataljona'
            duty, person = '', None
            continue
        if HEAD.match(t) and not re.search(r',\s*\d', t):
            m = re.search(r'(\d)\. bataljon\w*$', t)                      # "Komandiri vodova 1. bataljona", "u 4. bataljonu"
            duty_of_unit = f'{m.group(1)}. bataljona' if m else None
            duty = duty_of(re.sub(r'\s*(?:u )?\d\. bataljon\w*$', '', t))
            head_x, person = x, None
            continue
        # a man: "Milan - Miljo Milatović", "Zivana B. Vukoje", "Radovan Milošević, 2. vod 1. četa", "Cerovina"
        if re.fullmatch(r'[\d\W]+', t) or t == 'brigade':                # a sheet's mark, a heading's second line
            continue
        for a, b in NAME_FIXES.items():
            if t.startswith(a):
                t = b + t[len(a):]
        t = t.replace(' - ', '-').replace(' -', ' ')                     # "Vidosava -Popadić"
        aside = ''
        m = re.match(r'^(.*?)\s*\(([^)]*)\)$', t)                         # "Nataša Nada (Ruskinja)"
        if m:
            t, aside = m.group(1), m.group(2)
        name, _, place = t.partition(',')
        place = ', '.join(x for x in (place.strip(), aside) if x)
        m = re.match(rf'^(.*?)\s+(\d\.? vod.*|\d\. četa)$', name)         # "Slavko Nadaždin 3. četa"
        if m:
            name, place = m.group(1), m.group(2)
        parts = name.replace(' - ', '-').split()
        extra = []
        if len(parts) == 3 and not parts[1].endswith('.') and '-' not in parts[0]:
            parts, extra = parts[:2], parts[2:]                          # "Ziba Halilhodžić Monika": Monika another
        given, last = (parts[0], ' '.join(parts[1:])) if len(parts) > 1 else ('', parts[0])   # "Cerovina", alone
        nick = ''
        if '-' in given:
            given, nick = given.split('-', 1)
        initial = ''
        if re.fullmatch(r'[A-ZČĆŽŠĐ]\.', last.split()[0] if last else ''):
            initial, last = last.split()[0], ' '.join(last.split()[1:])
        where = duty_of_unit or of
        person = {'given': spelled(given, 'first_name') if given else '', 'last': spelled(last, 'last_name') if last else '',
                  'nick': nick, 'initial': initial, 'duty': f'{duty} {where}', 'place': place.strip().rstrip(' .'),
                  'when': '', 'unit': unit if not duty_of_unit else f'{duty_of_unit[0]}. bataljon',
                  'page': ws[0]['page'], 'words': ws}
        POSTS.append(person)
        for e in extra:
            POSTS.append({**person, 'given': '', 'last': spelled(e, 'first_name'), 'nick': '', 'initial': ''})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
    for p in POSTS:
        when = re.sub(r'[)"\s]+$', '', p['when']).rstrip('.')                # "od 18. 9. 44)"", "do 11. 5.."
        p['post'] = p['duty'] + (f", {p['place']}" if p['place'] else '') + (f", {when}" if when else '')
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], p['initial'], '')
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
        if p['post'] not in man['_posts']:
            man['_posts'].append(p['post'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = [w for w in p['words'] if not re.match(r'^\d', w['text'])] or p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
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
    run_parser(pdf_path=PDF, brigade_code=81, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
