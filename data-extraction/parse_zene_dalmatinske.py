"""
Parser: the women fighters of the 1. dalmatinska proleterska brigada (code 36, a third book) and of the 11. dalmatinska
brigada (code 53, a second book), from the brigades' own lists of 1944-1945.

Source: *Žene Hrvatske u narodnooslobodilačkoj borbi* (znaci.org 00003/585), two documents printed as tables:
    Dokument 368, "Žene borci I. dalmatinske proleterske brigade" (the whole book's PDF pp. 101-106)
        → website/public/pdfs/zene-1-dalmatinska.pdf: number, duty and rank, surname and given name, date and place of
        birth, when she joined the NOV, whether decorated, the brigade's opinion of her ("Hrabra, disciplinovana");
    Dokument 376, "Žene borci XI. dalmatinske brigade XXVI. divizije" (PDF pp. 144-150)
        → website/public/pdfs/zene-11-dalmatinska.pdf: the same cells in another order (the name before the duty).
The cells of a row stand on two or three lines that don't line up with the name's, so each is given to the name nearest
it; the columns are found on each page by its header. The bios printed after each table ("Među ženama borcima ... bile
su i ove drugarice") are not read.
These get 0036020001 on (the 1. dalmatinska's second book, its monograph, has 0036010001-) and 0053010001 on; a woman
also in the brigade's first list is merged (scripts/find_source_duplicates.py --brigade 36, 53).
Usage: python data-extraction/parse_zene_dalmatinske.py
"""
import re

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# each column's header word (its first that the page prints) and how far left of it the column's cells may start
HEADS = {'num': (('Red.', 'Red'), 8), 'duty': (('Funkcija',), 10), 'name': (('Prezime', 'PREZIME'), 30), 'born': (('Datum',), 16),
         'joined': (('Stupila',), 12), 'decorated': (('Da', 'Odliko-', 'Odlikovana', 'odliko-'), 8),
         'remarks': (('Opšte', 'Karakteristike', 'Karakteristike:', 'Karakteristike :', 'Karakteristi'), 25)}


# names the text layer spaced out (the maiden or married name on a line of its own above): what it read -> the name
SPACED = {'ro d . M ik u l a n d ra': None, 'G a šp ar J a n j a': 'Gašpar Janja (rođena Mikulandra)',
          'R a d o n ić u d a ta': None, 'B ra c a n o vi ć N e da': 'Bracanović Neda (rođena Radonić)'}


# their rows' cells, spaced out the same way, as the page prints them
SPACED_INFO = {
    'Gašpar Janja': 'pom. polit. koman. č., ppor.; rođena 9. II. 1921. Bilice Šibenik; u NOV od 1. VII. 1943.; '
                    'rođena Mikulandra; U radu vrlo agilna i disciplinovana',
    'Bracanović Neda': 'četna boln.; rođena 13. I. 1920. Korčula; u NOV od 13. II. 1943.; rođena Radonić; '
                       'Vrlo dobra bolničarka i borac, marljiva u radu',
}


