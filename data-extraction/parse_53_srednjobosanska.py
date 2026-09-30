"""
Parser: 53. srednjobosanska NOU divizija (brigade code 33) — the fallen, captured and missing.

Source: "Spisak poginulih, zarobljenih i nestalih boraca Pedeset treće NOU srednjebosanske divizije"
        znaci.org  →  website/public/pdfs/53-srednjobosanska-divizija.pdf
pp. 2-68 a numbered table (799 numbers and a row "505a", 12 a page, landscape; pages sit differently):
    Redni broj | PREZIME (očevo ime) i IME | Godina i mjesto rođenja | jedinica | Gdje je poginuo, nestao,
    zarobljen | Gdje je sahranjen | Primjedba
    1 | Aksenić Ristin Stojan | 1907 Miškovci | 1. četa I batalj. 18 brig. | Fojnica 5. V 1945. | nije izvučen |
Names are in title case, the father's name a possessive or a genitive. The remark says when a soldier was
not killed ("Nestao u borbi", "Zarobljen u borbi ranjen", "Umro u bolnici"); a row without one is a fallen
soldier. read_rows takes each page's column edges from where its text segments start and hands run_parser
one line per row: "Aksenić Ristin Stojan⁣ | 1907 Miškovci | 1. četa I batalj. 18 brig. | Fojnica 5. V 1945. | ..."
"""
import re

import pdfplumber

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser
from pdf_coords import viewer_words

MARK = '⁣'
DATE = r'(?:\d{1,2}\.\s*[IVX]{1,4}\.?\s*)?(?:1[89]\d\d)\.?(?:\s*g(?:od)?\.)?'
FATES = r'(?:[Pp]oginu[oloa]+|[Nn]esta[oloa]+|[Zz]arob[lj]+en[a]?|[Uu]mr[loa]+|[Ss]trijelj[a-z]*|[Ss]trelj[a-z]*|[Uu]bijen[a]?)'


def _segments(words: list[dict]) -> list[list[dict]]:
    """Text runs: the words of a line, split where the gap between two words is wider than a column gap."""
    segs = []
    for ln in _lines(words):
        cur = [ln[0]]
        for w in ln[1:]:
            if w['x0'] - cur[-1]['x1'] > 12:
                segs.append(cur)
                cur = [w]
            else:
                cur.append(w)
        segs.append(cur)
    return segs


def _columns(segs: list[list[dict]]) -> list[float]:
    """Left edges of the born, unit, killed, buried and remark columns, from where the page's text runs start."""
    xs = sorted(s[0]['x0'] for s in segs)
    clusters = []
    for x in xs:
        if clusters and x - clusters[-1][-1] < 25:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    starts = [(c[0], len(c)) for c in clusters]
    name = starts[0][0]
    pick = lambda lo, hi, n=1: next((x for x, k in starts if lo <= x <= hi and k >= n), None)
    born = pick(name + 150, name + 230, 5)
    unit = pick(born + 60, born + 120, 5)
    killed = pick(unit + 60, unit + 230, 5)
    buried = pick(killed + 90, killed + 170) or killed + 128
    note = pick(buried + 80, buried + 170) or buried + 128
    return [born - 4, unit - 4, killed - 4, buried - 4, note - 4]


def _merge_split_words(words: list[dict]) -> list[dict]:
    """The text layer puts a space inside some words ("Prnj avor") and after every letter of letter-spaced cells
    ("S a r a jevo"): those gaps are under 2pt, a real word gap 3pt or more (a comma may sit closer)."""
    out = []
    for line in _lines(words):
        for w in line:
            p = out[-1] if out and out[-1]['line'] is line else None
            if p and -1.5 < w['x0'] - p['x1'] < 2 and not p['text'].endswith(','):
                out[-1] = dict(p, text=p['text'] + w['text'], x1=w['x1'])
            else:
                out.append(dict(w, line=line))
    return out


