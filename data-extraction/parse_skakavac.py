"""
Скакавац и Скакавчани код Петровца (Poreklo library, doc 00000067): the fighters and the movement's people of the
village Skakavac by Bosanski Petrovac, as a book across units. Cyrillic; the OCR reads the font's Ђ as Б, В or Е
after a speck ("'Бурић" Đurić, "“Вилас" Đilas, ""Еуро" Đuro) and its Ћ as ћ, splits a J from its word ("Ј ове"),
and gives the Roman numerals of the brigades as "111", "Ш" (III), "И" (II), "УН" (VII), "У" (V), "Х" (X). Names are
read back as the site spells them (_village_books). Lists, numbered, a bio each, "Surname Father Given":
  - "Првоборци Скакавца" (scan pp. 167-169): the 23 who lived through the war and hold the Partizanska spomenica
    1941; p. 169's two bios, which the OCR scattered over the page, are typed from its pieces (`TYPED`);
  - "Списак Скакавчана учесника НОР-а који су преживјели рат" (pp. 170-177): 84, "(1927-1989)" their birth and
    death; one the bio names only a participant of the NOR ("учесник НОР-а од 1942. до 1945.") is marked
    `role: 'participant'` (the user's decision of 2026-10-20 for lists that don't tell a fighter from an activist);
  - "Погинули борци у народно-ослободилачком рату" (pp. 177-181): 67;
  - the movement's people, names only (pp. 185-195): the NOO, the fund's and the AFŽ's committees of 1941-1943, the
    MNOO of Skakavac and its neighbours, the municipal NOO, AFŽ and Narodni front, the war youth's leaders and the
    members of its organization, the party cell and its candidates, the inter-municipal and municipal committees,
    the partisan furriers' workshop (`activists`). A name that fits one entry of the lists above is that man and
    joins his entry; the rest are entries of their own, `role: 'activist'`, one a person.
Out: the victims of terror (pp. 183-184) and the colonists' lists after the war (p. 201 on).

Output: data-extraction/poreklo/skakavac-entries.json, IDs 9086xxxxxx: the prvoborci 9086000001-023, the survivors
9086000101-184, the fallen 9086000201-267, the activists 9086001001 on (in the order the book first names them).
Usage: python data-extraction/parse_skakavac.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
import parse_trebinjci_pali as T  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'skakavac.json'
OUT = HERE / 'poreklo' / 'skakavac-entries.json'
PREFIX = '9086'
OFFSET = 4                                  # scan page minus the book's page (p. 167 is the book's 163)
TITLE = 'Skakavac i Skakavčani kod Petrovca'
VILLAGE = 'Skakavac, Bosanski Petrovac'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
LISTS = [('prvoborci', range(167, 170), 'Prvoborci Skakavca koji su preživjeli rat i dobili Partizansku spomenicu 1941',
          0, 'ПРВОБОРЦИ', 'По презименима'),
         ('survivors', range(170, 178), 'Spisak Skakavčana učesnika NOR-a koji su preživjeli rat', 100,
          'СКАКАВЧАНА УЧЕСНИКА', 'ПОГИНУЛИ'),
         ('fallen', range(177, 182), 'Poginuli borci u narodno-oslobodilačkom ratu', 200,
          'Борци у народно-ослободилачком', 'Погштули по презименима')]
# p. 169: two bios the OCR set word by word over the page, typed from its pieces in their order
TYPED = {('prvoborci', 22): 'Чича Дане Лука рођен 1921. године, земљорадник, учесник НОР-а од 1941. године, борац у '
                            'јединицама V крајишког одреда и VII крајишке бригаде. По завршетку рата остао на служби у '
                            'ЈНА. Завршио одговарајућу официрску школу и пензионисан у чину мајора. Сада живи у Новом '
                            'Београду.',
         ('prvoborci', 23): 'Чурчић Косте Јово рођен 1915. године, земљорадник и сезонски радник. Учесник НОР-а од 1941. '
                            'године, борац у III крајишкој бригади од њеног оснивања. Учесник битке на Сутјесци и '
                            'Неретви. По завршетку рата демобилисан, а 1946. године колонизиран у Челарево гдје је и '
                            'умро 1990. године.'}
# the movement's people (pp. 185-195), as the book names them, the given name first, under each body; the
# village the body is of (else Skakavac)
COMMITTEES = [
    ('NOO Skakavca (oktobar 1941)', '', 185, ['Savo Ćulibrk', 'Vaso Knežević', 'Marko Stupar-Vujinović', 'Božo Dukić-Radošević']),
    ('NOO Marjanović Dola (oktobar 1941)', '', 185, ['Dušan Kerkez-Bikan', 'Mile Pećanac', 'Nikola-Nina Đaković', 'Blažo Marjanović']),
    ('Odbor fonda Skakavca', '', 185, ['Pero Marjanović', 'Rade Brkljač', 'Mile Stupar-Ćotlić']),
    ('Odbor fonda Marjanović Dola', '', 186, ['Mića Marjanović', 'Jovo Kerkez', 'Boja Dragišić']),
    ('pomogli organizovanje narodne vlasti', '', 186, ['Ilija Došen', 'Jovo Kecman-Šuco', 'Zdravko Čelar', 'Milan Guteša']),
    ('Odbor AFŽ-a Skakavca', '', 186, ['Stana Ćulibrk', 'Milka Čurčić', 'Boja Petković-popadija']),
    ('Odbor AFŽ-a Marjanović Dola', '', 186, ['Vela Kecman', 'Mara Branković', 'Đuja Marjanović']),
    ('MNOO sela Vođenice', 'Vođenica, Bosanski Petrovac', 186, ['Branko Stupar', 'Mićo Jokić', 'Rade Ćulibrk', 'Dragica Tešić', 'Vaso Bjelić']),
    ('Odbor AFŽ-a sela Vođenice', 'Vođenica, Bosanski Petrovac', 186, ['Dragica Šmonja', 'Milica Latković', 'Marija Ćurguz', 'Deva Marinković', 'Jelka Brkljač']),
    ('MNOO sela Suvaje', 'Suvaja, Bosanski Petrovac', 186, ['Marko Đumić', 'Jovo Milanović', 'Petar Grbić-Pepica', 'Simo Knežević', 'Pajo Grbić-Pajica']),
    ('Odbor AFŽ-a sela Suvaje', 'Suvaja, Bosanski Petrovac', 186, ['Milica Grbić', 'Milka Đumić', 'Anđa Pećanac', 'Ruža Knežević']),
    ('MNOO sela Skakavca', '', 187, ['Dušan Kerkez-Bikan', 'Trivun Knežević', 'Mara Stupar', 'Zorka Grbić', 'Dušan Kerkez-Lazin']),
    ('Odbor AFŽ-a sela Skakavca', '', 187, ['Dragica Ćulibrk', 'Boja Petković-popadija', 'Đuja Marjanović', 'Trivuna Knežević']),
    ('MNOO sela Brestovca', 'Brestovac, Bosanski Petrovac', 187, ['Nikola Selaković', 'Koviljka Bulajić', 'Mićo Bulajić', 'Simeuna Lajić']),
    ('Odbor AFŽ-a sela Brestovca', 'Brestovac, Bosanski Petrovac', 187, ['Cuka Bulajić', 'Kosa Selaković', 'Milka Mirčeta', 'Danica Lajić']),
    ('Opštinski NOO Vođenice (oktobar 1943)', '', 187, ['Marko Šipka', 'Mile Pećanac', 'Jovo Ćulibrk-Joviš', 'Milan Jovanić', 'Jovan Bulajić', 'Dušan Grubiša']),
    ('Opštinski odbor AFŽ-a', '', 187, ['Anđa Pećanac', 'Deva Marinković', 'Đuja Lajić', 'Sava Egelja', 'Trivuna Knežević', 'Milica Latković', 'Perka Jokić']),
    ('Opštinski odbor Narodnog fronta', '', 187, ['Milan Jovanić', 'Todor Šipka', 'Dušan (Laze) Kerkez']),
    ('rukovodioci omladine Skakavca', '', 190, ['Božo Grbić', 'Dušan (Jove) Ćulibrk', 'Đorđe (Nikole) Đaković', 'Ilija (Petra) Ćuk',
                                           'Gojko (Pere) Marjanović', 'Stana (Josipe) Knežević', 'Mara (Laze) Stupar']),
    ('partijska ćelija Skakavca (1942)', '', 194, ['Savo Ćulibrk', 'Vaso Knežević', 'Dako Latković', 'Jovo Latković-Palamušić', 'Simo Drljača', 'Kosta Kecman']),
    ('kandidatska grupa KPJ (1942)', '', 194, ['Mile Pećanac', 'Dušan Kerkez-Bikan', 'Đorđe Đaković']),
    ('međuopštinski komitet KPJ (1942)', '', 194, ['Đuro Milanović-Brico', 'Savo Miljuš', 'Dako Latković', 'Milan Guteša', 'Milan Karanović',
                                               'Savo Ćulibrk', 'Mira Brkljač-Pavić']),
    ('partijska organizacija Skakavca i Suvaje (1943)', '', 194, ['Mile Pećanac', 'Marko Šipka', 'Anđa Pećanac', 'Pajo Grbić', 'Dragica Grbić',
                                                             'Milka Đumić', 'Gojko Marjanović']),
    ('partijska organizacija Vođenice i Brestovca (1943)', '', 194, ['Jovo Latković', 'Milka Egelja', 'Jovan Bulajić', 'Milan Jovanić', 'Milka Vojinović']),
    ('Opštinski komitet KPJ za Vođenicu (1944)', '', 194, ['Boško Kecman', 'Mile Pećanac', 'Đorđe Đaković', 'Anđa Pećanac', 'Đuro (Vasilije) Kerkez']),
    ('partizanska kožunarska radionica', '', 195, ['Božo Petković', 'Drago Knežević', 'Mirko Budimir', 'Mićo Debeljak']),
]
YOUTH = 'članovi omladinske organizacije Skakavca'
MENTIONS = 'Pripadnici NOP-a u Skakavcu i okolini'
ROMAN_UNIT = {'111': 'III', 'Š': 'III', 'UN': 'VII', 'UP': 'VII', 'UŠ': 'VIII', 'U': 'V', 'I': 'II', 'H': 'X'}


# the OCR's slips in names, as the list around them shows (the other entries of the family)
SLIPS = [('Кнежевт ћ', 'Кнежевић'), ('Кесман', 'Кецман'), ('Масрјановић', 'Марјановић'), ('Сандрач', 'Сантрач')]
# the soldier's words of these bios, whose "učesnik NOR-a" the mixed lists' rule takes for an activist's: a unit,
# the army, demobilized, a duty in a unit
FIGHTER_WORDS = re.compile(r'demobili|\bbrigad|bataljon|\bodred|\bjedinic|\bvojsk|komand\w*\s+mj?est|\bpartizan|\bKNOJ|'
                           r'\barmij|\bborac|\bborb|komandir|komesar|vodnik|artiljer|\bustan', re.I)
PARTICIPANT = re.compile(r'\b(?:aktivn\w*\s+)?učesni\w*\s+(?:u\s+)?(?:NOB|NOP|NOR|narodnooslobodil)\S*', re.I)
# out: a survivor who went over to the Chetniks in 1943 and left with them in 1945 (the user's rule of 10-14)
OUT_ENTRIES = {('survivors', 47)}
# a survivor who "went the same way as his father", a fighter of the III krajiška (no. 80)
FIGHTERS = {('survivors', 81)}


def role_of(info: str, key: str, no: int) -> str | None:
    """None for a fighter, 'activist' for the movement's other people, 'participant' for a survivor the bio names
    only a participant of the NOR; the fallen and the spomenica's holders the book counts as fighters"""
    if V.role(info) is None or FIGHTER_WORDS.search(info) or (key, no) in FIGHTERS:
        return None
    if V.role(PARTICIPANT.sub('', info)) == 'activist':
        return 'activist'
    return 'participant' if key == 'survivors' else None


