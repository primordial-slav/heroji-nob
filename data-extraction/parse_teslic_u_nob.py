"""
Advan Hozić, *Teslić u NOB* (Skupština opštine Teslić, 1985; znaci.org 00003/1026, a scan with no text layer): its
two lists of the municipality's people in the war, books across units. Their entries are added to the records of the
soldiers they describe (scripts/match_references.py), the rest go to Ostali borci.

The site's PDF website/public/pdfs/teslic-u-nob-borci.pdf is the scan's PDF pages 142-164, each spread split into its
two book pages (book pp. 234-279). The text is Tesseract's (data-extraction/ocr_scan.py, `--lang hrv`), saved in
data-extraction/ocr/teslic-u-nob-borci.json; this parser reads only that file.

- "Spisak boraca narodnooslobodilačkog rata opštine Teslić" (book pp. 234-267, 912 entries, numbered, each entry
  hanging): "1. ABDUZAIMOVIĆ Alibega ALJO, r. 1925, Teslić, Musliman, trgovac, u NOVJ od 10. 10. 1944;". The list
  counts with the fighters the odbornici and the NOP's collaborators ("odbornik NOO-a", "aktivni saradnik NOP-a"):
  only the fighters go in, by the rule of `parse_mosorski_odred_2.fighter` (borac, a military duty, an army unit, "u
  NOVJ od"), and "u JA od" (the Yugoslav Army, from March 1945). IDs 9082xxxxxx, by the book's number.
- "Spisak poginulih i umrlih boraca narodnooslobodilačkog rata opštine Teslić" (pp. 269-279, 193 entries): "1.
  AHMETAŠEVIĆ Mušana SAFET, r. 1927, Teslić, Musliman, đak borac od 9. 8. 1943, poginuo kao komesar čete 5. kozaračke
  brigade 24. 3. 1945. u Maloj Plečici — Bjelovar, član KPJ;". It counts collaborators of the NOP killed in camps as
  well: the same rule. IDs 9083xxxxxx. Its list of the civilian victims of terror after it (p. 280 on) is not read.

Each entry names the site's units its text names (`units`), and has the box of its lines on its first page.
Output: data-extraction/znaci/teslic-u-nob-borci-entries.json, teslic-u-nob-poginuli-entries.json.
Usage: python data-extraction/parse_teslic_u_nob.py [--dropped] [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import ocr_scan  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
from _ocr_readback import LAT, Corpus, title  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402

PDF = 'teslic-u-nob-borci.pdf'
LISTS = [  # (pages of the site's PDF, prefix, output, title)
    (range(1, 35), '9082', HERE / 'znaci' / 'teslic-u-nob-borci-entries.json',
     'Spisak boraca narodnooslobodilačkog rata opštine Teslić'),
    (range(36, 47), '9083', HERE / 'znaci' / 'teslic-u-nob-poginuli-entries.json',
     'Spisak poginulih i umrlih boraca narodnooslobodilačkog rata opštine Teslić')]
ABBR = {'NOVJ', 'NOVI', 'NOP', 'NOO', 'KPJ', 'SKOJ', 'SBUB', 'AFŽ', 'USAOJ', 'JNA', 'SSSR', 'NOB', 'NOR'}
START = re.compile(r'^(\d{1,3})\s*[.,:;]$')
ETHNIC = re.compile(r'^(?:Musliman\w*|Srb\w*|Srpkinja|Hrvat\w*|Slovenac|Slovenka|Crnogor\w*|Jevrej\w*|Čeh\w*|Rus\w*|'
                    r'Ukrajin\w*|Poljak\w*|Polj\w*|Nijem\w*|Mađar\w*|Talijan\w*|Ital\w*|Slovak\w*|Rusin\w*|Rom\w*|Cigan\w*)$')
# "u NOVJ od", "u JA od" (the Yugoslav Army, from March 1945), as the OCR reads them too ("u NOVJ ed", "u NOV: od",
# "i JE od", "u BIOVJ od", "u NOVIJI od", "zemNOVJ od"); a brigade, odred or battalion named with its number
# ("vodič 18. SBUB", "zastavnik I. proleterske brigade"); "ustanički borac" (the OCR's "bora?"), "partizanski pilot"
JA = re.compile(r'(?:\bu|\bi|[:,]|zem)\s*(?:NOV[J1I:O]?\w*|BIOVJ|JA|JE)(?=[\s:;,.]|$)|\bu\s+Jugoslovensk\w*\s+armij'
                r'|\b(?:\d{1,2}|[IVX]{1,4})\.\s*(?:\w+\s+){0,2}(?:brigad\w*|odred\w*|bataljon\w*|divizij\w*|SBUB)\b'
                r'|\bustaničk\w*\s+bor|\bpartizansk\w*\s+pilot')
UNITS = [(r'\b5\.\s*kozarač', 12), (r'\b11\.\s*(?:krajišk|kozarač)', 107), (r'\b3\.\s*krajišk\w*\s+prol', 10),
         (r'\b1\.\s*krajišk\w*\s+prol', 123), (r'\b2\.\s*krajišk\w*\s+(?:prol\w*\s+)?brigad', 24),
         (r'\b4\.\s*krajišk\w*\s+(?:prol\w*\s+)?brigad', 11), (r'\b6\.\s*krajišk\w*\s+(?:prol\w*\s+)?brigad', 13),
         (r'\b7\.\s*krajišk\w*\s+(?:prol\w*\s+)?brigad', 48), (r'\b8\.\s*krajišk\w*\s+(?:prol\w*\s+)?brigad', 14),
         (r'\b12\.\s*krajišk\w*\s+(?:prol\w*\s+)?brigad', 54), (r'\b13\.\s*krajišk', 124),
         (r'\b1\.\s*prol\w*\s+brigad', 1), (r'\b2\.\s*prol\w*\s+brigad', 39), (r'\b13\.\s*(?:hrvatsk\w*\s+)?prol', 6),
         (r'\b10\.\s*hercegovač', 43), (r'\b5\.\s*crnogorsk', 41), (r'\b17\.\s*majevič', 29), (r'\b15\.\s*majevič', 49),
         (r'\b18\.\s*hrvatsk', 52), (r'\b14\.\s*(?:SBUB|srednjobosansk)', 56), (r'\b21\.\s*tuzlansk', 32),
         (r'\b53\.\s*divizij', 33), (r'\b1\.\s*vojvođansk', 9), (r'\b7\.\s*vojvođansk', 22), (r'\b8\.\s*vojvođansk', 78),
         (r'\b6\.\s*(?:istočnobosansk|proleterske istočnobosansk)', 42)]
MONTHS = 'januar|februar|mart|april|maj|jun|jul|avgust|august|septemb|oktob|novemb|decemb|proljeć|ljet|jesen|zim'
DEATH = re.compile(r'\b(poginu[oa]|umr(?:o|la)|ubijen[a]?|strijeljan[a]?|streljan[a]?|nesta[oa]|podlegao|podlegla|'
                   r'obješen[a]?|spaljen[a]?)\b(.{0,90}?)\b(19[4-5]\d)\b', re.I)
CORPUS: Corpus | None = None


def lines_of(ocr: dict, pages: range) -> list[tuple[int, dict]]:
    out = []
    for pno in pages:
        for ln in ocr['pages'][str(pno)]['lines']:
            text = ' '.join(w[4] for w in ln['words'])
            # the page number (not an entry's last line, "1945;"), specks, the lists' titles
            if (re.fullmatch(r'\W*\d{3}\W*', text) and ln['top'] > 560) or re.fullmatch(r'\W{1,3}', text) or re.search(r'S\s*P\s*I\s*S\s*A\s*K|NARODNOOSLOBODILA\w*\s+RATA|'
                                                                r'OPŠTINE\s+TESLI|POGINULIH\s+I\s+UMRLIH', text):
                continue
            out.append((pno, ln))
    return out


def read(pages: range) -> list[dict]:
    """Entries: a line that starts with the entry's number left of the hanging lines starts one"""
    ocr = ocr_scan.load(PDF)
    entries: list[dict] = []
    lines = lines_of(ocr, pages)
    margin = {}                                 # each page's margin: where its entries' first lines start
    for pno in pages:
        xs = sorted(round(ln['x0']) for p, ln in lines if p == pno)
        if xs:
            common = Counter(xs)
            low = min((x for x in xs if sum(common[x + d] for d in (-2, -1, 0, 1, 2)) >= 3), default=xs[0])
            start = Counter(x for x in xs if low <= x <= low + 12).most_common(1)[0][0]   # (not a speck further left)
            cont = Counter(x for x in xs if x > start + 10).most_common(1)
            margin[pno] = (start + cont[0][0]) / 2 if cont else start + 9     # halfway to the hanging lines
    for pno, ln in lines:
        words = ln['words']
        m = START.match(words[0][4]) if words else None
        # the numbers stand left of the hanging lines: a line that starts at the margin starts an entry, whatever the
        # OCR made of its number ("l.", "36.ALIĆ")
        # (a speck at the margin before a hanging line is no start: a start has a name in capitals in its first words)
        at_margin = ln['x0'] < margin[pno] and any(re.fullmatch(r'[A-ZČĆŽŠĐ]{3,}[,.]?', w[4]) and
                                                     w[4].strip(',.') not in ABBR for w in words[:4])
        if at_margin and ((m and len(words) > 1 and re.match(r'[A-ZČĆŽŠĐ]', words[1][4])) or (entries and len(words) > 2)):
            glued = re.match(r'^(\d{1,3})[.,]([A-ZČĆŽŠĐ].*)$', words[0][4])
            if m:
                rest = list(words[1:])
            elif glued:
                rest = [words[0][:4] + [glued.group(2)] + words[0][5:]] + list(words[1:])
            elif re.search(r'\d', words[0][4]) or len(words[0][4]) <= 2:
                rest = list(words[1:])              # a number the OCR garbled
            else:
                rest = list(words)                  # no number at all: the line is the name's
            entries.append({'no': 0, 'page': pno, 'lines': [(pno, ln)], 'words': rest})
        elif entries:
            entries[-1]['lines'].append((pno, ln))
            entries[-1]['words'] += words
    # the book's number: the list has no gaps, and the OCR misreads many ("3." for 5.)
    for i, e in enumerate(entries, 1):
        e['no'] = i
    return entries


