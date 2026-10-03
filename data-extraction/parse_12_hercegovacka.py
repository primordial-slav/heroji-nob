"""
Parser: 12. hercegovačka NOU brigada (brigade code 101).

Source: Osman Đikić, "Dvanaesta hercegovačka NOU brigada" (znaci.org 00001/243_10.pdf, its pages 13-26, book pp.
        207-220)  →  website/public/pdfs/12-hercegovacka.pdf. Cyrillic, one column, every line flush left, by the
        municipality the fallen came from:
    Prilog 3, "Spisak poginulih boraca i starješina 12. hercegovačke NOU brigade (16. novembar 1943 - 23. maj 1945.)"
        Opština Bileća
        BRATIĆ R. Đorđo, rođen 1905. god. u Bresticama. Borac. Poginuo 13. februara 1944. godine.
An entry starts with a surname in capitals; a second name after the given one is a nickname ("VUČINIĆ L. Mihajlo
Milan"). The birthplace is the village (in the nominative the other units know) and the municipality of the heading.
The heroes' biographies and the officers' list before it (Prilog 1 and 2) are not read.
"""
import re
from itertools import product

import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_muni = {'name': ''}
MONTHS = {'januaru': 'januar', 'februaru': 'februar', 'martu': 'mart', 'aprilu': 'april', 'maju': 'maj', 'junu': 'jun',
          'julu': 'jul', 'avgustu': 'avgust', 'septembru': 'septembar', 'oktobru': 'oktobar', 'novembru': 'novembar',
          'decembru': 'decembar'}


def keep(ln: dict) -> bool:
    t = ln['text'].strip().replace('J1', 'L').replace('j1', 'l')             # Л read as Ј1
    m = re.match(rf'^Opština\s+([{U}][{L}]+(?:\s+[{U}][{L}]+)?)', t)
    if m:
        _muni['name'] = m.group(1)
        return False
    if re.fullmatch(r'[\d\W]{1,6}', t) or t.startswith('*') or re.match(r'^(?:Prilog|Spisak|12\. hercegova|\(16\. novembar)', t):
        return False                                                         # headings, the footnotes on sources
    if re.match(rf'^[{U}]{{2,}}(?:-[{U}]{{2,}})?\s+(?:[{U}][{L}]?\.\s*)?[{U}][{L}]', t) and not re.match(r'^(?:NOU|SKOJ|KPJ|NOB|NOR)\b', t):
        t = f'§p§{_muni["name"]}§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    muni = text[3:text.index('§', 3)]
    text = text[text.index('§', 3) + 1:].strip()
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "Pogi- nuo"
    head, info = (re.split(r',|\.\s+(?=ro[đd]en)', text, 1) + [''])[:2]          # "MILJANOVIĆ R. Slavko. rođen"
    info = info.strip()
    words = head.split()
    last = words.pop(0) if words else ''
    father = words.pop(0) if words and re.fullmatch(rf'[{U}][{L}]?\.', words[0]) else ''
    notes = ['zvani ' + ' '.join(words[1:])] if len(words) > 1 else []
    rec = _record(last, words[0] if words else '', father, '; '.join(notes + [info]))
    y = re.search(r'\bro[đd]en[a]?\s+(1[89]\d\d)', info)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.search(rf'\bro[đd]en[a]?\s+(?:1[89]\d\d\.?\s*(?:god\.|godine)?\s*)?u\s+(?:selu\s+|zaseoku\s+)?'
                  rf'([{U}][{L}]+(?:\s+[{U}][{L}]+)?)', info)
    if b:
        rec['_birth'] = (b.group(1), muni)
    rec['death_type'] = death_type_from_text(info) or 'poginuo'
    sentences = [x.strip() for x in re.split(r'(?<=[a-zčćžšđ)])\.\s+(?=[A-ZČĆŽŠĐ])', info)]
    duty = sentences[1] if len(sentences) > 1 and not re.match(r'(?:Poginu|Umr|Ubijen|Strijelj|Streljan|Zarob|Nesta|Četnici|Ranjen)', sentences[1]) else ''
    if duty and len(duty) < 60 and not re.search(r'\s(?:u|na|i|je|se)\s', duty):
        rec['rank'] = (duty[0].lower() + duty[1:]).rstrip('.')                             # "Komandir voda." = komandir voda
    d = re.search(r'\b(?:[Pp]oginu\w+|[Uu]mr\w+|[Ss]trijeljan\w*|[Uu]bijen\w*)\s+((?:\d{1,2}\.\s*)?(?:[a-zčćžšđ]+\s+){0,2}1[89]\d\d)\.?'
                  r'(?:\s*(?:god\.|godine))?\s*(?:(?:u|kod|na)\s+(?:selu\s+)?([A-ZČĆŽŠĐ][\w\s-]*?))?(?:[.,(]|$)', info)
    if d:
        date = re.sub(r'^(?:u|početkom|krajem)\s+', '', d.group(1))
        rec['death_date'] = re.sub(r'\b[a-z]+u\b', lambda m: MONTHS.get(m.group(0), m.group(0)), date)   # "u junu 1944" = jun 1944
        if d.group(2):
            rec['death_place'] = d.group(2).strip()
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    soldiers = repair_cyrillic_ocr(soldiers, ik_is_ic=True)
    known = top._corpus()[0]

    def nominative(place: str) -> str:
        forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in place.split()))]
        forms = [f for f in forms if f != place and known[f] > known[place]]
        return max(forms, key=lambda f: known[f]) if forms else place

    for s in soldiers:
        if s.get('death_place'):                                             # "Mosku-Trebinje" = Mosko, Trebinje, where known
            parts = [p.strip() for p in s['death_place'].split('-')]
            s['death_place'] = ', '.join(nominative(p) for p in parts if p)
        birth = s.pop('_birth', None)
        if birth:
            place, muni = birth
            nom = nominative(place)
            if nom == place and re.search(r'(?:[^ć]i|u|ju|oj \S+|om \S+)$', place) and not muni:
                continue                                                     # a locative no other unit knows; the text keeps it
            if nom == place and re.search(r'(?:[^ć]i|u|ju)$', place):
                s['birth_place'] = muni                                      # "u Bresticama": the municipality at least
            else:
                s['birth_place'] = nom + (', ' + muni if muni and muni != nom else '')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/12-hercegovacka.pdf',
        brigade_code=101,
        output_path='website/public/12-hercegovacka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