def clean(t: str) -> str:
    t = re.sub(r'(?<![\w])["\'“”]+([БВЕ])(?=[а-яђјљњћџ])', 'Ђ', t)         # 'Бурић, “Вилас, "Еуро: Đ
    t = re.sub(r'(?<![\w])["\'“”]+', '', t)                                 # the other specks before a word
    t = re.sub(r'(?<![\w])Ј\s+(?=[а-яђјљњћџ]{2,})', 'Ј', t)                 # "Ј ове" = Јове
    t = re.sub(r'(?<![\w])\]\s*(?=[а-яђјљњћџ]{2,})', 'Ј', t)                   # "] ове" = Јове
    for old, new in SLIPS:
        t = t.replace(old, new)
    return t.replace('Еуро', 'Ђуро')


def lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = clean(l.text.strip())
            if l.x0 > 3000 or re.fullmatch(r'[\d\s.,]{1,6}', t):
                continue
            out.append((page, t))
    return out


def unit_text(info: str) -> str:
    """the brigades' Roman numerals as the OCR gave them, for the units' reader"""
    return re.sub(r'\b(111|Š|UN|UP|UŠ|U|I|H)\s+(?=(?:krajišk|vojvođansk|dalmatinsk|proletersk))',
                  lambda m: ROMAN_UNIT[m.group(1)] + ' ', info)


