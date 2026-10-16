"""
Parser: Istrski odred (brigade code 67) — its command, a second list.

Source: Maks Zadnik, "Istrski odred" (Knjižnica NOV in POS 27/1, 1975; znaci.org 00003/811.pdf, PDF pp. 821-826,
        book pp. 821-826, before its roster on the site)  →  website/public/pdfs/istrski-odred-kader.pdf:
        "Poveljniški kader", the odred's commanders, political commissars, their deputies and chiefs of staff, those of
        its three battalions, of the 4. bataljon of the 9. and 18. brigade it became in September 1944, and of that
        battalion's four companies, a name a line with the days held, as the Cankarjeva's (parse_cankarjeva_kader):
    Komandanti
    Franc Korošec-Miha          od 27. 11. 1943 do 12. 12.1 943
A man in several posts is one record with each; a post held for a while ("(začasno)") says so. The deputy commander
"Iztok*", whose real name the author could not learn (the page's footnote), is a record under that name, as the
Kokrški odred's Iztok is. znaci
re-typeset the book from its OCR, so the page shows its slips ("Karei Vene", "Vdčič"); the names are read back from
the odred's roster (`NAMES`). The roster and the fallen are the unit's first list (IDs from 1); these get IDs from
10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from parse_cankarjeva_kader import dates_of, rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/istrski-odred-kader.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_811.pdf'   # znaci.org 00003/811.pdf
FIRST_PAGE, LAST_PAGE = 821, 826
TITLE = 'Poveljniški kader Istrskega odreda'
DUTY = re.compile(r'^(Komandant|Komandanti|Komandirj ?[ia]|Politični komisarji|Namestniki|Načelniki)\b')
B4 = '4. bataljon 9. in 18. brigade'
# the OCR's slips, read back from the odred's roster and the lines that print the name right
NAMES = {'Klemenćič': 'Klemenčič', 'Vdčič': 'Vičič', 'Srećko': 'Srečko', 'Karei ': 'Karel ', 'Kocjanoič': 'Kocjančič',
         'jože Žnddaršič': 'Jože Žnidaršič', 'Dmdič': 'Drndić', 'Piane Zorc': 'Franc Zorc',
         'Peeič': 'Pecič'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def read_posts(pdf_path: str) -> None:
    unit, duty, note = 'Štab odreda', '', False
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for r in rows_of(viewer_words(page)):
                text = ' '.join(w['text'] for w in r)
                if note or text.startswith('('):                              # a note on a company, to its bracket
                    note = not re.search(r'\)\.?$', text.rstrip())                # "... štab IX. korpusa)."
                    continue
                if re.fullmatch(r'\d{3}|POVELJNIŠKI KADR?[EI]R?( CET)?|4\. bataljona 9\. in 18\. brigade', text) or text.startswith('* '):
                    if text.startswith('POVELJNIŠKI KADER') and n > 1:
                        unit = B4
                    continue
                m = re.fullmatch(r'([123])\. BATALJON', text)
                if m:
                    unit = f'{m.group(1)}. bataljon'
                    continue
                m = re.fullmatch(r'([1-4])\. [CČ]ETA', text)
                if m:
                    unit = f'{B4}, {m.group(1)}. četa'
                    continue
                if DUTY.match(text) and ' od ' not in f' {text} ':
                    duty = re.sub(r'Komandirj ?([ia])', r'Komandirj\1', text)
                    continue
                m = re.search(r'\bod\b', text)
                od_x = next(w['x0'] for w in r if w['text'] == 'od')
                words = [w for w in r if w['x0'] < od_x]
                name = ' '.join(w['text'] for w in words)
                POSTS.append({'unit': unit, 'duty': duty, 'name': name, 'dates': dates_of(text[m.start():]),
                              'page': n, 'words': words})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        name = p['name']
        for a, b in NAMES.items():
            name = name.replace(a, b)
        temporary = '(začasno)' in name
        name = name.replace('(začasno)', '').replace('*', '').strip()
        words = name.split()
        if len(words) == 1:                                                  # "Iztok*": his real name unknown
            p.update(last=words[0], given='', nick=words[0], unknown=True)
        else:
            last, _, nick = ' '.join(words[1:]).partition('-')
            p.update(last=last, given=words[0], nick=nick, unknown=False)
        frm, to = p['dates']
        head = 'Štab Istrskega odreda' if p['unit'] == 'Štab odreda' else p['unit']
        p['text'] = f"{head}, {p['duty'].lower()}, od {frm} do {to}" + (' (začasno)' if temporary else '')
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (p['last'], p['given'], p['nick'] if p['unknown'] else '')
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        man['_posts'].append(p['text'])
        if p['nick'] and p['nick'] not in man['_nicks'] and not p['unknown']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        unknown = '' if s['first_name'] else '(pravo ime neugotovljeno); '
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{unknown}{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=67, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/istrski-odred-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
