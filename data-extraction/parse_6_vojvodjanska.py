"""
Parser: 6. vojvođanska udarna brigada (brigade code 83).

Source: Živan M. Ninković, "Šesta vojvođanska udarna brigada" (znaci.org 00001/252_8.pdf, its pages 5-29, book
        pp. 175-199)  →  website/public/pdfs/6-vojvodjanska.pdf:
    "Spisak poginulih boraca i rukovodilaca" (349 names; the brigade's reports count 81 more fallen without names),
    one column, entries flush with a gap between them:
        ADŽIJA živan, rođen 1925. godine, s. Idvor, opština Kovačica,
        poginuo 8. februara 1945. godine kod s. V. Črešnjevica.
The surname in capitals, then the given name; the birthplace and its municipality, the date and place of death,
where they were buried. The list of those thanked for the liberation of Belgrade (book pp. 200-206) is printed as a
facsimile with no text layer and is not read.
"""
import re
import sys

from _parser_scaffold import _record, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_prev = {'page': 0, 'y': 0.0}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    page, y = ln['page'], ln['y']
    if re.fullmatch(r'\d{3}|\W*\w{0,2}\W*', t) or (page == 1 and (y < 230 or y > 490)):
        return False                                                         # page numbers; the heading and the footnote
    t = re.sub(r'^\S+', lambda m: re.sub(rf'(?<=[{U}])[l1](?=[{U}])', 'I', m.group(0)), t)   # "AUGUSTINClC", "BABlC"
    gap = page != _prev['page'] or y - _prev['y'] > 12
    _prev.update(page=page, y=y)
    if gap and re.match(rf'^[{U}]{{2,}}', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


GENITIVE = {'Aleksincu': 'Aleksinac'}
DEATH_PLACES = {'Avali': 'Avala', 'Avale': 'Avala', 'Dravi': 'Drava', 'Radetića brdu': 'Radetića brdo',
                'Spišić-Bukovice': 'Spišić-Bukovica', 'Spišić-Bukovica': 'Spišić-Bukovica', 'Velike Črešnjevice': 'Velika Črešnjevica',
                'Velike Ćrešnjevice': 'Velika Črešnjevica', 'Velike Crešnjevice': 'Velika Črešnjevica', 'Turnašice': 'Turnašica',
                'Razbojišta': 'Razbojište', 'Podgorača': 'Podgorač', 'Slatinice': 'Slatinica', 'Budrovca': 'Budrovac',
                'Virovitice': 'Virovitica', 'Pitomače': 'Pitomača', 'Feričanaca': 'Feričanci'}     # this book's battlefields


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "po- ginuo"
    text = text.replace('Ì', '1')
    text = re.sub(rf'^([{U}]{{2,}}),\s+(?=[{U}][{L}]+,)', r'\1 ', text)      # "ILIČ, Marko,"
    head, _, rest = text.partition(',')
    head = re.sub(rf'\b([{U}][{L}]+) ([{L}]{{1,3}})\b', r'\1\2', head)       # "Va sa"
    toks = head.split()
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})?', toks[0]):
        caps.append(toks.pop(0))
    if not toks and len(caps) >= 2:
        toks = [caps.pop()]                                                  # "BANKOTI EMIL"
    if len(caps) > 1 and any(len(c) <= 3 for c in caps):
        caps = [''.join(caps)]                                               # "PET ROV IČ"
    given = ' '.join(toks)
    given = re.sub(r'^([šžčćđ])', lambda m: m.group(1).upper(), given)       # "živan" = Živan
    rec = _record(' '.join(caps), given.title() if given.isupper() else given, '', rest.strip())
    y = re.search(r'rođen[a]?\s+(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.search(rf'ro[đd]e[nd][a]?\s+(?:1[89]\d\d\.?\s*(?:godine)?)?[.,]?\s*(?:(u\s+s\.|u|s\.|selo)\s+)?([{U}][^,]*?)(?:,\s*(?:opština\s+)?([{U}][^,]*?))?,\s*(?=pogin|umr|ubijen|streljan|udavi|nesta|[a-zčćžšđ])', rest)
    if b:
        prep, village, muni = b.group(1), b.group(2).strip(), (b.group(3) or '').strip()
        village = GENITIVE.get(village, village) if prep == 'u' else village
        muni = re.sub(r'\s+', ' ', muni.replace('St. Pa- zova', 'Stara Pazova').replace('St. Pazova', 'Stara Pazova'))
        rec['_places'] = [village] + ([muni] if muni and muni != village else [])
    rec['death_type'] = 'umro' if re.search(r'\bumr(?:o|la)\b', rest) and not re.search(r'\bpogin', rest) else 'poginuo'
    d = re.search(rf'(?:pogin|umr|ubijen|nesta)\w*\s+(?:[^,]*?\b1?9?4\d\.?\s*(?:godine)?)[,.]?\s*((?:kod|u|na)\s+)?(s\.\s*|sela\s+|ž\.\s*st\.\s*)?'
                  rf'([{U}](?:[^,(.]|\.(?=\s*[{U}]))*?)(?=\s*[,(]|\.\s*$|\.\s+[a-zčćžšđ]|\s+sahranj|$)', rest)   # "kod s. V. Črešnjevica."
    if d:
        rec['_death'] = ((d.group(1) or '').strip(), bool(d.group(2)), re.sub(r'\s*—\s*', '-', d.group(3).strip()))
    return rec


def places(soldiers: list[dict]) -> list[dict]:
    """Each part in the form the other units know ("St. Pazova" -> Stara Pazova, "V. Moštanica" -> Velika Moštanica)."""
    import json
    from collections import Counter
    from pathlib import Path
    from parse_5_vojvodjanska import known_place
    from itertools import product
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    from scripts.name_utils import BRIGADE_CONFIGS
    known = Counter()                                                        # the places the other units print, a file at a time
    for code, cfg in BRIGADE_CONFIGS.items():
        f = Path('website/public') / cfg['json_file']
        if code != 83 and f.exists():
            for s in json.loads(f.read_text(encoding='utf-8')):
                for k in ('birth_place', 'death_place'):
                    for part in filter(None, (s.get(k) or '').split(', ')):
                        known[part] += 1
    for s in soldiers:
        parts = [re.split(r'\s+(?=pogin|umr|DOgin)', p)[0] for p in s.pop('_places', [])]   # "Nova Kanjiža poginuo ..."
        named = []
        for p in parts:
            p = re.sub(r'\bSl\.\s*Brod\b', 'Slavonski Brod', p)
            q = re.sub(r'^V\. ', 'Vel. ', re.sub(r'^B\. ', 'Ban. ', p))      # "V. Moštanica", "B. Aleksandrovo"
            k = known_place(q, known)
            named.append(k if k != q else p)                                 # unknown: as printed
        death = s.pop('_death', None)
        if death:
            prep, village, place = death                                     # "na Avali" = Avala, "kod Spišić-Bukovice"
            place = re.sub(r'^V(?:el)?\.\s*(?=[ČĆC]rešnjevic|Moštanic)', 'Velika ', place)   # "V. Črešnjevica", "Vel. Moštanica"
            place = DEATH_PLACES.get(place, place)
            village = village or place in DEATH_PLACES.values()
            if prep and not village:
                forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in place.split()))]
                forms = [f for f in forms if f != place and known[f] > known[place]]
                place = max(forms, key=lambda f: known[f]) if forms else (place if known[place] else '')
            if place:
                s['death_place'] = place
        if named:
            s['birth_place'] = ', '.join(dict.fromkeys(named))
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/6-vojvodjanska.pdf',
        brigade_code=83,
        output_path='website/public/6-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=places,
    )
