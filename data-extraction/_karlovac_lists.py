"""
The lists at the end of the Karlovac archive's kotar volumes (Zbornik Historijskog arhiva u Karlovcu: Gospić i Perušić,
Korenica i Udbina, Donji Lapac, Gračac, Plaščanska dolina, ...): books across units, their entries added to the records of
the soldiers they describe (see scripts/match_references.py). Each volume prints, by općina and village under centred
headings ("OPĆINA GOSPIĆ", "ČITLUK", "PAVLOVAC—VREBAC—ZAVODE"), numbered within each village:
    pali borci, the fighters who fell, in two columns of bios:
        "3. KRAJNOVIĆ Tome DUŠAN, 1917, kožarski radnik, Srbin. Stupio u NOB 1941, ... Ubili ga četnici kao borca
        6. div. kod Gračaca 18. 12. 1942." (knj. 20), "1. BELIC Mojsije PETAR, 1920. Clan KPJ od 1940. ..." (knj. 10);
    žrtve fašističkog terora i rata (civilians) and umrli od tifusa, which stay out of the site;
    in some volumes the nosioci partizanske spomenice 1941, a line each ("1. BAKIĆ Maksima MILE, 1923, seljak, Srbin.").
The site's PDF of a volume holds only its fighters' lists. A volume's parser gives the book's config to main():
    pdf, prefix (the IDs' first four digits), lists: [(kind, pages of the site's PDF, columns)], heads (names the reader
    can't take apart: what the page prints -> how it is read); optionally opcina (a volume of one općina prints no
    OPĆINA headings), names: 'title', spaced, and drop (a pattern for lines that are the page's furniture, not text).
The archive's village chronicles have the same lists (Mrkalj, *Sjeničak*, 1980), one column.

An entry starts where its number hangs left of the text (a line that starts with a number at the text's edge, "1. LPO
»Velebit«", "2. bat.", runs on), or, where the OCR lost the number, with SURNAME Father GIVEN. In a two-column volume
whose right column sets the numbers in the gutter, the PDF is listed in entry_boxes.NUMBERS_IN_GUTTER. A woman may carry
two surnames, married and maiden ("HRŽENJAK KRAJNOVIĆ Ilije JANJA", "RAŠETA r. PLEĆAŠ Laze SARA"), and the matcher
tries both (`also`); carons the OCR lost come back from the corpus ("BAKIC" = Bakić).

Output: data-extraction/znaci/<pdf name>-entries.json (IDs <prefix>xxxxxx, in the book's order), with the fields the
matcher reads (last_name, also, first_name, nick, fathers_name in the genitive as printed or its initial, birth_year,
born_in: the entry's own village or the heading's, and the općina; death_year and death_date for the fallen), the list,
and the entry's place on the page and its box. The entry's text starts with the village and općina (and, for the
spomenica, the list's title, which gives the record the medal).
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402

LISTS = {'fallen': 'Pali borci', 'spomenica': 'Nosioci partizanske spomenice 1941. godine'}
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# an entry's number ("63" may have lost its period) before the surname; in the spomenica list the surname may be
# printed in small letters ("5. Graovac Tanasije JANJA")
NOT_A_NAME = r'(?!(?:NOB|NOV|NOO|KPJ|KPH|SKOJ|LPO|LNOPO|GŠH|AFŽ|USAOH|SAD|PPKČ)\b)'
START = re.compile(rf'^(\d{{1,3}})\s?(?:[.,]\s*|\s+){NOT_A_NAME}(?=[{U}]{{3}}|[{U}][{L}]+-[{U}]{{3}}|[{U}]\s[{U}]{{3}})')
# a start whose number stands at the text's edge (the OCR moved it, or lost its period: "8 KRAUS Bele ZELJKO",
# "15 ŠOL A JA Luke"): the number, a surname in capitals (perhaps broken apart) and a father, after a finished entry
START_EDGE = re.compile(rf'^(\d{{1,3}})\.?\s+{NOT_A_NAME}(?=[{U}]{{2,}}(?:\s[{U}]{{1,4}})*\s[{U}][{L}]+\s)')
# a number the OCR read as letters ("e. BORJAN", "U. DRAGAŠ"): a start where it hangs, its number unknown
START_LOST = re.compile(rf'^\S{{1,2}}[.,]\s+{NOT_A_NAME}(?=[{U}]{{3}})')
START_LINE = re.compile(rf'^(\d{{1,3}})\s?[.,]\s*{NOT_A_NAME}(?!KPO\b)(?=[{U}])')   # not "1. KPO 18. 4. 1942"
NATION = re.compile(r'(?:Srbin|Srpkinja|Hrvat|Hrvatica|Musliman|Muslimanka|Slovenac|Slovenka|Crnogorac|Jevrej|Rus|Talijan)\b')
# a start whose number the OCR lost: SURNAME Father GIVEN
NAME = re.compile(rf'^[{U}]{{3,}}(?:\s+[{U}]{{3,}})?\s+(?:[{U}][{L}]+|[{U}]\.)\s+[{U}]{{3,}}\b')
# a volume that prints the names in small letters (knj. 14: "16. Glušica Vuje Spaso Pajo, 1920. Srbin."): a start is
# the number before Surname Father; one whose number the OCR lost is Surname Father Given, and the year
START_TITLE = re.compile(rf'^(\d{{1,3}})\s?(?:[.,]\s*|\s+)(?=[{U}][{L}]+(?:-[{U}][{L}]+)?\s+(?:[{U}][{L}]+|[{U}]\.)\s)')
NAME_TITLE = re.compile(rf'^[{U}][{L}]{{2,}}\s+[{U}][{L}]+\s+[{U}][{L}]+(?:\s+[{U}][{L}]+)?,\s*1[89]\d\d\b')
# how a fallen fighter's entry tells his death ("Ubile ga ustaše", "ranjena ... i umrla"): the first such word, and the
# first year after it
DEATH = re.compile(r'\b(?:pogin\w*|poeinu\w*|po\W?\s?g[mi]nu\w*|ubil\w*|ubijen\w*|ubi[oj]|[sš]tr[ie]*jelja\w*|zaklal\w*|'
                   r'zaklan\w*|umr\w*|nesta[lo]\w*|objesil\w*|obješen\w*|spalil\w*|uhvatil\w*|zarobil\w*|podleg\w*|'
                   r'izgubi\w*|likvidir\w*|smrz\w*)\b', re.I)
# the OCR's slips in these books: accents it put on letters, j read as ".T", i as "1", 1943 as "i 943"
OCR = str.maketrans('äàáâöòóüùúèéÄÀÁÖÜÈÉ', 'aaaaooouuueeAAAOUEE')


def title(word: str) -> str:
    return '-'.join(p[:1] + p[1:].lower() for p in word.split('-'))


def place(heading: str) -> str:
    """"LIČKI OSIK" -> "Lički Osik", "PAVLOVAC—VREBAC—ZAVODE" -> "Pavlovac—Vrebac—Zavode", "BUNIĆ II" -> "Bunić II",
    "KOMIĆ I POLJICE" -> "Komić i Poljice"."""
    words = heading.split(' ')
    out = []
    for i, w in enumerate(words):
        if re.fullmatch(r'I{1,3}|IV|V', w) and i == len(words) - 1 and i:
            out.append(w)                                                  # a part of a village: "BUNIĆ II"
        elif w == 'I' and 0 < i < len(words) - 1:
            out.append('i')
        else:
            out.append(re.sub(rf'[{U}]+', lambda m: title(m.group(0)), w))
    return ' '.join(out)


_places: dict = {}       # folded upper-case word of a place -> Counter of the site's spellings


def place_corpus() -> None:
    for f in (HERE.parent / 'website' / 'public').glob('*soldiers.json'):
        for s in json.loads(f.read_text(encoding='utf-8')):
            for w in re.findall(rf'[{U}][{L}]+', ' '.join(s.get(k) or '' for k in ('birth_place', 'death_place'))):
                _places.setdefault(w.upper().translate(ofz.FOLD), Counter())[w] += 1


def place_spelled(name: str) -> str:
    """A village heading in the site's spelling where the OCR lost a caron ("Rebic" = Rebić, "Seganovac" = Šeganovac);
    a word the site spells as printed, or doesn't know, is left alone."""
    def one(w: str) -> str:
        c = _places.get(w.upper().translate(ofz.FOLD))
        if not c or c.get(w, 0) >= 2:
            return w
        fits = [s for s, n in c.most_common() if n >= 3 and len(s) == len(w)
                and all(a == b or b.upper() in ofz.LOST.get(a.upper(), '') for a, b in zip(w, s))]
        return fits[0] if fits else w
    # a heading the OCR broke apart ("KESTENOV AC" = Kestenovac): joined where the site knows the whole
    words = name.split(' ')
    for i in range(len(words) - 1):
        whole = words[i] + words[i + 1].lower()
        if (len(words[i + 1]) <= 3 and not re.fullmatch(r'I{1,3}|IV|V|i', words[i + 1])     # "Bunić II", "Komić i Poljice"
                and _places.get(whole.upper().translate(ofz.FOLD))):
            words[i:i + 2] = [whole]
            break
    return re.sub(rf'[{U}][{L}]+', lambda m: one(m.group(0)), ' '.join(words))


