"""
Прва нишка гимназија 1878-1969. (Poreklo library, doc 00008460): "Преглед гимназијалаца разних генерација
погинулих у НОБ-у и жртава фашистичког терора" (scan pp. 225-236), as a book across units. Cyrillic, numbered within
each part, a short bio each: "1. АБРАМОВИЋ (Ивана) ИВАН, рођен 9. 8. 1926. године у Нишу. ... Погинуо у НОБ-у 1944.
године." The parts:
    I. "погинули као борци партизанских одреда и народноослободилачке војске Југославије" (61): every entry goes in;
    II. "Гимназијалци заклани од четника" (2), IV. "Гимназијалци стрељани на Бубњу и на Бањици" (20): by the mixed
        lists' rule, a partisan in as a fighter, the movement's people marked `role: 'activist'`, the rest out;
    III. "Изгинули гимназијалци у интернацији" (8) and V. "Гимназијалци погинули од бомбардовања": out.
The OCR sets the capitals' Ћ as 'Б or 'Н (АБРАМОВИ'Б) and Ђ as 'Б ('БОР'БЕВИ'Б); names are read back as the site
spells them (_village_books).

Output: data-extraction/poreklo/prva-niska-gimnazija-entries.json (IDs 9097xxxxxx: part I from 000001, II from
000201, IV from 000401, by the book's number).
Usage: python data-extraction/parse_prva_niska_gimnazija.py [--sample N]
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
import _village_books as V  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'prva-niska-gimnazija.json'
OUT = HERE / 'poreklo' / 'prva-niska-gimnazija-entries.json'
PREFIX = '9097'
OFFSET = 4                                  # scan page minus the book's page (the head of scan 229: "225")
TITLE = 'Prva niška gimnazija 1878-1969.'
LIST = 'Pregled gimnazijalaca raznih generacija poginulih u NOB-u i žrtava fašističkog terora'
PARTS = {'I': ('poginuli kao borci partizanskih odreda i Narodnooslobodilačke vojske Jugoslavije', 0, 'all'),
         'II': ('Gimnazijalci zaklani od četnika', 200, 'rule'),
         'III': ('Izginuli gimnazijalci u internaciji', 300, 'out'),
         'IV': ('Gimnazijalci streljani na Bubnju i na Banjici', 400, 'rule'),
         'V': ('Gimnazijalci poginuli od bombardovanja', 500, 'out')}
UC = 'А-ЯЂЈЉЊЋЏ'
HEADS = [(re.compile(r'погинули као борци'), 'I'), (re.compile(r'заклани од четника'), 'II'),
         (re.compile(r'у интернацији'), 'III'), (re.compile(r'стрељани на Бубњу'), 'IV'),
         (re.compile(r'од бомбардовања$'), 'V')]


# names past the rules, read from the bio and the site's spellings: (part, number) -> (surname, father, given, nickname)
NAMES = {('I', 6): ('Vukašinović', 'Miladina', 'Vukašin', ''), ('I', 12): ('Žilnik', 'Viktora', 'Konrad', 'Slobodan'),
         ('I', 13): ('Žikić', 'Đorđa', 'Petar', 'Maks'), ('I', 14): ('Ignjatović', 'Mihajla', 'Dušan', ''),
         ('I', 18): ('Koković', 'Dragoljuba', 'Ljubinko', ''), ('I', 27): ('Mitić', 'Jovana', 'Miodrag', ''),
         ('I', 37): ('Petrović', 'Ilije', 'Aleksandar', 'Aca Kapetan'),
         ('I', 41): ('Petrović', 'Dragoljuba', 'Miodrag', 'Mija Francuz'), ('I', 42): ('Petrić', 'Živojina', 'Radovan', ''),
         ('I', 43): ('Pešić', '', 'Radomir', ''), ('I', 44): ('Popović', 'Blagoja', 'Ljubiša', ''),
         ('I', 45): ('Rinčić', 'Đorđa', 'Vojislav', ''), ('I', 51): ('Tasković', 'Pejče', 'Dušan', ''),
         ('I', 55): ('Trajković', 'Dimitrija', 'Rista', ''), ('I', 57): ('Džakić', 'Aleksandra', 'Dragoslav', ''),
         ('I', 58): ('Čortanović', 'Milosava', 'Ljubivoje', ''), ('I', 60): ('Simonović', 'Nićifora', 'Strahinja', ''),
         ('I', 61): ('Hazan', '', 'Tilko', ''), ('I', 17): ('Jovanović', 'Spire', 'Marko', 'Joca'),
         ('I', 23): ('Marjanović', 'Božidara', 'Veljko', ''), ('I', 30): ('Mitrović', 'Milivoja', 'Petar', ''),
         ('I', 33): ('Nikodijević', 'Đure', 'Aleksandar', '')}
# a man the book names in two parts: one entry with both texts (Žikić Petar, a fighter shot as a captured partisan)
SAME = {('IV', 13): ('I', 13)}


def caps_name(w: str) -> str:
    """the OCR's 'Б, 'Н, 'В for Ћ at a word's end and for Ђ at its start ("'БОР'БЕВИ'Б" Ђорђевић)"""
    w = re.sub(r"^['’]?[БН]|^Т\)", 'Ђ', w) if re.match(r"^['’][БН]|^Т\)", w) else w
    w = re.sub(r"['’][БНВЊ]", lambda m: 'Ћ' if m.end() == len(w) else 'Ђ', w)
    w = re.sub(r"['’]", '', w)
    return w


