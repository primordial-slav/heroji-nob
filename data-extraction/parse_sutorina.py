"""
*Суторина - хроника подручја и насеља са родословљем* (doc 00000589 of the Poreklo library), Sutorina by Herceg Novi,
as a book across units, three of its appendices (Cyrillic):
    9.1.4, "Суторинска партизанска чета" (book pp. 405-409, scan 451-455): the company's command at its founding and
        its four platoons by village (Rustovo and Prijevor; Radanovići, Malta and Konjevići; Šćepoševići; Lučići and
        Rajevići), a man a line: "* Беко Крста Јефто 1909 борац" (the father in the genitive, the birth year, the
        duty), a nickname or a given name run on to the next line;
    9.1.5 a), "Пали борци НОР-а 1941-1945. године" (pp. 410-414): 18 fallen, two to a line, the father in the
        nominative and the years under the name: "Јанчић (Саво) Петар / 1923–1944. г.";
    9.1.6, "Суторани - носиоци Партизанске споменице 1941" (pp. 416-418): three, a biography each beside the name and
        the years ("Грбић Јова Марко / 1896–1972. г."), who lived through the war (`survived`).
A fallen fighter or a holder who is in the company is one entry with both texts. Out: the same appendix's victims of
fascist terror and its dead of 1991-1995, the volunteers of the wars of 1852-1918, and the children sent to Srem.

Output: data-extraction/poreklo/sutorina-entries.json (IDs 9110xxxxxx: the company from 000001, the fallen from
001001, the holders from 002001).
Usage: python data-extraction/parse_sutorina.py
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
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'sutorina.json'
OUT = HERE / 'poreklo' / 'sutorina-entries.json'
PREFIX = '9110'
BOOK_TITLE = 'Sutorina - hronika područja i naselja sa rodoslovljem'
OFFSET = 46                                 # scan page minus the book's page in these appendices
COMPANY = 'Sutorinska partizanska četa'
FALLEN = 'Pali borci NOR-a 1941-1945. godine'
SPOMENICA = 'Sutorani - nosioci Partizanske spomenice 1941'
PLACE = 'Sutorina, Herceg Novi'
U, L = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
W = rf'[{U}][{L}]+'
ROW = re.compile(rf"^\*\s*({W}(?:\s*[—–-]\s*{W})?)\s+({W}|[{U}]\.)[,.]?\s*({W}(?:\s*[—–-]\s*{W})?)?\s*([—–-])?\s*(\d{{4}})\s+(.+)$")
DUTIES = {'командир вода': 'komandir voda', 'заменик командира вода': 'zamenik komandira voda', 'борац': 'borac'}


def cyr(t: str) -> str:
    """the OCR's slips in Cyrillic: a quote before Б for Ђ ("'Бура"), capitals inside a word ("ВУКа", "НоваКа")"""
    t = re.sub(r"['’\"“„]\s*[БВ](?=[{}])".format(L), 'Ђ', t)
    t = re.sub(r"['’\"“”„]", '', t)                                    # the specks left: "Обрад ““ 1913"
    for a, b in READ.items():
        t = t.replace(a, b)
    # a word in capitals or with capitals inside it: "ГУГОЊ", "ВУКа", "НоваКа"
    return re.sub(rf'(?<![{U}{L}])([{U}])([{U}{L}]+)', lambda m: m.group(1) + m.group(2).lower(), t).replace('·', '-')


# names past the rules, read from the list (the brothers beside them) and the site's names
READ = {'Черврти': 'Четврти', 'РајевићкиШ': 'Рајевићки', 'Трииа': 'Трифка', 'Јона,': 'Јова,'}


FATHERS = {'Ilijd': 'Ilija'}           # (the converter's slip for the printed "Илија")


def genitive(n: str) -> str:
    """the fallen list's father in the nominative ("(Ристо)") as the company list prints fathers, in the genitive"""
    if n.endswith('o'):
        return n[:-1] + 'a'
    if n.endswith('a'):
        return n[:-1] + 'e'
    return n + 'a' if re.search(r'[bcčćdđfghjklmnprsštvzž]$', n) else n


