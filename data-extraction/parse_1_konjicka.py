"""
Parser: 1. konjička brigada NOVJ (brigade code 92).

Source: Milorad Gončin, "1. konjička brigada" (znaci.org 00001/278_18.pdf, its pages 22-32, book pp. 317-327)
        →  website/public/pdfs/1-konjicka.pdf. Cyrillic, two lists:
    pp. 1-4     "Spisak palih boraca i rukovodilaca Prve konjičke brigade", a hanging indent:
                    TEŠIĆ Marka TIHOMIR, rođen 15. IX 1922. godine, Korenita, srez Jadar, poginuo 25. IV 1945. godine,
                    selo Tomašica, srez Daruvar.
    pp. 5-11    "Ratni spisak starešina i boraca Prve konjičke brigade", names only in capitals, two columns:
                    ADAMOVIĆ JOVAN
The OCR reads Ћ as Б, Н, Е or К at a surname's end, Ђ as Б, and Л as A ("MIAAN" = Milan): repaired by the names the
other units know (parse_23_srpska.read_back, _parser_scaffold.repair_cyrillic_ocr). The roster holds everyone, the
fallen too.
"""
import re

import parse_23_srpska as p23
from _parser_scaffold import _record, death_type_from_text, extract_lines_single_column, repair_cyrillic_ocr, restore_diacritics, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROSTER_FROM = 5
FIXES = {'BOGOLoUB': 'BOGOLJUB', 'DOBRIČIBRADOICA': 'DOBRIČIĆ RADOJICA', 'KIJANOVINJOVAN': 'KIJANOVIĆ JOVAN',
         'MLABO': 'MLAĐO'}                                                   # roster names the OCR glued or misread


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    return extract_lines_single_column(pdf_path, 1, ROSTER_FROM - 1) + columns_reader(2)(pdf_path, ROSTER_FROM, end_page)


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|\W*\w{0,2}\W*', t) or re.match(r'^(?:SPISAK|PRVE KONJ|RATNI SPISAK)', t) or ln['y'] < 70:
        return False                                                         # headings, page numbers
    t = re.sub(r'[\s,.;:~*\'")]+$', '', t) if ln['page'] >= ROSTER_FROM else t
    if ln['page'] >= ROSTER_FROM:
        if not re.match(rf'^[{U}A-Z]{{3,}}', t):
            return False
        ln['text'] = '§r§ ' + p23.decode_head(t)
        return True
    t = re.sub(r'(?<=[A-Z])L\.(?=[A-Z])', 'LJ', t)                            # "BOGOL.UB": Љ read as L.
    if ln['x'] <= p23.margin(ln) + 5 and re.match(rf'^[{U}A-Z]{{3,}}', t):
        t = '§p§ ' + p23.decode_head(t)
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    if text.startswith('§r§'):
        for bad, good in FIXES.items():
            text = text.replace(bad, good)
        toks = [re.sub(r'[^A-ZČĆŽŠĐa-zčćžšđ-]', '', w).upper() for w in text[4:].split()]
        toks = [w for w in toks if w]
        notes = ['zvani ' + ' '.join(toks[2:]).title()] if len(toks) > 2 else []
        return _record(toks[0] if toks else '', toks[1] if len(toks) > 1 else '', '', '; '.join(notes))
    rec = p23.parse(text)
    rest = rec['additional_info']
    y = re.search(r'rođen[a]?\s+(?:\d{1,2}\.\s*[IVX]+\.?\s*)?(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    rec.pop('birth_place', None)
    b = re.search(rf'rođen[a]?\s+(?:[^,]*?1[89]\d\d\.?\s*(?:godine)?)?,?\s*(?:u\s+)?(?:s\.\s*|selo\s+)?([{U}][^,]*?),\s*(?:srez\s+)?([{U}][^,]*?),', rest)
    if b:
        rec['birth_place'] = b.group(1).strip() + ', ' + re.sub(r'\s+\d.*$', '', b.group(2).strip())
    rec['death_type'] = death_type_from_text(rest) or 'poginuo'
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """A Cyrillic text layer keeps С apart from Ш: of restore_diacritics' changes only the -ić ending stays
    ("КОСТА" is Kosta, not the Košta other books print)."""
    soldiers = repair_cyrillic_ocr(soldiers, ik_is_ic=True)
    fields = ('first_name', 'middle_name', 'last_name')
    printed = [{f: s[f] for f in fields} for s in soldiers]
    soldiers = restore_diacritics(soldiers)
    for s, was in zip(soldiers, printed):
        for f, old in was.items():
            if s[f] != old and not (f == 'last_name' and old.endswith('ic') and s[f] == old[:-2] + 'ić'):
                s[f] = old
        s['fathers_name'] = s['middle_name']
        if s['last_name'].endswith('ii'):
            s['last_name'] = s['last_name'][:-1] + 'ć'
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/1-konjicka.pdf',
        brigade_code=92,
        output_path='website/public/1-konjicka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=re.compile(r'^§[rp]§'),
        parse_entry_fn=parse,
        prepare_fn=p23.prepare,
        line_filter=keep,
        post_fn=post,
    )