def head_names(head: str) -> tuple[str, str, str, str]:
    """"Кнежевић Душана Ђуро", "Керкез Раде Душан-Бикан", "Ступар Николе Лука – тобџија", "Драгић Јово"""
    head = re.sub(r'\s*[–—-]\s*', '-', head.strip(' ,.'))
    words = head.split()
    if len(words) >= 3:
        sur, fath, given = words[0], words[1], ' '.join(words[2:])
    elif len(words) == 2:
        sur, fath, given = words[0], '', words[1]
    else:
        sur, fath, given = words[0], '', ''
    if '-' in sur:                                          # "Ступар Шпире-Вујиновић": the given name not printed
        sur, nick0 = sur.split('-', 1)
    given, _, nick = given.partition('-')
    last, first = V.name_word(sur), V.name_word(given) if given else ''
    nick = latin(nick).strip()
    if nick and nick[:1].isupper():
        nick = V.name_word(nick) if len(nick.split()) == 1 else nick
    return last, V.father(fath) if fath else '', first, nick


def lists(book: dict) -> list[dict]:
    out = []
    for key, pages, title, base, start, stop in LISTS:
        raw, cur, started = [], None, False
        for page, t in lines(book, pages):
            if not started:
                started = start in t
                continue
            if t.startswith(stop):
                break
            m = re.match(r'^(\d{1,2})(?!\d)(?:\s*\.\s*[-–—·•]*|\s*[-–—·•]+)\s*(.*)', t)       # "29.••Кецман"
            if m and int(m.group(1)) == (cur['no'] if cur else 0) + 1:
                cur = {'no': int(m.group(1)), 'page': page, 'parts': [m.group(2)]}
                raw.append(cur)
            elif cur:
                cur['parts'].append(t)
        for r in (r for r in raw if (key, r['no']) not in OUT_ENTRIES):
            text = TYPED.get((key, r['no'])) or V.unhyphen(' '.join(r['parts']))
            if key == 'survivors':
                m = re.match(r'^(.*?)\s*\((\d{4})\s*(?:[-–]\s*(\d{4}))?\s*-?\s*\)\s*,?\s*(.*)$', text)
                head, born, died, rest = (m.groups() if m else (text.split(',')[0], '', '', text))
            else:
                m = re.search(r'\s*,?\s+(?=ро[дђ]ј?ен)', text)
                head, rest = (text[:m.start()], text[m.end():]) if m else (text.split(',')[0], text)
                born = (re.search(r'ро[дђ]ј?ен[а]?\s+(1[89]\d\d)', rest) or [None, ''])[1]
                died = ''
            last, fath, first, nick = head_names(head)
            info = V.read_cyr(rest)
            name = ' '.join(x for x in (last, fath, first) if x)
            printed = f'{last} {fath + " " if fath else ""}{first}{"-" + nick if nick else ""}'.strip()
            years = f' ({born}{"-" + died if died else ""})' if key == 'survivors' and born else ''
            e = {'soldier_id': f'{PREFIX}{base + r["no"]:06d}', 'name': name, 'last_name': last, 'also': [],
                 'first_name': first, 'nick': nick, 'fathers_name': fath, 'birth_year': born, 'born_in': VILLAGE,
                 'death_year': '', 'survived': key != 'fallen', 'units': V.units_of(unit_text(info)),
                 'additional_info': f'{title}: {r["no"]}. {printed}{years}, {info}', 'list': title,
                 'book_title': TITLE, 'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
            role = role_of(info, key, r['no'])
            if key == 'fallen':
                d = V.death(info)
                e.update({'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
                          **({'death_place': d['place']} if d.get('place') else {})})
            if role:
                e['role'] = role
            out.append(e)
    return out


def youth(book: dict) -> list[tuple[str, str, str, int]]:
    """The youth organization's members, two groups in two columns, "16. - Керкез Ј. Бранко": (surname, father's
    initial, given name, scan page)"""
    out = []
    pat = re.compile(rf'(\d{{1,2}})\s*\.\s*[-–—·]?\s*([{UC}][{LC}]+)\s+([{UC}])\.\s*([{UC}][{LC}]+)')
    started = False
    for page, t in lines(book, range(190, 192)):
        if 'сматра прва група омладине' in t:
            started = True
            continue
        if t.startswith('Огромна је заслуга'):
            break
        if started:
            for m in pat.finditer(t):
                out.append((V.name_word(m.group(2)), latin(m.group(3)), V.name_word(m.group(4)), page))
    return out


def fold(s: str) -> str:
    return T.latin(s).lower().translate(str.maketrans('čćžšđ', 'cczsd')) if s else ''


def main():
    V.corpus()
    book = load(BOOK)
    entries = lists(book)
    by_name = defaultdict(list)
    for e in entries:
        by_name[(fold(e['last_name']), fold(e['first_name']))].append(e)
    # the movement's people: each mention, then one person per name
    mentions = []
    for body, village, page, names in COMMITTEES:
        for n in names:
            m = re.match(r'^(\S+)(?:\s+\((\S+)\))?\s+(\S+?)(?:-(\S+))?$', n)
            given, fath, sur, nick = m.groups()
            mentions.append({'body': body, 'village': village, 'given': given, 'father': fath or '',
                             'sur': sur, 'nick': nick or '', 'page': page})
    for sur, initial, given, page in youth(book):
        mentions.append({'body': YOUTH, 'village': '', 'given': given, 'father': initial, 'sur': sur, 'nick': '',
                         'page': page})
    people, counts = {}, Counter()
    for m in mentions:
        cands = by_name[(fold(m['sur']), fold(m['given']))]
        if m['father']:
            cands = [c for c in cands if fold(c['fathers_name'])[:len(m['father'])] == fold(m['father'])[:len(m['father'])]
                     or fold(c['fathers_name']).startswith(fold(m['father'])[:3])]
        # "title, village: body – name", as a list's heading gives the village (the field extractor reads only the
        # village as the birthplace, never the body: "Odbor AFŽ-a sela Vođenice" would pass for a place)
        village = (m['village'] or VILLAGE).split(',')[0]
        text = f"{MENTIONS}, {village}: {m['body']} – {m['given']}" \
               f"{' (' + m['father'] + ('.' if len(m['father']) == 1 else '') + ')' if m['father'] else ''} {m['sur']}" \
               f"{' - ' + m['nick'] if m['nick'] else ''}"
        if len(cands) == 1:
            c = cands[0]
            if text not in c['additional_info']:
                c['additional_info'] = c['additional_info'].rstrip('. ') + f'. {text}'
            counts['mentions joined to a list entry'] += 1
            continue
        if len(cands) > 1:
            counts['mentions that fit two entries: left out'] += 1
            continue
        key = (fold(m['sur']), fold(m['given']), fold(m['nick']))
        p = people.setdefault(key, {**m, 'texts': []})
        if text not in p['texts']:
            p['texts'].append(text)
        if m['father'] and not p['father']:
            p['father'] = m['father']
    for i, p in enumerate(people.values(), 1):
        fath = p['father'] if len(p['father']) > 1 else ''
        entries.append({'soldier_id': f'{PREFIX}{1000 + i:06d}',
                        'name': ' '.join(x for x in (p['sur'], fath, p['given']) if x), 'last_name': p['sur'], 'also': [],
                        'first_name': p['given'], 'nick': p['nick'], 'fathers_name': fath, 'birth_year': '',
                        'born_in': p['village'] or VILLAGE, 'death_year': '', 'survived': False, 'units': [],
                        'role': 'activist', 'additional_info': '. '.join(p['texts']),
                        'list': MENTIONS, 'book_title': TITLE,
                        'source_url': viewer_url(book, p['page']), 'source_page': p['page'] - OFFSET})
        counts['activists of their own'] += 1
    counts.update(e['list'] for e in entries)
    counts.update(f"role {e.get('role')}" for e in entries)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))


if __name__ == '__main__':
    main()
