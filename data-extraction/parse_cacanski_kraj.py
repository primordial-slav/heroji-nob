"""
Čačanski kraj u NOB — pali borci i žrtve (grupa autora; znaci.org 00003/698) → website/public/pdfs/cacanski-kraj-pali.pdf:
a book across units, its fighters added to the records of the soldiers it describes (see scripts/match_references.py).

The book names the dead of the Čačak region, 1941-1945, by region (Dragačevci, Ljubićani, Takovci, Trnavci, Čačani:
the chapters 698_1-698_5, joined into one PDF, 313 pages) and village: the fallen fighters, and the civilians shot,
killed or dead in camps. Only the fighters are read: an entry that names a partisan unit or calls the man a "borac",
"borac NOVJ", a commander, commissar, courier or medic of one; never an entry of the Chetnik side ("borac Jeličkog
četničkog odreda"), nor a civilian victim, a "saradnik NOP-a" or an "odbornik NOO" without a fighter's word. The
book's "Narodni heroji pali u NOR-u", its documents and the "Poginuli posle 1948. godine" are not read.
Cyrillic, one column, each entry's first line indented (some 30pt right of the lines under it), the village headings
spaced out ("Б Е Л И  К А М Е Н"):
    ПАЈИЋ Живојина МИЛИСАВ, зидар, рођен 1906. у Вирову; борац Драгачевског батаљона; заробили га четници и предали
    Немцима, који су га стрељали код ВТЗ у Чачку 7. децембра 1941.
Surname, father (genitive), given name, a nickname after a dash, as in the Čačanski odred's list of its fallen (unit
126), whose battalions most of these men served in: the odred's battalions and the odred give the entry unit 126, the
2. proleterska 39.

Output: data-extraction/znaci/cacanski-kraj-pali-entries.json (IDs 9016xxxxxx, in the book's order) with the fields
the matcher reads, the region and village, and the entry's place on the page and its box.

Usage: python data-extraction/parse_cacanski_kraj.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
from _parser_scaffold import cyrillic_to_latin, extract_lines_single_column  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from parse_cacanski_odred import fix_digits  # noqa: E402

PDF = 'cacanski-kraj-pali.pdf'
PDF_PATH = HERE.parent / 'website' / 'public' / 'pdfs' / PDF
OUT = HERE / 'znaci' / 'cacanski-kraj-pali-entries.json'
PREFIX = '9016'
CHAPTERS = ['698_1.pdf', '698_2.pdf', '698_3.pdf', '698_4.pdf', '698_5.pdf']     # znaci.org/00003/...
REGIONS = ['Dragačevci', 'Ljubićani', 'Takovci', 'Trnavci', 'Čačani']
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]+'
FIGHTER = re.compile(r'\bbor(?:ac|ca|kinja)\b|\bbolničar|\bkurir|\bkomandir|\bkomandant|\bkomesar|\bdesetar|\bvodnik|'
                     r'\bpartizan|\bNOVJ?\b|\bNOP odred|\bbrigad|\bbataljon', re.I)
CHETNIK = re.compile(r'četničk\w* (?:odred|brigad|korpus|bataljon|čet\w*|komand)|ravnogor|ljotićev|nedićev\w* (?:odred|straž)|'
                     r'srpsk\w* državn\w* straž|dobrovolj', re.I)
UNITS = [(re.compile(r'(?:Dragačevsk|Ljubićk|Takovsk|Trnavsk|Čačansk|Gradsk)\w* (?:NOP |partizansk\w* )?(?:bataljon|čet|odred)|'
                     r'Čačansk\w* (?:NOP |partizansk\w* )?odred'), 126),
         (re.compile(r'Drug\w* proletersk\w* brigad'), 39)]


def join_chapters() -> None:
    """The five chapters as one PDF (the site's), once"""
    if PDF_PATH.exists():
        return
    out = fitz.open()
    for ch in CHAPTERS:
        out.insert_pdf(fitz.open(HERE / '.cache' / 'cacanski_kraj' / ch))
    out.save(PDF_PATH, garbage=3, deflate=True)


def chapter_starts() -> list[int]:
    starts, n = [], 1
    for ch in CHAPTERS:
        starts.append(n)
        n += len(fitz.open(HERE / '.cache' / 'cacanski_kraj' / ch))
    return starts


def read() -> list[dict]:
    lines = extract_lines_single_column(str(PDF_PATH), 1, None)
    starts = chapter_starts()
    left: dict = {}
    for ln in lines:
        ln['text'] = fix_digits(cyrillic_to_latin(ln['text'].strip()))
        if re.search(rf'[{L}]', ln['text']):                           # the text's margin: where the lines under it start
            left[ln['page']] = min(left.get(ln['page'], 10 ** 6), ln['x'])
    entries, village = [], ''
    for ln in lines:
        t, page = ln['text'], ln['page']
        region = REGIONS[max(i for i, s in enumerate(starts) if s <= page)]
        if re.fullmatch(r'[\d\W]{1,5}', t):
            continue                                                   # the page number
        if not re.search(rf'[{L}\d,;]', t):
            # a village (or region) heading, its letters spaced out ("B E L I K A M E N": the word gap is lost)
            village = re.sub(r'\s+', '', t) if re.fullmatch(rf'(?:[{U}]\s+)+[{U}]', t) else t
            continue
        indent = ln['x'] > left.get(page, 0) + 15
        if indent and re.match(rf'^{CAPS}', t):
            entries.append({'lines': [t], 'pdf_page': page, 'pdf_x': ln['x'], 'pdf_y': ln['y'], 'region': region,
                            'village': village})
        elif entries:
            entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = lines[0]
    for ln in lines[1:]:
        if re.search(rf'[{L}]-$', text) and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln
        else:
            text += ' ' + ln
    return re.sub(r'\s+', ' ', text).strip()


def village_name(spaced: str) -> str:
    return ' '.join(w[:1] + w[1:].lower() for w in spaced.split())


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    head, _, info = text.partition(',')
    parts = [p.split() for p in re.split(r'\s+[—–-]\s+', head)]
    words = [w.strip('.') for w in parts[0]]
    nick = ' '.join(w for p in parts[1:] for w in p).title()
    last = []
    while words and re.fullmatch(CAPS, words[0]):
        last.append(words.pop(0))
    father = words.pop(0) if words and re.fullmatch(rf'[{U}][{L}]+', words[0]) else ''
    given = [w for w in words if re.fullmatch(CAPS, w)]
    if not given and len(last) > 1:
        given = [last.pop()]
    if len(given) > 1 and not nick:
        given, nick = given[:1], ' '.join(given[1:]).title()
    last_name = ' '.join(w[:1] + w[1:].lower() for w in last)
    first_name = ' '.join(w[:1] + w[1:].lower() for w in given)
    info = re.sub(r'\bro[đćdcnN]e{1,2}n(a?)\b', r'rođen\1', info.strip())    # "roćen", "roden", "rođeen"
    info = re.sub(r'\bbo[oa]ac\b', 'borac', info)                         # "booac"
    rec = {'soldier_id': f'{PREFIX}{n:06d}',
           'name': ' '.join(x for x in (last_name, father, first_name) if x) + (f' — {nick}' if nick else ''),
           'last_name': last_name, 'first_name': first_name, 'nick': nick, 'fathers_name': father}
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
    rec['birth_year'] = y.group(1) if y else ''
    b = re.search(rf'\brođen[a]?\s+(?:1[89]\d\d\.?\s*)?u\s+([{U}][{L}]+(?:\s+[{U}]?[{L}]+){{0,2}})', info)
    rec['born_in'] = b.group(1) if b else (village_name(e['village']) if len(e['village']) >= 4 else '')
    years = re.findall(r'\b(19[34]\d)\b', info[b.end() if b else 0:])
    rec['death_year'] = years[-1] if years else ''
    when = re.search(rf'\b\d{{1,2}}\.\s*(?:[{L}]+|\d{{1,2}}\.)\s*19[34]\d', info)
    parsed = parse_when(when.group(0)) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = sorted({code for rx, code in UNITS if rx.search(info)})
    rec['region'], rec['village'] = e['region'], village_name(e['village'])
    rec['additional_info'] = info
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=round(e['pdf_x'], 1), pdf_y=round(e['pdf_y'], 1))
    return rec


def fighter(rec: dict) -> bool:
    info = rec['additional_info']
    return bool(FIGHTER.search(info)) and not CHETNIK.search(info)


def main():
    join_chapters()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    kept = [r for r in recs if fighter(r)]
    stats = entry_boxes.fill_boxes(kept)
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding='utf-8')
    by = {}
    for r in kept:
        by[r['region']] = by.get(r['region'], 0) + 1
    print(f'{len(recs)} entries read, {len(kept)} fighters -> {OUT.relative_to(HERE.parent)}; {by}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(kept, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} | {r['units']}")
            print(f"      {r['additional_info'][:150]}")
        print('-- left out:')
        for r in random.sample([r for r in recs if not fighter(r)], 6):
            print(f"  {r['name']!r}: {r['additional_info'][:140]}")


if __name__ == '__main__':
    main()
