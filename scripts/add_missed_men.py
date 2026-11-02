"""
Men the parsers lost: an entry on the page that no record of the unit holds, found by holding each page's headings against
the records (2026-11-02). A surname whose capitals the scan broke with one small or odd letter ("ALEKSANDRIč", "KOJü",
"РИСТИТх") failed a parser's start of an entry, and its lines were dropped with it; the 1. konjička's reader dropped each
page's first rows as a heading.

MEN holds each man read from the page: (page, top of the heading's line, surname, father, given name[, note]). What follows
the name on the line, and the lines under it, are read from the page's own lines down to the next start. A re-parse would
shift the units' IDs, so they are corrections (`add`, ids from 009001 in the unit's block), right after the record above.

Run: python scripts/add_missed_men.py [--write START] (without --write it prints each record).
"""
import collections, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data-extraction'))
sys.stdout.reconfigure(encoding='utf-8')
import entry_boxes as EB
from name_utils import BRIGADE_CONFIGS, genitive_to_nominative

LAT = dict(zip('абвгдђежзијклмнопрстћуфхцчш', 'abvgdđežzijklmnoprstćufhcčš'))
LAT.update({'љ': 'lj', 'њ': 'nj', 'џ': 'dž'})
CYR = re.compile('[А-Яа-яЂђЉљЊњЋћЏџЈј]')