def clean(text: str) -> str:
    """The OCR's slips at a line's start and in capitals: bullets and specks ("•3. HRNJAK", "•GRABUŠIĆ"), l for I in a
    word set in capitals ("ZlGlC", "FRKASlČ", "MANlSA")."""
    text = re.sub(r'^[•·■*^:;\'’`]+\s*', '', text)
    return re.sub(rf'\b[{U}l]{{3,}}\b', lambda m: m.group(0).replace('l', 'I')
                  if sum(c.isupper() for c in m.group(0)) >= 2 else m.group(0), text)


def spelled(word: str, part: str) -> str:
    """A name in the site's spelling where the OCR lost a caron ("BAKIC" = Bakić, "DURO" = Đuro); see
    parse_ofanziva_1942.known. Other slips are left as printed."""
    if ofz._spell[part].get(word.upper().translate(ofz.FOLD), {}).get(word.upper(), 0) >= 2:
        return title(word)
    n, best = ofz.known(word, part)
    if n >= 3:
        return title(best)
    # an I the OCR read as L, set in capitals ("OPACLC" = Opačić, "HINLC" = Hinić)
    w = word.upper()
    spots = [i for i, c in enumerate(w) if c == 'L' and not w[i + 1:i + 2] == 'J']        # not the LJ of "LJUBA"
    tries = [w[:i] + 'I' + w[i + 1:] for i in spots]
    tries += [w[:i] + 'I' + w[i + 1:j] + 'I' + w[j + 1:] for i in spots for j in spots if i < j]
    found = [hit for hit in (ofz.known(t, part) for t in tries) if hit[0] >= 3]
    return title(max(found)[1]) if found else title(word)