def text_of(words: list[list]) -> str:
    out = []
    for w in words:
        t = w[4]
        if re.fullmatch(r'[|~·•“"]+', t):
            continue
        core = re.sub(r'^\W+|\W+$', '', t)
        if w[5] < 80 and len(core) > 3 and core.isalpha() and core.islower():
            t = t.replace(core, CORPUS.word(core, opts=LAT, alts=(w[6],) if len(w) > 6 else ()))
        out.append(t)
    text = ' '.join(out)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)                              # "trgo- / vac"
    text = re.sub(r'\bNOV[I1l]\b', 'NOVJ', text)                                # the OCR's "NOVI"
    text = re.sub(r'\b(\d{1,2})[,.]\s*(\d{1,2})[,.]\s*(1[89]\d\d)', r'\1. \2. \3', text)   # "10, 10, 1944"
    text = re.sub(r'\b1[08]([0-4]\d)\b', r'19\1', text)                         # "1843", "1044" for 1943, 1944
    text = re.sub(r'\b(\d{1,2}),\s+(?=[a-zčćžšđ])', r'\1. ', text)             # "3, krajiške", "4, krajiškog"
    text = re.sub(r'(?:\s+[a-zA-Z|]{1,2}[.,]?)+\s*$', '', text)               # specks after the entry: "; i i"
    return re.sub(r'\s+([.,;:])', r'\1', re.sub(r'\s+', ' ', text)).strip().rstrip(';').strip()