MEN = {
    '5-vojvodjanska.pdf': (82, [
        (2, 345, 'Aleksandrić', 'Milisava', 'Božidar'), (3, 171, 'Ališić', '', 'Milovan'), (3, 305, 'Andrić', '', 'Obrenija', 'rođ. Simić'),
        (3, 331, 'Andrić', '', 'Sava'), (3, 340, 'Andrić', '', 'Sreta'), (7, 492, 'Bajin', '', 'Proka'), (9, 136, 'Bartulović', '', 'Nikola'),
        (16, 88, 'Bradić', 'Dušana', 'Sava'), (18, 170, 'Buš', '', 'Stevan'), (18, 374, 'Civrić', '', 'Slavko'),
        (19, 94, 'Cuculić', 'Trive', 'Živana', 'rođ. Matijević'), (20, 150, 'Cvijović', '', 'Antun'), (24, 221, 'Dabrić', 'Dušana', 'Ivan'),
        (25, 483, 'Demajo-Breberina', 'Marka', 'Bosiljka'), (28, 356, 'Dragišić', '', 'Adam'), (30, 70, 'Dumjan', '', 'Milorad'),
        (35, 401, 'Frić', 'Marka', 'Stjepan'), (41, 423, 'Guzelić', '', 'Stevan'), (42, 102, 'Hadžić', '', 'Borivoj'), (42, 216, 'Hibuš', '', 'Đorđe'),
        (50, 191, 'Jevtić', '', 'Milorad'), (57, 102, 'Jozić', 'Mike', 'Mihajlo'), (57, 420, 'Kajfeš', 'Tome', 'Julijana'), (59, 256, 'Kepečki', 'Mitra', 'Momčilo'),
        (62, 459, 'Komanović', '', 'Dušan'), (63, 99, 'Komnenović', '', 'Drago'), (67, 232, 'Krmerić', '', 'Mato'), (67, 312, 'Krompić', 'Živote', 'Duško'),
        (69, 117, 'Kukuruzović', 'Nikole', 'Milan'), (69, 134, 'Kulundžić', '', 'Nikola'), (70, 191, 'Lakić', 'Steve', 'Dobra'), (74, 245, 'Mailović', '', 'Ilija'),
        (75, 61, 'Maksimčev', 'M.', 'Brana'), (85, 176, 'Milić', '', 'Dragić'), (92, 53, 'Munćan', '', 'Mirko'), (93, 185, 'Nedeljkov', '', 'Aca'),
        (96, 53, 'Nikolić', '', 'Vidoje'), (102, 273, 'Pavković', 'Antuna', 'Eva'), (109, 224, 'Popadić', 'Pante', 'Kuzman'), (111, 272, 'Poznanović', '', 'Mitar'),
        (111, 281, 'Poznanović', '', 'Sreta'), (111, 390, 'Prekogačić', '', 'Svetozar'), (111, 408, 'Prekogačić', 'Steve', 'Vasa'), (111, 426, 'Pribić', 'Radislava', 'Savo'),
        (116, 146, 'Rajinović', '', 'Joco'), (118, 77, 'Ranković', '', 'Ilija'), (120, 249, 'Rojić', '', 'Đuro'), (122, 56, 'Sarić', 'Bože', 'Živko'),
        (124, 172, 'Sičev', 'Antonija', 'Marko'), (127, 413, 'Stajčić', 'Lazara', 'Cveja'), (127, 430, 'Stajčić', 'Save', 'Danica', 'rođ. Simić'),
        (128, 385, 'Stanisavljević', '', 'Miloš'), (129, 393, 'Stanojčić', '', 'Kosa'), (134, 88, 'Straživuk-Nović', 'Radovana', 'Slavica'), (137, 56, 'Šomođi', 'Petra', 'Pavle'),
        (137, 250, 'Šulata', 'Milinka', 'Miloš'), (137, 303, 'Šuljmančević', '', 'Boro'), (137, 346, 'Šunjuković', 'Jovana', 'Nikola'), (137, 399, 'Šutović', '', 'Rade'),
        (138, 269, 'Tanjurdžić', '', 'Milan'), (139, 72, 'Tereček', 'Vase', 'Anđelka'), (139, 108, 'Tešera', '', 'Milorad'), (141, 222, 'Trestglavić', 'Vaselina', 'Dušan'),
        (142, 161, 'Tumić', '', 'Dimitrije'), (142, 447, 'Umrčić', 'Mihajla', 'Pavle'), (143, 345, 'Valok', '', 'Ratomir', 'zvani Radomir'), (144, 211, 'Vasiljević', '', 'Milutin'),
        (144, 457, 'Venjac', '', 'Nikola'), (146, 141, 'Višić', '', 'Šime'),
    ]),
    'cacanski-odred.pdf': (126, [
        (13, 8, 'Stanković', 'Miloša', 'Radosav'), (18, 32, 'Simović', 'Petra', 'Milun'), (30, 454, 'Živković', 'Dragoslava', 'Radiša'), (38, 42, 'Đoković', 'Živorada', 'Slavko'),
        (46, 51, 'Avramović', 'Dragutina', 'Milutin'), (60, 7, 'Ramović', 'D.', 'Filip'), (64, 409, 'Bogetić', '', 'Radovan'), (64, 519, 'Jocović', 'Jelesija', 'Bogoljub'),
        (69, 196, 'Vuković', 'Vukosava', 'Hranislav'), (69, 257, 'Vulićević-Minić', 'Filipa', 'Ljubica'), (69, 438, 'Grujičić', 'Milorada', 'Milica'), (69, 499, 'Dabović', 'Ranka', 'Radovan'),
        (70, 35, 'Dašić', 'Gavrila', 'Petko', 'zvani Kudro'), (74, 8, 'Maslovarić', 'Jovana', 'Radojko'), (76, 8, 'Obrenović', 'Dmitra', 'Miodrag'), (77, 90, 'Radosavljević', 'Radosava', 'Radojica'),
        (77, 127, 'Radosavčević', 'Vučka', 'Stevan'), (77, 164, 'Radulović', 'Miće', 'Aleksandar', 'zvani Cile'), (77, 191, 'Rajičić', 'Božidara', 'Milenko'), (77, 228, 'Ristić', 'Periše', 'Bogoljub'),
        (77, 256, 'Ristić', 'Milovana', 'Jovan'), (77, 284, 'Ristović', 'Božidara', 'Branko'), (77, 303, 'Ristović', 'Dmitra', 'Gordana', 'zvana Grozda'), (77, 331, 'Rosić', 'Spasoja', 'Sretko'),
        (77, 359, 'Savić', 'Aleksandra', 'Ljubiša'), (77, 460, 'Slavković', '', 'Slavoljub'), (77, 519, 'Spasić', 'Petra', 'Božidar', 'zvani Boka'), (78, 7, 'Spasić', 'Petra', 'Momčilo'),
        (78, 336, 'Stišović', 'Jezdimira', 'Slobodan', 'zvani Cale'),
    ]),
    'mosorski-odred.pdf': (148, [
        (18, 697, 'Belamarić', 'Josipa', 'Serđo'), (21, 414, 'Blašković', 'Tome', 'Jordan'), (53, 655, 'Filipović', 'Jakova', 'Ivan'), (61, 841, 'Ivković', 'Joze', 'Ivanka'),
        (66, 331, 'Jerčić', 'Ante', 'Ivan'), (66, 392, 'Jerčić', 'Mije', 'Mate', 'zvani Barbin'), (71, 446, 'Juričić', 'Ivana', 'Stipe'), (77, 368, 'Karaman', 'Jure', 'Jerolim'),
        (81, 766, 'Klarić', 'Petra', 'Ante'), (94, 328, 'Kuvačić', 'Spira', 'Petar'), (94, 387, 'Kuvačić', 'Ante', 'Stipe'), (103, 455, 'Maggiolar', '', 'Vicenzo'),
        (104, 411, 'Mandić', 'Frane', 'Ivan'), (104, 664, 'Mandić', 'Josipa', 'Petar-Veljko'), (105, 379, 'Manojlović', '', 'Mirko', 'zvani Krajišnik'), (110, 348, 'Marović', 'Jakova', 'Marin'),
        (113, 393, 'Mastelić', 'Marka', 'Jure'), (113, 454, 'Mašković', 'Petra', 'Marin'), (115, 485, 'Medić', 'Jure', 'Mate'), (115, 511, 'Medić', 'Jure', 'Vladimir-Vlade'),
        (118, 757, 'Mihovilović', 'Ante', 'Branko'), (122, 496, 'Miljković', 'Jerka', 'Lovre'), (130, 845, 'Ožegović', 'Petra', 'Nikola-Nikica'), (132, 333, 'Pandžić', 'Stipe', 'Ivan'),
        (134, 666, 'Pavičić', 'Marjana', 'Mate'), (136, 662, 'Penović', 'Ljube', 'Boris'), (137, 368, 'Perasović', 'Pavla', 'Augustin'), (138, 330, 'Perčić', 'Ante', 'Stipe'),
        (138, 407, 'Perčić-Matulj', 'Mate', 'Zorka'), (139, 655, 'Peričić', 'Ivana', 'Anka-Ane'), (139, 804, 'Peričić', 'Jure', 'Marin'), (150, 842, 'Prančić', 'Mate', 'Ivan'),
        (151, 388, 'Prančić', 'Grge', 'Mirko'), (155, 706, 'Radojević', '', 'Nikola'), (170, 810, 'Stanić', 'Marina', 'Ante'), (174, 380, 'Strujić', 'Jure', 'Ćiro'),
        (181, 805, 'Šurlić', 'Alberta', 'Milan'), (200, 511, 'Vujević', 'Ivana', 'Mate'), (204, 556, 'Vulić', 'Marina', 'Ivan'),
    ]),
    '1-konjicka.pdf': (92, [
        (6, 40, 'Gogić', '', 'Aleksandar'), (6, 40, 'Damljanović', '', 'Mirko'), (6, 50, 'Grbeša', '', 'Petar'), (6, 50, 'Damjanović', '', 'Petar'), (6, 60, 'Grković', '', 'Branko'),
        (6, 60, 'Damljanović', '', 'Vlado'), (6, 374, 'Jekić', '', 'Žarko'), (7, 40, 'Janković', '', 'Borivoje'), (7, 40, 'Lukić', '', 'Miloš'), (7, 50, 'Jovičić', '', 'Dragoljub'),
        (7, 50, 'Lukić', '', 'Živko'), (7, 60, 'Jovičić', '', 'Ivan'), (7, 60, 'Maletić', '', 'Milorad'), (7, 80, 'Maksimović', '', 'Bogoljub'), (7, 90, 'Maglovski', '', 'Đuro'),
        (7, 111, 'Marin', '', 'Živojin'), (7, 222, 'Mandel', '', 'Las'), (7, 232, 'Mandarić', '', 'Đuro'), (7, 272, 'Maslikosa', '', 'Dušan'), (7, 322, 'Marković', '', 'Milivoje'),
        (7, 363, 'Medić', '', 'Milan'), (7, 373, 'Medić', '', 'Lazo'), (7, 383, 'Miletić', '', 'Vaso'), (8, 42, 'Obradović', '', 'Borivoje'), (8, 42, 'Milosavljević', '', 'Radovan'),
        (8, 52, 'Obradović', '', 'Radivoje'), (8, 52, 'Milojica', '', 'Čedomir'), (8, 62, 'Obradović', '', 'Aleksandar'), (8, 62, 'Milojević', '', 'Špiro'), (9, 46, 'Radić', '', 'Jovan'),
        (9, 47, 'Stanković', '', 'Savo'), (9, 56, 'Radaković', '', 'Rade'), (9, 57, 'Stanimirović', '', 'Vitomir'), (9, 68, 'Stanojević', '', 'Nemanja'), (10, 42, 'Vukobrat', '', 'Vojin'),
        (10, 42, 'Tijanić', '', 'Živko'), (10, 52, 'Tomić', '', 'Rajko'), (10, 62, 'Vurdelja', '', 'Savo'), (11, 39, 'Marković', '', 'Desimir'), (11, 39, 'Skakić', '', 'Mileva'),
        (11, 49, 'Majstorović', '', 'Mane'), (11, 49, 'Petković', '', 'Vladimir'), (11, 58, 'Veličković', '', 'Vaso'), (11, 59, 'Masandžić', '', 'Drago'), (11, 68, 'Grujić-Petrović', '', 'Olga'),
    ]),
    '5-srpska.pdf': (127, [
        (20, 67, 'Anđelković', 'Milana', 'Vujoš'), (21, 405, 'Balug', 'N.', 'Stevan'), (24, 96, 'Vasiljević', '', 'Aleksandar'), (24, 181, 'Vasiljević', '', 'Sava'), (25, 385, 'Vujić', '', 'Milovan'),
        (37, 210, 'Jakovljević', 'Dragoljuba', 'Veselin'), (54, 384, 'Mihailović', '', 'Mita'), (73, 429, 'Stojnaljković', '', 'Dobrivoje'), (75, 334, 'Tripković', '', 'Svetislav'),
        (77, 224, 'Filipović', 'S.', 'Radiša'), (77, 246, 'Filipović', 'Gavrila', 'Radovan'),
    ]),
    '13-proleterska-spisak.pdf': (6, [
        (30, 109, 'Hartman', 'Josipa', 'Dragutin'), (76, 318, 'Požeg', '', 'Josip'), (80, 453, 'Rakitović', '', 'J.'), (82, 190, 'Rimac', '', 'Stjepan'),
        (90, 187, 'Stojiljković', 'Mihajla', 'Toma'), (96, 139, 'Todorović', 'Milutina', 'Milojko'), (96, 559, 'Tomašević', 'Milića', 'Miloš'), (98, 660, 'Turibi', '', 'Oskar'), (107, 658, 'Živanović', 'Bogdana', 'Dejan'),
    ]),
    '3-krajiska-spisak-boraca.pdf': (10, [
        (105, 99, 'Fistanić', 'Juraja', 'Tomislav'), (234, 520, 'Maričić', 'Jovana', 'Živomir'), (271, 367, 'Mladenović', 'A.', 'Dimitrije'), (456, 264, 'Vučković', 'Bož.', 'Stanko'),
    ]),
    '6-dalmatinska.pdf': (103, [(2, 346, 'Binić', '', 'Boža'), (7, 65, 'Krivić', 'F.', 'Filip')]),
    '8-kordunaska-divizija.pdf': (60, [(84, 164, 'Savić', 'Nikole', 'Savo'), (84, 211, 'Savić', 'Marka', 'Stanko')]),
    '7-srpska.pdf': (85, [(33, 226, 'Pavlović', 'V.', 'Đorđe'), (34, 69, 'Pajkić', 'Dimitrija', 'Đorđe'), (40, 200, 'Slampelić', 'V.', 'Dušan'), (42, 235, 'Ćulak', 'J.', 'Jura')]),
    '14-srednjobosanska.pdf': (56, [(34, 270, 'Gajić', 'V.', 'Radovan')]),
    '18-srpska.pdf': (128, [(89, 33, 'Radulović', '', 'Dragutin')]),
    '32-divizija-borci.pdf': (35, [(66, 138, 'Posavec', 'Mije', 'Stjepan')]),
}
FATHERS = {'Vaselina': 'Vaselin'}
# the name's end on the heading's line: what stands before the first comma, or (a list of names) the whole line
NAME_ONLY = {'1-konjicka.pdf'}
# a line that starts the next entry in a list printed flush: a surname in capitals
CAPS = re.compile(r'^\W*(?:\d{1,4}\W+)?(?!(?:SKOJ|KPJ|NOB|NOV|NOVJ|POJ|MPO|NOPO|KNOJ|XII|VIII|VII|III|СКОЈ|КПЈ|НОБ|НОВЈ)\b)[A-ZČĆŽŠĐА-ШЂЉЊЋЏЈ]{3,}')
# lists printed flush: an entry's lines all start level, so only a surname in capitals ends it
FLUSH = {'6-dalmatinska.pdf', '8-kordunaska-divizija.pdf', '14-srednjobosanska.pdf'}
# what follows the name, read from the page where the line is past rules
OVERRIDE = {('5-vojvodjanska.pdf', 146): '1911, Šid, zemljoradnik, borac.', ('5-vojvodjanska.pdf', 143): 'oficir u štabu bataljona.',
            ('5-vojvodjanska.pdf', 139, 72): '1929, Savino Selo, domaćica, bolničarka.',
            ('32-divizija-borci.pdf', 66): 'r. 1917, s. Imbriovec, Koprivnica, Hrvat, poljopriv., čl. KPJ, NOV 1944, ranjen 1944.'}


