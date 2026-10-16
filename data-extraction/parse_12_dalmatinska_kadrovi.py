"""
Parser: 12. dalmatinska brigada (1. otočka, brigade code 50) — its staffs, a second list in the same PDF.

Source: Nikola Anić, the brigade's monograph (znaci.org 00001/80_7.pdf, on the site as 12-dalmatinska.pdf; its
        Prilozi, PDF pp. 22-25, book pp. 339-342): "Pregled rukovodećih kadrova Štaba 12. dalmatinske NOU brigade i
        štabova bataljona od 15. rujna 1943. do 15. svibnja 1945. godine", the brigade staff and the staffs of its
        four battalions, numbered under each duty, given name first, the surname in capitals, with the days:
    Komandant:
    1. Jure FRANICEVIC-Pločar od 15. IX do 11. X 1943.
A word joined to the given name or the surname by a hyphen is what he was called ("Josip-Bepo", "ILIĆ-Šuro"). A man
in several posts is one record with each; his box is around his name at each post on his first post's page. The OCR
lost carons on capitals ("FRANICEVIC", "Zivko"); the names take them back where the corpus prints them so
(`parse_6_vojvodjanska_stabovi.respelled`). The fallen are the unit's first list (IDs from 1); these get IDs from
10001.
"""
import re
import sys

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_6_vojvodjanska_stabovi import is_caps, respelled, rows_of

PDF = 'website/public/pdfs/12-dalmatinska.pdf'
UNIT = 'website/public/12-dalmatinska-soldiers.json'
FIRST_PAGE, LAST_PAGE = 22, 25
TITLE = 'Pregled rukovodećih kadrova štabova 12. dalmatinske brigade'
SECTIONS = [(r'^A\. Stab', 'Štab brigade', 'brigade'),
            (r'^I\. Sastav', '1. bataljon', '1. (bračkog) bataljona »Josip Bodlović«'),
            (r'^II\. Sastav', '2. bataljon', '2. (hvarskog) bataljona »Matija Ivanić«'),
            (r'^III\. Sastav', '3. bataljon', '3. (viškog) bataljona'),
            (r'^IV\. Sastav', '4. bataljon', '4. bataljona')]
# the two posts of the dressing station, printed after the medical officers without a number
OWN = re.compile(r'^(Upravnica brigadnog previjališta|Politički komesar brigadnog previjališta) (.+?)\.?$')
NAME_FIXES = {'Zeldmir': 'Želimir', 'Zelimir': 'Želimir', 'Zivko': 'Živko', 'Zivan': 'Živan', 'Sime': 'Šime',
              'Sibe': 'Šibe', 'ZlZlĆ': 'ŽIŽIĆ', 'Suro': 'Šuro', 'STAMBUK': 'ŠTAMBUK', 'BLAZEVIC': 'BLAŽEVIĆ',
              'BIOClNA': 'BIOČINA'}
# one man under two forms of his given name: the 3. bataljon's komandant to 13. III 1945, the brigade's deputy from then
SAME = {('Vukasović', 'Pero'): 'Petar'}
DATE_FIXES = [(r'zamjenik«', 'zamjenik'), (r'bio- je', 'bio je'), (r'(\w)- (\w)', r'\1\2'), (r'\s+', ' ')]
POSTS: list = []


def duty_of(text: str, section: str) -> str:
    """'Zamjenik komandanta:' under the 1. bataljon -> 'zamjenik komandanta 1. (bračkog) bataljona »Josip Bodlović«'."""
    duty = text.rstrip(': ').replace(' :', '').replace('Štaba', 'štaba')
    duty = duty[:1].lower() + duty[1:]
    duty = re.sub(r' (brigade|bataljona|u bataljonu)$', '', duty)
    duty = duty.replace('političko-prosvjetni odsjek brigade (šef odsjeka)', 'šef političko-prosvjetnog odsjeka')
    return f'{duty} {section}'


