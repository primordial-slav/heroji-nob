"""
Parser: 9. dalmatinska divizija (brigade code 145) and 3. dalmatinska brigada (code 46, a second book): their fallen
and missing of the Fourth Offensive, 1943.

Source: Obrad Egić, *Dva rođenja Devete dalmatinske divizije* (znaci.org 00001/187, the whole book's PDF pp. 113-120,
book pp. 121-128). The division kept no list of its losses; the author gathered them from its survivors:
    "Spisak boraca i rukovodilaca 9. dalmatinske NOU divizije koji su poginuli i nestali u borbama od 11. II do
        15. IV 1943. god." (PDF pp. 113-118) → website/public/pdfs/9-dalmatinska-divizija.pdf;
    the losses of the 3. samostalna dalmatinska brigada, 14 April - 6 June 1943, after a short note (PDF pp. 118-120)
        → website/public/pdfs/3-dalmatinska-poginuli.pdf (its first page repeats the division's last).
Names only, two columns, a name a line: the surname and the given name in capitals, the father's possessive after
them ("ALAVANJA PAVAO Vasiljev"; a woman's "Antina", or "žena Lukina", Luka's wife), at times a nickname after a
dash ("NIKOLA-LENJO"), in quotes on the next line ("»Smokva«") or a place that tells two namesakes apart
("JOZIPOVIC MATE Marijanov — / B. Voda"). The scan loses carons and reads I as l ("COVlC"); the corpus gives them
back (parse_8_kordunaska_divizija.post).
The division's list is unit 145's (0145000001-); the brigade's gets 0046010001 on, after its Borci Sutjeske records.
Usage: python data-extraction/parse_9_dalmatinska_divizija.py
"""
import json
import re
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}lI1\-]+'
# where each PDF's list is on its pages: (first top, last top) by page; the division's heading on its first page,
# and the page the two lists share (the note between them: "Isto kao i u 9. diviziji, ni u 3. samostalnoj ...")
SPAN = {
    '9-dalmatinska-divizija.pdf': {1: (230, 660), 6: (0, 470)},
    '3-dalmatinska-poginuli.pdf': {1: (575, 660)},
}
SPELLED = {                                       # names the scan split or ran together
    'BE ARA BRANKO': 'BEARA BRANKO', 'KAŠTEL ANIĆ ANTE': 'KAŠTELANIĆ ANTE', 'VIŠKO VIC JOZO': 'VIŠKOVIĆ JOZO',
    'MIM ICAROKO': 'MIMICA ROKO', 'JUGO VIC MATE': 'JUGOVIĆ MATE', 'STIPICA MRIN': 'STIPICA MARIN',
    'LUC A ': 'LUCA ', 'ŠUŠNJAR TADIĆ': 'ŠUŠNJAR-TADIĆ', 'MRSA MATE Sekso': 'MRSA MATE »Sekso«',
}
WORDS = {                                         # fathers the scan misread ("Iiijin" = Ilijin)
    'Iiijin': 'Ilijin', 'iiijin': 'Ilijin', 'Ianov': 'Ivanov', 'Japovljev': 'Jakovljev', 'Svevanov': 'Stevanov',
    'Marino': 'Marinov',
}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    span = SPAN[pdf_path.replace('\\', '/').rsplit('/', 1)[-1]]
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            lo, hi = span.get(pno, (0, 660))
            words = [w for w in viewer_words(page, keep_blank_chars=False) if lo <= w['top'] <= hi]
            if not words:
                continue
            left = min(w['x0'] for w in words)
            # the right column: the first surname in capitals well right of the left column's start
            right = min((w['x0'] for w in words if w['x0'] > left + 140 and re.fullmatch(CAPS, w['text'])), default=1e9)
            for col in (0, 1):
                cw = [w for w in words if (w['x0'] >= right - 8) == bool(col)]
                rows = []
                for w in sorted(cw, key=lambda w: (round(w['top']), w['x0'])):
                    if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                        rows[-1].append(w)
                    else:
                        rows.append([w])
                for r in rows:
                    r.sort(key=lambda w: w['x0'])
                    text = ' '.join(w['text'] for w in r)
                    if re.fullmatch(r'[\d*\W]{1,5}', text):
                        continue                         # page numbers, the asterisks between the lists
                    lines.append({'text': text, 'x': r[0]['x0'], 'y': r[0]['top'], 'page': pno})
    # an entry starts with a surname in capitals, unless the one before has no given name yet ("VUCKOVlC-VUClCEVlC" /
    # "ZIVKO" / "Stojanov") or ends with a dash ("JOZIPOVIC MATE Marijanov —" / "B. Voda")
    out, open_ = [], False
    for ln in lines:
        t = ln['text'] = re.sub(rf'(?<=[{U}])"', '', ln['text'])    # 'CUDINA" MILE Franin'
        new = bool(re.match(rf'^{CAPS}(?:\s|$)', t)) and not open_
        if new:
            ln['text'] = '§x§ ' + t
        caps = re.findall(rf'(?<!\S){CAPS}(?!\S)', t)
        open_ = (new and len(caps) == 1 and len(t.split()) == 1) or t.rstrip().endswith(('—', '-'))
        out.append(ln)
    return out


