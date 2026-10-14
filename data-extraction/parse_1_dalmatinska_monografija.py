"""
Parser: 1. dalmatinska proleterska brigada (brigade code 36), second book: the monograph's lists, with a scan.

Source: the brigade's monograph (znaci.org 00001/108, the chapter 108_21.pdf, its PDF pp. 1-109) →
website/public/pdfs/1-dalmatinska-monografija.pdf. Three of its lists:
    "Pregled komandira i komesara četa koji su prošli kroz 1. dalmatinsku brigadu" (PDF pp. 1-4): by battalion,
        two columns, the company commanders on the left and the political commissars on the right, a name a line
        in capitals ("ANDRIJIC KUZMA    BAČINIĆ ANTE"), a nickname or a second surname at times ("BORIĆ JURE
        (JULIO)", "SOLIC — STRIČEVIĆ NIKOLA");
    "Narodni heroji Prve dalmatinske brigade" (pp. 10-40): each hero's biography under his name ("ANTUNOVIĆ Jure
        ILIJA, rođen je 20. juna 1919. ..."), with photo captions in between ("Ilija Antunović");
    "Spisak boraca Prve dalmatinske proleterske NOU brigade poginulih u toku narodnooslobodilačkog rata" (pp. 41-109),
        numbered 1-2165: the same list the site has from znaci.org's web page (parse_1_dalmatinska.py), here with
        its scan ("653. Glučina D. Ivo, rođen 1921. godine u Drašnici — Makarska, borac III bat., ...").
The revolutionaries the battalions were named after (pp. 5-9) were not the brigade's men and are not read.
These get 0036010001 on; a fallen fighter's entry is merged into his record from the web page, and a commander or a
hero into his fallen record where he fell (scripts/find_source_duplicates.py --brigade 36), so the records gain the
page of the book.
Usage: python data-extraction/parse_1_dalmatinska_monografija.py
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
COMMANDERS, HEROES, FALLEN = range(1, 5), range(10, 41), range(41, 110)
SPLIT = 200                                                   # the commanders' columns: < commanders, >= commissars


def rows(page) -> list[list[dict]]:
    out = []
    for w in sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (round(w['top']), w['x0'])):
        if out and abs(out[-1][0]['top'] - w['top']) <= 3:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in out]


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    section = ''
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for r in rows(page):
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'[\d\W]{1,5}', text):
                    continue                                   # page numbers
                if pno in COMMANDERS:
                    if re.search(r'\bBATALJON\b|\bČETA\b|\bCETA\b|DIVIZION|BATERIJ', text) and not text.startswith('Komandir '):
                        section = re.sub(r'\s*[»«].*$', '', text).strip().title().replace('. Bataljon', '. bataljon')
                        continue
                    if text.startswith(('PREGLED', 'KOMANDIRA I', '1. DALMATINSKU', 'Komandiri', '(u sastavu')):
                        continue
                    m = re.match(r'^Komandir inžinjerijske čete brigade\s+(.+)$', text)
                    if m:
                        lines.append({'text': f'§c§Komandir inžinjerijske čete brigade§ {m.group(1)}', 'x': r[-2]['x0'],
                                      'y': r[0]['top'], 'page': pno})
                        continue
                    for side, words in (('Komandir čete', [w for w in r if w['x0'] < SPLIT]),
                                        ('Politički komesar čete', [w for w in r if w['x0'] >= SPLIT])):
                        if words:
                            name = ' '.join(w['text'] for w in words)
                            lines.append({'text': f'§c§{side}, {section}§ {name}', 'x': words[0]['x0'],
                                          'y': words[0]['top'], 'page': pno})
                elif pno in HEROES:
                    if text.startswith('NARODNI HEROJI'):
                        continue
                    if re.fullmatch(rf'[{U}][{L}]+ [{U}][{L}]+', text):
                        continue                               # a photo's caption: "Ilija Antunović"
                    if re.match(rf'^[{U}][{U}lI1\-]{{2,}}\s+[{U}][{L}]+\s+[{U}][{U}lI1\-]+,', text):
                        text = '§h§ ' + text
                    lines.append({'text': text, 'x': r[0]['x0'], 'y': r[0]['top'], 'page': pno})
                elif pno in FALLEN:
                    if re.match(r'^(?:S P I S|BORACA PRVE|U TOKU NARODNO)', text):
                        continue
                    if re.match(rf'^\d{{1,4}}\.\s+[{U}]', text):
                        text = '§f§ ' + text
                    lines.append({'text': text, 'x': r[0]['x0'], 'y': r[0]['top'], 'page': pno})
    return lines


def parse(text: str) -> dict:
    m = re.match(r'^§c§([^§]*)§\s*(.*)$', text)
    if m:                                                      # a commander or commissar: a name in capitals
        role, name = m.group(1), m.group(2)
        nick = re.search(r'\(([^)]+)\)', name)
        name = re.sub(r'\s*\([^)]*\)', '', name)
        name = re.sub(r'\s*[—–-]\s*', '-', name)               # "SOLIC — STRIČEVIĆ"
        words = [k8.caps_word(w) for w in name.split()]
        last, given = (words[0] if words else ''), (words[1] if len(words) > 1 else '')
        extra = words[2:]
        info = f'{role}.'
        nicks = [n.title() for n in ([nick.group(1)] if nick else []) + extra]
        if nicks:
            info = f"zvani {', '.join(nicks)}; {info}"
        return _record(last.title(), given.title(), '', info)
    if text.startswith('§h§'):                                 # a hero: "ANTUNOVlC Jure ILIJA, rođen je ..."
        rec = k8.parse_entry(text[3:].strip())
        rec.pop('unit_detail', None)
        return rec
    m = re.match(r'^§f§\s*(\d{1,4})\.\s*(.*)$', text)
    if m:                                                      # "653. Glučina D. Ivo, rođen 1921. godine u ..."
        # the name ends at the first comma, or at a full stop before "rođen" ("Anterić B. Jozo. rođen 1919. ...")
        parts = re.split(r',|\.?\s+(?=ro[dđ]en[a]?\b|star\s+\d)', m.group(2), 1)
        head, info = parts[0], (parts[1] if len(parts) > 1 else '')
        nick = re.search(r'[»"„]([^«"“]+)[«"“]', head)            # "Alaber Antun »Pubo«"
        head = re.sub(r'\s*[»"„][^«"“]*[«"“]?', '', head).replace('.', '. ').replace(' .', ' ')
        words = [w for w in head.split() if w not in ('.',)]
        initial = next((w for w in words[1:] if re.fullmatch(rf'[{U}]\.?', w)), '')   # "D." and "L"
        rest = [w for w in words[1:] if w != initial]
        if initial and not initial.endswith('.'):
            initial += '.'
        info = info.strip()
        if nick:
            info = f'zvani {nick.group(1).strip()}; {info}'
        rec = _record(words[0] if words else '', ' '.join(rest), initial, info)
        y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
        rec['birth_year'] = y.group(1) if y else ''
        return rec
    return {}


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/1-dalmatinska-monografija.pdf',
        brigade_code=36,
        output_path='website/public/1-dalmatinska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§[chf]§'),
        parse_entry_fn=parse,
        extract_fn=extract,
        post_fn=k8.post,
        id_start=10001,
        keep_other_sources=True,
    )
