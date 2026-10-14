"""
Parser: Prvi tenkovski bataljon NOV i PO Hrvatske (brigade code 162).

Source: Vujo Vidaković, "Prvi tenkovski bataljon" (znaci.org 00003/543.pdf), the roll at the end
        →  website/public/pdfs/1-tenkovski-bataljon.pdf (book pp. 337-340):
    "Popis pripadnika Tenkovskog voda Grupe partizanskih odreda za Liku, Tenkovske čete 1. korpusa NOV i PO
    Hrvatske i Tenkovskog bataljona Glavnog štaba NOV i PO Hrvatske": 251 names, numbered, two columns,
    "65. Dokić Đuro 109. Lenac David". The scan reads ć as č at a name's end ("Bajič"); restore_diacritics
    reads them back where the other units agree.
"""
import glob
import json
import re
from collections import Counter

import pdfplumber

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser
from pdf_coords import viewer_words


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """One line per numbered entry, at its number: '§x§ 65. Dokić Đuro'."""
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(start, (end or len(pdf.pages)) + 1):
            words = viewer_words(pdf.pages[pno - 1])
            rows = {}
            for w in words:
                rows.setdefault(round(w['top'] / 3), []).append(w)
            for key in sorted(rows):
                row = sorted(rows[key], key=lambda w: w['x0'])
                cur = None
                for w in row:
                    if re.fullmatch(r'\d{1,3}\.', w['text']):
                        cur = {'page': pno, 'x': round(w['x0'], 1), 'y': round(w['top'], 1), 'words': [w['text']],
                               'x_end': w['x1']}
                        out.append(cur)
                    elif cur is not None:
                        cur['words'].append(w['text'])
                        cur['x_end'] = w['x1']
    lines = []
    for e in out:
        n = int(e['words'][0].rstrip('.'))
        name = ' '.join(e['words'][1:]).strip(' _-')
        lines.append({'page': e['page'], 'x': e['x'], 'y': e['y'], 'text': f'§x§{e["x_end"]:.1f}§ {n}. {name}'})
    lines.sort(key=lambda l: int(re.search(r'(\d+)\.', l['text']).group(1)))
    return lines


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§([\d.]+)§\s*(\d+)\.\s*(.*)$', text)
    x_end = float(m.group(1))
    name = re.sub(r'^[-–]\s*', '', m.group(3))                              # "-Babič Mario"
    if not name[:1].isupper():
        return {}                                                            # "1. korpusa NOV i" in the title
    words = re.sub(r'\s+-\s+', ' ', name).split()                            # "Vidaković Vujica - Vujo"
    last, given = (words[0], words[1] if len(words) > 1 else '') if words else ('', '')
    nick = ' '.join(words[2:])                                               # "Fatkić Zaim Mali", "Pribić Todor Tošo"
    rec = _record(last, given, '', f'zvani {nick}' if nick else '')
    rec['_x_end'] = x_end                                                    # the box ends at the name's last word
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """"Bajič" = Bajić: the scan's č for ć at a name's end, where the other units know the name only with ć."""
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    seen = Counter()
    for f in glob.glob('website/public/*soldiers.json'):
        if f.replace('\\', '/').endswith('/1-tenkovski-bataljon-soldiers.json'):
            continue
        for r in json.load(open(f, encoding='utf-8')):
            seen[r.get('last_name') or ''] += 1
    for s in soldiers:
        name = s['last_name']
        if name.endswith('ič') and seen[name[:-1] + 'ć'] >= 5 and seen[name[:-1] + 'ć'] >= 5 * seen[name]:
            s['last_name'] = name[:-1] + 'ć'
            s['full_name'] = s['full_name'].replace(name, s['last_name'], 1)
    for s in soldiers:
        s['pdf_x_end'] = s.pop('_x_end')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/1-tenkovski-bataljon.pdf',
        brigade_code=162,
        output_path='website/public/1-tenkovski-bataljon-soldiers.json',
        start_page=1,
        end_page=4,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
