"""
*Kordunski rekvijem* (doc 00003071 of the Poreklo library), a book across units, two of its lists:
    "Pali borci općine Primišlje 1941—1945." (scan pp. 177-191), the fallen of the old Primišlje općina by village
        (Gornje Primišlje, Tržić Primišljanski, Donje Primišlje, Tounjski Tržić, Tobolić, Vrelo Mrežnice i Tuk, Zbjeg i
        Mrzlo Polje), numbered within each, three columns a page, a short bio each: "1. Batalo Sime Đuro, rođen 1914, u
        NOV od 1942, borac brigade 8. divizije, poginuo 1942. u Sisku;". Dušan Livada's list, as the plaque in Primišlje
        counts them: fighters, party and SKOJ members, the people's committees and the AFŽ, so only fighters go in
        (`_village_books.role`) and the movement's other people are activists;
    "Nosioci Partizanske spomenice 1941. godine kolonizirani iz Slunja" (scan pp. 338-347), the holders who settled in
        Čonoplja and Kljajićevo, after Kozin's Zbornik of the Sombor SUBNOR (1971), a bio each under the numbered name.
        (Its pages after 342 were fetched on 2026-10-28, the morning after the rest.)

The OCR reads Đ as D ("Dure", "Durđa") or in Cyrillic look-alikes ("Виго" Đuro), J as "]", u as "и" or "11", and
loses the Zb of Zbjeg ("ijeg"): the names are read back from the site's spellings (`_karlovac_lists.spelled`).

Output: data-extraction/poreklo/kordunski-rekvijem-entries.json (IDs 9105xxxxxx: the fallen from 000001, the
spomenica holders from 001001, in the book's order).
Usage: python data-extraction/parse_kordunski_rekvijem.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _karlovac_lists as kl  # noqa: E402
import _village_books as V  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'kordunski-rekvijem.json'
OUT = HERE / 'poreklo' / 'kordunski-rekvijem-entries.json'
PREFIX = '9105'
OFFSET = 0                                          # the scan's page is the book's
TITLE = 'Kordunski rekvijem'
FALLEN = ('Pali borci općine Primišlje 1941—1945.', range(177, 192))
SPOMENICA = ('Nosioci Partizanske spomenice 1941. godine kolonizirani iz Slunja', range(338, 348))
COLUMNS = (0, 1550, 2660)
# the villages' headings as the OCR has them, and the place each is (the census's općina)
VILLAGES = {'Gornje Primišlje': ('Gornje Primišlje', 'Slunj'), 'Tržič Primišljanski': ('Tržić Primišljanski', 'Slunj'),
            'Donje Primišlje': ('Donje Primišlje', 'Slunj'), 'Tounjski Tržič': ('Tounjski Tržić', 'Ogulin'),
            'TbboHč': ('Tobolić', 'Slunj'), 'Vrelo Mrežnice i Tuk': ('Vrelo Mrežnice i Tuk', ''),
            'ijeg i Mrzlo Polje': ('Zbjeg i Mrzlo Polje', 'Slunj')}
START = re.compile(r'^(\d{1,2})\s*\.\s*(?=[A-ZČĆŽŠĐ\]]|Виг|AdŽ)')
# Cyrillic letters the OCR set for the Latin they look like, and its other slips in the text
CYR = str.maketrans('иогаесрк', 'uoraecpk')


def text_of(t: str) -> str:
    t = re.sub(r'\bВиг(?=[a-zоеа])', 'Đur', t)                     # "Виго", "Виге": Đuro, Đure
    t = re.sub(r'[а-я]+', lambda m: m.group(0).translate(CYR), t)
    t = t.replace(']', 'J').replace('—', '-').replace('–', '-')
    t = re.sub(r'(?<=\d\.) 11 (?=[A-ZČĆŽŠĐ])|(?<=\d\.)11 (?=[A-ZČĆŽŠĐ])', ' u ', t)   # "1944. 11 Dubravi"
    t = re.sub(r'\bu ijeg', 'u Zbjeg', t)
    t = re.sub(r'\b(19[34]\d)3\b', r'\1', t)                        # "umro od tifusa 19433": the ; read as 3
    t = re.sub(r'poginuol(9[34]\d)', r'poginuo 1\1', t)                # "poginuol945."
    t = re.sub(r'(\w)- (?=[a-zčćžšđ])', r'\1', t)                   # "pogi- nuo", "Pe- tar"
    t = re.sub(r'(\w)- (?=[A-ZČĆŽŠĐ]\w*[a-zčćžšđ])', r'\1-', t)     # "Gornjo-primišljanskog" stays joined
    return re.sub(r'\s+', ' ', t).strip()


# names past the rules, read from the list's order and the brothers beside them
READ = {'Rafaan': 'Rafajla', 'Soflja': 'Sofija', 'Saša': 'Šaša', 'llije': 'Ilije', 'Durana': 'Đurana', 'Dura': 'Đura',
        'anatija': 'Ignatija'}


def given(w: str) -> str:
    """a given name or father: Đ where the OCR read it as D ("Dure", "Durana") and the site has it with Đ"""
    w = kl.spelled(READ.get(w, w), 'first')
    if w.startswith('D') and V.T._given[('Đ' + w[1:]).upper()] > 3 * V.T._given[w.upper()]:
        return 'Đ' + w[1:]
    return w


def name_of(head: str) -> tuple[str, str, str]:
    """"Batalo Sime Đuro": surname, the father in the genitive, the given name, in the site's spellings"""
    head = re.sub(r'\b(Lj|Ignjatij) (?=[a-z])', r'\1', head)          # "Lj evanić", "Ignjatij e"
    words = [READ.get(w, w) for w in re.split(r'[\s,]+', head) if w]
    if len(words) < 2:
        return (kl.spelled(words[0], 'last') if words else '', '', '')
    sur = lambda w: re.sub(r'ič$', 'ić', kl.spelled(w, 'last'))        # "Bjelopetrovič"
    if len(words) == 2:
        return sur(words[0]), '', given(words[1])
    return ' '.join(sur(w) for w in words[:-2]), given(words[-2]), given(words[-1])


