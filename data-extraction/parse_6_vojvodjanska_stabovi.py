"""
Parser: 6. vojvođanska brigada (brigade code 83) — the staffs and company commands, a second list.

Source: Živan M. Ninković, "Šesta vojvođanska udarna brigada" (znaci.org 00001/252_8.pdf, its pp. 1-4, book pp.
        171-174, before the list of the fallen on the site)  →  website/public/pdfs/6-vojvodjanska-stabovi.pdf:
        "Spisak štabova i komandi 6. vojvođanske brigade", the members of the brigade staff and of the staffs of its
        five battalions, run on under each duty, given name first, the surname and what he was called in capitals,
    Komandanti: Žarko SAMARDZlC BACA, Petar MATIĆ DTJLE.
        then the company commands' commanders, deputies, commissars and assistant commissars, surname first:
    Komandiri: ANKOVlC Nikola, BUGARSKI Marko, ... ĐORĐEVIC Milan HAJDUK, ...
The list gives no dates. A man in several posts is one record with each; his box is around his name at each post on
his first post's page. znaci re-typeset the book from its OCR, so the page shows its slips: carons lost on capitals
("SAMARDZlC", "Zika"), l for I, surnames broken apart ("K AL AF AT IC", "I VANO VIC"); the names take back the carons
the corpus prints where only carons differ, and the pieces join where the corpus knows the whole. The fallen are the
unit's first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/6-vojvodjanska-stabovi.pdf'
UNIT = 'website/public/6-vojvodjanska-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_252_8.pdf'   # znaci.org 00001/252_8.pdf
FIRST_PAGE, LAST_PAGE = 1, 4
TITLE = 'Spisak štabova i komandi 6. vojvođanske brigade'
U = 'A-ZČĆŽŠĐ'
L = 'a-zčćžšđ'
DUTIES = {'komandanti': 'komandant', 'zamenici komandanta': 'zamenik komandanta',
          'politički komesari': 'politički komesar', 'pomoćnici političkih komesara': 'pomoćnik političkog komesara',
          'načelnici štaba': 'načelnik štaba', 'načelnici obaveštajnog odseka': 'načelnik obaveštajnog odseka',
          'načelnici ozn-e': 'načelnik OZN-e', 'načelnici artiljerije': 'načelnik artiljerije',
          'načelnici veze': 'načelnik veze', 'načelnici inžinjerije': 'načelnik inžinjerije',
          'referenti saniteta': 'referent saniteta', 'intendanti': 'intendant', 'sekretari skoj-a': 'sekretar SKOJ-a',
          'intendanti bataljona u brigadi': 'intendant bataljona',
          'referenti saniteta bataljona u brigadi': 'referent saniteta bataljona',
          'komandiri': 'komandir čete', 'zamenici komandira': 'zamenik komandira čete'}
COMPANY = {'politički komesar': 'politički komesar čete', 'pomoćnik političkog komesara': 'pomoćnik političkog komesara čete'}
# one man printed two ways ("ŠUMLJANAC", "ŠULJMANAC"), and slips the corpus can't read back
NAME_FIXES = {'ŠUMLJANAC': 'ŠULJMANAC', 'FUNTER': 'FUNTEK', 'KMEClC': 'KMEZIĆ', 'DTJLE': 'DULE', 'Tadiia': 'Tadija',
              'Vujađin': 'Vujadin', 'SUVAJDDZlC': 'SUVAJDŽIĆ', 'Košta': 'Kosta', 'Zivan': 'Živan', 'Zivko': 'Živko',
              'Zika': 'Žika', 'ZIKA': 'ŽIKA', 'Dura': 'Đura', 'CIKA': 'ČIKA', 'CAVRA': 'ČAVRA',
              'LONCARSKI': 'LONČARSKI', 'SUBlC': 'SUBIĆ'}
# a man under two forms of his given name, as the list prints him: one record
SAME = {('Pirtić', 'Pera'): 'Petar', ('Obradović', 'Vlada'): 'Vlado', ('Zarić', 'Toša'): 'Todor'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def is_caps(w: str) -> bool:
    return bool(re.fullmatch(rf'[{U}][{U}l-]*', w))


def is_title(w: str) -> bool:
    return bool(re.fullmatch(rf'[{U}][{L}]+', w))


ADDS = {('c', 'č'), ('c', 'ć'), ('s', 'š'), ('z', 'ž'), ('d', 'đ')}


def respelled(word: str, *fields: str) -> str:
    """'SAMARDZlC' -> 'Samardžić': the corpus's spelling where only carons differ. A word in capitals lost its
    carons: its final -IC is -ić, its DZ is DŽ ("GADZA") and its final -CKI -čki ("ŠTRBACKI"), where the corpus
    doesn't print it so."""
    out = []
    for part in word.split('-'):
        caps = is_caps(part)
        if caps:
            part = part.replace('l', 'I')
            part = part[:1] + part[1:].lower()
        for field in fields:
            best = k8.respell(part, field)
            if best != part and len(best) == len(part) and \
                    all(a == b or (a.lower(), b.lower()) in ADDS for a, b in zip(part, best)):
                part = best
                break
        if caps and not any(k8._spell[f].get(k8.fold(part)) and
                            k8._spell[f][k8.fold(part)].most_common(1)[0][0] == part.upper() for f in fields):
            part = re.sub(r'ic$', 'ić', part)
            part = re.sub(r'cki$', 'čki', part)
            part = part.replace('dz', 'dž').replace('Dz', 'Dž')
        out.append(re.sub(r'ič$', 'ić', part))
    return '-'.join(out)


