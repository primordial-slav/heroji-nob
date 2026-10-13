"""
Village chronicles of the Poreklo library (collection "Monografije sela", 274 books): their lists of the village's
fighters in the people's liberation war, as a book across units (see scripts/match_references.py). Each list's
entries are added to the records of the soldiers they describe; the chronicles add no records of their own.

Only lists the book itself heads as the NOB's fighters go in: the fallen fighters, the participants, the holders of
the Partisan Commemorative Medal 1941 ("spomenica"). These books also list the dead of the Balkan wars, the First
World War and the 1990s, civilian victims, internees, prisoners, the punished after the war and Chetniks: none of
that is read. A list that keeps fighters and victims of fascist terror together is read only for the entries the
list itself marks as fighters (Donje Vidovo's "NOB" column).

The lists were found by searching the collection for their headings ("палих бораца", "учесници НОР", "Партизанске
споменице" ...) and reading the hits; each is in LISTS by its book, scan pages, the heading it starts under and the
one it stops at, and its entry style. The OCR is cached in data-extraction/.cache/poreklo/villages/ (not in git:
fetched through a member's login): whole books as <document>.json, else the pages about the search hits in
survey.json.

The OCR of these books reads the capital Ћ and Ђ as Б and gives -ИЋ as -ИТЈ, -И'Б, -ИТ}; names are read back as the
spelling the site's records know best. Entries are kept in Latin.

Output: data-extraction/poreklo/seoske-hronike-entries.json (IDs 9005xxxxxx), with the fields the matcher reads;
born_in is the village the entry gives, else the village heading over it, else the book's village, with the
municipality.

Usage: python data-extraction/parse_seoske_hronike.py [--sample N] [--list KEY]
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
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import Line, page_lines, page_words, printed_page, viewer_url  # noqa: E402

CACHE = HERE / '.cache' / 'poreklo' / 'villages'
OUT = HERE / 'poreklo' / 'seoske-hronike-entries.json'
PREFIX = '9005'
COLLECTION = '0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/'

UC = 'А-ЯЂЈЉЊЋЏ'
LC = 'а-яђјљњћџ'
FIRST = 'А-ЯЂЈЉЊЋЏћђчшж'           # a name's first letter; the OCR gives some capitals in lower case (ћопић)

# the books: title, author and year as the library gives them; the village and municipality of their people (for
# matching); offset: scan page minus the book's page
BOOKS = {
    '00000261': dict(title='Lika i Srbi Medačke opštine', author='Dušan Uzelac', year=2004, place='',
                     municipality='Gospić', offset=10),
    '00000397': dict(title='Prigrevica', author='Zorica Korica-Aćimović', year=1997, place='',
                     municipality='', offset=4),
    '00000050': dict(title='Hašani', author='Jovan Jakšić', year=1991, place='Hašani',
                     municipality='Bosanska Krupa', offset=2),
    '00000464': dict(title='Beli Breg (Aleksinac)', author='Slobodan V. Stanojević', year=2009, place='Beli Breg',
                     municipality='Aleksinac', offset=7),
    '00000196': dict(title='Petrlaš: selo koje nestaje', author='Stanimir Stavrov', year=2001, place='Petrlaš',
                     municipality='Dimitrovgrad', offset=None),
    '00000722': dict(title='Prekopčelica, predgrađe Caričinog Grada', author='Nikola C. Stanković', year=2012,
                     place='Prekopčelica', municipality='Lebane', offset=None),
    '00000849': dict(title='Brezovica i Stublica', author='Milan Bogićević, Milan Panić', year=2015,
                     place='Brezovica', municipality='Trstenik', offset=None),
    '00000721': dict(title='Labukovo: zapisi obojeni lirikom', author='Srbislav Jocić', year=2007, place='Labukovo',
                     municipality='Svrljig', offset=None),
    '00000130': dict(title='Donje Vidovo', author='Miroslav Dimitrijević', year=1997, place='Donje Vidovo',
                     municipality='Paraćin', offset=None),
    '00000094': dict(title='Donja Gorevnica (zemlja i ljudi)', author='Radul Marković', year=1996,
                     place='Donja Gorevnica', municipality='Čačak', offset=-5),
    '00000784': dict(title='Podgočka naselja trsteničkog kraja', author='Momčilo R. Todosijević', year=2008,
                     place='', municipality='Trstenik', offset=6),
    '00000430': dict(title='Makce', author='Zorica Korica-Aćimović', year=2000, place='Makce',
                     municipality='Veliko Gradište', offset=4),
}

# the lists: key -> book, scan pages, the heading it starts under and stops at (regexes on the OCR line), kind
# (fighters; spomenica: holders of the medal, alive or not; survivors: fighters who lived through the war; MARKED:
# fighters and victims, the fighters marked), style
LISTS = {
    'medak-pali': dict(book='00000261', pages=(444, 475), style='caps', kind='fighters',
                       heading='Imena boraca narodnooslobodilačkog rata koji su poginuli u borbi sa neprijateljem '
                               'od 1941—1945. godine'),
    'medak-spomenica': dict(book='00000261', pages=(516, 523), style='caps', kind='spomenica',
                            heading='Nosioci Partizanske spomenice 1941. godine'),
    'prigrevica-pali': dict(book='00000397', pages=(311, 336), style='plain', kind='fighters',
                            start=r'Погинули, умрли и нестали борци', stop=r'^\s*\d+\.?\s*Сердар Миће',
                            heading='Poginuli, umrli i nestali borci NOR-a'),
    'prigrevica-spomenica': dict(book='00000397', pages=(343, 357), style='plain', kind='spomenica', stop=r'Борци од 1941',
                                 start=r'Носиоци партизанске споменице', heading='Nosioci partizanske spomenice 1941.'),
    'hasani-pali': dict(book='00000050', pages=(137, 140), style='plain', kind='fighters',
                        start=r'ПОГ.НУЛИ, УМРЛИ И НЕСТАЛИ', stop=r'НОСИОЦИ', subhead=r'^Погинули борци за које',
                        heading='Poginuli, umrli i nestali borci NOR-a iz Hašana'),
    'hasani-spomenica': dict(book='00000050', pages=(140, 141), style='plain', kind='spomenica',
                             start=r'НОСИОЦИ', stop=r'ОСТАЛИ ПРЕ', heading='Nosioci „Partizanske spomenice 1941.“'),
    # 10.5, "survivors recognized as fighters by law for their work for the NOP", mostly women activists, stays out
    'hasani-ucesnici': dict(book='00000050', pages=(141, 142), style='names', kind='survivors',
                            start=r'ОСТАЛИ ПРЕ', stop=r'10\.5|ПРЕЖИВЈЕЛИ БОРЦИ', heading='Ostali preživjeli učesnici NOR-a'),
    # its table goes on with prisoners and internees, royal army men and later JNA officers: those stay out
    'beli-breg': dict(book='00000464', pages=(120, 121), style='table', kind='fighters',
                      start=r'учесници НОР', stop=r'ЗАРОБ.ЕНИ И ИНТЕРНИРАНИ', section=r'^(ПОГИНУЛИ ТОКОМ.*)',
                      heading='Belobrežani učesnici NOR-a'),
    'petrlas': dict(book='00000196', pages=(350, 351), style='table', kind='fighters',
                    start=r'СПИСАК БОРАЦА ПРВЕ ЦАРИБРОДСКЕ', stop=r'Укупан број|Сремском фронту, на реци|Прилог 8|СПИСАК ПОГИНУЛИХ',
                    heading='Spisak boraca Prve caribrodske, 8., 10. i 12. srpske brigade, 13. dopunskog bataljona '
                            'i drugih jedinica NOVJ iz Petrlaša'),
    'prekopcelica-ucesnici': dict(book='00000722', pages=(123, 127), style='plain', kind='fighters',
                                  start=r'13\. српска бригада', stop=r'Погинули у партизанима',
                                  section=r'^\s*(\d+\.\s*(?:српска|јужноморавска|македонска)\s+бригада|'
                                          r'[А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+\s+(?:НОП\s+)?одред(?=\s*\d*\s*$)|\d+\.\s*дивизија|'
                                          r'Прекопчелчани\s+припадници\s+позадинских\s+јединица|Припадници\s+КНОЈ|'
                                          r'Остали\s+учесници\s+НОР)',
                                  # the rear units (auxiliary squads, the front's committees) and those only their
                                  # relatives named stay out
                                  drop_sections=r'позадинских|Остали учесници',
                                  heading='Iz Prekopčelice u brigadama NOVJ'),
    'prekopcelica-pali': dict(book='00000722', pages=(128, 128), style='plain', kind='fighters',
                              start=r'Погинули у партизанима', stop=r'жртв|Жртв|убијен као',
                              heading='Poginuli u partizanima'),
    'brezovica': dict(book='00000849', pages=(117, 119), style='plain', kind='fighters',
                      start=r'УЧЕСНИЦИ НОР–а КОЈИ СУ МОБИЛИСАНИ', stop=r'ОСУ.ЕНИ И СТРАДАЛИ ПОСЛЕ',
                      subhead=r'^(УЧЕСНИЦИ НОР|Вратили|Погинули|Мобилисани)',
                      heading='Učesnici NOR-a koji su mobilisani oktobra 1944.; poginuli i nestali u toku rata'),
    'stublica': dict(book='00000849', pages=(482, 483), style='plain', kind='fighters',
                     start=r'УЧЕСНИЦИ НОР–а', stop=r'ЖРТВЕ ФАШИСТИЧКОГ', subhead=r'^(УЧЕСНИЦИ НОР|Вратили|Мобилисани)',
                     heading='Učesnici NOR-a'),
    # its "fallen in the NOB" also has men killed "od fašističkog terora": civilians, left out
    'labukovo': dict(book='00000721', pages=(46, 47), style='son', kind='fighters', exclude=r'teror|talac|logor',
                     start=r'ПОГИНУЛИ У НОБ', stop=r'длоча|плоча', heading='Poginuli u NOB-u od 1941. do 1945. godine'),
    'donje-vidovo': dict(book='00000130', pages=(129, 130), style='vidovo', kind='MARKED',
                         start=r'СПИСАК ЛИЦА ПОГИНУЛИХ', stop=r'^СПИСАК\s*\d|број заробљеника',
                         heading='Spisak lica poginulih kao učesnici NOB-a, mobilisanih 1944. godine, i žrtava '
                                 'fašističkog terora'),
    # fighters and victims together; a royal army soldier and a civilian are left out (MIXED); its "Poginuli na
    # Sremskom frontu" repeats men of this list
    'gorevnica': dict(book='00000094', pages=(228, 233), style='plain', kind='MIXED', numbered=True, deskew=True,
                      start=r'Пали борци и жртве', stop=r'Поема|Заточеници',
                      heading='Pali borci i žrtve iz Donje Gorevnice u NOB-u 1941–1945. godine'),
    'gornji-ribnik': dict(book='00000784', pages=(200, 201), style='plain', kind='fighters', place='Gornji Ribnik',
                          start=r'Погинули у НОР-у на Сремском', stop=r'Погинули од четника',
                          heading='Poginuli u NOR-u na Sremskom frontu'),
    'odzaci': dict(book='00000784', pages=(350, 351), style='caps', kind='fighters', place='Odžaci',
                   start=r'Учесници НОР–а који су погинули', stop=r'Жртве фашистичког',
                   skip=r'Списак погинулих у НОР|1941-1945\. општине', heading='Učesnici NOR-a koji su poginuli ili '
                                                                         'nestali u toku rata'),
    # the fallen of Makce and its victims of the terror (ŽFT), who stay out; then the fighters who lived, with the
    # year of birth and the medal (the SUBNOR of Veliko Gradište)
    'makce-pali': dict(book='00000430', pages=(66, 68), style='plain', kind='fighters', numbered=True,
                       start=r'Марковић", 1998', stop=r'^Укупно', exclude=r'\bŽFT\b|žrtva fašističkog',
                       heading='Nastradali Makčani u Drugom svetskom ratu — poginuli, umrli, nestali'),
    'makce-preziveli': dict(book='00000430', pages=(68, 70), style='table', kind='survivors',
                            start=r'Презиме и име', stop=r'^Од 94 преживела',
                            heading='Učesnici NOR-a koji su preživeli rat'),
}

# village headings as the OCR gives them -> the village (Medak's lists, by village)
PLACES = {'МЕДАК': 'Medak', 'ПАПУЧА': 'Papuča', 'ПОЧИТЕЛЈ': 'Počitelj', 'ПОЧИТЕЊ': 'Počitelj', 'РАДУЧ': 'Raduč',
          'МОГОРИБ': 'Mogorić', "МОГОРИ'Б": 'Mogorić', 'ПАВЛОВАЦ': 'Pavlovac', 'ВРЕБАЦ': 'Vrebac',
          'ЗАВОБЕ': 'Zavođe', 'КРУШКОВШ': 'Kruškovac', "ВРЕБАЦ, ЗАВО'БЕ И ПАВЛОВАЦ": 'Vrebac, Zavođe i Pavlovac'}
ABBREV = {'НОВ', 'НОБ', 'НОР', 'КПЈ', 'СКОЈ', 'ЈНА', 'ЛПО', 'ВШ', 'МНОО', 'БЈВ', 'УНС', 'НОО', 'ОЗН', 'СУБНОР',
          # a place that ends the line before ("Доњи Лапац, борац ..."), not a name
          'ДОЊИ', 'ДОЊА', 'ДОЊЕ', 'ГОРЊИ', 'ГОРЊА', 'ГОРЊЕ', 'ВЕЛИКИ', 'ВЕЛИКА', 'МАЛИ', 'МАЛА', 'НОВИ', 'НОВА', 'СТАРИ',
          'ДОЊОЈ', 'ГОРЊОЈ'}
# what follows the comma after a name in an entry (else the line goes on the entry before it: "Санског Моста, јула")
ENTRY_REST = rf'(?:рођ|погин|пог\.|умр|нестал|нестао|стрељ|стријељ|убиј|борац|бораца|1[89]\d\d|живи|учесник|y |у |радник|' \
             rf'земљорад|ђак|пољопр|[{UC}]{{2}})'

_names: Counter = Counter()


def corpus() -> None:
    for f in (HERE.parent / 'website' / 'public').glob('*soldiers.json'):
        for s in json.loads(f.read_text(encoding='utf-8')):
            for k in ('last_name', 'first_name', 'middle_name'):
                for w in re.split(r'[\s-]+', s.get(k) or ''):
                    if w:
                        _names[w.upper()] += 1


def fix_name(word: str) -> str:
    """A word of a name: -ИЋ the OCR gives as -ИБ, -ИТЈ, -И'Б, -ИТ}, -ИТ:, -ИВ; a Б read back as Ђ or Ћ, an Њ as Љ,
    where the site's names know that spelling better ("БУРО" = ЂУРО, "МИБО" = МИЋО, "ЊУБОЈЕВИЋ" = ЉУБОЈЕВИЋ)"""
    w = re.sub(r'^["\'’`]+|["\'’`.,;:]+$', '', word)
    w = re.sub(r"И(?:['’]?[БНВ]|Т[Ј}:1]|ТЈ|Т|Ђ)$", 'ИЋ', w) if re.search(r"И(?:['’][БНВ]|Б|Ђ|Т[Ј}:1]?)$", w) else w
    w = re.sub(r"['’]", '', w)
    if not w:
        return w
    cands = {w}
    if w.startswith('Е'):
        cands.add('Ђ' + w[1:])                                         # ЕУРО: ЂУРО
    if re.match(r'Т[ОА](?=[УЈ])', w):
        cands.add('Ђ' + w[2:])                                         # TOYPO, TAYPO: ЂУРО
    cands.add(re.sub(r'(?<=[ИА])(?:В|ТЗ|Т|ТЈ|Н)$', 'Ћ', w))
    if 'Њ' in w:
        cands |= {c.replace('Њ', 'Љ') for c in list(cands)}
    for i, ch in enumerate(w):
        if ch == 'Б':
            cands |= {c[:i] + x + c[i + 1:] for c in list(cands) for x in 'ЂЋ'}
        elif ch in 'ЂЋ':                                                # ЋОРЂЕВИЋ: ЂОРЂЕВИЋ
            cands |= {c[:i] + ('Ћ' if ch == 'Ђ' else 'Ђ') + c[i + 1:] for c in list(cands)}
    return max(sorted(cands), key=lambda c: (_names[latin(c).upper()], c == w))     # sorted: the same choice every run


