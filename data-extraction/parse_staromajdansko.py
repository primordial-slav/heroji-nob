"""
Staromajdansko područje u NOB 1941-1945. godine (Poreklo library): "Poginuli borci i učesnici NOR-a i žrtve fašističkog
terora; umrli borci i učesnici NOR-a ...; živi borci i učesnici NOR-a ... i nosioci Partizanske spomenice 1941.", the
Stari Majdan area of the Sanski Most municipality village by village, as a book across units.

Under each village (a heading in spaced capitals, "D E M 1 S Е V C 1") stand "Borci poginuli u NOR-u:" and "Žrtve
fašističkog terora:"; only the first go in, an entry a paragraph, the first line indented: "DAMJANOVIĆ Maksima
DRAGAN, rođen 1922. godine, stupio u NOB početkom 1942. godine, poginuo novembra 1943. godine kod Bihaća;" (scan
pp. 177-246, fetched on 2026-10-19 and 10-20; a victim goes in only where his entry names him one of the movement's,
and none does). After them, names only, run on under each village in two columns (pp. 247-266): the "borci i
učesnici rata" who had died since the war and those living at the start of 1983, marked `role: 'participant'`, and
the holders of the Partizanska spomenica 1941.

The names are read as the Sanski Most book's (`parse_sanski_most.parse`, the same area and the same kind of list):
the surname and the given name in capitals, the father between, carons the OCR lost read back from the site's names.

Output: data-extraction/poreklo/staromajdansko-entries.json (IDs 9063xxxxxx in each list's order: the fallen from
9063000001 and the men split out of the entry before them from 9063009001 (`split_glued`), the victims from 9063010001, the died since the war from 9063020001, the living from 9063030001, the
spomenica's holders from 9063040001).
Usage: python data-extraction/parse_staromajdansko.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import parse_ofanziva_1942 as ofz  # noqa: E402
import _karlovac_lists as kl  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
import parse_sanski_most as sm  # noqa: E402
from parse_ostrvica import death_of, level_lines  # noqa: E402
from parse_vrebac import columns  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'staromajdansko.json'
OUT = HERE / 'poreklo' / 'staromajdansko-entries.json'
PREFIX = '9063'
PAGES = range(177, 247)             # the villages' lists: scan pp. 177-216 fetched on 2026-10-19, 217-246 on 10-20
VICTIMS_LIST = 'Žrtve fašističkog terora'
# the lists of the people who lived through the war, names only, run on, under each village, in two columns ("BRDARI:
# MUNJIZA Lazara Velimir, ..."): IDs from PREFIX + base; `role` 'participant' where the list names "borci i učesnici
# rata" together (the user's decision of 2026-10-20: in, marked, since no word tells a fighter from an activist)
NAME_LISTS = [(range(247, 253), 'Umrli borci i učesnici rata od završetka NOR-a do početka 1983. godine', 20000,
               'participant'),
              (range(253, 265), 'Živi borci i učesnici rata na početku 1983. godine', 30000, 'participant'),
              (range(265, 267), 'Nosioci Partizanske spomenice 1941. godine', 40000, None)]
# given names and fathers whose Đ the OCR read as B or D ("Виго" Buro = Đuro, "Durđa", "Borda" = Đorđa)
DJ = {'Buro': 'Đuro', 'Duro': 'Đuro', 'Burađ': 'Đurađ', 'Durađ': 'Đurađ', 'Durđa': 'Đurđa', 'Dure': 'Đure',
      'Burđa': 'Đurđa', 'Bure': 'Đure', 'Dordo': 'Đorđo', 'Borda': 'Đorđa', 'Dorde': 'Đorđe', 'Borde': 'Đorđe',
      'Duka': 'Đuka', 'Dukan': 'Đukan', 'Dula': 'Đula', 'Dura': 'Đura', 'Bordo': 'Đorđo', 'Burica': 'Đurica',
      'Dorda': 'Đorđa', 'Durda': 'Đurđa', 'Buja': 'Đuja', 'Durdević': 'Đurđević'}
OFFSET = 0                                  # the scan's pages are the book's
TITLE = 'Staromajdansko područje u NOB 1941-1945. godine'
LIST = 'Borci poginuli u NOR-u'
# the two headings as the OCR gives them: "Borci", "Ват!", "Banci poginuli u NOR-u:", "Poginuli borci u NOR-u:";
# "Žrtve", "Žnve", "Žn've fašističkog terora:", "Žnve _fášisričkog terora:" (Usorci's, whose victims were read as
# fallen fighters before 2026-10-20)
FALLEN = re.compile(r'^(?:\S+\s+poginul\w*|Poginul\w*\s+borc\w*)\s+\S+\s+NOR', re.I)
VICTIMS = re.compile(r'^Ž\S*\s+(?:fa[sš]|[_\W]*f\S*\s+teror)', re.I)
# the page's running head, as the OCR garbles it ("15. Staromqjdansko područje u NOB", "Ib. Suiromajdansko područje")
RUNNING_HEAD = re.compile(r'\w*m\w*jdansko\s+područje', re.I)
# the headings' carons the OCR lost, and "OŠTRALUKA" printed as one word
VILLAGE_FIX = {'Alisici': 'Ališići', 'Demisevci': 'Demiševci', 'Pobrijezje': 'Pobriježje', 'Oštraluka': 'Oštra Luka',
               'Podvidaca': 'Podvidača', 'Ostraluka': 'Oštra Luka', 'Ostra Luka': 'Oštra Luka', 'Dzevar': 'Dževar',
               'Okrec': 'Okreč', 'Suhaca': 'Suhača', 'Nistovci': 'Ništovci', 'Starimajdan': 'Stari Majdan',
               'Stararijeka': 'Stara Rijeka', 'Husimovći': 'Husimovci', 'Suhaća': 'Suhača', 'Ališiči': 'Ališići', 'Dževak': 'Dževar', 'Čirkici': 'Čirkići',
               # a heading run into the line before it in the names-only lists
               'Nob Nistovci': 'Ništovci', 'Rata Od Završetka Č I R K I C I': 'Čirkići'}
# Cyrillic letters the OCR set in a Latin name, as the Latin they look like ("Реге" Pere)
LOOKALIKE = str.maketrans('АВЕКМНОРСТХаеорсухнвтгмкиЈј', 'ABEKMHOPCTXaeopcyxhbtrmkuJj')


def heading(t: str) -> str:
    """a village's heading, its letters spaced and read with 1 for I and 0 for O ("A L 1 S 1 C 1" = ALIŠIĆI is printed
    so, the caron lost); else ''"""
    t = t.translate(LOOKALIKE).strip()
    words = t.split()
    if len(words) > 2 and all(len(w) <= 2 for w in words):
        t = ''.join(words)
    t = t.replace('1', 'I').replace('0', 'O')
    return t if sm.is_village(t) and not re.search(r'TEROR|NOR|POGIN', t) else ''


def raw_entries(book: dict) -> list[dict]:
    out, village, kind, ended = [], '', '', True
    for page in PAGES:
        for l in level_lines(page_words(book, page)):
            t = re.sub(r"^[•·■*^_'’`]+\s*", '', l.text.strip())
            t = re.sub(r"^'I'", 'T', t)                                   # "'I'RKULJA" = TRKULJA
            if re.fullmatch(r'\d{1,3}', t) or re.search(r'Staro\w*\s+područje u NOB \d+$', t):
                continue
            h = heading(t)
            if h and not re.search(r',', t):
                village, kind, ended = h, '', True
                continue
            if FALLEN.match(t):
                kind, ended = 'fallen', True
                continue
            if VICTIMS.match(t):
                kind, ended = 'victims', True
                continue
            was_ended, ended = ended, bool(re.search(r'[;.:]\s*$', t))
            if kind not in ('fallen', 'victims'):
                continue
            if sm.START.match(t) and re.match(r'^[^,]{3,70},', t) and was_ended:
                out.append({'kind': kind, 'list': LIST if kind == 'fallen' else VICTIMS_LIST, 'village': village,
                            'lines': [t], 'line_pages': [page], 'page': page, 'pdf_page': page, 'pdf_x': 0,
                            'pdf_y': 0})
            elif out and out[-1]['page'] in (page, page - 1):
                out[-1]['lines'].append(t)
                out[-1]['line_pages'].append(page)
    return out


def split_glued(raw: list[dict]) -> list[dict]:
    """The fallen entries' running heads dropped, and the men glued into an entry before them split out: an entry
    whose surname the OCR set with l for I ("RAJLlĆ Mile MIRKO", "VASlLJEVIĆ Nike BRANKO"), which the start's
    pattern misses, one after a running head, which hid the line before it ending the entry, one the OCR set on the
    line of the entry before ("...; STANKOVIĆ Buta OSTOJA, rođen"), and one whose name ends at a full stop ("ANTONIČ
    lOve_ MARA. rođena"). They come after the others (`late`), so the first reading's numbers stay put."""
    U = 'A-ZČĆŽŠĐl'
    inline = re.compile(rf'(?<=;)\s+(?=[{U}]{{3,}}["“”]?\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[{U}]{{2,}}\s*,)')
    def head_of(line: str) -> str:
        return re.sub(r'^([A-ZČĆŽŠĐ]+)["“”]', r'\1', read_l(line))             # "MRŠIĆ" Živka MILAN"

    late = []
    for e in raw:
        if e['kind'] != 'fallen':
            continue
        kept = [(piece.translate(LOOKALIKE), pg) for ln, pg in zip(e['lines'], e['line_pages'])
                if not (RUNNING_HEAD.search(ln) and len(ln.split()) <= 8) for piece in inline.split(ln)]
        cuts = [i for i in range(1, len(kept)) if re.search(r'[;.:]\s*$', kept[i - 1][0])
                and sm.START.match(head_of(kept[i][0]))
                and re.match(r'^[^,]{3,70},|^[^,.]{3,70}\.\s+ro[dđ]en', kept[i][0])]
        parts = [kept[a:b] for a, b in zip([0] + cuts, cuts + [len(kept)])]
        e['lines'], e['line_pages'] = [ln for ln, _ in parts[0]], [pg for _, pg in parts[0]]
        for part in parts[1:]:
            late.append({**e, 'lines': [head_of(part[0][0])] + [ln for ln, _ in part[1:]],
                         'line_pages': [pg for _, pg in part], 'page': part[0][1], 'pdf_page': part[0][1],
                         'late': True})
    return raw + late


VILLAGES = {'ALIŠIĆI', 'AVCI', 'BATKOVCI', 'BRDARI', 'ČIRKIĆI', 'DEMIŠEVCI', 'DONJI KAMENGRAD', 'DŽEVAR', 'GARAVICA',
            'GORNJI KAMENGRAD', 'HUSIMOVCI', 'KOPRIVNA', 'MOVCI', 'NIŠTOVCI', 'OKREČ', 'OŠTRA LUKA', 'POBRIJEŽJE', 'PODLUG',
            'PODVIDAČA', 'RASAVCI', 'STARA RIJEKA', 'STARI MAJDAN', 'SUHAČA', 'USORCI', 'ZECOVI'}


def near_village(word: str) -> str:
    """the village whose name the word is but for one letter (the OCR's "DŽEVAK" for DŽEVAR), else ''"""
    def fold(s):
        return s.translate(str.maketrans('ČĆŠŽĐ', 'CCSZD'))
    for v in VILLAGES:
        a, b = fold(word), fold(v)
        if len(a) == len(b) and sum(x != y for x, y in zip(a, b)) <= 1 and len(a) > 3:
            return v
    return ''


# the names-only lists' slips no rule reads, as the line around them shows: four village headings ("U 5 0 R c I-."
# for USORCI:), a name the OCR ran together or broke with a comma, and letters it misread ("iiije" Ilije, "siipe
# Peiar" Stipe Petar, as Stara Rijeka's "SEDIC Stipe Mato" in the list before)
LINE_FIXES = [("PODVIDA'CA:", 'PODVIDAČA:'), ('BATKOVCk', 'BATKOVCI:'), ('PoaRllEžJE-', 'POBRIJEŽJE:'),
              ('U 5 0 R c I-.', 'USORCI:'), ('STARA RIJEKA-.', 'STARA RIJEKA:'), ("VRUL'INIĆ", 'VRUĆINIĆ'),
              ('JAHlĆHuske', 'JAHIĆ Huske'), ('Džanana..Eniz', 'Džanana Eniz'), ('KANTAR, Ilije', 'KANTAR Ilije'),
              ('JOvana', 'Jovana'), ('MiliĆije', 'Milićije'), ('Cvitka JOZO', 'Cvitka Jozo'), ('siipe Peiar', 'Stipe Petar'),
              ('iiije', 'Ilije'), ('Veijko', 'Veljko'), ("V'Ida", 'Vida'), ('Todora, Aleksa', 'Todora Aleksa'),
              ('GAJIC Vase, Jovo', 'GAJIC Vase Jovo'), ('KURUZOVIĆ M Husein', 'KURUZOVIĆ M. Husein'),
              ('ČOROKALO Čolić L.', 'ČOROKALO ČOLIĆ L.'), ('Boškadovan', 'Boška Jovan'),
              ('HADŽIĆ kae Rahmo', 'HADŽIĆ Rahmo'),         # the father past reading
              ('VRUĆINIC Sime ieiu.', '')]                  # the given name past reading: left out


def read_l(t: str) -> str:
    """The OCR's l for I in the names-only lists: in a word in capitals ("VUJKOVlĆ", "TlNTOR", "ZECOVl'"), and at the
    start of a father or given name before a consonant ("llije" = Ilije, "lve" = Ive), whose names the name pattern
    lost; its C' for Ć before a name ("GOLUBOVIC' Nikole Stana", which it took for a village's heading) and 'C for Ć
    ("'Cire"); "vid" and "vida" with their capital lost; and LINE_FIXES"""
    t = re.sub(r'(?<!\w)[A-ZČĆŽŠĐl]{2,}(?!\w)',
               lambda m: m.group(0).replace('l', 'I') if re.search('[A-ZČĆŽŠĐ]', m.group(0)) else m.group(0), t)
    t = re.sub(r'(?<!\w)l(?=[b-df-hk-np-tv-zčćšžđ])', 'I', t)
    for old, new in LINE_FIXES:
        t = t.replace(old, new)
    t = re.sub(r"(?<!\w)['’]C(?=[a-zčćžšđ])", 'Ć', t)
    t = re.sub(r'(?<!\w)vid(a?)(?!\w)', r'Vid\1', t)
    return re.sub(r"(?<=[A-ZČŽŠĐ]{2})C['’](?=\s+[A-ZČĆŽŠĐ][a-zčćžšđ])", 'Ć', t)


def name_entries(book: dict) -> list[dict]:
    """The names-only lists: "SURNAME Father Given," run on under "VILLAGE:", the page's two columns read in turn"""
    U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
    token = re.compile(rf'⟦(?P<page>\d+)⟧|(?P<village>(?:[{U}01l]\s?){{4,}}?)\s*[:;’\']+[\s.,]'
                       rf'|(?P<last>[{U}]{{2,}}(?:-[{U}]{{2,}})?)(?:\s+(?P<also>[{U}]{{3,}}))?\s+'
                       rf'(?:(?P<father>[{U}][{L}]+|[{U}]\.)\s+)?(?P<given>[{U}][{L}]+(?:-[{U}][{L}]+)?)\s*[,.;]?')
    out = []
    for pages, title, base, role in NAME_LISTS:
        parts = []
        for page in pages:
            parts.append(f'⟦{page}⟧')
            for l in columns(book, page):
                t = read_l(l.text.translate(LOOKALIKE).strip())
                if re.fullmatch(r'\d{1,3}', t) or (re.search(r'GODINE|BORCI|NOSIOCI|SPOMENIC|PARTIZANSK|UČES|UCES|'
                                                             r'NOR—a|NOR-a|POČETKU|POCETKU|ZAVRŠETKA|ZAVRSETKA', t)
                                                   and ',' not in t):
                    continue                                      # the list's title and the page numbers
                bare = re.sub(r'[^A-ZČĆŽŠĐ ]', '', t.replace('1', 'I').replace('0', 'O'))
                if ',' not in t and ':' not in t and (bare.replace(' ', '') in {v.replace(' ', '') for v in VILLAGES}
                                                       or near_village(bare)):
                    t = f'{t}:'                                   # a heading the book set without its colon
                parts.append(t)
        text = re.sub(r'\s+\d{3}\s+', ' ', ' '.join(parts))     # a page number run into the names ("Branko, 265 KNEŽ")
        page, village, n = pages[0], '', 0
        for m in token.finditer(text):
            if m.group('page'):
                page = int(m.group('page'))
            elif m.group('village'):
                h = heading(m.group('village').replace('l', 'I'))
                v = VILLAGE_FIX.get(sm.village_name(h), sm.village_name(h)).upper() if h else ''
                if h and (v in VILLAGES or near_village(v)):       # one of the area's villages, not a surname
                    village = h
            elif village:
                if m.group('also') and near_village(m.group('last')):
                    # a heading whose colon the OCR lost, before the first name under it ("DŽEVAK DAMJANOVIĆ Todora
                    # Branko" for "D Ž E V A R:" and Damjanović)
                    village = near_village(m.group('last'))
                    m = token.match(m.group(0)[len(m.group('last')):].lstrip())
                    if not m or not m.group('last'):
                        continue
                n += 1
                if m.group('also') and re.fullmatch(r'[ĆČ]?I[ĆČ]|VI[ĆČ]', m.group('also')):
                    last, also = kl.spelled(m.group('last') + m.group('also'), 'last'), []    # "GRUJ ĆIĆ" = Grujčić
                else:
                    last = kl.spelled(m.group('last'), 'last')
                    also = [kl.spelled(m.group('also'), 'last')] if m.group('also') else []
                # the names lists' -ič and -ic are the OCR's -ić (the area's surnames are all -ić: "PLAVŠIČ",
                # "RIVIC"), and its Đ read as D ("DURDEVIĆ")
                last, *also = [DJ.get(x, x) for x in (re.sub(r'i[čc]$', 'ić', x) for x in (last, *also))]
                father = m.group('father') or ''      # a woman's or a man's name printed without it
                father = DJ.get(father, father)
                given = DJ.get(m.group('given'), kl.spelled(m.group('given').upper(), 'first'))
                v = VILLAGE_FIX.get(sm.village_name(village), sm.village_name(village))
                printed = ' '.join(x for x in (m.group('last'), m.group('also'), m.group('father'), m.group('given')) if x)
                out.append({'soldier_id': f'{PREFIX}{base + n:06d}',
                            'name': ' '.join(x for x in (last, father, given) if x), 'last_name': last, 'also': also,
                            'first_name': given, 'nick': '', 'fathers_name': '' if father.endswith('.') else father,
                            'birth_year': '', 'born_in': f'{v}, Sanski Most', 'death_year': '',
                            **({'survived': True} if role else {}), **({'role': role} if role else {}),
                            'additional_info': f'{title}, {v}: {printed}', 'list': title, 'book_title': TITLE,
                            'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
    return out


# a holder of the spomenica who lived past the war stands in the 1983 list of the died or the living too (42 of the
# 64): one man, one entry with his line in both lists and no role, since the book counts him among its fighters of
# 1941 as the other books' spomenica lists are counted; matched on surname, father, given name and village, and by
# hand where the OCR spoiled one side (TWINS, by the names as printed: the twin's, and whose names the entry keeps)
TWINS = {'ČOROKALO MILJEVIĆ Dragutina Branko': ('ČOROKALO Miljević Branko', 'spomenica'),   # the died list prints no
         #                                                         father, and its "Miljević" is his second surname
         'BABIĆ Dune Ilija': ('BABIĆ Dure Ilija', 'twin')}        # the spomenica list's "Dune" is the OCR's Đure


def join_spomenica(names: list[dict]) -> list[dict]:
    def fold(s: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if not unicodedata.combining(c)).replace('đ', 'd')

    def key(e: dict) -> tuple:
        return fold(e['last_name']), fold(e['fathers_name'])[:4], fold(e['first_name']), e['born_in']

    printed = lambda e: e['additional_info'].split(': ', 1)[1]
    by_printed = {printed(e): e for e in names if e['list'] != NAME_LISTS[2][1]}
    by_key = defaultdict(list)
    for e in names:
        if e['list'] != NAME_LISTS[2][1]:
            by_key[key(e)].append(e)
    gone, joined = set(), set()
    for e in (e for e in names if e['list'] == NAME_LISTS[2][1]):
        if printed(e) in TWINS:
            tname, keep = TWINS[printed(e)]
            twin = by_printed[tname]
        elif len(by_key[key(e)]) == 1:
            twin, keep = by_key[key(e)][0], 'twin'
        else:
            continue
        assert twin['soldier_id'] not in joined, twin['soldier_id']
        if keep == 'spomenica':
            twin.update({k: e[k] for k in ('name', 'last_name', 'also', 'first_name', 'fathers_name')})
        twin['additional_info'] += '. ' + e['additional_info']
        twin.pop('role', None)
        joined.add(twin['soldier_id'])
        gone.add(e['soldier_id'])
    return [e for e in names if e['soldier_id'] not in gone]


def main():
    ofz.corpus()
    book = load(BOOK)
    entries, counts, n_fallen, n_victims, n_late = [], Counter(), 0, 0, 0
    for e in split_glued(raw_entries(book)):
        if e.get('late'):
            n_late += 1
            i = 9000 + n_late              # the men split out of the entry before them, from 9063009001
        elif e['kind'] == 'fallen':
            n_fallen += 1
            i = n_fallen
        else:
            n_victims += 1
            i = 10000 + n_victims          # the victims from 9063010001 (only the movement's people among them go in)
        e['lines'] = [ln.translate(LOOKALIKE) if re.search('[А-Яа-я]', ln) else ln for ln in e['lines']]
        r = sm.parse(e, i)
        if e.get('late') and not re.search(r'stupi\w*\s+u\s+NOB|\bborac\b', ' '.join(e['lines']), re.I):
            # a victim the heading over him lost, glued to the fallen before him (Rasavci's "ANTONIČ Ive MARA, ...
            # ubijena na Brdarima"): as the victims
            e['kind'] = 'victims'
        if e['kind'] == 'victims':
            # a victim the entry names as one of the movement's (the user, 2026-10-20: "any adjacent people who count
            # as activists"), or a fighter the book set among the victims; never one without such a word
            text = ' '.join(e['lines'])
            if mos.fighter_or_officer({'additional_info': text}):
                counts['victims: fighters'] += 1
            elif mos.activist({'additional_info': text}):
                r['role'] = 'activist'
                counts['victims: activists'] += 1
            else:
                counts['victims: out'] += 1
                continue
        for k in ('pdf_file', 'pdf_page', 'pdf_x', 'pdf_y', 'kind'):
            r.pop(k, None)
        village = VILLAGE_FIX.get(sm.village_name(e['village']), sm.village_name(e['village']))
        info = r['additional_info'].split(': ', 1)[1] if ': ' in r['additional_info'] else r['additional_info']
        info = re.sub(r'["“”„]\s*(?=godine)', '', info)                     # "krajem 1944. "godine"
        if re.search(r'i[čc]$', r['last_name']):
            # the OCR's -ič and -ic for -ić, which the site's corpus keeps for some of these names ("GLIGIČ", "PLAVŠIČ")
            r['last_name'] = re.sub(r'i[čc]$', 'ić', r['last_name'])
            r['name'] = ' '.join([r['last_name']] + r['name'].split()[1:])
        if r['first_name'].lower() == 'borac':
            # a given name the OCR garbled past reading, the parser's next word taken for it ("BARUDŽIJA Ostoje buho,
            # borac"): left empty, the text has it as printed
            r['first_name'], r['name'] = '', r['last_name']
        death = death_of(info)
        title = LIST if e['kind'] == 'fallen' else VICTIMS_LIST
        r.update({
            'soldier_id': f'{PREFIX}{i:06d}',
            'born_in': f'{village}, Sanski Most',
            'additional_info': f'{title}, {village}: {info}',
            'death_year': death.get('year') or r.get('death_year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            'survived': False,
            'list': title, 'book_title': TITLE,
            'source_url': viewer_url(book, e['page']), 'source_page': e['page'] - OFFSET,
        })
        if not r.get('death_place') and death.get('place'):
            r['death_place'] = death['place']
        entries.append(r)
    names = join_spomenica(name_entries(book))
    entries += names
    counts.update(r['list'] for r in names)
    counts['spomenica holders in a list of 1983'] = sum('. Nosioci Partizanske' in r['additional_info'] for r in names)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, f'fallen {n_fallen},', dict(counts))
    print(Counter(r['born_in'] for r in entries).most_common())
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} {r['birth_year']} [{r['born_in']}] "
                  f"† {r['death_year']} {r.get('death_place', '')!r} | {r['additional_info'][:110]}")


if __name__ == '__main__':
    main()
