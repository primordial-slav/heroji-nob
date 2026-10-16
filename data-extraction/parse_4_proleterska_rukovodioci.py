"""
Parser: 4. proleterska (crnogorska) brigada (brigade code 40) — the brigade's officers and its narodni heroji, two more
lists of Janković's book.

Source: Blažo Janković, "Četvrta proleterska crnogorska brigada" (znaci.org 00001/148_13.pdf) →
        website/public/pdfs/4-proleterska-poginuli.pdf, after the fallen (parse_4_proleterska_poginuli.py, pp. 1-107):
    pp. 109-126  "Rukovodioci 4. proleterske crnogorske brigade, zaključno sa komandama bataljona i samostalnih
                 jedinica i službi, od juna 1942. do maja 1945. godine": under the brigade's staff, each battalion,
                 the četa pratećih oruđa and the brigadna komora, each duty's holders in order, a bio each:
                     ĐUROVIĆ Jokov VASILIJE VAKO, rođen 1915. u Momišićima (Titograd), student, član KPJ, narodni
                     heroj, poginuo 9. juna 1943. na Sutjesci; komandant od 23. marta do 9. juna 1943.
                 A man in several posts has an entry under each; the merges (scripts/find_source_duplicates.py) join
                 them, and join them to the fallen's and the Borci Sutjeske's entries. The Politodjel's members stand
                 run on, a composition and its days at a time ("RIBAR Ivana JURICA, LEKIĆ RISTO (narodni heroj) i
                 ĐUROVIĆ Petrova STANA (od 1. decembra 1942. do 1. maja 1943)."): they are typed here (`POLITODJEL`),
                 a member who has an entry of his own in the list getting the department's days added to it.
    pp. 127-128  the cadres the brigade gave the army, counts only: not read.
    pp. 129-131  "Narodni heroji": the brigade's 49 heroes, birth and fate.
Cyrillic, read with the fallen parser's rules (its corpus, Л and Љ repairs, the possessive fathers).

The officers get IDs from 30001, the heroes from 40001 (the unit's other lists: Borci Sutjeske 1-, the fallen
10001-, the men at formation 20001-).

Usage: python data-extraction/parse_4_proleterska_rukovodioci.py
"""
import re

import parse_4_proleterska_poginuli as pog
from _parser_scaffold import run_parser

PDF = 'website/public/pdfs/4-proleterska-poginuli.pdf'
OUT = 'website/public/4-proleterska-soldiers.json'
UNITS = {'ŠTAB BRIGADE': 'štab brigade', 'PRVI BATALJON': '1. bataljon', 'DRUGI BATALJON': '2. bataljon',
         'TREĆI BATALJON': '3. bataljon', 'ČETVRTI BATALJON': '4. bataljon', 'PETI BATALJON': '5. bataljon',
         'ČETA PRATEĆIH ORUĆA': 'četa pratećih oruđa', 'BRIGADNA KOMORA': 'brigadna komora'}
DUTIES = {'Komandanti', 'Komandiri', 'Politički komesari', 'Zamjenici komandanta', 'Zamjenici komandira',
          'Zamjenici političkog komesara', 'Načelnici šgaba', 'Načelnici štaba', 'Intendanti', 'Rukovodioci saniteta',
          'Upravnici bolnice', 'Referenti saniteta', 'Palitodjel'}
TITLE = 'Rukovodioci 4. proleterske crnogorske brigade'
# the Politodjel's compositions, as the book runs them on (p. 111-112): (surname, father as printed, given name,
# what more the book says, the days)
POLITODJEL = [
    ('Popović', 'Milića', 'Milentije', 'inž.', ['od 10. juna do 25. juna 1942']),
    ('Masleša', 'Aleksandra', 'Veselin', 'narodni heroj', ['od 10. juna do 25. juna 1942', 'od 25. juna do 1. decembra 1942']),
    ('Zogović', 'Đorđijev', 'Radovan', '', ['od 10. juna do 25. juna 1942', 'od 25. juna do 1. decembra 1942']),
    ('Tomašević', 'Petrova', 'Stana', '', ['od 25. juna do 1. decembra 1942']),
    ('Ribar', 'Ivana', 'Jurica', '', ['od 1. decembra 1942. do 1. oktobra 1943']),
    ('Lekić', '', 'Risto', 'narodni heroj', ['od 1. decembra 1942. do 1. juna 1943']),
    ('Đurović', 'Petrova', 'Stana', '', ['od 1. decembra 1942. do 1. maja 1943']),
    ('Đorđić', 'Sekulov', 'Jovan', '', ['od 1. maja do 1. juna 1943']),
    ('Đurović', 'Sekulov', 'Jovan', '', ['od 1. jula do 1. oktobra 1943']),
    ('Stanišić', 'Maksimov', 'Milija', '', ['od 1. jula do 1. avgusta 1943']),
    ('Kruščić', 'Milosava', 'Stanojka', '', ['od 1. avgusta do 1. oktobra 1943']),
    ('Kalezić', '', 'Mirko', '', ['od 1. oktobra 1943. do 1. septembra 1944']),
    ('Vojvodić', '', 'Todor', 'zvani Đedo', ['od 1. oktobra 1943. do 1. septembra 1944']),
    ('Žarković', 'Mirkov', 'Gojko', '', ['od 1. oktobra 1943. do 1. septembra 1944']),
    ('Janjić', '', 'Tihomir', '', ['od 1. septembra 1944']),
    ('Stamatović', '', 'Jovan', '', ['od 1. septembra 1944']),
    ('Nikolić', '', 'Mica', '', ['od 1. septembra 1944']),
]
# an entry the fallen list's start misses: a doctor's "dr" or an engineer's "inž." before the given name, a second
# father in brackets, a given name in small letters ("MIKIĆ Milovanov dr ŽARKO", "BAROVIĆ Mijajlov (Mrgudov) SIMO",
# "BRAJOVIĆ Jovanov Jokaš,")
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ENTRY = re.compile(pog.ENTRY.pattern + rf'|^[{U}]{{2,}}(?:[-–][{U}]+)?\s+(?:[{U}][{L}]+\s+)?(?:\([{U}][{L}]+\)\s+)?'
                   rf'(?:dr\s+|inž\.\s+)?[{U}][{U}{L}]+(?:\s+[{U}]{{2,}})?,')
