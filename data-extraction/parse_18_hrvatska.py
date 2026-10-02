"""
Parser: 18. hrvatska istočnobosanska NOU brigada (brigade code 52).

Source: "Osamnaesta hrvatska istočnobosanska brigada" (zbornik, Grupa autora; znaci.org 00001/251_4.pdf), "Spisak
        boraca 18. hrvatske istočnobosanske narodnooslobodilačke udarne brigade" (book pp. 582-696)  →
        website/public/pdfs/18-hrvatska.pdf (pages 11-124 of the chapter PDF).
One column, Latin; znaci.org re-typeset the book from its OCR. Each entry's first line is indented:
    ABADŽIĆ Sime RAJKA, rođena 1923. godine u selu Jablanica, Lopare, SRBiH, Srpkinja, zemljoradnik, stupila u
    Brigadu 1944. godine, borac 3. bataljona. Poginula aprila 1945. godine kod Sarajeva.
Survivors and the fallen. Not parsed: the list of the brigade's officers by duty, names only (book pp. 573-581).
"""
import re

from _parser_scaffold import parse_standard_entry, repair_lj_ocr, restore_diacritics, run_parser

U = 'A-ZČĆŽŠĐ'
_margin: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _margin[ln['page']] = min(_margin.get(ln['page'], 10 ** 6), ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] == 1 and ln['y'] < 240:
        return False                                                         # the list's title
    if re.fullmatch(r'[\d\W]{1,5}', t):
        return False                                                         # page numbers
    if ln['x'] > _margin[ln['page']] + 15 and re.match(rf'^[{U}]', t):
        t = '§x§ ' + t                                                       # an indented first line starts an entry
    ln['text'] = t
    return True


FATHER_FIXES = {'Ornerà': 'Omera', 'ümera': 'Omera'}


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text)
    text = re.sub(rf'^([{U}]+) - ([{U}]+)', r'\1-\2', text)                  # "MAKSIMOVIĆ - DESANČIĆ"
    text = re.sub(rf'^([{U}]) ([{U}]{{3,}})', r'\1\2', text)                 # "J AĆIMOVIĆ"
    text = re.sub(rf'(?<=[a-zčćžšđ])\.(?=[{U}]{{2}})', ' ', text)            # "Sulje.OSMAN"
    text = re.sub(rf'(?<=[{U}]{{2}} )([{U}]{{2,}})\. (?=ro[dđ]en)', r'\1, ', text)   # "dr ASIM. rođen"
    head = re.match(rf'^(\S+)\s+(.*?)(?=\s[{U}]{{2,}}[{U}\s\-]*[,.]?\s+ro[dđ]en|\s[{U}]{{2,}}[{U}\-]*,)', text)
    if head:
        surname, middle = head.groups()
        surname = re.sub(rf'(?<=[{U}])1(?=[{U}])', 'I', surname).replace('_', '')   # "DOGLADOV1Ć"
        dr = re.search(r'\bdr\b\.?\s*', middle)
        if dr:
            middle = middle[:dr.start()] + middle[dr.end():]
        caps = re.match(rf'^([{U}]{{3,}})\s+(.*)$', middle)
        if caps:                                                             # "MAKSIMOVIĆ DESANČIĆ Danila PERO"
            surname, middle = surname + '-' + caps.group(1), caps.group(2)
        middle = re.sub(r'[,.]', '', middle).strip()
        if ' ' in middle and re.fullmatch(r'[\wàü ]+', middle):
            middle = middle.replace(' ', '')                                 # "Sulej mana", "Me h med a"
        middle = FATHER_FIXES.get(middle, middle)
        text = surname + (' ' + middle if middle else '') + text[head.end():]
    dr = head and dr
    text = re.sub(rf'^([{U}\-]+ [{U}][a-zčćžšđ]+ [{U}\-]+(?: [{U}\-]+)?) (?=rođen|roden)', r'\1, ', text)   # a comma missing
    text = re.sub(r'(?<=, )roden(a?)\b', r'rođen\1', text, count=1)                                      # OCR "roden"
    rec = parse_standard_entry(text)
    if dr:
        rec['additional_info'] = 'dr. ' + rec['additional_info']           # "NUHIĆ Huseina dr ASIM"
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/18-hrvatska.pdf',
        brigade_code=52,
        output_path='website/public/18-hrvatska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=lambda soldiers: repair_lj_ocr(restore_diacritics(soldiers)),
    )
