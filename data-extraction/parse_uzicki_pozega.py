"""
The Požega companies' rolls in Jovan R. Radovanović's *Požega u NOR i revoluciji 1941—1945* (znaci.org 00003/696, the
appendix 696_2.pdf, book pp. 611-637, Cyrillic) → website/public/pdfs/pozega-cete.pdf: a second book of the Užički NOP
odred (unit 26) and of the Druga proleterska (unit 39).

The lists of fighters, each by village (a heading in capitals, often letter-spaced: "Б А К И О Н И Ц А") and then
"Borci sa drugih teritorija" (with "iz <town>" after the name), the names run on, comma after comma:
    "Илић (Милан) Петар, Јовићевић (Милић) Јеремија, Марјано-\nвић (Војин) Добривоје, ..."   (the father in brackets)
  1. the 1. požeška četa, 28 July 1941 - 1 March 1942, and 2. the 2. požeška četa, from 22 September 1941 (unit 26);
  3. the Pilatovačka četa on the day it was formed (26);
  4. the fighters guarding the objects in Požega and Jeminska Stena, 22 September - 29 November 1941 (26);
  5. the participants of the NOR in units other than the Požega companies, 1941 (26: the odred's other companies);
  10. the 1. četa of the odred's 5. bataljon, 1944 (26);
  11. the fallen and dead of the Požega company of the 2. proleterska brigada, a death after each name, ";" or ","
      between them (unit 39).
The appendix's other lists stay out: the workers of the partisan workshops in Požega, the people of Požega "who took
part in the partisan detachments or were their supporters or sympathizers", the Slovene refugees, the committees.
The rolls were put together after the war by the companies' surviving fighters, and the book says that a man moved
from one unit to another is in several lists: each list's entry is a record, merged later where it is one man.
Each name has the box of its own words (pdf_rects when it runs on to the next line): the PDF is in
entry_boxes.INLINE_ENTRIES.
Usage: python data-extraction/parse_uzicki_pozega.py [--write]   (without --write: a dry run that prints the lists)
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
from _parser_scaffold import assign_ids_to_soldiers, cyrillic_to_latin  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'pozega-cete.pdf'
SITE_PDF = HERE.parent / 'website' / 'public' / 'pdfs' / PDF
SOURCE = HERE / '.cache' / 'pozega' / '696_2.pdf'                 # znaci.org/00003/696_2.pdf
FIRST_PAGE = 611                                                  # the book's page of the PDF's 2nd page
UNIT_FILES = {26: HERE.parent / 'website' / 'public' / 'uzicki-odred-soldiers.json',
              39: HERE.parent / 'website' / 'public' / 'druga-proleterska-soldiers.json'}
ID_START = 10001
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# each list: its heading's first words (Latin), title, unit; None for a list that stays out
LISTS = [
    (r'BORACA 1\. POŽEŠKE ČETE', 'Spisak boraca 1. požeške čete od 28. jula 1941. do 1. marta 1942. godine', 26),
    (r'BORACA 2\. POŽEŠKE ČETE', 'Spisak boraca 2. požeške čete od 22. septembra 1941. do 1. marta 1942. godine', 26),
    (r'PILATOVAČKA ČETA', 'Pilatovačka četa 1941. na dan formiranja', 26),
    (r'BORACA NA OBEZBEĐIVANJU', 'Spisak boraca na obezbeđivanju objekata u Požegi i Jeminskoj Steni od 22. septembra do 29. novembra 1941. godine', 26),
    (r'UČESNIKA NOR-a U JEDINICAMA', 'Spisak učesnika NOR-a u jedinicama izvan požeških četa 1941.', 26),
    (r'RADNICI PARTIZANSKIH RADIONICA', None, None),
    (r'LICA U POŽEGI UŽIČKOJ', None, None),
    (r'IZBEGLICA SLOVENACA', None, None),
    (r'BITKA KOD POŽEGE', None, None),
    (r'BORACA 1\. ČETE 5\. BATALJONA', 'Spisak boraca 1. čete 5. bataljona Užičkog NOP odreda 1944. godine', 26),
    (r'POGINULIH I UMRLIH BORACA POŽEŠKE ČETE', 'Spisak poginulih i umrlih boraca Požeške čete 2. proleterske brigade', 39),
    (r'NARODNOOSLOBODILAČKI ODBORI', None, None),
]


def build_pdf() -> None:
    if not SITE_PDF.exists():
        src, out = fitz.open(SOURCE), fitz.open()
        out.insert_pdf(src, from_page=1, to_page=27)              # book pp. 611-637: the rolls to the 2. proleterska's fallen
        out.save(SITE_PDF, garbage=4, deflate=True)


def latin(t: str) -> str:
    return cyrillic_to_latin(t)


def lines(pdf) -> list[dict]:
    out = []
    for pno, page in enumerate(pdf.pages, 1):
        rows: list[list[dict]] = []
        for w in sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (round(w['top']), w['x0'])):
            w = dict(w, text=latin(w['text']), page=pno)
            if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                rows[-1].append(w)
            else:
                rows.append([w])
        for r in rows:
            r.sort(key=lambda w: w['x0'])
            text = ' '.join(w['text'] for w in r).strip()
            if re.fullmatch(r'\d{3}|PRILOG br\. \d+\.?|P R I L O Z I', text):
                continue
            out.append({'page': pno, 'words': r, 'text': text, 'head': heading(r)})
    return out


def heading(words: list[dict]) -> str | None:
    """A village's heading: a line in capitals, often letter-spaced ("Б А К И О Н И Ц А", "М И Л И Ћ Е В О  С Е Л О"):
    the letters joined where the gap between them is a letter's, a space where it is wider"""
    text = ' '.join(w['text'] for w in words)
    if not re.fullmatch(rf'[{U}][{U} ().\-]*', text) or len(text.replace(' ', '')) < 3:
        return None
    if text.startswith('BORCI') or '(' in text:
        return ' '.join(w.capitalize() for w in text.split())  # "BORCI SA DRUGIH TERITORIJA", "FIRENCA (ITALIJA)"
    # the text layer groups the spaced letters as the kerning falls ("BAKI ONICA", "PR IJANOVIĆI"): every village here
    # is one word but those of TWO_WORDS
    joined = text.replace(' ', '')
    return TWO_WORDS.get(joined, joined.capitalize())