def head_of(text: str) -> tuple[str, str, str, str, str, str]:
    """SURNAME Father GIVEN [ud. Married] [— Nick], r. ...: the name's parts, a note (the married name), the rest"""
    m = re.match(r'^(.*?)[,.]\s*(?=[rR][.,]+\s*\d|ro[đd]en|r\s\d)', text)
    if not m:
        m = re.match(r'^(.*?)[,.]\s*(?=v?r?[.,]\s*1[89]\d\d)', text)              # the OCR's "vr." and "v." for r.
    head, rest = (m.group(1), text[m.end():]) if m else (text.split(',')[0], text[len(text.split(',')[0]) + 1:].strip())
    rest = re.sub(r'^(?:R|vr|v)(?=[.,]\s*1[89]\d\d)', 'r', rest)
    note = ''
    married = re.search(r'[,.]?\s*\b[uU]d[.,]\s*(.+)$', head)                 # "NAFA ud. Predojević": married
    if married:
        note = 'ud. ' + married.group(1).strip(' ,.')
        head = head[:married.start()]
    nick = ''
    if '—' in head or ' - ' in head:
        head, nick = re.split(r'\s*-?(?:—|\s-\s)\s*', head, maxsplit=1)
        nick = nick.strip(' »«"„“”-')
    words = [w.strip('.,') for w in head.split() if re.search(r'\w', w)]
    fi = next((i for i, w in enumerate(words) if i > 0 and not w.isupper()), None)
    if fi is not None:
        last, father, given = ' '.join(words[:fi]), words[fi], ' '.join(words[fi + 1:])
    else:
        last, father, given = words[0] if words else '', '', ' '.join(words[1:])
    c = CORPUS
    last = '-'.join(title(c.best(title(p), c.surnames, LAT)) for p in last.replace(' ', '-').split('-') if p)
    father = title(c.best(father, c.fathers, LAT)) if father and not father.endswith('.') else father
    given = ' '.join(title(c.best(title(g), c.givens, LAT)) for g in given.split())
    return last, father, given, nick.strip(' ,'), note, rest


