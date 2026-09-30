"""
Parser: 32. zagorska divizija NOVJ and the Western group of detachments (brigade code 35) — the roster.

Source: "32. divizija" (znaci.org), "Spisak boraca 32. divizije i Zapadne grupe Odreda"
        znaci.org  →  website/public/pdfs/32-divizija.pdf
pp. 1-41 names only, four columns a page, alphabetical, with photographs between them:
    Abramovac Pavao        Adamić Đure Franjo        *Abramović Marko        - Brajlović Šerif
"Imena ispred kojih su zvijezdice, to su borci poginuli u NOB-i. Crtice (povlaka) ispred imena i prezimena to su
borci koji su za vrijeme borbe u toku NOB-e nestali" — a star marks the fallen (the scan often reads it as ’ or ‘),
a dash the missing; the others lived. SURNAME, the father (genitive, or abbreviated: "Fr."), the given name.
read_lines hands run_parser one line per name, each column top to bottom.
"""
import glob
import json
import re
from collections import Counter

import pdfplumber

from _margin_entries import lone_names_to_given
from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser
from pdf_coords import viewer_words

MARK = '⁣'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
STAR, DASH = r'[*’‘\'•"„”]', r'[-–—]'
_last: Counter = Counter()


def _lines(words: list[dict]) -> list[list[dict]]:
    lines = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if lines and abs(lines[-1][0]['top'] - w['top']) < 3:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(ln, key=lambda w: w['x0']) for ln in lines]


def _merge_split_words(words: list[dict]) -> list[dict]:
    """The text layer breaks some names ("Pi jetro", "Dam j an"): pieces under 2pt apart are one word."""
    out = []
    for ln in _lines(words):
        prev = None
        for w in ln:
            if prev and -1.5 < w['x0'] - prev['x1'] < 2 and not re.fullmatch(STAR + '|' + DASH, prev['text']):
                prev['text'] += w['text']
                prev['x1'] = w['x1']
            else:
                prev = dict(w)
                out.append(prev)
    return out


