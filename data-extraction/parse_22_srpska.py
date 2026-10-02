"""
Parser: 22. srpska kosmajska NOU brigada (brigade code 74).

Source: Milorad Gončin, "22. srpska kosmajska brigada" (Smederevo; znaci.org 00003/445.pdf, PDF pages 317-399)
        →  website/public/pdfs/22-srpska.pdf:
    pp. 1-23    "Poginuli borci i starešine 22. srpske kosmajske brigade"
    pp. 24-83   "Preživeli borci i starešine 22. srpske kosmajske brigade"
Cyrillic, one column, a hanging indent; the surname and the given name in capitals, the father's name (genitive) or
initial between them, a nickname in capitals after the given name:
    АНТИЋ Владимира БОЖИДАР, рођен јуна 1919. године у Друговцу, срез Смедерево. Погинуо јануара 1945. ...
    АЛЕКСИЋ ДРАГОЉУБ ДРАГА, рођен у Великом Селу, Палилула, Београд. ...
The text layer reads Л as Ј1 or ЈТ ("АЈ1ЕКСИЋ", "МИЈТОВАН"). Parts of some pages are shifted right (the scan was
pasted up), so an entry is told by the margin measured near the line. Page 44 (book p. 360) is a scan with no text
layer: its 16 entries are typed here from the page image (PAGE_44), with each entry's top read from the image.
"""
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, cyrillic_to_latin, extract_lines_single_column, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_TO = 23
OWN = '22-srpska-soldiers.json'
NOT_NAMES = {'NOB', 'NOVJ', 'SKOJ', 'SSSR', 'JNA', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'KPJ', 'NOO'}

PAGE_44 = [  # book p. 360, typed from the image (no text layer); (top y, text)
    (202.1, 'ЉУБИСАВЉЕВИЋ Милорада БОГДАН, рођен 07. 11. 1928. године, Биновац, Смедерево. Од 09. 09. 1942. године у '
            'Космајском партизанском одреду. Санитетски референт батаљона. У Бригади од 12. 09. 1944. године.'),
    (245.8, 'ЉУБИЧИЋ Алексија ВОЈИН, рођен 7. 10. 1921. године, Мрчајевци, Чачак. Професор. У НОБ-у од 1941. године, био у '
            'конц. логору Бањица и Смедеревска Паланка. 10. 10. 1942. године ступио у партизански одред "Др Драгиша '
            'Мишовић". У Бригади од 12. 09. 1944.'),
    (289.0, 'ЉУБОЈЕВИЋ СТОЈАДИН, рођен 07. 08. 1918. године у Чајетини. Од маја 1944. године у Космајском одреду. Водник '
            'вода и заменик командира чете у одреду. У Бригади од 12. 09. 1944. године.'),
    (322.6, 'ЉУШТИНА Николе ЂУРО, рођен 1923. године, Медак, Госпић. Учесник у НОБ од 15. 08. 1941. године. У јединицама '
            'VI пролетерске дивизије комесар батаљона, у Космајској бригади од њеног преформирања у Љигу. Пуковник у пензији.'),
    (365.8, 'МАЦИЋ-КЛЕПАЦ Милосава БРАНИСЛАВКА, рођена 15. 08. 1926. године у Селевцу, Смедеревска Паланка. Учесник НОБ од '
            '15. 07. 1943. године. У Бригади од 12. 09. 1944. године.'),
    (399.4, 'МАЈИЋ Фрање ЈОВАН, рођен 1920, Београд, у Бригаду ступио 10. 11. 1944. године, борац.'),
    (422.9, 'МАЈСТОРОВИЋ Милоша ДУШАН, у Бригади од 12. 09. 1944. године.'),
    (436.3, 'МАЈСТОРОВИЋ Живка МИЛЕТА, рођен у Раљи, командир вода у III батаљону. У Бригади од 12. 09. 1944. године.'),
    (459.8, 'МАКСИМОВИЋ Милорада СЕЛИМИР, рођен 15. 02. 1920. године. У Бригаду ступио 12. 09. 1944. године.'),
    (483.4, 'МАКСИМОВИЋ МИЛОСАВ МИЋА, рођен 1923. године, Парцане, Сопот. Учесник НОБ од 01. 06. 1942. године. Био '
            'теренски радник и борац Космајског одреда. У Бригади од 12. 09. 1944. године, инвалид 100%.'),
    (526.1, 'МАКСИЋ Милоша СТАНИСЛАВ, рођен 15. 01. 1926. године, Лозовик, Велика Плана. У Бригаду ступио 12. 09. 1944. године.'),
    (549.6, 'МАЛИНИЋ Милана МИРКО, рођен 15. 07. 1924. године, Бајина Башта. У Бригаду ступио 12. 09. 1944. године.'),
    (573.1, 'МАНДИЋ Радоја АЛЕКСАНДАР, рођен 01. 01. 1921. године у Београду. Илегалац. У Бригади од 12. 09. 1944. године.'),
    (597.1, 'МАНЕСТЕР ЉУБО, III батаљон, III чета, политички делегат вода. У Бригади од 12. 09. 1944. године.'),
    (620.2, 'МАНИТАШЕВИЋ ЖИВОРАД, у Бригади од 12. 09. 1944. године.'),
    (633.6, 'МАРАВИЋ Николе СИМО, рођен 09. 11. 1924. године, Дрежница. У Бригаду ступио 12. 09. 1944. године, арт. '
            'потпуковник у пензији.'),
]


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    lines = [ln for ln in extract_lines_single_column(pdf_path, start_page, end_page) if ln['page'] != 44]
    if start_page <= 44 <= (end_page or 10 ** 6):
        lines += [{'page': 44, 'x': 125.8, 'y': y, 'text': t, 'typed': True} for y, t in PAGE_44]
    return sorted(lines, key=lambda ln: (ln['page'], ln['y']))


