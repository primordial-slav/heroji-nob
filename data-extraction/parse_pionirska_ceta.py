"""
Parser: Prva naoružana pionirska partizanska četa (brigade code 121), the armed children's company of Divoselo, Lika.

Source: Gojko Matić, "Ratnici od puške manji" (kazivanje o Prvoj naoružanoj pionirskoj partizanskoj četi iz Divosela;
        SABA RH, Zagreb, 2003), in the Digital library of Poreklo (biblioteka.poreklo.rs, collection "Drugi svetski rat";
        for members only). The library's OCR text of the list pages is kept in data-extraction/poreklo/pionirska-ceta.json
        (poreklo_text.py). "Popis boraca Prve naoružane pionirske partizanske čete" (scan pages 127-134, book pp. 125-132):
        the company formed in Divoselo on 7 November 1942 (p. 20) from the boys and girls of the village, about sixty of
        whom held the line from Rizvanuša to Čitluk until the end of the war; 78 fighters, numbered, by the author, its
        commander:
            7. Matić Ise Gojko, rođen 1929. godine u Divoselu; borac od 1. 1. 1942. godine; član SKOJ-a; komandir "Prve
            naoružane pionirske partizanske čete"; ...
        Each entry ends with the fighter's life after the war, and several with a death in 1993 or 1995 in the war of the
        1990s: the parser sets the fields itself (PARSER_FIELDS), a death only for 1941-1945.
        The typeface's old-style 3 reads as 5 ("rođen 1950", "poginuo 1995"): such numbers were read from the page images.

There is no scan on the site: records carry `source_url` (the page in the library's viewer) and `source_page`.
"""
import re

from _parser_scaffold import _record, run_parser
from poreklo_text import load, name_counts, page_lines, printed_page, restore_diacritics, viewer_url

BOOK = load('pionirska-ceta.json')
PAGES = range(127, 135)
MARK = 'ꙮ '                                          # starts an entry (a letter: the scaffold strips leading marks)
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# Numbers the OCR read from the old-style 3 as 5, read from the scans: (scan page, the OCR's text) -> as printed
SCAN = {
    (132, '55. Matić Ise Vojislav-Voćan, rođen 1950.'): '53. Matić Ise Vojislav-Voćan, rođen 1930.',
    (132, '56. Jerković Jove Janko-Gojica, rođen 1950.'): '56. Jerković Jove Janko-Gojica, rođen 1930.',
    (132, '57. Obradović Pante Gojko, rođen 1950.'): '57. Obradović Pante Gojko, rođen 1930.',
    (132, '1945. godine u borbi s ustašama i Talijanima'): '1943. godine u borbi s ustašama i Talijanima',
    (132, 'od 7. 11. 1942. godine; član SKOJ-a; ranjavan; poginuo 1995.'): 'od 7. 11. 1942. godine; član SKOJ-a; ranjavan; poginuo 1993.',
    (132, 'od 7. 11. 1942. godine; član SKOJ-a; poginuo 1995. godine'): 'od 7. 11. 1942. godine; član SKOJ-a; poginuo 1993. godine',
    (132, 'Novom; borac o 15. 5. 1945. godine'): 'Novom; borac o 13. 5. 1943. godine',
    (134, '78. Vujnović Dure Vlado, rođen 1952.'): '78. Vujnović Đure Vlado, rođen 1932.',
    (131, '48. Trošte Mije Stipe'): '48. Trošelj Mije Stipe',          # Trošelj, as the book's p. 20 prints the family
    (131, '49. Vujnović Čeče Dmitar'): '49. Vujnović Ćeče Dmitar',
}
# Names the OCR ran together, or read with a lowercase J
GLUED = {'JerkovićJove': 'Jerković Jove', 'Gojko-Doko': 'Gojko-Đoko', 'NikolaJanko': 'Nikola Janko', 'PočučaJanka': 'Počuča Janka',
         'Trešnjićjove': 'Trešnjić Jove', 'BjegovićJove': 'Bjegović Jove'}
# Where they were born, in the nominative, and the municipality
PLACES = {'Divoselu': 'Divoselo, Gospić', 'Rizvanuši': 'Rizvanuša, Gospić', 'Ličkom Novom': 'Lički Novi, Gospić',
          'Lučkom Novom': 'Lički Novi, Gospić', 'Brušanima': 'Brušani, Gospić', 'Počitelju': 'Počitelj, Gospić',
          'Ličkom Osiku': 'Lički Osik, Gospić', 'Lukovom Šugarju': 'Lukovo Šugarje'}
HEAD = re.compile(rf'^(?P<last>[{U}][{L}]+)\s+(?:(?P<father>[{U}][{L}]+)\s+)?(?P<given>[{U}][{L}]+)'
                  rf'(?:-(?P<nick>[{U}][{L}]+))?,\s*(?P<rest>.*)$')
