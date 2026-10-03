"""
Parser: Mačvanski (Podrinski) NOP odred (brigade code 109).

Source: Dragoslav Parmaković, "Mačvanski partizanski odred", the appendix "Spisak boraca Mačvanskog (Podrinskog) NOP
        odreda", published by znaci.org only as a web page: https://znaci.org/00001/48_102.htm  →
        data-extraction/sources/macvanski-odred.htm (a saved copy, Word markup stripped). Only its first part is there,
        July 1941 - March 1942 (the second, 1943-44, is "u pripremi"). Cyrillic, 1,629 numbered entries, by the place
        the fighters joined from, under its district ("ЈАДРАНСКИ СРЕЗ", "Бања Ковиљача"), then those from other
        detachments, of unknown residence, and the officers who came over from the Cer chetnik detachment:
            2) Машановић Здравко - р. 1917, Бапска Нова, избеглица, радник, сиромашан; породица: мајка и сестра;
            ступио септембра 1941, чета Д. Бајалице и Лозничка, пушкамитраљезац; члан КПЈ; ...
The name in bold italics (surname, given name, a nickname: "Комненовић Никола Академац"), then the bio. A few entries
lost their number on the web page. Each record's text starts with its heading ("Banja Koviljača (Jadranski srez):").
There is no scan: the records carry `source_url` instead of a PDF position.
"""
import html
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, cyrillic_to_latin, repair_cyrillic_ocr, run_parser

SOURCE = 'data-extraction/sources/macvanski-odred.htm'
SOURCE_URL = 'https://znaci.org/00001/48_102.htm'
MARK = '⁣'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
INTRO = ('ПРВИ ДЕО', 'Овај део списка', 'Чета је 10. 9. 1941.')                # the list's title and notes, no headings


def read_entries(path: str, start: int, end: int | None) -> list[dict]:
    """One line per entry, its text led by the heading it stands under."""
    paras = re.findall(r'<p>(.*?)</p>', Path(path).read_text(encoding='utf-8'), re.S)
    out, district, place = [], '', ''
    for p in paras:
        text = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', p))).strip()
        if not text or text.startswith(INTRO):
            continue
        bold = re.match(r'\s*<b>\s*<i>(.*?)</i>\s*</b>(.*)$', p, re.S)
        numbered = re.match(r'^\d{1,4}\s*\)', text)
        if not bold and not numbered and not re.search(r'\s-\s*р\.|\s-\s', text):
            if text == text.upper() or text.startswith('Из ') or text in ('Семберијска чета',) or text.startswith(('Непознато', 'Прешли')):
                district, place = text, ''                                   # "ЈАДРАНСКИ СРЕЗ", "ИЗ ВАЉЕВСКОГ ПО", "Из групе комуниста"
            else:
                place = text                                                 # "Бања Ковиљача"
            continue
        out.append({'text': MARK + f'{place}§{district}§' + re.sub(r'^\d{1,4}\s*\)\s*', '', text), 'x': 0, 'y': float(len(out)), 'page': 1})
    return out


_first: Counter = Counter()


def corpus() -> None:
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != 'macvanski-odred-soldiers.json':
            _first.update(s['first_name'] for s in json.loads(f.read_text(encoding='utf-8')))


def fix_ocr(w: str) -> str:
    """The web page's OCR: З read as 3 ("3minjak"), л as I ("SaIaš", "PoIje")."""
    w = re.sub(r'(?<![\w])3(?=[a-zčćžšđ])', 'Z', w)
    return re.sub(r'(?<=[a-zčćžšđ])I(?=[a-zčćžšđ])', 'l', w)


def fix_given(soldiers: list[dict]) -> list[dict]:
    """A given name the corpus doesn't know takes the best-known spelling one usual misread gives ("Ilmja" = Ilija,
    "Sreton" = Sreten); parse_1_dalmatinska's rule."""
    subs = [('n', 'u'), ('u', 'n'), ('rr', 'n'), ('ir', 'n'), ('r', 'n'), ('rn', 'm'), ('m', 'rn'), ('n', 'h'), ('h', 'n'),
            ('c', 'e'), ('e', 'c'), ('i', 'l'), ('l', 'i'), ('o', 'e'), ('e', 'o'), ('o', 'a'), ('a', 'o'), ('t', 'l'), ('mj', 'ij')]
    for s in soldiers:
        g = s['first_name']
        if not g or _first[g] >= 2:
            continue
        cands = {g[:m.start()] + b + g[m.end():] for a, b in subs for m in re.finditer(re.escape(a), g)}
        best = max(cands, key=lambda c: _first[c], default=None)
        if best and _first[best] >= 10:
            s['first_name'] = best
            s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def heading(place: str, district: str) -> str:
    d = district.strip()
    if d == d.upper():                                                       # "JADRANSKI SREZ" = Jadranski srez,
        d = re.sub(r'\bpo$', 'PO', d.capitalize())                           # "IZ VALJEVSKOG PO" = Iz Valjevskog PO
        d = re.sub(r'^Iz (\w)', lambda m: 'Iz ' + m.group(1).upper(), d)
    if place and d:
        return f'{place} ({d[0].lower() + d[1:] if d.startswith("Iz ") else d})'
    return place or d


