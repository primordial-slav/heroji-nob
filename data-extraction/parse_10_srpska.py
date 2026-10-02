"""
Parser: 10. srpska NOU brigada (brigade code 88).

Source: Radovan Timotijević, "Deseta srpska NOU brigada" (znaci.org 00003/381.pdf, its pages 486-539, book
        pp. 488-541)  →  website/public/pdfs/10-srpska.pdf. Cyrillic, one column, a hanging indent:
    "Spisak poginulih boraca i rukovodilaca u toku Narodnooslobodilačkog rata" (pp. 1-2 are the author's note on
    his sources), the fallen, died, missing and captured:
        ALEKSIĆ Vojina JULIJANA, rođena 25. 5. 1925. u selu Brlog, Pirot, Srpkinja, krojačka radnica, u NOB od
            polovine avgusta 1944, u Brigadi od 9. 9. 1944, bolničarka 1. čete 2. bataljona, zarobljena i ubijena
            20. 9. 1944. prilikom napada na selo Ramni Del, Vlasotince. Mesto sahrane nepoznato.
The parser sets the birthplace: the village after "u selu" and its municipality, a town after "u" in the nominative
the other units know ("u Pirotu" = Pirot).
The list of the brigade's officers before it (book pp. 459-487), by duty, is not read.
"""
import re
from collections import Counter
from itertools import product

