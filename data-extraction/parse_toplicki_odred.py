"""
Parser: Toplički NOP odred (brigade code 93).

Source: Dragoljub Dinić Mića, "Toplički narodnooslobodilački partizanski odred" (znaci.org 00001/280_12.pdf, its pages
        1-43, book pp. 302-344)  →  website/public/pdfs/toplicki-odred.pdf. Cyrillic, one column, an entry set apart
        from the next by a wider line gap, three lists:
    pp. 1-3     Prilog 1, "Borci Topličkog NOP odreda na dan formiranja, 3. avgusta 1941. godine", the name first:
                    BOŽIDAR ĐORĐEVIĆ RELJA, rođen 1922. godine u Prokuplju, obućarski radnik. ...
    pp. 4-31    Prilog 2, "Spisak poginulih i umrlih boraca i rukovodilaca Topličkog NOP odreda", by letter, "the
                surname, the name and the nickname":
                    ANĐELKOVIĆ STOJADIN DINE, 1917, Gornja Svarča, Prokuplje, zemljoradnik. U Odredu od jeseni 1941, ...
    pp. 32-43   Prilog 3, "Narodni heroji Jugoslavije koji su se borili ili poginuli u Topličkom NOP odredu", the name
                first, beside their photographs.
The nickname (the third name, or the names after a dash: "VELJKOVIĆ MIODRAG - VELJKO KARAMAN") goes to the entry as
"zvani X". Fighters the author knew only by one name or a nickname ("BRICA", "ŠALJAPIN (nepoznato prezime i ime)")
are kept under that name. The parser sets the birthplace: the places after the year, or the place after "u" in the
nominative the other units know ("u Prokuplju" = Prokuplje).
"""
import re
from collections import Counter
from functools import lru_cache
from itertools import product

from _parser_scaffold import _record, death_type_from_text, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LISTS = ((32, 3), (4, 2), (1, 1))                                            # first page of each list, list number
NOT_NAMES = r'(?:KPJ|SKOJ|NOP|NOB|NOR|JNA|SRS|SFRJ|ASNOS|RK|MK|OK|PK|CK|SPISAK|BORCI|FORMIRANJA|NARODNI|SE\s+BORILI|NOP\s+ODRED|I\s+RUKOVODILACA)'
FIXES = {'RAT^O': 'RATKO', 'JUJTIJANA': 'JULIJANA', 'MAIIĆ': 'MANIĆ', 'ARANAĐELOVIĆ': 'ARANĐELOVIĆ',   # misreadings (the order tells)
         'saobr^Ljajnoj': 'saobraćajnoj', 'tej>enU': 'terenu', 'otišZ0': 'otišao', 'godin^-': 'godine.', 'godin^': 'godine.',
         'četš#a': 'četnika', 'Prokuplje>': 'Prokuplje,', 'sajednomčetomTopličkog': 'sa jednom četom Topličkog',
         'narodnoghe': 'narodnog he', 'Jugoslavijeproglašenje9.': 'Jugoslavije proglašen je 9.', 'rođsn': 'rođen'}
ONE_NAME = {'BOBI', 'BRICA', 'ŽIKA', 'MEDICINAR', 'MICKO', 'MOMIR', 'ŠALJAPIN', 'SLAVKO'}   # a name or nickname, no surname
SPECIAL = {'IVAN SLOVENAC': ('', 'Ivan', 'Slovenac'), 'MILAN - MAKEDONAC': ('', 'Milan', 'Makedonac'),
           'ČEH GAVRO': ('', 'Gavro', 'Čeh'), 'MIODRAG DRAGI STAMENKOVIĆ SRBA': ('STAMENKOVIĆ', 'Miodrag', 'Dragi Srba')}
LOCATIVE = {'Blacu': 'Blace', 'Gnjilanu': 'Gnjilane', 'Omarskom': 'Omarska', 'Kapljoj Vasi': 'Kaplja Vas',
            'Mirnici': 'Mirnica', 'Donjem Branetiću': 'Donji Branetić', 'Grguru': 'Grgur', 'Berilju': 'Berilje',
            'Kalugi': 'Kaluga', 'Božurni': 'Božurna', 'Gornjem Adrovcu': 'Gornji Adrovac'}   # places no other book prints