def _lines(words: list[dict]) -> list[list[dict]]:
    lines = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if lines and abs(lines[-1][0]['top'] - w['top']) < 3:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(ln, key=lambda w: w['x0']) for ln in lines]


def _contiguous(cell: list[dict], y: float) -> list[dict]:
    """A cell's lines follow each other ~9pt apart: a wider gap ends it (the publisher's note under the last row,
    the rule and page number at a page's foot)."""
    kept, prev = [], y - 8
    for w in sorted(cell, key=lambda w: w['top']):
        if w['top'] - prev > 14:
            break
        kept.append(w)
        prev = max(prev, w['top'])
    return kept


def read_rows(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(start, (end or len(pdf.pages)) + 1):
            page = pdf.pages[pno - 1]
            words = _merge_split_words(viewer_words(page))
            page.close()
            hdr = max((w['bottom'] for w in words if w['text'] in ('rođenja', 'zarobljen', 'Primjedba', 'jedinica')), default=60)
            body = [w for w in words if w['top'] > hdr + 5]
            segs = _segments(body)
            bounds = _columns(segs)
            col = lambda w: sum(w['x0'] >= b for b in bounds)       # 0 = number and name, 1-5 the rest
            names = [s for s in segs if col(s[0]) == 0]
            starts, prev = [], -99.0
            for s in names:
                numbered = re.fullmatch(r'\d{1,3}', s[0]['text']) is not None and len(s) > 1
                if numbered or s[0]['top'] - prev > 20:
                    starts.append(s[0]['top'])
                prev = s[0]['top']
            for i, y in enumerate(starts):
                y_end = starts[i + 1] - 8 if i + 1 < len(starts) else y + 45     # not the closing note on p. 68
                cells = [[w for w in body if col(w) == k and y - 8 <= w['top'] < y_end] for k in range(6)]
                cells[0] = [w for w in cells[0] if w['top'] >= y - 2]
                cells = [_contiguous(c, y) for c in cells]
                name = ' '.join(w['text'] for ln in _lines(cells[0]) for w in ln)
                name = re.sub(r'^\d{1,3}\s*', '', name)
                # the page number (".2fi"), and footnotes: "1 Arhiva VII, dok. br. 2, ...", "i Ime nečitko vjerovatno Ismet"
                bare = re.sub(r'\([^)]*\)?', '', name)                  # not a note: "Grubač Adam (nije upisano ime ...)"
                if not re.search(r'[A-ZČĆŽŠĐ][a-zčćžšđ]{2}', bare) or len(re.findall(r'\b[a-zčćžšđ]{3,}', bare)) >= 2 \
                        or bare.startswith('Arhiva'):
                    continue
                first = min(cells[0], key=lambda w: (w['top'], w['x0']))
                text = [' '.join(w['text'] for ln in _lines(c) for w in ln) for c in cells[1:]]
                out.append({'text': re.sub(r'^(\S+)', r'\1' + MARK, name, count=1) + ' | ' + ' | '.join(text),
                            'x': first['x0'], 'y': round(first['top'], 1), 'page': pno})
    return out


def parse_entry(text: str) -> dict:
    """Surname [Father] Given | born | unit | killed | buried | remark"""
    text = text.replace(MARK, '').translate(str.maketrans('àèìòù', 'aeiou')).replace(";'", 'j')   # "Fahri;'a"
    text = re.sub(r"(?<=\w)['’/]+(?=\w)", '', text)                 # specks inside words: "J'ozo", "Toma/nović"
    text = re.sub(r"\s[«*'’]+(?=[\s,|]|$)", '', text)                # and between them: "Prnjavor «"
    text = re.sub(r"[■•\\\"_*]+|(?<=\w)['’]+(?=[\s.,|]|$)", '', text)   # "■Sije", "Čavci'", "23'. II"
    text = re.sub(r'!(?=\s|,|$)', ',', text)                         # "Jaružani! B. Luka"
    text = re.sub(r'\s+\.(?=\s|,|$)', '', re.sub(r',\s*,', ',', text))
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\bit\b', 'u', text)                               # "ml. vodnik it 3. batalj."
    cells = [c.strip() for c in text.split('|')] + [''] * 5
    name, born, unit, killed, buried, note = cells[:6]
    remark = re.findall(r'\(([^)]*)\)', name)                       # "(nije upisano ime u dokumentu)"
    name = re.sub(r'\s*\([^)]*\)', '', name)
    name = re.sub(r'^[a-z]\s+', '', name)                           # "a Pjetlović": a misread row number
    toks = [re.sub(r'\d+$', '', t) for t in name.split()]            # "Bege1": a footnote mark
    toks = [re.sub(r'\^$', 'ć', re.sub(r'^2(?=[a-z])', 'Ž', t)) for t in toks]   # "Dragonji^", "2ivko"
    toks = [t for t in toks if re.search(r'[A-Za-zČĆŽŠĐčćžšđ]', t)]
    i = 1
    while i < len(toks):                                            # "Stoj an": a name the OCR split
        if toks[i][0].islower():
            toks[i - 1:i + 1] = [toks[i - 1] + toks[i]]
        else:
            i += 1
    # "šunjić", "PavičiĆ": the case of a letter misread
    toks = [t[0].upper() + (t[1:].lower() if re.search(r'[a-zčćžšđ]', t[1:]) else t[1:]) for t in toks]
    last = toks[0] if toks else ''
    given = toks[-1] if len(toks) > 1 else ''
    father = ' '.join(toks[1:-1])
    parts = []
    born = born.strip(' ,').lstrip('. ')
    if born:
        born = re.sub(r'(1[89]\d\d)\.?(?:\s*g(?:od)?\.)?(?:\s+|$)', lambda m: m.group(1) + (', ' if m.end() < len(born) else ''),
                      born, count=1)
        parts.append('rođen ' + born)
    if unit:
        parts.append(unit)
    note = re.sub(r'^Netaso\b', 'Nestao', note)
    lead = re.search(FATES, note[:12])
    if lead:                                                          # "iMll Umrla od pjeg.": specks before it
        note = note[lead.start():]
    fate = re.match(FATES, note)
    verb = re.sub(r'^zarob[lj]+en', 'zarobljen', note[:fate.end()].lower()) if fate else 'poginuo'   # "Zarobjlen"
    rest = note[fate.end():].strip(' ,.') if fate else note
    rest = re.sub(r'^U\b', 'u', rest)                                 # "U borbi sa četnicima"
    if remark:
        rest = '; '.join(remark + ([rest] if rest else []))
    date = re.search(DATE, killed)
    place = (killed[:date.start()] + ' ' + killed[date.end():]).strip(' ,.') if date else killed.strip(' ,.')
    when = re.sub(r'\.?(?:\s*g(?:od)?\.)?$', '', date.group(0).strip(' ,')) if date else ''     # "29. VIII 1944. g."
    death = ' '.join(x for x in (verb, rest if rest.lower().startswith(('u ', 'od ', 'na ', 'kod ')) else '') if x)
    if not fate and re.match(FATES, place):                          # "Umro u div. bolnici u Tesliću" under "killed"
        death, place = place[0].lower() + place[1:], ''
    parts.append(', '.join(x for x in (death, when, place) if x))
    if buried:
        parts.append('sahranjen: ' + buried)
    info = re.sub(r'(?:,\s*)+,', ',', ', '.join(p for p in parts if p.strip(' ,')))
    if rest and not rest.lower().startswith(('u ', 'od ', 'na ', 'kod ')):
        info += '. ' + rest[0].upper() + rest[1:].rstrip('.') + '.'   # "Nije iznešen", "Odvežen kući": not a place
    return _record(last, given, father, info)


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/53-srednjobosanska-divizija.pdf',
        brigade_code=33,
        output_path='website/public/53-srednjobosanska-soldiers.json',
        start_page=2,
        end_page=68,
        script='latin',
        extract_fn=read_rows,
        entry_start_re=re.compile(r'^\S+' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