def read(book: dict) -> list[dict]:
    """The entries of the volume's lists in the book's order: their lines, page, start and the headings over them."""
    entries, opcina, village, ended = [], '', '', False
    kind_of ={p: (kind, cols) for kind, pages, cols in book['lists'] for p in pages}
    title_case = book.get('names') == 'title'
    firsts = {pages[0] for _, pages, _ in book['lists']}
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / book['pdf']) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            if pno not in kind_of:
                continue
            kind, cols = kind_of[pno]
            two = cols == 2
            data = entry_boxes.read_page(page, columns=cols, numbers_in_gutter=book['pdf'] in entry_boxes.NUMBERS_IN_GUTTER,
                                         gutter=entry_boxes.GUTTER.get((book['pdf'], pno)))
            if pno in firsts:
                # a list starts: its title, then its headings; a volume of one općina prints none (knj. 12, 16)
                opcina, village = book.get('opcina', ''), ''
                ended = False
            # on a list's first page, the title runs across both columns above the first općina's heading
            heads = [ln['top'] for col in data['columns'] for ln in col if re.match(r'OP[ĆČC]INA\s', ln['text'])]
            title_above = min(heads) - 10 if pno in firsts and heads else None
            table = False
            for col in data['columns']:
                # a footnote: the column's last lines, all in a smaller type ("* Naziv mjesta odnosi se ...", 7 pt
                # against 8.5; the OCR drops its asterisk as a speck)
                hs = sorted(ln['bottom'] - ln['top'] for ln in col)
                h = hs[len(hs) // 2] if hs else 0
                foot = len(col)
                while foot > len(col) // 2 and col[foot - 1]['bottom'] - col[foot - 1]['top'] < 0.85 * h:
                    foot -= 1
                col = col[:foot]
                lines = [dict(ln) for ln in col]
                # an entry's number hangs left of its text, where the lines run on: a line that starts with a number
                # there ("1. LPO »Velebit«", "2. bat.") runs on; in a list of a line each most lines are entries
                xs = sorted(ln['x0'] for ln in lines)
                text_x = xs[len(xs) // 2] if xs else 0
                # a number the right column sets in the gutter, a little higher or lower than its line
                merged = []
                for ln in lines:
                    if merged and re.fullmatch(r'\d{1,3}\s?[.,]', merged[-1]['text']) and abs(ln['top'] - merged[-1]['top']) < 6:
                        merged[-1] = dict(ln, text=merged[-1]['text'] + ' ' + ln['text'], x0=merged[-1]['x0'],
                                          top=min(ln['top'], merged[-1]['top']))
                    else:
                        merged.append(ln)
                for k, ln in enumerate(merged):
                    if title_above is not None and ln['top'] < title_above:
                        continue                                           # "Gračac 1941—1945.", the title's other half
                    if re.match(r'Tabela\s+\d', ln['text']):
                        table = True                                       # tables between the spomenica's pages,
                    if table and not START_LINE.match(ln['text']):         # up to the list's next entry
                        continue
                    table = False
                    t = clean(ln['text'].replace('­', '-').strip())
                    if book.get('spaced'):
                        # capitals the OCR spaced out ("M A Č AK" = MAČAK, "N O V"); a volume's own setting, since in
                        # another it would find entries its IDs, given in the book's order, don't count
                        t = re.sub(rf'(?<!\S)[{U}](?: [{U}]){{1,}}(?: [{U}]{{2}})?(?!\S)', lambda m: m.group(0).replace(' ', ''), t)
                    if re.fullmatch(r'\d{3,4}', t) and ln['top'] > data['height'] - 40 or (
                            re.fullmatch(r'\d{3,4}(?:\s+\d{3,4})?', t) and k >= len(merged) - 2):
                        continue                                           # the page number (two, on a spread)
                    if book.get('drop') and re.match(book['drop'], t):
                        continue                                           # a volume's own furniture ("22 SJENIČAK")
                    if re.match(r'(?:Žrtve fašističkog|Umrli od tifusa)', t):
                        ended = True                                       # the next list, of civilians, starts here
                    if ended:
                        continue
                    m = re.fullmatch(rf'OP[ĆČC]INA\s+([{U} -]+)', t)              # "OPČINA ZRMANJA" (knj. 13)
                    if m:
                        opcina, village = place_spelled(place(m.group(1))), ''
                        continue
                    if re.fullmatch(rf'[{U}][{U} .—–-]+', t) and not START.match(t) and len(t) < 40:
                        village = place_spelled(place(t))                  # "ČITLUK", "PAVLOVAC—VREBAC—ZAVODE"
                        continue
                    if not opcina:
                        continue                                           # the list's title
                    hanging = ln['x0'] < text_x - 5 if two else ln['x0'] < text_x + 5
                    first = START_TITLE if title_case else START if two else START_LINE
                    m = first.match(t) if hanging else None
                    m = m or (START_LOST.match(t) if hanging and two and entries and entries[-1]['list'] == kind else None)
                    if not m and two and not hanging and entries and entries[-1]['list'] == kind and entries[-1]['lines'][-1].rstrip().endswith('.'):
                        m = START_EDGE.match(t)
                    lost = not m and (NAME_TITLE if title_case else NAME).match(t) and entries and entries[-1]['list'] == kind
                    if m or lost:
                        no = int(m.group(1)) if m and m.re is not START_LOST else entries[-1]['no'] + 1
                        entries.append({'no': no, 'lines': [t[m.end():] if m else t], 'pdf_page': pno,
                                        'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1),
                                        'list': kind, 'opcina': opcina, 'village': village})
                    elif entries and entries[-1]['pdf_page'] in (pno, pno - 1) and entries[-1]['list'] == kind:
                        entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = lines[0]
    for ln in lines[1:]:
        if re.search(rf'[{L}{U}]-$', text) and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln                                          # "se-" / "ljak"
        elif re.search(rf'(?:^|\s)[{U}-]*[{U}]-$', text) and re.match(rf'[{U}]{{2,}}\b', ln):
            text = text[:-1] + ln                                          # a name: "VLADI-" / "MIR,", "PO-" / "BRO,"
        else:
            text += ' ' + ln
    return re.sub(r'\s+', ' ', text).strip()


def split_name(head: str) -> tuple[list[str], str, str, str]:
    """"KRAJNOVIĆ Jovana MILE" -> (surnames, father, given, nick); the father may be an initial ("T.") or missing.
    A married woman's maiden name follows "r." ("RAŠETA r. PLEĆAŠ Laze SARA"); it is left out of the surnames here
    and shown in the name."""
    head = re.sub(r'\s*[—–]\s*', ' — ', head.strip().rstrip('.'))
    nick = ''
    paren = re.search(r'\s*\(([^)]+)\)', head)
    if paren:                                                             # "EVICA (KOSA)"
        head, nick = (head[:paren.start()] + head[paren.end():]).strip(), paren.group(1)
    if ' — ' in head:                                                     # "DUŠAN — MILOŠ", "IVAN — VANJA"
        head, nick = head.split(' — ', 1)
    words = [w for w in head.split() if w not in ('r.', 'rođ.')]
    # a father's name the OCR broke ("Pa je" = Paje, "Ga vre" = Gavre)
    for i in range(1, len(words) - 1):
        if re.fullmatch(rf'[{U}][{U}{L}]{{0,3}}', words[i]) and re.fullmatch(rf'[{L}]{{2,4}}', words[i + 1]):
            words[i:i + 2] = [title(words[i]) + words[i + 1]]              # "IH je" = Ihje (Ilije?), as printed
            break
    caps = lambda w: w.replace('-', '').isupper() and len(w.rstrip('.')) > 1
    i = 0
    while i < len(words) and caps(words[i]):
        i += 1
    if i == len(words):
        # "NINKOVIĆ STEVO BAJA": a father the OCR set in capitals, a given name the site knows
        if len(words) == 3 and ofz.known(words[1], 'first')[0] >= 3 and ofz.known(words[0], 'last')[0] >= 3:
            return words[:1], title(words[1]), words[2], nick
        return words[:-1] or words, '', (words[-1] if len(words) > 1 else ''), nick   # "ČUBRIĆ BOJA": no father
    surnames, rest = words[:i] or words[:1], words[i:] if i else words[1:]
    if not rest:
        return surnames, '', '', nick
    if len(rest) == 1:                                                     # "PLAVŠIĆ Mile": the given name in small letters
        return surnames, '', rest[0], nick
    father, given = rest[0], ' '.join(rest[1:])
    return surnames, father, given, nick


def split_title(head: str) -> tuple[list[str], str, str, str]:
    """A name in small letters, by its order: "Glušica Vuje Spaso Pajo" -> (["Glušica"], "Vuje", "Spaso", "Pajo"); a
    married woman's maiden name after "r." ("Kosanović r. Vukša Rade Mara") is a second surname."""
    head = re.sub(r'\s*[—–]\s*', ' — ', head.strip().rstrip('.'))
    nick = ''
    paren = re.search(r'\s*\(([^)]+)\)', head)
    if paren:
        head, nick = (head[:paren.start()] + head[paren.end():]).strip(), paren.group(1)
    if ' — ' in head:
        head, nick = head.split(' — ', 1)
    # the OCR's marks in a name: "M-ilan", "Lazar-", "Stevo*"
    head, nick = (re.sub(rf'(?<=[{U}])-(?=[{L}])|-(?=\s|$)|\*', '', x).strip() for x in (head, nick))
    words = head.split()
    surnames = [words.pop(0)] if words else ['']
    if len(words) >= 2 and words[0] in ('r.', 'rođ.'):
        words.pop(0)
        surnames.append(words.pop(0))
    if len(words) == 1:
        return surnames, '', words[0], nick                               # "Popović Milka": no father
    father, given = (words[0], words[1]) if len(words) >= 2 else ('', '')
    if len(words) > 2 and not nick:
        nick = ' '.join(words[2:])                                         # "Spaso Pajo": what he was called
    return surnames, father, given, nick


def unsplit(head: str) -> str:
    """Capitals the OCR broke apart ("RAKI C" = RAKIĆ, "PUP A VAC" = PUPAVAC, "ELZ A" = ELZA): joined where the site knows
    the joined name and not the first piece."""
    words = head.split()
    out, i = [], 0
    while i < len(words):
        joined = None
        for k in (4, 3, 2):
            part = words[i:i + k]
            if len(part) == k and all(re.fullmatch(rf'[{U}]+', w) for w in part):
                whole = ''.join(part)
                kind = 'last' if not out else 'first'
                # "BAN J AC": Ban is a name too, but no name ends in a piece of a letter or two
                n_whole, n_first = ofz.known(whole, kind)[0], ofz.known(part[0], kind)[0]
                if n_whole >= 2 and (n_first < 2 or all(len(w) <= 2 for w in part[1:]) or n_whole >= 20 * n_first):
                    joined = whole
                    break
        if joined:
            out.append(joined)
            i += k
        else:
            out.append(words[i])
            i += 1
    return ' '.join(out)


def parse(book: dict, e: dict, n: int) -> dict:
    text = join(e['lines']).translate(OCR)
    text = re.sub(rf'(?<=[{U}])\.T(?=[{U}])', 'J', text)                     # "BAN.TEGLAV"
    text = re.sub(rf'(?<=[{U}{L}])1(?=[{U}{L}])', 'i', text)                  # "TODOR1Ć"
    text = re.sub(r'(?<![\w.])[iIlÌÍ] ?(9[34]\d)\b', r'1\1', text)            # "augusta i 943", "6. 12. Ì944"
    text = re.sub(r'^([^,]*?[a-zčćžšđA-ZČĆŽŠĐ])\.\s+(?=1[89]\d\d)', r'\1, ', text)   # "Nikola. 1918"
    head, info = (re.split(r',\s*', text, 1) + [''])[:2]
    sentence = re.search(rf'\.\s+(?=[{U}][{L}]+\s+[{L}])', head)
    y0 = re.search(r'[\s.,]+(1[89]\d\d)\b[.,]?\s*', head)
    if sentence and (not y0 or sentence.start() < y0.start()):            # "BEŠIR Srbislav. Stupio u NOB ..."
        head, info = head[:sentence.start()], head[sentence.end():] + (', ' + info if info else '')
    elif y0:                                                                # "MARKO 1922 seljak."
        head, info = head[:y0.start()], f'{y0.group(1)}, ' + head[y0.end():] + (', ' + info if info else '')
    head = book.get('heads', {}).get(head, head)
    # marks the OCR set inside or after a name: "M.ILE", "ORL»OVIC", "KOVAČEV^", "JOJA>", "RADUSIN -Ilije"
    head = re.sub(rf'(?<=[{U}{L}])[.»^](?=[{U}{L}])|[>^»]+(?=\s|$)|(?<=\s)-(?=[{U}])', '', head)
    head = unsplit(head)
    trade = re.search(r'\s([a-zčćžšđ]{4,})$', head)
    if trade:                                                               # "DANICA seljanka, Srpkinja"
        head, info = head[:trade.start()], f'{trade.group(1)}, {info}'
    # a comma after the surname alone: "MOMČILOVIĆ, Miloša MARKO, 1899"
    rest = re.match(rf'^([{U}][{L}]+\s+[{U}]{{2,}}(?:\s+[{U}]{{2,}})?)\s*,\s*', info) if re.fullmatch(rf'[{U}]{{3,}}', head) else None
    if rest:
        head, info = f'{head} {rest.group(1)}', info[rest.end():]
    # a nickname after the given name, before the year: "JOSO, Brico, 1912", "MILAN, MIĆA, 1924"; or her maiden name,
    # "MILKA, rođ. Miščević, 1908"
    alias = re.match(r'^([^,\d]{2,25}),\s*(?=1[89]\d\d)', info)
    surnames, father, given, nick = split_title(head) if book.get('names') == 'title' else split_name(head)
    maiden = re.fullmatch(rf'(?:rođ\.|r\.)\s*([{U}][{U}{L}]+)', alias.group(1).strip()) if alias else None
    if maiden:
        surnames, info = surnames + [maiden.group(1).upper()], info[alias.end():]
        head = f'{head} r. '                                               # shown as "Popović r. Miščević Rade Milka"
    elif alias and not nick:
        nick, info = alias.group(1).replace('- ', '').strip(), info[alias.end():]
    if '-' in given and all(len(p) > 2 for p in given.split('-')):        # "IVAN-Ćujo", "PETAR-PEKISA"
        given, nick = given.split('-', 1)[0], nick or given.split('-', 1)[1]
    if len(given.split()) == 2 and not nick:                               # "MILAN MIĆO": the second is what he was called
        given, nick = given.split()
    surnames = [spelled(w, 'last') for w in surnames]
    last = surnames[-1]
    first = ' '.join(spelled(w, 'first') for w in given.split())
    shown = (' r. ' if re.search(r'\sr\.\s', head) else ' ').join(surnames)
    name = ' '.join([shown] + ([father] if father else []) + ([first] if first else []))
    rec = {'soldier_id': f"{book['prefix']}{n:06d}", 'name': name + (f' — {title(nick)}' if nick else ''),
           'last_name': last, 'also': surnames[:-1], 'first_name': first, 'nick': title(nick),
           'fathers_name': father}                       # an initial too ("B."): the matcher compares it
    y = re.match(r'(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    where = f"{e['village']}, općina {e['opcina']}" if e['village'] and e['village'] != e['opcina'] else f"općina {e['opcina']}"
    # a village the entry names after the year ("1921, Pavlovac, seljak") is his own, under a heading of several
    # ("PAVLOVAC—VREBAC—ZAVODE") or none
    segs = [x.strip() for x in info.split(',')]
    own = segs[1] if (y and len(segs) > 2 and re.fullmatch(r'1[89]\d\d', segs[0]) and len(segs[1]) >= 3
                      and re.fullmatch(rf'[{U}][{L}]+(?:[\s—–-]+[{U}]?[{L}]+){{0,3}}', segs[1])
                      and not NATION.match(segs[1])) else ''
    village = own or e['village']
    rec['born_in'] = f"{village}, {e['opcina']}" if village else e['opcina']
    if e['list'] == 'fallen':
        d = DEATH.search(info)
        years = re.findall(r'\b(19[34]\d)\b', info[d.start():]) if d else []
        rec['death_year'] = years[0] if years else ''
        when = re.search(r'\b\d{1,2}\.\s?\d{1,2}\.\s?19[34]\d', info[d.start():]) if d else None
        parsed = parse_when(when.group(0)) if when else None
        rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
        rec['additional_info'] = f'{where}: {info}'
    else:
        rec['death_year'] = rec['death_date'] = ''
        rec['additional_info'] = f"{LISTS['spomenica']}, {where}: {info}"
    rec['list'] = LISTS[e['list']]
    rec['no'] = e['no']
    rec.update(pdf_file=book['pdf'], pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


def main(book: dict) -> None:
    out = HERE / 'znaci' / (book['pdf'].replace('.pdf', '') + '-entries.json')
    ofz.corpus()
    place_corpus()
    raw = read(book)
    recs = [parse(book, e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {out.relative_to(HERE.parent)}; {dict(Counter(r["list"] for r in recs))}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    # the numbers run 1, 2, 3 ... under each village: a gap is an entry the reader missed
    gaps, prev = [], None
    for r, e in zip(recs, raw):
        key = (e['list'], e['opcina'], e['village'])
        if prev and prev[0] == key and r['no'] != prev[1] + 1:
            gaps.append(f"{e['village']} {prev[1]}->{r['no']} (p{r['pdf_page']})")
        prev = (key, r['no'])
    print(f'number gaps: {len(gaps)}', gaps[:40])
    print(f"no birth year: {sum(not r['birth_year'] for r in recs)}, no father: {sum(not r['fathers_name'] for r in recs)}, "
          f"no given name: {sum(not r['first_name'] for r in recs)}, fallen without a death year: "
          f"{sum(not r['death_year'] for r in recs if r['list'] == LISTS['fallen'])}")
    if '--sample' in sys.argv:
        random.seed(3)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} | p{r['pdf_page']}")
            print(f"      {r['additional_info'][:150]}")
