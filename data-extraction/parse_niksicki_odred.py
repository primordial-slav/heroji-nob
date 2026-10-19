"""
Gojko Miljanić, *Nikšićki odred* (Vojnoizdavački zavod, Beograd 1970; znaci.org 00003/1024, a scan with no text
layer): its lists of the region's fallen and its narodni heroji, books across units. Its entries are added to the
records of the soldiers they describe (scripts/match_references.py), the rest go to Ostali borci.

The site's PDF website/public/pdfs/niksicki-odred-pali-borci.pdf is the scan's PDF pages 196-213, each spread split
into its two book pages (book pp. 393-420 and 423-427, the site's pages 1-28 and 29-33). The text is Tesseract's
(data-extraction/ocr_scan.py, `--lang srp`), saved in data-extraction/ocr/niksicki-odred-pali-borci.json; this
parser reads only that file.

- "Imena palih boraca u toku NOR-a" (book pp. 393-420): "Sa područja bivšeg nikšićkog sreza i zapadne Boke skoro svi
  borci prošli su kroz Nikšićki odred. U toku NOR-a u brigadama, u odredu, pri vojnopozadinskim ustanovama i
  jedinicama i na drugim dužnostima poginulo je oko 1500 boraca." A table in Cyrillic, a man a row: SURNAME Father
  GIVEN (the father in the genitive, or an initial), the place and year of birth, the place and year of death, under
  two headings: "Iz sreza nikšićkog" and (p. 418 on) "Spisak poginulih boraca sa teritorije opštine Herceg-Novi",
  which has no column for the year of birth. "—" is a cell the author could not fill. IDs 9080xxxxxx, by the row's
  place in the list.
- "Spisak narodnih heroja" (book pp. 423-427): the 39 narodni heroji of the Nikšić and Herceg-Novi municipalities, a
  short biography each ("1. — АЛЕКСИЋ Јефта ВЕЉКО, рођен 1918. у с. Подврш, ... За народног хероја проглашен 20.
  XII 1951."), all of them, the fallen and the living. IDs 9081xxxxxx, by the book's number.

The OCR's slips are read back from the names and places the site knows (`_ocr_readback`); the list is alphabetical
(the Latin order: А, Б, Ц, Ч, Д ...), so a surname's first letter the OCR confuses (Б, В, Ђ) follows its neighbours.
Every row whose name or place the site doesn't know, or whose reading the rules changed, or whose years can't be, was
checked against the page image: the cells read there are kept in data-extraction/ocr/niksicki-odred-pali-borci.scan.json
(page, the row's top, and the cells to set). Names printed so are kept as printed ("Kadih", "Ferdinand Golub",
"Anrijevica"); a year the print got wrong (born 1944, died 1925) is left out. The book prints Jovanović Đorđija Marko
twice on p. 7: both entries are kept. The srez's list has 1,232 rows to the book's count of 1,231.
The heroes' biographies are typed from the page images (`HEROES`): the OCR garbles their roman months.

Output: data-extraction/znaci/niksicki-odred-pali-borci-entries.json, niksicki-odred-narodni-heroji-entries.json.
Usage: python data-extraction/parse_niksicki_odred.py [--sample N] [--rows P]   (--rows: print page P's rows as read)
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ocr_scan  # noqa: E402
from _ocr_readback import CYR, LOOKALIKE, Corpus, fold, latin, title  # noqa: E402

PDF = 'niksicki-odred-pali-borci.pdf'
OUT = HERE / 'znaci' / 'niksicki-odred-pali-borci-entries.json'
OUT_HEROES = HERE / 'znaci' / 'niksicki-odred-narodni-heroji-entries.json'
PREFIX, PREFIX_HEROES = '9080', '9081'
TITLE = 'Imena palih boraca u toku NOR-a'
LISTS = {'srez': 'iz sreza nikšićkog', 'hn': 'sa teritorije opštine Herceg-Novi'}
HERO_TITLE = 'Narodni heroji Nikšića i Herceg-Novog'
LIST_PAGES = range(1, 29)
HERO_PAGES = range(29, 34)
YEAR = re.compile(r'^[(\[]?(1[89]\d\d)[.,:;)]*$')
DASH = re.compile(r'^[—–-]+$')
UC = 'А-ЯЂЈЉЊЋЏA-Z'

# cells the OCR garbled past the rules, read from the page images: (page, the row's top in points, rounded) -> the
# cells as printed, in Latin: last, father, given, nick, bp (birthplace), by (year), dp (death place), dy (year)
SCAN: dict[tuple[int, int], dict] = {}
SCAN_FILE = HERE / 'ocr' / 'niksicki-odred-pali-borci.scan.json'     # (kept beside the OCR: page, y, cells)


def is_caps(word: str) -> bool:
    letters = [c for c in word if c.isalpha()]
    return len(letters) >= 2 and sum(c.isupper() for c in letters) >= 0.6 * len(letters)


def column_starts(lines: list[dict]) -> list[float]:
    """The x where a table column starts: words that follow a wide gap on their line, clustered"""
    xs = []
    for ln in lines:
        ws = sorted(ln['words'], key=lambda w: w[0])
        for a, b in zip(ws, ws[1:]):
            if b[0] - a[2] >= 12:
                xs.append(b[0])
    xs.sort()
    clusters: list[list[float]] = []
    for x in xs:
        if clusters and x - clusters[-1][-1] <= 6:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    rows = sum(1 for ln in lines if len(ln['words']) >= 4)
    starts = [min(c) for c in clusters if len(c) >= max(4, 0.2 * rows)]
    return [s for s in starts if s > 120]


class W(str):
    """A word as the OCR read it, with its other reading (ocr_scan.py's first, where it read the word again)"""
    alt = ''


def word(w: list) -> W:
    out = W(w[4])
    out.alt = w[6] if len(w) > 6 else ''
    return out


def cells(ln: dict, starts: list[float]) -> list[list[W]]:
    edges = [-1e9, *[s - 5 for s in starts], 1e9]
    out = [[] for _ in range(len(edges) - 1)]
    for w in sorted(ln['words'], key=lambda w: w[0]):
        i = max(k for k in range(len(edges) - 1) if w[0] >= edges[k])
        out[i].append(word(w))
    return out


def clean(words: list[W]) -> list[W]:
    """A cell's words without the specks the OCR read as marks ("|", "~", "“", ",")"""
    return [w for w in words if re.search(r'[\wА-Яа-я—–]', w) and not re.fullmatch(r'[|~“”"‘’`\'.,:;·*_+]+', w)]


def read_rows() -> list[dict]:
    ocr = ocr_scan.load(PDF)
    rows, section, done = [], 'srez', False
    for pno in LIST_PAGES:
        page = ocr['pages'][str(pno)]
        lines = page['lines']
        starts = column_starts(lines)
        for ln in lines:
            text = ' '.join(w[4] for w in ln['words'])
            if re.search(r'ТЕРИТОРИЈЕ|ОПШТИНЕ', text) and re.search('СПИСАК|ПОГИНУЛИХ|Х[EЕ]Р', text):
                section = 'hn'
                continue
            if re.search(r'НАПОМЕНА|УКУПНО', text):
                if 'УКУПНО' in text:
                    continue                             # the srez's total: "УКУПНО ИЗ СРЕЗА НИКШИЋКОГ 1231. ПАЛИ БОРАЦ"
                done = True
            if done:
                break
            c = [clean(x) for x in cells(ln, starts)]
            if not c[0] or len([x for x in c if x]) < 2:
                continue
            while c[0] and not is_caps(c[0][0]) and len(re.sub(r'\W', '', c[0][0])) <= 2:
                c[0] = c[0][1:]                          # a speck before the surname read as letters ("ji", "i")
            name = c[0]
            # (the OCR sets some surnames in small letters: "мишовић", "мили" for МИЛИЋ)
            if not name or len(re.sub(r'\W', '', name[0])) < 3 or re.search(r'ИМЕНА|СРЕЗА|Место|година', text):
                continue
            has_year = any(YEAR.match(w) for x in c[1:] for w in x)
            if not (has_year or any(DASH.match(w) for x in c[1:] for w in x)) or not (has_year or any(is_caps(w) for w in name)):
                continue                                 # no year and no dash in the row (prose, a heading), or a dash
                #                                          and no name in capitals (the footnote's "— sadašnjim opštinama —")
            rows.append({'page': pno, 'section': section, 'cells': c, 'ncols': len(c),
                         'x0': ln['x0'], 'top': ln['top'], 'x1': ln['x1'], 'bottom': ln['bottom'], 'text': text})
    return rows


def joined(words: list[W]) -> W:
    out = W(' '.join(words))
    out.alt = ' '.join(w.alt or w for w in words) if any(w.alt for w in words) else ''
    return out


def split_row(r: dict) -> tuple[list[W], W, W, W, W]:
    """name words, birthplace, birth year, death place, death year from a row's cells"""
    c = r['cells']
    name = c[0]
    rest = [joined(x) for x in c[1:]]
    # the columns: in the srez list place, year, place, year; in Herceg-Novi's place, place, year
    years = [i for i, x in enumerate(rest) if YEAR.match(x) or DASH.match(x)]
    if r['section'] == 'srez' and len(rest) >= 4:
        bp, by, dp, dy = rest[0], rest[1], rest[2], joined(rest[3:])
    elif r['section'] == 'hn' and len(rest) >= 3:
        bp, by, dp, dy = rest[0], W(''), rest[1], joined(rest[2:])
    else:
        # fewer cells than columns: take the years from the right
        bp = by = dp = dy = W('')
        if years and years[-1] == len(rest) - 1:
            dy = rest[-1]
            rest = rest[:-1]
        if rest:
            bp = rest[0]
        if len(rest) > 1:
            dp = rest[-1]
    return name, bp, by, dp, dy


def year(text: str) -> str:
    m = re.search(r'(1[89]\d\d)', text or '')
    return m.group(1) if m else ''


JUNK = re.compile(r"[\"“”„'‘’|~*·_]")


def tidy(text: str) -> str:
    """A place cell without the specks the OCR read as quotes and short words ("ii Cetinje", "Povija, li")"""
    words = [w for w in JUNK.sub('', text or '').split() if w]
    while words and (re.fullmatch(r'[—–-]+', words[0]) or (len(words) > 1 and re.fullmatch(r'[a-zа-яђјљњћџ]{1,2}', words[0]))):
        words = words[1:]
    while words and (re.fullmatch(r'[—–-]+|[a-zа-яђјљњћџ]{1,2}[.,]?', words[-1]) and len(words) > 1):
        words = words[:-1]
    return ' '.join(words).strip(' ,.;:')


def place(corpus: Corpus, text: W) -> str:
    alt = tidy(getattr(text, 'alt', '') or '')
    text = tidy(text)
    if not text or re.fullmatch(r'[—–-]+', text):
        return ''
    out = corpus.place(text, alts=(alt,) if alt else ())
    # a word read in capitals ("УЗдОМИР"): in small letters after its first
    return ' '.join(title(w) if sum(c.isupper() for c in w) > 1 and not re.fullmatch(r'\(?BiH\)?,?', w) else w
                    for w in out.split())


def strip(w: W) -> W:
    if re.fullmatch(rf'[{UC}]\.', w):
        return w
    out = W(w.strip(',.;:'))
    out.alt = w.alt.strip(',.;:')
    return out


def parse_name(corpus: Corpus, words: list[W]) -> tuple[str, str, str, str]:
    """SURNAME Father GIVEN [NICK]: the father the second word of three or more (in small letters, or an initial);
    of two words, the surname and the given name. "др" before the given name is a title."""
    words = [x for x in (strip(w) for w in words) if x]
    title_dr = [w for w in words[1:] if w.lower() in ('др', 'dr', 'инж')]
    words = [w for w in words if w not in title_dr]
    if len(words) >= 3:
        last, father, given = words[:1], words[1], words[2:]
    else:
        last, father, given = words[:1], W(''), words[1:]
    surname = '-'.join(corpus.surname(w, alts=(w.alt,) if w.alt else ()) for w in last)
    fathers = corpus.genitive(father, alts=(father.alt,) if father.alt else ()) if father else ''
    first = corpus.given(given[0], alts=(given[0].alt,) if given[0].alt else ()) if given else ''
    nick = ' '.join(title(latin(w)) for w in given[1:] if not re.fullmatch(r'[—–-]+', w))
    if title_dr:
        nick = ('dr ' + nick).strip()
    return surname, fathers, first, nick


def alphabet_fix(entries: list[dict], fixed: set) -> None:
    """The list is alphabetical by surname: a first letter the OCR confuses (B, V, Đ) that differs from both
    neighbours' and theirs agree, takes theirs when the site knows the surname so"""
    for i in range(1, len(entries) - 1):
        a, e, b = entries[i - 1], entries[i], entries[i + 1]
        la, le, lb = a['last_name'][:1], e['last_name'][:1], b['last_name'][:1]
        if la == lb != le and {le, la} <= set('BVĐ') and e['no'] not in fixed:
            e['last_name'] = la + e['last_name'][1:]


HERO_START = re.compile(r'^(\d{1,2})\s*[.,:]\s*[—–-]+\s*')
# The heroes as printed (book pp. 423-427), typed from the page images, since the OCR garbles the biographies' roman
# months and a few words ("KIIJ", "Mikšiću"): (surname, father, given name, what he was called, birthplace in the
# nominative, birth year, year of death in the war or '', lived after the war, the biography from "rođen")
HEROES = [
    ('Aleksić', 'Jefta', 'Veljko', '', 'Podvrš', '1918', '1943', False, 'rođen 1918. u s. Podvrš, opština vučedolska, šumar, član KPJ od 1940. U NOB od 1941. Poginuo na Ćurevu kod Sutjeske 12. juna 1943, kao komandir čete u 5. crnogorskoj brigadi. Za narodnog heroja proglašen 20. XII 1951.'),
    ('Asović', 'Mija', 'Muharem', 'Cigo', 'Nikšić', '1913', '1943', False, 'rođen 1913. u Nikšiću, po zanimanju kovač, član KPJ od 1934. u NOB od 1941. Teško ranjen od četnika ubio se 20. I. 1943. u s. Dragovoljićima kod Nikšića kao član Sreskog komiteta KPJ.'),
    ('Baletić', 'Lazara', 'Marko', '', 'Broćanac', '1917', '1943', False, 'rođen 1917. u s. Broćanac, Nikšić, student medicine, član KPJ od 1940. U NOB od 1941. Poginuo 13. juna 1943. prilikom proboja 5. brigade na Sutjesci. Za narodnog heroja proglašen 10. VII. 1952.'),
    ('Basković', 'Mitra', 'Aleksa', '', 'Drenoštica', '1912', '1944', False, 'rođen 1912. u s. Drenoštica, Pješivci, pravnik, član KPJ od maja 1941. U NOB od 1941. Poginuo 7. IV. 1944. kod Udbine (Lika) kao politički komesar divizije. Za narodnog heroja proglašen 20. XII. 1951.'),
    ('Bojović', 'Dimitrija', 'Danilo', '', 'Kuti', '1909', '1943', False, 'rođen 1909. u s. Kuti, Župa nikšićka, pravnik član KPJ od 1937. god. u NOB od 1941. godine. Poginuo u s. Konjsko u borbi sa četnicima i Italijanima pošto je bio otkriven i opkoljen u proleće 1943., kao član Okružnog komiteta Nikšić. Za narodnog heroja proglašen 11. XII. 1945.'),
    ('Bojović', 'Dragiše', 'Dušan', '', 'Kuti', '1914', '1943', False, 'rođen 1914. u s. Kuti, Župa nikšićka, student prava, član KPJ od 1940. U NOB od 1941. Poginuo na Sutjesci 13. juna 1943.'),
    ('Čupić', 'Save', 'Čedomir', 'Ljubo', 'Nikšić', '1913', '1942', False, 'rođen 1913. u Nikšiću, student prava, član KPJ od 1941. U NOB od 1941. Uhapšen kao borac Nikšićkog odreda u proleće 1942. i streljan 25. 5. 1942. pod Trebjesom kod Nikšića. Za narodnog heroja proglašen 10. VII. 1953. Prilikom streljanja njegove poslednje reči su bile: „Živela KPJ“, „Živeo drug TITO“! Njegovo herojsko držanje ostavilo je snažan utisak u Nikšiću kod neprijatelja a i kod simpatizera NOR-a.'),
    ('Đurković', 'Aleksije', 'Nikola', '', 'Risan', '1908', '1943', False, 'rođen 1908. u Risnu, advokat, član KPJ od 1936. godine. U NOB od 1941. Poginuo 21. I. 1943. u s. Podi kod Herceg-Novog kao sekretar MK Herceg-Novi zajedno sa još 3 člana MK pošto su bili otkriveni i opkoljeni od oko 200 Italijana, prihvatili su borbu i svi izginuli. Za narodnog heroja proglašen 1945. god.'),
    ('Đurović', 'Mile', 'Milisav', '', 'Župa nikšićka', '1911', '1944', False, 'rođen 1911. u Župi nikšićkoj, radnik, član KPJ od 1941. U NOB od 1941. Poginuo 17. X. 1944. kao komandant bataljona u borbama za oslobođenje Beograda. Za narodnog heroja proglašen 1953.'),
    ('Đurović', 'Đura', 'Milinko', '', 'Zagrad', '1910', '', True, 'rođen 1910. u s. Zagrad, Župa nikšićka, advokatski pripravnik, član KPJ od od 1936. godine. U NOB od 1941. General-pukovnik JNA u penziji. Prvi potilički komesar odreda i član Okružnog komiteta od osnivanja. Za narodnog heroja proglašen 10. VII. 1952.'),
    ('Giljan', 'Janka', 'Pero', '', 'Kočane', '1912', '1943', False, 'rođen 1912. u s. Kočane, Nikšić, zemljoradnik, član KPJ od 1935. godine. U NOB od 1941. Umro od tifusa februara 1943. u Bosanskom Petrovcu. Za narodnog heroja proglašen 10. VII. 1952.'),
    ('Ilić', 'Petra', 'Savo', '', 'Ledenice', '1914', '1943', False, 'rođen 1914. u s. Ledenice kod Risna, član KPJ od 1938. godine. U NOB od 1941. Poginuo u s. Podi kod Herceg-Novog 21. I. 1943. zajedno sa Nikolom Đurkovićem kao član MK. Bili su opkoljeni i da ne bi pali živi u ruke neprijatelju, počeli su se probijati i svi su izginuli. Savo se sam ubio. Za narodnog heroja proglašen 10. VII. 1953.'),
    ('Jovanović', 'Milana', 'Božidar', '', 'Nikšić', '1919', '', False, 'rođen 1919. u Nikšiću, student prava, član KPJ od 1942. godine. U NOB od 1941. U Nikšićkom odredu bio zamenik komandira i komesara čete 1941. i 1942. godine u 5. crnogorskoj brigadi a potom komandant Bokeljske brigade. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Jovanović', 'Milinka', 'Petar', '', 'Jugovići', '1921', '1942', False, 'rođen 1921. u s. Jugovići, Župa nikšićka, oficir BJV, član KPJ od 1941. godine. U NOB od 1941. Bio komandant bataljona u Nikšićkom odredu. Izvršio samoubistvo 26. XII. 1942. kod Bosanskog Novog, pošto je bio teško oboleo od tifusa. Za narodnog heroja proglašen 20. XII. 1953.'),
    ('Kilibarda', 'Vukote', 'Milo', '', 'Velimlje', '1913', '', True, 'rođen 1913. u Velimlju (Banjani), poljoprivredni činovnik, član KPJ od 1941. godine. U NOB od 1941. U Nikšićkom odredu bio komandant i komesar bataljona. General-pukovnik JNA. Za narodnog heroja proglašen 21. XI. 1953.'),
    ('Koprivica', 'Alekse', 'Vasilije', '', 'Koprivice', '1919', '1943', False, 'rođen 1919. u s. Koprivice (Banjani) zemljoradnik. Član KPJ od 1942. U NOB od 1941. Poginuo 28. marta 1943. kod Nevesinja kao komandir čete u 5. brigadi. Za narodnog heroja proglašen 20. X. 1953.'),
    ('Kovačević', 'Goluba', 'Miloš', '', 'Grahovo', '1912', '1943', False, 'rođen 1912. u Grahovu, podoficir BJV. član KPJ od 1941. godine. Poginuo u bici na Neretvi kod Konjica februara 1943. kao komandant bataljona u 5. crnogorskoj brigadi. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Kovačević', 'Nikole', 'Mitar', 'Mujo', 'Grahovo', '1916', '', False, 'rođen 1916. u Grahovu, privatni nameštenik. Član KPJ od 1941. godine, U NOB od 1941. U Nikšićkom odredu bio komandir čete i komandant Gatačko-nevesinjskog sektora. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Kovačević', 'Blagoja', 'Sava', '', 'Nudo', '1906', '1943', False, 'rođen 1906. godine u s. Nudo kod Grahova, zemljoradnik i radnik revolucionar. Član KPJ od 1925. godine. Jedan od najvećih junaka u u NOB. Kao neustrašivi junak stekao veliku popularnost u narodu kao komandant Nikšićkog odreda, komandant 5. brigade i 3. divizije. Postao legendarni junak. Poginuo 13. juna 1943. kada se na čelu 3. udarne divizije probijao kroz nemački obruč kod Krekova na Sutjesci. Za narodnog heroja proglašen 6. VII. 1943.'),
    ('Kovačević', 'Petra', 'Vojo', '', 'Grahovo', '1912', '', True, 'rođen 1912. u Grahovu, student tehnike, član KPJ od 1934. godine. U NOB od 1941. General-pukovnik JNA. Za narodnog heroja proglašen 10. VII. 1952.'),
    ('Kovačević', 'Petra', 'Vasilije', 'Čile', 'Grahovo', '1911', '', True, 'rođen 1911. u Grahovu, nameštenik, član KPJ od 1934. godine. U NOB od 1941. Umro 1961. godine u Sanfrancisku (SAD) kao konzul SFRJ. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Lješković', 'Mašana', 'Nikola', '', 'Pljevlja', '1916', '1943', False, 'rođen 1916. godine u Pljevljima, nesvršeni učenik. Član KPJ od 1936. U NOB od 1941. Poginuo 12. VI. 1943. na Sutjesci. Za narodnog heroja proglašen 20. XII. 1951.'),
    ('Maksimović', 'Mirka', 'Aleksa', '', 'Gornje Polje', '1919', '1943', False, 'rođen 1919. u s. Gornje Polje, student član KPJ u NOB od 1941. godine. Poginuo 17. V 1943. kod s. Oraho, Nikšić u borbi sa Nemcima.'),
    ('Mandić', 'Vida', 'Gligorije', '', 'Kameno', '1912', '', True, 'rođen 1912. u s. Kameno, kod Herceg-Novog, mašinski radnik, član KPJ od 1935. General-potpukovnik u penziji. U Nikšićkom odredu bio komandant bataljona. Za narodnog heroja proglašen 10. VII. 1952.'),
    ('Milatović', 'Milisava', 'Veljko', '', 'Nikšić', '1921', '', True, 'rođen 1921. u Nikšiću student tehnike, Član KPJ od 1940. godine. Predsednik Savezne konferencije SSRNJ. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Nikolić', 'Nikole', 'Vojin', 'Vojo', 'Miločane', '1914', '', True, 'rođen 1914. u s. Miločane kod Nikšića, član KPJ od 1933. U NOB od 1941. Bio zamenik komesara Nikšićkog odreda. Član Saveta Federacije SFRJ. General-pukovnik u rezervi. Za narodnog heroja proglašen 20. VII. 1952.'),
    ('Pavićević', 'Šaja', 'Đoko', '', 'Nikšić', '1872', '', True, 'rođen 1872. godine u Nikšiću, bio kapetan bivše crnogorske vojske. Član KPJ od 1943. U NOB od 1941. Pukovnik u penziji, Najstariji partizan u Jugoslaviji. Za narodnog heroja proglašen 27. XI. 1953. Umro 1970.'),
    ('Premović', 'Marka', 'Đorđe', '', '', '1910', '1943', False, 'rođen 1910. radnik. Član KPJ od 1933. U NOB od 1941. Bio jedan od organizatora odlaska dobrovoljaca u Španiju pa je i sam pošao, ali je pri odlasku bio otkriven i uhapšen. Poginuo marta 1943. kod Bileće kao komandir čete u 5. brigadi. Proglašen za narodnog heroja 20. XII. 1951.'),
    ('Radojević', 'Radoja', 'Lazar', '', '', '1916', '1941', False, 'rođen 22. III. 1916. tehničar. Član KPJ od 1938. U NOB od 1941. godine. Poginuo 1. XII. 1941. u napadu na Pljevlja kao zamenik komandanta bataljona „Peko Pavlović“. Za narodnog heroja proglašen 20. XII. 1951.'),
    ('Radulović', 'Veliše', 'Veljko', 'Mijo', 'Milojevići', '1915', '1942', False, 'rođen aprila 1915. u s. Milojevići u opštini Pješivci, zemljoradnik. Član KPJ od 1940. U NOB od 1941. godine. Poginuo 6. XI. 1942. kao ilegalac kod Oranog Dola, Pješivci u borbi sa četnicima. U Nikšićkom odredu bio komesar čete. Za narodnog heroja proglašen 13. VII. 1953.'),
    ('Todorović', 'Nedeljka', 'Veljko', '', 'Orah', '1914', '1944', False, 'rođen 20. IV. 1914. u s. Orahu, Župa nikšićka, zemljoradnik. Član KPJ od 1939. U NOB od 1941. Poginuo 29. VII. 1944. na mestu Velji Krš kod Andrijevice. Za narodnog heroja proglašen 20. XII. 1951.'),
    ('Vučinić', 'Radovana', 'Milica', '', 'Pješivci', '1921', '1943', False, 'rođena 1921. u Pješivcima, domaćica. Član KPJ od 1941. U NOB od 1941. Poginula marta 1943. kod s. Šipačna, Nevesinje u borbi sa četnicima kao bolničarka u četi. Za narodnog heroja proglašena 13. VII. 1953.'),
    ('Vujačić', 'Vidaka', 'Vasilije', 'Vajo', 'Grahovo', '1917', '1943', False, 'rođen 1. V. 1917. u Grahovu, radnik. Član KPJ od 1941. U NOB od 1941. Poginuo marta 1943. kod Blagaja (Hercegovina), kao komandant bataljona u 5. crnogorskoj brigadi. Za narodnog heroja proglašen 20. XII. 1951.'),
    ('Vujačić', 'Đoka', 'Dušan', '', 'Riđani', '1917', '1943', False, 'rođen 1917. u s. Riđani kod Nikšića, nadničar. Član KPJ od 1942. U NOB od 1941. Poginuo 25. V. 1943. na Zelenom vrhu, na pl. Vojnik, u borbi sa Nemcima kao komandir čete. Za narodnog heroja proglašen 13. VII. 1953.'),
    ('Vujović', 'Marka', 'Dušan', '', 'Lukovo', '1909', '1943', False, 'rođen 1909. u Lukovu, finansijski službenik. Član KPJ od 1942. U NOB od 1941. Izvršio samoubistvo u psihičkom rastrojstvu kao teški ranjenik juna 1943. kod Bajovog Polja (Brezna). Za narodnog heroja proglašen 27. XI. 1943.'),
    ('Vukotić', 'Draga', 'Jovo', '', 'Nikšić', '1907', '', True, 'rođen 22. II. 1907. u Nikšiću, oficir BJV. Član KPJ od 1942. U NOB od 1941. General-pukovnik u penziji. U Nikšićkom odredu bio zamenik komandanta bataljona. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Zeković', 'Sima', 'Veljko', '', 'Nikšić', '1906', '', True, 'rođen 1906. u Nikšiću, pravnik. Član KPJ od 1934. U NOB od 1941. godine. U Nikšićkom odredu bio je zamenik političkog komesara odreda. Bio član MK KP Nikšić, član pa sekretar Okružnog komiteta KP Nikšić. Član Saveta Federacije SFRJ. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Matković', 'Krsta', 'Mirko', '', 'Podi', '1915', '', True, 'rođen 3. XI. 1915. u s. Podi, kod Herceg-Novog, oficir BJV. Član KPJ od 1940. U NOB od 1941. General-major u penziji. U Nikšićkom odredu bio komandant Orjenskog bataljona. Za narodnog heroja proglašen 27. XI. 1953.'),
    ('Zvicer', 'Blagote', 'Jovo', '', 'Bare', '1914', '', False, 'rođen 15. 7. 1914. u s. Bare, Trešnjevo, radnik. Član KPJ od 1942. a u NOB od 1941. Poginuo na Vilića Gumnu kod Prozora marta u borbi sa Nemcima.'),
]


def read_heroes() -> list[dict]:
    """The heroes: each entry's place from the OCR (it starts at "N. —", hanging, and may run on to the next page),
    its words typed (HEROES), in the book's order"""
    ocr = ocr_scan.load(PDF)
    starts: list[dict] = []
    for pno in HERO_PAGES:
        for ln in ocr['pages'][str(pno)]['lines']:
            text = ' '.join(w[4] for w in ln['words'])
            if text.startswith('НАПОМЕНА'):
                break
            if HERO_START.match(text):
                starts.append({'page': pno, 'lines': [ln]})
            elif starts and starts[-1]['page'] == pno and not re.fullmatch(r'[\d\W]*', text):
                starts[-1]['lines'].append(ln)
    assert len(starts) == len(HEROES), (len(starts), len(HEROES))
    out = []
    for no, (st, (last, father, first, nick, born_in, by, dy, lived, bio)) in enumerate(zip(starts, HEROES), 1):
        lines = st['lines']
        out.append({'soldier_id': f'{PREFIX_HEROES}{no:06d}', 'name': ' '.join(x for x in (last, father, first, nick) if x),
                    'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': father, 'no': no,
                    'birth_year': by, 'born_in': born_in, 'death_year': dy, 'survived': lived,
                    'additional_info': f'{HERO_TITLE}: {bio}', 'list': HERO_TITLE,
                    'pdf_file': PDF, 'pdf_page': st['page'], 'pdf_x': round(lines[0]['x0'], 1),
                    'pdf_y': round(lines[0]['top'] - 1, 1), 'pdf_x_left': round(min(ln['x0'] for ln in lines), 1),
                    'pdf_x_end': round(max(ln['x1'] for ln in lines) + 1, 1),
                    'pdf_y_end': round(max(ln['bottom'] for ln in lines) + 1, 1)})
    return out


def load_scan() -> None:
    if SCAN_FILE.exists():
        for row in json.loads(SCAN_FILE.read_text(encoding='utf-8')):
            SCAN[(row['page'], row['y'])] = {k: v for k, v in row.items() if k not in ('page', 'y', 'ocr')}


def main() -> None:
    load_scan()
    corpus = Corpus()
    rows = read_rows()
    if '--rows' in sys.argv:
        p = int(sys.argv[sys.argv.index('--rows') + 1])
        for r in rows:
            if r['page'] == p:
                print(r['section'], r['cells'])
        return
    entries, fixed = [], set()
    for n, r in enumerate(rows, 1):
        name, bp, by, dp, dy = split_row(r)
        last, father, first, nick = parse_name(corpus, name)
        if not year(dy) and year(dp):                # the year slid into the place's column: "Gornje Polje 1944"
            dy, dp = W(year(dp)), W(re.sub(r'\s*\(?1[89]\d\d\W*$', '', dp))
        if not year(by) and year(bp):
            by, bp = W(year(bp)), W(re.sub(r'\s*\(?1[89]\d\d\W*$', '', bp))
        bp, dp = place(corpus, bp), place(corpus, dp)
        by, dy = year(by), year(dy)
        fix = SCAN.get((r['page'], round(r['top'] - 1)))
        if fix:
            fixed.add(n)
            last, father, first, nick = (fix.get(k, v) for k, v in (('last', last), ('father', father),
                                                                     ('given', first), ('nick', nick)))
            bp, by, dp, dy = (fix.get(k, v) for k, v in (('bp', bp), ('by', by), ('dp', dp), ('dy', dy)))
        info = (f"{TITLE}, {LISTS[r['section']]}: "
                + ', '.join(x for x in (f'rođen {by}' if by else 'rođen', bp or '—') if x)
                + '; poginuo ' + ', '.join(x for x in (dy, dp) if x))
        info = info.replace('rođen, —; ', '')
        rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': ' '.join(x for x in (last, father, first, nick) if x),
               'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': father, 'no': n,
               'birth_year': by, 'born_in': bp, 'death_year': dy, 'death_place': dp,
               'additional_info': info, 'list': f'{TITLE}, {LISTS[r["section"]]}',
               'pdf_file': PDF, 'pdf_page': r['page'], 'pdf_x': round(r['x0'], 1), 'pdf_y': round(r['top'] - 1, 1),
               'pdf_x_end': round(r['x1'] + 1, 1), 'pdf_y_end': round(r['bottom'] + 1, 1)}
        entries.append(rec)
    alphabet_fix(entries, fixed)
    for e in entries:
        e['name'] = ' '.join(x for x in (e['last_name'], e['fathers_name'], e['first_name'], e['nick']) if x)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    heroes = read_heroes()
    OUT_HEROES.write_text(json.dumps(heroes, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(heroes)} narodni heroji (numbers {[h['no'] for h in heroes][:3]}...{heroes[-1]['no']}), "
          f"{sum(h['survived'] for h in heroes)} alive after the war")
    if '--heroes' in sys.argv:
        for h in heroes:
            print(f"   {h['no']}. {h['name']!r} [{h['born_in']}] {h['birth_year']} d{h['death_year']} | {h['additional_info'][:150]}")
    sec = Counter(e['list'] for e in entries)
    print(f'{len(entries)} rows: {dict(sec)}')
    print(f"  no given name: {sum(not e['first_name'] for e in entries)}, no father: "
          f"{sum(not e['fathers_name'] for e in entries)}, birth year: {sum(bool(e['birth_year']) for e in entries)}, "
          f"birthplace: {sum(bool(e['born_in']) for e in entries)}, death year: {sum(bool(e['death_year']) for e in entries)}, "
          f"death place: {sum(bool(e['death_place']) for e in entries)}")
    unknown = Counter(e['last_name'] for e in entries if not corpus.surnames[e['last_name'].lower().translate(str.maketrans('čćžšđ', 'cczsd'))])
    print(f'  surnames the site doesn\'t know: {len(unknown)}: {", ".join(list(unknown)[:60])}')
    if '--sample' in sys.argv:
        random.seed(3)
        for e in random.sample(entries, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"   p{e['pdf_page']} {e['name']!r} | {e['born_in']} {e['birth_year']} | {e['death_place']} {e['death_year']}")


if __name__ == '__main__':
    main()