# the running footer ("36 Četvrta proleterska 625") and a stray mark the scan left at a column's foot
FURNITURE = re.compile(r'^\d+\s+Četvrta proleterska|^I$')
_heads: list[tuple] = []        # (page, y, unit) of each unit's heading
_politodjel: list[dict] = []    # the Politodjel block's lines (page, y, text)


def prepare(lines: list[dict]) -> None:
    """Drop the title, the headings and the Politodjel's block, keeping where each unit's heading stands."""
    keep, block, started = [], False, False
    for ln in lines:
        t = ln['text'].strip()
        if t in UNITS:
            _heads.append((ln['page'], ln['y'], UNITS[t]))
            started, block = True, False
            continue
        if not started:
            continue                                                      # the title over the staff's heading
        if t in DUTIES:
            block = t == 'Palitodjel'
            continue
        if block:
            _politodjel.append(ln)
            continue
        keep.append(ln)
    lines[:] = keep


def unit_of(s: dict) -> str:
    here = (s.get('pdf_page') or 0, s.get('pdf_y') or 0)
    units = [u for p, y, u in _heads if (p, y) <= here]
    return units[-1] if units else ''


def officers(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        unit = unit_of(s)
        s['unit_detail'] = unit
        s['additional_info'] = f'{TITLE}, {unit}: {s["additional_info"]}'
    for last, father, given, more, days in POLITODJEL:
        text = f"član Politodjela brigade {', '.join(days)}"
        own = [s for s in soldiers if s['last_name'] == last and s['first_name'] == given]
        if own:
            own[0]['additional_info'] = own[0]['additional_info'].rstrip('.') + f'; {text}.'
            continue
        where = next((ln for ln in _politodjel if last.upper() in ln['text'].upper().replace('  ', ' ')), None)
        rec = {'last_name': last, 'middle_name': father, 'first_name': given, 'fathers_name': '',
               'full_name': ' '.join(p for p in (last, father, given) if p), 'birth_year': '',
               'unit_detail': 'politodjel brigade',
               'additional_info': f"{TITLE}, politodjel brigade: {(more + '; ') if more else ''}{text}."}
        if where:
            rec.update({'pdf_file': '4-proleterska-poginuli.pdf', 'pdf_page': where['page'], 'pdf_y': where['y'],
                        'pdf_x': round(where.get('x', 0), 1)})
        soldiers.append(rec)
    return pog.post(soldiers)


def heroes(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        s['additional_info'] = f'Narodni heroj, 4. proleterska crnogorska brigada: {s["additional_info"]}'
    return pog.post(soldiers)


def officer_lines(ln: dict) -> bool:
    ln['text'] = ln['text'].replace('Dimitrij ev', 'Dimitrijev')         # "POLEKSIĆ Dimitrij ev MOMČILO"
    return pog.keep(ln) and not FURNITURE.match(ln['text'].strip())


def hero_lines(ln: dict) -> bool:
    return officer_lines(ln) and ln['text'].strip() != 'NARODNI HEROJI'


if __name__ == '__main__':
    pog.corpus()
    common = dict(pdf_path=PDF, brigade_code=40, output_path=OUT, layout='single', extract_fn=pog.extract,
                  script='cyrillic', entry_start_re=ENTRY, parse_entry_fn=pog.parse_entry, keep_other_sources=True)
    run_parser(start_page=109, end_page=126, prepare_fn=prepare, line_filter=officer_lines, post_fn=officers,
               id_start=30001, **common)
    run_parser(start_page=129, end_page=131, line_filter=hero_lines, post_fn=heroes, id_start=40001, **common)