def undouble(w: str) -> str:
    """Lines whose text layer prints each letter twice ("RRuuppoottiinnee")"""
    return w[0::2] if len(w) >= 4 and len(w) % 2 == 0 and w[0::2] == w[1::2] else w


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, offsets = [], {}
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = [dict(w, text=undouble(w['text'])) for w in viewer_words(page, keep_blank_chars=False)]
            name_head = min((w for w in words if w['text'] in HEADS['name'][0]), key=lambda w: w['top'])
            band = [w for w in words if abs(w['top'] - name_head['top']) < 30]
            cols = {}
            for col, (names, slack) in HEADS.items():
                hit = [w for w in band if w['text'] in names or any(w['text'].startswith(n) for n in names if len(n) > 4)]
                if hit:
                    cols[col] = min(w['x0'] for w in hit) - slack
            # a header the text layer spaced out ("Fu nk c ija"): the column stands where it stood on the pages before,
            # as far from the names
            for col, off in offsets.items():
                cols.setdefault(col, cols['name'] + off)
            offsets.update({c: x - cols['name'] for c, x in cols.items()})
            order = sorted(cols.items(), key=lambda kv: kv[1])
            col_of = lambda x: max([c for c, x0 in order if x >= x0] or [order[0][0]], key=lambda c: cols[c])
            top = max(w['bottom'] for w in band) + 1
            body = [w for w in words if w['top'] > top and not re.fullmatch(r'\d{1,3}', w['text'])
                    or w['top'] > top and col_of(w['x0']) != 'name' and re.fullmatch(r'\d{1,3}', w['text'])]
            # a table's end: the source's line under it ("Šef personalnog otsjeka ...", a footnote)
            stop = [w['top'] for w in body if re.match(r'(?:Šef|Original)', w['text']) and w['x0'] < cols['name']]
            if stop:
                body = [w for w in body if w['top'] < min(stop) - 2]
            names = [w for w in body if col_of(w['x0']) == 'name']
            rows = []
            for w in sorted(names, key=lambda w: (round(w['top']), w['x0'])):
                if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            anchors = []
            for r in rows:
                text = ' '.join(w['text'] for w in sorted(r, key=lambda w: w['x0']))
                if text in SPACED:                           # names the text layer spaced out letter by letter
                    if SPACED[text] is None:
                        continue
                    text = SPACED[text]
                if not re.search(rf'[{U}][{L}]{{2,}}', text):
                    continue
                if anchors and r[0]['top'] - anchors[-1]['top'] < 9 and not re.search(rf'[{U}][{L}]+\s+[{U}][{L}]+', text):
                    anchors[-1]['name'] += ' ' + text            # a name on two lines ("Barišić-" / "Škerović Ljubica")
                    continue
                anchors.append({'top': r[0]['top'], 'x': r[0]['x0'], 'name': text, 'cells': {}})
            # a name: two words or more, each with a capital ("Sekretar" is a duty run into the column, "Glavnom
            # odboru AFŽ" the note under the last table)
            anchors = [a for a in anchors if re.match(rf'^(?:[ilIoO1]{{1,3}}\s+)?[{U}][{L}]', a['name'])
                       and len(a['name'].split('(')[0].split()) >= 2
                       and all(w[0].isupper() or w[0].isdigit() for w in a['name'].split('(')[0].split())]
            for w in body:
                c = col_of(w['x0'])
                if c in ('name', 'num') or not anchors:
                    continue
                a = min(anchors, key=lambda a: abs(a['top'] - w['top']))
                if abs(a['top'] - w['top']) > 16:
                    continue
                a['cells'].setdefault(c, []).append(w)
            for a in anchors:
                cell = lambda c: ' '.join(w['text'] for w in sorted(a['cells'].get(c, []), key=lambda w: (round(w['top']), w['x0'])))
                text = '§x§ ' + ' ¦ '.join([a['name']] + [cell(c) for c in ('duty', 'born', 'joined', 'decorated', 'remarks')])
                out.append({'text': text, 'x': a['x'], 'y': a['top'], 'page': pno})
    return out


def parse(text: str) -> dict:
    name, duty, born, joined, decorated, remarks = [x.strip() for x in re.sub(r'^§x§\s*', '', text).split('¦')]
    name = re.sub(r'\d\)?$|\s*\d\)', '', name)                    # "Rokov Milka2)", "Nola Krasna3": a footnote's mark
    maiden = re.search(r'\s*\((rođena [^)]+)\)', name)
    if maiden:
        name = name[:maiden.start()]
        remarks = f'{maiden.group(1)}; {remarks}'.strip('; ')
    name = re.sub(r'-\s+', '-', name)
    name = re.sub(r'^(?:[ilIoO1]{1,3}|\d+)\s+(?=[A-ZČĆŽŠĐ])', '', name)          # the row's number misread: "i", "Ioi"
    words = name.split()
    last, given = (words[0], ' '.join(words[1:])) if words else ('', '')
    sub = lambda t: re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', re.sub(r'(?<=[IVX])\s(?=[IVX])', '', t)).strip()
    parts = [sub(duty), f'rođena {sub(born)}' if born else '', f'u NOV od {sub(joined)}' if joined else '',
             'odlikovana ' + sub(decorated)[0].lower() + sub(decorated)[1:] if decorated and decorated not in ('—', '-') else '',
             sub(remarks)]
    info = '; '.join(p for p in parts if p).replace(' ,', ',')
    info = SPACED_INFO.get(f'{last} {given}', info)
    rec = _record(last, given, '', info)
    y = re.search(r'\b(19[0-3]\d|18\d\d)\b', born.replace('I924', '1924'))
    rec['birth_year'] = y.group(1) if y else ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    for pdf, code, out, first in (('zene-1-dalmatinska.pdf', 36, '1-dalmatinska-soldiers.json', 20001),
                                  ('zene-11-dalmatinska.pdf', 53, '11-dalmatinska-soldiers.json', 10001)):
        run_parser(
            pdf_path=f'website/public/pdfs/{pdf}',
            brigade_code=code,
            output_path=f'website/public/{out}',
            start_page=1,
            end_page=None,
            layout='single',
            script='latin',
            entry_start_re=re.compile(r'^§x§'),
            parse_entry_fn=parse,
            extract_fn=extract,
            post_fn=k8.post,
            id_start=first,
            keep_other_sources=True,
        )