def column_lines(book: dict, page: int) -> list[str]:
    ws = page_words(book, page)
    out = []
    for lo, hi in zip(COLUMNS, COLUMNS[1:] + (99999,)):
        for l in level_lines([w for w in ws if lo <= w.x0 < hi]):
            t = l.text.strip()
            if re.match(r'^\(\d{2,3}\)\s*[A-ZČĆŽŠ]', t):                # a footnote ends the column
                break
            out.append(t)
    return out


def fallen(book: dict) -> list[dict]:
    title, pages = FALLEN
    entries, village, cur = [], ('', ''), None
    for page in pages:
        for t in column_lines(book, page):
            if re.match(r'^(\d{3}\s+Kordunski|Kordun|borbi, 1941|П\.|II\.\s*Kordun)', t) or re.search(r'rekvijem$', t):
                continue                                                # the running heads
            if t.startswith('(Izvor'):
                return entries
            if t in VILLAGES:
                village, cur = VILLAGES[t], None
                continue
            m = START.match(t)
            if m:
                cur = {'no': int(m.group(1)), 'village': village, 'page': page, 'lines': [t[m.end():]]}
                entries.append(cur)
            elif cur:
                cur['lines'].append(t)
    return entries


def spomenica(book: dict) -> list[dict]:
    entries, cur = [], None
    for page in SPOMENICA[1]:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.match(r'^\(\d{3}\)|^\d{3}\s+Kordunski|^III\.\s*Kordun|^Nosioci|^Slunja', t):
                if t.startswith('(1'):
                    cur = None                                         # the footnote under the title
                continue
            m = re.match(r'^(\d{1,3})\.\s+(\S.*)$', t)
            if m and not re.search(r'\d{4}', m.group(2)) and (not entries or int(m.group(1)) == entries[-1]['no'] + 1):
                cur = {'no': int(m.group(1)), 'page': page, 'head': m.group(2), 'lines': []}
                entries.append(cur)
            elif cur:
                cur['lines'].append(t)
    return entries


def main():
    ofz.corpus()
    V.corpus()
    book = load(BOOK)
    out, counts, roles = [], Counter(), Counter()
    for no, e in enumerate(fallen(book), 1):
        text = text_of(' '.join(e['lines']))
        head = re.split(r',?\s*(?:ro-?\s?đen|rođ|ro-|stupio|učestvovao|\(|kandidat)', text, 1)[0]
        last, fath, first = name_of(head)
        rest = text[len(head):].lstrip(' ,').rstrip(' ;.')
        role = V.role(rest)
        if role == 'out' and re.search(r'učestvovao u ustanku', rest):
            role = None                                                 # an insurgent of 30 July 1941
        elif role == 'out' and re.search(r'kandidat KP', rest):
            role = 'activist'                                           # a party candidate the Ustaše killed
        if role == 'out':
            counts['out'] += 1
            print('  out:', e['no'], head, '|', rest[:120])
            continue
        vil, opc = e['village']
        born = re.search(r'ro\s?đen[a]?\s+(1[89]\d\d)', rest)
        d = V.death(rest)
        units = V.units_of(rest)
        if re.search(r'8\.\s*divizij', rest) and 60 not in units:
            units.append(60)                                            # the 8. kordunaška divizija
        rec = {'soldier_id': f'{PREFIX}{no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
               'last_name': last, 'also': [], 'first_name': first, 'nick': '', 'fathers_name': fath,
               'birth_year': born.group(1) if born else '', 'born_in': ', '.join(x for x in (vil, opc) if x),
               'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
               **({'death_place': 'Srem' if d['place'] == 'Sremskom' else d['place']} if d.get('place') else {}),
               'survived': False, 'units': units,
               'list': FALLEN[0], 'book_title': TITLE, 'source_url': viewer_url(book, e['page']),
               'source_page': e['page'] - OFFSET,
               'additional_info': f"{FALLEN[0]}, {vil}: {e['no']}. {last} {fath} {first}, {rest}."}
        if role:
            rec['role'] = role
            roles[role] += 1
        out.append(rec)
        counts['fallen'] += 1
    for e in spomenica(book):
        last, fath, first = name_of(text_of(e['head']))
        bio = text_of(' '.join(e['lines']))
        born = re.search(r'(?:(\d{1,2})\.\s?(\d{1,2})\.\s?)?(1[89]\d\d)\.?\s*(?:godine\s+)?u\s+(?:selu\s+)?([^.]+?)\.', bio)
        rec = {'soldier_id': f'{PREFIX}{1000 + e["no"]:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
               'last_name': last, 'also': [], 'first_name': first, 'nick': '', 'fathers_name': fath,
               'birth_year': born.group(3) if born else '', 'born_in': '', 'death_year': '', 'survived': True,
               'units': [], 'list': SPOMENICA[0], 'book_title': TITLE, 'source_url': viewer_url(book, e['page']),
               'source_page': e['page'] - OFFSET,
               'additional_info': f"{SPOMENICA[0]}: {e['no']}. {last} {fath} {first}. {bio}"}
        out.append(rec)
        counts['spomenica'] += 1
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), dict(roles), '->', OUT.name, len(out))


if __name__ == '__main__':
    main()
