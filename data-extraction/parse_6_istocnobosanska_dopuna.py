"""
Parser: 6. istočnobosanska proleterska brigada (brigade code 42), second book: the fighters found after its roster.

Source: Rudi Petovar, Savo Trikić, *Šesta proleterska istočnobosanska brigada* (Beograd 1982; znaci.org 00001/140,
the chapter 140_14.pdf "Zbirni podaci o borcima brigade", its PDF pp. 8-20, book p. 676 on) →
website/public/pdfs/6-istocnobosanska-dopuna.pdf. The brigade's roster of 6,020 fighters was printed in *Borbeni put
Šeste proleterske brigade* (1977); this book adds those found from 1977 to 1981, in Cyrillic, one column:
    "Pregled podataka za 213 boraca brigade čiji podaci nisu objavljeni u knjizi ..." (PDF pp. 8-19), an entry a
        paragraph, ending with a semicolon:
        Аксентијевић Александар, рођен у с. Гривац, Кнић, у НОБ ступио 1944., борац, погинуо 18. децембра 1944. ...;
    "Spisak boraca za koje nije utvrđeno mjesto i vrijeme pogibije, odnosno nestanka" (p. 20), a name a line.
Surname, the father in the genitive or an initial, the given name. The OCR reads ђ as ћ ("роћен") and the capital Ћ as
Б, so a run of B names where the list is at Ć ("Берајић" = Ćerajić, "Бурчић" = Ćurčić) takes the letter back.

The unit's first book is its Borci Sutjeske chapter; these get 0042010001 on.
Usage: python data-extraction/parse_6_istocnobosanska_dopuna.py
"""
import re

from _parser_scaffold import _record, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_state = {'list': 0, 'open': False}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|\S{1,2}|\d+;', t):
        return False                                     # page numbers ("691;"), specks
    if re.match(r'^(?:PREGLED PODATAKA|SPISAK BORACA ZA KOJE)', t):
        _state['list'] = 1 if t.startswith('PREGLED') else 2
        _state['open'] = False
        return False
    if not _state['list'] or (re.fullmatch(rf'[{U}0-9 .,„"“”\-()]+', t) and len(t) > 6):
        return False                                     # before the list; the rest of a title in capitals
    if _state['list'] == 1:
        if not _state['open'] and re.match(rf'^[{U}][{L}]+', t):
            t = '§x§ ' + t
        _state['open'] = not t.endswith(';')
    else:                                                 # a name a line
        if re.match(rf'^[{U}][{L}]+ ', t):
            t = '§x§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).strip().rstrip(';,.').strip()
    text = re.sub(r'\broćen', 'rođen', text)
    head, _, info = text.partition(',')
    words = head.split()
    last = words[0] if words else ''
    if len(words) >= 3:
        father, given = words[1], ' '.join(words[2:])     # "Банковић Боже Миливоје", "Цветић М. Павле"
    else:
        father, given = '', ' '.join(words[1:])
    rec = _record(last, given, father, info.strip() + '.' if info.strip() else '')
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
    rec['birth_year'] = y.group(1) if y else ''
    return rec


def letters(soldiers: list[dict]) -> list[dict]:
    """A run of B names where the list is at Ć (between C/Č/Ć and Č/Ć/D names) or at Đ: the OCR's Б for Ћ, Ђ"""
    initial = lambda s: s['last_name'][:1]
    i = 0
    while i < len(soldiers):
        if initial(soldiers[i]) != 'B':
            i += 1
            continue
        j = i
        while j < len(soldiers) and initial(soldiers[j]) == 'B':
            j += 1
        before = initial(soldiers[i - 1]) if i else ''
        after = initial(soldiers[j]) if j < len(soldiers) else ''
        for letter, lo, hi in (('Ć', 'CČĆ', 'ČĆD'), ('Đ', 'DĐ', 'ĐE')):
            if before in lo and after in hi and before and after:
                for s in soldiers[i:j]:
                    s['last_name'] = letter + s['last_name'][1:]
        i = j
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/6-istocnobosanska-dopuna.pdf',
        brigade_code=42,
        output_path='website/public/6-istocnobosanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=letters,
        id_start=10001,
        keep_other_sources=True,
    )
