"""
Parser: 4. brigada Slavonije (brigade code 129) — its leaders, a second list.

Source: Stanko Obradović, Antun Miletić, *4. NOU brigada Slavonije* (znaci.org 00001/190, the chapter 190_6.pdf, its
        pp. 13-18, book pp. 177-182)  →  website/public/pdfs/4-brigada-slavonije-rukovodioci.pdf: "Pregled rukovodilaca
        na raznim dužnostima u brigadi", made with the brigade's officers from the archive and their memories. Under each
        unit (the staff and its units, each battalion) a duty and its men, separated by semicolons, each with where he
        came from and some of his service:
    Komandant: Nikola Dolinić Pitomi, iz Seovice kod Pakraca. Borac od 1941. godine. Prvi komandant Brigade. ...
        A man is also named where he took over the post ("Zamenio ga je Franjo Šljivarić, ..."); a word after the
        surname is what he was called ("Vlado Milanović Had"); an item that names no one adds to the man before it
        ("Ivica Delač, iz Podvirja, Sl. Brod; 1. četa"). The note after the list names more men "na raznim dužnostima",
        each with his duty after the name. A man in several posts is one record with each; his box is around his name
        at his first post. The lists of the fallen and wounded are the unit's first list (IDs from 1); these get IDs
        from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/4-brigada-slavonije-rukovodioci.pdf'
UNIT = 'website/public/4-brigada-slavonije-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_190_6.pdf'   # znaci.org 00001/190_6.pdf
PAGES = range(13, 19)
TITLE = 'Pregled rukovodilaca na raznim dužnostima u 4. brigadi'
# the text layer's slips, read from the page
FIX = {'Du.ro': 'Đuro', 'Đuro.': 'Đuro', 'Duro': 'Đuro', 'Boris lav': 'Borislav', 'Stoj an': 'Stojan', 'Ni jaz': 'Nijaz',
       'Živoj in': 'Živojin', 'Gaibrijel': 'Gabrijel', 'Đofco': 'Đoko', 'Surkalo vić': 'Surkalović', 'MaJksimović': 'Maksimović',
       'Čeven.ski': 'Čevenski', 'Uroa': 'Uroš', 'Sljivarić': 'Šljivarić', 'Ceta za': 'Četa za', 'Sefovi': 'Šefovi',
       'Sifrant': 'Šifrant', 'Zunec': 'Žunec', 'Zivanović': 'Živanović', 'Zivojin': 'Živojin', 'Zivan': 'Živan',
       'Sprajser': 'Šprajser', 'Cirić': 'Ćirić', 'Ađutaint': 'Ađutant', 'Ljubiiša': 'Ljubiša', 'Suibota': 'Subota',
       'čeita': 'četa', 'Ćoralič': 'Ćoralić', 'Mamutovdć': 'Mamutović', 'Krstonožić': 'Krstonošić',
       'Slavfco': 'Slavko', 'Savio vić': 'Saviović', 'Milosevic': 'Milošević', 'Mirasavljević': 'Mirosavljević', 'Cehoslovaćke': 'Čehoslovačke', 'čedo': 'Čedo', 'Cedo': 'Čedo'}
PROSE = [('Pri formiranju brigade nije bilo funkcije zamjenik komandanta brigade. Kasnije, marta 1945. na ovu dužnost '
          'bili su postavljeni:', 'Zamjenik komandanta brigade (od marta 1945.):'),
         ('* Na raznim dužnostima u 4. brigadi bili su i sljedeći drugovi:', 'Na raznim dužnostima:'),
         ('oikoline', 'okoline'), ('rodoim', 'rodom'), ('Slamka mena', 'Slankamena'), ('Vrbov- Ijana', 'Vrbovljana'),
         ('SI. ', 'Sl. '), ('voij. ', 'voj. '), ('pomoć, referenta', 'pomoć. referenta')]
SECTIONS = [(r'^U Štabu 4\. brigade', ('Štab brigade', 'brigade')), (r'^U (\d)\. bataljonu', None),
            (r'^Inžinjerska četa', ('inžinjerska četa', 'inžinjerske čete brigade')),
            (r'^Četa za vezu', ('četa za vezu', 'čete za vezu brigade')),
            (r'^Radni vod', ('radni vod', 'radnog voda brigade'))]
WORDS = [(r'^komandanti\b', 'komandant'), (r'^komandiri\b', 'komandir'), (r'^politički komesari\b', 'politički komesar'),
         (r'^pomoćnici\b', 'pomoćnik'), (r'\bpolitičkih komesara\b', 'političkog komesara'), (r'^načelnici\b', 'načelnik'),
         (r'^ađutanti\b', 'ađutant'), (r'\boficiri\b', 'oficir'), (r'^omladinski rukovodioci\b', 'omladinski rukovodilac'),
         (r'^opunomoćenici\b', 'opunomoćenik'), (r'\bozne\b', 'OZN-e'), (r'^intendanti\b', 'intendant'),
         (r'^referenti\b', 'referent'), (r'^šefovi\b', 'šef'), (r'^vodnici\b', 'vodnik'), (r'^politički delegati?\b', 'politički delegat'),
         (r'\bčeta\b', 'čete'), (r'\bvodova\b', 'voda'), (r'^delegat\b', 'delegat'), (r'\s+u \d\. bataljonu$', ''),
         (r'\s+(brigade|bataljona)$', '')]
NAME = r"[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:-[A-ZČĆŽŠĐ][a-zčćžšđ]+)?"
SUCCESSOR = re.compile(rf"(?:Zamenio ga je|Zamjenio ga je|Njega je zamenio|kada ga je zamenio|zamjenio ga je)\s+({NAME} {NAME})")
NOT_GIVEN = {'Borac', 'Bio', 'Prvi', 'Odmah', 'Prije', 'Došao', 'Zamenio', 'Zamjenio', 'Njega', 'Bataljon', 'Kasnije', 'Pri',
             'Rat', 'Rođen', 'Umro', 'Ovaj', 'Ova', 'Na', 'Od', 'Do', 'Iz', 'Sa', 'Sl', 'Bord', 'Bos', 'Slavonskog', 'Slavonski'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in PAGES:
        w.add_page(r.pages[i - 1])
    with open(PDF, 'wb') as f:
        w.write(f)


def stream(pdf) -> tuple[str, list]:
    """The list's text in reading order, one line a row, and for each character the word it belongs to; the page
    numbers and the note on how the list was made (the first page's foot) left out."""
    text, owner = '', []
    for n, page in enumerate(pdf.pages, 1):
        words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size'])]
        foot = next((w['top'] for w in words if n == 1 and w['text'] == '*' and w['top'] > 300), None)
        for r in rows_of(words):
            if foot is not None and r[0]['top'] >= foot - 1:
                continue
            t = ' '.join(w['text'] for w in r)
            if re.fullmatch(r'[\]\d ]{2,5}', t) or t.startswith(('PREGLED RUKOVODILACA', 'BRIGADI*')):
                continue
            for i, w in enumerate(r):
                piece = w['text'] + (' ' if i < len(r) - 1 else '\n')
                text += piece
                owner += [w] * len(piece)
    return text, owner


def mend(text: str, owner: list) -> tuple[str, list]:
    """Words broken over lines joined, the scan's slips mended, keeping each character's word."""
    out, own, i = [], [], 0
    while i < len(text):
        if text[i] == '-' and text[i + 1:i + 2] == '\n' and i + 2 < len(text) and text[i + 2].islower():
            i += 2                                                       # "Bo-\nrac"
            continue
        out.append(' ' if text[i] == '\n' else text[i])
        own.append(owner[i])
        i += 1
    s = ''.join(out)
    for a, b in list(FIX.items()) + PROSE:
        while a in s:
            j = s.index(a)
            s = s[:j] + b + s[j + len(a):]
            own = own[:j] + [own[j]] * len(b) + own[j + len(a):]
    return s, own


def duty_of(label: str) -> str:
    low = re.sub(r'\s+', ' ', label).strip().rstrip(':').strip()
    low = low[:1].lower() + low[1:]
    for p, d in WORDS:
        low = re.sub(p, d, low)
    return low


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        text, owner = mend(*stream(pdf))
    # the units' headings and the duties' labels, with where each starts
    marks = []
    for m in re.finditer(r'(U Štabu 4\. brigade i prištapskim jedinicama|U \d\. bataljonu|'
                         r'Inžinjerska četa|Četa za vezu|Radni vod \(radionice\))', text):
        marks.append((m.start(), m.end(), 'head', m.group(1)))
    # a label starts with a duty's word, so a name before it can't take it in
    for m in re.finditer(r"(?<![\wčćžšđ])((?:Komand|Politi|Pomoćni|Načelni|Ađutant|Operativ|Omladinsk|Opunomoć|Obavje|Intendan|"
                         r"Referent|Šefovi|Šifrant|Propagand|Zamjenik|Vojnoobav|Vodnici|Delegat|Na raznim)[a-zčćžšđ]*"
                         r"(?: [\wčćžšđ.\-]+){0,6}?(?: \([^)]*\))?):\s", text):
        marks.append((m.start(), m.end(), 'label', m.group(1)))
    marks.sort()
    unit, of = 'Štab brigade', 'brigade'
    for k, (start, end, kind, what) in enumerate(marks):
        body_end = marks[k + 1][0] if k + 1 < len(marks) else len(text)
        if kind == 'head':
            for p, v in SECTIONS:
                m = re.match(p, what)
                if m:
                    unit, of = v if v else (f'{m.group(1)}. bataljon', f'{m.group(1)}. bataljona')
            continue
        duty = duty_of(what)
        own_duty = duty == 'na raznim dužnostima'
        body = text[end:body_end]
        add_men(body, end, owner, duty, unit, of, own_duty)


def add_men(body: str, offset: int, owner: list, duty: str, unit: str, of: str, own_duty: bool) -> None:
    """Each man of a duty's text: the names that start its items or take over the post, his words, his details."""
    starts = []
    for m in re.finditer(rf"(?:^|(?<=; )|(?<=;)|(?<=\. )|(?<=, i )|(?<= i )|(?<=, ))({NAME}(?: {NAME}){{0,2}})", body):
        words = m.group(1).split()
        after_comma = body[:m.start()].endswith(', ') and not body[:m.start()].endswith(', i ')
        if words[0] in NOT_GIVEN or (len(words) == 1 and not re.match(r'(?:^\s*|.*; |.*, i |.* i )$', body[:m.start()])):
            continue
        if after_comma and (len(words) < 2 or k8.known(words[0], 'first_name') < 20):
            continue                                                     # ", iz Podvirja, Sl. Brod": not a man
        item_start = re.match(r'(?:^\s*|.*; ?)$', body[:m.start()], re.S)    # an item's first words: a man's name
        if len(words) == 1 or item_start or k8.known(words[0], 'first_name') >= 5:
            starts.append((m.start(), m.end(), words))
    for m in SUCCESSOR.finditer(body):
        starts.append((m.start(1), m.end(1), m.group(1).split()))
    starts.sort()
    for i, (s, e, words) in enumerate(starts):
        tail_end = starts[i + 1][0] if i + 1 < len(starts) else len(body)
        detail = body[e:tail_end].strip(' ,;.*')
        detail = re.sub(r'\s*(Zamenio ga je|Zamjenio ga je|Njega je zamenio|kada ga je zamenio|zamjenio ga je)$', '', detail)
        detail = re.sub(r'(?:^|[\s,]+)i$', '', detail).strip(' ,;.*')           # "..., i Karpov": the "i" before the next
        if len(words) == 1:
            given, last, nick = '', words[0], ''
        else:
            given, last, nick = words[0], words[1], ' '.join(words[2:])
        if own_duty:                                                    # "Mato Mažur, vodnik": his own duty
            post, detail, man_unit = f"{detail or 'na raznim dužnostima'} u brigadi", '', 'brigada'
        else:
            post, man_unit = (duty if re.search(r'\bbrigade\b', duty) else f'{duty} {of}'), unit
        ws = []
        for c in range(offset + s, offset + e):
            if owner[c] not in ws:
                ws.append(owner[c])
        POSTS.append({'given': given, 'last': last, 'nick': nick, 'post': post, 'detail': detail.strip(),
                      'unit': man_unit, 'page': ws[0]['page'], 'words': ws})


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


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (k8.fold(p['last']), k8.fold(p['given']))
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        post = f"{p['post']}, {p['detail']}" if p['detail'] else p['post']
        if post not in man['_posts']:
            man['_posts'].append(post)
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            for line in rows_of(p['words']):
                man['_rects'].append([round(min(w['x0'] for w in line), 1), round(min(w['top'] for w in line), 1),
                                      round(max(w['x1'] for w in line), 1), round(max(w['bottom'] for w in line), 1)])
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=129, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