def latin(line):
    line = re.sub(r'([ЛлНн])>', lambda m: {'Л': 'Љ', 'л': 'љ', 'Н': 'Њ', 'н': 'њ'}[m.group(1)], line)
    line = re.sub(r'Ј1', 'Л', line)
    out = ''
    for c in line:
        l = LAT.get(c.lower())
        out += c if l is None else (l.capitalize() if c.isupper() else l)
    return out


def main():
    units = {}
    words = collections.Counter()
    for code, cfg in BRIGADE_CONFIGS.items():
        p = ROOT / 'website/public' / cfg['json_file']
        if p.exists() and not 131 <= code <= 138:
            data = json.loads(p.read_text(encoding='utf-8'))
            for s in data:
                words.update(re.findall(r'[^\W\d_]{4,}', s.get('additional_info') or ''))
            if code in {v[0] for v in MEN.values()}:
                units[code] = data
    known = {w for w, n in words.items() if n >= 3}
    given_names = collections.Counter()
    for code, cfg in BRIGADE_CONFIGS.items():
        p = ROOT / 'website/public' / cfg['json_file']
        if p.exists() and not 122 <= code <= 138:
            given_names.update(s.get('first_name') for s in json.loads(p.read_text(encoding='utf-8')))
    by_first = collections.defaultdict(list)
    for w, n in words.items():
        if n >= 30:
            by_first[w[0].lower()].append(w)

    def read(t, cyr):
        t = latin(t)
        t = t.replace('\u00ad', '-')
        t = re.sub(r'(?<=[^\W\d_])-\s+(?=[a-zčćžšđ])', '', t)
        t = re.sub(r'\s+', ' ', t).strip().replace('ß', 's')
        if not cyr:
            return t
        t = re.sub(r'\bY\b', 'U', re.sub(r'\bTh(?=[a-zčćžšđ])', 'Ć', t))    # the Cyrillic У and the Ћ as "Тх"

        def fix(m):
            w = m.group(0)
            if w in known or len(w) < 4:
                return w
            best = max(by_first.get(w[0].lower(), ()), key=lambda c: SequenceMatcher(None, w.lower(), c.lower()).ratio(), default=None)
            if best and SequenceMatcher(None, w.lower(), best.lower()).ratio() >= 0.8 and len(best) >= len(w) - 1:
                return best if w[0].islower() == best[0].islower() else (best.capitalize() if w[0].isupper() else best.lower())
            return w
        return re.sub(r'[^\W\d_]+', fix, t)

    cache = EB.PageCache()
    out, problems = [], []
    for pdf, (code, men) in MEN.items():
        data = units[code]
        pages = cache.pages(pdf, sorted({m[0] for m in men}))
        tops = collections.defaultdict(list)                     # the known starts, the new men's too
        for s in data:
            for e in [s] + [o for o in s.get('other_sources', ()) if not o.get('ref_book') and not o.get('unit_file')]:
                if e.get('pdf_file') == pdf and e.get('pdf_y') is not None:
                    tops[int(e['pdf_page'])].append((e['pdf_y'], e.get('pdf_x') or 0))
        for m in men:
            tops[m[0]].append((m[1], None))
        used = {s['soldier_id'] for s in data}
        n = 9001
        for m in sorted(men, key=lambda m: (m[0], m[1])):
            page, top, last, father, given = m[:5]
            note = m[5] if len(m) > 5 else ''
            pg = pages.get(page)
            hit = None
            for col in pg['columns']:
                for li, ln in enumerate(col):
                    if abs(ln['top'] - top) < 1.5 and (hit is None or fuzzy(last, ln['text']) > fuzzy(last, hit[0][hit[1]]['text'])):
                        hit = (col, li)
            if hit is None:
                problems.append((pdf, m, 'no line'))
                continue
            col, li = hit
            head = col[li]
            lines = [head]
            if pdf not in NAME_ONLY:
                for lj in range(li + 1, len(col)):
                    ln = col[lj]
                    step = ln['top'] - lines[-1]['top']
                    if pdf not in FLUSH and abs(ln['x0'] - head['x0']) <= 4.5 and step > 4:
                        break
                    if any(abs(y - ln['top']) < 3 and (x is None or abs(x - ln['x0']) < 40) for y, x in tops[page]):
                        break
                    if step > 2.1 * max(head['bottom'] - head['top'], 8) or CAPS.match(ln['text']):
                        break
                    lines.append(ln)
            raw = ' '.join(l['text'] for l in lines)
            cyr = bool(CYR.search(raw))
            if pdf in NAME_ONLY:
                rest = ''
            else:
                # what follows the name: after the first comma, or from a year printed before it
                c = raw.find(',')
                year = re.search(r'\s(1[89]\d\d)\b', raw[:c] if c >= 0 else raw)
                rest = raw[year.start() + 1:] if year else raw[c + 1:] if c >= 0 else ''
                if pdf == '7-srpska.pdf':
                    rest = re.sub(r'^.*?(?=\()', '', raw, count=1)
                rest = OVERRIDE.get((pdf, page, top)) or OVERRIDE.get((pdf, page)) or rest
            rest = read(rest, cyr).strip(' ,;:')
            rest = re.sub(r'\s+\d{3}\.?$', '', rest)                       # the page's number under the entry
            info = '; '.join(x for x in (note, rest) if x)
            # the year he was born: what the text opens with, or after "rođen", "r.", "rod."
            y = re.match(r'\W*(1[89]\d\d)\b', rest) or re.search(r'\b(?:[Rr]ođena?|[Rr]od\.|[Rr]ođ\.|r\.)\s+(?:\d{1,2}\.\s*(?:[IVX]+|\d{1,2})\.?\s*)?(1[89]\d\d)\b', rest)
            birth = y.group(1) if y else ''
            fat = nominative(father, given_names, code in (82, 126, 127, 85)) if father and not father.endswith('.') else father
            # the record above on its page, else the last before it
            before = [s for s in data if s.get('pdf_file') == pdf and s.get('pdf_page') is not None and (int(s['pdf_page']), s.get('pdf_y') or 0) <= (page, top)]
            prev = max(before, key=lambda s: (int(s['pdf_page']), s.get('pdf_y') or 0))['soldier_id'] if before else data[0]['soldier_id']
            while f'{code:04d}00{n}' in used:
                n += 1
            new_id = f'{code:04d}00{n}'
            used.add(new_id)
            rec = {'last_name': last, 'middle_name': father, 'first_name': given, 'fathers_name': fat, 'additional_info': info, 'birth_year': birth,
                   'pdf_file': pdf, 'pdf_page': page, 'pdf_y': head['top'], 'pdf_x': head['x0']}
            out.append(dict(pdf=pdf, prev=prev, new_id=new_id, rec=rec, raw=raw))
    print(len(out), 'men', collections.Counter(r['pdf'] for r in out).most_common())
    for p in problems:
        print('PROBLEM', p)
    if '--write' in sys.argv:
        start = int(sys.argv[sys.argv.index('--write') + 1])
        P = ROOT / 'corrections.json'
        corr = json.loads(P.read_text(encoding='utf-8'))
        assert not [c for c in corr if c['id'] >= start]
        add = [{'id': start + i, 'action': 'add', 'soldier_id': r['prev'], 'new_id': r['new_id'], 'record': r['rec'],
                'reason': f"Lost by the parser (its surname's capitals broken on the scan, or a page's first rows dropped): {r['pdf']}, p. {r['rec']['pdf_page']}: \"{r['raw'][:70]}\""}
               for i, r in enumerate(out)]
        P.write_text(json.dumps(corr + add, ensure_ascii=False, indent=2), encoding='utf-8')
        print('written', len(add), start, start + len(add) - 1)
    else:
        for r in out:
            x = r['rec']
            print(r['new_id'], x['last_name'], '|', x['middle_name'], '/', x['fathers_name'], '|', x['first_name'], '|', x['birth_year'], '|', x['additional_info'][:150])


def nominative(g, names, serbian):
    """A father printed in the genitive, as the name the units' men bear most: "Milinka" Milinko, "Pavla" Pavle, "Petra" Petar,
    "Ante" Ante; a form in -e in Serbia and Vojvodina is one in -a where the name exists ("Save" Sava), as the census has it."""
    cands = []
    if g.endswith('a'):
        cands = [g[:-1], g[:-1] + 'o', g[:-1] + 'e', g[:-2] + 'a' + g[-2]]
    elif g.endswith('e'):
        cands = [g[:-1] + 'o', g[:-1] + 'a', g, g[:-1] + 'ija' if g.endswith('ije') else g]
        if serbian and names.get(g[:-1] + 'a'):
            return g[:-1] + 'a'
    best = max(cands, key=lambda c: names.get(c, 0), default=g)
    return best if names.get(best) else FATHERS.get(g) or genitive_to_nominative(g)


def fuzzy(last, text):
    a, b = re.sub(r'\W', '', latin(last).lower()), re.sub(r'\W', '', latin(text[:len(last) + 6]).lower())
    return SequenceMatcher(None, a, b).ratio()


if __name__ == '__main__':
    main()
