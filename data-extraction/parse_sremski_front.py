"""
Sremski front (Dragoljub Tmušić, Dnevnik, Novi Sad 1987; znaci.org 00003/724) → website/public/pdfs/
sremski-front-poginuli.pdf: a book across units, its entries added to the records of the soldiers it describes (see
scripts/match_references.py).

"Spiskovi poginulih boraca po jedinicama", the fighters of the Yugoslav army killed on the Srem front (23 October 1944 -
13 April 1945), by division and brigade: a short history of each, then "Poginuli borci <the brigade>" and the names
run on in Cyrillic, numbered, surname, father's initial and given name, a nickname after a dash:
    1. Аћимовић М. Чедомир, 2. Аћимовић М. Станко, 3. Адамовић В. Бошко, 4. Адамовић Р. Милорад, ...
The Soviet units' lists that follow (the Red Army's regiments, in Russian, from "64. Streljački korpus" on the PDF's last
page) are not read.
So an entry has the name, the father's initial and the brigade (the site's unit where it is on the site: `units`); the
matcher weighs the unit and the father, and rules out a record that has him fall outside 1944-1945 (`death_years`).
Each name gets a box around its words (two when it runs on, pdf_rects).

Output: data-extraction/znaci/sremski-front-poginuli-entries.json (IDs 9014xxxxxx, in the book's order), in Latin.
Usage: python data-extraction/parse_sremski_front.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from pdf_coords import viewer_offset, viewer_words  # noqa: E402

PDF = 'sremski-front-poginuli.pdf'
OUT = HERE / 'znaci' / 'sremski-front-poginuli-entries.json'
PREFIX = '9014'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# words the OCR garbled past the rules, read from the page images (znaci re-typeset it in Cyrillic from the OCR, so
# "Сре1.ковић" stands there too: Srećković by the list's order and the corpus)
WORDS = {'Mij1S,': ['Mile,'], 'Sre1.ković': ['Srećković'], 'Vukadin,..1.35.': ['Vukadin,', '135.'],
         "Po'luzzi": ['Poluzzi']}
# names the OCR garbled, as the list's order, the brigade's own records and the corpus read them ("Bojat^ć Pero" is
# 5. krajiška's Bojanić Pero)
SPELLED = {'Š^pirić': 'Špirić', 'Jov^nović': 'Jovanović', 'J?remić': 'Jeremić', 'Bojat^ć': 'Bojanić',
           'BoiJKOVić': 'Bojković', 'Mi.pojković': 'Milojković', 'Jovanović " adovan': 'Jovanović Radovan',
           'Cvetićanin radomir': 'Cvetićanin Radomir', 'Sv tozar': 'Svetozar', 'Dobri la': 'Dobrila',
           'li Arsić': 'Arsić', 'Biljić te Branislav': 'Biljić Branislav', 'brekić': 'Brekić', 'Mi go': 'Migo'}
# a brigade by its number and its first adjective, in any case ("Deseta krajiška", "Treće krajiške proleterske") ->
# the site's unit
UNITS = {
    (1, 'proletersk'): 1, (3, 'krajišk'): 10, (13, 'proletersk'): 6, (8, 'crnogorsk'): 38, (2, 'proletersk'): 39,
    (4, 'crnogorsk'): 40, (4, 'krajišk'): 11, (1, 'ličk'): 2, (2, 'ličk'): 3, (3, 'ličk'): 118, (22, 'srpsk'): 74,
    (5, 'krajišk'): 12, (12, 'krajišk'): 54, (6, 'istočnobosansk'): 42, (2, 'krajišk'): 24, (15, 'majevičk'): 49,
    (4, 'srpsk'): 21, (21, 'srpsk'): 80, (8, 'srpsk'): 87, (10, 'srpsk'): 88, (12, 'srpsk'): 90, (1, 'vojvođansk'): 9,
    (2, 'vojvođansk'): 18, (4, 'vojvođansk'): 76, (3, 'vojvođansk'): 57, (5, 'vojvođansk'): 82, (6, 'vojvođansk'): 83,
    (7, 'vojvođansk'): 22, (3, 'makedonsk'): 51, (1, 'konjičk'): 92, (1, 'krajišk'): 123, (5, 'srpsk'): 127,
}
ORDINALS = [('jedanaest', 11), ('dvanaest', 12), ('trinaest', 13), ('četrnaest', 14), ('petnaest', 15),
            ('šesnaest', 16), ('sedamnaest', 17), ('osamnaest', 18), ('devetnaest', 19), ('prv', 1), ('drug', 2),
            ('treć', 3), ('četvrt', 4), ('pet', 5), ('šest', 6), ('sedm', 7), ('osm', 8), ('devet', 9), ('deset', 10)]
ADJECTIVES = ('proletersk', 'krajišk', 'ličk', 'srpsk', 'vojvođansk', 'crnogorsk', 'makedonsk', 'majevičk',
              'istočnobosansk', 'konjičk')
# a unit's heading: "Deseta krajiška narodnooslobodilačka udarna brigada", "Samostalne i prištapske jedinice ..."
HEADING = re.compile(rf'^[{U}][{L}]+(?: [{U}{L}()]+)*? (?:brigad[aei]|jedinice|divizij[ae]|bataljon|pukovnij[ae])'
                     rf'(?: [{U}{L}()]+)*(?: »[^«]+«)?$')                # no digits, no commas, no sentence


def ordinal(word: str) -> int | None:
    w = word.lower()
    return next((n for stem, n in ORDINALS if w.startswith(stem)), None)


def site_unit(label: str) -> int | None:
    words = label.split()
    n, i = None, 0
    if len(words) > 1 and words[0].lower().startswith(('dvadeset', 'trideset')):
        tens = 20 if words[0].lower().startswith('dvadeset') else 30
        n, i = tens + (ordinal(words[1]) or 0), 2
    elif words:
        n, i = ordinal(words[0]), 1
    adj = next((a for w in words[i:i + 2] for a in ADJECTIVES if w.lower().startswith(a)), None)
    return UNITS.get((n, adj)) if n and adj else None


def latin_layer(page) -> list[dict]:
    """A list the text layer holds twice (brigade »Italija«, PDF pp. 21-22: its Italian names in Latin, and the OCR's
    Cyrillic reading of them in the same place, which word extraction interleaves letter by letter, "AAćbee1tee" for
    "Abete"): the Latin run of the page's char stream as words in viewer coordinates; [] on the other pages"""
    runs, cur = [], []
    for c in page.chars:
        if re.match('[Ѐ-ӿ]', c['text']):
            if cur:
                runs.append(cur)
            cur = []
        else:
            cur.append(c)
    runs.append(cur)
    run = max(runs, key=lambda r: sum(c['text'].isalpha() for c in r))
    if sum(c['text'].isalpha() for c in run) < 200:
        return []
    while run and not run[0]['text'].isalnum():
        run = run[1:]                                                  # the hyphen ending the Cyrillic run: "Оо-1. Abete"
    dx, dy = viewer_offset(page)
    words, cur = [], []
    for c in run + [None]:
        if c is None or c['text'] == ' ' or (cur and (abs(c['top'] - cur[-1]['top']) > 2 or c['x0'] - cur[-1]['x1'] > 1.5)):
            if cur:
                words.append({'text': ''.join(x['text'] for x in cur).replace('\xad', '-'),     # "Giusep-" / "pe"
                              'x0': min(x['x0'] for x in cur) - dx, 'x1': max(x['x1'] for x in cur) - dx,
                              'top': min(x['top'] for x in cur) - dy, 'bottom': max(x['bottom'] for x in cur) - dy})
            cur = [c] if c is not None and c['text'] != ' ' else []
        else:
            cur.append(c)
    return [w for w in words if w['text']]


