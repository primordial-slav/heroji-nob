"""
*Od ustanka do pobjede: zbornik sjećanja učesnika NOR-a i socijalističke revolucije na dobojskoj opštini*, knjiga III
(Doboj 1986, ed. Rizah Biser; doc 00006946 of the Poreklo library), a book across units: "Poginuli borci narodno-
oslobodilačkog rata" (book pp. 366-422, scan 370-426), the Doboj municipality's 637 fighters who fell, by village
under its heading in capitals, an entry each, the first line indented:

    "AVDAKOVIČ Ibrahima ALIJA, 1920, Klokotnica, Doboj, Musliman, zemljoradnik, u NOB-u od oktobra 1943, u 18.
    hrvatskoj NOU brigadi, kao zamjenik komandira čete poginuo u jesen 1944. kod Caglina, Slavonija;"

The surname and the given name in capitals, the father in the genitive, the birth year, village and općina,
nationality, trade, when he joined the NOB, the units and how and where he fell. The insurgents of 23 August 1941
the enemy shot ("kao ustanik strijeljan") are the list's fighters too. The list of the victims of fascist terror
after it (from scan p. 427) stays out.

The OCR reads -ić as -ič and loses carons in capitals ("VASILIČ", "PETROVIC"): the names come back as the site
spells them (`spell`).

Output: data-extraction/poreklo/doboj3-entries.json (IDs 9111xxxxxx, in the list's order).
Usage: python data-extraction/parse_doboj.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import _village_books as vb  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'doboj3.json'
OUT = HERE / 'poreklo' / 'doboj3-entries.json'
PREFIX = '9111'
OFFSET = 4                                   # scan page minus the book's page
PAGES = range(370, 427)
TITLE = 'Od ustanka do pobjede: zbornik sjećanja učesnika NOR-a i socijalističke revolucije na dobojskoj opštini, knjiga III'
LIST = 'Poginuli borci narodnooslobodilačkog rata'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# an entry's first line: the surname in capitals (two joined by a hyphen), the father, the given name in capitals,
# a nickname after a dash, and the birth year after a comma
START = re.compile(
    rf"^'?\s*([{U}][{U}' ]*[{U}](?:\s*[-–—]\s*[{U}][{U}]+)?)"                  # the surname, spaced out by the OCR at times
    rf"(?:\s+(?:ž\.\s*)?([{U}]?[{L}]+))?"                                       # the father ("petra"; a wife's "ž. Stojke")
    rf"[,.]?\s+([{U}][{U}]+[a-z]?(?:\s+'?[{U}][{U}]+[a-z]?)*|[{U}][{L}]+)"       # the given name ("DORDo", "Mustafa")
    rf"(?:\s*[-–—]\s*([{U}][{U}{L}]+))?"                                       # a nickname
    rf"\s*[,.]\s*(?:(1[89]\d\d|\?)|(?=[{U}][{L}])|(?=[,.]?$))")                           # the birth year, or the village
GLUED = re.compile(rf";\s*'?\s*(?=[{U}][{U} ]+[{U}]\s+(?:ž\.\s*)?[{U}]?[{L}]+\s+[{U}]|[{U}]{{3,}}\s+[{U}]{{3,}}\s*,)")
FOOTER = re.compile(r"\d*\s*[CO0]D\s+USTANKA\s+\S+\s+POBJEDE\s*\d*\.?|(?:^|(?<=[;.]))\s*[\w']{0,3}\s*\d{3}\.?\s*$")


def caps_fixed(t: str) -> str:
    """the OCR's l for I in a word in capitals ("AHlVIED", "VIDOVlČ"), and a capital it set apart ("N URKO")"""
    t = re.sub(r"\b[A-ZČĆŽŠĐl]{3,}\b", lambda m: m.group(0).replace('l', 'I')
               if sum(c.isupper() for c in m.group(0)) >= 2 else m.group(0), t)
    return re.sub(r"\b([A-ZČĆŽŠĐ]) ([A-ZČĆŽŠĐ]{2,})\b", r"\1\2", t)


