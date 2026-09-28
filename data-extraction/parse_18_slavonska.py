"""
Parser: 18. Slavonska Udarna Brigada (brigade code 17).

Source: Rade Roksandić, Zdravko B. Cvetković — "18. SLAVONSKA BRIGADA"
        znaci.org/00001/101_5.pdf  →  website/public/pdfs/18-slavonska.pdf
Two lists, Latin:
    pp. 1-24   "SPISAK POGINULIH I UMRLIH BORACA I RUKOVODILACA 18. UDARNE BRIGADE" — a three-column
               table without rules: name stacked in column 1 (surname / father / first name),
               birth date and place in column 2, date and place of death in column 3:
                   Barvalac     2. 3. 1912.     21. 3. 1945.
                   Božidara     Bobota,         Stražeman
                   Milenko      Vukovar
    pp. 30-54  "SPISAK PREŽIVELIH BORACA 18. SLAVONSKE UDARNE BRIGADE" — one line per soldier:
                   Bognić Andrija, Gor. Andrijevci, kbr. 100 — Sl. Brod,
pp. 25-29 list the officers by unit, 55-57 are the table of contents; 58-66 belong to an unrelated
publication bound into the same scan. Street addresses and house numbers of the survivors
(post-war residence) are left out; village and municipality are kept.
"""
import json
import re
import sys
from collections import Counter

import pdfplumber
from _parser_scaffold import _record, assign_ids_to_soldiers, repair_lj_ocr, restore_diacritics
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/18-slavonska.pdf'
OUT = 'website/public/18-slavonska-soldiers.json'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
TABLE_PAGES = range(1, 25)
SURVIVOR_PAGES = range(30, 55)
ENTRY_GAP = 10.1          # pt: lines within an entry are 8.2-9.7 apart, entries 10.6+ (measured on all table pages)
DEATH_WORD = re.compile(r'\b(?:poginu|umr|nesta|streljan|ubijen|zarobljen)', re.I)


def _undouble(word: str) -> str:
    """Bold type OCR'd twice per letter: "GGrruubbiiššnnoo" → "Grubišno"."""
    if len(word) >= 4 and len(word) % 2 == 0 and all(word[i] == word[i + 1] for i in range(0, len(word), 2)):
        return word[::2]
    return word


def _lines(words):
    """Group words into lines by their top coordinate."""
    out = []
    for w in words:
        w['text'] = _undouble(w['text']).replace('ié', 'ić').strip('"')
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if out and abs(w['top'] - out[-1]['y']) < 3.5:
            out[-1]['words'].append(w)
        else:
            out.append({'y': w['top'], 'words': [w]})
    for ln in out:
        ln['words'].sort(key=lambda w: w['x0'])
        ln['text'] = ' '.join(w['text'] for w in ln['words'])
        ln['x'] = ln['words'][0]['x0']
    return out


def table_entries(pdf):
    for pno in TABLE_PAGES:
        page = pdf.pages[pno - 1]
        words = viewer_words(page)
        if not words:
            continue
        # column 1's left edge: the most common x0 in the left third of the text
        xs = Counter(round(w['x0']) for w in words)
        left = min(w['x0'] for w in words)
        c1 = max((x for x in xs if x < left + 40), key=lambda x: xs[x])
        b12, b23 = c1 + 68, c1 + 170
        body = [w for w in words if w['top'] > 150 or pno > 1]
        body = [w for w in body if not re.fullmatch(r'[123X]', w['text'])]
        col = lambda w: 0 if w['x0'] < b12 else (1 if w['x0'] < b23 else 2)
        c1_lines = _lines([w for w in body if col(w) == 0 and re.match(rf'[{U}]', w['text'])])
        c1_lines = [ln for ln in c1_lines if not re.search(r'Prezime|Datum|rođenja|SPISAK|RUKOVODILACA', ln['text'])]
        starts = [i for i, ln in enumerate(c1_lines) if i == 0 or ln['y'] - c1_lines[i - 1]['y'] > ENTRY_GAP]
        for k, i in enumerate(starts):
            j = starts[k + 1] if k + 1 < len(starts) else len(c1_lines)
            names = [ln['text'] for ln in c1_lines[i:j]]
            top = c1_lines[i]['y']
            bottom = c1_lines[j]['y'] if j < len(c1_lines) else top + 60
            cells = []
            for c in (1, 2):
                cw = [w for w in body if col(w) == c and top - 3 <= w['top'] < bottom - 3]
                cells.append(' '.join(ln['text'] for ln in _lines(cw)))
            yield {'page': pno, 'y': round(top, 1), 'x': round(c1_lines[i]['x'], 1),
                   'y_end': round(bottom - 2, 1), 'names': names, 'born': cells[0], 'died': cells[1]}