# the villages of two words, whose letter-spaced headings join into one
TWO_WORDS = {'MILIĆEVOSELO': 'Milićevo Selo', 'SREDNJADOBRINJA': 'Srednja Dobrinja', 'DONJADOBRINJA': 'Donja Dobrinja',
             'GORNJADOBRINJA': 'Gornja Dobrinja', 'JELENDO': 'Jelen Do', 'GOJNAGORA': 'Gojna Gora'}


def read(pdf) -> list[dict]:
    entries, cur, title, unit, village, skipping = [], None, None, None, '', False
    tokens = []
    for ln in lines(pdf):
        t = ln['text']
        listed = next(((pat, ttl, u) for pat, ttl, u in LISTS if re.search(pat, t)), None)
        if listed:
            title, unit, village = listed[1], listed[2], ''
            tokens.append(('list', title, unit))
            continue
        if t.startswith('S P I S A K') or t.startswith('SPISAK') or re.fullmatch(r'(?:DO|OD) .*GODINE|\d{4}\. GODINE|IZVAN POŽEŠKIH ČETA 1941\.|JEMINSKOJ STENI .*|2\. PROLETERSKE BRIGADE', t):
            continue
        if ln['head'] and not re.search(r'[,.]', t):
            tokens.append(('village', ln['head']))
            continue
        for k, w in enumerate(ln['words']):
            tokens.append(('word', w, k == len(ln['words']) - 1))
    # a word broken at a line's end ("Marjano-" / "vić") is one; a note in brackets that reconstructs the roll ends it
    words = []
    for tk in tokens:
        if tk[0] != 'word':
            words.append(tk)
            continue
        _, w, end = tk
        prev = words[-1][1] if words and words[-1][0] == 'word' and words[-1][2] else None
        if prev and prev['text'].endswith('-') and w['text'][:1].islower():
            words[-1] = ('word', dict(prev, text=prev['text'][:-1] + w['text'], parts=prev['parts'] + [w]), end)
        else:
            words.append(('word', dict(w, parts=[w]), end))
    # the words of each list and village; a note in brackets that tells who reconstructed the roll ends the list's names
    sections, title, unit, village, skipping = [], None, None, '', False
    for tk in words:
        if tk[0] == 'list':
            title, unit, village, skipping = tk[1], tk[2], '', False
            continue
        if tk[0] == 'village':
            village = tk[1]
            continue
        w = tk[1]
        if title is None or skipping:
            continue
        if re.match(r'\((?:Sastav|Rekonstrukc|Napomena|Podaci)', w['text']):
            skipping = True
            continue
        if not sections or sections[-1]['key'] != (title, village):
            sections.append({'key': (title, village), 'list': title, 'unit': unit, 'village': village, 'words': []})
        sections[-1]['words'].append(w)
    # a name ends at its comma; in the 2. proleterska's list a death follows each name ("Bojić Slavko, poginuo 8. juna
    # 1943. godine na Milin Kladama; Smiljanić Manojle Cimer, poginuo ..."), so a name ends only where the next one
    # begins: after a comma or semicolon, two words with capitals
    def starts_name(ws: list[dict], i: int) -> bool:
        return (i + 1 < len(ws) and re.fullmatch(rf'[{U}][{L}]+', ws[i]['text'])
                and re.fullmatch(rf'[{U}][{L}]+[,;]?|[—–-]', ws[i + 1]['text']) is not None)
    for s in sections:
        ws, pending, depth = s['words'], [], 0
        for i, w in enumerate(ws):
            pending.append(w)
            depth = max(0, depth + w['text'].count('(') - w['text'].count(')'))
            if not re.search(r'[,;.]$', w['text']) or depth or re.fullmatch(rf'[{U}]\.', w['text']):
                continue
            if s['unit'] == 39 and i + 1 < len(ws) and not starts_name(ws, i + 1):
                continue
            entries.append({'words': pending, 'list': s['list'], 'unit': s['unit'], 'village': s['village']})
            pending = []
        if pending:
            entries.append({'words': pending, 'list': s['list'], 'unit': s['unit'], 'village': s['village']})
    # two men the book joins with "i" ("Zlatanović Momčilo, iz Leskovca, poginuo ... i Nikolić Tihomir Baćo, iz Lekovca")
    out = []
    for e in entries:
        ws = e['words']
        k = next((i for i in range(1, len(ws) - 2) if ws[i]['text'] == 'i' and e['unit'] == 39
                  and re.fullmatch(rf'[{U}][{L}]+', ws[i + 1]['text']) and re.fullmatch(rf'[{U}][{L}]+,?', ws[i + 2]['text'])), None)
        if k:
            out += [dict(e, words=ws[:k]), dict(e, words=ws[k + 1:])]
        else:
            out.append(e)
    return out


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


