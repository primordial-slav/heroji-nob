"""
Parser: 8. kordunaška divizija (brigade code 60).

Source: "Osma kordunaška udarna divizija", Zbornik Historijskog arhiva u Karlovcu, knj. 9 (znaci.org 00003/571.pdf),
        "Popis palih boraca Osme divizije" (book p. 806 on)  →  website/public/pdfs/8-kordunaska-divizija.pdf (PDF pages
        843-950 of the book). The book's table after the list counts 2,682 fallen.
Two columns, Latin, every line flush left; the surname and the given name in capitals, the father's name (genitive)
between them; entries end without a full stop:
    ADAMOVIC Jove UROŠ, 1920, Smoljanac, Korenica, stupio u NOV 15. 5. 1942, borac 3. brig. 8. div, poginuo
    11. 4. 1944. kod Cazina
The scan loses carons and accents in the capitals ("ADAMOVIC", "BOZO") and reads I as l ("BlZlĆ"): restored from the
corpus. The brigade ("3. brig. 8. div") goes to unit_detail.
"""
import glob
import json
import re
from collections import Counter, defaultdict

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NOT_NAME = re.compile(r'^(?:NOV|VPB|NOO|JV|BJV|KPJ|SKOJ|SAUL|UBNOR|AFŽ|[IVX]+\.)\b')
# The text layer's misreadings: "Ornerà" = Omera, "MIL8" = MILE, "GALOGA2A" = GALOGAŽA, "-ie"/"^" = -IĆ
TEXT_FIXES = [('Ornerà', 'Omera'), ('Ciré', 'Ćire'), ('MIL8', 'MILE'), ('GALOGA2A', 'GALOGAŽA')]
_spell: dict = {}


def fold(w: str) -> str:
    return w.lower().translate(str.maketrans('čćšžđ', 'ccszd'))


def corpus() -> None:
    """Every spelling of a name the other units print, by its letters without diacritics."""
    for f in ('last_name', 'first_name', 'middle_name'):
        _spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if fn.replace('\\', '/').endswith('8-kordunaska-divizija-soldiers.json'):
            continue
        for s in json.load(open(fn, encoding='utf-8')):
            for f in _spell:
                if s.get(f):
                    _spell[f][fold(s[f])][s[f].upper()] += 1


def known(w: str, field: str = 'last_name') -> int:
    return sum(_spell[field].get(fold(w), {}).values())


def head_of(t: str) -> str:
    return re.split(r',|\(|\s(?=1[89]\d\d\b)', t, 1)[0]


def keep(ln: dict) -> bool:
    t = re.sub(r'^[.\s]+(?=[A-ZČĆŽŠĐ])', '', ln['text'].strip())             # ". DRVODELIĆ Pavia IMBRO"
    if re.fullmatch(r'[\d\W]{1,5}', t):
        return False
    if ln['page'] == 1 and (ln['y'] > 552 or re.match(r'^(?:Popis palih|ivizije)', t)):
        return False                                                         # the heading and the editors' footnote
    head = head_of(t)
    if (re.match(rf'^[{U}][{U}l0-9^]{{2,}}', t) and not NOT_NAME.match(t)
            and (len(head.split()) >= 2 or '(ostalo nepoznato)' in t)):
        t = '§x§ ' + t
    ln['text'] = t
    return True


def caps_word(w: str) -> str:
    w = re.sub(r'(?:ie|\^)$', 'IĆ', w)
    return w.replace('l', 'I').replace('1', 'I').replace('0', 'O')


def is_caps(w: str) -> bool:
    return bool(re.fullmatch(rf'[{U}][{U}\-]*', caps_word(w))) and not re.fullmatch(rf'[{U}][{L}]+', w)


def join_parts(parts: list[str], field: str) -> str:
    """A name the text spaced apart ("PARA VINA", "RAD AKO VIC", "F AB I JAN"): one word when the corpus knows it so,
    or when a piece is too short to be a name."""
    if len(parts) <= 1:
        return parts[0] if parts else ''
    whole = ''.join(parts)
    if (known(whole, field) or any(len(p) <= 3 for p in parts) or re.search(r'(?:VI[ĆC]|I[ĆC])$', parts[-1])):
        return whole
    if field == 'last_name' and not all(known(p) for p in parts):
        return whole                                                         # "HALA VANJA" = Halavanja
    return ('-' if field == 'last_name' else ' ').join(parts)


