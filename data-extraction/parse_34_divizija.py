"""
Parser: 34. udarna divizija NOVJ (brigade code 97).

Source: Vladimir Hlaić, "34. udarna divizija NOV i PO Hrvatske" (znaci.org 00003/641_1.pdf, 32 pages, book pp. 401-432)
        →  website/public/pdfs/34-divizija.pdf. Latin, a numbered table:
    "Pregled poginulih boraca i rukovodilaca 34. divizije" (1,410 rows)
        Prezime i ime | Čin | Brig. | Rođen | Mjesto rođenja | U NOB | Poginuo kod | Datum pogibije
        1. ANTOLIĆ Milan | borac | KB | 1920. | Žabljak, Barilović | 1944. | D.kupčina | 06.09.44.
The columns sit at the same distances from each page's row numbers. A cell's second line, or a cell set a line above
or below its row, goes to the nearest row. The brigade (KB = Karlovačka brigada, FOS = "Franjo Ogulinac Seljo",
ŽB = Žumberačka, OBJV = Omladinska brigada "Joža Vlahović", T-PO = Turopoljsko-posavski odred, ...) goes to
unit_detail. Names as in the Karlovac archive's lists, put right by parse_8_kordunaska_divizija's helpers.
"""
import glob
import json
import re
from collections import Counter, defaultdict

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
COLS = (14, 82, 110, 132, 152, 234, 260, 295)                              # name, rank, brigade, born, birthplace, joined, place, date
UNITS = {'KB': 'Karlovačka brigada', 'kb': 'Karlovačka brigada', 'UKB': 'Karlovačka udarna brigada',
         'FOS': 'brigada „Franjo Ogulinac Seljo“', 'ŽB': 'Žumberačka brigada', 'Žb': 'Žumberačka brigada',
         'ŽN': 'Žumberačka brigada', 'OBJV': 'Omladinska brigada „Joža Vlahović“', 'OMJV': 'Omladinska brigada „Joža Vlahović“',
         'T-PO': 'Turopoljsko-posavski partizanski odred', 'TPO': 'Turopoljsko-posavski partizanski odred',
         'T-P': 'Turopoljsko-posavski partizanski odred', 'KPO': 'Karlovački partizanski odred', 'KP': 'Karlovački partizanski odred',
         'ŽPO': 'Žumberačko-pokupski partizanski odred', 'ZPO': 'Žumberačko-pokupski partizanski odred',
         '34.d.': 'štab 34. divizije', '34,d.': 'štab 34. divizije', '34.d': 'štab 34. divizije'}
NUM = re.compile(r'^(?:\d{1,4}|1L|\d{2,3}l)[.,]?$|^\d{1,4}\.(?=[A-ZČĆŽŠĐ])')


def corpus() -> None:
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if fn.replace('\\', '/').endswith('/34-divizija-soldiers.json'):
            continue
        for s in json.load(open(fn, encoding='utf-8')):
            for f in k8._spell:
                if s.get(f):
                    k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def _lines(words: list[dict]) -> list[list[dict]]:
    out: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if out and abs(out[-1][0]['top'] - w['top']) <= 2.5:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(ln, key=lambda w: w['x0']) for ln in out]


def read_rows(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages[start_page - 1:end_page], start_page):
            words = [w for w in viewer_words(page) if pno > 1 or w['top'] > 125]   # the list's heading and the table's
            left = min(w['x0'] for w in words)
            xs = [round(w['x0']) for w in words if NUM.match(w['text']) and w['x0'] < left + 8]
            n = max(set(xs), key=xs.count)
            edges = [n + c for c in COLS]
            anchors = []
            for ln in _lines(words):
                first = ln[0]
                if first['x0'] < n + 8:                                      # a row starts at the numbers' edge ("3®.", "1Ö37.")
                    anchors.append({'y': first['top'], 'x': first['x0'], 'cells': [[] for _ in COLS]})
            if not anchors:
                continue
            for w in words:
                a = min(anchors, key=lambda a: (abs(a['y'] - w['top']), -a['y']))
                if abs(a['y'] - w['top']) > 9:
                    continue                                                 # the editors' closing note
                col = max((i for i, e in enumerate(edges) if w['x0'] >= e - 2), default=0)
                a['cells'][col].append(w)
            for a in anchors:
                cells = [' '.join(w['text'] for w in sorted(c, key=lambda w: (round(w['top'] / 4), w['x0']))) for c in a['cells']]
                rows.append({'page': pno, 'x': a['x'], 'y': a['y'], 'text': '§t§ ' + '¦'.join(cells)})
    return rows


