"""
Parser: Zaščitna enota vojaško-političnega vodstva NOB Slovenije (brigade code 150), the partisan unit that guarded the
CK KPS, the IO OF and their bases.

Source: Mira Mihevc, *Na nevarnih poteh. Razvoj zaščitne enote vojaško političnega vodstva narodnoosvobodilnega boja
        Slovenije 1943/1945* (Skupnost borcev zaščitne enote VPV Slovenije, Ljubljana 1995; Knjižnica NOV in POS
        55/2; znaci.org 00003/757.pdf, PDF pp. 291-308) → website/public/pdfs/zascitna-enota-vpv.pdf (book pp. 293-310).
Four lists, two columns, each entry hanging:
    site pp. 1-12   "Pripadniki zaščitne enote vojnopolitičnega vodstva NOV in POS": the members who lived through the
                    war, "Anžur Anton-Bernard, 18.11.1913, Podmolnik; 24; † 1971" (given name and partisan name, the
                    birth, after the semicolon the VPV bases or units served in, a dagger and the year for one who
                    has died since)
    site pp. 13-14  "Padli borci": "Anžič Tone-Beli; Dolomiti; † 1944, Rigel" (the year and place of death)
    site p. 15      "Narodni heroji" (six, each also in one of the lists above)
    site pp. 17-18  "Nosilci Partizanske spomenice 1941" (names only, all of them members above)
The OCR reads the dagger as "ft", "tf", "$", "9", "D", "*", "■f" and the like: a year other than the birth date's is
the year of death, and the dagger is put back before it. The parser sets the fields (PARSER_FIELDS): birthplace, the
bases as the unit detail ("baza 20, baza 24"), the death. The heroes' and spomenica holders' entries are merged into
the members' records by corrections.
Usage: python data-extraction/parse_zascitna_enota.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
from _parser_scaffold import _record, run_parser  # noqa: E402

PDF = HERE.parent / 'website' / 'public' / 'pdfs' / 'zascitna-enota-vpv.pdf'
SOURCE = HERE / '.cache' / 'mihevc' / '757.pdf'                    # znaci.org/00003/757.pdf
OUTPUT = HERE.parent / 'website' / 'public' / 'zascitna-enota-soldiers.json'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LISTS = {**{p: 'clan' for p in range(1, 13)}, 13: 'padli', 14: 'padli', 15: 'heroj', 17: 'spomenica', 18: 'spomenica'}
TITLE = {'clan': '', 'padli': 'Padli borci: ', 'heroj': 'Narodni heroj: ',
         'spomenica': 'Nosilec Partizanske spomenice 1941: '}
NAME = re.compile(rf'^[{U}][{L}]+(?:\s?-\s?[{U}][{L}]+)?(?:\s+roj\.\s+[{U}][{L}]+)?\s+[{U}][{L}]+')
DATE = r'\d{1,2}\.\s?\d{1,2}[.-]\s?(?:1[89]\d\d)'
NICK = rf'(?:-[{U}][{L}]+|\s[{U}][{L}]+)?(?:\s+roj\.\s+[{U}][{L}]+)?'
STRONG = re.compile(NAME.pattern + NICK + rf',\s*(?:{DATE}|1[89]\d\d\b)')
WEAK = re.compile(NAME.pattern + NICK + r'\s*[,;]|' + NAME.pattern + rf'(?:-[{U}][{L}]+)?\s+roj\.$')   # "... roj." / "Becele,"
# the OCR's readings of the dagger before a year (or a day and month, or a month): "■f", "ft", "$", "9", "1>" ...
DAGGER = r"(?:■\S{0,2}|[ftlJ]{1,2}1?|tf|ti1|i\)1|\$|9|D|\*|'\?|'i|'t|<t|4|0|-f|1\)|1>|i>|1\?|v|e|f)"
WHEN = r'(?:\d{1,2}\.\s?\d{1,2}\.\s?|[a-z]+\s+)?(?:19|20)\d\d'
# names the OCR garbled (the page is re-typeset from it, so it shows them too): its c read as e at a word's end
# ("Tornine" = Tominc, whom the 1964 census has fall in 1942 at Ambrus, as the list does), its k as h (Završnik, in
# the census at Glažuta), its v as u, a caron lost under the list's Ž, the heroes' list's spelling of Henrik
NAMES = {'Tornine': 'Tominc', 'Završnih': 'Završnik', 'Martine': 'Martinc', 'Župane': 'Županc', 'Hernrik': 'Henrik',
         'Juže': 'Jože', 'Zabkar': 'Žabkar', 'Zidan': 'Židan', 'Debeuc': 'Debevc', 'Ausec': 'Avsec',
         'Ćerpič': 'Čerpič'}
BASES = {'Dolomiti', 'Novi breg', 'Podlipoglav', 'Tisovec', 'Zaščitna patrola', 'Avstrijska baza', 'Doblička gora'}


def build_pdf() -> None:
    if not PDF.exists():
        out = fitz.open()
        out.insert_pdf(fitz.open(SOURCE), from_page=290, to_page=307)
        out.save(PDF, garbage=4, deflate=True)


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """Each entry as one line, "§<list>§ " and its text: an entry starts left of the hanging lines, with a name; its
    lines are joined here (the scaffold would drop a line that is only a base's number, "20"). Headings, letters,
    page numbers and the footnote are dropped."""
    out = []
    for ln in lines_of(pdf_path):
        if ln['text'].startswith('§'):
            out.append(dict(ln))
        elif out:
            prev = out[-1]['text']
            out[-1]['text'] = (prev[:-1].rstrip() if prev.endswith('-') and ln['text'][:1].islower() else prev + ' ') + ln['text']
    return out


def lines_of(pdf_path: str) -> list[dict]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            kind = LISTS.get(pno)
            if not kind:
                continue
            for col in entry_boxes.read_page(page, columns=2)['columns']:
                lines = [ln for ln in col if not re.fullmatch(r'[A-ZČŠŽ]|[a-zčšž]|\d{3}|c|o|s|z|š|ž|č', ln['text'].strip())]
                lines = [ln for ln in lines if not re.search(r'PRIPADNIKI|POLITIČNEGA|ENOTE VOJNO|NOV IN POS|^PADLI BORCI|'
                                                             r'^NARODNI HEROJI|^NOSILCI|^SPOMENICE 1941|'
                                                             r'^\d\d Za rojstnimi|navedena imena oz', ln['text'])]
                starts = ([ln['x0'] for ln in lines if STRONG.match(fix(ln['text']))]
                          or [ln['x0'] for ln in lines if WEAK.match(fix(ln['text']))])    # the fallen give no birth
                left = min(starts) if starts else 0
                prev = None
                for ln in lines:
                    t = fix(ln['text'])
                    # a name and a birth date or year always start an entry; a name and a comma or semicolon only
                    # left of the hanging lines ("Mala Dobrava; 24" runs on), where the line before closed its
                    # entry; the spomenica list is a name a line
                    if kind == 'spomenica':
                        is_start = bool(NAME.match(t))
                    else:
                        weak = WEAK.match(t) or kind == 'padli' and re.match(rf'^[{U}][{L}]+;', t)   # "Savo; Novi breg"
                        is_start = bool(STRONG.match(t)) or bool(weak) and (
                            ln['x0'] <= left + 4 or prev is not None and ln['x0'] < prev['x0'] - 5
                            and not prev['text'].rstrip().endswith(','))
                    out.append({'text': (f'§{kind}§ ' if is_start else '') + t, 'x': round(ln['x0'], 1),
                                'y': round(ln['top'], 1), 'page': pno})
                    prev = ln
    return out


def fix(t: str) -> str:
    """"AličEdi" = Alič Edi; "Anžin Marija - Olga" = Anžin Marija-Olga; "Mar jek" = Marjek; the OCR's l for a
    capital I ("lzidor", "lvanov")"""
    t = re.sub(r'(?<=[a-zčšž])(?=[A-ZČŠŽ][a-zčšž])', ' ', t.strip())
    t = re.sub(rf'(?<=[{L}])\s+-\s*(?=[{U}])', '-', t)               # "Kozina Stane -Ribnčan" 
    t = re.sub(r'(?<=[\s-])l(?=[zvgnrdst][a-zčšž])', 'I', t)
    t = t.replace('Mar jek', 'Marjek').replace('Alfred-Suit an', 'Alfred-Sultan')
    return re.sub(rf'[{U}][{L}]+', lambda m: NAMES.get(m.group(0), m.group(0)), t)


def cleaned(text: str) -> str:
    """An entry's text as printed, its words joined again and its daggers put back"""
    t = re.sub(r'\s+', ' ', text).strip()
    t = re.sub(r'\xad\s*', '', t)                                       # a soft hyphen at a line's end
    t = re.sub(r'(?<=[a-zčšž])-\s(?=[a-zčšž])', '', t)                  # "Ljublja- na"
    t = re.sub(r'\bPodli\s+poglav\b', 'Podlipoglav', t)
    t = re.sub(r'\bDo\s?lo\s?miti\b', 'Dolomiti', t)
    t = re.sub(r'\bLjublja\s+na\b', 'Ljubljana', t)
    t = re.sub(r'(?<=\b25)i9(?=;)', '', t)                              # the footnote's mark, 49, on the first entry
    t = re.sub(r';\s*(?=\d{1,2}\.\s?\d{1,2}\.)', ', ', t, count=1)     # "Trček Matevž-Matko; 21.9.1921" 
    t = re.sub(r'(?<=\d\.\d)\.\s+(?=1[89]\d\d)|(?<=\d\.\d\d)\.\s+(?=1[89]\d\d)', '.', t)    # "16.4. 1923"
    return t


def birth(t: str) -> re.Match | None:
    """The birth: a date, else a year right after the name ("Puc Ivan-Don, 1905, Podkraj")"""
    head = t.split(';')[0]
    return re.search(DATE, head) or re.match(rf'^[^,;]*,\s*(1[89]\d\d)\b(?!\.\d)', head)


def daggers(t: str, start: int) -> str:
    """After the birth: the dagger the OCR garbled, or lost, before a year of death (or a day and month, or a
    month: "† 25.5.1944", "† december 1944"); a dagger left at the end with no year"""
    head, rest = t[:start], t[start:]
    rest = re.sub(rf'([;,]?)\s*{DAGGER}\s*({WHEN})\b', r'\1 † \2', rest)
    rest = re.sub(rf'([;,])\s*(?<!†\s)((?:19|20)\d\d)\b', r'\1 † \2', rest)
    rest = re.sub(r'([;,])\s*(?:\$|■\S{0,2})\s*$', r'\1 †', rest)
    rest = re.sub(r'\s[a-zA-Z■]\S?\s(?=†)', ' ', rest)                  # a stray mark beside the dagger
    return re.sub(r'\s+', ' ', head + rest).strip(' ;,')


def parse_entry(text: str) -> dict:
    m = re.match(r'^§(\w+)§\s*(.*)$', text, re.S)
    kind, t = m.group(1), cleaned(m.group(2))
    head = re.match(rf'^([{U}][{L}]+(?:-[{U}][{L}]+)?)(?:\s+roj\.\s+([{U}][{L}]+))?(?:\s+([{U}][{L}]+)'
                    rf'(?:-([{U}][{L}]+)|\s([{U}][{L}]+)(?=,))?)?(?:\s+roj\.\s+([{U}][{L}]+))?', t)
    last, maiden, given, nick, nick2, maiden2 = head.groups()
    nick, maiden = nick or nick2, maiden or maiden2
    if kind == 'spomenica':
        t = re.sub(r'\s+((?:19|20)\d\d)$', r' † \1', t)                # "Anžin Marija-Olga 1993"
    else:
        born = birth(t)
        t = daggers(t, born.end() if born else head.end())
    rest = t[head.end():].lstrip(' ,;')
    info = rest if kind in ('clan', 'padli') else TITLE[kind] + t
    notes = [f'zvani {nick}'] if nick and nick != given and kind in ('clan', 'padli') else []
    if maiden:
        notes.append(f'roj. {maiden}')
    rec = _record(last, given or '', '', '; '.join(notes + [info]) if notes else info)
    born = birth(t)
    rec['birth_year'] = (born.group(1) if born.groups() else born.group(0)[-4:]) if born else ''
    if rec['birth_year'] and int(rec['birth_year']) > 1935:
        rec['birth_year'] = ''                                         # "Černe Karel-Žan, 9.10.1984": the book's slip
    fields(rec, kind, t, born)
    return rec


def fields(rec: dict, kind: str, t: str, born: re.Match | None) -> None:
    """birth_place, unit_detail (the bases), death from the entry's parts; a base the OCR's lost semicolon left in
    the birthplace ("14.4.1908, Zalog, Novi breg, Podlipoglav, Dolomiti, 20") is moved to the bases"""
    parts = [p.strip() for p in t.split(';')]
    bases = []
    if born:
        place = parts[0][born.end():].strip(' ,')
        place = re.sub(r',?\s*†\s*[^,]*\d{4}', '', place).strip(' ,')    # "2.7.1913, † 1992, Tomačevo"
        words = [w.strip() for w in place.split(',') if w.strip()]
        # the first word is the birthplace even where a base bears its name (Podlipoglav, Tisovec)
        cut = next((i for i, w in enumerate(words) if i and is_base(w)), len(words))
        bases += words[cut:]
        place = ', '.join(words[:cut])
        if place and not re.search(r'\d|†', place):
            rec['birth_place'] = place
    else:
        place = re.sub(rf'^[{U}][{L}]+(?:-[{U}][{L}]+)?(?:\s+[{U}][{L}]+(?:-[{U}][{L}]+)?)?', '', parts[0]).strip(' ,')
        if place and not re.search(r'\d|†', place) and kind == 'clan':
            rec['birth_place'] = place                                 # "Breznik Werner-List, Maribor; ..."
    for p in parts[1:]:
        bases += [b.strip() for b in re.split(r',\s*', re.sub(rf'†\s*(?:{WHEN})?', '', p))]
    names = []
    for b in bases:
        if re.fullmatch(r'\d{2}(?:\s?A)?(?:\s*\(.*\))?', b):
            names.append('baza ' + re.sub(r'\s', '', b.split('(')[0]))
        elif b.split(' (')[0] in BASES:
            names.append(b.split(' (')[0])
    if names:
        rec['unit_detail'] = ', '.join(dict.fromkeys(names))
    d = re.search(r'†\s*((?:\d{1,2}\.\s?\d{1,2}\.\s?|[a-z]+\s+)?((?:19|20)\d\d))(?:,\s*([^;]+))?', t)
    if d:
        year = int(d.group(2))
        rec['death_type'] = 'poginuo' if kind != 'clan' and year <= 1945 else 'umro'
        rec['death_date'] = d.group(1)
        if kind != 'clan' and year <= 1945 and d.group(3):
            rec['death_place'] = re.sub(r',?\s*\(.*$', '', d.group(3)).strip(' .,')
    elif kind == 'padli':
        rec['death_type'] = 'poginuo'
    elif '†' in t:
        rec['death_type'] = 'umro'


def is_base(w: str) -> bool:
    return bool(re.fullmatch(r'\d{2}(?:\s?A)?', w)) or w in BASES


if __name__ == '__main__':
    build_pdf()
    run_parser(
        pdf_path=str(PDF),
        brigade_code=150,
        output_path=str(OUTPUT),
        extract_fn=extract,
        entry_start_re=re.compile(r'^§\w+§'),
        parse_entry_fn=parse_entry,
    )
