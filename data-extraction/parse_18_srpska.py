"""
Parser: 18. srpska brigada (brigade code 128).

Source: Krstivoje Milosavljević, "Osamnaesta srpska brigada" (Beograd 1989; znaci.org 00001/88), the chapter
        "Oni su se borili u 18. srpskoj brigadi" (88_9.pdf → website/public/pdfs/18-srpska.pdf, book pp. 313-426):
        everyone in the brigade, rebuilt from SUBNOR's register, the 25. division's medical records and the
        brigade's surviving papers, 5,047 fighters and officers by the author's count (780 fallen, 787 wounded, 47
        missing, 49 dead of illness). Its p. 2 is the author's note; the last pages are the sources and contents.
Cyrillic, two columns, each entry hanging (its first line some 12pt left of the lines under it), surname and given
name in capitals, no father; the year and village of birth, a duty, the wound or death:
    МИЛИЋ РАДИВОЈЕ, 1918, Везичево. Погинуо марта 1945. код Градачца
    МИЛИН СИБИН, водник, шеф столарске радионице
Some entries give only a surname, a given name or a nickname. The scan spells many names in Latin look-alikes of the
Cyrillic letters ("ABPAMOBHR" = Аврамовић, read back with parse_uzicki_odred.decode) and reads Ћ as К, Н or Б at a
name's end ("МИЛИБ").
"""
import itertools
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, extract_lines_two_column, repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser
from parse_uzicki_odred import FIRST, LAST, LOOKALIKE, TELL

# parse_uzicki_odred's look-alikes, and this book's digits for letters ("AA3APEBHR" = Лазаревић, "CBET03APEBHR" =
# Светозаревић) and "H." for Њ ("KOH.HR" = Коњић)
LOOK = dict(LOOKALIKE, **{'3': ('Z',), '0': ('O',), 'H.': ('NJ',)})
LOOK_WORD = re.compile(r'(?:A>|H>|H\.|III|UI|IU|[ABCEHIKMNOPTXYJRU430])+')

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\->4]+'
COLUMN_SPLIT = 150                 # the left column's lines start at x 45-95, the right column's at 195-255
_left: dict = {}


def page_number(t: str) -> bool:
    return bool(re.fullmatch(r'[\d\W]{1,5}', t)) or len(t) <= 2


def entry_like(t: str) -> bool:
    return bool(re.match(rf'^[{U}A-Z]{{2,}}\S*\s*[{U}A-Z,]', t))


def measure(lines: list[dict]) -> None:
    for ln in lines:
        t = ln['text'].strip()
        if entry_like(t) and not page_number(t):
            key = (ln['page'], ln['x'] > COLUMN_SPLIT)
            _left[key] = min(_left.get(key, 10 ** 6), ln['x'])


def letters(t: str) -> str:
    """Љ and Њ read as "Л>", "Н>" (after transliteration "L>", "H>"), У as Y or ¥"""
    t = re.sub(r'L>(?=[A-ZČĆŽŠĐ¥])', 'LJ', t).replace('L>', 'Lj')
    t = re.sub(r'H>(?=[A-ZČĆŽŠĐ¥])', 'NJ', t).replace('H>', 'Nj')
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])¥|¥(?=[A-ZČĆŽŠĐ])', 'U', t)
    # Љ read as "La", "Lz", "Lo", "L.", "L)", "Ij", "Az", "Lj" before an U: "DRAGOLaUB", "LzUBISAV", "L.ubiša"
    t = re.sub(r'(?:L[azo.)j]|Ij|Az)(?=[Uu])', 'LJ', t)
    # and inside a word: "MILOSAVL.EVIĆ", "NEDEL.KOVIĆ", "BOGOSAVL)", "MILOSAVA)EVIĆ"
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])[LA][.)>](?=[A-ZČĆŽŠĐ]|\b)', 'LJ', t)
    t = re.sub(r'(?<=[a-zčćžšđ])[la][.)>](?=[a-zčćžšđ])', 'lj', t)
    return re.sub(r'(?<![\w])[Y¥](?=\s|$)', 'U', t)