def unit_of(info: str) -> str:
    m = re.search(r'(?:(\d)\.\s*bat\.?,?\s*)?(\d|Muslim\w*|Karlovačk\w*|Plaščansk\w*)[\s.,]*brig', info)
    if not m:
        return ''
    b = m.group(2)
    brigade = (f'{b}. brigada' if b.isdigit() else
               {'M': 'Muslimanska brigada', 'K': 'Karlovačka brigada', 'P': 'Plaščanska brigada'}[b[0]])
    return (f'{m.group(1)}. bataljon, ' if m.group(1) else '') + brigade


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text)
    for a, b in TEXT_FIXES:
        text = text.replace(a, b)
    text = re.sub(rf'^([{U}]+ [{U}][{L}]+)([{U}]{{2,}})', r'\1 \2', text)  # "PETIĆ RadeNIKOLA."
    head = head_of(text)
    info = text[len(head):].lstrip(',').strip()
    nick = re.search(r'\s*»([^«]+)«', head)                                   # "VOJISLAV »Dušan«"
    if nick:
        head = head[:nick.start()] + head[nick.end():]
    words = [w.rstrip('.') for w in head.split()]
    lead = []
    while words and is_caps(words[0]):
        lead.append(caps_word(words.pop(0)))
    lower = []
    while words and not is_caps(words[0]):
        lower.append(words.pop(0))
    tail = [caps_word(w) for w in words]
    if tail:                                                                 # SURNAME Father GIVEN
        last, father, given = join_parts(lead, 'last_name'), ''.join(lower), join_parts(tail, 'first_name')
    elif lower:                                                              # "SKUKAN Petra Ilija": the given name in small letters
        last = join_parts(lead, 'last_name')
        father, given = (''.join(lower[:-1]), lower[-1]) if len(lower) > 1 else ('', lower[0])
    elif len(lead) == 3 and known(lead[1], 'middle_name') and not known(lead[0] + lead[1]):
        last, father, given = lead[0], lead[1].title(), lead[2]             # "RASTOVAC ILIJE MILE"
    elif len(lead) > 1:                                                      # "BAClC MIRKO": no father
        last, father, given = join_parts(lead[:-1], 'last_name'), '', lead[-1]
    else:                                                                    # "LUDVIG (ostalo nepoznato)"
        last, father, given = (lead[0] if lead else ''), '', ''
    if father.endswith('ia') and not known(father, 'middle_name') and known(father[:-2] + 'la', 'middle_name'):
        father = father[:-2] + 'la'                                          # "Pavia" = Pavla
    if nick:
        info = 'zvani ' + nick.group(1).strip().title() + '; ' + info
    rec = _record(last, given, father, info)
    by = re.match(r'^(1[89]\d\d)\b', info)
    if by:
        rec['birth_year'] = by.group(1)
    unit = unit_of(info)
    if unit:
        rec['unit_detail'] = unit
    return rec


def respell(v: str, field: str) -> str:
    """The spelling the corpus knows, when the scan lost or confused a caron ("Abdič" = Abdić, "Cubra" = Čubra)."""
    out = []
    for part in v.split('-'):
        cands = _spell[field].get(fold(part))
        if cands:
            best, n = cands.most_common(1)[0]
            if best != part.upper() and n >= 2 and n >= 3 * cands.get(part.upper(), 0):
                part = best.title() if part[:1].isupper() else best.lower()
        out.append(part)
    return '-'.join(out)


def marks(w: str) -> int:
    return sum(c in 'čćšžđČĆŠŽĐ' for c in w)


def post(soldiers: list[dict]) -> list[dict]:
    """restore_diacritics, then the corpus's spelling (respell); a "dz" the corpus doesn't know is "dž", a final "-ič"
    is "-ić"; and where this list prints one surname with and without its carons ("Balcin", "Balčin"), the carons win:
    the scan loses them, it doesn't add them."""
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    for s in soldiers:
        for f in ('last_name', 'first_name', 'middle_name'):
            v = s[f]
            if re.search('dz', v, re.I) and not _spell[f].get(fold(v), {}).get(v.upper()):
                v = re.sub('dz', 'dž', re.sub('Dz', 'Dž', v))
            if f == 'last_name' and v.endswith('ič') and not known(v, f):
                v = v[:-2] + 'ić'
            s[f] = v
    groups = defaultdict(Counter)
    for s in soldiers:
        groups[fold(s['last_name'])][s['last_name']] += 1
    for s in soldiers:
        g = groups[fold(s['last_name'])]
        if len(g) > 1:
            s['last_name'] = max(g, key=lambda v: (marks(v), g[v]))
    for s in soldiers:
        s['last_name'] = respell(s['last_name'], 'last_name')
        s['first_name'] = ' '.join(respell(w, 'first_name') for w in s['first_name'].split(' '))
        s['middle_name'] = respell(s['middle_name'], 'middle_name')
        s['fathers_name'] = s['middle_name']
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/8-kordunaska-divizija.pdf',
        brigade_code=60,
        output_path='website/public/8-kordunaska-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        col_split_x='auto',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
    )
