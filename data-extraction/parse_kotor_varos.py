"""
Opština Kotor-Varoš i Skender-Vakuf u NOB-u 1941-1945 (Poreklo library), as a book across units: its Prilozi.

    "Spisak poginulih, umrlih ili nestalih učesnika NOR-a 1941-1945. godine prema mjesnim udruženjima SUBNOR-a"
        of the Kotor-Varoš općina (scan pp. 333-344) and of the Skender-Vakuf općina (pp. 344-354), compiled by the
        two općinas' SUBNOR boards: two columns, under each village's heading in capitals (GRABOVICA, KOTOR-VAROŠ,
        MASLOVARE, ...), an entry each, the surname in capitals: "BOŽIĆ Branko, rođen 1908. godine u Grabovici.
        U NOVJ od 1941. godine kao borac Četvrtog krajiškog NOP odreda. Kao komandir čete poginuo 13. novembra 1941.
        godine u Borcima."
    "Spisak nosilaca partizanske spomenice 1941." (p. 357), the two općinas' holders, names alone (`SPOMENICA`,
        typed from the page: the OCR lost the left column's numbers and broke two names over lines).

The list counts the participants of the war who died: fighters, and the movement's people who were none ("Član
Sreskog NOO Kotor-Varoš, vijećnik ZAVNOBiH-a ... Umro juna 1944"; "Uhapšena u ljeto 1944. godine i ubijena u
logoru"). The fighters go in as such, the others by the mixed lists' rule (`_village_books.role`): the movement's
people marked `role: 'activist'`, and those the list names a participant with nothing more `role: 'participant'`.
The tables after the lists (p. 355-356, the fighters and victims by year and village) are numbers only.

The OCR loses the carons of the surnames in capitals ("BOZIC", "TICIC"); they come back from the site's names
(`_karlovac_lists.spelled`). A full-width village heading parts the page into bands, each read left column first.

Output: data-extraction/poreklo/kotor-varos-entries.json (IDs 9092xxxxxx: the fallen from 000001 in the list's
order, the spomenica holders from 001001 by the book's number).
Usage: python data-extraction/parse_kotor_varos.py [--sample N]
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
from poreklo_text import FOLD, load, page_words, viewer_url  # noqa: E402

BOOK = 'kotor-varos.json'
OUT = HERE / 'poreklo' / 'kotor-varos-entries.json'
PREFIX = '9092'
OFFSET = 0                                   # the scan's pages are the book's
TITLE = 'Opština Kotor-Varoš i Skender-Vakuf u NOB-u 1941-1945'
LIST = 'Spisak poginulih, umrlih ili nestalih učesnika NOR-a 1941-1945'
OPCINE = [(range(333, 345), 'Kotor-Varoš'), (range(344, 355), 'Skender-Vakuf')]
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# an entry's first line: the surname in capitals (two, a woman's: "PETRIĆ KAPOR"), the given name, a nickname or
# a second given name ("FIFIC Asim Mićo"), and a comma
START = re.compile(rf'^([{U}][{U}]+(?:[ -][{U}][{U}]+)?)\s+([{U}][{L}]+(?:\s+[{U}][{L}]+)?)\s*[,.]')
OWN = set()                                  # the book's own surnames (its spomenica list), filled in main()
SPOMENICA_TITLE = 'Spisak nosilaca partizanske spomenice 1941.'
SPOMENICA = {  # by the book's number; 1-21 the Kotor-Varoš općina, 22-36 Skender-Vakuf
    1: 'Arsenić Ljuboja', 2: 'Borić Duško', 3: 'Bubić Ankica', 4: 'Fazlić Galib', 5: 'Gajić Milenko',
    6: 'Hadžiselimović Nijaz', 7: 'Josipović Dušan', 8: 'Knežević Petar', 9: 'Lukrecija Jovo', 10: 'Marić Mile',
    11: 'Mirić Marović Bosa', 12: 'Panić Adam', 13: 'Petrić Nevenka', 14: 'Petrić Kapor Viktorija',
    15: 'Sautner Nedeljković Tatjana', 16: 'Trkulja Mile', 17: 'Tvrz Josip Pepi', 18: 'Vrljanović Jovo',
    19: 'Šugić Anastazija', 20: 'Šugić Evgenije', 21: 'Šugić Šećer',
    22: 'Babić Petar', 23: 'Dukić Mirko', 24: 'Dukić Nikola', 25: 'Đenić Vid', 26: 'Dukarić Srećo',
    27: 'Marić Đuro', 28: 'Marić Vladimir', 29: 'Miljić Savo', 30: 'Pavlović Mihajlo', 31: 'Podgorac Kukolj Živka',
    32: 'Radulić Đorđo', 33: 'Radetić Luka', 34: 'Teinović Todor', 35: 'Tepić Marinko',
    36: 'Trkulja Crnomarković Jovanka'}


def heading(t: str) -> str:
    t = re.sub(r'\s*-\s*', '-', t.strip())
    if re.fullmatch(rf'[{U}][{U}\- ]{{3,}}', t) and not re.search(r'SPISAK|SUBNOR|POGINULIH|GODINE|NOR', t):
        return t
    return ''


def page_lines(book: dict, page: int) -> list:
    """the page's lines in reading order: bands between full-width headings, each band's left column first"""
    words = page_words(book, page)
    if not words:
        return []
    left, right = min(w.x0 for w in words), max(w.x1 for w in words)
    cut = min(range(int(left + (right - left) * 0.38), int(left + (right - left) * 0.62), 5),
              key=lambda x: sum(1 for w in words if w.x0 < x < w.x1))
    lines = level_lines(words)
    heads = [l for l in lines if heading(l.text) and l.x0 > left + (right - left) * 0.25 and l.x1 > cut]
    out = []
    bounds = [float('-inf')] + [h.top for h in heads] + [float('inf')]
    for i in range(len(bounds) - 1):
        band = [w for w in words if bounds[i] <= w.middle < bounds[i + 1]
                and not any(h.top - 1 <= w.middle <= h.bottom + 1 for h in heads)]
        if i:
            out.append(heads[i - 1])
        for side in (True, False):
            out += level_lines([w for w in band if ((w.x0 + w.x1) / 2 < cut) == side])
    return out


def raw_entries(book: dict) -> list[dict]:
    out, n = [], 0
    for pages, opcina in OPCINE:
        village, started = '', False
        for page in pages:
            for l in page_lines(book, page):
                t = l.text.strip()
                if 'SKENDER-VAKUF' in t.replace(' ', '') and 'OPSTINE' in t.replace('Š', 'S'):
                    if opcina == 'Kotor-Varoš':
                        started = False
                        break
                    started = True
                    continue
                if opcina == 'Kotor-Varoš' and 'KOTOR-VAROŠ' in t.replace(' ', '') and 'OPSTINE' in t.replace('Š', 'S'):
                    started = True
                    continue
                if not started:
                    if opcina == 'Kotor-Varoš' and page == 333 and heading(t) == 'GRABOVICA':
                        started = True
                    elif opcina == 'Skender-Vakuf' and heading(t) == 'BASTAJI':
                        started = True
                    else:
                        continue
                if re.fullmatch(r'\d{1,3}|\*.*|i Skender-Vakuf\.', t):
                    continue
                h = heading(t)
                if h:
                    village = h
                    continue
                m = START.match(t)
                if m and not re.fullmatch(r'NOP|NOVJ|SKOJ|KPJ|NOO|AFŽ', m.group(1)):
                    n += 1
                    out.append({'opcina': opcina, 'village': village, 'page': page, 'no': n, 'lines': [t]})
                elif out:
                    out[-1]['lines'].append(t)
            else:
                continue
            break
    return out


# the OCR sets a Cyrillic letter for its Latin look-alike now and then ("роginuo", "роčetka")
LATIN = str.maketrans('аеорсухАВЕКМНОРСТХ', 'aeopcyxABEKMHOPCTX')


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[—–-]$', text) and re.match(rf'[{L}]', ln):
            text = re.sub(r'[—–-]$', '', text) + ln
        else:
            text += (' ' if text else '') + ln
    text = text.translate(LATIN).replace('N00', 'NOO').replace('Iiegaino', 'Ilegalno')
    text = re.sub(r'(?<=\w)\s*[—–]\s*(?=[A-ZČĆŽŠĐ])', '-', text)             # "Kotor—Varoš", "Skender— Vakuf"
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[A-ZČĆŽŠĐ])', '-', text)              # "Skender- Vakufu"
    return re.sub(r'\s+', ' ', text).replace("u' ", 'u ').replace('godineu ', 'godine u ').strip()


# where he was born, in the locative as printed: "rođen 1908. godine u Grabovici", "rođena u Banjaluci 1907. godine",
# "rođen 1920. godine u Radahovoj kod Dunića"
BORN = re.compile(rf"\brođen[a]?\s+(?:(?:\d{{1,2}}\.\s*\w+\s+)?1[89]\d\d\.?\s*(?:godine\s*)?,?\s*)?u\s+"
                  rf"((?:[{U}][{L}\-]*\.?\s*){{1,3}}?)(?=\s*[,.;(]|\s+(?:kod|1[89]\d\d|[{L}]))")


def surname(word: str, own: set) -> str:
    """the site's spelling of a surname in capitals; one the site lacks takes -ić for -ic, and the book's own
    spelling where it prints the name elsewhere ("SUGIC" = Šugić of its spomenica list)"""
    s = kl.spelled(word, 'last')
    if s != s.translate(FOLD):
        return s
    for o in own:
        if o.translate(FOLD) == s:
            return o
    if ofz.known(word, 'last')[0] < 3 and s.endswith('ic'):
        return s[:-2] + 'ić'
    return s


def main():
    ofz.corpus()
    OWN.update(w for v in SPOMENICA.values() for w in v.split()[:-1])
    book = load(BOOK)
    entries, counts = [], Counter()
    for e in raw_entries(book):
        text = join(e['lines'])
        m = START.match(text)
        caps, given = m.group(1), m.group(2)
        surnames = [surname(w, OWN) for w in re.split(r'[ -]', caps)]
        gw = given.split()
        first = kl.spelled(gw[0], 'first')
        nick = gw[1] if len(gw) > 1 else ''
        body = text[m.end():].strip()
        village = kl.title(e['village']).replace('-V', '-V') if e['village'] else ''
        village = '-'.join(kl.title(p) for p in e['village'].split('-')) if e['village'] else ''
        info = f"{surnames[0]}{' ' + surnames[1] if len(surnames) > 1 else ''} {first}{' ' + nick if nick else ''}, {body}"
        role = vb.role(info)
        if role == 'out':                   # the list names him a participant of the war, the entry no more
            role = 'participant'
            print('  participant:', info[:150])
        y = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)', body)
        death = vb.death(info)
        born = BORN.search(info)
        rec = {
            'soldier_id': f"{PREFIX}{e['no']:06d}",
            'name': f"{' '.join(surnames)} {first}" + (f" — {nick}" if nick else ''),
            'last_name': surnames[0], 'first_name': first, 'nick': nick, 'fathers_name': '',
            'also': surnames[1:], 'birth_year': y.group(1) if y else '',
            # the village the entry names, else the heading's (a local SUBNOR board), and the općina
            'born_in': f"{born.group(1).strip() if born else village}, {e['opcina']}" if born or village else '',
            'death_year': death.get('year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            **({'death_place': death['place']} if death.get('place') else {}),
            'survived': False, 'units': vb.units_of(info),
            **({'role': role} if role else {}),
            'additional_info': f"{LIST}, {village}: {info}",
            'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, e['page']), 'source_page': e['page'] - OFFSET,
        }
        entries.append(rec)
        counts[role or 'fighter'] += 1
    for no, printed in SPOMENICA.items():
        w = printed.split()
        last, first = w[0], w[-1]
        also = w[1:-1]
        entries.append({
            'soldier_id': f'{PREFIX}{1000 + no:06d}', 'name': printed, 'last_name': last, 'first_name': first,
            'nick': '', 'fathers_name': '', 'also': also, 'birth_year': '', 'born_in': '', 'death_year': '',
            'survived': True, 'units': [],
            'additional_info': f"{SPOMENICA_TITLE}, {'Opština Kotor-Varoš' if no <= 21 else 'Opština Skender-Vakuf'}: "
                               f"{no}. {printed}",
            'list': SPOMENICA_TITLE, 'book_title': TITLE,
            'source_url': viewer_url(book, 357), 'source_page': 357})
        counts['spomenica'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    print(Counter(r['born_in'].split(',')[0] for r in entries).most_common(40))
    if '--sample' in sys.argv:
        random.seed(4)
        for r in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {r['name']} | {r['birth_year']} [{r['born_in']}] † {r['death_year']} {r.get('death_place', '')!r} "
                  f"{r.get('role', '')} {r['units']} | {r['additional_info'][:120]}")


if __name__ == '__main__':
    main()
