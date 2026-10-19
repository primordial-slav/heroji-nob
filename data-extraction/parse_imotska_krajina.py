"""
Nedjeljko Kujundžić (ed.), *Imotska krajina u NOB-u 1941-1945.* (znaci.org bk=803, the whole book 00003/803.pdf, PDF pp.
163-472: "Pali borci i žrtve fašističkog terora") → website/public/pdfs/imotska-krajina-pali-borci.pdf, the pages that
hold its fighters: a book across units.

By village (a title page each, Aržano to Župa Donja), two sections, each under its own heading: "Poginuli borci" and
"Žrtve fašističkog terora", then the village's memorials ("Spomen obilježja", "MJESNO UDRUŽENJE SUBNOR-a ..."). Only the
first section goes in (the user's decision of 2026-10-14 for the books that list fighters and victims together; here the
book itself parts them). Two columns a page, a bio each, the name given name first:
    "ANTE BREKALO pok. Petra rođen je 1924. godine u Aržanu. Zemljoradnik. Hrvat. / U NOV je stupio 1943 godine. ..."
The father is "pok. Petra" (the late Petar, genitive), a possessive ("Markov", "Antin") or, for a wife, her husband
("ž. Ivanova", left out as father); a nickname in »«. The units the site has that an entry names go to `units`
(4. splitska = 8, ...). Each entry keeps the box of its lines in its column.

Output: data-extraction/znaci/imotska-krajina-pali-borci-entries.json, IDs 9037xxxxxx.
Usage: python data-extraction/parse_imotska_krajina.py [--sample N]
"""
from __future__ import annotations

import json
import random
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
import _karlovac_lists as kl  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
from parse_mosorski_odred_2 import CHETNIK, FIGHTER, REAR  # noqa: E402
from pdf_coords import viewer_offset  # noqa: E402

BOOK = 'imotska-krajina-pali-borci'
SRC = HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_803.pdf'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9037'
TITLE = 'Imotska krajina u NOB-u, Poginuli borci'
FIRST, LAST = 163, 472                                 # the list's pages in the whole book's PDF
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NOT_A_NAME = {'NOV', 'NOB', 'NOVJ', 'NOO', 'KPJ', 'KPH', 'SKOJ', 'AFŽ', 'SUBNOR', 'NDH', 'MJESNO', 'UDRUŽENJE', 'OPĆINSKI',
              'ODBOR', 'SPOMEN', 'PLOČA', 'ŠKOLE', 'KOJE', 'NOSE', 'IMENA', 'PODACI', 'USAOH', 'JNA'}
UNITS = [(r'\b(?:4\.|IV\.?)\s*splitsk|\b4\.\s*dalmatinsk', 8), (r'\b(?:1\.|I\.?)\s*dalmatinsk', 36),
         (r'\b(?:2\.|II\.?)\s*dalmatinsk', 7), (r'\b(?:3\.|III\.?)\s*dalmatinsk', 46), (r'\b(?:11\.|XI\.?)\s*dalmatinsk', 53),
         (r'\b(?:12\.|XII\.?)\s*dalmatinsk', 50), (r'\b(?:6\.|VI\.?)\s*dalmatinsk', 103),
         (r'Mosorsk\w*\s+(?:partizansk\w*\s+)?odred', 148), (r'\b(?:13\.|XIII\.?)\s*proletersk', 6)]


def caps(w: str) -> bool:
    letters = [c for c in w if c.isalpha()]
    return len(letters) >= 2 and all(c.isupper() for c in letters) and w.strip('»«-.,') not in NOT_A_NAME


def page_lines(page) -> list[list[dict]]:
    """The page's lines, column by column (two columns that stand where the scan put them)."""
    dx, dy = viewer_offset(page)
    ws = [dict(w, x0=w['x0'] - dx, x1=w['x1'] - dx, top=w['top'] - dy, bottom=w['bottom'] - dy)
          for w in page.extract_words(keep_blank_chars=False)]
    if not ws:
        return []
    # the columns' left edges: the two x where most words start, at least a column's width apart
    starts = Counter(round(w['x0'] / 5) * 5 for w in ws).most_common()
    margins = [starts[0][0]]
    for x, n in starts[1:]:
        if abs(x - margins[0]) > 120 and n >= 3:
            margins.append(x)
            break
    split = max(margins) - 8 if len(margins) == 2 else 10 ** 6
    cols = []
    for side in (lambda w: w['x0'] < split, lambda w: w['x0'] >= split):
        lines = []
        for w in sorted((w for w in ws if side(w)), key=lambda w: (w['top'], w['x0'])):
            if lines and abs(w['top'] - lines[-1]['top']) < 3:
                lines[-1]['words'].append(w)
            else:
                lines.append({'top': w['top'], 'words': [w]})
        for ln in lines:
            ln['words'].sort(key=lambda w: w['x0'])
            ln['text'] = ' '.join(w['text'] for w in ln['words'])
            ln['x0'] = ln['words'][0]['x0']
            ln['x1'] = max(w['x1'] for w in ln['words'])
            ln['bottom'] = max(w['bottom'] for w in ln['words'])
        cols.append(lines)
    return cols


