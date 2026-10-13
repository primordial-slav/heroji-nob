"""
Reference book: Zbornik narodnih heroja Jugoslavije (Beograd, 1957), in the Digital library of Poreklo
(biblioteka.poreklo.rs, collection of biographies; for members only).

Not a unit's book: the heroes it portrays served in units all over the site, so its entries are not records of their
own but references added to the hero's record (`reference` corrections, see scripts/match_references.py). Each
portrait opens with a heading and a summary, then the life story:

    AKSENTIJEVIĆ Danila VLADA
    Rođen 1916 u Grabovcu, Obrenovac. Srbija. Student tehnike. Član KPJ od pre rata. U NOB stupio 1941. Obešen u
    proleće 1942. Za narodnog heroja proglašen 14-XII-1949.

The entry kept is the heading and the summary, as printed (the OCR's look-alike letters and digits read back); the life
story stays in the book, a click away in the library's viewer. The full OCR of the book is cached in
data-extraction/.cache/poreklo/zbornik-heroja-1957.json (23 MB, not in git); this script writes the entries to
data-extraction/poreklo/zbornik-heroja-1957-entries.json.

Usage: python data-extraction/parse_zbornik_heroja.py
"""
import json
import re
import sys
from pathlib import Path

from poreklo_text import name_counts, page_lines, printed_page, restore_diacritics, viewer_url

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache' / 'poreklo' / 'zbornik-heroja-1957.json'
OUT = HERE / 'poreklo' / 'zbornik-heroja-1957-entries.json'
PAGES = range(26, 1005)
PREFIX = '9001'                                  # reference IDs: 9001 + the hero's number in the book's order
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROMAN = 'IVXL'
LOOKALIKE = str.maketrans({'и': 'u', 'Х': 'X', 'х': 'x', 'І': 'I', 'М': 'M', 'В': 'B', 'А': 'A', 'Е': 'E', 'О': 'O',
                           'Р': 'P', 'С': 'C', 'Т': 'T', 'Н': 'H', 'К': 'K', 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p',
                           'с': 'c', 'у': 'y', 'ј': 'j', 'Ј': 'J'})
SUMMARY_START = re.compile(r'^(?:Ro[dđ]en|R0[dđ]en|Rod[ej]n)a?\b')


