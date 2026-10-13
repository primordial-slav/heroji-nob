"""
Parser: 13. krajiška brigada "Garava" (brigade code 124).

Source: Milan N. Zorić, "Trinaesta krajiška brigada" (znaci.org 00001/263), the chapter "Prilozi" (263_7.pdf →
        website/public/pdfs/13-krajiska.pdf, book pp. 364-404), two lists:
    "Spisak boraca i rukovodilaca koji su bili u brigadi u avgustu i septembru 1943." (PDF pp. 2-24): everyone in the
        brigade in its first two months (it was proclaimed from the Ribnički NOP odred on 23 August 1943), with village,
        municipality and duty, and how each of those who fell died and where he lies;
    "Spisak članova KPJ partijske organizacije 13. krajiške udarne brigade od maja 1945." (pp. 25-41): its party
        members in May 1945, when each joined the party, duty, how often wounded. Mostly the men of the first list:
        find_source_duplicates.py merges them (LISTS).
One column, Latin, each entry hanging (its first line some 26pt left of the lines under it), the name in capitals,
surname first, no father:
    ADAMOVIČ ĐURO iz Vranovine, Krnjeuša, Bosanski Petrovac, borac, poginuo u Jagarama 24. 11. 1944. godine,
    sahranjen iznad Karanovca kod Banjaluke.
The scan reads Ć as Č ("ADAMOVIČ", "AĆIMOVIČ") and I as l ("ADZlĆ"), and loses carons ("BABIC"): the corpus's
spelling wins where it knows the name.
"""
import re
import unicodedata

from _parser_scaffold import _fold, _load_name_reference, _record, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]+'
LISTS = [(2, 24), (25, 41)]
_left: dict = {}


def plain_caps(t: str) -> str:
    t = ''.join(c if c in 'čćžšđČĆŽŠĐ' else unicodedata.normalize('NFD', c)[0] for c in t)
    t = re.sub(rf'(?<=[{U}])[1l](?=[{U}])', 'I', t)
    t = re.sub(rf'(?<![\w{L}])[l1](?=[{U}]{{2}})', 'I', t)                    # "lVANIĆ", "1LIĆ"
    return re.sub(rf'(?<=[{U}])(?:ie|\^)(?=\s)', 'IĆ', t)                       # "BOGOJEVie"


def page_number(t: str) -> bool:
    return bool(re.fullmatch(r'[\d\W]{1,5}', t)) or bool(re.fullmatch(r'[\d\W]*\d+\.?\s*13\.\s*[Kk]rajiška brigada[\s\d\W]*', t))


def heading(t: str) -> bool:
    return bool(re.match(r'^(?:SPISAK|BRIGADI U AVGUSTU|13\. KRAJIŠKE UDARNE|OD MAJA 1945)', t))


def measure(lines: list[dict]) -> None:
    """Where a page's entries start: the leftmost line that looks like one ("SURNAME GIVEN iz"), so a speck the scan
    read as a word left of the margin ("IhmIIW", p. 28) doesn't move it"""
    for ln in lines:
        t = plain_caps(ln['text'].strip())
        if re.match(rf'^[{U}]{{2,}}\S*\s+[{U}]{{2,}}', t) and not heading(t):
            _left[ln['page']] = min(_left.get(ln['page'], 10 ** 6), ln['x'])


def keep(ln: dict) -> bool:
    t = plain_caps(re.sub(r'^[•·\s"\']+', '', ln['text'].strip()))
    if page_number(t) or heading(t) or not t:
        return False
    new = ln['x'] < _left[ln['page']] + 12 and bool(re.match(rf'^[{U}]', t))
    ln['text'] = ('§x§ ' if new else '') + t
    return True


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).strip()
    # the name ends where "iz <village>" starts ("iZ" in the scan), else at its comma
    end = re.search(r'\s+(?=[iI][zZ]\s)|,', text)
    head, info = (text[:end.start()], text[end.end():].strip()) if end else (text, '')
    info = re.sub(r'^iZ\b', 'iz', info)
    words = [w.strip('.,;:') for w in head.split()]
    words = [w.upper() if sum(c.isupper() for c in w) >= 0.7 * len(w) else w for w in words if w]
    while words and not re.fullmatch(CAPS, words[0]):                       # a speck read as a word ("IhmIIW")
        words.pop(0)
    nick = ''
    if len(words) > 2 and not re.fullmatch(CAPS, words[-1]):                # "PERO Pekan": a nickname in small letters
        nick = words.pop()
    # a name the scan spaced apart: "TOD OR" = Todor, "ST ANI VUK" = Stanivuk, "MAC ANO VIĆ" = Macanović
    while len(words) > 2:
        i = next((i for i in range(len(words) - 1)
                  if len(words[i]) <= 3 or len(words[i + 1]) <= 3 or re.fullmatch(r'O?V?IĆ', words[i + 1])), None)
        if i is None:
            break
        words[i:i + 2] = [words[i] + words[i + 1]]
    if len(words) > 2:                                                      # "ĐAKOVIĆ NIKOLA NINARA": a nickname
        nick, words = ' '.join(words[2:]).title(), words[:2]
    last, given = (words[:-1], words[-1:]) if len(words) > 1 else (words, [])
    info = re.split(r'(?<=[.\w])\s*\d\)', info)[0]                            # the editor's footnote under p. 24
    info = info.rstrip(' .;') + '.' if info else ''
    if nick:
        info = f'zvani {nick}; {info}'
    return _record(' '.join(last), ' '.join(given), '', info)


def post(soldiers: list[dict]) -> list[dict]:
    """The scan's Č for Ć at a surname's end ("ADAMOVIČ"): -ić unless the corpus prints the name with -ič more often"""
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    ref = _load_name_reference()['last_name']
    for s in soldiers:
        v = s['last_name']
        if v.endswith('ič'):
            cands = ref.get(_fold(v).lower(), {})
            if cands.get(v, 0) <= cands.get(v[:-1] + 'ć', 0) or not cands:
                s['last_name'] = v[:-1] + 'ć'
                s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers



if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/13-krajiska.pdf',
        brigade_code=124,
        output_path='website/public/13-krajiska-soldiers.json',
        start_page=2,
        end_page=41,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        prepare_fn=measure,
        post_fn=post,
    )
