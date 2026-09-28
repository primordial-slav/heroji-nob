"""
Parser: 25. Srpska NOU Divizija (brigade code 19).

Source: Milojica Pantelić — "25. SRPSKA NOU DIVIZIJA"
        znaci.org/00001/123_10.pdf  →  website/public/pdfs/25-srpska-divizija.pdf
Chapter: "Spisak poginulih boraca i rukovodilaca 25. divizije" — 96 pages, single column,
Cyrillic, numbered 1-883:
    1. ИВАНОВИЋ АЛЕКСАНДАР, борац 3. чете 2. батаљона 16. српске бригаде, рођен у селу
       Црквини код Крушевца, рањен 12. јула 1944. год. на Кривој букви ...
    867. КАРАПАНЏИЋ Ј. СЛАВОЉУБ, борац чете аутоматичара 19. српске бригаде, ...
    117. ЦАКИЋ (или ЦОКИЋ, односно ...) ...
Any numbered line that starts with a capitalised word begins an entry. The running header
("23 25. srpska NOU divizija 353") is dropped. No father's names, except an occasional initial.
"""
import re
from _parser_scaffold import L, U, extract_birth_year, parse_standard_entry, repair_lj_ocr, restore_diacritics, run_parser

NUMBERED_ENTRY = re.compile(rf'^\d{{1,3}}\s?\.\s*[{U}]{{2,}}')
RUNNING_HEADER = re.compile(r'^\d*\s*25\. srpska NOU divizija\s*\d*$|^\d{1,3}$')


ALIAS = re.compile(r'\s*\(?\s*(?:ili|moguće|verovatno|odnosno)\s+([^()]*?)(?:\s*[—–-]+\s*prim\. red\.)?\)|\s*\(\?\)')


def _entry_name(t: str) -> str:
    """Normalise the name part of an entry (up to the first comma outside parentheses); alias notes
    move to the start of the bio as "ili X;"."""
    t = re.sub(rf'(?<=[{U}])-\s+(?=[{U}]{{1,}}\b)', '', t, count=1)          # "DIMITRI- JE" broken across lines
    m = re.match(r'^(\d{1,3}\.\s+)((?:[^,(]|\([^)]*\))*?)(,|$)(.*)$', t)
    if not m:
        return t
    num, name, comma, rest = m.groups()
    aliases = []

    def take(mm):
        if mm.group(0).strip() == '(?)':
            aliases.append('nesigurno prezime')
        elif mm.group(1):
            names = re.split(r',\s*odnosno\s+', mm.group(1).strip(' ,'))
            aliases.append('ili ' + ' ili '.join(n.title() for n in names))
        return ' '
    if re.search(r'\bili\b|moguće|verovatno|\(\?\)', name):
        name = ALIAS.sub(take, name)
    name = name.replace('J1', 'L')                                            # Л read as "Ј1": IJ1IĆ → ILIĆ
    name = re.sub(rf'([{U}]{{3,}})Th\b', r'\1Ć', name)                          # ROKSANDITh → ROKSANDIĆ
    name = re.sub(rf'^([{U}]{{2,}}[{U}\-]*)\.(\s)', r'\1\2', name)              # КАРАПАНЏИЋ. Ј. СЛАВОЉУБ
    name = re.sub(rf'^([{U}]{{2,}}[{U}\-]*)\s([{U}])\s(?=[{U}]{{2,}})', r'\1 \2. ', name)   # MATEJIĆ Ž ALEKSANDAR
    name = re.sub(r'\bSv\.', 'S.', name)
    name = re.sub(rf'\b([{U}])\.([{U}]{{3,}})\s*$', r'\1\2', name)               # "VUJNOVIĆ K.AMENKO" → KAMENKO
    name = re.sub(rf'(?<=[{U}])-\s?(?=[{U}]{{2,}}\s*$)', '', name)               # DIMITRI-JE, SRE-TEN
    name = re.sub(r'\s+', ' ', name).strip()
    if re.match(rf'^[{U}]{{2,}}\s+[{U}][{L}]+$', name):                        # "KADIĆ Petar" → caps given name
        head, given = name.rsplit(' ', 1)
        name = f'{head} {given.upper()}'
    prefix = '; '.join(aliases)
    if prefix:
        rest = f' {prefix};{rest}' if comma else f' {prefix}'
        comma = ','
    return f'{num}{name}{comma}{rest}'


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if RUNNING_HEADER.match(t) or (ln['page'] == 1 and re.match(r'^(?:SPISAK|POGINULIH BORACA|\*)', t)):
        return False
    t = re.sub(r'\s*\d{1,3}\s+25\. srpska NOU divizija\s+\d{1,3}\s*', ' ', t)     # header run into a line
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    """Standard parse after name normalisation; an entry whose name still doesn't fit
    ("MILADINOVIĆ D., borac") keeps its surname."""
    text = _entry_name(text)
    rec = parse_standard_entry(text)
    if rec.get('last_name'):
        return rec
    m = re.match(rf'^\d{{1,3}}\.\s+([{U}][{U}\-]+)\s*([^,]*),\s*(.*)$', text)
    if not m:
        return rec
    return {'last_name': m.group(1).capitalize(), 'first_name': '', 'middle_name': m.group(2).strip(), 'fathers_name': m.group(2).strip(),
            'full_name': f'{m.group(1).capitalize()} {m.group(2).strip()}'.strip(), 'additional_info': m.group(3).strip(),
            'birth_year': extract_birth_year(m.group(3))}


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/25-srpska-divizija.pdf',
        brigade_code=19,
        output_path='website/public/25-srpska-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=NUMBERED_ENTRY,
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        post_fn=lambda soldiers: repair_lj_ocr(restore_diacritics(soldiers)),
    )