def clean_summary(text: str) -> str:
    """The summary as printed: look-alike letters, digits read as letters in dates ("20-X-I915", "1V"), words broken
    at a line's end ("Zemljo- radnik"), "naroang"/"praglašen" read back"""
    text = text.translate(LOOKALIKE)
    text = re.sub(rf'(?<=[{L}])[-—–]\s+(?=[{L}])', '', text)                      # "Zemljo- radnik"
    text = re.sub(r'(?<=\d)\s*[—–]\s*(?=[\dIVXl])|(?<=[IVX])\s*[—–]\s*(?=[\dIl])', '-', text)   # "4-1—1943"
    text = re.sub(r'(?<!\S)\](?=\d)', '1', text)                                 # "]6-VII-1913"
    # a year with letters for its ones and a gap: "I890", "I 915", "l 910", "[908", "[9/0", "19/6", "I9]4", "1 920"
    one = lambda c: '1' if c in 'Il[]/' else c
    text = re.sub(r'(?<![\d\w])([1Il\[\]])\s?([89])\s?([\dIl/\[\]])([\dIl/\[\]])(?![\d])',
                  lambda m: '1' + m.group(2) + one(m.group(3)) + one(m.group(4)), text)
    text = re.sub(r'\b(19\d) (\d)\b', r'\1\2', text)                             # "195 1"
    text = re.sub(r'(?<=\d)-\s+(?=[IVX\d])|(?<=[IVX\d])\s+-(?=[\dIV])', '-', text)   # "3- V-1920"
    text = re.sub(r'\btf\b', 'u', text)                                          # "tf Livnu"
    text = re.sub(r'\bheroia\b', 'heroja', text)
    # the OCR's usual slips in the summaries: "Clan KPJod", "Strelian", "Zemlioradnik", "radni/<", "Rodena"
    for wrong, right in ((r'\bClan\b', 'Član'), (r'\bclan\b', 'član'), (r'\bKPJod\b', 'KPJ od'), (r'\bStrel[il]an', 'Streljan'),
                         (r'\bZemlioradn', 'Zemljoradn'), (r'\bRoden(a?)\b', r'Rođen\1'), (r'\bPaginu', 'Poginu'),
                         (r'\bP0ginu', 'Poginu'), (r'\bPo-\s*ginu', 'Poginu')):
        text = re.sub(wrong, right, text)
    text = re.sub(r'(?<=[a-zčćžšđ])/[<c](?=[\s.,;]|$)', 'k', text)               # "radni/<", "Šumski radni/c"
    text = re.sub(r'(?<=-)([IVXl1]+)(?=-\d)', lambda m: m.group(1).replace('l', 'I').replace('1', 'I'), text)   # "-l1-"
    text = re.sub(r'\bnaro(?:ang|dn0g|d/mg)\b', 'narodnog', text)
    text = re.sub(r'\bpr[ao]g/?l?a[sš]en(a?)\b', r'proglašen\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_head(head: str) -> dict | None:
    """"BALETIĆ Lazara MARKO", "BAJIĆ B. SLOBODAN _ PAJA", "ACEVA Dona VERA — DOSTA", "ACEV MIRČE" """
    head = head.translate(LOOKALIKE).replace("'", '').replace('"', '')
    head = re.sub(r'(?<=[A-ZČĆŽŠĐ])l(?=[A-ZČĆŽŠĐ])', 'I', head)                 # "MlRČE"
    head = re.sub(r'(?<=[A-ZČĆŽŠĐ])0(?=[A-ZČĆŽŠĐ]|\b)', 'O', head)              # "KI R0"
    # a heading the OCR set on the last line of the bio before: "... u četničku zasedu. BAJIĆ Vasilija BUDO"
    tail = re.search(r'(?:^|[.!?»“”"<>]\s+)((?:[A-ZČĆŽŠĐ]{2,}[A-ZČĆŽŠĐ ]*)(?:\s+\S+){1,5})$', head.strip())
    if tail and tail.start(1) > 0:
        head = tail.group(1)
    tokens = [t for t in re.split(r'\s+', head.strip(' ._—–-')) if t and not re.fullmatch(r'[_—–-]+', t)]
    if len(tokens) < 2 or not re.fullmatch(rf'[{U}][{U}-]*', tokens[0]):
        return None
    caps = lambda t: bool(re.fullmatch(rf'[{U}][{U}-]*', t))
    is_father = lambda t: bool(re.fullmatch(rf'[{U}][{L}]+|[{U}{L}]\.', t))
    fi = next((i for i, t in enumerate(tokens) if is_father(t)), None)

    def joined(parts):
        """caps words the OCR split ("BIZJ AK", "BA KOVIĆ", "KI RO"): a fragment of up to three letters joins its
        neighbour"""
        out = []
        for p in parts:
            if out and (len(p) <= 3 or len(out[-1]) <= 3) and caps(p) and caps(out[-1]):
                out[-1] += p
            else:
                out.append(p)
        return out
    if fi is not None:
        surname = joined([t for t in tokens[:fi] if caps(t)])
        rest = [t for t in tokens[fi + 1:] if caps(t)]
        rest = joined(rest)
        if len(surname) != 1 or not rest:
            return None
        return {'last': surname[0], 'father': tokens[fi], 'given': rest[0], 'nick': ' '.join(rest[1:])}
    words = [t for t in tokens if caps(t)]
    if len(words) != len(tokens) or len(words) < 2:
        return None
    return {'last': words[0], 'father': '', 'given': words[1], 'nick': ' '.join(words[2:])}


def main():
    book = json.load(open(CACHE, encoding='utf-8'))
    entries, missed = [], []
    for page in PAGES:
        lines = page_lines(book, page)[0]
        for i, line in enumerate(lines):
            if not SUMMARY_START.match(line.text.strip()) or not i:
                continue
            head = lines[i - 1].text.strip()
            parsed = parse_head(head)
            if not parsed and i > 1:                                  # a heading over two lines
                parsed = parse_head(lines[i - 2].text.strip() + ' ' + head)
                head = lines[i - 2].text.strip() + ' ' + head
            if not parsed:
                missed.append((page, head))
                continue
            summary = [line.text.strip()]
            for nxt in lines[i + 1:i + 14]:
                t = nxt.text.strip()
                # the life story begins with its first word in capitals ("DO punoletstva", "ODRASTAO je")
                if re.match(rf'^[{U}]{{2,}}\s+[{L}]', t) and not re.match(r'^(?:KPJ|NOB|NOV|SKOJ|JNA|CK|NR|FNRJ)\b', t):
                    break
                summary.append(t)
                if re.search(r'progla[sš]en[a]?\b', ' '.join(summary)) and re.search(r'\d\s*\.?\s*$', t):
                    break
            text = clean_summary(' '.join(summary))
            end = re.search(r'progla[sš]ena?\s+(?:je\s+)?[^.]*?\d{4}\s*\.?', text)
            if end:
                text = text[:end.end()].rstrip(' .') + '.'
            entries.append({'page': page, 'head': head, **parsed, 'summary': text})
    out = []
    # the capitals lose their diacritics ("DURIĆ", "CETKOVIĆ"): the spelling the units' records use
    all_names = [{'last_name': e['last'].title(), 'first_name': e['given'].title(),
                  'middle_name': e['father'] if not e['father'].endswith('.') else ''} for e in entries]
    restore_diacritics(all_names, name_counts(''))
    for n, (e, names) in enumerate(zip(entries, all_names), 1):
        last, given = names['last_name'], names['first_name']
        father = names['middle_name'] or e['father'].upper()
        name = ' '.join(x for x in (last, father, given) if x)
        born = re.search(r'Ro[dđ]ena?\s+[^.]{0,14}?(?P<y>1[89]\d\d)\.?\s*[“"\'}:\[]*\s*(?:u|na)\s*(?:selu\s+|mestu\s+)?(?P<p>[^.]+)', e['summary'])
        out.append({
            'soldier_id': f'{PREFIX}{n:06d}', 'name': name + (f" ({e['nick'].title()})" if e['nick'] else ''),
            'last_name': last, 'fathers_name': father, 'first_name': given, 'nick': e['nick'].title(),
            'birth_year': born.group('y') if born else '', 'born_in': born.group('p').strip() if born else '',
            'additional_info': e['summary'], 'source_url': viewer_url(book, e['page']),
            'source_page': printed_page(book, e['page']),
        })
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(out)} heroes; {len(missed)} headings not read: {missed[:15]}')


if __name__ == '__main__':
    main()