def one_spelling(recs: list[dict]) -> None:
    """A surname the site doesn't know, printed (or read) with and without its carons ("Iriškić", "Iriskić"): the
    book's commonest spelling, the one with more carons where they tie"""
    from _ocr_readback import fold
    by: dict[str, Counter] = {}
    for r in recs:
        if not CORPUS.surnames[fold(r['last_name'])] or True:
            by.setdefault(fold(r['last_name']), Counter())[r['last_name']] += 1
    for r in recs:
        forms = by.get(fold(r['last_name']))
        if forms and len(forms) > 1:
            best = max(forms, key=lambda f: (forms[f], sum(ch in 'čćžšđČĆŽŠĐ' for ch in f)))
            if r['last_name'] != best and sum(ch in 'čćžšđČĆŽŠĐ' for ch in best) >= sum(ch in 'čćžšđČĆŽŠĐ' for ch in r['last_name']):
                r['last_name'] = best
                r['name'] = ' '.join(x for x in (r['last_name'], r['fathers_name'], r['first_name'], r['nick']) if x)


def born_in(rest: str) -> tuple[str, str]:
    m = re.match(r'^r[.,]*\s*(1[89]\d\d)\.?,?\s*(.*)$', rest)
    if not m:
        return '', ''
    places = []
    for part in m.group(2).split(','):
        part = part.strip()
        if not part or ETHNIC.match(part) or re.match(r'(?:radi[ol]a?|živi[ol]a?|stanovao|nastanjen)\b', part) or \
                len(places) == 2 or not part[:1].isupper():
            break
        places.append(part)
    return m.group(1), ', '.join(places)


# names the OCR garbled past the rules, read from the page images: (page, the entry's top) -> the fields to set
SCAN = {(r['page'], r['y']): r for r in json.loads((HERE / 'ocr' / 'teslic-u-nob-borci.scan.json').read_text(encoding='utf-8'))}
# lines the OCR lost (faint print), read from the page: (prefix, the book's number) -> the text that ends the entry
LOST = {('9082', 810): 'u NOVJ od 15. 9. 1941', ('9082', 812): 'u NOVJ od 20. 5. 1944'}