_prev: dict = {}
_words: Counter = Counter()


def list_of(page: int) -> int:
    return next(n for first, n in LISTS if page >= first)


def keep(ln: dict) -> bool:
    """An entry starts after a gap wider than the line spacing (or at the top of a page) with a name in capitals."""
    t = ln['text'].strip()
    prev = _prev.get(ln['page'])
    gap = ln['y'] - prev if prev is not None else 99
    _prev[ln['page']] = ln['y']
    if re.fullmatch(r'[\d\W]{1,6}|\W*\w{0,2}\W*|Prilog \d\.', t) or ln['page'] == 4 and 160 < ln['y'] < 360:
        return False                                                         # page numbers, letters, the author's note
    for bad, good in FIXES.items():
        t = t.replace(bad, good)
    t = t.replace('J1', 'L').replace('j1', 'l')                              # Л read as Ј1 ("BJ1AGOJE")
    if not _words:
        _words.update(_corpus()[1])
    t = repair_words(t, _words)
    if list_of(ln['page']) == 3 and re.search(rf'[{U}]{{2}}-$', t):
        t = t[:-1] + '­'                                                # "ANE-" / "TA-MILENA": a name broken at the line's end
    if gap > 13 and re.match(rf'^[{U}]{{3,}}\b', t) and not re.match(NOT_NAMES + r'\b', t):
        t = f'§{list_of(ln["page"])}§ ' + t
    ln['text'] = t
    return True


def head_and_rest(text: str) -> tuple[list[str], str]:
    """The name in capitals at the entry's start, and what follows it."""
    m = re.match(rf'^((?:[{U}]{{2,}}(?:-[{U}]{{2,}})*|-)(?:\s+(?:[{U}]{{2,}}(?:-[{U}]{{2,}})*|-))*)\s*[.,]?\s*', text)
    head = m.group(1).split() if m else []
    return head, text[m.end():] if m else text


def parse(text: str) -> dict:
    lst = int(text[1])
    text = text[4:].strip()
    text = re.sub(r'­\s*', '', text)
    for bad, good in FIXES.items():
        text = text.replace(bad, good)                                       # "ro-" / "đsn": split over two lines
    head, rest = head_and_rest(text)
    key = ' '.join(head)
    nick = []
    if key in SPECIAL:
        last, given, n = SPECIAL[key]
        nick = [n]
    elif len(head) == 1:
        last, given = ('', head[0].title()) if head[0] in ONE_NAME else (head[0], '')
    else:
        if '-' in head:                                                      # "MANČIĆ MILORAD - JOVA ŠOP"
            i = head.index('-')
            head, nick = head[:i], [' '.join(head[i + 1:]).title()]
        last, given, more = (head[0], head[1], head[2:]) if lst == 2 else (head[1], head[0], head[2:])
        given = given.title()
        nick = [' '.join(more).title()] * bool(more) + nick
    rec = _record(last or '§', given, '', '; '.join(['zvani ' + ' '.join(nick)] * bool(nick) + [rest] * bool(rest)))
    y = re.match(r'(1[89]\d\d)\b', rest) or re.search(r'\brođen[a]?\s+(1[89]\d\d)\b', rest)
    if y:
        rec['birth_year'] = y.group(1)
    if re.match(r'(?:1[89]\d\d[,.]\s*)?[{U}]'.format(U=U), rest) and not re.search(r'\brođen', rest[:20]):
        parts = [p.strip() for p in re.split(r',\s*|\.\s+', re.sub(r'^1[89]\d\d[,.]?\s*', '', rest))]
        places = []
        for p in parts[:3]:
            p = re.sub(r'^selo\s+', '', p)
            if re.fullmatch(rf'[{U}][{L}]+(?:[\s-]+[{U}]?[{L}]+)*', p) and not re.match(r'(?:Član|Poginu|Umr|Ubijen|Bio|U\s)', p):
                places.append(p)
            else:
                break
        if places:
            rec['birth_place'] = ', '.join(places[:2])
    else:
        b = re.search(rf'\brođen[a]?\s+(?:1[89]\d\d[.,]?\s*(?:godine\s*)?)?(?:u|kod|,)\s*(?:selu\s+)?([{U}][{L}]+(?:\s+[{U}][{L}]+)?)(?:,\s*([{U}][{L}]+(?:\s+[{U}][{L}]+)?)\s*[,.])?', rest)
        if b:
            rec['_birth'] = (b.group(1), b.group(2) or '')
    rec['death_type'] = death_type_from_text(rest) or ('poginuo' if lst == 2 else '')
    if rec['death_type'] == 'zarobljen':                                     # captured: what became of them
        fate = re.search(r'(?i)\b(streljan|obešen|umr[lo]|ubijen|poginu|spaljen|ubi[lo])', rest[rest.lower().index('zarobljen'):])
        if fate:
            word = fate.group(1).lower()
            rec['death_type'] = 'streljan' if word == 'streljan' else 'umro' if word.startswith('umr') else 'poginuo'
        elif lst == 2:
            rec['death_type'] = 'poginuo'                                    # this list holds only the dead
    d = re.search(r'\b(?:poginu|umr)\w*\b\D{0,60}?(19\d\d)', rest, re.I)
    if rec['death_type'] == 'poginuo' and d and int(d.group(1)) > 1945:
        rec['death_type'] = 'umro'                                           # "poginuo 1965. godine u saobraćajnoj nesreći"
    rec['_list'] = lst
    return rec