# the OCR's slips past the rules: Omer lost his O, Pajić's JI read as a Cyrillic Л
FIX = {'Saliha mer': 'Saliha OMER', 'PAЛC': 'PAJIĆ'}
HEADING = re.compile(rf'^[{U} ]{{4,}}$')
LATIN = str.maketrans({'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C',
                       'Т': 'T', 'Х': 'X', 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'u', 'х': 'x',
                       'т': 'm', 'Ј': 'J', 'ј': 'j', '»': '»', '<': '«'})


def spell(word: str, part: str) -> str:
    """the site's spelling of a name in capitals: the OCR sets -ić as -ič and drops carons, so the spelling the site
    has most often of these letters, carons aside; a name the site lacks keeps its letters, -ič and -ic as -ić"""
    w = word.replace("'", '')
    c = ofz._spell[part].get(w.translate(ofz.FOLD))
    if c and sum(c.values()) >= 2:
        return kl.title(c.most_common(1)[0][0])
    return kl.title(re.sub(r'I[ČC]$', 'IĆ', w))


def given_name(caps: str) -> str:
    """a given name in capitals, which the OCR may break ("BOGOLJ UB"): joined where the site knows it so"""
    words = caps.split()
    joined = ''.join(words)
    if len(words) > 1 and ofz.known(joined, 'first')[0] >= 3:
        return spell(joined, 'first')
    return ' '.join(spell(w, 'first') for w in words)


def fix_father(f: str) -> str:
    """a father whose Đ the OCR read as D ("Dorđa", "Dure")"""
    f = re.sub(r'^Dor(?=đ)', 'Đor', f)
    f = re.sub(r'^Dur(?=đ|[oaei]$)', 'Đur', f)
    return re.sub(r'^Duk(?=[aoe]$)', 'Đuk', f)


def village_name(heading: str, born: list[str]) -> str:
    """the heading over an entry, in the spelling of the villages its entries name ("STA N ARI" = Stanari)"""
    flat = re.sub(r'[^A-Z]', '', heading.upper().translate(ofz.FOLD))
    for b in born:
        if re.sub(r'[^A-Z]', '', b.upper().translate(ofz.FOLD)) == flat:
            return b
    return kl.place(heading)