def fix(s: str) -> str:
    """A name word in the Latin the records use, capitalized"""
    return '-'.join(p[:1].upper() + p[1:].lower() for p in latin(fix_name(s.upper())).split('-')) if s else ''


def load_book(num: str) -> dict:
    whole = CACHE / f'{num}.json'
    if whole.exists():
        return json.loads(whole.read_text(encoding='utf-8'))
    survey = json.loads((CACHE / 'survey.json').read_text(encoding='utf-8'))
    doc = COLLECTION + num
    return {'id': doc, 'pages': {k.rsplit('|', 1)[1]: v for k, v in survey['ocr'].items()
                                 if k.startswith(doc + '|') and v}}


def deskewed_lines(book: dict, page: int) -> list[Line]:
    """A tilted, curved scan's lines (Donja Gorevnica, whose entry numbers otherwise come out as lines of their own
    after the names): each word, from left to right, joins the line whose last word ends just before it at about its
    height; the lines are then put in order along the page's slope"""
    words = page_words(book, page)
    if not words:
        return []
    h = sorted(w.height for w in words)[len(words) // 2] or 1
    chains = []
    for w in sorted(words, key=lambda w: w.x0):
        near = [c for c in chains if -h < w.x0 - c[-1].x1 < 4 * h and abs(c[-1].middle - w.middle) < 0.45 * h]
        if near:
            min(near, key=lambda c: abs(c[-1].middle - w.middle)).append(w)
        else:
            chains.append([w])

    def spread(s):                      # how far a line's words stray from a straight line of slope s
        return sum(abs((w.middle - s * w.x0) - (c[0].middle - s * c[0].x0)) for c in chains for w in c)
    slope = min((s / 1000 for s in range(-30, 31)), key=spread)
    chains.sort(key=lambda c: c[0].middle - slope * c[0].x0)
    return [Line(c) for c in chains]


def rows_of(book: dict, L: dict) -> list[tuple[int, float, str]]:
    """The list's lines, from the line after its heading to the line before the heading it stops at"""
    out, started = [], 'start' not in L
    for p in range(L['pages'][0], L['pages'][1] + 1):
        lines = deskewed_lines(book, p) if L.get('deskew') else page_lines(book, p, 1)[0]
        for line in lines:
            t = line.text.strip()
            if not t:
                continue
            if not started:
                started = bool(re.search(L['start'], t))
                continue
            if 'stop' in L and re.search(L['stop'], t):
                return out
            out.append((p, line.x0, t))
    return out


LOOKALIKE = str.maketrans('TopyaecxKMHBAEOPCXknr', 'ТоруаесхКМНВАЕОРСХкпг')     # "nor." = пог.


def clean_line(t: str) -> str:
    # a word in the Latin letters that look like Cyrillic ones ("Toypo", "Бумаth") among Cyrillic words
    t = re.sub(r'\b[A-Za-z][A-Za-zА-Яа-яЂЈЉЊЋЏђјљњћџ]*\b',
               lambda m: m.group(0).translate(LOOKALIKE) if re.fullmatch(r'[TopyaecxKMHBAEOPCXknrА-Яа-яЂЈЉЊЋЏђјљњћџ]+', m.group(0))
               and re.search(r'[А-Яа-я]', t) else m.group(0), t)
    t = re.sub(rf'(^|[.,]\s+)(?:\S*[^\w\s.,;:„“"\'’()–—-]\S*\s+)+(?=[\d.]*\s*[\"\'’]?[{UC}])', r'\1', t)
    t = re.sub(r'\b(1[89]\d)[OОoо]\b', r'\g<1>0', t)                       # 191O
    t = re.sub(r'(?<![\w.])([БГДЂЖЗЈЛЉМНЊПРТЋФХЦЧЏШ]) (?=[а-яђјљњћџ]{2,})', r'\1', t)     # "Ј ове"; not И, У, А, О, С, К, В
    return re.sub(rf'(^|\.\s+)([\d.]*\s*[{UC}])\s([{UC}]{{2,}})', r'\1\2\3', t)


NUM = r'^\W*(?:\d{1,3}\s*[.,)]?\s*)?[\W_]*'
STYLES = {
    # "N. SURNAME Father GIVEN, 1921, trade, ethnicity. ..."
    'caps': re.compile(NUM + rf"(?P<name>[{FIRST}][{UC}'’\"}}:ћђ]+(?:\s+[{UC}'’\"}}:]{{2,}})*(?:\s+(?:рођ\.|р\.)\s+[{UC}'’]+)?(?:\s*\([{UC}][{LC}]+\))?"
                       rf"(?:\s+[\"'’]?[{UC}][{LC}]+){{0,2}}(?:\s+[\"'’]?[{UC}][{UC}'’\"}}:]+)*(?:\s*[–—-]\s*[{UC}]+)?)"
                       rf"\s*,\s*(?P<rest>.*)$"),
    # "N. Surname Father Given [Nick], рођен 1921 ..." or "Surname (Father) Given (4.7.1920.), у НОР ..."
    'plain': re.compile(NUM + rf"(?P<name>[\"'’]?[{FIRST}][{LC}]+(?:\s*[–-]\s*[{UC}][{LC}]+)?(?:\s*\([^)]*\))?(?:\s+[\"'’]?[{UC}][{LC}]+"
                        rf"(?:\s*[–-]\s*[{UC}][{LC}]+)?|\s*\([^)]*\)){{1,4}})\s*(?:,\s*(?P<rest>{ENTRY_REST}.*)|"
                        rf"(?P<rest2>\(\s*\d.*))$"),
    # "N. Surname Father Given 1921 ..." (a table without commas)
    'table': re.compile(r'^\W*(?:\d{1,3}\s*[.,)]?\s*)?' + rf"(?P<name>[\"'’]?[{FIRST}][{LC}]+(?:\s+[{UC}]\.)?(?:\s+[\"'’]?[{UC}{LC}][{LC}]+){{1,3}}"
                        rf"(?:\s*[·—–-]\s*[{UC}][{LC}]+)?)\s+(?P<rest>1[89]\d\d.*)$"),
    # "N. SURNAME Father GIVEN 1922 јануара 1945. од Немаца НОБ"
    'vidovo': re.compile(r'^\W*\d{1,3}\s*[.,)]?\s*' + rf"(?P<name>[{UC}'’\s\dћђ]{{3,}}\s+[{UC}][{LC}]+\s+[{UC}][{UC}{LC}'’]+)"
                         rf"\s*(?P<rest>1[89]\d\d.*)$"),
    # ". Surname Father Given" or "N. Surname Father Given, 1921." (names only, often two to a line)
    'names': re.compile(r'^\W*(?:\d{1,3}\s*[.,)]?)?[\W_]*' + rf"(?P<name>[\"'’]?[{FIRST}][{LC}]+(?:\s+[\"'’]?[{UC}][{LC}]+){{1,3}})"
                        rf"(?P<rest>(?:\s*[–—-]+\s*[{UC}][{LC}]+)?(?:\s*\([^)]*\))?\s*(?:,\s*1[89]\d\d\.?)?[\W_]*)$"),
    # a numbered list: "N. Surname Father Given, trade, ..." whatever the trade, a letter of the name in the wrong case
    # ("19. ЈанковИћ Радомира Милуника, домаћица", "47. Николић милијана Драгољуб, бравар")
    'numbered': re.compile(r'^\W*\d{1,3}\s*[.,)]\s*' + rf"(?P<name>[\"'’]?[{FIRST}][{UC}{LC}]+(?:\s+[\"'’]?[{UC}{LC}][{UC}{LC}]+){{1,3}})"
                           rf"\s*[,.]\s*(?P<rest>.*)$"),
    # "Surname Given, Tasin sin, rođen ..." / "Surname Given, sin Viden(a) i ... iz familije ..., rođen ..."
    'son': re.compile(rf"^(?P<name>[{UC}][{LC}]+\s+[{UC}][{LC}]+)\s*,\s*(?P<rest>(?:[{UC}][{LC}]+н\s+син|син\s).*)$"),
}


def entries_of(rows: list[tuple[int, float, str]], L: dict, book_place: str) -> list[dict]:
    style = STYLES[L['style']]
    out, place, cur, unit = [], book_place, None, ''
    for page, x0, t in rows:
        t = clean_line(t)
        if L['style'] == 'caps' and x0 > 900 and len(t.split()) <= 5 and not re.search(r'\d{3}', t):
            key = t.strip(" .'’")
            if key.upper() in PLACES or key in PLACES:
                place = PLACES.get(key.upper(), PLACES.get(key))
                continue
            if re.fullmatch(r'[\W\d_]*', t) or len(t) <= 3:
                continue
        if L.get('skip') and re.search(L['skip'], t):
            continue
        if re.fullmatch(r'[\d\W]{1,6}', t) or re.match(rf'^\d{{2,3}}[{UC}][{LC}]', t):     # page numbers, footnotes ("143Јован")
            continue
        if L.get('section') and re.match(L['section'], t):
            unit = re.sub(r'\d+$', '', re.match(L['section'], t).group(1)).strip()   # footnote numbers off
            unit = unit.replace(' 1/1 ', ' И ')                       # "ПОГИНУЛИ ТОКОМ 1/1 УМРЛИ"
            if unit == unit.upper() and len(unit) > 12:
                unit = unit[0] + unit[1:].lower()
            cur = None
            continue
        if L.get('subhead') and re.match(L['subhead'], t):
            cur = None
            continue
        if L['style'] == 'caps':
            parts = re.split(rf"(?<=[{LC}.,])\s+(?=(?:\d{{1,3}}\.|\.)\s*[\"'’]?[{UC}]\s?[{UC}]{{2,}}[^,]{{0,40}},\s*1[89]\d\d)", t)
        elif L['style'] in ('plain', 'names'):
            # two entries side by side: "1. Штиковац Буре Бошко, 1921. 4. Раилић Буре Коста", ". Балаћ Јове Перо . Новаковић"
            parts = re.split(rf"(?<=\S)\s+(?=(?:\d{{1,3}}\.|\.)[–-]?\s*[\"'’]?[{FIRST}][{LC}]+(?:[–-][{UC}][{LC}]+)?\s+[{FIRST}][{LC}]+\s+[{FIRST}][{LC}]+)", t)
        elif L['style'] == 'table':
            parts = re.split(rf"(?<=\S)\s+(?=\d{{1,3}}\.\s+[{FIRST}][{LC}]+\s)", t)     # "... 1926 Медаља 4. Аћимовић ..."
        elif L['style'] == 'vidovo':
            parts = re.split(rf"(?<=\S)\s+(?=\d{{1,3}}\.\s*[{UC}]{{3,}})", t)     # "...\" \" 8.ЈЕВТИЋ Живојина ..."
        else:
            parts = [t]
        if L['style'] == 'names':
            parts = [q for p in parts for q in re.split(r'\s+\.\s+', p)]
            parts = [q for p in parts for q in (
                [' '.join(re.findall(rf'[{FIRST}][{LC}]+', p)[:3]), ' '.join(re.findall(rf'[{FIRST}][{LC}]+', p)[3:])]
                if re.fullmatch(rf'[\W\d]*(?:[{FIRST}][{LC}]+\s+){{5}}[{FIRST}][{LC}]+[\W]*', p) else [p])]
        for part in parts:
            m = style.match(part)
            if m and L.get('numbered') and not re.match(r'^\W*\d{1,3}\s*[.,)]', part):
                m = None                                             # a numbered list: a line without a number goes on
            if not m and L['style'] == 'plain' and re.match(r'^\W*\d{1,3}\s*[.,)]', part):
                m = STYLES['names'].match(part)                      # a numbered entry that gives only the name
            if not m and L.get('numbered'):
                m = STYLES['numbered'].match(part)
            first = m.group('name').split()[0].strip("'’\"") if m else ''
            if m and first.upper() not in ABBREV and len(first) >= 3:
                rest = m.group('rest') if 'rest' in m.groupdict() and m.group('rest') is not None else m.group('rest2')
                name = m.group('name')
                if L.get('numbered'):
                    name = ' '.join(w[0].upper() + w[1:].lower() for w in name.split())
                cur = {'page': page, 'name': name, 'text': [rest or ''], 'place': place, 'unit': unit}
                out.append(cur)
            elif L['style'] == 'table' and re.match(r'^\W*\d{1,3}\s', part):
                cur = None                                           # a row whose name the OCR garbled
            elif cur:
                cur['text'].append(part)
    return out


def split_name(raw: str, style: str) -> tuple[str, str, str, str, str]:
    """(surname, father, given, nickname, maiden name) as the records spell them"""
    raw = raw.replace('"', ' ').replace('—', '–').replace('·', '–')
    raw = re.sub(r'^(\S+)\s+[–-]\s+', r'\1-', raw.strip())                  # Корица – Новковић
    maiden = ''
    m = re.search(r'\s(?:рођ\.|р\.)\s+([^\s]+)', raw)
    if m:
        maiden, raw = m.group(1), raw[:m.start()] + raw[m.end():]
    if style in ('caps', 'vidovo'):
        raw = re.sub(r'\(([{UC}][{LC}]+)\)'.replace('{UC}', UC).replace('{LC}', LC), r' \1 ', raw)   # ЋУРКОВИЋ (Стевана) МИЛОСАВ
        toks = [t.strip("'’`") for t in re.split(r'\s+|\s*–\s*', raw) if t.strip("'’`")]
        sur = []
        while toks and re.fullmatch(rf"[{UC}'’}}:1ћђ]+", toks[0]) and len(toks) > 1:
            sur.append(toks.pop(0))
            if toks and not re.fullmatch(rf"[{UC}'’}}:1ћђ]+", toks[0]):
                break
        father = toks.pop(0) if toks and re.fullmatch(rf'[{UC}][{LC}]+', toks[0]) and len(toks) > 1 else ''
        given = toks[0] if toks else ''
        nick = ' '.join(toks[1:])
        return ' '.join(fix(s) for s in sur), fix(father), fix(given), ' '.join(fix(n) for n in nick.split()), fix(maiden)
    # Title case: "Surname Father Given [Nick]", "Surname (Father) Given", "Surname Given" ('son' style)
    raw = re.sub(r'\([^)]*\d[^)]*\)', ' ', raw)                      # a birth date in brackets is no father
    paren = re.search(r'\(([^)]*)\)', raw)
    father = paren.group(1).strip() if paren else ''
    toks = [t.strip("'’`") for t in re.sub(r'\([^)]*\)', ' ', raw).split() if t.strip("'’`")]
    toks = [t.split('–')[0].split('-')[0] if i == 1 and not paren and len(toks) > 2 else t for i, t in enumerate(toks)]
    if style == 'son' or len(toks) == 2:
        sur, given, nick = toks[0], toks[-1], ''
    elif paren:
        sur, given, nick = toks[0], toks[1] if len(toks) > 1 else '', ' '.join(toks[2:])
    else:
        sur, father, given, nick = toks[0], toks[1], toks[2] if len(toks) > 2 else '', ' '.join(toks[3:])
    nick = re.sub(r'^[–-]\s*', '', nick)
    return fix(sur), fix(father), fix(given), ' '.join(fix(n) for n in nick.split()), fix(maiden)


# an entry the line reader left inside the one before it: a number (or the list's dot) and three capitalized words, then
# a comma, "rođen" or a year ("... kod Prijedora 63. Zorić Marka Nikola, Mala Krupska Rujiška")
GLUED = re.compile(r'(?<=\S)\s+(?:\d{1,3}\.|\.)\s+(?=[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:-[A-ZČĆŽŠĐ][a-zčćžšđ]+)?\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+'
                   r'(?:\s*\([^)]*\))?\s*(?:,|rođ|1[89]\d\d))')


# a fighter in a list of fighters and victims: what the entry says he was; a royal army soldier or a Chetnik is not
FIGHTER = re.compile(r'\bbor(?:ac|kinja)\b|\bpartizan|\bdesetar\w*|\bkomandir\w*|\bkomesar\w*|\bvodnik\b|\bNOVJ\b|\bbrigad|'
                     r'\bbataljon|\bodred\b|\bodreda\b|učesnik NO', re.I)
# a reserve officer of the royal army who led a partisan company is a fighter (Lukić Vlajka Bogoljub, Donja Gorevnica)
PARTISAN_UNIT = re.compile(r'\bbataljon|\bNOP odred|\bNOVJ\b|\bKNOJ|\bpartizansk|\bbrigad|\bdivizij', re.I)
NOT_FIGHTER = re.compile(r'\bBJV\b|vojnik Kraljev|\bkao četnik|u četnicima|četničk\w+ (?:odred|korpus|brigad|komand)', re.I)
DEATH = re.compile(r'\b(?:[Pp]oginu|[Pp]og\.|[Uu]mr[oaij]|[Ss]trij?elj|[Uu]bi[ljj]|[Ss]mrz|[Zz]akla|[Oo]bjes|[Oo]bes|'
                   r'[Nn]esta|[Ss]palj|[Pp]odleg)\w*[^;]{0,160}?\b(19[34]\d)\b')
BIRTH = re.compile(r'(?:\b[Rr]o(?:đ|dj)en[a]?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?|^\s*\(?\s*(?:\d{1,2}\.\s*\d{1,2}\.\s*)?)'
                   r'(1[89]\d\d)\b')
# "rođen 1907. u selu Mogorić, Gospić"; the OCR drops the "u" or the year, adds a comma, or puts the place in lower case
# ("rođen, 1920. u Šamaračkim Brđanima", "rođen 1906. Javornik", "rođen 1913. u ljubini, Dvor na Uni")
BORN_IN = re.compile(r'\b[Rr]o(?:đ|dj)en[a]?,?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(?:1[89]\d\d\.?\S?\s*)?(?:god(?:ine|\.)\s*)?'
                     r'(?:[uy]\s+(?:[Ss]el[ou]\s+|[Ss]epu\s+)?(?=[A-ZČĆŽŠĐa-zčćžšđ])|(?=[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+)?,))([^\W\d][^,;.]*(?:,\s*[A-ZČĆŽŠĐ][^,;.]*)?)')


def main():
    corpus()
    only = sys.argv[sys.argv.index('--list') + 1] if '--list' in sys.argv else None
    books = {}
    entries, counts = [], Counter()
    for key, L in LISTS.items():
        if only and key != only:
            continue
        book = books.setdefault(L['book'], load_book(L['book']))
        meta = BOOKS[L['book']]
        for e in entries_of(rows_of(book, L), L, L.get('place', meta.get('place', ''))):
            text = ' '.join(e['text'])
            if L['style'] == 'table':
                # a table's columns the OCR garbled into Latin letters and runs of digits ("Gepagpžršžž' 4222313231313,")
                text = re.sub(r'\S*(?:[A-Za-zÀ-ž]{3,}|\d{7,})\S*', ' ', text)
                text = re.sub(r"\.\s?(?:0к[тг]|ок·г|0к'г|0KT)\.", '.окт.', text).replace('.н0в.', '.нов.')
                text = re.sub(r'\s+', ' ', text)
            text = latin(text).strip()
            # Latin look-alikes the OCR gives for Cyrillic words ("y ceny" = u selu) and -ić read as -iđ (Gospiđ)
            text = re.sub(r'\by\s+ceny\b', 'u selu', text)
            text = re.sub(r'\by\b', 'u', text)
            text = re.sub(r'(?<=[a-zčćžšđ])iđ\b', 'ić', text)
            # the divisions' Roman numerals as the OCR reads them ("U! proleterske", "UN banijske", "HHHU divizije")
            text = re.sub(r'(?<!\S)(?:U!|Vl|U\||U1|V\|)(?=\s+(?:proleterske|ličke)\b)', 'VI', text)
            text = re.sub(r'(?<!\S)(?:UN|U!!|VI\||Vll|V\|I)(?=\s+banijske\b)', 'VII', text)
            text = re.sub(r'(?<!\S)HHHU(?=\s+divizije\b)', 'XXXV', text)
            text = re.sub(r'(?<!\S)XlX(?=\s)', 'XIX', text)
            text = re.sub(r'(?<!\S)(\|{1,3})(?=\s+(?:proleterske|krajiške|ličke|brigade|divizije|bataljona)\b)',
                          lambda m: 'I' * len(m.group(1)), text)                        # "borac || proleterske brigade"
            text = re.sub(r'(?<=[a-zčćžšđ])\](?=\s)', 'j', text)                         # "Široko] Kuli"
            text = re.sub(r'(?<!\S)\](?=\.)', '1', text)                                  # "]. bat."
            text = re.sub(r'(?<=\d\.)[áéíóú]|[←\\]', '', text)                           # stray marks
            text = re.sub(r'\b([Uu]) (?:[Ss]epu|Selu)\b', r'\1 selu', text)              # "u sepu Široka Kula"
            text = re.sub(r'([a-zčćžšđ]) · ([A-ZČĆŽŠĐ])', r'\1-\2', text)               # "Rašeta · Slećaš"
            # the book's page number or a footnote after the last entry of a page ("Umro je 1976. godine. 99",
            # "66. Podaci uzeti iz evidencije ...")
            text = re.sub(r'\s+\d{1,3}\.?\s+(?:Podaci|Izvor|Prema|Spisak je)\b.*$', '', text)
            text = re.sub(r'(?<=\.)\s+\d{1,3}$', '', text.strip())
            text = re.sub(r'(?:\s+\S*[°+_=~^*#@<>{}|]\S*)+$', '', text)                 # "Srbin rrfčfdž+", "mmm__"
            text = re.sub(r'\bNjubi(?=ć)', 'Ljubi', text)                  # Љ read as Њ (Ljubić, Donja Gorevnica)
            text = re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', text)
            # a capital the OCR set apart from the rest of its word ("Donjoj G orevnici"); not the one-letter words
            text = re.sub(r'\b([BCDGHJLMNPRTFČĆŠĐŽ]) (?=[a-zčćžšđ]{3,})', r'\1', text)
            text = re.sub(r'\b([A-ZČĆŽŠĐ][a-zčćžšđ]{2,}?)[d,]?(rođena?\s+1[89]\d\d)', r'\1, \2', text)   # "Perodrođen 1921."
            head, *rest = GLUED.split(text)
            tails = [(m.group(1), m.group(2)) for m in (re.match(r'(\S+\s+\S+\s+\S+(?:\s*\([^)]*\))?)\s*,?\s*(.*)$', r, re.S)
                                                     for r in rest) if m]
            for name, style, text in [(e['name'], L['style'], head)] + [(n, 'plain', t) for n, t in tails]:
                if L['kind'] == 'MARKED':
                    # Donje Vidovo: "... od Nemaca NOB" or ditto marks for the line above
                    # a line with no category ("od četnika", "od ustaša") is not taken for a fighter, nor dittos under it
                    if re.search(r'\bNOB\b', text):
                        kind = 'NOB'
                    elif re.search(r'["“”]\s*["“”]?\s*$', text):
                        kind = counts.get(key + ' last', 'other')
                    else:
                        kind = 'other'
                    counts[key + ' last'] = kind
                    if kind != 'NOB':
                        counts[key + ' left out'] += 1
                        continue
                if L['kind'] == 'MIXED' and (not FIGHTER.search(text) or (NOT_FIGHTER.search(text) and not PARTISAN_UNIT.search(text))):
                    counts[key + ' left out'] += 1
                    continue
                if L.get('drop_sections') and re.search(L['drop_sections'], e.get('unit') or ''):
                    counts[key + ' left out'] += 1
                    continue
                if L.get('exclude') and re.search(L['exclude'], text, re.I):
                    counts[key + ' left out'] += 1
                    continue
                sur, father, given, nick, maiden = split_name(name, style)
                if not sur or not given:
                    counts[key + ' unreadable'] += 1
                    continue
                if L['style'] == 'son':
                    son = re.match(r'([A-ZČĆŽŠĐ][a-zčćžšđ]+)n\s+sin|sin\s+([A-ZČĆŽŠĐ][a-zčćžšđ]+)', text)
                    father = (son.group(1) + 'e') if son and son.group(1) else (son.group(2) if son else '')
                year = BIRTH.search(text)
                place = e['place'] or ''
                if ' i ' in place or ',' in place:                       # a heading over several villages
                    own = re.match(r'^\s*1[89]\d\d\s*,\s*([A-ZČĆŽŠĐ][a-zčćžšđ]+)', text)
                    place = own.group(1) if own and own.group(1) in place else ''
                own = BORN_IN.search(text)
                born_in = own.group(1).strip()[:1].upper() + own.group(1).strip()[1:] if own else ', '.join(x for x in (place, meta['municipality']) if x)
                death = DEATH.search(text)
                unit = e.get('unit') or ''
                n = len(entries) + 1
                entries.append({'soldier_id': f'{PREFIX}{n:06d}',
                                'name': f"{sur}{' (' + maiden + ')' if maiden else ''} {father + ' ' if father else ''}{given}"
                                        f"{' – ' + nick if nick else ''}",
                                'last_name': sur, 'first_name': given, 'nick': nick, 'fathers_name': father,
                                'birth_year': year.group(1) if year else '', 'born_in': born_in,
                                'death_year': death.group(1) if death and L['kind'] not in ('spomenica', 'survivors') else '',
                                # alive after the war: a list of those who lived, or an entry that says so ("Živi u
                                # Prigrevici", "Umro je 1981. godine")
                                'survived': L['kind'] == 'survivors' or bool(re.search(
                                    r'\bŽiv[ie]\b|\b[Uu]mr\w*\s+(?:je\s+)?(?:194[6-9]|19[5-9]\d|20\d\d)', text)),
                                'additional_info': (latin(unit) + ': ' if unit else '') + text, 'list': key,
                                'list_heading': L['heading'], 'book_title': meta['title'],
                                'source_url': viewer_url({'id': COLLECTION + L['book']}, e['page']),
                                'source_page': e['page'] - meta['offset'] if meta.get('offset') is not None else
                                printed_page(book, e['page'])})
                counts[key] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(entries)} entries:', {k: v for k, v in counts.items() if not k.endswith(' last')})
    if '--sample' in sys.argv:
        import random
        random.seed(2)
        pool = [e for e in entries if not only or e['list'] == only]
        for e in random.sample(pool, min(len(pool), int(sys.argv[sys.argv.index('--sample') + 1]))):
            print(f"\n{e['soldier_id']} {e['list']} p.{e['source_page']} | {e['name']} | b. {e['birth_year']} {e['born_in']} "
                  f"| d. {e['death_year']}\n   {e['additional_info'][:200]}")


if __name__ == '__main__':
    main()