def _columns(words: list[dict]) -> list[float]:
    """Left edges of columns 2-4: the starts of text runs (a gap over 8pt before them) cluster at four places."""
    starts = []
    for ln in _lines(words):
        for i, w in enumerate(ln):
            if i == 0 or w['x0'] - ln[i - 1]['x1'] > 8:
                starts.append(w['x0'])
    clusters = []
    for x in sorted(starts):
        if clusters and x - clusters[-1][-1] < 20:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    big = sorted(sorted(clusters, key=len, reverse=True)[:4], key=lambda c: c[0])
    return [sorted(c)[len(c) // 10] - 12 for c in big[1:]]                  # a star sits a few points left


def read_lines(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(start, (end or len(pdf.pages)) + 1):
            page = pdf.pages[pno - 1]
            words = [w for w in _merge_split_words(viewer_words(page))
                     if not (pno == 1 and w['top'] < 400) and w['bottom'] - w['top'] > 8]   # title, legend; captions (6pt)
            page.close()
            if not words:
                continue
            for w in words:                                                 # a lone mark goes with the name after it
                if re.fullmatch(r'[^\w\s(]+', w['text']):
                    nxt = [v for v in words if abs(v['top'] - w['top']) < 3 and 0 <= v['x0'] - w['x1'] < 15]
                    if nxt:
                        w['x0'] = min(v['x0'] for v in nxt) - 0.5
            bounds = _columns(words)
            col = lambda w: sum(w['x0'] >= b for b in bounds)
            for k in range(4):
                for ln in _lines([w for w in words if col(w) == k]):
                    text = ' '.join(w['text'] for w in ln).strip()
                    # page numbers, photo captions ("Zakletva boraca 32. divizije NOVJ"): not a name
                    lower = [t for t in re.findall(rf'\b[{L}]{{3,}}\b', re.sub(r'\([^)]*\)', '', text)) if t not in ('ing',)]
                    if re.fullmatch(r'[\W\d]*', text) or len(lower) >= 2 or re.search(r'\d{2}', text):
                        continue
                    if re.match(r'^(?:\(|iz\s|kod\s|u\b)', text) and out and out[-1]['page'] == pno:
                        out[-1]['text'] += ' ' + text                        # "(iz Ludbrega)", "iz s. G. Voča" under its name
                        continue
                    text = re.sub(rf'^([^\w(]*)([{U}]{{3,}})\b', lambda m: m.group(1) + m.group(2).title(), text)   # "HABIJANEC Ivan"
                    pair = re.match(rf'^(\S+ )(\S+) i ([{U}][{L}]+)$', text)          # "Šćurić Mato i Martin": two brothers
                    for t in ([pair.group(1) + pair.group(2), pair.group(1) + pair.group(3)] if pair else [text]):
                        out.append({'text': MARK + t, 'x': ln[0]['x0'], 'y': round(ln[0]['top'], 1), 'page': pno})
    return out


def parse_entry(text: str) -> dict:
    """[*|-] Surname [Father | F.] Given [ing.] [(note)]"""
    text = text.replace(MARK, '')
    fate = ''
    m = re.match(rf'^\s*([^\w\s(]+|4(?=[{U}]))\s*', text)                  # the mark before the name
    if m:
        mark = m.group(1)
        if re.fullmatch(DASH + '+', mark):
            fate = 'nestao u NOB'
        elif not re.fullmatch(r'[.,]+', mark):                           # "*", "‘", "’", "\"", "■", "4": the star
            fate = 'poginuo u NOB'
        text = text[m.end():]
    text = text.translate(str.maketrans('àèìòùäÌ}', 'aeiouall', '■')).replace('}', '')   # "Andrò", "MÌaden"
    notes = re.findall(r'\(([^)]*)\)', text)
    text = re.sub(r'\s*\([^)]*\)?', '', text)
    nick = re.findall(r'»([^«]*)«?', text)                                 # "Turčić »Ćoso«"
    text = re.sub(r'\s*»[^«]*«?', '', text)
    notes += ['zvani ' + n for n in nick]
    text = re.sub(r'\s+[-—–]+\s*$', '', text)                              # a stray dash after the name
    m2 = re.search(r'\s+[-—–]\s+(\S.*)$', text)                           # "Mirković Đuro — čiča", "Maroti — žena"
    if m2:
        notes.append(m2.group(1))
        text = text[:m2.start()]
    place = re.search(r'\s(?:iz|kod)\s.*$', text)                          # "Medenjak Drago iz s. G. Voča"
    if place:
        notes.append(place.group(0).strip())
        text = text[:place.start()]
    tail = re.search(r'\s+(st|ml)\.?$', text)                              # stariji, mlađi
    if tail:
        notes.insert(0, tail.group(1) + '.')
        text = text[:tail.start()]
    if re.search(r'\s\?$', text):                                         # "Anđelić ?": the given name unknown
        notes.insert(0, 'ime nepoznato')
        text = text[:-1].strip()
    toks = [t.strip(".,;:'’‘*") if not re.fullmatch(rf'[{U}][{L}]?\.', t) else t for t in text.split()]
    toks = [t for t in toks if t]
    if toks and toks[0].lower().rstrip('.') == 'dr':                        # "Dr. Soć"
        notes.insert(0, 'dr.')
        toks.pop(0)
    if toks and toks[-1] in ('ing', 'ing.', 'dr', 'dr.'):                  # "Župan Ante ing."
        notes.insert(0, toks.pop().rstrip('.') + '.')
    toks = [re.sub(r'^2(?=[a-z])', 'Ž', t) for t in toks]                 # "2ic Sofija"
    toks = [t[0].upper() + t[1:] if t[0].islower() and len(t) > 2 else t for t in toks]   # "čuček Marko": a lost capital
    last = toks[0] if toks else ''
    given = toks[-1] if len(toks) > 1 else ''
    father = ' '.join(toks[1:-1]).rstrip('.') if len(toks) > 2 else ''
    info = '; '.join(x for x in (fate, *notes) if x)
    return _record(last, given, father, info)


def carons(soldiers: list[dict]) -> list[dict]:
    """The scan drops the caron of Ž (and some Š, Č): the roster sorts Ž after Z, so once the Ž names begin (the
    first one printed with its caron), a later plain Z name takes it ("Zugec" → Žugec), unless the corpus knows
    it only without."""
    pairs = {'Z': 'Ž', 'S': 'Š', 'C': 'Č'}
    in_caron = None
    for s in soldiers:                                                     # document order
        name = s['last_name']
        base = name[:1].translate(str.maketrans('ŽŠČĆ', 'ZSCC'))
        if in_caron and base != in_caron:
            in_caron = None
        if base in pairs and name[:1] == pairs[base]:
            in_caron = base
        elif in_caron and name[:1] == base:
            cand = pairs[base] + name[1:]
            if not (_last[name] >= 5 and _last[name] >= 10 * _last[cand]):
                s['last_name'] = cand
                s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    first = Counter()
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.endswith('32-divizija-soldiers.json'):
            first.update(s['first_name'] for s in json.load(open(f, encoding='utf-8')))
    return lone_names_to_given(repair_lj_ocr(restore_diacritics(carons(soldiers))), first, _last)


if __name__ == '__main__':
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.endswith('32-divizija-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                _last[s['last_name']] += 1
    run_parser(
        pdf_path='website/public/pdfs/32-divizija.pdf',
        brigade_code=35,
        output_path='website/public/32-divizija-soldiers.json',
        start_page=1,
        end_page=41,
        script='latin',
        extract_fn=read_lines,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
