"""
Револуционарно Грахово (Poreklo library, doc 00010235): Grahovo by Nikšić and the villages around it, its fighters who
fell in the war, as a book across units. Cyrillic; the OCR reads the font's Ћ and Ђ as Б, ћ or Н ("АНДРИЈАШЕВИБ",
"роћен", "Борћијев"): names are read back as the site spells them (_village_books). Lists:
  - "Борци из Грахова пали у НОР-у и револуцији 1941-1945. године" (scan pp. 96-131): a bio each, "АНТУНОВИЋ
    Ђорђијев МАТИЈА-МАТО, рођен 1914. године у Нудолу, ...", the father a possessive (as printed: the matcher reads
    it, build_ostali_borci gives his nominative). The list counts the movement's people killed in prisons and camps
    with its fighters: they are marked `role: 'activist'` by parse_mosorski_odred_2's rule;
  - "Погинули народни хероји" (pp. 84-94): five long bios in narrow columns beside the photographs, whose lines the
    OCR scatters; each hero has his short entry in the list above, which takes the day he was proclaimed (`HEROES`);
  - "Жртве фашистичког терора" (pp. 132-136): of them only the movement's people by the same rule (`role:
    'activist'`) and a fighter the book set among them; the civilians stay out.

Output: data-extraction/poreklo/revolucionarno-grahovo-entries.json, IDs 9089xxxxxx: the fallen 9089000001 on in the
list's order, the victims' activists 9089001001 on.
Usage: python data-extraction/parse_revolucionarno_grahovo.py
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
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'revolucionarno-grahovo.json'
OUT = HERE / 'poreklo' / 'revolucionarno-grahovo-entries.json'
PREFIX = '9089'
OFFSET = 3                                  # scan page minus the book's page
TITLE = 'Revolucionarno Grahovo'
MUNICIPALITY = 'Nikšić'
FALLEN = 'Borci iz Grahova pali u NOR-u i revoluciji 1941-1945. godine'
VICTIMS = 'Žrtve fašističkog terora'
HERO_LIST = 'Poginuli narodni heroji'
UC = 'А-ЯЂЈЉЊЋЏ'
LC = 'а-яђјљњћџ'
# the heroes (surname, the father's possessive's start, given name) -> (scan page of the bio, the day he was proclaimed)
HEROES = {('Vujačić', 'Vid', 'Vasilije'): (84, '1951. godine'), ('Zvicer', 'Blago', 'Jovan'): (86, '1953. godine'),
          ('Kovačević', 'Golub', 'Miloš'): (88, '1953. godine'), ('Kovačević', 'Petr', 'Mirko'): (90, '1951. godine'),
          ('Kovačević', 'Blago', 'Sava'): (92, '6. jula 1943. godine')}
HEAD = re.compile(rf"^([{UC}'A-Z]{{3,}}(?:\s*[—–-]\s*[{UC}'A-Z]{{3,}})?)\s+([{UC}][{LC}A-Za-z]+)\s+"
                  rf"([{UC}'A-Z]{{2,}}(?:\s*-\s*[{UC}'A-Z]{{2,}})?)(?:\s*[—–-]\s*([{UC}'A-Z]{{2,}}))?\s*(?:,|(?=\(\s*1[89]))\s*(.*)$")
# possessives the OCR garbled, as the man's hero bio prints him; surnames it garbled past the reader
POSSESSIVES = {'Galubov': 'Golubov'}
SURNAMES = {'КОВАЧЧВИБ': 'КОВАЧЕВИЋ', 'ВЧЈАЧИБ': 'ВУЈАЧИЋ', 'КЕШЕЊЕВИБ': 'КЕШЕЉЕВИЋ'}


def lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.fullmatch(r'[\s_—–\-\d.]{1,8}', t):
                continue                                    # page numbers ("_93_", "–126—")
            out.append((page, t))
    return out


def read(book: dict, pages, start: str, stop: str | None) -> list[dict]:
    raw, cur, started = [], None, False
    for page, t in lines(book, pages):
        if not started:
            started = t.startswith(start)
            continue
        if stop and t.startswith(stop):
            break
        m = HEAD.match(t)
        if m:
            cur = {'page': page, 'head': m.groups()[:4], 'parts': [m.group(5)]}
            raw.append(cur)
        elif cur:
            cur['parts'].append(t)
    return raw


def entry(r: dict, i: int, title: str) -> dict:
    sur, poss, given, nick = r['head']
    sur = SURNAMES.get(sur, sur)
    last = '-'.join(V.name_word(x) for x in re.split(r'\s*[—–-]\s*', sur))
    first, *more = [V.given_word(x) for x in re.split(r'\s*-\s*', given)]
    nick = V.given_word(nick) if nick else (more[0] if more else '')
    fath = latin(poss).replace('Borć', 'Đorđ').replace('Bur', 'Đur') if re.match(r'^[БЂ]', poss) else latin(poss)
    fath = POSSESSIVES.get(fath, fath)
    info = V.read_cyr(' '.join(r['parts']))
    printed = f'{last.upper()} {fath} {first.upper()}{" – " + nick.upper() if nick else ""}'
    d = V.death(info)
    born = re.search(r'\brođen[a]?\s+(?:je\s+)?(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
    years = re.match(r'^\(?\s*(1[89]\d\d)\.?\s*[—–-]\s*(19\d\d)', info)     # a hero's entry: "(1917. — 1942.) narodni heroj"
    e = {'soldier_id': f'{PREFIX}{i:06d}', 'name': ' '.join(x for x in (last, fath, first) if x), 'last_name': last,
         'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
         'birth_year': born.group(1) if born else (years.group(1) if years else ''),
         'born_in': V.born_in(info, MUNICIPALITY), 'death_year': d.get('year') or (years.group(2) if years else ''),
         **({'death_date': d['date']} if d.get('date') else {}), **({'death_place': d['place']} if d.get('place') else {}),
         'survived': False, 'units': V.units_of(info),
         'additional_info': f'{title}: {printed}, {info}', 'list': title, 'book_title': TITLE,
         'source_url': viewer_url(r['_book'], r['page']), 'source_page': r['page'] - OFFSET}
    if V.role(info) == 'activist':
        e['role'] = 'activist'
    return e


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for i, r in enumerate(read(book, range(96, 132), 'БОРЦИ ИЗ ГРАХОВА', 'ЖРТВЕ ФАШИСТИЧКОГ'), 1):
        r['_book'] = book
        entries.append(entry(r, i, FALLEN))
        counts['fallen'] += 1
    n = 0
    for r in read(book, range(132, 137), 'ЖРТВЕ ФАШИСТИЧКОГ', None):
        r['_book'] = book
        info = V.read_cyr(' '.join(r['parts']))
        role = V.role(info)
        if role == 'out':
            counts['victims: out'] += 1
            continue
        n += 1
        entries.append(entry(r, 1000 + n, VICTIMS))
        counts[f'victims: {role or "fighter"}'] += 1
    for (last, fath, first), (page, proclaimed) in HEROES.items():
        hits = [e for e in entries if e['last_name'] == last and e['first_name'] == first and e['list'] == FALLEN
                and e['fathers_name'].startswith(fath)]
        assert len(hits) == 1, (last, first, len(hits))
        hits[0]['additional_info'] = hits[0]['additional_info'].rstrip('. ') + f'. {HERO_LIST} (str. {page - OFFSET}): za narodnog heroja proglašen je {proclaimed}'
        counts['heroes joined'] += 1
    counts.update(f"role {e.get('role')}" for e in entries)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))


if __name__ == '__main__':
    main()