def given(w: str) -> tuple[str, str]:
    """"Божидар –Божо": the given name and the nickname, read back"""
    parts = [p for p in re.split(r'\s*[—–-]\s*', w) if p]
    return V.given_word(parts[0]), (V.given_word(parts[1]) if len(parts) > 1 else '')


def company(book: dict) -> list[dict]:
    out, platoon = [], 'komanda čete'
    for line in [l.text.strip() for l in level_lines(page_words(book, 451))]:
        m = re.match(rf'^\d\.\s*([^:]+):\s*({W})\s+(\S+)\s+({W})\s*\((\d{{4}})\)', cyr(line))
        if m:
            out.append({'last': V.name_word(m.group(2)), 'father': V.father(m.group(3)), 'first': V.given_word(m.group(4)),
                        'nick': '', 'year': m.group(5), 'duty': V.read_cyr(m.group(1)).strip().lower(), 'unit': platoon,
                        'page': 451})
    for page in range(452, 456):
        ls = [cyr(l.text.strip()) for l in level_lines(page_words(book, page))]
        head = next((t for t in ls if re.search(r'вод:', t)), '')
        platoon = V.read_cyr(head.split(':')[0]).strip() + (f" ({V.read_cyr(head.split(':', 1)[1]).strip()})" if ':' in head else '')
        prev = None
        for t in ls:
            if re.match(r'^\d+[.)]\s', t):
                prev = None
                continue                            # a footnote
            m = ROW.match(t)
            if m:
                sur, fath, first, dash, year, duty = m.groups()
                first, nick = given(first) if first else ('', '')
                prev = {'last': '-'.join(V.name_word(p) for p in re.split(r'\s*[—–-]\s*', sur)), 'father': FATHERS.get(V.father(fath), V.father(fath)),
                        'first': first, 'nick': nick, 'year': year, 'duty': DUTIES.get(duty.strip(' *]°“"\'').lower(), 'borac'),
                        'unit': platoon, 'page': page, 'open': not first or bool(dash)}
                out.append(prev)
            elif prev and prev.get('open') and re.fullmatch(rf'{W}(?:\s*[—–-]\s*{W})?\s*[-·]?', t):
                a, b = given(t.strip(' -·'))
                if not prev['first']:
                    prev['first'], prev['nick'] = a, b
                else:
                    prev['nick'] = a
                prev['open'] = False
    return out


def fallen(book: dict) -> list[dict]:
    names, years, pages = [], [], []
    for page in range(456, 461):
        for t in [cyr(l.text.strip()) for l in level_lines(page_words(book, page))]:
            if t.startswith('б)'):
                break
            if re.match(r'^(9\.1\.5|и у последњем|а\)|\d+\.\s)', t):
                continue                            # the headings and the footnote, which carry years too
            for m in re.finditer(rf'({W})\s*\(({W})\)\s*({W}(?:\s*[—–-]\s*{W})?)', t):
                names.append(m.groups())
                pages.append(page)
            years += re.findall(r'(\d{4})\s*[—–-]\s*(19[34](?:\d|\(\?\)))', t)
    assert len(names) == len(years), (len(names), len(years))
    out = []
    for (sur, fath, first), (born, died), page in zip(names, years, pages):
        first, nick = given(first)
        out.append({'last': V.name_word(sur), 'father': genitive(V.given_word(fath)), 'printed_father': V.given_word(fath),
                    'first': first, 'nick': nick, 'year': born,
                    'died': died if died[3:].isdigit() else '', 'page': page})
    return out


def holders(book: dict) -> list[dict]:
    out = []
    for page in range(462, 465):
        ls = [l for l in level_lines(page_words(book, page))]
        name = years = ''
        bio = []
        for l in ls:
            t = cyr(l.text.strip())
            m = re.match(rf"^['\s]*({W})\s+({W}|[{U}]\.)\s+({W})(?:\s+(.*))?$", t)
            y = re.search(r'(1[89]\d\d)\s*[—–-]\s*(19\d\d|20\d\d)\.\s*г\.', t)
            if not name and m and not re.match(r'^Рођен', t):
                name = m.groups()[:3]
                if m.group(4):
                    bio.append(m.group(4))
                continue
            if y and not years:
                years = y.groups()
                t = t[:y.start()] + t[y.end():]
            if re.fullmatch(r'\d{3}|.*\d+\.\s+[A-ZА-Я]{2,}.*\d{4}.*стр.*', t) or t.startswith(('9.1.6', '15.')):
                continue
            bio.append(t.strip())
        out.append({'last': V.name_word(name[0]), 'father': V.father(name[1]) if not name[1].endswith('.') else V.read_cyr(name[1]),
                    'first': V.given_word(name[2]), 'year': years[0] if years else '', 'died': years[1] if years else '',
                    'bio': V.read_cyr(' '.join(x for x in bio if x)), 'page': page})
    return out