from _parser_scaffold import _record, death_type_from_text, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FIRST_PAGE = 3
_starts: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    """The entry starts' x near this line: the leftmost x two lines share (long bios put only one or two entry
    starts within reach)."""
    xs = sorted(x for y, x in _starts.get(ln['page'], []) if abs(y - ln['y']) <= 150)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 2:
            return x
    return xs[0] if xs else ln['x']


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    t = re.sub(rf'(?<=[{U}])J1|J1(?=[{U}])', 'L', t).replace('J1', 'L').replace('j1', 'l')   # Л read as J1
    if ln['page'] < FIRST_PAGE or re.fullmatch(r'[\d\W]{1,5}|\W*\w{0,2}\W*', t):
        return False                                                         # the author's note, page numbers
    if ln['x'] <= margin(ln) + 5 and re.match(rf'^[{U}]{{2,}}', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "Vra- nje"
    text = re.sub(r'^[A-Z]\d\.', '', text)                                    # "L1.LAPKNOVIĆ"
    text = re.sub(rf'(?<=[{U}])\.(?=[{U}])', '', text)                        # "BL.AGOJE"
    text = re.sub(rf'^([{U}]{{2,}})\.(?=\s)', r'\1', text)                    # "STOŠIĆ. S. BORIS"
    text = re.sub(rf'^([^,]*?[{U}]{{2,}})\.\s+(?=rođen)', r'\1, ', text)      # "BUDIMIR. rođen"
    head, _, rest = text.partition(',')
    rest = rest.strip()
    notes = []
    toks = head.split()
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*', toks[0]):
        caps.append(toks.pop(0))
    father = ''
    if toks and re.fullmatch(rf'(?:[{U}][{L}]*\.?|Lj\.|Nj\.)', toks[0]):
        father = toks.pop(0)                                                 # "Vojina", "M."
    toks = [t.strip('„“"') for t in toks]                                    # "MANČIĆ „BLAGOJE"
    caps += [t for t in toks if re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*', t)]
    extra = [t for t in toks if not re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*', t)]
    if len(caps) == 1 and father.endswith('.') and len(extra) == 1:
        caps.append(extra.pop())                                             # "BOCIĆ Đ. Živojin"
    if extra:
        notes.append('zvani ' + ' '.join(extra).strip('()"„“'))
    last = caps[0] if caps else ''
    given = ' '.join(caps[1:])
    if not given and father and not father.endswith('.'):
        given, father = father, ''                                           # "ANĐELKOVIĆ Dušan"
    if len(caps) == 1 and not given and not father:
        last, given = '§', caps[0]                                           # "PANE, rođen u selu Gornji Stajevac": one name
    rec = _record(last, given.title() if given.isupper() else given, father, '; '.join(notes + ([rest] if rest else [])))
    y = re.search(r'rođen[a]?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.search(rf'rođen[a]?\s+(?:[\d.\s]*?(?:1[89]\d\d)\.?(?:\s*godine)?\s*)?(?:(u\s+selu|u)\s+)([{U}][^,]*?),\s*([{U}][^,]*?),', rest)
    if b:
        rec['_birth'] = (b.group(1), b.group(2).strip(), b.group(3).strip())
    else:
        b = re.search(rf'rođen[a]?\s+(?:[\d.\s]*?(?:1[89]\d\d)\.?\s*)?u\s+([{U}][^,]*?),', rest)
        if b:
            rec['_birth'] = ('u', b.group(1).strip(), '')
    d = re.search(rf'(?:poginu\w+|umr\w+|ubijen\w*|nesta\w+)\s+[\d.\s]*19\d\d\.?\s*(?:godine\s+)?'
                  rf'(?:prilikom\s+[{L}]+\s+(?:na|u|kod|za|preko)\s+|u\s+borbi\s+(?:na|u|kod|za|sa\s+\S+\s+(?:na|u|kod))\s+|kod\s+|na\s+|u\s+)'
                  rf'(?:(?:selo|sela|selu|vis|visu|uzvišenje|uzvišenju|planini|planinu|grad|reci|reku|šumi|kotu|koti)\s+)?'
                  rf'([{U}][{L}]+(?:\s+[{U}]?[{L}]+)?)(?:,\s*([{U}][{L}]+(?:\s+[{U}][{L}]+)?))?\s*[,.(]', rest)
    if d:
        rec['_death'] = (d.group(1), d.group(2) or '')
    rec['death_type'] = death_type_from_text(rest) or 'poginuo'
    if re.search(r'\bzarobljen[a]?\s+i\s+(?:ubijen|streljan)', rest):
        rec['death_type'] = 'streljan' if 'streljan' in rest else 'poginuo'
    return rec


def _known_places() -> Counter:
    import json
    from pathlib import Path
    from scripts.name_utils import BRIGADE_CONFIGS
    known = Counter()                                                        # the places the other units print, a file at a time
    for code, cfg in BRIGADE_CONFIGS.items():
        f = Path('website/public') / cfg['json_file']
        if code != 88 and f.exists():
            for s in json.loads(f.read_text(encoding='utf-8')):
                for k in ('birth_place', 'death_place'):
                    for part in filter(None, (s.get(k) or '').split(', ')):
                        known[part] += 1
    return known


def post(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    known = _known_places()

    def nominative(word: str) -> str:
        forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in word.split()))]
        forms = [f for f in forms if f != word and known[f] > known[word]]
        return max(forms, key=lambda f: known[f]) if forms else word

    for s in soldiers:
        if s['last_name'] == '§':                                            # a soldier known by one name
            s['last_name'] = ''
            s['full_name'] = s['first_name']
        death = s.pop('_death', None)
        if death:
            place, muni = death                                              # "na selo Beljanicu, Leskovac" = Beljanica
            place = nominative(place)
            if known[place] or muni:
                s['death_place'] = place + (', ' + muni if muni and muni != place else '')
        birth = s.pop('_birth', None)
        if birth:
            prep, place, muni = birth
            if prep == 'u':
                place = nominative(place)                                    # "u Pirotu" = Pirot
                if muni and not known[muni]:
                    muni = ''                                                # "u Vranju, Srbin": no municipality
            if re.fullmatch(r'Srbin|Srpkinja|Hrvat|Makedonac|Bugarin|Albanac', muni):
                muni = ''
            s['birth_place'] = place + (', ' + muni if muni and muni != place else '')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/10-srpska.pdf',
        brigade_code=88,
        output_path='website/public/10-srpska-soldiers.json',
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
