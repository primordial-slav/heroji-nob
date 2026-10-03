"""
Parser: Posavski NOP odred (brigade code 110), Serbia, 1941.

Source: Milosav Bojić, "Posavski partizanski odred" (znaci.org 00001/279_9.pdf, its pages 22-199, book pp. 565-742)
        →  website/public/pdfs/posavski-odred.pdf. Cyrillic, one column, a hanging indent: "Borci Posavskog partizanskog
        odreda", some 2,500 of the 2,985 who were in it in October 1941 (the editors' note), under the detachment's
        command, its hospital, and each battalion: "Prvi posavski bataljon", "Drugi posavski beogradski bataljon",
        "3. tamnavski i 4. posavotamnavski bataljon" (one list for the two):
            АКСЕНТИЈЕВИЋ БРАНИМИР БРАНА, рођен 1913, Грабовац, Обреновац, учитељ, ... Погинуо крајем новембра 1941.
The name in capitals: surname (a second one: "АЛАРГИЋ СТАМБОЛИЋ ЈУДИТА"), an initial, the given name, a nickname;
"... АДАМ": the surname unknown. The section gives `unit_detail`. The text layer reads ђ as ћ ("роћен") and -ВИЋ as
-ВИН, -ВИЕ or -ВИБ; repair_cyrillic_ocr puts the names right.
"""
import re
from collections import Counter

from _parser_scaffold import _record, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SECTIONS = [(r'^KOMANDA ODREDA', 'komanda odreda'), (r'^PRVI POSAVSKI BATALJON', '1. posavski bataljon'),
            (r'^DRUGI POSAVSKI BEOGRADSKI BATAL', '2. posavski (beogradski) bataljon'),
            (r'^3\. TAMNAVSKI I 4\. POSAVOTAMNAVSKI', '3. tamnavski i 4. posavotamnavski bataljon')]
# the name: words in capitals, an initial, "dr", " - " before an alias ("KON IMRE - KOSTIĆ MIRKO")
HEAD = re.compile(rf'^(?:(?:[{U}][{U}\-]+|[{U}]\.?|dr|Dr|DR|-|\([{U}][{L}]+\))(?:\s+|(?=[,.])|$))+')
ABBR = {'PK', 'KPJ', 'SKOJ', 'CK', 'NOV', 'NOVJ', 'NOB', 'NOR', 'NOP', 'JNA', 'BJV', 'AVNOJ', 'SUBNOR', 'ZAVNOS', 'VŠ', 'SR',
        'SFRJ', 'POJ', 'PO', 'NOO', 'OK', 'SK', 'II', 'III', 'IV'}
_section = {'name': ''}
_margin: dict = {}
_first: Counter = Counter()