def read() -> tuple[list[dict], list[int]]:
    entries, section, village, pages = [], '', '', set()
    with pdfplumber.open(SRC) as pdf:
        for pno in range(FIRST, LAST + 1):
            cols = page_lines(pdf.pages[pno - 1])
            for col in cols:
                for ln in col:
                    t = ln['text'].replace('\xad', '-').strip()
                    # the headings, a title across both columns: "Poginuli" | "borci", "Žrtve fašističkog" | "terora"
                    if re.fullmatch(r'Poginuli(?:\s+borci)?', t):
                        section = 'borci'
                        continue
                    if re.match(r'^(?:Žrtve fašističkog|Spomen\b|SPOMEN|MJESNO UDRUŽENJE|OPĆINSKI ODBOR|Opća napomena|PODACI O BROJU|'
                                r'Pali borci i žrtve)', t):
                        section = ''
                        continue
                    if t in ('borci', 'terora'):
                        continue
                    if len(cols[0]) + len(cols[1] if len(cols) > 1 else []) <= 2 and re.fullmatch(rf'[{U}][{L}]+(?:\s+[{U}]?[{L}]+)*', t):
                        village = t                              # a village's title page ("Aržano")
                        section = ''
                        continue
                    if section != 'borci' or re.fullmatch(r'[\d\W]{1,6}', t):
                        continue
                    words = t.split()
                    start = len(words) >= 1 and caps(words[0]) and (len(words) == 1 or caps(words[1]) or words[1] in ('-', '—'))
                    if start or (words and caps(words[0]) and not entries):
                        entries.append({'lines': [t], 'pdf_page': pno, 'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1),
                                        'box': [ln['x0'], ln['top'], ln['x1'], ln['bottom']], 'village': village})
                        pages.add(pno)
                    elif entries:
                        e = entries[-1]
                        e['lines'].append(t)
                        if pno == e['pdf_page']:
                            b = e['box']
                            e['box'] = [min(b[0], ln['x0']), b[1], max(b[2], ln['x1']), max(b[3], ln['bottom'])]
                        pages.add(pno)
    return entries, sorted(pages)


