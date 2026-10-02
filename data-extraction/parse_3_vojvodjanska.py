"""
Parser: 3. vojvođanska NOU brigada (brigade code 57).

Source: Radovan Panić, "Treća vojvođanska NOU brigada" (znaci.org 00001/70_7.pdf) → website/public/pdfs/3-vojvodjanska.pdf
        (its pages 11-181): "Spiskovi boraca i starešina brigade" (book p. 479 on):
    pp. 1-42    Poginuli borci i starešine brigade
    pp. 43-65   Borci i starešine brigade čije su sudbine ostale neutvrđene
    pp. 66-171  Preživeli borci i starešine brigade
Cyrillic, one column, a hanging indent; the name in capitals:
    ВУЧЕТИЋ ЛАЗА, рођен 1925. у Сремској Митровици, земљорадник, десетар, погинуо 29. 4. 1944. Ступари ...
The scan reads a final Ћ as Б, Е or И ("АНДРИЈИБ.", "ВУКАСОВИЕ", "ОМЕРОВИИ") and Ђ as "&" or Б: read back by
repair_cyrillic_ocr and here.
"""
import re

from _parser_scaffold import parse_standard_entry, repair_cyrillic_ocr, run_parser

U = 'A-ZČĆŽŠĐ'
_margin: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        if re.match(rf'^[{U}&]{{2}}', ln['text']):
            _margin[ln['page']] = min(_margin.get(ln['page'], 10 ** 6), ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}', t) or re.match(r'^(?:SPISKOVI BORACA|POGINULI BORCI I|BORCI I STAREŠINE BRIGADE ČIJE|'
                                                   r'OSTALE NEUTVR|PREŽIVELI BORCI I)', t):
        return False
    if ln['x'] <= _margin.get(ln['page'], ln['x']) + 4 and re.match(rf'^[{U}&]{{2}}', t):
        t = '§x§ ' + t                                                       # an entry starts at the margin
    ln['text'] = t
    return True


def fix_caps(word: str) -> str:
    """The scan's misreadings inside a capitalized word: Л as Ј1, П as 11, О as 0, Ч as 4, Љ as Л>."""
    w = word.replace('J1', 'L').replace('j1', 'l').replace('L>', 'LJ').replace('l>', 'lj')
    if sum(c.isupper() for c in w) >= 2:
        w = w.replace('11', 'P').replace('0', 'O').replace('4', 'Č')
        w = re.sub(rf'(?<=[{U}])1(?=[{U}])', 'I', w)
    return w


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).replace('&', 'Đ')
    head, comma, rest = text.partition(',')
    text = ' '.join(fix_caps(w) for w in head.split(' ')) + comma + rest
    text = re.sub(rf'^([{U}\-]+)\.\s+', r'\1 ', text)                       # "ANDRIJIB. FRANJA"
    text = re.sub(rf'^([{U}\-]+\s+[{U}])[-,]\s+', r'\1. ', text)             # "VULETIE I- LAZAR"
    text = re.sub(rf'^([{U}\-]+?)II\b', r'\1IĆ', text)                      # "OMEROVII": Ћ read as И
    prefix = ''
    br = re.match(rf'^([{U}\-]+)\s*\((rođena\s+)?([^)]+)\)\s+', text)
    if br:                                                                   # "KOVAČEVIĆ (Mate) ANTUN", "BOŽOVIĆ (Kavčić) RANKA"
        inner = br.group(3).strip()
        if not br.group(2) and re.fullmatch(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+[ae]', inner):
            text = f'{br.group(1)} {inner} ' + text[br.end():]
        else:
            prefix = ('rođ. ' if br.group(2) else 'ili ') + inner.title()
            text = br.group(1) + ' ' + text[br.end():]
    rec = parse_standard_entry(text)
    if prefix:
        rec['additional_info'] = prefix + '; ' + rec['additional_info']
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """repair_cyrillic_ocr, then a name whose Ђ was read as Б and that the corpus knows as such too ("Bura" = Đura):
    the Đ spelling when the corpus knows it five times as often."""
    import glob
    import json
    soldiers = repair_cyrillic_ocr(soldiers)
    known = {'last_name': {}, 'first_name': {}}
    for f in glob.glob('website/public/*soldiers.json'):
        if f.replace('\\', '/').endswith('3-vojvodjanska-soldiers.json'):
            continue
        for s in json.load(open(f, encoding='utf-8')):
            for k in known:
                known[k][s[k]] = known[k].get(s[k], 0) + 1
    for s in soldiers:
        s['additional_info'] = re.sub(r'\b[rp]oćen(a?)\b', r'rođen\1', s['additional_info'])   # the scan's роћен = рођен
        m = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)\b', s['additional_info'])
        if m and not s['birth_year']:
            s['birth_year'] = m.group(1)
        for k in known:
            v = s[k]
            if v.startswith('B') and known[k].get('Đ' + v[1:], 0) >= max(3, 5 * known[k].get(v, 0)):
                s[k] = 'Đ' + v[1:]
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/3-vojvodjanska.pdf',
        brigade_code=57,
        output_path='website/public/3-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
