"""
Parser: 12. krajiška NOU brigada (brigade code 54).

Source: Joco Marjanović, Mile Kukolj, Milutin Vujović, Boro Gaćeša, Rade Ranilović, "Dvanaesta krajiška NOU
        brigada" (znaci.org 00001/168): two closing chapters, Cyrillic, one column, a hanging indent:
    168_7.pdf → website/public/pdfs/12-krajiska-poginuli.pdf   "Poginuli borci i rukovodioci Brigade"
        Андрић М. Андрија, борац, рођен 1922. у с. Бела Црква, Крупањ, погинуо 18. 10. 1944. код Авале, Београд
    168_8.pdf → website/public/pdfs/12-krajiska-prezivjeli.pdf "Preživjeli borci i rukovodioci Brigade", pp. 1-70
        Аврамовић В. Момчило, 1922, Врчин, Гроцка
The names are not in capitals: surname, the father's initial, the given name. Not parsed: the survivors the
authors had nothing more on, names run on with commas (168_8.pdf pp. 71-72).
"""
import re

from _parser_scaffold import _record, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_margin: dict = {}


_note: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        key = (ln['file'], ln['page'])
        _margin[key] = min(_margin.get(key, 10 ** 6), ln['x'])
        if ln['page'] == 1 and ln['text'].lstrip().startswith('*') and ln['file'] not in _note:
            _note[ln['file']] = ln['y']                                     # the editors' footnote on the first page


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] == 1 and ln['y'] >= _note.get(ln['file'], 10 ** 6):
        return False
    if re.fullmatch(r'[\d\W]{1,5}', t) or re.match(r'^(?:POGINULI|PREŽIVJELI) BORCI|^BRIGADE\*?$|^\*', t):
        return False
    if ln['x'] <= _margin[(ln['file'], ln['page'])] + 5 and re.match(rf'^[{U}]', t):
        t = '§x§ ' + t                                                       # an entry starts at the margin
    ln['text'] = t
    return True


NAME = re.compile(rf'^([{U}][{L}]+(?:-[{U}][{L}]+)?)\.?\s+(?:\(([{U}][{L}]+)\)\s+|(\S{{1,3}})\.\s*(?:\S\.\s*)?)?'
                  rf'(?:\(([^)]*)\)\s*)?(?:dr\s+)?([{U}][{L}]+)')
INITIAL = {'3': 'Z', 'T>': 'Đ', '11': 'P', 'iA': 'D', 'JB': 'Lj'}


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text)
    text = re.sub(rf'^([{U}][{L}]+)\s+[—–-]\s+([{U}][{L}]+)', r'\1-\2', text)          # "Majkić — Vujić"
    head, comma, rest = text.partition(',')
    m = NAME.match(head)
    if not m:
        toks = head.split()
        return _record(toks[0] if toks else '', ' '.join(toks[1:]), '', rest.strip())
    last, father_name, initial, nick, given = m.groups()
    father = father_name or ((INITIAL.get(initial, initial) + '.') if initial else '')
    extra = head[m.end():].strip()
    info = rest.strip()
    prefix = []
    if re.search(r'\bdr\s', head[:m.end()]):
        prefix.append('dr.')
    if nick:
        prefix.append(f'zvani {nick.strip()}')
    elif re.match(r'\(([^)]*)\)', extra):
        prefix.append('zvani ' + re.match(r'\(([^)]*)\)', extra).group(1).strip())
        extra = re.sub(r'^\([^)]*\)\s*', '', extra)
    if extra:
        info = extra + (', ' + info if info else '')
    if prefix:
        info = '; '.join(prefix) + '; ' + info
    return _record(last, given, father, info)


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_cyrillic_ocr(soldiers)
    for s in soldiers:
        if s['pdf_file'] == '12-krajiska-prezivjeli.pdf' and not s['birth_year']:
            m = re.match(r'^(1[89]\d\d)\b', s['additional_info'])
            if m:
                s['birth_year'] = m.group(1)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/12-krajiska-poginuli.pdf',
        brigade_code=54,
        output_path='website/public/12-krajiska-soldiers.json',
        start_page=1,
        end_page=None,
        additional_pdfs=[{'pdf_path': 'website/public/pdfs/12-krajiska-prezivjeli.pdf', 'start_page': 1, 'end_page': 70}],
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