def parse(e: dict) -> dict | None:
    text = ' '.join(w['text'] for w in e['words']).strip().rstrip(',;.').strip()
    text = re.sub(r'\s+', ' ', text).replace("'", '')                # "Miliv'oje"
    text = re.sub(rf'(?<![\d.])06(?=[{L}])', 'Ob', text)             # "06renović", "(06ren)": the OCR's 06 for Об
    # the 2. proleterska's list: the name, then where he came from and how he died ("..., iz Zlakuse, poginuo ...")
    name, _, rest = text.partition(', ') if e['unit'] == 39 else (text, '', '')
    # "Atanacković Branislav iz Kruševca": the place after "iz"; "Vuković Dragoslav — Vule Pupavac": what he was called
    place = ''
    m = re.search(r'(?:^|\s+)iz\s+([^,]+)', name if e['unit'] != 39 else name + ', ' + rest)
    if m:
        place = m.group(1).strip()
        name = re.sub(r'\s+iz\s+[^,]+$', '', name)
    # two surnames parted by a dash ("Savičić — Marinković Desimir Era", "Drndarević — Vidić Milomir"): the first
    double = re.match(rf'^([{U}][{L}]+)\s+[—–-]\s+([{U}][{L}]+)\s+(?=[{U}])', name)
    if double:
        name = double.group(1) + ' ' + name[double.end():]
    nick = ''
    m = re.search(r'\s+[—–-]\s+(.+)$', name)
    if m:
        nick, name = m.group(1), name[:m.start()]
    duty = ''
    m = re.search(r'\s*\(((?:komandir|politički|zamenik|desetar|vodnik)[^)]*)\)', name)
    if m:
        duty, name = m.group(1), name[:m.start()] + name[m.end():]
    father = ''
    m = re.search(rf'\s*\(([{U}][{L}]+)\)', name)
    if m:
        father, name = m.group(1), name[:m.start()] + name[m.end():]
    m = re.search(rf'\s+([{U}])\.\s+', name)                     # "Marinković M. Radiša", "Petrović R. Slavka"
    if m and not father:
        father, name = m.group(1) + '.', name[:m.start()] + ' ' + name[m.end():]
    ws = name.split()
    if len(ws) < 2 or not all(re.fullmatch(rf'[{U}][{L}]+(?:-[{U}][{L}]+)?', w) for w in ws[:2]):
        return None                                             # "Đurašević kapetan (ime nepoznato)"
    last, first, more = ws[0], ws[1], ' '.join(ws[2:])
    nick = ' '.join(x for x in (more, nick) if x)
    others = not e['village'] or e['village'].startswith('Borci')
    where = place if others else e['village']
    info = f"{e['list']}, {'borci sa drugih teritorija' if others else e['village']}: {text}"
    rec = {'last_name': last, 'first_name': first, 'middle_name': '', 'fathers_name': father,
           'full_name': f'{last} {first}', 'additional_info': info, 'birth_year': '', 'birth_place': where,
           'unit_detail': '', '_unit': e['unit']}
    if nick:
        rec['nickname'] = nick
    if duty:
        rec['rank'] = duty
    rec.update(boxes(e['words']))
    return rec