@lru_cache(maxsize=None)
def _corpus() -> tuple[Counter, Counter]:
    """The birthplaces the other units print, and the words of their entries (a file at a time)."""
    import json
    from pathlib import Path
    from scripts.name_utils import BRIGADE_CONFIGS
    known, words = Counter(), Counter()
    for code, cfg in BRIGADE_CONFIGS.items():
        f = Path('website/public') / cfg['json_file']
        if code != 93 and f.exists():
            for s in json.loads(f.read_text(encoding='utf-8')):
                for part in filter(None, (s.get('birth_place') or '').split(', ')):
                    known[part] += 1
                words.update(re.findall(rf'[A-Za-z{U}{L}]+', s.get('additional_info') or ''))
    return known, words


SWAPS = (('i', 'pnl'), ('n', 'pi'), ('p', 'n'), ('I', 'P'))                  # п and н read as и, and back


def repair_words(text: str, words: Counter) -> str:
    """Words the text layer misread by a letter or two ("Pogiiuo", "Irokuplju", "iosle"): the spelling the other
    books print far more often. Nicknames are left alone."""
    def edits(w: str):
        for i, ch in enumerate(w):
            for a, bs in SWAPS:
                if ch == a:
                    for b in bs:
                        yield w[:i] + b + w[i + 1:]

    def fix(m: re.Match) -> str:
        w = m.group(0)
        if len(w) < 4 or w.isupper():                                        # names in capitals are left alone
            return w
        cands = set(edits(w)) | {v for e in edits(w) for v in edits(e)}
        best = max(cands, key=lambda v: words[v], default=w)
        return best if words[best] >= max(5, 20 * words[w]) else w

    return re.sub(rf'[A-Za-z{U}{L}]+', fix, text)


def post(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    known = _corpus()[0]
    for s in soldiers:
        for part in filter(None, (s.get('birth_place') or '').split(', ')):
            known[part] += 5                                                 # the book's own nominatives: "Konjarnik, Prokuplje"

    def nominative(place: str) -> str:
        forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in place.split()))]
        forms = [f for f in forms if f != place and known[f] > known[place]]
        return max(forms, key=lambda f: known[f]) if forms else place

    for s in soldiers:
        s.pop('_list', None)
        if s['last_name'] == '§':
            s['last_name'] = ''
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['first_name']) if p)
        birth = s.pop('_birth', None)
        if birth:
            place, muni = birth
            place = LOCATIVE.get(place) or nominative(place)                 # "u selu Konjarniku" = Konjarnik
            if muni and not known[muni]:
                muni = nominative(muni) if known[nominative(muni)] else ''
            s['birth_place'] = place + (', ' + muni if muni and muni != place else '')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/toplicki-odred.pdf',
        brigade_code=93,
        output_path='website/public/toplicki-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§\d§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
