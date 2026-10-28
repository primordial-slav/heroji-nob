"""
Milorad T. Divac, *Mileševski kraj 1912-1945.* (doc 00007006 of the Poreklo library), a book across units: Prilog
"Učesnici narodnooslobodilačkog pokreta iz Mileševskog sreza (evidentirani po tadašnjim opštinama) poginuli u toku
Drugog svetskog rata" (scan pp. 144-188), in Cyrillic, under each općina's heading (АЉИНОВИЋИ, БАБИНЕ, БРОДАРЕВО, ...),
an entry each, numbered within the općina (the OCR lost many numbers):

    "Дивац Петка Владе, земљорадник, рођен 1916. године у Лучицама. Ступио у Милешевски одред 1943. године. Погинуо у
    Бродареву као командант батаљона 22. новембра 1943. у борби против Немаца."

Each općina's list ends with a count of its fallen ("Из Аљиновића је у народноослободилачкој борби погинуло укупно
12 бораца ..."), which is left out. The list counts the movement's people who were no fighters too: those by the mixed
lists' rule (`_village_books.role`), the movement's people `role: 'activist'`, and those the entry names with no more
than the list's title (a fighter's mother the Chetniks shot) `role: 'participant'`. The lists after it, the victims of
fascist terror, those who died in the civil war or with the occupier, and the war's other dead, stay out.

The OCR sets a given name at times above its number ("Благоје, земљорадник, рођен 1923. године" / "10. Трмчић
Богдана у"), which is put back.

Output: data-extraction/poreklo/milesevski-entries.json (IDs 9113xxxxxx, in the list's order).
Usage: python data-extraction/parse_milesevski.py [--sample N]
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
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'milesevski.json'
OUT = HERE / 'poreklo' / 'milesevski-entries.json'
PREFIX = '9113'
OFFSET = -9                                  # scan page minus the book's page (scan 144 is p. 153)
PAGES = range(144, 189)
TITLE = 'Mileševski kraj 1912-1945.'
LIST = ('Učesnici narodnooslobodilačkog pokreta iz Mileševskog sreza poginuli u toku Drugog svetskog rata')
MUNICIPALITY = 'Prijepolje'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
W = rf'[{CU}][{CL}]+'
START = re.compile(rf'^(?:(\d{{1,3}})\s*[.,]?\s*|[.,_]+\s*)?({W}(?:\s*-\s*{W})?)\s+({W}|[{CU}]\.)\s+({W})(?:\s*[-·]?\s*({W}))?\s*[,.]\s*(.*)$')
# a numbered entry that names no father ("46. Перишић Јагош, земљорадник")
START_NO_FATHER = re.compile(rf'^(\d{{1,3}})\s*[.,]?\s*({W})\s+({W})\s*,\s*(.*)$')
# a numbered entry run on after the one before it ("... у борби против Немаца. 11. Кукуљац Ћазима Ариф, ...")
RUN_ON = re.compile(rf'(?<=[.)])\s+(?=\d{{1,3}}\s*[.,]\s*[{CU}])')
# an entry glued on after a full stop behind a heading the OCR garbled ("... Немаца. 1(). Јусовић Саита Вехбија, земљорадник")
GLUED = re.compile(rf'(?<=[.)])\s+(?=(?:\S{{0,4}}\s+)?(?:\d+\s*[.,:]?\s*)?[^\s,]+\s+[^\s,]+\s+[^\s,]+\s*,\s*'
                   rf'(?:земљо|радник|домаћ|учен|рођен|студент|службеник|трговац))')
LENIENT = re.compile(r'^(?:\S{0,4}\s+)?(?:\d+\s*[.,:]?\s*)?([^\s,]+)\s+([^\s,]+)\s+([^\s,]+?)\s*,\s*(.*)$')
SUMMARY = re.compile(r'^Из\s.*(?:општин|погинуло|борби)|(?:Гинули|Погинули|Изгинули) су у борби|ступил[иo]\s+(?:је\s+)?у\s+борбу|'
                     r'погинул[оa]\s+(?:је\s+)?(?:укупно\s+)?\d|^Свега|бораца, и то')
HEADING = re.compile(rf'^[{CU}ЋЂ\' ]{{4,}}$')
GIVEN_FIRST = re.compile(rf'^({W}(?:\s+{W})?),\s+(.*)$')            # "Благоје, земљорадник, РОћеН 1923. године"
# the općinas' headings as the OCR reads them (Љ as Њ, Ћ as Б)
OPCINE = {'АЊИНОВИБИ': 'Aljinovići', 'ПРИЈЕПОЊЕ': 'Prijepolje', 'СЕЊАШНИЦА': 'Seljašnica'}
# names the OCR garbled, as the context reads them (Veruović of Velika Župa, the Latin C for С of Smiljanović)
NAME_FIX = {'Bepyonnh': 'Veruović', 'Nšsola': 'Nikola', 'Potežšda': 'Potežica', 'Romapdić': 'Romandić',
            'Radoji': 'Radojica', 'Veselš': 'Veselin', 'Mujezinovićč': 'Mujezinović', 'Sgiković': 'Stiković',
            'Cpica': 'Špica', 'Cmiljanović': 'Smiljanović'}
# an entry whose given name the OCR garbled past reading: the name as far as it goes, the rest kept as printed
UNREAD = {'Пејовић Ананија П.. гар,': ('Пејовић', 'Ананија')}
# where he was born, in the locative as printed: "rođen 1924. godine u Goločevini. Stupio ..."
BORN_IN = re.compile(r'\bro[đd]en[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?1[89][\d()]{2}[_.]?\s*(?:god\w*\.?\s*)?,?\s*(?:u|na|y|U)\s+'
                     r'([A-ZČĆŽŠĐ][\w-]*(?:\s+[A-ZČĆŽŠĐ][\w-]*){0,2}?)(?=\s*[.,;]|\s+[a-zčćžšđ]|\s+(?:Stup|Pogin|Solun|Rad))')
NUMBER_LINE = re.compile(rf'^(\d{{1,3}})\s*\.?\s*({W})\s+({W}|[{CU}]\.)(\s+у)?$')   # "10. Трмчић Богдана у"


def soft_c(word: str) -> str:
    """a name the OCR begins with a small ћ, a quote before it at times: Ђ or Ћ, whichever the site's names have more
    often ("ћуковић" is Ćuković, "ћерасима" Đerasima)"""
    rest = word[1:]

    def n(c):
        return max(V.T._names[latin((c + rest).upper())], V.T._given[latin((c + rest).upper())],
                   V.T._given[latin((c + rest[:-1]).upper())])          # a father's genitive: Ђерасим(а)
    best = max(('Ђ', 'Ћ'), key=n)
    return best + rest if n(best) else word                            # not a name: "ћелије" stays


def clean(t: str) -> str:
    t = re.sub(r'["\'‘’]\s*(?=[Бб]ур|[Бб]ор)', '', t).replace('"Б', 'Ђ').replace("'Б", 'Ђ')
    t = re.sub(rf'\b"?[Бб](?=ур[{CL}]|орђ)', 'Ђ', t)                     # "Бурашићима", "'ћорђија" for Ђ
    t = re.sub(rf'(?:["\'‘’]\s*)?(?<![{CL}{CU}])ћ[{CL}]+', lambda m: soft_c(m.group(0).lstrip('"\'‘’ ')), t)
    t = re.sub(r'^(\d{1,3}\s*[.,]?\s*)ћ', r'\1Ћ', t).replace('ћурђи је', 'Ђурђије')   # a name the site lacks; "Ђурђије"
    return re.sub(r'\s+', ' ', t).strip()


def raw_entries(book: dict) -> list[dict]:
    entries, opcina, summary = [], '', False
    for page in PAGES:
        lines = [seg for l in level_lines(page_words(book, page)) for seg in RUN_ON.split(clean(l.text))]
        for i, t in enumerate(lines):
            if not t or re.fullmatch(r'[\d\s.]{1,5}', t) or t.startswith(('УЧЕСНИЦИ', 'ПОКРЕТА', '(ЕВИДЕН', 'ОПШТИНАМА', 'ДРУГОГ')):
                continue
            if HEADING.match(t) and not re.search(rf'[{CL}]', t):
                opcina, summary = t.strip(), False
                continue
            if SUMMARY.search(t) and not START.match(t):
                summary = True                    # "Из Аљиновића је у народноослободилачкој борби погинуло укупно 12 бораца"
                continue
            num = NUMBER_LINE.match(t)
            if num and entries and GIVEN_FIRST.match(entries[-1]['lines'][-1]) and len(entries[-1]['lines']) > 1:
                given_line = entries[-1]['lines'].pop()         # the given name set above its number
                g = GIVEN_FIRST.match(given_line)
                t = f"{num.group(1)}. {num.group(2)} {num.group(3)} {g.group(1)}, {g.group(2)}{' у' if num.group(4) else ''}"
            t = re.sub(rf'^(\d{{1,3}}\.\s*{W}\s+{W}\s+)([{CL}])', lambda x: x.group(1) + x.group(2).upper(), t)
            m = START.match(t) or START_NO_FATHER.match(t) or any(t.startswith(u) for u in UNREAD)
            ends = not entries or re.search(r'[.)]\s*$', ' '.join(entries[-1]['lines']))
            if m and (m is True or m.group(1) or ends or summary):
                entries.append({'opcina': opcina, 'page': page, 'lines': [t]})
                summary = False
                continue
            if summary:
                continue
            if entries:
                entries[-1]['lines'].append(t)
    return entries


def main():
    V.corpus()
    book = load(BOOK)
    out, counts = [], Counter()
    pieces = []                                 # an entry's text, with the entries a heading the OCR garbled glued on split
    for e in raw_entries(book):
        s = ' '.join(e['lines'])
        cuts = [0]
        for m in GLUED.finditer(s):             # a cut, four words or more after the one before (not "10." alone)
            if len(s[cuts[-1]:m.start()].split()) >= 4:
                cuts.append(m.start())
        cuts.append(len(s))
        parts = [s[a:b].strip() for a, b in zip(cuts, cuts[1:])]
        pieces += [dict(e, lines=[p], glued=i > 0) for i, p in enumerate(parts) if p.strip()]
    for no, e in enumerate(pieces, 1):
        unread = next((u for u in UNREAD if e['lines'][0].startswith(u)), None)
        if unread:
            (sur, fath), given, second = UNREAD[unread], None, None
            rest = e['lines'][0][len(' '.join(unread.split()[:2])):].strip()
        elif not e['glued'] and START.match(e['lines'][0]):
            _, sur, fath, given, second, rest = START.match(e['lines'][0]).groups()
        elif not e['glued'] and START_NO_FATHER.match(e['lines'][0]):
            _, sur, given, rest = START_NO_FATHER.match(e['lines'][0]).groups()
            fath, second = '', None
        else:
            sur, fath, given, rest = LENIENT.match(e['lines'][0]).groups()
            sur, fath, given, second = re.sub(r'[^\w-]', '', sur), re.sub(r'[^\w.]', '', fath), re.sub(r'\W', '', given), None
        last = '-'.join(V.name_word(x) for x in re.split(r'\s*-\s*', sur))
        first = V.given_word(given) if given else ''
        nick = V.given_word(second) if second else ''
        last, first = NAME_FIX.get(last, last), NAME_FIX.get(first, first)
        if last == 'Aidonović' and first == 'Bore':
            first = 'Ćore'                      # "Аидоновић 'Ђорђија Ћоре"
        fath = latin(fath)
        info = V.read_cyr(' '.join([rest] + e['lines'][1:])).strip()
        info = re.split(r'\s(?=Od ukupno\b|Prema godinama stupanja)', info)[0]     # the općina's count of its fallen
        name = ' '.join(x for x in (last, fath, first) if x)
        text = f"{name}{' ' + nick if nick else ''}, {info}"
        role = V.role(text)
        if role == 'out':                       # the list names him a participant of the movement, the entry no more
            role = 'participant'
        d = V.death(text)
        born = re.search(r'\bro[đd]en[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
        place = BORN_IN.search(info)
        rec = {'soldier_id': f'{PREFIX}{no:06d}', 'name': name, 'last_name': last, 'also': [], 'first_name': first,
               'nick': nick, 'fathers_name': fath, 'birth_year': born.group(1) if born else '',
               'born_in': f'{place.group(1).strip()}, {MUNICIPALITY}' if place else '', 'death_year': d.get('year', ''),
               **({'death_date': d['date']} if d.get('date') else {}),
               **({'death_place': d['place']} if d.get('place') else {}),
               'survived': False, 'units': V.units_of(text), **({'role': role} if role else {}),
               'additional_info': f"{LIST}, {OPCINE.get(e['opcina'], latin(e['opcina']).title())}: {text}",
               'list': LIST, 'book_title': TITLE, 'source_url': viewer_url(book, e['page']),
               'source_page': e['page'] - OFFSET}
        out.append(rec)
        counts[role or 'fighter'] += 1
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts))
    print(Counter(r['additional_info'].split(': ')[0].split(', ')[-1] for r in out))
    if '--sample' in sys.argv:
        random.seed(6)
        for r in random.sample(out, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(out))):
            print(f"  {r['soldier_id']} {r['name']} {r['nick']} | {r['birth_year']} [{r['born_in']}] † {r['death_year']} "
                  f"{r.get('death_place', '')!r} {r.get('role', '')} {r['units']} | {r['additional_info'][110:260]}")


if __name__ == '__main__':
    main()