def surname_of(caps: list[str]) -> tuple[str, list[str]]:
    """The surname's pieces ("I VANO VIC" = Ivanović) where the corpus knows them joined; the rest is the nickname."""
    for i in range(len(caps), 1, -1):
        if k8.known(''.join(caps[:i]).replace('l', 'I')):
            return ''.join(caps[:i]), caps[i:]
    return caps[0], caps[1:]


def rows_of(page) -> list[list[dict]]:
    rows: list = []
    for w in sorted(viewer_words(page), key=lambda w: (w['top'], w['x0'])):
        if rows and abs(w['top'] - rows[-1][0]['top']) <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def stream_of(pdf) -> list[dict]:
    """The list's words in reading order, with the section and duty each name stands under; a word broken at a
    line's end ("STOJANO-" / "VIC") is one."""
    out, unit, duty = [], '', ''
    for n, page in enumerate(pdf.pages, 1):
        for r in rows_of(page):
            text = ' '.join(w['text'] for w in r)
            if re.fullmatch(r'\d{3}', text) or n == 1 and r[0]['top'] < 120:
                continue
            if text.startswith('Napomena'):
                return out
            m = re.match(r'ČLANOVI ŠTABA (BRIGADE|(\d|I)\. BATALJONA)|KOMANDE [CČ]ETA', text)
            if m:
                unit = 'Štab brigade' if m.group(1) == 'BRIGADE' else \
                    f"{1 if m.group(2) == 'I' else m.group(2)}. bataljon" if m.group(2) else 'čete'
                continue
            i = next((i for i, w in enumerate(r[:6]) if w['text'].endswith(':')), None)
            if i is not None:
                key = ' '.join(w['text'] for w in r[:i + 1]).rstrip(':').lower()
                duty = DUTIES[key]
                r = r[i + 1:]
            for w in r:
                w = {**w, 'page': n, 'unit': unit, 'duty': duty, 'words': [{**w, 'page': n}]}
                if out and out[-1]['text'].endswith('-') and out[-1]['top'] < w['top'] - 3:
                    prev = out[-1]
                    out[-1] = {**prev, 'text': prev['text'][:-1] + w['text'], 'words': prev['words'] + [w]}
                else:
                    out.append(w)
    return out


def names_of(stream: list[dict]) -> list[list[dict]]:
    """The names, split at commas, full stops and "i" (the OCR's "I" too, where a name before it is whole); a given
    name after a whole given-name-first name starts the next one ("Laza MIŠKOVIC Petar PETROVIC JAPAN")."""
    names, cur = [], []

    def whole(c):
        return any(is_caps(x['text'].strip(',.')) for x in c) and any(is_title(x['text'].strip(',.')) for x in c)

    for w in stream:
        t = w['text']
        if cur and (cur[0]['duty'], cur[0]['unit']) != (w['duty'], w['unit']):
            names.append(cur)
            cur = []
        if t == 'i' or t == 'I' and whole(cur):
            names.append(cur)
            cur = []
            continue
        if cur and is_title(t) and is_title(cur[0]['text']) and whole(cur):
            names.append(cur)
            cur = []
        cur.append(w)
        if t.endswith((',', '.')):
            names.append(cur)
            cur = []
    if cur:
        names.append(cur)
    return [c for c in names if c]


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        stream = stream_of(pdf)
    for name in names_of(stream):
        words = [x['text'].strip(',.') for x in name]
        title = 'dr' if words[0] == 'dr' else ''
        words = [NAME_FIXES.get(x, x) for x in words if x != 'dr']
        text = ' '.join(words)
        for a, b in NAME_FIXES.items():
            text = text.replace(a, b) if ' ' in a else text
        words = text.split()
        if is_title(words[0]):                                               # Žarko SAMARDZlC BACA
            given, (last, nick) = words[0], surname_of(words[1:])
        else:                                                                # K AL AF AT IC Stevan, ĐORĐEVIC Milan HAJDUK
            k = next((i for i, x in enumerate(words) if is_title(x)), None)
            if k is None:
                print('  no given name:', text)
                continue
            last, given, nick = ''.join(words[:k]), words[k], words[k + 1:]
        p = name[0]
        duty = p['duty']
        if p['unit'] == 'čete':
            duty = COMPANY.get(duty, duty)
        elif p['unit'] == 'Štab brigade':
            duty = f'{duty} brigade'
        elif 'bataljona' not in duty:
            duty = f"{duty} {p['unit']}a"                                    # "komandant 1. bataljona"
        given = respelled(given, 'first_name')
        last = respelled(last, 'last_name')
        POSTS.append({'last': last, 'given': given,
                      'nick': ' '.join(respelled(x, 'first_name', 'last_name') for x in nick),
                      'title': title, 'duty': duty, 'unit': '' if p['unit'] == 'čete' or 'bataljona' in p['duty']
                      else p['unit'], 'page': p['page'], 'words': [w for x in name for w in x['words']]})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def rects_of(words: list[dict]) -> list[list[float]]:
    """A box around the name's words on each line it stands on."""
    lines: list = []
    for w in words:
        if lines and abs(lines[-1][0]['top'] - w['top']) <= 3:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [[round(min(w['x0'] for w in ln), 1), round(min(w['top'] for w in ln), 1),
             round(max(w['x1'] for w in ln), 1), round(max(w['bottom'] for w in ln), 1)] for ln in lines]


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (k8.fold(p['last']), k8.fold(SAME.get((p['last'], p['given']), p['given'])))
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'], s['_title'] = [], [], [], p['title']
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['duty'] not in man['_posts']:
            man['_posts'].append(p['duty'])
        if p['nick'] and k8.fold(p['nick']) not in [k8.fold(n) for n in man['_nicks']]:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            man['_rects'] += rects_of([w for w in p['words'] if w['page'] == p['page']])
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
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=83, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