def halves(page, pno: int) -> list[list[dict]]:
    """The page's lines top to bottom (the words in viewer coordinates); a page holds one book page, one column."""
    words = viewer_words(page, keep_blank_chars=False)
    latin = latin_layer(page)
    if latin:
        # the Latin layer's lines in place of the words read from both layers at once
        spans = defaultdict(list)
        for w in latin:
            spans[round(w['top'])].append(w)
        lines = [(t, min(w['x0'] for w in ws), max(w['x1'] for w in ws)) for t, ws in spans.items()]
        words = [w for w in words if not any(abs(w['top'] - t) < 3 and (x0 - 3 <= (w['x0'] + w['x1']) / 2 <= x1 + 3
                                                                        or re.search('[Ѐ-ӿ]', w['text']))
                                             for t, x0, x1 in lines)] + latin
    out = []
    for side in (0,):
        ws = words
        rows: list[list[dict]] = []
        for w in sorted(ws, key=lambda w: (w['top'], w['x0'])):
            if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                rows[-1].append(w)
            else:
                rows.append([w])
        lines = []
        for r in rows:
            r.sort(key=lambda w: w['x0'])
            lines.append({'page': pno, 'words': [dict(w, page=pno, text=cyrillic_to_latin(w['text'])) for w in r],
                          'text': cyrillic_to_latin(' '.join(w['text'] for w in r))})
        out.append(lines)
    return out


