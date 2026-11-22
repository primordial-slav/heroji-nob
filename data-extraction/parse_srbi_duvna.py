"""
*Srbi Duvna, život i stradanja* (Poreklo library, doc a6066c5f.../00003619), a book across units: three of its lists of
Duvno's (Tomislavgrad's) fighters, in Latin:

    "Borci bitke na Sutjesci rodom iz Duvna" (scan pp. 276-284, two columns), from Viktor Kučan's *Borci Sutjeske*:
        "BILANOVIĆ Bože LUKA, desetar u 4. bataljonu, rođen 1925, Mandino Selo, Duvno, zemljoradnik, Srbin, u NOB od
        1942, član SKOJ-a, poginuo na Sutjesci kod Tjentišta 13. juna 1943 godine" (the Serbs, Muslims and Croats).
    "Popis oficira i podoficira koji su bili u NOV-u prema registru SUBNOR-a" (pp. 324-325): "Karan, Božin, Marko,
        1914. (1. 11. 1941), poručnik", the father as a possessive.
    "Poginuli Srbi iz Duvna u NOR-u 1941-1945" (tables 31 and 33, pp. 328-331), by village: "3 Vuković Miloša Bogdo
        1910 Jan—43 Sutjeska borac 5. proleterske brig."

A man in two or three of the lists is one entry, the other lists' lines added to it (same surname and given name, the
father agreeing whatever his case). The brigade headings over the Sutjeska list are not taken: the columns run so that
which entries a heading covers can't be told from the text.

The OCR reads M as "IVI" or "lVl", I as l in the capitals ("MlLlCA MlKA"), Đ as D ("Dorđa", "DORDE"), and sets a few
table rows in Cyrillic ("Simić Милоша Јованка", "Ljy6o").

Output: data-extraction/poreklo/srbi-duvna-entries.json (IDs 9118xxxxxx: the Sutjeska fighters from 000001 in the
list's order, the fallen of the tables no Sutjeska entry names from 001001 by their number, the officers no other list
names from 002001).
Usage: python data-extraction/parse_srbi_duvna.py
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
import _village_books as V  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import load, page_lines, page_words, viewer_url  # noqa: E402

BOOK = 'srbi-duvna.json'
OUT = HERE / 'poreklo' / 'srbi-duvna-entries.json'
PREFIX = '9118'
OFFSET = -93                                 # scan page minus the book's page (scan 276 is p. 369)
TITLE = 'Srbi Duvna, život i stradanja'
SUTJESKA = 'Borci bitke na Sutjesci rodom iz Duvna'
OFFICERS = 'Popis oficira i podoficira koji su bili u NOV-u prema registru SUBNOR-a'
FALLEN = 'Poginuli Srbi iz Duvna u NOR-u 1941–1945'
UP = 'A-ZČĆŽŠĐ'
LOW = 'a-zčćžšđ'
VILLAGE = {'Duvna': 'Duvno', 'grada Duvna': 'Duvno', 'Eminova Sela': 'Eminovo Selo', 'Mokronogu': 'Mokronoge',
           'Oplećana': 'Oplećani', 'Kongom': 'Kongora', 'Kongore': 'Kongora', 'Mandina Sela': 'Mandino Selo',
           'Rašćana': 'Rašćani', 'Srđana': 'Srđani', 'Baljaka': 'Baljci'}


def fix(t: str) -> str:
    t = latin(t) if re.search('[А-Яа-я]', t) else t
    t = t.replace('IVI', 'M').replace('lVl', 'M').replace('Ljy6', 'Ljub').replace('*', '')
    t = t.replace('I<o', 'KO').replace('BORISA-', 'BORIŠA-')                        # "MARI<o", Boriša
    t = re.sub(r'\bl(?=[A-ZČĆŽŠĐ]{2})', 'I', t)                                     # "lVAN"
    t = re.sub(r'\b([A-ZČĆŽŠĐ]+)l([A-ZČĆŽŠĐl]*)\b', lambda m: (m.group(1) + 'I' + m.group(2)).replace('l', 'I'), t)
    t = re.sub(r'\bDor(?=đ)', 'Đor', t)
    t = re.sub(r'\bDur(?=[aeo]\b)', 'Đur', t)
    t = re.sub(r'\bDORDE\b', 'ĐORĐE', t).replace('DOKO', 'ĐOKO')
    t = re.sub(r'(?<=[a-z])H\b', 'n', t).replace('Manojlovih', 'Manojlović')     # "SlobodaH", "LjubaH"
    return t


def title(w: str) -> str:
    return '-'.join(p[:1].upper() + p[1:].lower() for p in w.split('-')).replace('Lj', 'Lj').replace('Nj', 'Nj')


def fold(s: str) -> str:
    return re.sub(r'[^a-z]', '', (s or '').translate(str.maketrans('čćžšđČĆŽŠĐ', 'cczsdCCZSD')).lower())


def father_stem(f: str) -> str:
    """the father's name without its case: Bože, Božin, Božo; Marka, Markov, Marko"""
    f = fold(f)
    return re.sub(r'(?:ina|ova|eva|in|ov|ev|a|e|o)$', '', f) if len(f) > 3 else f


