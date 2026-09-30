"""
Parser: 8. crnogorska NOU brigada (brigade code 38) — the fallen.

Source: "Osma crnogorska NOU brigada — zbornik sjećanja" (znaci.org/00001/275.pdf, the whole book), cut to
        website/public/pdfs/8-crnogorska.pdf:
    p. 1      the chapter's title page (book p. 471)
    pp. 2-31  "Pali drugovi borci i starješine brigade" (book pp. 472-501), Cyrillic:
        АДАМОВИЋ Владимира АЛЕКСАНДАР, рођен у Туларима, земљорадник, у бригади од октобра 1944, погинуо ...
    pp. 32-33 the book's afterword (p. 509-510): forty more fallen that the SUBNOR committee of Ub sent after the
              book was printed, in Latin, the same way ("JOVANOVIĆ Svetomira MILOJE, rođ. 1922. ...")
Entries and their continuation lines start at the same margin (flush), so an entry starts at a line that reads
SURNAME [Father] GIVEN, ... The Cyrillic OCR reads a final Ћ as Н/К/Б, Ђ as Б, Л as А and garbles some given
names ("AAEKSANDAR"): repair_cyrillic_ocr, repair_capital_c, and given names mended against the corpus.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from _margin_entries import MARK, MarginEntries, fix_caps_head, fix_cyrillic_ocr_line, join_split_surname, \
    lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_capital_c, repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

me = MarginEntries()
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SUPPLEMENT_FIRST_PAGE = 32
# SURNAME [Father] GIVEN, — after a speck or two ("'. BIRTAŠEVIK"); the comma may be missing ("NOVAK rođen")
START = re.compile(rf'^(?:[^\s{U}]{{0,2}}|[^\w]{{1,3}}\s)([{U}][{U}\-]{{2,}})\s+(?:[{U}][{L}]+\s+)?[{U}]{{2}}[^,]{{0,30}}(?:,|\srođen)')


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    p, y = ln['page'], ln['y']
    if p == 1 or re.fullmatch(r'[\W\d]{1,6}', t) or len(t) < 8 and not re.match(rf'^[{U}]{{3}}', t):
        return False                                                   # title page, page numbers, stray bits ("ro e")
    if p == 2 and y < 150 or p == SUPPLEMENT_FIRST_PAGE and y < 128:   # the list's heading; the afterword's text
        return False
    t = join_split_surname(fix_caps_head(fix_cyrillic_ocr_line(t)))
    m = START.match(t)
    if m:
        t = m.group(1) + MARK + t[m.end(1):]                           # (a speck before the surname dropped)
    ln['text'] = t
    return True


def _corpus() -> tuple[Counter, Counter, Counter]:
    """Names in the units on the site before this one (codes below 38): later units must not change what this
    parser reads (its IDs follow the names' order, and corrections refer to the IDs)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
    from name_utils import BRIGADE_CONFIGS
    first, last, fathers = Counter(), Counter(), Counter()
    for code, cfg in BRIGADE_CONFIGS.items():
        f = Path('website/public') / cfg['json_file']
        if code < 38 and f.exists():
            for s in json.loads(f.read_text(encoding='utf-8')):
                first[s['first_name']] += 1
                last[s['last_name']] += 1
                fathers[s.get('middle_name') or ''] += 1
    return first, last, fathers


# the book sorts by the Cyrillic alphabet, А Б В Г Д Ђ Е Ж З И Ј К Л Љ М Н Њ О П Р С Т У Ф Х Ц Ч Џ Ш, but puts Ћ
# after Ц
CYR_ORDER = ['A', 'B', 'V', 'G', 'D', 'Đ', 'E', 'Ž', 'Z', 'I', 'J', 'K', 'L', 'LJ', 'M', 'N', 'NJ', 'O', 'P', 'R', 'S',
             'T', 'U', 'F', 'H', 'C', 'Ć', 'Č', 'DŽ', 'Š']
# misreads the rules below don't reach: Ћ read as К or Н inside a name, Л as А, a first letter lost or misread
SURNAME_FIXES = {
    'Dragikević': 'Dragićević', 'Đurbin': 'Đurđić', 'Đurck': 'Đurić', 'Đorbevii-Jovanović': 'Đorđević-Jovanović',
    'Iain': 'Ilin', 'Jezernić': 'Jezernik', 'Jeftnn': 'Jeftić', 'Kaluberović': 'Kaluđerović',
    'Krnvokapić': 'Krivokapić', 'Aban': 'Laban', 'Pavinević': 'Pavićević', 'Pljakin': 'Pljakić', 'Jretel': 'Pretel',
    'Jrljanović': 'Prljanović', 'Adovanović': 'Radovanović', 'Srekković': 'Srećković', 'Tmušin': 'Tmušić',
    'Čogurin': 'Čogurić', 'Llundić': 'Šundić', 'Pkepanović': 'Šćepanović', 'Ikepanović': 'Šćepanović',
}
GIVEN_FIXES = {'Kovani': 'Đovani', 'Košta': 'Kosta', 'Šnepan': 'Šćepan', 'Glero': 'Đero',
               'Ijšja': 'Ilija', 'Dragolp': 'Dragoljub', 'Saavoaaub': 'Slavoljub', 'Dimitrkje': 'Dimitrije',
               'Lljbiša': 'Ljubiša', 'Bogik': 'Bogić', 'Batrik': 'Batrić'}
BORN_GARBLED = re.compile(r'\b(?:rođei|roćei|roćep|rođec|roBen|rođ|rđ|đen|đn|đ)(?=,?\s+1[89]\d\d\b)')
FATHER_FIXES = {'Borđa': 'Đorđa', 'Boke': 'Đoke', 'Borća': 'Đorđa', 'Borćija': 'Đorđija', 'Kirka': 'Ćirka'}


def letter_sections(soldiers: list[dict]) -> list[dict]:
    """The OCR reads the capital Ђ as Б and Ћ as Б or Н, so the Ђ names come out as B names ("Bukić" Đukić) and the
    Ћ names as B or N names ("Nirić" Ćirić). A run of such names printed where the list is at Đ (between D or Đ
    names and Đ or E names) or at Ć (between C or Ć names and Ć or Č names) takes the letter back."""
    listed = [s for s in soldiers if s['pdf_page'] < SUPPLEMENT_FIRST_PAGE]
    initial = lambda s: s['last_name'][:1]
    i = 0
    while i < len(listed):
        if initial(listed[i]) not in 'BN':
            i += 1
            continue
        j = i
        while j < len(listed) and initial(listed[j]) in 'BN':
            j += 1
        before = initial(listed[i - 1]) if i else ''
        after = initial(listed[j]) if j < len(listed) else ''
        for letter, lo, hi in (('Đ', 'DĐ', 'ĐE'), ('Ć', 'CĆ', 'ĆČ')):
            if before and after and before in lo and after in hi and (before == letter or after == letter):
                for s in listed[i:j]:
                    s['last_name'] = letter + s['last_name'][1:]
        i = j
    return soldiers


def _cyr_fold(w: str) -> tuple:
    w, key = w.upper(), []
    while w:
        ch = w[:2] if w[:2] in CYR_ORDER else w[0]
        key.append(CYR_ORDER.index(ch) if ch in CYR_ORDER else 99)
        w = w[len(ch):]
    return tuple(key)


def restore_cropped(soldiers: list[dict], last: Counter) -> list[dict]:
    """Some pages lose the left edge of their lines, and with it a surname's first letter(s) ("Jopović" Popović,
    "Azarević" Lazarević, "Ikepanović" Šćepanović). The list runs in the Cyrillic alphabet, so the full surname
    sorts between the nearest known surnames before and after it: the most common known surname that ends with
    what is left (or with all but a damaged first letter), 1-3 letters longer and in that range, wins."""
    listed = [s for s in soldiers if s['pdf_page'] < SUPPLEMENT_FIRST_PAGE]     # the afterword's list is not sorted
    by_suffix = defaultdict(list)
    for w in last:
        if len(w) >= 3:
            by_suffix[w.lower()[-3:]].append(w)
    known = [bool(last[s['last_name']] >= 2) for s in listed]
    for i, s in enumerate(listed):
        name = re.sub(r'i[ib]$', 'ić', s['last_name'])                        # "Obradovii"
        if last[name] >= 2:
            s['last_name'] = name
            continue
        if known[i]:
            continue
        lo = next((_cyr_fold(listed[j]['last_name']) for j in range(i - 1, -1, -1) if known[j]), ())
        hi = next((_cyr_fold(listed[j]['last_name']) for j in range(i + 1, len(listed)) if known[j]), (99,))
        if lo <= _cyr_fold(name) <= hi and re.search('[aeiou]', name[:2].lower()):
            continue                                                   # in its place: a rare name ("Čavor")
        r = name.lower()
        cands = []
        for tail, damaged in ((r, 0), (r[1:], 1)):
            if len(tail) < 3:
                continue
            for w in by_suffix.get(tail[-3:], ()):
                add = len(w) - len(tail)
                if w.lower().endswith(tail) and 1 <= add + damaged <= 3 and lo <= _cyr_fold(w) <= hi:
                    cands.append((last[w] / (1 + damaged), w))
        if cands:
            n, best = max(cands)
            if last[best] >= 3:
                s['last_name'] = best
    for s in listed:
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def _mend(g: str, known: Counter) -> str:
    """A name the corpus doesn't know takes the best-known spelling one or two usual misreads give (Л read as А or Д:
    "Aaeksandar"; И as Н: "Mnlana"; Т as Г: "Svegozara"; Ћ as К at the end: "Batrik"; Ђ as Б: "Borđa"; others)."""
    subs = [('a', 'l'), ('A', 'L'), ('d', 'a'), ('D', 'A'), ('n', 'u'), ('u', 'n'), ('n', 'i'), ('i', 'l'), ('l', 'i'),
            ('e', 'c'), ('c', 'e'), ('h', 'n'), ('r', 'n'), ('o', 'a'), ('b', 'đ'), ('g', 't'), ('B', 'Đ')]
    if not g or known[g] >= 3:
        return g
    cands = {g[:m.start()] + b + g[m.end():] for a, b in subs for m in re.finditer(re.escape(a), g)}
    cands |= {c[:m.start()] + b + c[m.end():] for c in list(cands) for a, b in subs for m in re.finditer(re.escape(a), c)}
    cands.add(re.sub('ik$', 'ić', g))
    best = max(cands, key=lambda c: known[c], default=None)
    return best if best and known[best] >= 20 and known[best] >= 10 * known[g] else g


def mend_given(soldiers: list[dict], first: Counter, fathers: Counter) -> list[dict]:
    """Љ read as "l.", "l/" ("Dragol.ub", "Ll/biša"); a name in mixed case ("MILOMIr"); a second given name is a
    nickname ("Milovan Kešik"). Then the given name and the father's name are mended against the corpus."""
    for s in soldiers:
        for k in ('first_name', 'middle_name'):
            v = re.sub(r'(?i)l[./]', 'lj', s.get(k) or '')
            s[k] = ' '.join(w[:1].upper() + w[1:].lower() if re.search(r'[a-zčćžšđ]', w[1:]) else w for w in v.split())
        words = s['first_name'].split()
        if len(words) == 2 and words[1][0].isupper():
            s['first_name'] = words[0]
            s['additional_info'] = f'zvani {words[1]}; ' + s['additional_info']
        s['first_name'] = GIVEN_FIXES.get(s['first_name']) or _mend(s['first_name'], first)
        s['middle_name'] = FATHER_FIXES.get(s['middle_name']) or _mend(s['middle_name'], fathers)
        s['fathers_name'] = s['middle_name']
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_capital_c(repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True))))
    first, last, fathers = _corpus()
    soldiers = restore_cropped(letter_sections(soldiers), last)
    for s in soldiers:
        s['last_name'] = SURNAME_FIXES.get(s['last_name'], s['last_name'])
        born = re.match(r'^(\S+)\s+\S{1,2}n\s+(\d{4})$', s['first_name'])      # "MILORdd đn 1927": rođen ran in
        if born:
            s['first_name'] = born.group(1)
            s['additional_info'] = f'rođen {born.group(2)}. ' + s['additional_info']
    soldiers = mend_given(lone_names_to_given(split_leading_aliases(soldiers), first, last), first, fathers)
    for s in soldiers:
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
        # "rođen" is set in small raised letters on the first pages, and the OCR splits or garbles it ("đn 1925.",
        # "rđ 1921.", "rođei 1923."); the afterword abbreviates it ("rođ. 1925. godine")
        info = BORN_GARBLED.sub('rođen', s['additional_info'], count=1)
        s['additional_info'] = info.replace('u B(?ogradu', 'u Beogradu').replace('u Novacnma', 'u Novacima')   # misreads
        born = re.match(r'^(?:[^,]{0,20},\s*)?(?:rođena?|rođ\.)\s+(1[89]\d\d)\b', s['additional_info'])
        if born and not s['birth_year']:
            s['birth_year'] = born.group(1)
        if s['pdf_page'] >= SUPPLEMENT_FIRST_PAGE:
            s['additional_info'] = (s['additional_info'].rstrip('.') + '. ' if s['additional_info'] else '') + \
                'Iz dopunskog spiska Opštinskog odbora SUBNOR-a Ub.'
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/8-crnogorska.pdf',
        brigade_code=38,
        output_path='website/public/8-crnogorska-soldiers.json',
        start_page=1,
        end_page=33,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(rf'^[{U}][{U}\-]*{MARK}'),
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        post_fn=post,
    )