def read_posts(pdf_path: str, start: int, end: int) -> None:
    unit = section = duty = ''
    current = None
    with pdfplumber.open(pdf_path) as pdf:
        for n in range(start, end + 1):
            rows = rows_of(pdf.pages[n - 1])
            starts = [round(r[0]['x0']) for r in rows if re.fullmatch(r'\d\.?', r[0]['text']) and len(r) > 2]
            ex = min(starts)
            for r in rows:
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'\d{3}', text) or n == 22 and (r[0]['top'] < 280 or r[0]['top'] > 650):
                    continue                                                 # page numbers, the title, its footnote
                sec = next((s for s in SECTIONS if re.match(s[0], text)), None)
                if sec:
                    unit, section = sec[1], sec[2]
                    current = None
                    continue
                if text.startswith('B. Rukovodeći'):
                    continue
                m = OWN.match(text)
                if m:
                    POSTS.append({'unit': unit, 'duty': m.group(1)[:1].lower() + m.group(1)[1:], 'page': n,
                                  'words': r[len(m.group(1).split()):], 'name': m.group(2), 'when': ''})
                    current = None
                    continue
                if re.fullmatch(r'\d\.?', r[0]['text']) and len(r) > 2 and abs(r[0]['x0'] - ex) < 6:
                    POSTS.append({'unit': unit, 'duty': duty, 'page': n, 'words': r[1:],
                                  'text': ' '.join(w['text'] for w in r[1:])})
                    current = POSTS[-1]
                    continue
                if r[0]['x0'] < ex - 8 and text.rstrip().endswith(':'):          # "Zamjenik komandanta:"
                    duty = duty_of(text, section)
                    current = None
                    continue
                if r[0]['x0'] > ex + 8 and current is not None:                 # a wrapped line
                    current['text'] += ' ' + text
                    continue
                current = None                                                  # "Napomena: Poslije Bepa ..."


def name_of(p: dict) -> None:
    """'Josip-Bepo MARINKOVIĆ od 15. IX ...' -> Marinković Josip, zvani Bepo, and the days."""
    if 'name' in p:
        words, when = p['name'].split(), ''
    else:
        words = p['text'].split()
        k = next((i for i, w in enumerate(words) if i and (w[:1].islower() or w.startswith('('))), len(words))
        words, when = words[:k], ' '.join(words[k:])
    title = ''
    if words[0] == 'Dr':
        title, words = 'dr', words[1:]
    words = [NAME_FIXES.get(w, w) for w in words]
    given, _, nick = words[0].partition('-')
    last = ' '.join(words[1:])
    if '-' in last:                                                          # "FRANICEVIC-Pločar", "ILIĆ-Šuro"
        a, _, b = last.partition('-')
        if not is_caps(b):
            last, nick = a, b
    for a, b in DATE_FIXES:
        when = re.sub(a, b, when).strip()
    p.update(given=respelled(NAME_FIXES.get(given, given), 'first_name'), last=respelled(last, 'last_name'),
             nick=NAME_FIXES.get(nick, nick), title=title, when=when.rstrip('.'))
    p['post'] = f"{p['duty']}{' ' if p['when'][:1] == '(' else ', '}{p['when']}" if p['when'] else p['duty']


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path, start_page, end_page)
    for p in POSTS:
        name_of(p)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def name_words(p: dict) -> list[dict]:
    out = []
    for w in p['words']:
        if out and (w['text'][:1].islower() or w['text'].startswith('(')):
            break
        out.append(w)
    return out


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (k8.fold(p['last']), k8.fold(SAME.get((p['last'], p['given']), p['given'])))   # "Kažimir", "Kazimir"
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'], s['_title'] = [], [], [], p['title']
            s['unit_detail'] = p['unit']
            out.append(s)
        man['_posts'].append(p['post'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = name_words(p)
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = '; '.join(([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}"
        for k in ('_post', '_posts', '_nicks', '_rects', '_title'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run_parser(pdf_path=PDF, brigade_code=50, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               start_page=FIRST_PAGE, end_page=LAST_PAGE, id_start=10001, keep_other_sources=True)