def corpus() -> None:
    import glob
    import json
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('/posavski-odred-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                _first[s['first_name'].upper()] += 1


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _margin[ln['page']] = min(_margin.get(ln['page'], 999), ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}', t):
        return False                                                         # page numbers
    for rx, name in SECTIONS:
        if re.match(rx, t):
            _section['name'] = name
            return False
    if t.startswith('U bolnicu Posavskog NOP odreda'):
        _section['name'], _section['note'] = 'bolnica odreda', True          # the nurses not in the battalions' lists
    if _section.get('note'):
        _section['note'] = not t.endswith('i to:')                           # the note that leads the nurses' list
        return False
    if ln['page'] == 1 or (ln['page'] == 2 and not _section['name']):
        return False                                                         # the editors' foreword
    t = t.replace('roćen', 'rođen')                                          # ђ read as ћ
    t = re.sub(rf'(?<=[{U}])(?:Lz|L>)\s?(?=[{U}])', 'LJ', t)                 # Љ read as Лз, Л>: "VASILzEVIĆ"
    t = re.sub(r'^[•·*]+\s*', '', t)                                          # "• PETROVIĆ VELIMIR": a speck
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ]{3})[a-zčćžšđ](?=[\s,])', lambda c: c.group(0).upper(), t)   # "RATKOVIć"
    t = re.sub(r'\bG1(?=[A-ZČĆŽŠĐ])', 'P', t)                                # П read as Г1: "G1ANIĆ"
    run = HEAD.match(re.sub(r'(?<=[A-ZČĆŽŠĐ])[a-z](?=[A-ZČĆŽŠĐ])', 'X', re.sub(r'^[.\s]+', '', t)))   # "ARNAuTOVIĆ"
    names = re.findall(rf'[{U}X]{{2,}}', run.group(0)) if run else []
    names = [n for n in names if n not in ABBR]                               # "PK KPJ za Srbiju": no name
    if ln['x'] < _margin[ln['page']] + 10 and (len(names) >= 2 or (re.match(r'^[.\s]{2,}', t) and names)):
        t = f'§p§{_section["name"]}§ ' + t                                   # the name in capitals, a comma or not after it
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    section = text[3:text.index('§', 3)]
    text = text[text.index('§', 3) + 1:].strip()
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "zemljorad- nik"
    unknown = bool(re.match(r'^[.\s]{2,}', text))
    text = re.sub(r'^[.\s]+', '', text)                                       # "... ADAM", ". . ZLATOMIR": no surname
    text = re.sub(r'(?<=[A-ZČĆŽŠĐ])[a-z](?=[A-ZČĆŽŠĐ])', lambda c: c.group(0).upper(), text)   # "ARNAuTOVIĆ"
    m = HEAD.match(text)
    head, info = (m.group(0), text[m.end():]) if m else (text, '')
    info = re.sub(r'^[\s,.]+', '', info)
    alias = ''
    other = re.search(rf'\(([{U}][{L}]+)\)', head)
    if other:
        head = head.replace(other.group(0), ' ')                              # "ZASTRIJANOVIĆ (Industrijanović)"
    if ' - ' in head:
        head, alias = head.split(' - ', 1)                                   # "KON IMRE - KOSTIĆ MIRKO", "BOŽIDAR - BOŽA KREZA"
    tokens = head.split()
    dr = any(t.lower() == 'dr' for t in tokens)
    tokens = [t for t in tokens if t.lower() != 'dr']
    father = next((t for t in tokens if re.fullmatch(rf'[{U}]\.', t)), '')
    words = [t for t in tokens if t != father]
    nick: list[str] = []
    if not words:
        print('   no name:', text[:80])
        return _record('', '', '', info)
    if unknown or len(words) == 1:
        last, given, nick = '', words[0], words[1:]                          # "... ADAM", "... BRANA ŽUTI": no surname
    elif len(words) == 2:
        last, given = words
    elif _first[words[1]] >= 3 or _first[words[2]] < 3:
        last, given, nick = words[0], words[1], words[2:]                    # "AKSENTIJEVIĆ BRANIMIR BRANA"
    else:
        last, given, nick = words[0] + ' ' + words[1], words[2], words[3:]   # "ALARGIĆ STAMBOLIĆ JUDITA"
    nick = nick + ([alias] if alias else [])
    notes = (['ili ' + other.group(1)] if other else []) + (['dr.'] if dr else []) + (['zvani ' + ' '.join(w.title() for w in ' '.join(nick).split())] if nick else [])
    rec = _record(last or '?', given, father.rstrip('.'), '; '.join(notes + [info] * bool(info)))
    rec['_no_surname'] = not last
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    b = re.search(rf'\brođen[a]?\s+1[89]\d\d\s*,\s*([{U}][{L}]+(?:\s+[{U}][{L}]+)?)\s*,\s*([{U}][{L}]+(?:\s+[{U}][{L}]+)?)\s*[,.]', info)
    if b:
        rec['birth_place'] = f'{b.group(1)}, {b.group(2)}'                  # "rođen 1899, Stubline, Obrenovac"
    if section:
        rec['unit_detail'] = section
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_cyrillic_ocr(soldiers)
    known = {'last_name': Counter(), 'first_name': _first}
    import glob
    import json
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('/posavski-odred-soldiers.json'):
            known['last_name'].update(x['last_name'].upper() for x in json.load(open(f, encoding='utf-8')))
    for s in soldiers:
        for f in ('last_name', 'first_name'):                                 # Ђ read as Е, К or Б: "Eosić" = Đosić, "Kuro" = Đuro
            v = s[f]
            if v and v[0] in 'EKB' and not known[f][v.upper()] and known[f]['Đ' + v[1:].upper()] >= 3:
                s[f] = 'Đ' + v[1:]
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
        if s.pop('_no_surname', False):
            s['last_name'] = ''
            s['full_name'] = ' '.join(p for p in (s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/posavski-odred.pdf',
        brigade_code=110,
        output_path='website/public/posavski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
