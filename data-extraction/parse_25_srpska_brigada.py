"""
Parser: 25. srpska NOU brigada (brigade code 31) — the fallen and the wounded.

Source: the brigade's monograph, chapters "Spisak poginulih boraca i rukovodilaca" (pp. 2-7, 108 names, then
        the author's note) and "Spisak ranjenih boraca i rukovodilaca 25. srpske brigade" (pp. 9-21, 260 names),
        compiled from the brigade's wartime lists in the Military History Institute archive
        znaci.org  →  website/public/pdfs/25-srpska-brigada.pdf
Single column, Cyrillic, numbered (each list from 1):
    1. КРСТИН П. Најдан из Гостуше, срез нишавски, борац 2. чете 2. батаљона, погинуо 11. X 1944. ...
    106. НИКОЛИН Чедомир, борац 4. батаљона, погинуо 28. IX 1944. код Трновца.
SURNAME, the father's initial, the given name in title case, then "из" and the village. The scan reads a
final Ћ as К, Н or Е (КРСТИН, ЖИВКОВИК, ЈОВАНОВИЕ) and Ђ as Б (БОРБЕВИК); every surname in these lists ends
in -ић, so -ин/-ик/-ие always become -ić.
"""
import glob
import itertools
import json
import re
from collections import Counter

from _margin_entries import fix_cyrillic_ocr_line
from _parser_scaffold import _record, repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

U = 'A-ZČĆŽŠĐ'
OUTPUT = 'website/public/25-srpska-brigada-soldiers.json'
ENTRY_START = re.compile(rf'^\d{{1,3}}\s*[.,]\s*(?![IVX]+\b)[{U}]{{2,}}')     # not a date: "10. XI 1944."


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or re.fullmatch(r'[IVX]', t):     # page numbers, specks
        return False
    if ln['page'] == 7 and ln['y'] > 150:                                  # the note after the list of the fallen
        return False
    if ln['page'] == 1 or ln['page'] == 8:                                 # the lists' titles
        return False
    t = re.sub(rf'^(\d{{1,3}}\s*[.,]\s*[{U}]{{2,}}) 3\.\s', r'\1 Z. ', t)   # "KOSTIK 3. Novica": the father's З
    t = fix_cyrillic_ocr_line(t).replace('L>', 'Lj').replace('l>', 'lj')    # Љ read as "Л>": "Л>убераће"
    t = re.sub(r'\bLz(?=[a-zčćžšđ.])', 'Lj', t)                            # ... or as "Лз": "Лзубомир", "Лз."
    t = re.sub(r"\s[:>'„\"]+(?=\s|$)", '', t)                              # specks: "2. čete 1. > bataljona"
    t = re.sub(r"(?<=\.)\s+[^A-Za-zčćžšđ]*(?:[a-z][^A-Za-zčćžšđ]*)?$", '', t)   # "na Ušima. ••.-.,> ;d /,"
    t = re.sub(r"(?<=[,.])'", '', t)                                       # "Trnjanska,' srez"
    t = re.sub(r'\bmlaći\b', 'mlađi', t)                                   # ђ read as ћ
    t = re.sub(rf'(?<=[{U}])\.T(?=[{U}])', 'J', t)                         # "STO.TANOVIĆ"
    t = re.sub(rf'^(\d{{1,3}}\s*[.,]\s*)([{U}][{U}j]*[{U}])(?=\s)',          # "VELjKOVIK": Lj inside a caps name
               lambda m: m.group(1) + m.group(2).upper(), t)
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    """N. SURNAME [F.] Given [Given2] iz Village, srez ..., rank unit, poginuo/ranjen date place."""
    text = re.sub(r'^\d{1,3}\s*[.,]\s*', '', text)
    end = re.search(r',|\s(?=iz\s)', text)
    head, bio = (text[:end.start()], text[end.end():].strip()) if end else (text, '')
    toks = head.split()
    last = toks[0] if toks else ''
    rest = toks[1:]
    father = ''
    if rest and re.fullmatch(rf'[{U}][a-zčćžšđ]?[.-]?', rest[0]) and (len(rest) > 1 or rest[0][-1] in '.-'):
        father = rest.pop(0).rstrip('.-')   # "VACIE A- Radivoje"
    note = []
    if len(rest) > 1:                                                     # "Ivan Ivica": a second name
        note.append('zvani ' + ' '.join(rest[1:]))
    info = '; '.join(note + ([bio] if bio else []))
    return _record(last, rest[0] if rest else '', father, info)


def ic_endings(soldiers: list[dict]) -> list[dict]:
    """A surname ending -in/-ik/-ie is -ić misread (see above); "Ćirić" read as "Ćirik" too."""
    for s in soldiers:
        s['last_name'] = re.sub(r'i[nke]$', 'ić', s['last_name'])
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


CONFUSIONS = {'A': 'D', 'a': 'dl', '°': 'o', 't': 'g', 'B': 'Đ', 'V': 'Đ', 'b': 'đ', 'ć': 'đ'}


def name_counts() -> dict[str, Counter]:
    counts = {'last_name': Counter(), 'first_name': Counter()}
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.endswith(OUTPUT.split('/')[-1]):                          # not this unit's earlier output
            for s in json.load(open(f, encoding='utf-8')):
                for k in counts:
                    counts[k][s[k]] += 1
    return counts


def ocr_confusions(soldiers: list[dict]) -> list[dict]:
    """A name unknown as printed takes the best-known spelling one or two of the scan's usual misreads give:
    Д read as А ("Aragutin", "Aušan"), д/л as а ("Mlaaenović", "Fiaipović"), о as ° ("A°brivoje"), г as т
    ("Miodrat"), Ђ as Б or В and ђ as ћ ("Borće", "Vorbević")."""
    ref = name_counts()
    counts = {k: ref[k] + Counter(s[k] for s in soldiers) for k in ref}   # and names read cleanly in these lists
    changed = 0
    for s in soldiers:
        for k in counts:
            v = s[k]
            # known elsewhere; a misread printed the same in both lists ("Aušan") or in another book counts little
            if not v or ref[k][v] >= 3:
                continue
            spots = [i for i, ch in enumerate(v) if ch in CONFUSIONS]
            best = None
            for n in (1, 2):
                for combo in itertools.combinations(spots, n):
                    for repl in itertools.product(*(CONFUSIONS[v[i]] for i in combo)):
                        cand = list(v)
                        for i, r in zip(combo, repl):
                            cand[i] = r
                        cand = ''.join(cand)
                        if counts[k][cand] >= max(2, 5 * counts[k][v]) and (best is None or counts[k][cand] > best[0]):
                            best = (counts[k][cand], cand)
                if best:
                    break
            if best:
                s[k] = best[1]
                changed += 1
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    print(f'  repaired {changed} names by the scan\'s usual misreads')
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(ic_endings(soldiers), ik_is_ic=True)))
    return ocr_confusions(soldiers)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/25-srpska-brigada.pdf',
        brigade_code=31,
        output_path=OUTPUT,
        start_page=2,
        end_page=21,
        layout='single',
        script='cyrillic',
        entry_start_re=ENTRY_START,
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        post_fn=post,
    )
