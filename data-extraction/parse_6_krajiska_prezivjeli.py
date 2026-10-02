"""
Parser: 6. Krajiška NOU Brigada (brigade code 13) — the brigade's survivors, a second book.

Source: "Šesta krajiška NOU brigada — ratna sjećanja", part IV (znaci.org 00001/147_4.pdf), "Spisak boraca Šeste
        krajiške NOU brigade koji su preživjeli narodnooslobodilački rat 1945." (book pp. 747-762)  →
        website/public/pdfs/6-krajiska-prezivjeli.pdf (PDF pp. 35-50 of the part).
Cyrillic, two columns, names only, under a heading for each letter; a few with a note:
    Бурић Јове Рајко „Роћени"            Дрљача Мићо Брано — умро 1974.
znaci.org re-typeset the book from its OCR in a font without ђ: every ђ is ћ, Ђ is Б (the section after Д
prints "Б" over Бурић = Đurić), and the Ћ, Ц and Џ sections are headed Б, Д and Ц. The headings come in the
alphabet's order, so the n-th heading is the n-th letter, and a name that doesn't start with its section's
letter takes it (Бурић → Đurić). Inside a name, ć is read back as đ where the corpus knows only that spelling
(Burćević → Đurđević). Names are as printed otherwise; the father is in the genitive (Jove) or an initial.
The book's list of the fallen is the unit's first book (IDs from 1); these get IDs from 10001.
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import _record, extract_lines_two_column, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ALPHABET = ['A', 'B', 'V', 'G', 'D', 'Đ', 'E', 'Ž', 'Z', 'I', 'J', 'K', 'L', 'Lj', 'M', 'N', 'Nj', 'O', 'P', 'R', 'S',
            'T', 'Ć', 'U', 'F', 'H', 'C', 'Č', 'Dž', 'Š']
HEADING = re.compile(r'^(?:[A-ZČĆŽŠĐ3]|[a-zd]|Lj|Nj|Dž)$')
_section = {'i': -1}
FIXED: list = []
# the text layer's misreadings, checked against the page: г for т, stray dots and carets
TEXT_FIXES = {"' gupar": 'Stupar', 'S gupar': 'Stupar', 'Sgupar': 'Stupar', 'Sgeve': 'Steve', 'Svegozar': 'Svetozar',
              'Sl.^vko': 'Slavko', 'Da.jić': 'Dajić', 'Sto.janović': 'Stojanović', 'RadakoviJ!': 'Radaković',
              'Os goja': 'Ostoja', 'GJ': 'P', 'JSalućerović': 'Kalućerović', 'Pegra': 'Petra', 'Burs Mane': 'Bure Mane',
              '>': 'j'}
SUPPLEMENT: set = set()                                                      # "Naknadni spisak": in no order


def keep(ln: dict) -> bool:
    t = ln['text'].strip().lstrip('.,` ')                                    # ". Šević Luke Trivo"
    if ln['page'] == 1 and (ln['y'] < 185 or ln['y'] > 620):
        return False                                                         # title; the footnote
    if re.fullmatch(r'\d{3}\.?', t):
        return False                                                         # page numbers
    if t == 'NAKNADNI SPISAK':
        _section['i'] = None
        return False
    if HEADING.match(t) and _section['i'] is not None:
        _section['i'] += 1
        return False
    for bad, good in TEXT_FIXES.items():
        t = t.replace(bad, good)
    if _section['i'] is None:
        SUPPLEMENT.add((ln['page'], ln['y']))
        ln['text'] = t
        return True
    sec = ALPHABET[_section['i']] if _section['i'] >= 0 else 'A'
    if re.match(rf'^[{L}]\S*\s+(?:[{U}]\.\s+)?[{U}][{L}]', t):
        t = t[1:] if t[1].isupper() else sec + t[1:]                         # "žakšić B. Petar", "hMazalica Ljuba"
    first = re.match('(?:Lj|Nj|Dž|[A-ZČĆŽŠĐ])', t)
    if first and first.group(0) != sec:
        FIXED.append((ln['page'], t.split(' ')[0], sec + t.split(' ')[0][len(first.group(0)):]))
        t = sec + t[len(first.group(0)):]
    ln['text'] = t
    return True


NICK = re.compile(r'\s*[„"»]([^"“”«]+)["“”«]')


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """Two entries the text layer put on one line, after a stray dot: "Шева Станка Боро . Шевић Луке Триво"."""
    lines = []
    for ln in extract_lines_two_column(pdf_path, start, end, 283):     # the left column's long lines reach x 270
        for part in re.split(r'\s\.\s+(?=[А-ЯЂЋЏЉЊЈ])', ln['text']):
            lines.append({**ln, 'text': part})
    return lines


def parse_entry(text: str) -> dict:
    name, note = text, ''
    if re.search(r'\s[—–-]+\S?\s', text):
        name, note = re.split(r'\s+[—–-]+[•\-]?\s+', text, maxsplit=1)    # "— umro 1984.", "—• umro 1979"
    nick = NICK.search(name)
    if nick:
        name = name[:nick.start()] + name[nick.end():]
    toks = name.split()
    while toks and not re.search(rf'[{U}{L}]', toks[-1]):
        toks.pop()                                                           # "Rade 1", "Milutin <."
    toks = [w[0].upper() + w[1:] if w[0].islower() else w for w in toks]   # "Petroš jovan"
    last = toks[0] if toks else ''
    father, given = '', ''
    if len(toks) == 2:
        given = toks[1]
    elif len(toks) >= 3:
        father, given = toks[1], ' '.join(toks[2:])
    info = ('zvani ' + nick.group(1).strip() + '; ' if nick else '') + note.strip()
    return _record(last, given, father, info.strip('; '))


_by_fold: dict = {}
_FOLD = str.maketrans('đ', 'ć')


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if f.replace('\\', '/').endswith('6-krajiska-soldiers.json'):
            continue
        for s in json.load(open(f, encoding='utf-8')):
            for k in ('last_name', 'first_name', 'middle_name'):
                v = s.get(k) or ''
                if v:
                    _by_fold.setdefault(v.translate(_FOLD), Counter())[v] += 1


def dj(word: str) -> str:
    """ć where the font had đ: the spelling the corpus knows best of those that differ only in ć/đ."""
    if 'ć' not in word and 'Ć' not in word:
        return word
    options = _by_fold.get(word.translate(_FOLD).replace('Đ', 'Ć'), Counter()) + _by_fold.get(word.translate(_FOLD), Counter())
    if not options:
        return word
    best, n = options.most_common(1)[0]
    return best if best != word and n > 2 * options[word] else word


def dj_initial(word: str) -> str:
    """A given name or father's name whose Đ the font printed as B ("Buro" = Đuro): the Đ spelling when the
    corpus knows it far better."""
    if not word.startswith('B'):
        return word
    alt = dj('Đ' + word[1:])
    n_alt, n_word = sum(_by_fold.get(alt.translate(_FOLD), Counter()).values()), _count(word)
    return alt if _count(alt) > 3 * n_word and n_alt else word


def _count(word: str) -> int:
    return _by_fold.get(word.translate(_FOLD), Counter())[word]


def final_n(word: str) -> str:
    """н read as п at the end of a name ("Bogdap", "Dušap"; "Đurćevip" = -ić): the spelling the corpus knows."""
    for bad, good in (('ip', 'ić'), ('p', 'n')):
        if word.endswith(bad) and _count(word) == 0 and _count(word[:-len(bad)] + good) >= 3:
            return word[:-len(bad)] + good
    return word


def post(soldiers: list[dict]) -> list[dict]:
    changed = Counter()
    for s in soldiers:
        supplement = (s['pdf_page'], s['pdf_y']) in SUPPLEMENT
        for k in ('first_name', 'middle_name') + (('last_name',) if supplement else ()):
            s[k] = ' '.join(dj_initial(w) for w in s[k].split(' '))
        for k in ('last_name', 'first_name', 'middle_name'):
            parts = [final_n(dj(p)) for p in s[k].split('-')]
            new = '-'.join(parts)
            if new != s[k]:
                changed[(s[k], new)] += 1
                s[k] = new
        s['fathers_name'] = s['middle_name']
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    print('  ć → đ:', sum(changed.values()), changed.most_common(25))
    print('  section letters:', len(FIXED), [f for f in FIXED if f[0] != 5])
    return soldiers


if __name__ == '__main__':
    import sys
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/6-krajiska-prezivjeli.pdf',
        brigade_code=13,
        output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/6-krajiska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=re.compile(rf'^[{U}]'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
        id_start=10001,
        keep_other_sources=len(sys.argv) <= 1,
    )