def parse(text: str) -> dict:
    t = re.sub(r'^§x§\s*', '', text).strip()
    for a, b in SPELLED.items():
        t = t.replace(a, b)
    notes = []
    nick = re.search(r'[»"„]([^«"“]+)[«"“]?', t)
    if nick:                                      # "PAVKOVIC IVAN Ivanov »Smokva«"
        notes.append(f'zvani {nick.group(1).strip()}')
        t = (t[:nick.start()] + t[nick.end():]).strip()
    place = re.search(r'\s+—\s*(.+)$', t)
    if place:                                     # "JOZIPOVIC MATE Marijanov — B. Voda"
        notes.append(place.group(1).strip())
        t = t[:place.start()]
    wife = re.search(rf'\s+žena\s+([{U}][{L}]+)$', t)
    if wife:                                      # "BATINARIC MASA žena Lukina": Luka's wife
        notes.insert(0, f'žena {wife.group(1)}')
        t = t[:wife.start()]
    words = [WORDS.get(w, w) for w in t.split()]
    if 'Dr' in words:                             # "PAUT Dr EUGEN"
        words.remove('Dr')
        notes.insert(0, 'dr')
    if len(words) >= 3 and re.fullmatch(rf'[{U}]+(?:OV|EV|IN)A?', words[-1]) and re.fullmatch(CAPS, words[1]):
        words[-1] = words[-1].title()             # "ERICA ANTE MARINOV": the father in capitals
    caps = [k8.caps_word(w) for w in words if re.fullmatch(CAPS, w)]
    small = [w for w in words if not re.fullmatch(CAPS, w)]
    last = caps[0] if caps else ''
    given, father = ' '.join(caps[1:]), ''
    if small:
        if given and len(caps) == 2 and re.search(r'[EA]$', caps[1]) and re.search(r'[aeo]$', small[0])                 and not re.search(r'(?:ov|ev|in|ova|eva|ina)$', small[0]):
            # "PETROVIC ILIJE Olga": the father in the genitive, then her given name
            father, given = caps[1], small[0]
        elif not given:
            given = small[0]                         # "GILJEVIC Ante", "VUĆKOVIĆ-ŠKORIC Petar"
        else:
            father = small[0]                        # "Vasiljev", "Antina"
    alias = re.fullmatch(rf'([{U}]+)-([{U}]+)', given)
    if alias:                                     # "NIKOLA-LENJO", "ANTE-CUCA": the nickname after a dash
        given = alias.group(1)
        notes.insert(0, f'zvani {alias.group(2).title()}')
    rec = _record(last.title(), given.title(), father.title() if father.isupper() else father, '; '.join(notes))
    rec['birth_year'] = ''
    return rec


def nominative(poss: str) -> str:
    """The father's name from its possessive, as the site's given names spell it: "Jozin" = Jozo, "Matin" = Mate,
    "Ilijin" = Ilija, "Petrov" = Petar, "Stipanov" = Stipan, a daughter's "Antina" = Ante; a genitive ("ILIJE") or a
    form none of these explains stays as printed."""
    m = re.fullmatch(rf'([{U}][{L}]+?)(ov|ev|in)a?', poss)
    if not m:
        return poss
    base, end = m.groups()
    cands = [base + 'o', base + 'a', base + 'e', base] if end == 'in' else \
        [base, base + 'o', base + 'e', re.sub(r'([^aeiou])([rl])$', r'\1a\2', base)]
    if base.endswith('lj'):                          # "Jakovljev" = Jakov, "Vasiljev" = Vasilije
        cands = [base[:-2], base[:-1] + 'ije']
    # Dalmatia's forms first ("Matin" is Mate there, Mato elsewhere), then the corpus's
    best = max(cands, key=lambda c: (dalmatian().get(c, 0), k8.known(c, 'first_name')))
    return k8.respell(best, 'first_name') if dalmatian().get(best) or k8.known(best, 'first_name') else poss   # Simun = Šimun


_dalm: dict = {}


def dalmatian() -> dict:
    """Given names of the Dalmatian units on the site, by count"""
    if not _dalm:
        for f in ('2-dalmatinska', '4-splitska', '1-dalmatinska', '11-dalmatinska', '12-dalmatinska', '6-dalmatinska',
                  '19-sjevernodalmatinska'):
            for s in json.loads(Path(f'website/public/{f}-soldiers.json').read_text(encoding='utf-8')):
                for g in s['first_name'].split():
                    _dalm[g] = _dalm.get(g, 0) + 1
    return _dalm


def post(soldiers: list[dict]) -> list[dict]:
    printed = {id(s): s['middle_name'] for s in soldiers}
    soldiers = k8.post(soldiers)
    for s in soldiers:
        # the corpus's spelling for names, not for the fathers' possessives ("Jozin" is not "Jožin")
        s['middle_name'] = printed.get(id(s), s['middle_name'])
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        s['fathers_name'] = nominative(s['middle_name']) if s['middle_name'] else ''
    return soldiers


if __name__ == '__main__':
    k8.corpus()
    for pdf, code, out, extra in (
            ('9-dalmatinska-divizija.pdf', 145, '9-dalmatinska-divizija-soldiers.json', {}),
            ('3-dalmatinska-poginuli.pdf', 46, '3-dalmatinska-soldiers.json',
             {'id_start': 10001, 'keep_other_sources': True})):
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
            post_fn=post,
            **extra,
        )
