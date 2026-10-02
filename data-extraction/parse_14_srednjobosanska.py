"""
Parser: 14. srednjobosanska NOU brigada (brigade code 56).

Source: Stevo Samardžija, "14. srednjobosanska NOU brigada" (znaci.org 00003/579.pdf)  →
        website/public/pdfs/14-srednjobosanska.pdf (PDF pages 422-485 of the book):
    pp. 1-29  "Spisak poginulih, umrlih i nestalih boraca i rukovodilaca XIV SB NOU brigade" (book p. 393 on),
              one column:  ADŽALIĆ M. AVDO, rođen 1926, Doboj, borac 1 č. 3. bat. poginuo 6. maja 1945. ...
    pp. 30-64 "Spisak boraca 14. SBNOU brigade koji su preživjeli rat" (book p. 423 on), two columns, under the
              municipality they came from:  OPŠTINA DERVENTA / ALEKSIĆ J. NEDELJKO, 1920, Osinja;
Latin, a hanging indent; znaci.org re-typeset the book from its OCR. A survivor's entry gets its municipality
appended, "(opština Derventa)", as the 17. slavonska lists do. The editors' note after the survivors says the
brigade's archive was lost and 4,000-4,500 fighters passed through it.
"""
import re

from _parser_scaffold import (extract_lines_single_column, extract_lines_two_column, parse_standard_entry,
                              repair_lj_ocr, restore_diacritics, run_parser)

U = 'A-ZČĆŽŠĐ'
SURVIVORS_FROM = 30
_margin: dict = {}
_state = {'opstina': ''}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_single_column(pdf_path, start, SURVIVORS_FROM - 1)
    lines += extract_lines_two_column(pdf_path, SURVIVORS_FROM, end, 'auto')
    for ln in lines:
        col = (ln['page'], ln['page'] >= SURVIVORS_FROM and ln['x'] > 250)
        if re.match(rf'^[{U}]{{2}}', ln['text']):
            _margin[col] = min(_margin.get(col, 10 ** 6), ln['x'])
    return lines


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(rf'[\d\W]{{1,5}}|[{U}]', t):
        return False                                                         # page numbers, letter headings
    if ln['page'] == 1 and re.match(r'^(?:S P I S|POGINULIH, UMRLIH|XIV SB NOU)', t):
        return False
    if ln['page'] == SURVIVORS_FROM and ln['y'] < 320:
        return False                                                         # the survivors' title
    m = re.match(r'^OPŠTINA\s+(.+)$', t)
    if m:
        _state['opstina'] = m.group(1).strip().title()
        return False
    col = (ln['page'], ln['page'] >= SURVIVORS_FROM and ln['x'] > 250)
    if ln['x'] <= _margin.get(col, ln['x']) + 4 and re.match(rf'^[{U}]{{2}}', t):
        tag = (_state['opstina'] if ln['page'] >= SURVIVORS_FROM else '') or 'x'     # 'x': a marker the scaffold keeps
        t = f'§{tag}§ ' + t                                                  # an entry starts at the column's edge
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    m = re.match(r'^§([^§]*)§\s*', text)
    opstina = m.group(1) if m and m.group(1) != 'x' else ''
    text = text[m.end():] if m else text
    text = re.sub(rf'^([{U}]+)\s+[—–-]\s+([{U}]+)', r'\1-\2', text)          # "AVDIĆ — OSMANČEVIĆ"
    text = re.sub(rf'^([{U}\-]+)\s+2\.\s', r'\1 Z. ', text)                   # the initial З read as 2
    alias = re.match(rf'^([{U}\-]+)\s+\(ili\s+([{U}\-]+)\)\s+', text)        # "MILOJEVIĆ (ili MILIVOJEVIĆ) J. MILUTIN"
    if alias:
        text = alias.group(1) + ' ' + text[alias.end():]
    rec = parse_standard_entry(text)
    if alias:
        rec['additional_info'] = f'ili {alias.group(2).title()}; ' + rec['additional_info']
    split = re.fullmatch(r'(\w+)-(\w{1,3})', rec['first_name'])
    if split:                                                                # "VELIN-KA": split at the line's end
        rec['first_name'] = split.group(1) + split.group(2).lower()
        rec['full_name'] = ' '.join(p for p in (rec['last_name'], rec['middle_name'], rec['first_name']) if p)
    if opstina:
        info = rec['additional_info'].rstrip(' ;.')
        rec['additional_info'] = f'{info} (opština {opstina})'
        y = re.match(r'^(?:rod\.\s+u\s+[^,]+,\s*)?(1[89]\d\d)\b', info)
        if y and not rec['birth_year']:
            rec['birth_year'] = y.group(1)
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/14-srednjobosanska.pdf',
        brigade_code=56,
        output_path='website/public/14-srednjobosanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=lambda soldiers: repair_lj_ocr(restore_diacritics(soldiers)),
    )