def parse_entry(text: str) -> dict:
    text = text.replace(MARK, '')
    place, district, body = text.split('§', 2)
    place, district = fix_ocr(place), fix_ocr(district)
    m = re.match(r'^(.*?)\s+[-–]\s+(.*)$', body)
    head, bio = (m.group(1), m.group(2)) if m else (body, '')
    head = re.sub(r'(?<=\w)—(?=\w)', '-', head)                              # "Dukić—Bogdanović": one surname
    head = re.sub(r'\s+(?:—|zv\.)\s+', ' ', head).replace(',', ' ').replace('"', '').replace('„', '').replace('“', '')
    dr = re.search(r'\s[Dd]r\.?(?=\s)', head)
    if dr:
        head = head[:dr.start()] + head[dr.end():]                           # "Janković dr Živorad Žika"
    words = [fix_ocr(w) for w in head.split()]
    if (len(words) >= 3 and re.search(r'(?:ić|ov)$', words[1]) and _first[words[2]] >= 3 and _first[words[1]] < 3):
        words = [words[0] + ' ' + words[1]] + words[2:]                      # "Ilić Bibić Milutin": two surnames
    last, given, nick = words[0], (words[1].rstrip('.') if len(words) > 1 else ''), words[2:]
    notes = [heading(place, district)] if heading(place, district) else []
    lead = (': ' if notes and (bio.strip() or nick or dr) else '')
    pre = ('dr.; ' if dr else '') + (('zvani ' + ' '.join(nick) + '; ') if nick else '')
    rec = _record(last, given, '', (notes[0] if notes else '') + lead + pre + bio.strip())
    norm = re.sub(r'\br[,\s]\s*(?=1[89]\d\d)', 'r. ', bio)                   # "r, 1898": the full stop misread
    y = re.search(r'\br\.\s*(1[89]\d\d)\b', norm)
    rec['birth_year'] = y.group(1) if y else ''
    b = re.search(rf'\br\.\s*(?:\d{{1,2}}\.\s*\d{{1,2}}\.\s*)?1[89]\d\d[.,]?\s*,\s*([{U}][{L}]+(?:\s+[{U}][{L}]+)?)(?=\s*[,;.]|\s*$)', norm)
    occupation = ''
    for seg in re.split(r',', norm.split(';')[0].split(':')[0])[:7]:         # "r. 1920, osnovna škola, zemljoradnik; ..."
        seg = re.sub(r'\s+\d[\d,]*\s*(?:ha|kj|ari)\b.*$', '', seg.strip().rstrip('.'))   # "zemljoradnik 3 ha"
        if (not seg or re.match(rf'^(?:r\.|rođen|[{U}0-9(])', seg) or re.search(r'škol|gimnazij|nepismen|samouk|fakultet|matur|izbe[gt]lic|siromaš|imovn|\bha\b|ž\. u', seg)
                or re.fullmatch(r'(?:samac|oženjen|neoženjen|udata)', seg)):
            continue                                                         # the birth, a place, the schooling, "izbeglica"
        if re.fullmatch(rf'[{L}]+(?:[ -][{L}]+){{0,2}}', seg):
            occupation = seg                                                 # the first trade after them
        break
    if occupation:
        rec['occupation'] = occupation
    if b and not re.match(r'(?:Srbin|Srpkinja|Hrvat|Hrvatica|Musliman|Muslimanka|Jevrej|Jevrejin|Jevrejka|Slovenac|Rus|Mađar|Nemac|Ciganin)\b', b.group(1)):
        rec['birth_place'] = b.group(1)                                      # "р. 1917, Бапска Нова"
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        for k in ('pdf_page', 'pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = SOURCE_URL
    return fix_given(repair_cyrillic_ocr(soldiers))


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path=SOURCE,
        brigade_code=109,
        output_path='website/public/macvanski-odred-soldiers.json',
        start_page=1,
        end_page=1,
        script='cyrillic',
        extract_fn=read_entries,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