def table_record(e):
    names = [n.strip(' .,•\'') for n in e['names'] if n.strip(' .,•\'')]
    if not names:
        return None
    last = names[0]
    first = names[-1] if len(names) > 1 else ''
    father = ' '.join(names[1:-1]) if len(names) > 2 else ''
    born = re.sub(r'\s+', ' ', e['born']).strip(' ,')
    died = re.sub(r'\s+', ' ', e['died']).strip(' ,')
    died = re.sub(r"[^\w.)]+$", '', died)
    died = re.sub(r'(\d{4})\.\s(?=\S)', r'\1, ', died, count=1)          # "14. 1. 1945. Grub. Polje" → "14. 1. 1945, Grub. Polje"
    parts = []
    if born:
        parts.append(re.sub(r'(\d{4})\.\s', r'\1, ', born, count=1))       # "2. 3. 1912. Bobota, Vukovar" → "2. 3. 1912, Bobota, ..."
    if died:
        parts.append(died if DEATH_WORD.search(died) else 'poginuo ' + died)
    rec = _record(last, first.upper(), father, ', '.join(parts))
    rec.update({'pdf_file': '18-slavonska.pdf', 'pdf_page': e['page'], 'pdf_y': e['y'], 'pdf_x': e['x'], 'pdf_y_end': e['y_end']})
    return rec


SURVIVOR = re.compile(rf'^([{U}][{L}]+(?:-[{U}][{L}]+)?)\s+(?:([{U}][{L}]?)\.\s*)?([{U}][{L}]+(?:\s[{U}][{L}]+)?),\s*(.*)$')
ADDRESS = re.compile(r'\b(?:kbr|ul|trg|br)\.?\s|\d|\b(?:ulica|ul|trg|cesta|obala|put|bb)\b', re.I)


def survivor_records(pdf):
    for pno in SURVIVOR_PAGES:
        for ln in _lines(viewer_words(pdf.pages[pno - 1])):
            t = ln['text'].strip()
            m = SURVIVOR.match(t)
            if not m:
                continue
            last, initial, first, rest = m.groups()
            # keep village and municipality; drop street names and house numbers (post-war residence)
            place = [p.strip(' ,.•') for p in re.split(r',|—', rest) if p.strip(' ,.•') and not ADDRESS.search(p)]
            rec = _record(last, first.upper(), initial or '', ', '.join(place))
            rec.update({'pdf_file': '18-slavonska.pdf', 'pdf_page': pno, 'pdf_y': round(ln['y'], 1), 'pdf_x': round(ln['x'], 1),
                        'pdf_y_end': round(ln['y'] + 9, 1)})
            yield rec


if __name__ == '__main__':
    with pdfplumber.open(PDF) as pdf:
        fallen = [r for r in (table_record(e) for e in table_entries(pdf)) if r]
        survivors = list(survivor_records(pdf))
    print(f'[17] {len(fallen)} fallen (table), {len(survivors)} survivors')
    soldiers = repair_lj_ocr(restore_diacritics(fallen + survivors))
    soldiers.sort(key=lambda s: (s['last_name'].lower(), s['first_name'].lower()))
    soldiers = assign_ids_to_soldiers(soldiers, 17)
    json.dump(soldiers, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'  {len(soldiers)} soldiers  |  birth_year: {sum(1 for s in soldiers if s["birth_year"])}  →  {OUT}')
