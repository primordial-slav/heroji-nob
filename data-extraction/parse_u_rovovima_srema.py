"""
U rovovima Srema (Milorad Gončin; znaci.org 00001/211, the chapter 211_1.pdf) → website/public/pdfs/
u-rovovima-srema-poginuli.pdf: a book across units, its entries added to the records of the soldiers it describes (see
scripts/match_references.py).

"Spisak palih boraca", the fighters killed on the Srem front, one column, by brigade (a heading in capitals) and under
each by the village where they fell, the names run on, given name first, a duty after some:
    PRVA PROLETERSKA BRIGADA
    ERDEVIK: Simo Tubić, Svetozar Živković, Ljubo Vujović, Đuro Ni-
    kolić, Radmila Jovičić, ... Jelena Jelisavljević, bolničarka, Miloje Jovanović, Špiro Knežević.
So an entry has the name, the brigade (the site's unit where it is on the site: `units`) and the place of death; the
matcher weighs the unit and the place, and rules out a record that has him fall outside 1944-1945 (`death_years`).
The author's note on the last page is not read. Each name gets a box around its words (two when it runs on to the next
line, pdf_rects), so entry_boxes.py leaves these alone (INLINE_ENTRIES).

Output: data-extraction/znaci/u-rovovima-srema-poginuli-entries.json (IDs 9013xxxxxx, in the book's order).
Usage: python data-extraction/parse_u_rovovima_srema.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import parse_ofanziva_1942 as ofz  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'u-rovovima-srema-poginuli.pdf'
OUT = HERE / 'znaci' / 'u-rovovima-srema-poginuli-entries.json'
PREFIX = '9013'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# the brigades' headings and the site's unit for each that is on the site
UNITS = {
    'PRVA PROLETERSKA BRIGADA': 1, 'TREĆA KRAJIŠKA PROLETERSKA BRIGADA': 10, 'ČETVRTA KRAJIŠKA UDARNA BRIGADA': 11,
    'DVANAESTA KRAJIŠKA UDARNA BRIGADA': 54, 'PETA KRAJIŠKA (KOZARSKA) UDARNA BRIGADA': 12,
    'ČETVRTA SRPSKA UDARNA BRIGADA': 21, 'OSMA SRPSKA UDARNA BRIGADA': 87,
    'DESETA SRPSKA UDARNA BRIGADA': 88, 'DVANAESTA SRPSKA UDARNA BRIGADA': 90, 'KOSMAJSKA UDARNA BRIGADA': 74,
    'DVADESET PRVA SRPSKA UDARNA BRIGADA': 80, 'PRVA LIČKA PROLETERSKA BRIGADA': 2, 'DRUGA LICKA PROLETERSKA BRIGADA': 3,
    'TREĆA LIČKA PROLETERSKA BRIGADA': 118, 'TRINAESTA PROLETERSKA BRIGADA »RADE KONČAR«': 6,
    'ČETVRTA VOJVOĐANSKA UDARNA BRIGADA': 76, 'PETA VOJVOĐANSKA UDARNA BRIGADA': 82, 'ŠESTA VOJVOĐANSKA BRIGADA': 83,
    'OSMA CRNOGORSKA UDARNA BRIGADA': 38, 'TREĆA MAKEDONSKA UDARNA BRIGADA': 51, 'KONJIČKA BRIGADA': 92,
    'ČETVRTA PROLETERSKA CRNOGORSKA BRIGADA': 40, 'PRVA KRAJIŠKA UDARNA BRIGADA': 123, 'PETA SRPSKA UDARNA BRIGADA': 127,
}
PLACE = re.compile(rf'^([{U}][{U}.-]*(?:\s+(?:[{U}][{U}.-]*|[—–-]))*)\s*:$')    # "ERDEVIK:", "OTOK — RIPAĆA:"
HEAD_WORD = re.compile(rf'[{U}][{U}.-]*:?|[—–-]')                               # a word of such a heading
UNIT_LINE = re.compile(rf'[{U}][{U} .»«"()-]{{6,}}')                             # "PETA KRAJIŠKA (KOZARSKA) UDARNA BRIGADA"


def title(text: str) -> str:
    """"PRVA PROLETERSKA BRIGADA" -> "Prva proleterska brigada", keeping "»Rade Končar«"."""
    words = text.split()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        out.append(low[:1].upper() + low[1:] if i == 0 or w.startswith('»') or (out and out[-1].startswith('»')
                                                                              and not out[-1].endswith('«')) else low)
    return ' '.join(out).replace('»rade', '»Rade').replace('končar«', 'Končar«')


def place_name(text: str) -> str:
    return ' '.join(w[:1] + w[1:].lower() for w in text.split())


def lines(pdf) -> list[dict]:
    out = []
    for pno, page in enumerate(pdf.pages, 1):
        rows: list[list[dict]] = []
        for w in sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (round(w['top']), w['x0'])):
            if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                rows[-1].append(w)
            else:
                rows.append([w])
        for r in rows:
            r.sort(key=lambda w: w['x0'])
            text = ' '.join(w['text'] for w in r)
            if (re.match(r'^U rovovima S\w+\.?\s*\d*$', text) or re.fullmatch(r'\d{2,3}', text)
                    or re.match(r'^\d{2,3}\s+Milo\s?rad\s+Gon', text)):
                continue                                               # the running heads ("234 Milorad Gončin"), page numbers
            out.append({'page': pno, 'words': [dict(w, page=pno) for w in r], 'text': text})
    return out


def read() -> list[dict]:
    """The names in reading order, each with its words, brigade and place."""
    entries, unit, place, cur = [], None, None, []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        stream = []
        for ln in lines(pdf):
            if ln['text'].startswith('U pisanju knjige'):
                break                                                  # the author's note, last page
            if UNIT_LINE.fullmatch(ln['text']) and ':' not in ln['text']:
                stream.append(('unit', ln['text']))
                continue
            for k, w in enumerate(ln['words']):
                stream.append(('word', w, k == len(ln['words']) - 1))
    # tokens: a word broken at a line's end ("Ni-" / "kolić", "Milosav-" / "Ijević" with its lj read as Ij) is one
    toks = []
    for item in stream:
        if item[0] == 'unit':
            toks.append(item)
            continue
        _, w, line_end = item
        prev = toks[-1][1] if toks and toks[-1][0] == 'tok' and toks[-1][2] else None
        if prev and prev['text'].endswith('-') and (w['text'][:1].islower() or re.match(rf'Ij[{L}]', w['text'])):
            rest = 'lj' + w['text'][2:] if w['text'].startswith('Ij') else w['text']
            toks[-1] = ('tok', dict(prev, text=prev['text'][:-1] + rest, parts=prev['parts'] + [w]), line_end)
        else:
            toks.append(('tok', dict(w, parts=[w]), line_end))
    # a place's heading ("ERDEVIK:", "OTOK — RIPAĆA:") opens its names, also after a name a page end left without its
    # comma; a comma or period ends a name, except inside a note in brackets ("(umro u bolnici)")
    pending: list[dict] = []
    depth = 0
    for t in toks:
        if t[0] == 'unit':
            unit, place, pending, depth = t[1], None, [], 0
            continue
        w = t[1]
        if w['text'].endswith(':') and (HEAD_WORD.fullmatch(w['text']) or any(HEAD_WORD.fullmatch(x['text']) for x in pending)):
            # the heading is what stands since the last name, from its first word in capitals ("SOTIN — Grabovačka
            # pustara:", "KUKUJEVCI — DEONICA:"); a name before it lost its comma at a page's end ("Blažić KOMLETINCI:")
            k = 0
            while k < len(pending) and not HEAD_WORD.fullmatch(pending[k]['text'].rstrip(':')):
                k += 1
            if pending[:k] and unit and place:
                cur.append({'words': pending[:k], 'unit': unit, 'place': place})
            place = place_name(' '.join(x['text'] for x in pending[k:] + [w]).rstrip(':'))
            pending, depth = [], 0
            continue
        pending.append(w)
        depth = max(0, depth + w['text'].count('(') - w['text'].count(')'))
        if w['text'].endswith((',', '.')) and not depth and not re.fullmatch(rf'[{U}]\.', w['text']):
            # (a father's initial, "Dragomir U. Stanković", does not end the name)
            if unit and place:
                cur.append({'words': pending, 'unit': unit, 'place': place})
            pending = []
    for it in cur:
        words = it['words']
        # a duty after a name ("bolničarka", "zamenik komandira čete") belongs to the name before it, also when its
        # comma is missing before the next name ("vodnik Vukašin Petrović")
        j = 0
        while j < len(words) and words[j]['text'][:1].islower() and not re.match(rf'[čćžšđ][{L}]+(?:ić|ović|ević)\b', words[j]['text']):
            j += 1
        if j and entries:
            duty = ' '.join(x['text'] for x in words[:j]).rstrip(',.')
            entries[-1]['duty'] = (entries[-1].get('duty', '') + ', ' + duty).strip(', ')
            entries[-1]['words'] += words[:j]
        words = words[j:]
        text = ' '.join(x['text'] for x in words).rstrip(',.').strip()
        note = ' '.join(re.findall(r'\(([^)]*)\)?', text))
        text = re.sub(r'\s*\([^)]*\)?', '', text).strip()
        text = re.sub(r'[>*]|,\)', '', text)                          # the OCR's marks: "S>imić", "Vojisla*", "Lukić,)"
        text = re.sub(rf'([{U}{L}])\^\s*([{L}])', r'\1\2', text)      # "Ra^ dujko"
        text = re.sub(rf'\b([{U}][{L}]{{1,2}}) ([{L}]{{3,}})\b', r'\1\2', text)   # "Nu rija"
        own = ''
        dash = re.search(r'\s+[—–-]\s+(\S+)$', text)
        if dash:                                                       # "Aleksandar Antić — Prma"
            own, text = dash.group(1), text[:dash.start()]
        ws = text.split()
        if len(ws) >= 2 and ws[0][:1].isupper() and re.match(r'[čćžšđ]', ws[1]):
            ws[1] = ws[1].capitalize()                                 # a surname its capital lost: "Vojislav živanović"
        k = len(ws)
        while k > 1 and ws[k - 1][:1].islower():
            k -= 1
        if k < len(ws):                                                # "Branko Zec komandir voda": the duty, its comma lost
            it = dict(it, duty=' '.join(ws[k:]))
            ws = ws[:k]
        text = ' '.join(ws)
        if not re.search(rf'[{U}{L}]{{2}}', text) or text in ('Skoja', 'SKOJ-a', 'KPJ'):
            continue                                                   # "član Skoja", a duty
        names = text.split()
        # two names whose comma the text layer lost: "Miladin Zavić Branko Živković"
        groups = [names[:2], names[2:]] if len(names) == 4 and all(x[:1].isupper() for x in names) else [names]
        for g in groups:
            entries.append(dict(it, words=words, text=' '.join(g), note=note, own=own))
    return entries


def boxes(words: list[dict]) -> dict:
    parts = [p for w in words for p in w['parts']]
    page = parts[0]['page']
    segs: list[list[dict]] = []
    for p in parts:
        if p['page'] != page:
            break
        if segs and abs(segs[-1][-1]['top'] - p['top']) < 4:
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


def parse(e: dict, n: int) -> dict:
    words = e['text'].split()
    # a word the OCR split ("Dragoj e Branković"): a piece of a letter or two joins the word before it; a name whose
    # caron-letter the OCR set small ("živanović") gets its capital
    joined = []
    for w in words:
        if joined and re.fullmatch(rf'[{L}]{{1,2}}', w):
            joined[-1] += w
        else:
            joined.append(w[:1].upper() + w[1:] if re.match(r'[čćžšđ]', w) else w)
    given, last = (joined[0], joined[-1]) if len(joined) >= 2 else ('', joined[0] if joined else '')
    middle = ' '.join(joined[1:-1])
    name = ' '.join(joined)
    father = middle if re.fullmatch(rf'[{U}]\.', middle) else ''     # "Dragomir U. Stanković"
    nick = e.get('own') or ('' if father else middle)
    shown = ' '.join(x for x in (last, father, given) if x) + (f' {nick}' if nick else '')
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': shown,
           'last_name': last, 'first_name': given, 'nick': nick, 'fathers_name': father, 'birth_year': '', 'born_in': '',
           'death_place': e['place'], 'death_years': ['1944', '1945'], 'death_year': '',
           'units': [UNITS[e['unit']]] if e['unit'] in UNITS else [], 'unit': title(e['unit'])}
    rec['additional_info'] = (f"{rec['unit']}, {e['place']}: {name}" + (f" ({e['note']})" if e.get('note') else '')
                              + (f", {e['duty']}" if e.get('duty') else '') + '.')
    rec.update(boxes(e['words']))
    return rec


def main():
    ofz.corpus()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    by = Counter(r['unit'] for r in recs)
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}; {len(by)} units')
    for u, c in by.most_common():
        print(f'   {c:4d}  {u}')
    odd = [r for r in recs if not re.fullmatch(rf'[{U}][{L}]+(?:-[{U}][{L}]+)? [{U}][{L}]+(?: [{U}][{L}]+)?', r['name'])]
    print(f'odd names: {len(odd)}', [r['name'] for r in odd[:40]])
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} {r['units']} | {r['additional_info'][:120]}")


if __name__ == '__main__':
    main()
