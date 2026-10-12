"""
Parser: Prvi proleterski bataljon Hrvatske (brigade code 120).

Source: Bogdan Mamula, Rudi Bašić, Branko Vurdelja, Dušan Pekić, "Prvi proleterski bataljon Hrvatske" (Historijski arhiv
        u Karlovcu, 1983), in the Digital library of Poreklo (biblioteka.poreklo.rs, collection "Drugi svetski rat"; for
        members only). The library's OCR text of the list pages is kept in data-extraction/poreklo/1-proleterski-bataljon.json
        (poreklo_text.py). "Spisak boraca Prvog proleterskog bataljona Hrvatske" (scan pages 286-301, book pp. 262-277):
        the battalion from its formation in Korenica on 7 May 1942 until it went into the 13. proleterska brigada. The
        editors built it on the battalion's register of 5 July 1942 (227 fighters, Vojnoistorijski institut, K 229) and
        on survivors' memory for those who came later, and say it is not complete. One entry a paragraph, the first line
        flush and the others indented:
            ANTIC Andrije ANDRIJA, 1914, Selce, Crikvenica. Poginuo 21. 1. 1943. u Krašiću, sahranjen u Sošicama.
            ANTIČ Stipe MILJENKO ŠIŠE, 1913, Šepurina, Šibenik.        (a nickname after the given name)
        The capitals lose or swap their diacritics (ANTIC, ANTIČ = Antić): restored from the other units' spellings.

There is no scan on the site: records carry `source_url` (the page in the library's viewer) and `source_page`.
"""
import re

from _parser_scaffold import _record, run_parser
from poreklo_text import load, name_counts, page_lines, printed_page, restore_diacritics, viewer_url

BOOK = load('1-proleterski-bataljon.json')
PAGES = range(286, 302)
MARK = 'ꙮ '                                          # starts an entry (a letter: the scaffold strips leading marks)
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LOOKALIKE = str.maketrans({'Ј': 'J', 'В': 'B', 'А': 'A', 'Е': 'E', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Н': 'H',
                           'К': 'K', 'М': 'M', 'Х': 'X'})
# the name: SURNAME, the father in the genitive, GIVEN, a NICKNAME in capitals
# Names the OCR garbled, read from the page scans: (scan page, the OCR line's start) -> the line's start as printed
SCAN = {
    (288, 'ШЈМЕТА'): 'BUNETA',                       # an ink blot on the B; BUNETA Mate GRGA is the line before
    (289, 'СОЦ STANK_Q'): 'ČOVIĆ STANKO',
    (289, "DIOMATRIC'"): 'DIOMATRIĆ',
    (294, 'Q_MAQIČ'): 'MAVRIĆ',                      # after MATIJEVIĆ MILE, a line of its own
    (295, 'PERKOV Sime 1080'): 'PERKOV Šime JOSO',
    (297, 'SMOLIČ'): 'SMOLIĆ',                       # printed without a given name
}
# Specks the scan left after an entry's text: "Kozjan, T. Korenica. ja», 17 „ga../«C,— џ–"
TAIL_JUNK = {(289, 'ČOVIĆ STANKO'): 'ČOVIĆ STANKO, Kozjan, T. Korenica.'}
# a second entry the OCR set on the line before it: "... Poginuo 1943. u Srbiji. PILEPIĆ Ivana MELHIOR DUPIN, 1922, ..."
SECOND_ENTRY = re.compile(r'(?<=\.)\s+(?=[A-ZČĆŽŠĐ]{3,}\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]{2,}[^,]{0,20},\s*1[89]\d\d)')

HEAD = re.compile(rf'^(?P<last>[{U}][{U}\-]+(?:\s[{U}]{{1,2}}(?=[{U}\s]))?)\s+(?:(?P<father>[{U}][{L}]+(?:\s[{U}][{L}]+)?)\s+)?'
                  rf'(?P<given>[{U}][{U}]*(?:\s?J\s?[{U}]+)?)(?:\s+(?P<nick>[{U}][{U}]+(?:\s[{U}][{U}]+)?))?\s*(?:,|\.|$|(?=\s1[89]\d\d))')