def parse(text: str) -> dict:
    name, rank, unit, born, place, joined, fell, date = (p.strip() for p in (text[4:].split('¦') + [''] * 8)[:8])
    name = re.sub(r'^1L\s+', '', name)                                       # "1L" = 11.
    name = re.sub(r'^[^\sA-Za-zČĆŽŠĐ]*(?:[^\s\d]{0,2}\d)+[^A-Za-zČĆŽŠĐ\s]*\s*(?=[A-ZČĆŽŠĐl])', '', name)   # the row number, misread too
    name = re.sub(r'^(?=[\dIlLÖO®!]*\d)[\dIlLÖO®!]{1,5}[.,]*\s*', '', name)   # ("1360.KARNAS", "1I76TURK", "1Đ75.", "U52.")
    name = re.sub(r'^[lIO\d]{1,4}[.,]\s*(?=[A-ZČĆŽŠĐ]{2})', '', name)         # "1 lOl.ŠANDOR" = 1101., "135 l.HAPAČ"
    name = re.sub(r'^[^\sa-z]{1,5}\.(?=[A-ZČĆŽŠĐ]{3})', '', name)             # "ÌOIO.SAMBOL" = 1010.
    name = re.sub(r'^[.\s]+', '', name)                                       # "281. .FRIC"
    name = re.sub(r'^([A-ZČĆŽŠĐ]) (?=[A-ZČĆŽŠĐ]{2})', r'\1', name)            # "S AMACI." = SAMAC I.
    name = re.sub(r'(?<=[A-ZČĆŽŠĐ]{2})1\.', ' I.', name)                     # "BAJIĆ1. Juraj"
    name = re.sub(r'\s+(?:borac|k-dant|komandant|oper\.ofic)\b.*$|(?<=[a-zčćžšđ])oper\.ofic$|,.*$', '', name)   # rank run in
    name = re.sub(r'(?<=[A-ZČĆŽŠĐ])1(?=[A-ZČĆŽŠĐ])', 'I', name)             # "BAĆ1Ć", "DELIMAR1Ć"
    name = re.sub(rf'([{U}]{{2,}})([{U}]\.)', r'\1 \2', name)               # "GALOVIĆJ. Stjepan"
    name = re.sub(rf'([{U}]\.)(?=[{U}][{L}])', r'\1 ', name)                # "M.Nikolai"
    name = re.sub(rf'([{U}]{{3,}})([{U}][{L}])', r'\1 \2', name)            # "ANTOLEKMijo"
    words = name.split()
    if len(words) >= 3 and re.fullmatch(rf'[{U}][{L}]+', words[0]) and re.fullmatch(rf'[{U}]\.', words[1]):
        words[0] = words[0].upper()                                          # "Modic J. Juraj"
    caps = []
    while words and re.fullmatch(rf'[{U}][{U}l10\-]+', words[0]) and not re.fullmatch(rf'[{U}]\.', words[0]):
        caps.append(k8.caps_word(words.pop(0)))
    father = words.pop(0) if words and re.fullmatch(rf'(?:[{U}i]|Lj|Nj|Dž)\.?', words[0]) and len(words) > 1 else ''
    father = (father if not father or father.endswith('.') else father + '.').upper() if len(father) <= 2 else father
    given = re.sub(r'\s*\d+\.?', '', ' '.join(words)).strip(' ,.')                # "Lovro 43."
    given = given[:1].upper() + given[1:]                                    # "josip"
    if caps and not k8.known(caps[0]) and k8.known(caps[0][:-1]) and not father and len(caps) == 1:
        caps[0], father = caps[0][:-1], caps[0][-1] + '.'                   # "BRITVECN Josip" = BRITVEC N. Josip
    last = k8.join_parts(caps, 'last_name')
    for_unit = UNITS.get(unit.split()[0], '') if unit else ''
    rank_text = rank if not re.fullmatch(r'[\d.]*', rank) else ''
    date = date.strip(' .')
    d = re.fullmatch(r'(\d{1,2})\.(\d{1,2})\.(\d{2})', date)
    death_date = f'{int(d.group(1))}. {int(d.group(2))}. 19{d.group(3)}' if d else ''
    info = ', '.join(p for p in (rank_text, unit, (born + ' ' + place).strip(' .,') if born or place else '',
                                 f'u NOB {joined.strip(" .")}' if re.search(r'19\d\d', joined) else '',
                                 ('poginuo ' + fell if fell and not re.match(r'(?i)umr|ranj', fell) else fell),
                                 date) if p)
    rec = _record(last, given, father, info)
    y = re.search(r'1[89]\d\d', born)
    if y:
        rec['birth_year'] = y.group(0)
    if place:
        rec['birth_place'] = re.sub(r'\s+', ' ', place).strip(' ,.')
    if death_date:
        rec['death_date'] = death_date
    rec['death_type'] = 'umro' if re.search(r'(?i)\bumr', fell) else 'poginuo'
    if fell and not re.search(r'(?i)\bumr|ranj|zavr', fell):
        rec['death_place'] = fell
    if for_unit:
        rec['unit_detail'] = for_unit
    duty = re.sub(r'\s+', ' ', rank_text).strip(' ,')
    for short, full in RANKS:
        duty = re.sub(short, full, duty)
    if duty and re.fullmatch(rf'[{L} ]+', duty):
        rec['rank'] = duty
    return rec


RANKS = [(r'^k-?dir\s*č(?:ete|\.)?$|^k-dirčete$', 'komandir čete'), (r'^k-?sar\s*č(?:ete|\.)?$|^k-sarčete$', 'komesar čete'),
         (r'^k-?dir\s*v(?:oda|\.)?$', 'komandir voda'), (r'^k-?dir\s*od\.?$', 'komandir odeljenja'),
         (r'^k-?dant\s*b(?:at|atalj)?\.?$', 'komandant bataljona'), (r'^ml\.\s*vod\.?$', 'mlađi vodnik'),
         (r'^st\.\s*vod\.?$', 'stariji vodnik'), (r'^pol\.\s*del\.?$', 'politički delegat'), (r'^del\.\s*voda$', 'delegat voda'),
         (r'^zastav\.$', 'zastavnik'), (r'^p?\.?\s*poruč\.$', 'poručnik'), (r'^potpor\.$', 'potporučnik'),
         (r'^bolnič\.$', 'bolničar'), (r'^intend\.$', 'intendant'), (r'^inf\.\s*oficir$', 'informativni oficir'),
         (r'^artilj\.$', 'artiljerac'), (r'^int\.\s*batalj\.$', 'intendant bataljona')]


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/34-divizija.pdf',
        brigade_code=97,
        output_path='website/public/34-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=read_rows,
        script='latin',
        entry_start_re=re.compile(r'^§t§'),
        parse_entry_fn=parse,
        post_fn=k8.post,
    )