def main():
    V.corpus()
    book = load(BOOK)
    recs, counts = [], Counter()
    for no, e in enumerate(company(book), 1):
        printed = ' '.join(x for x in (e['last'], e['father'], e['first']) if x) + (f" - {e['nick']}" if e['nick'] else '')
        recs.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': printed.replace(' - ', ' — '), 'last_name': e['last'],
                     'also': [], 'first_name': e['first'], 'nick': e['nick'], 'fathers_name': e['father'],
                     'birth_year': e['year'], 'born_in': PLACE, 'death_year': '', 'survived': False, 'units': [],
                     'list': COMPANY, 'book_title': BOOK_TITLE, 'source_url': viewer_url(book, e['page']),
                     'source_page': e['page'] - OFFSET,
                     'additional_info': f"{COMPANY}, {e['unit']}: {printed}, {e['year']}, {e['duty']}"})
        counts['company'] += 1
    by_name = {}
    for r in recs:
        by_name.setdefault((r['last_name'], r['first_name'], r['birth_year']), []).append(r)
    for no, e in enumerate(fallen(book), 1):
        printed = f"{e['last']} ({e['printed_father']}) {e['first']}" + (f" - {e['nick']}" if e['nick'] else '') + f", {e['year']}–{e['died'] or '194?'}."
        text = f'{FALLEN}: {printed}'
        same = by_name.get((e['last'], e['first'], e['year']), [])
        if len(same) == 1:
            same[0]['additional_info'] += '. ' + text
            same[0]['death_year'] = e['died']
            counts['fallen, joined to the company'] += 1
            continue
        recs.append({'soldier_id': f'{PREFIX}{1000 + no:06d}', 'name': f"{e['last']} {e['father']} {e['first']}",
                     'last_name': e['last'], 'also': [], 'first_name': e['first'], 'nick': e['nick'], 'fathers_name': e['father'],
                     'birth_year': e['year'], 'born_in': PLACE, 'death_year': e['died'], 'survived': False, 'units': [],
                     'list': FALLEN, 'book_title': BOOK_TITLE, 'source_url': viewer_url(book, e['page']),
                     'source_page': e['page'] - OFFSET, 'additional_info': text})
        counts['fallen'] += 1
    for no, e in enumerate(holders(book), 1):
        text = f"{SPOMENICA}: {e['last']} {e['father']} {e['first']}, {e['year']}–{e['died']}. {e['bio']}"
        same = [r for r in by_name.get((e['last'], e['first'], e['year']), [])]
        if len(same) == 1:
            same[0]['additional_info'] += '. ' + text
            same[0]['survived'] = True
            counts['holders, joined to the company'] += 1
            continue
        recs.append({'soldier_id': f'{PREFIX}{2000 + no:06d}', 'name': f"{e['last']} {e['father']} {e['first']}",
                     'last_name': e['last'], 'also': [], 'first_name': e['first'], 'nick': '', 'fathers_name': e['father'],
                     'birth_year': e['year'], 'born_in': PLACE, 'death_year': '', 'survived': True, 'units': [],
                     'list': SPOMENICA, 'book_title': BOOK_TITLE, 'source_url': viewer_url(book, e['page']),
                     'source_page': e['page'] - OFFSET, 'additional_info': text})
        counts['holders'] += 1
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(recs))
    for r in recs:
        print(f"  {r['soldier_id']} {r['name']} | {r['birth_year']} {r['death_year']} {r['survived']} | {r['additional_info'][:110]}")


if __name__ == '__main__':
    main()