def read_lines(_path: str, _start: int, _end) -> list[dict]:
    out, used = [], set()
    for page in PAGES:
        lines = page_lines(BOOK, page)[0]
        left = min((l.x0 for l in lines), default=0)
        for line in lines:
            raw = line.text
            for (pg, ocr), printed in SCAN.items():
                if pg == page and raw.startswith(ocr):
                    raw, _ = printed + raw[len(ocr):], used.add((pg, ocr))
                    raw = TAIL_JUNK.get((pg, printed), raw)
            text = re.sub(r'^[^\w]+', '', raw.translate(LOOKALIKE)).strip()
            text = re.sub(r'\s*\d+\s+Prvi prolet\. bataljon\s+\d+\s*$', '', text)   # the page's foot, set on a line
            text = re.sub(rf'(?<=[{U}])([čćžšđ])(?=[{U}]|\b)', lambda m: m.group(1).upper(), text)   # "FUćAK", "PILEPIć"
            text = re.sub(rf'(?<![{U}\w])J (?=[{U}]{{2,}})', 'J', text)     # "Ј OVICA", "J UKIC"
            text = re.sub(rf'(?<=[{U}])l(?=[{U}])', 'I', text)                # "PlLEPIĆ": a lowercase l for I
            if not text or re.fullmatch(r'[\d\s]+', text) or text.startswith(('S P I S A K', 'BORACA PRVOG')):
                continue
            if page == 301 and text.startswith(('Napomena', 'U radu na prikupljanju')):
                break                                                        # the editors' note and thanks after the list
            # the first line is flush; a few first lines the scan set in are known by the name and the year after it
            start = ((line.x0 - left < 60 and bool(re.match(rf'^[{U}]{{2,}}', text)))
                     or bool(re.match(rf'^[{U}Ш]{{3,}}(?:-[{U}]+)?\s+(?:[{U}][{L}]+\s+)?[{U}]{{2,}}\b', text)))
            parts = SECOND_ENTRY.split(text)
            for k, part in enumerate(parts):
                out.append({'text': (MARK if start or k else '') + part, 'x': line.x0, 'y': line.top, 'page': page})
    assert used == set(SCAN), f'readings not used: {set(SCAN) - used}'
    return out


def parse_entry(text: str) -> dict:
    text = text.replace(MARK, '').strip()
    text = re.sub(r'(?<=[a-zčćžšđ])[—–-]\s+(?=[a-zčćžšđ])', '', text)       # "NOR— u", words broken at a line's end
    m = HEAD.match(text)
    if not m:
        only = re.match(rf'^([{U}][{U}\-]+),\s*(.*)$', text)               # "SMOLIĆ, Kistanje, Knin": no given name
        return _record(only.group(1), '', '', only.group(2)) if only else {}
    last = re.sub(r'\s', '', m.group('last'))                                # "ZJ ACA"
    given = re.sub(r'\s', '', m.group('given'))                              # "VJ ERKO", "J OVICA"
    info = text[m.end():].strip()
    if m.group('nick'):
        info = f"zvani {m.group('nick').title()}; {info}"
    rec = _record(last, given, m.group('father') or '', info)
    y = re.match(r'(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        page = s.pop('pdf_page')
        for k in ('pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = viewer_url(BOOK, page)
        s['source_page'] = printed_page(BOOK, page)
    counts = name_counts('1-proleterski-bataljon-soldiers.json')
    printed = {id(s): s['last_name'] for s in soldiers}
    n = restore_diacritics(soldiers, counts)
    # A Croatian book whose OCR reads the capital Ć as Č ("SMOLIČ", "MAVRIČ" for SMOLIĆ, MAVRIĆ): a surname printed with
    # -ic, -ič or -ić ends in -ić when another unit spells it so, though the Slovene -ič be more common there
    for s in soldiers:
        was = printed[id(s)]
        if re.search(r'i[cčć]$', was, re.I):
            ic = s['last_name'][:-1] + 'ć'
            if s['last_name'] != ic and counts['last_name'][ic] > 0:
                s['last_name'] = ic
                n += 1
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
    print(f'  diacritics restored in {n} names')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='poreklo/1-proleterski-bataljon.json',
        brigade_code=120,
        output_path='website/public/1-proleterski-bataljon-soldiers.json',
        extract_fn=read_lines,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