def read() -> list[dict]:
    """The names, each with its words and its brigade's label."""
    stream = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for lines in halves(page, pno):
                stream += lines
    # a heading the page wrapped: "Četvrta vojvođanska narodnooslobodilačka udarna" / "brigada"
    joined = []
    for ln in stream:
        if (joined and re.match(r'^(?:narodnooslobodilačk\w+\s+)?(?:udarn\w+\s+)?brigad[aei]\b', ln['text'])
                and not re.search(r'\d', joined[-1]['text'])
                and re.match(rf'^[{U}]', joined[-1]['text']) and len(joined[-1]['text']) < 70):
            joined[-1] = dict(joined[-1], text=joined[-1]['text'] + ' ' + ln['text'])
        else:
            joined.append(ln)
    stream = joined
    entries, label, listing, heading, brigade = [], None, False, None, None
    for ln in stream:
        t = ln['text']
        if re.match(r'^\d{1,3}$', t):
            continue                                                   # a page number
        if re.match(r'^\d+\. Streljački korpus', t):
            break                                                      # the Red Army's lists
        if t.startswith('Poginuli borci'):
            heading, listing = t[len('Poginuli borci'):].strip(), False
            continue
        if not listing and HEADING.match(t) and len(t) < 90:
            brigade, heading = t, None                                 # a unit's heading, its history follows
            continue
        if not listing:
            if re.match(r'^[1Il]\.\s', t) and (heading is not None or brigade):         # "1.", the OCR's "I."
                # the list begins: "Poginuli borci <the brigade>", or the heading above when it says only "Poginuli
                # borci" (Deseta krajiška) or nothing at all
                label, listing = (heading or brigade or '').strip().replace('irištapske', 'prištapske'), True
            elif heading is not None:
                heading += ' ' + t                                     # "Poginuli borci Prve proleterske / brigade"
                continue
            else:
                continue
        if not re.search(r'\d+\.\s', t) and not re.match(rf'^[{L}]', t) and len(t) < 90 and not t.endswith((',', '.')):
            listing, heading = False, None                             # the next unit's heading
            if HEADING.match(t):
                brigade = t
            continue
        for w in ln['words']:
            entries.append({'word': w, 'label': label})
    # the run-on names: a number after a comma (or the list's start) opens one; a "3." inside a name is the initial
    # З. the OCR read as a digit ("Čoković 3. Milisav")
    # a comma and the next number read as one word ("Milenko,155.", "Petar,'272."): two tokens
    split = []
    for e in entries:
        if e['word']['text'] in WORDS:                                 # read from the page image
            split += [dict(e, word=dict(e['word'], text=t)) for t in WORDS[e['word']['text']]]
            continue
        m = re.fullmatch(r"(.+,)['’]?([a-z]?\d{1,4}[a-z]?[.,;]?)", e['word']['text'])   # also ",’b9.", ",136a."
        if m:
            split += [dict(e, word=dict(e['word'], text=m.group(1))), dict(e, word=dict(e['word'], text=m.group(2)))]
        elif re.fullmatch(r'[Il1]{1,2}\.', e['word']['text']) and (
                not split or split[-1]['label'] != e['label'] or split[-1]['word']['text'].endswith(',')):
            # the OCR's "I." and "II." for 1. and 11. (a father's initial "I." follows a surname, not a comma)
            split.append(dict(e, word=dict(e['word'], text=re.sub('[Il]', '1', e['word']['text']))))
        else:
            split.append(e)
    entries = split
    out, cur, prev, ended = [], None, '', None
    for i, e in enumerate(entries):
        w = e['word']
        if e['label'] == ended:
            continue
        # a name that ends with a full stop and has no number after it is the list's last: what follows is a photo's
        # caption ("Žujović Čedomir. VOKS1 —1TA1LJAM1 ROOŠ1LJ ...")
        nxt = entries[i + 1] if i + 1 < len(entries) else None
        if (cur and re.search(rf'[{L}]{{2}}\.$', w['text']) and nxt and nxt['label'] == e['label']
                and not re.fullmatch(r"[,'’:.«^]*[\dIl]{1,4}[a-z]?[.,«;-]*", nxt['word']['text'])):
            ended = e['label']
        # "17.", "811-", ",'272.", "918a.", ":357.", and after a comma a bare "717"
        num = re.fullmatch(r"[,'’:.«^]*(\d{1,4})[a-z]?[.,«-]+", w['text']) or (
            re.fullmatch(r'(\d{1,4})', w['text']) if prev.endswith(',') else None)
        # a number opens a name after a comma, or when it is the next in the list (its comma lost: "Aleksa 18.")
        if num and (cur is None or prev.endswith((',', '.')) or e['label'] != cur['label']
                    or 0 < int(num.group(1)) - cur['no'] <= 2):
            if cur:
                out.append(cur)
            cur = {'no': int(num.group(1)), 'words': [], 'label': e['label']}
        elif cur is not None and prev.endswith(',') and (re.search(r'\d', w['text'])
                                                          or re.fullmatch(r'[^\w\s]{1,2}[-.]|[A-Z]-', w['text'])):
            out.append(cur)                                            # a number the OCR garbled: "b9.", "129;", "P-"
            cur = {'no': cur['no'] + 1, 'words': [], 'label': e['label']}
        elif cur is not None:
            if w['text'] == '3.':
                w = dict(w, text='Z.')
            cur['words'].append(w)
        prev = w['text']
    if cur:
        out.append(cur)
    # a number the OCR misread between two good ones ("224. ..., 2246. ..., 226.", "525. ..., 256. ..., 527."): the one
    # between them
    for a, b, c in zip(out, out[1:], out[2:]):
        if a['label'] == b['label'] == c['label'] and c['no'] == a['no'] + 2 and b['no'] != a['no'] + 1:
            b['no'] = a['no'] + 1
    return out