def join_lines(ls: list[str]) -> str:
    text = ''
    for ln in ls:
        if re.search(r'[-]$', text) and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def parse(e: dict, n: int, page_map: dict) -> dict:
    text = join_lines(e['lines']).translate(kl.OCR)
    text = re.sub(r'\b(?:Dr|dr)\.\s+', '', text)
    words = text.split()
    i = 0
    while i < len(words) and (caps(words[i]) or words[i] in ('-', '—')):
        i += 1
    # digits the OCR read for letters in the capitals: "KUJUND2IĆ", "2UPIĆ" (Ž), "MI5EVIĆ" (Š), "M1JO" (I)
    name_words = [w.translate(str.maketrans('251', 'ŽŠI')) for w in words[:i] if w not in ('-', '—')]
    rest = ' '.join(words[i:])
    given = name_words[0] if name_words else ''
    surname = '-'.join(''.join(p.split()) for p in re.split(r'\s*-\s*', ' '.join(name_words[1:]))) if len(name_words) > 1 else ''
    # "ANDRIJA UJE VIC": a surname the OCR broke apart is one word; "BULJAN - KLAPIRIĆ" keeps its hyphen
    father = ''
    m = re.match(rf'^pok\.\s+([{U}][{L}]+)\s*', rest)
    if m:
        father, rest = m.group(1), rest[m.end():]
    else:
        m = re.match(rf'^ž\.\s+[{U}][{L}]+\s*', rest)              # a wife: her husband, not her father
        if m:
            rest = rest[m.end():]
        else:
            m = re.match(rf'^([{U}][{L}]+(?:ov|ev|in|ova|eva|ina|ljev|ljeva))\s+', rest)
            if m:
                father, rest = m.group(1), rest[m.end():]
    nick = ''
    m = re.match(r'^[»"]\s*([^«"]+?)\s*[«"]\s*', rest)
    if m:
        nick, rest = re.sub(r'\.\s+', '', m.group(1)).strip(' -'), rest[m.end():]      # "Ame. rikanac"
    first = '-'.join(kl.spelled(p, 'first') for p in given.split('-') if p)
    last = '-'.join(kl.spelled(p, 'last') for p in surname.split('-') if p)
    rec = {'soldier_id': f'{PREFIX}{n:06d}',
           'name': ' '.join(x for x in (first, f'»{nick}«' if nick else '', last) if x) + (f', {father}' if father else ''),
           'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': father}
    born = re.search(r'\bro[đd]en[a]?\s+(?:je\s+)?(?:[\d.\s]*?)(1[89]\d\d)\.?,?\s*(?:godine\s*)?(?:u\s+([^.,]+))?', rest)
    rec['birth_year'] = born.group(1) if born else ''
    rec['born_in'] = ', '.join(x for x in ((born.group(2) or '').strip() if born else '', e['village']) if x)
    death = list(re.finditer(r'\b(?:poginu[oa]|ubijen[a]?|ubil[ei]|strijeljan[a]?|strijeljal[ei]|umro|umrla|nesta[oa]|nestala|zaklal[ei])\b', rest, re.I))
    after = rest[death[0].start():] if death else ''
    y = re.search(r'\b(19[34]\d)\b', after[:140])
    rec['death_year'] = y.group(1) if y else ''
    when = re.search(r'\b\d{1,2}\.\s?\d{1,2}\.?\s?19[34]\d', after[:140])
    parsed = parse_when(when.group(0)) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = sorted({code for pat, code in UNITS if re.search(pat, rest, re.I)})
    rec['additional_info'] = f"{e['village']}: {rest}" if e['village'] else rest
    rec['list'] = TITLE
    b = e['box']
    rec.update(pdf_file=PDF.name, pdf_page=page_map[e['pdf_page']], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'],
               pdf_x_end=round(b[2], 1), pdf_y_end=round(b[3], 1))
    return rec


def main() -> None:
    ofz.corpus()
    raw, pages = read()
    page_map = {p: i for i, p in enumerate(pages, 1)}
    if not PDF.exists():
        src, out = fitz.open(SRC), fitz.open()
        for p in pages:
            out.insert_pdf(src, from_page=p - 1, to_page=p - 1)
        out.save(PDF, garbage=4, deflate=True)
    every = [parse(e, i, page_map) for i, e in enumerate(raw, 1)]          # IDs by place among the section's entries
    # within the section too, only the fighters (the book counts there SKOJ members and political workers killed in
    # prison, and Lovreć's heading over its victims is lost): the rule of parse_mosorski_odred_2
    fighters = [r for r in every if FIGHTER.search(REAR.sub('', r['additional_info'])) and not CHETNIK.search(r['additional_info'])]
    # an officer given only his rank, or a man the entry puts in a unit without a verb of joining, is a fighter too; the
    # activists whose entry names their part in the movement (SKOJ, the party, the NOO) go in, marked (the user's
    # decision of 2026-10-19); the rest, Lovreć's massacre among them, stay out
    extra = [r for r in every if r not in fighters and mos.fighter_or_officer(r)]
    for r in every:
        if r not in fighters and r not in extra and mos.activist(r):
            r['role'] = 'activist'
    recs = [r for r in every if r in fighters or r in extra or r.get('role')]
    print(f'{len(every)} entries in the fighters\' sections, {len(fighters)} fighters by the rule, {len(extra)} by rank '
          f'or unit, {sum(bool(r.get("role")) for r in recs)} activists')
    if '--dropped' in sys.argv:
        for r in extra:
            print(f"  F   {r['name']!r} | {r['additional_info'][:140]}")
        for r in every:
            if r not in recs or r.get('role'):
                print(f"  {'ACT' if r.get('role') else 'OUT'} {r['name']!r} | {r['additional_info'][:140]}")
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} fighters on {len(pages)} pages -> {OUT.relative_to(HERE.parent)}; villages: {len({r["additional_info"].split(":")[0] for r in recs})}')
    print(f"no given: {sum(not r['first_name'] for r in recs)}, no surname: {sum(not r['last_name'] for r in recs)}, "
          f"father: {sum(bool(r['fathers_name']) for r in recs)}, birth year: {sum(bool(r['birth_year']) for r in recs)}, "
          f"death year: {sum(bool(r['death_year']) for r in recs)}, units: {Counter(u for r in recs for u in r['units'])}")
    if '--sample' in sys.argv:
        random.seed(6)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['units']} | {r['additional_info'][:120]}")


if __name__ == '__main__':
    main()