def lines(book: dict, pages, columns: int):
    for page in pages:
        for col in page_lines(book, page, columns):
            for l in col:
                t = fix(l.text.strip())
                if t and not re.fullmatch(r'\d{3}', t):
                    yield page, t


START = re.compile(rf'^([{UP}][{UP}{LOW}]*(?:-[{UP}][{UP}{LOW}]*)?)\s+(?:([{UP}][{LOW}]+)\s+)?'
                   rf'([{UP}][{UP}j]+(?:[\s-]+[{UP}][{UP}{LOW}j]+)*|[{UP}][{LOW}]+)\s*,\s*(.*)$')


def sutjeska(book: dict) -> list[dict]:
    raw = []
    for page, t in lines(book, range(276, 285), 2):
        if re.fullmatch(rf'[{UP} ()]+', t) and len(t) > 8 and not raw[-1:] == [] and ' ' in t:
            continue                                                   # a brigade's heading
        m = START.match(t)
        if m and (m.group(1).isupper() or m.group(3).isupper()):
            raw.append({'page': page, 'g': list(m.groups()[:3]), 'text': m.group(4)})
        elif raw:
            raw[-1]['text'] += ' ' + t
    out = []
    for i, r in enumerate(raw, 1):
        last, fath, given = r['g']
        fath = fath or ''
        gwords = re.split(r'[\s-]+', given)
        nick = ' '.join(title(w) for w in gwords[1:])
        info = re.sub(r'\s+', ' ', r['text']).strip(' ,.')
        d = V.death(info)
        if d.get('year') and int(d['year']) > 1945:                   # "Umro 20. jula 1995. godine": after the war
            d = {}
        fell = bool(d.get('year')) or bool(re.search(r'pogin|strijelj|ubijen|nestao', info, re.I))
        born = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
        printed = ' '.join(x for x in (title(last), fath, title(gwords[0])) if x)
        e = {'soldier_id': f'{PREFIX}{i:06d}', 'last_name': title(last), 'first_name': title(gwords[0]),
             'nick': nick, 'fathers_name': fath, 'birth_year': born.group(1) if born else '',
             'born_in': V.born_in(info, 'Duvno'), 'death_year': d.get('year', ''),
             **({'death_date': d['date']} if d.get('date') else {}),
             **({'death_place': d['place']} if d.get('place') else {}),
             'survived': not fell, 'units': V.units_of(info),
             'text': [f"{SUTJESKA}: {printed}{' – ' + nick if nick else ''}, {info}."],
             'list': SUTJESKA, 'page': r['page']}
        out.append(e)
    return out


TABLE = re.compile(rf'^(?:(\d{{1,2}})\s+)?([{UP}][{LOW}]+(?:-[{UP}][{LOW}]+)?)\s+([{UP}][{LOW}]+)\s+([{UP}][{LOW}]+)\s*\|?\s*'
                   r'(1[89]\d\d)\s*\|?\s*(.*)$')


def fallen(book: dict) -> list[dict]:
    out, village = [], 'Duvno'
    on = False
    for page, t in lines(book, range(328, 332), 1):
        if 'POGINULI SRBI' in t:
            on = True
            continue
        if not on:
            continue
        if t.startswith('Korišteni izvori'):
            break
        mv = re.match(r'^Iz\s+(?:sela\s+|grada\s+)?(.+)$', t)
        if mv:
            village = VILLAGE.get(mv.group(1).strip(), mv.group(1).strip())
            continue
        m = TABLE.match(t)
        if not m:
            continue
        no, last, fath, given, born, rest = m.groups()
        rest = rest.replace('|', ' ')
        dm = re.match(r'^(?:([A-Za-z]{3}|\d{1,2})\s*[.—–-]\s*)?(?:19)?(\d\d)\.?\s*[—–-]?\s*(.*)$', rest)
        year = '19' + dm.group(2) if dm else ''
        tail = dm.group(3) if dm else rest
        um = re.search(r'\s(borac|bolničarka|kom\.|komandir|kapetan|Komanda|Koman\.|NOR)', ' ' + tail)
        place = tail[:um.start() - 1].strip() if um else tail.strip()
        duty = tail[um.start() - 1:].strip() if um else ''
        info = f"{FALLEN}, {village}: {no + '. ' if no else ''}{last} {fath} {given}, {born}, {rest.strip()}."
        out.append({'no': int(no) if no else None, 'last_name': last, 'first_name': given, 'nick': '',
                    'fathers_name': fath, 'birth_year': born, 'born_in': f'{village}, Duvno', 'death_year': year,
                    **({'death_place': place} if place and place != 'Nepoznato' else {}), 'survived': False,
                    'units': V.units_of(duty.replace('brig.', 'brigade')), 'text': [info], 'list': FALLEN,
                    'page': page})
    for i, e in enumerate(out):                                        # the rows the OCR printed without their number
        if e['no'] is None:
            e['no'] = (out[i - 1]['no'] or 0) + 1 if i else 1
    return out