def keep(ln: dict) -> bool:
    t = letters(ln['text'].strip())
    if page_number(t):
        return False
    new = ln['x'] < _left.get((ln['page'], ln['x'] > COLUMN_SPLIT), 0) + 7 and entry_like(t)
    ln['text'] = ('§x§ ' if new else '') + t
    return True


def decode(word: str, known) -> str | None:
    """parse_uzicki_odred.decode with this book's look-alikes: the reading the corpus knows best"""
    w = word.upper()
    if not LOOK_WORD.fullmatch(w) or not re.search(r'[A-Z]', w):
        return None
    parts = re.findall(r'A>|H>|H\.|III|UI|IU|.', w)
    options = [LOOK[p] for p in parts]
    if sum(len(o) > 1 for o in options) <= 7:
        best = max((''.join(c) for c in itertools.product(*options)), key=lambda c: known[c])
        if known[best] and (TELL.search(w) or re.search(r'[30]|H\.', w) or not known[w]):
            return best
    if not (TELL.search(w) or re.search(r'[30]|H\.', w)):
        return None
    return re.sub(r'NĆ$', 'IĆ', ''.join(o[0] for o in options))


def read_word(w: str, known) -> str:
    return decode(w, known) or w


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).strip()
    head, _, info = text.partition(',')
    head = re.sub(r'\s+[-–—]\s*|\s*[-–—]\s+', ' — ', head)
    parts = head.split(' — ')
    words = [w.strip('.') for w in parts[0].split()]
    words = [w.upper() if sum(c.isupper() for c in w) >= 0.7 * len(w) else w for w in words]   # "ŽURKIć"
    nick = parts[1:]
    if len(words) > 2 and len(words[-1]) <= 2:                              # "ПЕТРОВИЋ ЈОВ АН": a name spaced apart
        words = words[:-2] + [words[-2] + words[-1]]
    if len(words) > 2:                                                       # "ЂОРЂЕВИЋ ЖИВОЈИН СОКО": a nickname
        words, nick = words[:2], words[2:] + nick
    last, given = (words[:1], words[1:]) if len(words) > 1 else (words, [])
    last = ['-'.join(read_word(p, LAST) for p in w.split('-')) for w in last]
    given = [read_word(w, FIRST) for w in given]
    info = info.strip()
    if nick:
        info = 'zvani ' + ' '.join(nick).strip().title() + '; ' + info
    return _record(' '.join(last), ' '.join(given), '', info)


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    return sorted(lines, key=lambda l: (l['page'], l['x'] > COLUMN_SPLIT, l['y']))


def vocabulary() -> Counter:
    words = Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != '18-srpska-soldiers.json':
            for r in json.loads(f.read_text(encoding='utf-8')):
                words.update(re.findall(r'[A-Za-zČĆŽŠĐčćžšđ]+', r.get('additional_info') or ''))
    return words


def l_for_d(text: str, words: Counter) -> str:
    """The italics of the fallen's entries read л as д ("bodničarka", "Godubac", "bodesti"): a word the corpus
    doesn't know becomes the spelling with л it knows well"""
    def fix(m: re.Match) -> str:
        w = m.group(0)
        if words[w] >= 2 or 'd' not in w:
            return w
        spots = [i for i, c in enumerate(w) if c == 'd']
        best, n = w, 0
        for k in range(1, 1 << min(len(spots), 4)):
            v = list(w)
            for j, i in enumerate(spots[:4]):
                if k >> j & 1:
                    v[i] = 'l'
            v = ''.join(v)
            if words[v] > n:
                best, n = v, words[v]
        return best if n >= 5 else w
    return re.sub(r'[A-Za-zČĆŽŠĐčćžšđ]{3,}', fix, text)


def post(soldiers: list[dict]) -> list[dict]:
    words = vocabulary()
    for s in soldiers:
        s['additional_info'] = l_for_d(s['additional_info'], words)
    return repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True)))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/18-srpska.pdf',
        brigade_code=128,
        output_path='website/public/18-srpska-soldiers.json',
        start_page=3,
        end_page=112,
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        prepare_fn=measure,
        post_fn=post,
    )
