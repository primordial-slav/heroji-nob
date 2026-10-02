"""
Parser: 21. srpska (2. šumadijska) NOU brigada (brigade code 80).

Source: Isidor Đuković, "Druga šumadijska - 21. srpska brigada" (znaci.org 00001/197_15.pdf, "U koloni Druge
        šumadijske brigade", book pp. 385-...)  →  website/public/pdfs/21-srpska.pdf (its pages 1-86):
    pp. 3-28    "Dali su živote za slobodu" (the fallen)
    pp. 29-79   "Preživeli su rat"
    pp. 80-86   "Borili su se u brigadi": others the archive or the memoirs place in the brigade
    (pp. 87-102, the political workers of the two districts, fallen and living, are not read: they were the
    districts' party workers, not the brigade's)
Cyrillic, one column; the surname and the given name in capitals, both parents between them, a nickname after:
    АГАЧЕВИЋ, Драгутина и Лепосаве, ЧЕДОМИР, делегат вода, рођен 17. 3. 1926. у Стублинама, Обреновац, ...
    АЋИМОВИЋ Миладина ЗОРКА, болничарка, рођена 15. 1. 1908. ...
    АДАМОВИЋ СТОЈАН, по архиви, борац (шофер), 29. 9. 1944. био је у бригади.
An entry starts flush or set in, so a line opens one where it starts with a name in capitals after a line that ended
a sentence. The mother goes into the bio as "majka X" (as in 1. šumadijska). Л is read as Ј1.
"""
import re

from _parser_scaffold import _record, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_TO, SURVIVORS_TO = 28, 79
NOT_NAMES = {'KPJ', 'SKOJ', 'NOP', 'NOB', 'NOV', 'NOVJ', 'SSSR', 'OZN', 'OZNA', 'JNA', 'II', 'III', 'IV', 'VI', 'OK', 'SK'}
_prev = {'end': True, 'page': 0}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])J1|J1(?=[A-ZČĆŽŠĐ])', 'L', t).replace('j1', 'l')     # "AJ1EKSEJ", "DAJ1I"
    if ln['page'] != _prev['page']:
        _prev.update(page=ln['page'], end=True)
    if re.fullmatch(r'[\d\W]{1,5}|\w', t) or re.match(r'^(?:DALI SU ŽIVOTE|PREŽIVELI SU RAT|BORILI SU SE U)', t):
        _prev['end'] = True
        return False
    first = re.match(rf'^([{U}]{{2,}}(?:-[{U}]{{2,}})?)[.,]?(?:\s|$)', t)
    if first and first.group(1) not in NOT_NAMES and _prev['end']:
        kind = 'p' if ln['page'] <= FALLEN_TO else 's' if ln['page'] <= SURVIVORS_TO else 'b'
        t = f'§{kind}§ ' + t
    _prev['end'] = bool(re.search(r'[.)]\s*$', t))
    ln['text'] = t
    return True


NAME = re.compile(rf'^([{U}]{{2,}}(?:-[{U}]{{2,}})?)\s*[.,]?\s*'
                  rf'(?:([{U}][{L}]+(?:-[{U}][{L}]+)?)(?:\s+i\s+([{U}][{L}]+))?\s*,?\s*|([{U}])\.\s*)?'
                  rf'([{U}]{{2,}}(?:-[{U}]{{2,}})?)((?:\s+[{U}][{L}]+)?)\s*[,.]?\s*(.*)$')


def parse(text: str) -> dict:
    kind = text[1]
    text = re.sub(r'^§\w§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "Bran- čiću"
    text = re.sub(r'\b([Rr])oćen(a?)\b', r'\1ođen\2', text)
    m = NAME.match(text)
    if not m:
        head, _, rest = text.partition(',')
        toks = head.split()
        rec = _record(toks[0].title() if toks else '', ' '.join(t.title() for t in toks[1:]), '', rest.strip())
    else:
        last, father, mother, initial, given, nick, rest = m.groups()
        if mother and mother.endswith('e'):
            mother = mother[:-1] + 'a'                                       # the genitive: "Kosane" = Kosana
        paren = re.match(r'^\(([^)]+)\)\s*,?\s*', rest)                     # "(Žika Mornar), načelnik štaba"
        if paren and not nick.strip():
            nick, rest = paren.group(1), rest[paren.end():]
        notes = (['majka ' + mother] if mother else []) + (['zvani ' + nick.strip()] if nick.strip() else [])
        rec = _record(last.title(), given.title(), father or (initial + '.' if initial else ''),
                      '; '.join(notes + ([rest.strip()] if rest.strip() else [])))
    y = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)', text)
    if y:
        rec['birth_year'] = y.group(1)
    if kind == 'p':
        rec['death_type'] = 'umro' if re.search(r'\bumr(?:o|la)\b', text) and not re.search(r'\bpogin', text) else 'poginuo'
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/21-srpska.pdf',
        brigade_code=80,
        output_path='website/public/21-srpska-soldiers.json',
        start_page=3,
        end_page=86,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§\w§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=repair_cyrillic_ocr,
    )
