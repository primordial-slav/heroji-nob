"""
Parser: 16. slavonska omladinska NOU brigada "Jože Vlahović" (brigade code 37) — its leaders.

Source: the same book as parse_16_slavonska_omladinska.py, its last list "Rukovodioci brigade od njenog formiranja
        do kraja rata" (znaci.org/00002/407.pdf pp. 424-426, printed pp. 426-428) → pages 38-40 of
        website/public/pdfs/16-slavonska-omladinska.pdf.
Names only, grouped under the duty they held, two columns a page; a column that starts without a heading continues
the list the column before it ended with:
    Komandanti brigade          Načelnici štaba brigade
    BASARIĆ Stanko              BOBETKO Mijo
    KNEŽEVIĆ Rade Tihi          ...                       (a nickname after the given name)
Each leader becomes a record whose entry is the duty (several duties when a name is under several headings), with
IDs from 0037010001 so the lists of the fallen keep theirs. Leaders who are also on a list of the fallen are made one
record with that entry by merge corrections (scripts/find_source_duplicates.py).
"""
import re

import pdfplumber

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser
from pdf_coords import viewer_words

U = 'A-ZČĆŽŠĐ'
PDF = 'website/public/pdfs/16-slavonska-omladinska.pdf'
FIRST_PAGE, LAST_PAGE = 38, 40

# the headings, and the duty each gives its names
DUTIES = {
    'komandanti brigade': 'komandant brigade',
    'načelnici štaba brigade': 'načelnik štaba brigade',
    'politički komesari brigade': 'politički komesar brigade',
    'zamjenici komandanta brigade': 'zamjenik komandanta brigade',
    'zamjenici (pomoćnici) komesara brigade': 'zamjenik (pomoćnik) komesara brigade',
    'komandanti bataljona': 'komandant bataljona',
    'politički komesari bataljona': 'politički komesar bataljona',
    'zamjenici komandanata bataljona': 'zamjenik komandanta bataljona',
    'zamjenici (pomoćnici) komesara bataljona': 'zamjenik (pomoćnik) komesara bataljona',
    'komandiri četa': 'komandir čete',
    'politički komesari četa': 'politički komesar čete',
}


def _lines(words: list[dict]) -> list[list[dict]]:
    lines = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if lines and abs(lines[-1][0]['top'] - w['top']) < 4:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(ln, key=lambda w: w['x0']) for ln in lines]


def _is_heading(text: str) -> bool:
    """'Komandanti brigade', 'Zamjenici (pomoćnici)', 'komesara brigade': every word lowercase or capitalized
    (a surname is in capitals, also where the OCR read an I as l: 'KlS Franjo')."""
    return all(re.fullmatch(r'\(?[A-ZČĆŽŠĐ]?[a-zčćžšđ]+\)?', w) for w in text.split())


def read_lines(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """One line per name, in reading order (each page's left column, then its right), the duty appended after a tab."""
    out, duty = [], ''
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(start, (end or len(pdf.pages)) + 1):
            page = pdf.pages[pno - 1]
            words = [w for w in viewer_words(page) if not re.fullmatch(r'[\\/^|]', w['text'])]   # specks
            page.close()
            # the list's title, the closing note, the page number
            words = [w for w in words if not (pno == FIRST_PAGE and w['top'] < 360) and not (pno == LAST_PAGE and w['top'] > 470)
                     and not re.fullmatch(r'\d{3}', w['text'])]
            starts = [ln[0]['x0'] for ln in _lines(words)]
            right = min((w['x0'] for ln in _lines(words) for i, w in enumerate(ln)
                         if w['x0'] > 260 and (i == 0 or w['x0'] - ln[i - 1]['x1'] > 25)), default=max(starts) + 1)
            for col in ([w for w in words if w['x0'] < right - 3], [w for w in words if w['x0'] >= right - 3]):
                heading = []
                for ln in _lines(col):
                    text = ' '.join(w['text'] for w in ln).strip()
                    if _is_heading(text):
                        heading.append(text)
                        key = ' '.join(heading).lower()
                        if key in DUTIES:
                            duty, heading = DUTIES[key], []
                        continue
                    heading = []
                    out.append({'text': text + '\t' + duty, 'x': ln[0]['x0'], 'y': round(ln[0]['top'], 1),
                                'page': pno})
    return out


def _join_pieces(tokens: list[str]) -> list[str]:
    """The text layer splits some words: 'POP AR A' (Popara), 'MATI JE VIC', 'Blagoj e', 'Ma ti ja'."""
    out = []
    for t in tokens:
        if out and (re.fullmatch(rf'[{U}]+', t) and re.fullmatch(rf'[{U}]+', out[-1]) and len(out) == 1
                    or re.fullmatch(r'[a-zčćžšđ]{1,3}', t)):
            out[-1] += t
        else:
            out.append(t)
    return out


def parse_entry(text: str) -> dict:
    """SURNAME Given [Nickname]  +  the duty"""
    name, _, duty = text.partition('\t')
    if '...' in name:                                     # "ISO ... komandir 2. č. 1. bat.": no surname printed
        given = name.split('...')[0].strip().title()
        return _record(given, '', '', f"{duty.capitalize()}; u knjizi: »{name.strip()}«.")
    tokens = _join_pieces(name.split())
    tokens = [re.sub(r'l', 'I', t) if re.fullmatch(rf'[{U}l]+', t) and 'l' in t and t != 'l' else t for t in tokens]  # ZlROVClC
    last = tokens[0] if tokens else ''
    given = tokens[1] if len(tokens) > 1 else ''
    nick = ' '.join(tokens[2:])
    info = duty.capitalize() + '.'
    if nick:
        info = f'zvani {nick}; ' + info
    return _record(last, given, '', info, rank=duty)


FIXES = {'Dulig': 'Dulić', 'Cedomir': 'Čedomir'}         # DULlG (also printed DULIC), Cedomir (Č lost)


def post(soldiers: list[dict]) -> list[dict]:
    """A name under several headings is one leader who held each of those duties (the same name twice under one
    heading would be two people)."""
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    for s in soldiers:
        s['last_name'], s['first_name'] = FIXES.get(s['last_name'], s['last_name']), FIXES.get(s['first_name'], s['first_name'])
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['first_name']) if p)
    out, seen = [], {}
    for s in sorted(soldiers, key=lambda s: (s['pdf_page'], s['pdf_x'] > 250, s['pdf_y'])):    # reading order
        key = (s['last_name'], s['first_name'])
        first = seen.get(key)
        if first and s['rank'] not in first['rank'].split('; '):
            first['rank'] += '; ' + s['rank']
            nick = re.match(r'(zvani [^;]+; )', first['additional_info'])
            first['additional_info'] = (nick.group(1) if nick else '') + first['rank'][:1].upper() + first['rank'][1:] + '.'
            continue
        seen.setdefault(key, s)
        out.append(s)
    return out


if __name__ == '__main__':
    run_parser(
        pdf_path=PDF,
        brigade_code=37,
        output_path='website/public/16-slavonska-omladinska-soldiers.json',
        start_page=FIRST_PAGE,
        end_page=LAST_PAGE,
        script='latin',
        extract_fn=read_lines,
        entry_start_re=re.compile(''),          # every line is a name
        parse_entry_fn=parse_entry,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
    )