def entry(e: dict, prefix: str, list_title: str) -> dict:
    text = text_of(e['words'])
    if (prefix, e['no']) in LOST:
        text = text.rstrip(' ,') + ', ' + LOST[(prefix, e['no'])]
    last, father, given, nick, note, rest = head_of(text)
    by, bp = born_in(rest)
    fix = SCAN.get((e['page'], round(e['lines'][0][1]['top'] - 1)))
    if fix:
        fix['used'] = True
        last, father, given, nick, by, bp = (fix.get(k, v) for k, v in (('last', last), ('father', father),
                                             ('given', given), ('nick', nick), ('by', by), ('bp', bp)))
    death = None
    for d in DEATH.finditer(rest):
        death = d
    when = None
    if death:
        dm = re.search(rf'(\d{{1,2}})\.\s*(\d{{1,2}})\.\s*{death.group(3)}', death.group(0))
        when = parse_when(f'{dm.group(1)}. {dm.group(2)}. {death.group(3)}') if dm else None
    first = [ln for p, ln in e['lines'] if p == e['page']]
    rec = {'soldier_id': f"{prefix}{e['no']:06d}", 'name': ' '.join(x for x in (last, father, given, nick) if x),
           'last_name': last, 'also': [], 'first_name': given, 'nick': nick, 'fathers_name': father, 'no': e['no'],
           'birth_year': by, 'born_in': bp, 'death_year': death.group(3) if death else '',
           'death_date': iso(when[0]) if when and when[0][2] else '',
           'units': sorted({code for pat, code in UNITS if re.search(pat, rest, re.I)}),
           'additional_info': f'{list_title}: ' + (f'{note}, ' if note else '') + rest, 'list': list_title,
           'pdf_file': PDF, 'pdf_page': e['page'], 'pdf_x': round(first[0]['x0'], 1), 'pdf_y': round(first[0]['top'] - 1, 1),
           'pdf_x_left': round(min(ln['x0'] for ln in first), 1), 'pdf_x_end': round(max(ln['x1'] for ln in first) + 1, 1),
           'pdf_y_end': round(max(ln['bottom'] for ln in first) + 1, 1)}
    return rec


def fighter(rec: dict) -> bool:
    info = rec['additional_info'].split(': ', 1)[1]
    return mos.fighter({'additional_info': info}) or bool(JA.search(info))


def main() -> None:
    global CORPUS
    CORPUS = Corpus(census=('bih',), entries=())
    for pages, prefix, out, list_title in LISTS:
        raw = read(pages)
        every = [entry(e, prefix, list_title) for e in raw]
        one_spelling(every)
        recs = [r for r in every if fighter(r)]
        dropped = [r for r in every if not fighter(r)]
        out.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
        nos = [r['no'] for r in every]
        gaps = [(a, b) for a, b in zip(nos, nos[1:]) if b != a + 1]
        print(f'{list_title}: {len(every)} entries (numbers {nos[0]}-{nos[-1]}, gaps {gaps}); {len(recs)} fighters, '
              f'{len(dropped)} left out')
        print(f"  no birth year: {sum(not r['birth_year'] for r in recs)}, no birthplace: {sum(not r['born_in'] for r in recs)}, "
              f"no father: {sum(not r['fathers_name'] for r in recs)}, death year: {sum(bool(r['death_year']) for r in recs)}, "
              f"units: {Counter(u for r in recs for u in r['units'])}")
        if '--dropped' in sys.argv:  # noqa
            for r in dropped:
                print(f"    OUT {r['no']}. {r['name']}: {r['additional_info'].split(': ', 1)[1][:150]}")
        if '--sample' in sys.argv:
            random.seed(5)
            for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
                print(f"    {r['no']}. {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['units']} | "
                      f"{r['additional_info'].split(': ', 1)[1][:120]}")


if __name__ == '__main__':
    main()
    unused = [k for k, r in SCAN.items() if not r.get('used')]
    assert not unused, f'hand readings that fit no entry: {unused}'