def join(words: list[dict]) -> str:
    text = ''
    for w in words:
        if text.endswith('-') and w['text'][:1].islower():
            text = text[:-1] + w['text']                               # "Adamo-" / "vić"
        else:
            text += (' ' if text else '') + w['text']
    text = re.sub(r'\s+', ' ', text).strip().rstrip(',.;').strip()
    # the OCR's readings of a few Cyrillic letters and its specks: Љ as "L>" or "JĐ" (Ljubiša, Ljubinko), в as B
    # inside a word ("PerkoBić"), a quote, a dash or a digit stuck to a word, a comma after the surname
    text = re.sub(r'\bL>|\bJĐ', 'Lj', text)
    text = re.sub(rf'(?<=[{L}])B(?=[{L}])', 'v', text)
    text = re.sub(r"(?<!\bD)(?<!\bDell)['’>]", ' ', text)                # not the Italian "D’elfonso", "Dell’arciprete"
    text = re.sub(rf'(?<!\S)[-\d]+(?=[{U}])', '', text)
    text = re.sub(rf'^([{U}][{L}]+),\s', r'\1 ', text)
    for bad, good in SPELLED.items():
        text = text.replace(bad, good)
    # Л read as "JT" or "JJ", Љ as "JB" ("JTabus", "JBubo"); specks before or inside a name (".Čurić", "Adrović:",
    # "Miluti"n"); a word broken over two lines with its second half capitalized ("Bjeli- Ca", "Burzano- Vić") or
    # its hyphen kept ("Mi-lovan"); an initial with a dash ("D- Vlastimir"); two words run together ("TintorĐuro",
    # "MašićUglješa") or a capital inside one ("NiKola", "JovanOvić", "UzelaC")
    text = re.sub(r'\bJ[TJ](?=[a-z])', 'L', text)
    text = re.sub(r'\bJB(?=[a-z])', 'Lj', text)
    text = re.sub(r'^[^\w]+', '', text)
    text = re.sub(r'(?<=\w)[:"]|"(?=\w)', '', text)
    # (a double surname broken at its hyphen, "Polovina- Bulajić", keeps it: both halves are longer)
    text = re.sub(rf'([{L}]+)- ([{U}][{L}]*)', lambda m: m.group(1) + m.group(2).lower()
                  if min(len(m.group(1)), len(m.group(2))) <= 3 else m.group(0), text)
    text = re.sub(rf'(?<=[{L}])-(?=[{L}])', '', text)
    text = re.sub(rf'\b([{U}])- ', r'\1. ', text)
    text = re.sub(rf'(?<=[{L}]{{4}})(?![{U}]vić\b)([{U}])(?=[{L}]{{3,}})', r' \1', text)
    text = re.sub(rf'(?<=[{U}{L}][{L}])([{U}])(?=[{L}]+\b)', lambda m: m.group(1).lower(), text)
    text = re.sub(rf'(?<=[{L}]{{3}})C\b', 'c', text)
    return re.sub(r'\s+', ' ', text).strip()


