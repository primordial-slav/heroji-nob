"""
Parser: Druga lička proleterska brigada (brigade code 3) — survivors, from a second book.

Source: "DRUGA LIČKA PROLETERSKA BRIGADA — Sjećanja", chapter "Spisak preživjelih boraca i starješina Druge
        ličke proleterske brigade" (author of the lists: Đuro Mileusnić)
        znaci.org  →  website/public/pdfs/druga-licka-sjecanja-prezivjeli.pdf
Two columns, Latin; the gutter moves from page to page (auto). pp. 2-187 the list, then the book's contents.
    ADAMOVIĆ PETRA MIRKO rođen 1918. u Ličkom Petrovom Selu - T. Korenica. U NOB-1941. Borac brigade. ...
    AJDUKOVIĆ ILIJE ANDRIJA NANIJA rođen 1925. u Oraovcu - D. Lapac. ...      (a nickname after the name)
Entries are separated by a blank line, not by indentation; the father is printed in caps like the name.

Unit 3's file already holds the Military History Institute's list of the fallen (druga-licka-spisak.pdf,
IDs from 0003000001): these records get IDs from 0003010001 and a re-run replaces only them.
"""
import glob
import json
import re

from _margin_entries import split_leading_aliases
from _parser_scaffold import parse_standard_entry, repair_lj_ocr, restore_diacritics, run_parser

LETTER_HEADING = re.compile(r'^[A-ZČĆŽŠĐ]{1,2}$')
JOIN = '⁠'          # word joiner after the first word of a line that continues a name broken with a hyphen
_prev = {'text': ''}


def _known_names():
    """Folded surnames and given/father names of the other units, to rejoin names the OCR split."""
    last, other = set(), set()
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.endswith('druga-licka-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                last.add(_fold(s['last_name']))
                other.update(_fold(s.get(k) or '') for k in ('first_name', 'middle_name'))
    return last, other


def _fold(w: str) -> str:
    return w.upper().translate(str.maketrans('ČĆŽŠĐ', 'CCZSD'))


KNOWN_LAST, KNOWN_OTHER = _known_names()


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if LETTER_HEADING.match(t) or re.fullmatch(r'[\W\d]{1,6}', t):
        return False
    # "... MILIVOJA DRAGO-" / "MIR U NOB-1944": the second line continues the name, it doesn't start an entry
    # (the marker goes after the first word: the scaffold strips anything non-alphanumeric at the start)
    if re.search(r'[A-ZČĆŽŠĐ]-$', _prev['text']) and re.match(r'^[A-ZČĆŽŠĐ]', t):
        t = re.sub(r'^(\S+)', r'\1' + JOIN, t, count=1)
    ln['text'] = _prev['text'] = t
    return True


def _rejoin(tokens: list[str]) -> list[str]:
    """Words the OCR split: "GAVRILO VIĆ KRSTI VO JA", "ALTA RAC", "BER ETI Ć". Adjacent caps words are joined
    when the joined word is a name used elsewhere and the pieces are not all names themselves."""
    out, i = [], 0
    while i < len(tokens):
        known = KNOWN_LAST if not out else KNOWN_OTHER
        for j in range(min(len(tokens), i + 5), i + 1, -1):
            w = ''.join(tokens[i:j])
            if _fold(w) in known and not all(len(t) > 2 and _fold(t) in KNOWN_OTHER | KNOWN_LAST for t in tokens[i:j]):
                out.append(w)
                i = j
                break
        else:
            out.append(tokens[i])
            i += 1
    return out


def parse_entry(text: str) -> dict:
    text = re.sub(r'-(\S+)' + JOIN, r'\1', text).replace(JOIN, '')        # "DRAGO-MIR⁠" → "DRAGOMIR"
    text = re.sub(r'([A-ZČĆŽŠĐ])- ([A-ZČĆŽŠĐ])', r'\1\2', text)            # "JELISA- VETA"
    text = re.sub(r'\bro- ?(đen|den)', r'ro\1', text)
    head = re.match(r'^[A-ZČĆŽŠĐ0-9!.\- ]+(?=\s|$)', text)
    if head:
        h = re.sub(r'(?<=[A-ZČĆŽŠĐ])1(?=[A-ZČĆŽŠĐ])|(?<=[A-ZČĆŽŠĐ])1\b', 'I', head.group(0))    # "BOGUTOV1Ć"
        cut = re.search(r'\sU\s+NOB', h)            # "PAVLOVIĆ M. ŽIVKO U NOB-1944.": no birth, the name ends at "U"
        name, rest = (h[:cut.start()], ',' + h[cut.start():]) if cut else (h, '')
        toks = name.split()
        for j in (4, 3, 2):         # a surname in short pieces: "BER ETI Ć", "STE VIC", "JELO VAC"
            w = ''.join(toks[:j])
            if len(toks) > j and all(len(t) <= 4 for t in toks[1:j]) and len(toks[0]) <= 5 and len(w) >= 5 and \
                    re.search(r'(?:IĆ|IC|AC|AK|AR|OV|EV)$', w) and (len(toks[0]) <= 3 or _fold(toks[0]) not in KNOWN_LAST):
                toks = [w] + toks[j:]
                break
        name = ' '.join(_rejoin(toks))
        text = name + rest + text[head.end():]
    return parse_standard_entry(text)


def nicknames(soldiers: list[dict]) -> list[dict]:
    """SURNAME FATHER GIVEN NICKNAME: "AJDUKOVIĆ ILIJE ANDRIJA NANIJA"; or joined by a hyphen: "PETAR-PETLJICA",
    "RADE-RAJKO" (the hyphen of a name broken across lines is already gone)."""
    for s in soldiers:
        m = re.match(r'^([A-ZČĆŽŠĐ]{3,}) (?=ro[đd]en)', s['additional_info'])         # "JOVICA rođen 1920."
        if m:
            s['additional_info'] = f'zvani {m.group(1).capitalize()}; ' + s['additional_info'][m.end():]
        g = s['first_name']
        if '-' in g:
            a, b = g.split('-', 1)
            if _fold(a + b) in KNOWN_OTHER and _fold(a) not in KNOWN_OTHER:
                s['first_name'] = (a + b).capitalize()
            elif _fold(a) in KNOWN_OTHER:
                s['first_name'] = a + (' ' + b if ' ' in g else ' ' + b)
        words = s['first_name'].split()
        if len(words) == 2 and s.get('middle_name'):
            s['first_name'] = words[0]
            s['additional_info'] = f'zvani {words[1]}; ' + s['additional_info']
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    return nicknames(split_leading_aliases(repair_lj_ocr(restore_diacritics(soldiers))))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/druga-licka-sjecanja-prezivjeli.pdf',
        brigade_code=3,
        output_path='website/public/druga-licka-soldiers.json',
        start_page=2,
        end_page=187,
        layout='two_column',
        col_split_x='auto',
        script='latin',
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
    )