DUTIES = [(r'zamjenik komandira', 'zamjenik komandira čete'), (r'zamjenik komesara', 'zamjenik komesara čete'),
          (r'komandir “Prve', 'komandir čete'), (r'komesar “Prve', 'komesar čete'), (r'rukovodilac SKOJ', 'rukovodilac SKOJ-a'),
          (r'komandir (?:prvog|drugog|trećeg) voda', 'komandir voda'), (r'delegat (?:prvog|drugog|trećeg) voda', 'delegat voda'),
          (r'bolničarka', 'bolničarka'), (r'desetar', 'desetar'), (r'obavještajac', 'obavještajac'),
          (r'puškomitraljezac', 'puškomitraljezac'), (r'posad[ei] (?:kod|na) teško[gm] mitraljez', 'mitraljezac')]
VOD = {'prvom': '1. vod', 'prvog': '1. vod', 'drugom': '2. vod', 'drugog': '2. vod', 'trećem': '3. vod', 'trećeg': '3. vod'}


def read_lines(_path: str, _start: int, _end) -> list[dict]:
    out, used = [], set()
    for page in PAGES:
        for line in page_lines(BOOK, page)[0]:
            text = line.text.strip()
            for (pg, ocr), printed in SCAN.items():
                if pg == page and text.startswith(ocr):
                    text, _ = printed + text[len(ocr):], used.add((pg, ocr))
            if page == 134 and text.startswith('U rujnu'):
                break                                                        # the author's afterword after the list
            if not text or re.fullmatch(r'\d{1,3}', text) or text.startswith(('POPIS BORACA', 'NA OR', 'PAR TIZANSKE')):
                continue
            start = bool(re.match(rf'^\d{{1,2}}\.\s+[{U}]', text))
            out.append({'text': (MARK if start else '') + text, 'x': line.x0, 'y': line.top, 'page': page})
    assert used == set(SCAN), f'readings not used: {set(SCAN) - used}'
    return out


def parse_entry(text: str) -> dict:
    text = re.sub(r'\s+', ' ', text.replace(MARK, '')).strip()
    text = re.sub(r'(?<=[a-zčćžšđ])[—–-]\s+(?=[a-zčćžšđ])', '', text)       # "pu- škomitraljezac"
    text = re.sub(r'(?<=SKOJ)\s*[—–]\s*a\b', '-a', text)                  # "SKOJ— a"
    text = text.replace('naoružaan', 'naoružanoj').replace('N ijemcima', 'Nijemcima').replace('7. 1 1.', '7. 11.')
    for wrong, right in GLUED.items():
        text = text.replace(wrong, right)
    text = re.sub(r'^\d{1,2}\.\s+', '', text)
    m = HEAD.match(text)
    if not m:
        return {}
    info = m.group('rest').rstrip(' .,')
    if m.group('nick'):
        info = f"zvani {m.group('nick')}; {info}"
    rec = _record(m.group('last'), m.group('given'), m.group('father') or '', info)
    born = re.search(r'rođena?\s+(?:(?P<y1>19\d\d)\.\s+godine\s+u\s+(?:selu\s+)?(?P<p1>[^;,]+)|u\s+(?P<p2>[^;,]+?)\s+(?P<y2>19\d\d)\.)', info)
    if born:
        rec['birth_year'] = born.group('y1') or born.group('y2')
        place = (born.group('p1') or born.group('p2')).strip()
        rec['birth_place'] = PLACES.get(place, place)
    # a death in this war, 1941-1945, or with no year (the author: seventeen fell in battle); a death in the 1990s, or
    # after the war ("umro"), is no fall in this war
    death = re.search(r'\bpoginul?[oa]\b(?P<clause>[^;]*)', info)        # "poginuo godine 1993. u Divoselu" too
    year = re.search(r'\b(19\d\d)\b', death.group('clause')) if death else None
    if death and (not year or 1941 <= int(year.group(1)) <= 1945):
        rec['death_type'] = 'poginuo'
        if year:
            rec['death_date'] = year.group(1)
        if re.search(r'\bu\s+Divoselu\b', death.group('clause')):
            rec['death_place'] = 'Divoselo'
    elif re.search(r'\bumrl?[oa]\b|\bumro\b', info) and not death:
        rec['death_type'] = 'umro'
    for pattern, duty in DUTIES:
        if re.search(pattern, info):
            rec['rank'] = duty
            break
    else:
        rec['rank'] = 'borac'
    vod = re.search(r'\bu (prvom|drugom|trećem) vodu\b|\b(?:komandir|delegat) (prvog|drugog|trećeg) voda\b', info)
    if vod:
        rec['unit_detail'] = VOD[vod.group(1) or vod.group(2)]
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        page = s.pop('pdf_page')
        for k in ('pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = viewer_url(BOOK, page)
        s['source_page'] = printed_page(BOOK, page)
    n = restore_diacritics(soldiers, name_counts('pionirska-ceta-soldiers.json'))    # "Dure", "Duro": Đure, Đuro
    print(f'  diacritics restored in {n} names; {sum(1 for s in soldiers if s.get("death_type") == "poginuo")} fell')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='poreklo/pionirska-ceta.json',
        brigade_code=121,
        output_path='website/public/pionirska-ceta-soldiers.json',
        extract_fn=read_lines,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