def boxes(words: list[dict]) -> dict:
    page = words[0]['page']
    segs: list[list[dict]] = []
    for p in words:
        if p['page'] != page:
            break
        if segs and abs(segs[-1][-1]['top'] - p['top']) < 4 and p['x0'] >= segs[-1][-1]['x0']:
            segs[-1].append(p)
        else:
            segs.append([p])
    rects = [[round(min(p['x0'] for p in s), 1), round(min(p['top'] for p in s), 1),
              round(max(p['x1'] for p in s), 1), round(max(p['bottom'] for p in s), 1)] for s in segs]
    out = {'pdf_file': PDF, 'pdf_page': page, 'pdf_x': rects[0][0], 'pdf_y': rects[0][1],
           'pdf_x_end': max(r[2] for r in rects), 'pdf_y_end': max(r[3] for r in rects)}
    left = min(r[0] for r in rects)
    if left < rects[0][0]:
        out['pdf_x_left'] = left
    if len(rects) > 1:
        out['pdf_rects'] = rects
    return out


DROPPED: list = []


def parse(e: dict, n: int) -> dict | None:
    text = join(e['words'])
    # a list's last name and the note or caption after it: "Šešić Dobrivoj. (Za Artiljerijsku brigadu ... nisu
    # prikupljeni podaci)", "Trifunović Milorad. Imena poginulih boraca ..." (a father's initial is "B.", not "ir.")
    text = re.sub(rf'(?<=[{L}]{{2}})\.\s+.*$', '', text)
    if not re.search(rf'[{U}][{L}]', text):
        return None
    if len(text.split()) > 7 or re.search(r'[§\d]', text):
        DROPPED.append(text[:80])                                      # a photo's caption, a history's sentence
        return None
    printed = text
    # what the list says of him after the name: "Zorić Miladin—narodni heroj, k-dir čete", "Orlando Enrido (iz Modene,
    # Italija)", "Kosturanov Đorgi (Jošeski)" (the entry's text keeps it)
    text = re.sub(rf'\s*[—–]\s*[{L}].*$', '', text)
    text = re.sub(r'\s*\([^)]*\)', '', text).strip()
    nick = ''
    m = re.search(r'\s+[—–]\s+(.+)$', text)
    if m:                                                              # "Ašković B. Dragoljub — Dragan"
        nick, text = m.group(1).strip(), text[:m.start()]
    words = text.split()
    if len(words) > 1 and re.fullmatch(rf'[{U}][{L}]+[—–][{U}][{L}]+', words[-1]):
        words[-1], nick = re.split('[—–]', words[-1])                 # "Milutinović Fima—Femija"
    if len(words) >= 3 and words[0] in ('De', 'Di', 'Da', 'Dal', 'Del', 'Della', 'Dalla', 'Lo', 'La'):
        words = [f'{words[0]} {words[1]}'] + words[2:]                 # brigade »Italija«: "De Biasi Ferdinando"
    last = words[0] if words else ''
    father = next((w for w in words[1:] if re.fullmatch(rf'[{U}]\.', w)), '')
    given = ' '.join(w for w in words[1:] if w != father)
    shown = ' '.join(x for x in (last, father, given) if x) + (f' — {nick}' if nick else '')
    label = (e['label'] or '').strip()
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': shown, 'last_name': last, 'first_name': given, 'nick': nick,
           'fathers_name': father, 'birth_year': '', 'born_in': '', 'death_year': '', 'death_years': ['1944', '1945'],
           'units': [c] if (c := site_unit(label)) else [], 'unit': label, 'no': e['no']}
    # "Poginuli borci Prve proleterske brigade", "Prva konjička brigada, poginuli borci"
    intro = f'Poginuli borci {label}' if re.search(r'\bbrigade\b', label) else f'{label}, poginuli borci'
    rec['additional_info'] = f"{intro}: {e['no']}. {printed}."
    rec.update(boxes(e['words']))
    return rec


def main():
    raw = read()
    recs = []
    for e in raw:
        r = parse(e, len(recs) + 1)
        if r:
            recs.append(r)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    by = Counter((r['unit'][:60], tuple(r['units'])) for r in recs)
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}; {len(by)} lists')
    for (u, c), k in by.most_common():
        print(f'   {k:5d}  {c}  {u}')
    gaps = [f"{a['no']}->{b['no']}" for a, b in zip(recs, recs[1:]) if b['no'] != a['no'] + 1 and b['no'] != 1]
    print(f'number gaps: {len(gaps)}', gaps[:30])
    print(f"dropped as no names: {len(DROPPED)}", DROPPED[:12])
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} {r['units']} | {r['additional_info'][:110]}")


if __name__ == '__main__':
    main()