def main() -> None:
    build_pdf()
    with pdfplumber.open(SITE_PDF) as pdf:
        raw = read(pdf)
    recs, dropped = [], []
    for e in raw:
        r = parse(e)
        if r:
            recs.append(r)
        else:
            dropped.append(' '.join(w['text'] for w in e['words']))
    print(f'{len(recs)} names; by list:', dict(Counter(r['additional_info'].split(',')[0][:60] for r in recs)))
    print('not names:', dropped)
    for u in (26, 39):
        mine = [r for r in recs if r['_unit'] == u]
        print(f'unit {u}: {len(mine)}; villages {len({r["birth_place"] for r in mine})}; fathers {sum(bool(r["fathers_name"]) for r in mine)}')
    if '--write' not in sys.argv:
        import random
        random.seed(1)
        for r in random.sample(recs, 20):
            print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} [{r['birth_place']}] {r.get('nickname', '')} | {r['additional_info'][:110]}")
        return
    for u, path in UNIT_FILES.items():
        mine = [dict(r) for r in recs if r['_unit'] == u]
        for r in mine:
            r.pop('_unit')
        mine.sort(key=lambda s: (s['last_name'].lower(), s['first_name'].lower()))
        mine = assign_ids_to_soldiers(mine, u, ID_START)
        kept = [s for s in json.loads(path.read_text(encoding='utf-8')) if s.get('pdf_file') != PDF]
        for s in kept:
            if s.get('other_sources'):
                s['other_sources'] = [o for o in s['other_sources'] if o.get('pdf_file') != PDF]
                if not s['other_sources']:
                    del s['other_sources']
        clash = {s['soldier_id'] for s in kept} & {s['soldier_id'] for s in mine}
        assert not clash, sorted(clash)[:5]
        path.write_text(json.dumps(kept + mine, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'unit {u}: {len(mine)} records from {ID_START} -> {path.name} (kept {len(kept)})')


if __name__ == '__main__':
    main()