def raw_entries(book: dict) -> list[dict]:
    out, part, started = [], None, False
    for page in range(225, 237):
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if not started:
                started = t.startswith('ГИМНАЗИЈАЛАЦА РАЗНИХ')
                continue
            if re.fullmatch(r'\d{3}|ПРВА НИШКА .*|\d{3} ПРВА НИШКА.*', t) or 'НИШКА' in t and len(t) < 30:
                continue
            head = next((p for rx, p in HEADS if rx.search(t) and len(t) < 70), None)
            if head and (not part or head != part):
                part = head
                continue
            if t.startswith('Тако се у току') or 'Ратни вихор' in t:
                return out
            t = re.sub(r'^зо\.', '30.', re.sub(r'^[>р]\s*', '', t))           # the OCR's "зо." for 30., ">23."
            m = re.match(r'^(\d{1,2})\s*[.,_·-]\s*(.*)$', t)
            last = out[-1]['no'] if out and out[-1]['part'] == part else 0
            # an entry whose number the OCR lost: a surname in capitals at the entries' indent, a bio after it
            lost = not m and part and l.x0 > 800 and re.match(rf"['’]?[{UC}]{{4,}}\S*\s", t) \
                and re.search(r'рођен|ученик|син\s', t)
            if m and part and last < int(m.group(1)) <= last + 2 and re.match(rf"['’]?[{UC}A-Za-zа-я]", m.group(2)) \
                    and l.x0 > 800:
                out.append({'part': part, 'no': int(m.group(1)), 'page': page, 'lines': [m.group(2)]})
            elif lost and out:
                out.append({'part': part, 'no': last + 1, 'page': page, 'lines': [t]})
            elif out:
                out[-1]['lines'].append(t)
    return out


def main():
    book = load(BOOK)
    entries, counts = [], Counter()
    for r in raw_entries(book):
        title, base, take = PARTS[r['part']]
        text = re.sub(r'\s+', ' ', V.unhyphen(' '.join(r['lines']))).strip()
        info = V.read_cyr(text)
        role = None
        if take == 'out':
            counts['out ' + r['part']] += 1
            continue
        if take == 'rule':
            role = V.role(info)
            if role == 'out':
                counts['out ' + r['part']] += 1
                continue
        cut = re.search(r',|\s(?:рођен|роћен|ученик|син|из)\b|\s[~—–]\s', text)
        head = text[:cut.start()] if cut else text
        paren = re.search(r'\(([^)]*)\)', head)
        words = head.replace('(', ' ').replace(')', ' ').split()
        caps = [w for w in words if re.sub(r"['’)]", '', w).isupper() or re.match(r"['’]", w)]
        title_words = [w for w in words if w not in caps]
        last = V.name_word(caps_name(caps[0])) if caps else ''
        first = V.given_word(caps_name(caps[-1])) if len(caps) > 1 else (V.given_word(title_words[-1]) if title_words else '')
        fath = V.father(paren.group(1) if paren else title_words[0]) if (paren or title_words) and len(caps) > 1 else ''
        nick = ''
        n = re.search(r'\s[~—–]\s+([^,]+?)(?:,|$)', text[:80])
        if n:
            nick = V.read_cyr(n.group(1))
        if (r['part'], r['no']) in NAMES:
            last, fath, first, nick = NAMES[(r['part'], r['no'])]
        if (r['part'], r['no']) in SAME:
            other = SAME[(r['part'], r['no'])]
            target = next(e for e in entries if e['soldier_id'] == f"{PREFIX}{PARTS[other[0]][1] + other[1]:06d}")
            target['additional_info'] += f" — {r['part']}. {title}: {r['no']}. {info}"
            counts['joined'] += 1
            continue
        y = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.?\s*\S+\s+)?(1[89]\d\d)', info)
        born = re.search(r'\bgodine\s+u\s+((?:selu\s+)?[A-ZČĆŽŠĐ]\w+(?:\s+[A-ZČĆŽŠĐ]\w+)?)', info)
        d = V.death(re.sub(r'\bu\s+NOB\S*', '', info))
        entries.append({
            'soldier_id': f"{PREFIX}{base + r['no']:06d}", 'name': ' '.join(x for x in (last, fath, first) if x),
            'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
            'birth_year': y.group(1) if y else '', 'born_in': born.group(1).replace('selu ', '') if born else '',
            'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
            **({'death_place': d['place']} if d.get('place') else {}),
            'survived': False, 'units': V.units_of(info), **({'role': role} if role else {}),
            'additional_info': f"{LIST}, {r['part']}. {title}: {r['no']}. {info}", 'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET})
        counts[r['part'] + (' ' + role if role else '')] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    if '--sample' in sys.argv:
        random.seed(9)
        for e in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {e['name']} — {e['nick']} | {e['birth_year']} [{e['born_in']}] † {e['death_year']} "
                  f"{e.get('death_place', '')!r} {e.get('role', '')} | {e['additional_info'][110:230]}")


if __name__ == '__main__':
    main()