OFFICER = re.compile(rf'^([{UP}][{LOW}]+),\s*((?:rođ\.\s*)?[{UP}][{LOW}]+),\s*([{UP}][{LOW}]+(?:\s*[—–-]\s*[{UP}][{LOW}]+)?)\s*,?\s*(1[89]\d\d)\.?\s*'
                     r'\(([^)]*)\)\s*,?\s*(.*)$')


def officers(book: dict) -> list[dict]:
    out, nation, on = [], '', False
    for page, t in lines(book, [324, 325], 1):
        if t.startswith('Popis oficira'):
            on = True
            continue
        if not on:
            continue
        if t.startswith('Da bi slika'):
            break
        if t.rstrip(':') in ('Srbi', 'Muslimani', 'Hrvati'):
            nation = t.rstrip(':')
            continue
        m = OFFICER.match(t)
        if not m:
            print('   officer unread:', page, t[:90])
            continue
        last, fath, given, born, joined, rank = m.groups()
        parts = re.split(r'\s*[—–-]\s*', given, maxsplit=1)               # "Kasim —Žaka"
        given, nick = parts[0], (parts[1] if len(parts) > 1 else '')
        rank = rank.strip(' .,“"0')
        maiden = fath.startswith('rođ.')
        info = f"{OFFICERS}, {nation}: {last}, {fath}, {given}, {born}. ({joined.strip()}){', ' + rank if rank else ''}."
        out.append({'last_name': last, 'first_name': given, 'nick': nick, 'fathers_name': '' if maiden else fath,
                    'birth_year': born, 'born_in': '', 'death_year': '', 'survived': True, 'units': [],
                    'text': [info], 'list': OFFICERS, 'page': page,
                    **({'also': [fath.split()[-1]]} if maiden else {})})
    return out


def same(a: dict, b: dict) -> bool:
    if fold(a['last_name']) != fold(b['last_name']) and not set(fold(x) for x in a['last_name'].split('-')) & \
            set(fold(x) for x in b['last_name'].split('-')):
        return False
    if fold(a['first_name']) != fold(b['first_name']):
        return False
    fa, fb = father_stem(a['fathers_name']), father_stem(b['fathers_name'])
    if fa and fb and fa != fb:
        return False
    ya, yb = a.get('birth_year'), b.get('birth_year')
    da, db = a.get('death_year'), b.get('death_year')
    room = 5 if da and db and da == db else 2                 # the table's year of birth is loose (Draško Marka Marko)
    return not (ya and yb and abs(int(ya) - int(yb)) > room)


def main():
    V.corpus()
    book = load(BOOK)
    entries = sutjeska(book)
    counts = Counter({'sutjeska': len(entries)})
    for group, base in ((fallen(book), 1000), (officers(book), 2000)):
        n = 0
        for e in group:
            hit = next((x for x in entries if same(x, e)), None)
            if hit:
                hit['text'] += e['text']
                for k in ('birth_year', 'death_year', 'death_place', 'born_in'):
                    if not hit.get(k) and e.get(k):
                        hit[k] = e[k]
                if e['list'] == FALLEN:
                    hit['survived'] = False
                hit['units'] = sorted(set(hit['units']) | set(e['units']))
                counts[f"{e['list'][:20]} joined"] += 1
                continue
            n = e['no'] if e['list'] == FALLEN else n + 1
            e['soldier_id'] = f'{PREFIX}{base + n:06d}'
            entries.append(e)
            counts[e['list'][:20]] += 1
    out = []
    for e in sorted(entries, key=lambda e: e['soldier_id']):
        page = e.pop('page')
        name = ' '.join(x for x in (e['last_name'], e['fathers_name'], e['first_name']) if x)
        rec = {'soldier_id': e['soldier_id'], 'name': name, 'last_name': e['last_name'], 'also': e.get('also', []),
               'first_name': e['first_name'], 'nick': e['nick'], 'fathers_name': e['fathers_name'],
               'birth_year': e['birth_year'], 'born_in': e['born_in'], 'death_year': e['death_year'],
               **({'death_date': e['death_date']} if e.get('death_date') else {}),
               **({'death_place': e['death_place']} if e.get('death_place') else {}),
               'survived': e['survived'], 'units': e['units'], 'additional_info': ' '.join(e['text']),
               'list': e['list'], 'book_title': TITLE, 'source_url': viewer_url(book, page), 'source_page': page - OFFSET}
        out.append(rec)
    dup = [k for k, n in Counter(e['soldier_id'] for e in out).items() if n > 1]
    assert not dup, dup
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts))
    for e in out:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['birth_year']} {e['born_in']} | {e['death_year']} "
              f"{e.get('death_place', '')} {e['units']} {'' if not e['survived'] else 'survived'} | "
              f"{e['additional_info'][:70]}")


if __name__ == '__main__':
    main()
