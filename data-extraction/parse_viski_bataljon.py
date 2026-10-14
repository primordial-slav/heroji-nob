"""
Parser: Viški dobrovoljački bataljon (brigade code 172), January - April 1944.

Source: Dr Veseljko Huljić, "Vis 1941-1945" (Institut za historiju radničkog pokreta Dalmacije, Split 1979; znaci.org
        00003/804.pdf) →  website/public/pdfs/viski-bataljon.pdf (book pp. 538-539), Prilog II/8: "Spisak boraca
        Viškog dobrovoljačkog bataljona (na otoku Visu krajem siječnja 1944. godine)": the command, then each četa and
        vod (and the desetine of Biševo and Oključna), the names run on, surname first:
            Vodnik: Žaja Vicko; borci: Roki Roko, Karuza Marica, Karuza Andrò, ...
The battalion was formed in January 1944 to strengthen the island's defence and disbanded at the end of April (the
book's note under the list). A man named twice (a vodnik among his platoon's borci) keeps both entries, as printed.
Each name keeps the box of its own words (entry_boxes.INLINE_ENTRIES), in two where it runs on to the next line.
"""
import re

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

ROLES = [('zamjenik komandanta', 'zamjenik komandanta'), ('zamjenik komandira', 'zamjenik komandira'),
         ('politički komesar', 'politički komesar'), ('komandant', 'komandant'), ('komandir', 'komandir'),
         ('vodnik', 'vodnik'), ('desetar', 'desetar'), ('borci', 'borac')]
ORD = {'prva': '1.', 'druga': '2.', 'treća': '3.'}
RECORDS: list[dict] = []


def _lines(page) -> list[list[dict]]:
    words = sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (round(w['top']), w['x0']))
    lines: list[list[dict]] = []
    for w in words:
        if lines and abs(lines[-1][0]['top'] - w['top']) < 5:       # the spaced headings sit lower
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(ln, key=lambda w: w['x0']) for ln in lines]


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """Reads both pages into RECORDS (name, role, section, boxes); returns one line per record for run_parser."""
    tokens, ctx = [], {'četa': '', 'vod': '', 'komanda': False}
    with pdfplumber.open(pdf_path) as pdf:
        for pn, page in enumerate(pdf.pages[start - 1:end], start):
            for ln in _lines(page):
                text = ' '.join(w['text'] for w in ln)
                squeezed = re.sub(r'\s+', '', text).rstrip(':').lower()
                if re.match(r'^(prilog|spisak|\(naotoku|\d{3}$|prema:|napomena)', squeezed) or squeezed.startswith('n a p'):
                    if squeezed.startswith(('prema:', 'napomena')):
                        break                                   # the sources and the note under the list
                    continue
                if squeezed == 'komandabataljona':
                    ctx = {'četa': '', 'vod': '', 'komanda': True}
                    continue
                m = re.fullmatch(r'(prva|druga|treća)četa', squeezed)
                if m:
                    ctx = {'četa': ORD[m.group(1)] + ' četa', 'vod': '', 'komanda': False}
                    continue
                m = re.fullmatch(r'(\d)\.vod', squeezed)
                if m:
                    ctx['vod'] = m.group(1) + '. vod'
                    continue
                if squeezed in ('biševo', 'oključna'):
                    ctx['vod'] = 'desetina ' + text.strip()
                    continue
                for w in ln:
                    tokens.append({'w': w, 'page': pn, 'ctx': dict(ctx), 'last': w is ln[-1]})
    # join the words a line end broke ("Stje­" / "pan", "Radov-" / "niković", "Vita-" / "Ijić")
    joined = []
    for t in tokens:
        if joined and joined[-1]['open']:
            prev = joined[-1]
            prev['text'] = prev['text'].rstrip('-­') + t['w']['text']
            prev['words'].append((t['page'], t['w']))
            prev['open'] = False
            continue
        txt = t['w']['text']
        joined.append({'text': txt, 'words': [(t['page'], t['w'])], 'ctx': t['ctx'],
                       'open': t['last'] and txt.endswith(('-', '­')) and len(txt) > 2})
    role, name = '', []
    i = 0
    while i < len(joined):
        tok = joined[i]
        low = tok['text'].lower().strip(':;,.')
        two = (low + ' ' + joined[i + 1]['text'].lower().strip(':;,.')) if i + 1 < len(joined) else low
        hit = next((r for k, r in ROLES if two == k), None)
        if hit:
            role, name, i = hit, [], i + 2
            continue
        hit = next((r for k, r in ROLES if low == k and ' ' not in k), None)
        if hit:
            role, name, i = hit, [], i + 1
            continue
        name.append(tok)
        if len(name) == 2:
            words = [pw for t in name for pw in t['words']]
            last = re.sub(r'(?<=[a-zčćžšđ])Ij', 'lj', name[0]['text'].strip(',;.:'))
            given = name[1]['text'].strip(',;.:').translate(str.maketrans('àèìòù', 'aeiou'))
            c = name[0]['ctx']
            sect = 'komanda bataljona' if c['komanda'] else ', '.join(x for x in (c['vod'], c['četa']) if x)
            RECORDS.append({'last': last, 'given': given, 'role': role, 'sect': sect, 'words': words})
            name = []
        i += 1
    out = []
    for k, r in enumerate(RECORDS):
        page, w = r['words'][0]
        out.append({'text': f'§x§{k}§', 'x': round(w['x0'], 1), 'y': round(w['top'], 1), 'page': page})
    return out


def parse_entry(text: str) -> dict:
    r = RECORDS[int(re.match(r'^§x§(\d+)§', text).group(1))]
    info = f"{r['role']}, {r['sect']}" if r['role'] else r['sect']
    rec = _record(r['last'], r['given'], '', info)
    rec['rank'] = r['role']
    if r['sect'] != 'komanda bataljona':
        rec['unit_detail'] = r['sect']
    rects = {}
    for page, w in r['words']:
        rects.setdefault((page, round(w['top'])), []).append(w)
    boxes = [[round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
              round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)] for ws in rects.values()]
    rec['_box'] = {'pdf_x_end': boxes[0][2], 'pdf_y_end': boxes[0][3] + 1}
    if len(boxes) > 1:
        rec['_box']['pdf_rects'] = boxes
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:                                              # run_parser sets a line's box; the name's words win
        s.update(s.pop('_box'))
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/viski-bataljon.pdf',
        brigade_code=172,
        output_path='website/public/viski-bataljon-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