def text_of(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[—–-]$', text) and re.match(rf'[{L}]', ln):
            text = re.sub(r'\s*[—–-]$', '', text) + ln
        else:
            text += (' ' if text else '') + ln
    text = text.translate(LATIN).replace('NOB—u', 'NOB-u').replace('NOVJ—a', 'NOVJ-a').replace('„', ',')
    text = re.sub(r'\b([{U}][{L}]+)ič\b'.format(U=U, L=L), r'\1ić', text)       # "Radič", "Petrovič": -ić
    text = re.sub(r'(?<=\w)\s*—\s*(?=\w)', '-', text)
    text = re.sub(r'(?<=[a-zčćžšđ])1(?=[a-zčćžšđ])', 'l', text)                # "Prnjavor Ma1i"
    return re.sub(r'\s+', ' ', text).strip(' ;.') + '.'


def raw_entries(book: dict) -> list[dict]:
    entries, village = [], ''
    for page in PAGES:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if not t or re.fullmatch(r'\d{3}', t) or t.startswith(('POGINULI BORCI', 'NARODNOOSLOBODILA', 'RATA')):
                continue
            t = t.replace('·', '').replace('"', '').translate(LATIN).strip()
            for a, b in FIX.items():
                t = t.replace(a, b)
            t = caps_fixed(FOOTER.sub('', t)).strip()
            if not t or t in ("'.", ',.', '.'):
                continue
            for seg in GLUED.split(t):
                seg = seg.strip()
                head = re.match(rf'^(.*?)(?:\s*\d{{0,3}}\s+\d{{3}})\s+([{U} ]{{4,}})\.?$', seg)
                if head and head.group(1) and entries:          # "... Ljeskovim Vodama. 27 419 TRNJANI."
                    entries[-1]['lines'].append(head.group(1))
                    village = head.group(2)
                    continue
                tail = re.match(rf'^(.*[;.])\s+([{U}][{U} ]{{3,}}[{U}])\.?$', seg)
                if tail and entries and 'HEROJ' not in tail.group(2):    # "... u Kreki, Tuzla; BRIJESNICA MALA."
                    entries[-1]['lines'].append(tail.group(1))
                    village = tail.group(2)
                    continue
                if START.match(seg):
                    entries.append({'village': village, 'page': page, 'lines': [seg]})
                    continue
                if HEADING.match(seg) and (not entries or entries[-1]['lines'][-1].rstrip().endswith(('.', ';'))):
                    village = seg
                    continue
                if entries:
                    entries[-1]['lines'].append(seg)
    return entries


def main():
    ofz.corpus()
    vb.corpus()
    book = load(BOOK)
    out, counts = [], Counter()
    raw = raw_entries(book)
    villages = {}                               # each heading's villages, as its entries print them
    for e in raw:
        v = re.match(r'[^,]*,\s*[^,]*,\s*([^,]+),', ' '.join(e['lines']))
        villages.setdefault(e['village'], []).append(v.group(1).strip() if v else '')
    for no, e in enumerate(raw, 1):
        first_line = e['lines'][0]
        m = START.match(first_line)
        caps, fath, given, nick, year = m.groups()
        surnames = [spell(w.replace(' ', '').replace("'", ''), 'last') for w in re.split(r'\s*[-–—]\s*', caps)]
        last = '-'.join(surnames)
        first = given_name(given.upper())
        fath = fix_father(fath.split()[0]) if fath else ''
        body = text_of([first_line[m.end():]] + e['lines'][1:]).lstrip(', ')
        place = re.match(r'([^,]+),\s*([^,]+),', body)
        born_in = ''
        if place:                               # "Kladari, Doboj"; a town alone, then the nationality: "Doboj, Jevrej"
            born_in = place.group(1).strip() + ('' if vb.ETHNIC.match(place.group(2).strip())
                                                else f', {place.group(2).strip()}')
        info = f"{' '.join(x for x in (last, fath, first) if x)}{' — ' + kl.title(nick) if nick else ''}, {year + ', ' if year else ''}{body}"
        role = vb.role(info)
        if role == 'out':                      # the list titles them all fallen fighters: the insurgents of 23 August
            role = 'activist' if re.search(r'\brad\w* za NOP', info) else None     # 1941 ("kao ustanik"); not
                                                                                    # Turkić Hamza's work for the NOP
        d = vb.death(info)
        rec = {
            'soldier_id': f'{PREFIX}{no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
            'last_name': last, 'first_name': first, 'nick': kl.title(nick) if nick else '', 'fathers_name': fath,
            'also': [], 'birth_year': year if year and year != '?' else '', 'born_in': born_in,
            'death_year': d.get('year', ''),
            **({'death_date': d['date']} if d.get('date') else {}),
            **({'death_place': d['place']} if d.get('place') else {}),
            'survived': False, 'units': vb.units_of(info),
            **({'role': role} if role else {}),
            'additional_info': f"{LIST}, {village_name(e['village'], villages[e['village']])}: {info}",
            'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, e['page']), 'source_page': e['page'] - OFFSET,
        }
        out.append(rec)
        counts[role or 'fighter'] += 1
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts))
    print(Counter(u for r in out for u in r['units']).most_common(20))
    if '--sample' in sys.argv:
        random.seed(5)
        for r in random.sample(out, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(out))):
            print(f"  {r['soldier_id']} {r['name']} | {r['birth_year']} [{r['born_in']}] † {r['death_year']} "
                  f"{r.get('death_place', '')!r} {r.get('role', '')} {r['units']} | {r['additional_info'][:160]}")


if __name__ == '__main__':
    main()
