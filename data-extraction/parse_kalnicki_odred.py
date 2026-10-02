"""
Parser: Kalnički partizanski odred (brigade code 58).

Source: Žarko Milićević, "Kalnički partizanski odred" (znaci.org 00003/558.pdf), "Spisak boraca Kalničkoga partizanskog
        odreda" (book p. 311 on)  →  website/public/pdfs/kalnicki-odred.pdf (PDF pages 307-395 of the book).
Two columns, Latin, a hanging indent; znaci.org re-typeset the book from its OCR:
    ČIŽIĆ ANDRIJA, Tome, r. 1923; Gornja Višnjica, Ivanec; u KPO od 1942.
    BIHLER ZVONKO; u KPO od 1943; radnik OK KPH Varaždin; ...      ŽELJEZNJAK ĐURO iz Zbelave, Varaždin.
The father's name (genitive) after the given name. The editors list 3,273 members (of some 3,500), 667 of them
fallen; 132 with the name only.
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import _record, extract_lines_two_column, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐÖÜ', 'a-zčćžšđöü'
ETHNIC = {'Hrvat', 'Hrvatica', 'Srbin', 'Srpkinja', 'Slovenac', 'Slovenka', 'Musliman', 'Mađar', 'Rus', 'Nijemac'}
_margin: dict = {}
_first: Counter = Counter()
_last: Counter = Counter()


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if f.replace('\\', '/').endswith('kalnicki-odred-soldiers.json'):
            continue                                                         # not this list's own earlier reading
        for s in json.load(open(f, encoding='utf-8')):
            _first[s['first_name'].upper()] += 1
            _last[s['last_name'].upper()] += 1


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    for ln in lines:
        col = (ln['page'], ln['x'] > 210)
        if re.match(rf'^[{U}]{{2}}', ln['text']):
            _margin[col] = min(_margin.get(col, 10 ** 6), ln['x'])
    return lines


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}', t) or re.fullmatch(r'SPISAK BORACA|KALNIČKOGA(?: PARTIZANSKOG ODREDA)?|PARTIZANSKOG ODREDA', t):
        return False
    if ln['x'] <= _margin.get((ln['page'], ln['x'] > 210), ln['x']) + 4 and re.match(rf'^[{U}]{{2}}', t):
        t = '§x§ ' + t                                                       # an entry starts at the column's edge
    ln['text'] = t
    return True


def father_nominative(w: str) -> str:
    stem = w[:-1]
    for c in (stem, stem + 'o', stem + 'a', stem + 'e', w[:-2] + 'ij' if w.endswith('ia') else ''):
        if c and _first[c.upper()] >= 3:
            return c
    return ''


SURNAME_END = re.compile(r'(?:IĆ|IČ|AC|AK|EK|EC|OV|IN|AR|AJ|AN|ER|EŠ|UŠ|OR|UK|ŠA|KA|NA)$')


def split_glued(tok: str) -> list[str]:
    """'GAŽIPAVLE' → GAŽI PAVLE: the longest known given name at the end."""
    for k in range(3, len(tok) - 2):
        if _first[tok[k:]] >= 5 and len(tok[k:]) >= 3:
            return [tok[:k], tok[k:]]
    return [tok]


TEXT_FIXES = [                                                               # the text layer's misreadings, read off the list
    ('IIR/INA', 'HRŽINA'), ('ITIANJO', 'FRANJO'), ('JOSD,', 'JOSIP,'), ('DRAGITUN', 'DRAGUTIN'), ('FU N1AK MAIO', 'FUNJAK MATO'),
    ('OREŠČAMN', 'OREŠČANIN'), ('MAI IJA', 'MARIJA'), ('UERKA', 'JERKA'), ('MIHAJI£>VIĆ', 'MIHAJLOVIĆ'), ('BRIGTTA', 'BRIGITA'),
    ('TRIFL NOVIĆ', 'TRIFUNOVIĆ'), ('BARTOLIĆ JOSD', 'BARTOLIĆ JOSIP,'),
]
SUFFIX = re.compile(r'(?:[OE]?VIĆ|IĆ|EC|AK|EK)')


def _known(w: str) -> int:
    return max(_first[w], _last[w])


def join_fragments(toks: list[str]) -> list[str]:
    """The re-typeset text spaces some names apart ("BRAN OVI Ć", "MAJ ER", "FE LI KS", "DARIN KA"): join the pieces
    when together they are a name the corpus knows, or when a piece is a lone letter or two, or a surname ending."""
    toks = list(toks)
    changed = True
    while changed:
        changed = False
        for k in (3, 2):
            for i in range(len(toks) - k + 1):
                part = toks[i:i + k]
                if '-' in part:
                    continue
                whole = ''.join(part)
                if ((_known(whole) >= 3 and any(_known(p) < 3 or len(p) <= 2 for p in part))
                        or (_known(whole) and SUFFIX.fullmatch(part[-1]))):
                    toks[i:i + k] = [whole]
                    changed = True
                    break
            if changed:
                break
        if not changed:
            for i in range(1, len(toks)):
                if (len(toks[i]) <= 2 and '-' not in (toks[i], toks[i - 1]) and not toks[i].endswith('.')
                        and not toks[i - 1].endswith('.') and _known(toks[i]) < 10):
                    toks[i - 1:i + 1] = [toks[i - 1] + toks[i]]
                    changed = True
                    break
    return toks


def caps_word(w: str) -> str:
    """A capitalized word's OCR misreadings: l and 1 for I, I) for D, II for H at the start."""
    w = w.replace('I)', 'D').replace('l', 'I').replace('1', 'I')
    w = w.rstrip('.') if len(w) > 2 else w
    return re.sub(r'^II(?=[AEIOU])', 'H', w)


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).replace('^', '').replace('\\', '')
    for a, b in TEXT_FIXES:
        text = text.replace(a, b)
    text = re.sub(rf'^([{U} ]+[{U}]{{2,}})j(?=[{U}][{L}])', r'\1, ', text)    # "VIDjDimitrija": the comma read as j
    paren = re.match(rf'^([{U}]+)\s+\((.*?)\);?\s*', text)
    if paren:                                                                # SRIJEMAC (borac neutvrđenog imena, ...)
        return _record(paren.group(1), '', '', paren.group(2) + '; ' + text[paren.end():])
    prefix = []
    m = re.search(r'[,;]|\s?(?=r\.\s*1[89]\d\d)', text)
    head, rest = (text[:m.start()], text[m.end():].strip()) if m else (text, '')
    words = head.split()
    n = 0
    while n < len(words) and (re.fullmatch(rf"[{U}0-9l/)\.\-]*[{U}][{U}0-9l/)\.\-]*", words[n]) or words[n] in ('dr', 'dr.', '-')):
        n += 1                                                               # the name: the capitalized words
    if n < len(words):                                                       # "LJUBOMIR s Korduna", "VALENT izVaraždina"
        rest = ' '.join(words[n:]) + (', ' + rest if rest else '')
    words = words[:n]
    if any(w in ('dr', 'dr.') for w in words):                               # "VESENJAK HIRJAN dr JELKA", "HERKOV dr. BOŽIDARKA"
        words = [w for w in words if w not in ('dr', 'dr.')]
        prefix.append('dr.')
    head = re.sub(r'\s*-\s*', ' - ', ' '.join(caps_word(w) for w in words))
    toks = join_fragments(head.split())
    groups, cur = [], []                                                     # hyphenated words back together
    for t in toks:
        if t == '-' or (cur and cur[-1] == '-'):
            cur.append(t)
        else:
            if cur:
                groups.append(''.join(cur))
            cur = [t]
    if cur:
        groups.append(''.join(cur))
    groups = [g.strip('-') for g in groups if g.strip('-')]
    if len(groups) == 1:
        groups = split_glued(groups[0])                                      # "AMBROŠIGNAC, Ivana": a glued name
    initial = [g for g in groups[1:] if re.fullmatch(r'\w\.', g)]          # "SEVEROVIĆ S. NIKOLA": the father's initial
    groups = [g for g in groups if g not in initial]
    if len(groups) >= 3 and groups[0] in ('VAN', 'VON', 'DE', 'DI'):          # "VAN BROEKHOVEN MARINUS"
        groups[:2] = [groups[0] + ' ' + groups[1]]
    if len(groups) >= 3 and _first[groups[-1]] and _first[groups[1].split('-')[0]] < 3:
        last, given, nick = '-'.join(groups[:-1]), groups[-1], []           # a double surname without the hyphen
    else:
        last, given, nick = (groups[0] if groups else ''), (groups[1] if len(groups) > 1 else ''), groups[2:]
    if '-' in given:                                                         # "MILEVA - ŠOJKA": the name she went by
        given, *more = given.split('-')
        nick = more + nick
    if nick:
        prefix.append('zvani ' + ', '.join(w.title() for w in nick))
    father = ''
    seg, after = (re.split(r',|\s(?=r\.|iz\s)', rest, 1) + [''])[:2]
    seg = seg.strip()
    if seg.endswith('ia') and not father_nominative(seg) and father_nominative(seg[:-2] + 'la'):
        seg = seg[:-2] + 'la'                                                # "Pavia" = Pavla
    if (re.fullmatch(rf'[{U}][{L}]+', seg) and seg.endswith(('a', 'e', 'ia')) and seg not in ETHNIC
            and father_nominative(seg)):
        father, rest = seg, after.strip()
    rest = '; '.join(prefix + ([rest] if rest else []))
    rec = _record(last, given, father or ''.join(initial), rest)
    if initial and not father:
        rec['fathers_name'] = ''
    if father:
        rec['fathers_name'] = father_nominative(father)
    m = re.search(r'(?:^|[;,]\s*)r\.\s*(1[89]\d\d)\b', rest)
    if m:
        rec['birth_year'] = m.group(1)
    return rec


def _ij(word: str, known: Counter) -> str:
    """IJ read as U ("Marua" = Marija, "Terezua", "Pikua"): the IJ spelling the corpus knows far better."""
    have = known[word.upper()]
    for i in [m.start() for m in re.finditer('u', word)]:
        cand = word[:i] + 'ij' + word[i + 1:]
        if known[cand.upper()] >= 2 and known[cand.upper()] >= 10 * have:
            return cand
    return word


def post(soldiers: list[dict]) -> list[dict]:
    """repair_lj_ocr, restore_diacritics, and IJ read as U in a name."""
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    for s in soldiers:
        s['first_name'] = ' '.join(_ij(w, _first) for w in s['first_name'].split(' '))
        s['last_name'] = '-'.join(_ij(w, _last) for w in s['last_name'].split('-'))
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/kalnicki-odred.pdf',
        brigade_code=58,
        output_path='website/public/kalnicki-odred-soldiers.json',
        start_page=2,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
    )
