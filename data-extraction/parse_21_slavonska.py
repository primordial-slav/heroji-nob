"""
Parser: 21. slavonska udarna brigada (brigade code 34) — the fallen, died and missing.

Source: the brigade's monograph, chapter "Spisak poginulih, umrlih i nestalih boraca i starješina Dvadeset prve
        udarne slavonske brigade" (book pp. 345-398)
        znaci.org  →  website/public/pdfs/21-slavonska.pdf
Single column, Latin, names in title case (italic in print). pp. 1-53 the list:
    Abramović Jozo, komandir voda 3. čete 3. bataljona, rođen 1912. Vukojevci, Našice, Hrvat, član KPJ, poginuo ...
    Aleksa J. Mato, borac 2. bataljona, rođen 1921, u Okrugljači, Virovitica, Hrvat, zemljoradnik, poginuo ...
p. 54 a table of 14 of the brigade's fallen named on the memorial in Semberija but missing from the list
(the author's footnote), "Katić Bogoljub | Grabovac | 1923—1945". Then the book's contents.
Entries and their continuation lines start at the same margin; an entry starts at "Surname [F.] Given," after
a line that ends a sentence. The scan reads an italic capital L as "h" on p. 25 ("hatinović" = Latinović).
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser

MARK = '⁣'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NAME = re.compile(rf'^[{U}][{L}]+(?:-[{U}][{L}]+)?\s+(?:[{U}][{L}]?\.\s*)?[{U}][{L}]+(?:\s+[{U}][{L}]+)?\s*,')
MEMORIAL = re.compile(r'^(\S+) (\S+) (.+?) (1[89]\d\d)\s*[—–-]\s*(1[89]\d\d)$')
_prev_ended = [True]


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t):                                   # page numbers
        return False
    if ln['page'] == 1 and (ln['y'] < 245 or ln['y'] > 455):              # the title; the author's note on sources
        return False
    if ln['page'] == 54:
        m = MEMORIAL.match(t)
        if not m or ln['y'] > 470:                                         # the footnote under the table
            return False
        last, given, place, born, died = m.groups()
        given = re.sub(r'(?<=b)i$', '', given)                            # "Bogoljubi"
        ln['text'] = (f'{last}{MARK} {given}, rođen {born}, {place.replace(" j ", "j")}, poginuo {died}; '
                      'na spomen-obilježju palim borcima u Semberiji, nije u spisku poginulih')
        return True
    t = re.sub(rf'^h(?=[{L}]+\s+(?:[{U}]\.\s*)?[{U}][{L}]+\s*,)', 'L', t)   # "hatinović N. Nikola,"
    if _prev_ended[0] and NAME.match(t):
        t = re.sub(r'^(\S+)', r'\1' + MARK, t, count=1)
    _prev_ended[0] = bool(re.search(r'[.)]\s*$', t))
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    """Surname [F. | Father's] Given [Nick], bio"""
    text = text.replace(MARK, '')
    head, _, bio = text.partition(',')
    toks = head.split()
    last = toks[0] if toks else ''
    rest = toks[1:]
    father = rest.pop(0).rstrip('.') if len(rest) > 1 and re.fullmatch(rf'[{U}][{L}]?\.', rest[0]) else ''
    # "Prelević Milovana Stanimir", "Tokić Ivana Jure": a father printed in full, in the genitive
    if len(rest) == 2 and rest[0][-1] in 'ae':
        nominative = max(((rest[0][:-1] + e) for e in (('', 'o') if rest[0][-1] == 'a' else ('a', 'o'))), key=lambda n: _first[n])
        if _first[nominative] >= 3 and _first[nominative] >= 20 * _first[rest[0]]:     # not "Matija", "Vasilije"
            father = rest.pop(0)
    note = ['zvani ' + ' '.join(rest[1:])] if len(rest) > 1 else []
    bio = re.sub(r"^['^]+|(?<=\s)[\^]+", '', bio.strip())                 # "'borac", "u ^Čagliću"
    info = '; '.join(note + [bio])
    return _record(last, rest[0] if rest else '', father, info)


_first: Counter = Counter()
_last: Counter = Counter()
CARON = {'C': ('Č', 'Ć'), 'S': ('Š',), 'Z': ('Ž',)}
GIVEN_FIXES = {'Mlian': 'Milan', 'Mtjo': 'Mijo', 'Drušan': 'Dušan'}


def name_counts() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.endswith('21-slavonska-soldiers.json'):                   # not this unit's earlier output
            for s in json.load(open(f, encoding='utf-8')):
                _first[s['first_name']] += 1
                _last[s['last_name']] += 1


def carons(soldiers: list[dict]) -> list[dict]:
    """The scan drops many carons of Č/Ć, Š and Ž, but the book sorts those letters after the plain ones: in
    document order, once a letter's section has shown a name with the caron (Ćuk, Šantak, Žagar), a later plain
    name of that letter takes it too ("Cavić" → Čavić, "Skolić" → Školić, "Zivković" → Živković), unless the
    corpus knows it only without ("Stojadinović" printed out of order). Č or Ć by the corpus, Č when neither."""
    in_caron = None
    for s in soldiers:                                                     # document order
        name = s['last_name']
        base = name[:1].translate(str.maketrans('ČĆŠŽ', 'CCSZ'))
        if in_caron and base != in_caron:
            in_caron = None
        if base in CARON and name[:1] != base:
            in_caron = base
        elif in_caron and name[:1] == base:
            cands = [c + name[1:] for c in CARON[base]]
            best = max(cands, key=lambda c: _last[c])
            if not (_last[name] >= 5 and _last[name] >= 10 * _last[best]):
                s['last_name'] = best
    return soldiers


def ocr_names(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        s['last_name'] = re.sub(r'ie$', 'ić', re.sub(r'ae$', 'ac', re.sub(r'^Jl', 'Il', s['last_name'])))   # "Cavie", "Leskovae", "Jlić"
        s['first_name'] = GIVEN_FIXES.get(s['first_name'], s['first_name'])
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = carons(ocr_names(soldiers))
    for s in soldiers:
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    name_counts()
    run_parser(
        pdf_path='website/public/pdfs/21-slavonska.pdf',
        brigade_code=34,
        output_path='website/public/21-slavonska-soldiers.json',
        start_page=1,
        end_page=54,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^\S+' + MARK),
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        post_fn=post,
    )