_by_page: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _by_page.setdefault(ln['page'], []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    """The leftmost x that three lines within 60 pt share: a block pasted further right has its own margin."""
    near = sorted(x for y, x in _by_page.get(ln['page'], []) if abs(y - ln['y']) <= 60)
    for x in near:
        if sum(1 for o in near if abs(o - x) <= 3) >= 3:
            return x
    return near[0] if near else ln['x']


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    t = re.sub(r'\s*[~_—-]{3,}.*$', '', t)                                    # "1944. godine. g ~~------"
    if re.fullmatch(r'[\d\W]{1,5}', t) or re.match(r'^(?:POGINULI BORCI|PREŽIVELI BORCI|22\. SRPSKE)', t):
        return False
    t = re.sub(rf'^[\'\\|.\s]+|^\d(?=[{U}]{{3}})', '', t)                          # "..NIKOLIĆ", "7GJEPOVIĆ"
    first = re.match(rf'^([{U}][{U}J1-]+)', t)
    # "JANJIĆ MILAN.", "JANKOVIĆ Blagoja ŽIVADIN,": a name, wherever on the line the page was pasted in
    named = re.match(rf'^[{U}]{{3,}}(?:-[{U}]{{3,}})?[’\'*\\>]?,?\s+(?:[{U}][{L}]+\s+|[{U}]\.\s+)?[{U}J1]{{3,}}[,.\s]', t)
    if ln.get('typed') or (first and first.group(1) not in NOT_NAMES and len(first.group(1)) >= 2
                           and (ln['x'] <= margin(ln) + 6 or (named and ln['x'] <= margin(ln) + 40))):
        t = ('§p§ ' if ln['page'] <= FALLEN_TO else '§s§ ') + t
    ln['text'] = t
    return True


def caps(w: str) -> str:
    """'AJ1EKSIĆ' = Aleksić, 'MIJTOVAN' = Milovan: Л read as Ј1 or ЈТ."""
    return re.sub(r'J1|JT|Ј1', 'L', w)


NAME = re.compile(rf'^([{U}]{{2,}}(?:-[{U}]{{2,}})?)\s+(?:([{U}][{L}]+(?:-[{U}][{L}]+)?|[{U}]\.)\s+)?([{U}]{{2,}})((?:\s+[{U}]{{2,}})*)\s*[,.]?')


def parse(text: str) -> dict:
    text = re.sub(r'^§[ps]§\s*', '', text)
    text = re.sub(rf'(?<=[{U}])J1|J1(?=[{U}])', 'L', text).replace('j1', 'l').replace('JT', 'L')
    text = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', text)               # a word broken at the line's end
    text = re.sub(r'^(\S*?)T\\(?=\s)', r'\1Ć', text)                            # "MANDIT\" = MANDIĆ
    text = re.sub(rf'^([{U}]{{3,}})[’\'*>^]+', r'\1', text)                     # "MIŠKOVIĆ’", "ORLIĆ*"
    text = re.sub(rf'^([{U}]{{3,}})([{U}][{L}])', r'\1 \2', text)              # "KATIĆIvana"
    text = re.sub(rf'^([{U}]{{3,}}),\s+(?=[{U}][{L}]+\s+[{U}]{{2}})', r'\1 ', text)   # "PAVLOVIĆ, Vladimira"
    text = re.sub(rf'(?<=[{U}])0(?=[{U}]|\b)', 'O', text)                       # "ČUBRIL0"
    text = re.sub(r'^(\S+\s+)J1\.', r'\1L.', text)                              # "PERIŠIĆ J1."
    pre = []
    m = re.match(rf'^(\S+)\s+\((?:[Ii]li\s+|[Ii]\s+)?([{U}][^)]*)\)\s*', text)         # "PAIĆ (ili PEJOVIĆ) Alije", "(Nikolić)"
    if m:
        pre.append('ili ' + caps(m.group(2)).title())
        text = m.group(1) + ' ' + text[m.end():]
    m = re.search(rf'\s((?:[Ii]nž|[Dd]r)\.?)\s+(?=[{U}]{{2}})', text[:60])     # "Milana inž. PETAR", "Petra Dr DRAGUTIN"
    if m:
        pre.append(m.group(1).lower().rstrip('.') + '.')
        text = text[:m.start()] + ' ' + text[m.end():]
    m = NAME.match(text)
    if not m:
        head, _, rest = text.partition(',')
        toks = head.split()
        return _record(caps(toks[0]).title() if toks else '', ' '.join(t.title() for t in toks[1:]), '',
                       '; '.join(pre + ([rest.strip()] if rest.strip() else [])))
    last, father, given, nick = m.groups()
    rest = text[m.end():].strip()
    notes = pre + (['zvani ' + nick.strip().title()] if nick.strip() else [])
    return _record(caps(last).title(), caps(given).title(), father or '', '; '.join(notes + ([rest] if rest else [])))


def repair(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_cyrillic_ocr(soldiers)
    first = Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != OWN:
            for s in json.loads(f.read_text(encoding='utf-8')):
                first[s.get('first_name') or ''] += 1
    for s in soldiers:                                                       # "Vesejšn" = Veselin
        g = s['first_name']
        if g and not first[g]:
            for a, b in (('jš', 'li'), ('jt', 'l'), ('j1', 'l'), ('ji', 'l')):
                c = g.replace(a, b)
                if c != g and first[c] >= 10:
                    s['first_name'] = c
                    break
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/22-srpska.pdf',
        brigade_code=74,
        output_path=f'website/public/{OWN}',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=re.compile(r'^§[ps]§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=repair,
    )
