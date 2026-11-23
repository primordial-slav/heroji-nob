"""The census's place column in one form: data-extraction/places/census_forms.json, the stored value and the place, which standardize_fields.place_form reads.

The column prints a village and its area joined in small letters ("Doboj-tuzla", "Stol,pirot"), abbreviates without a space ("D.lapac", "Sv.križ"), writes a name's second word small ("Banja luka", "Crna gora")
and cuts everything at 15 characters ("Kestenovac-d.la", "Kosovska mitrov"). What it means is read here against the places the site knows, every part of every birthplace and place of death; a part it doesn't know
only takes a capital. Run after a batch of new census records; dry run without --write.

A value its 15 characters cut in a word ("Ilirska bistric", "Sremska mitrovi") gets the one known place it begins (Places.cut): known is a place GeoNames resolved
(data-extraction/places/resolved.json) or one the site prints SURE times (else KNOWN times: "cut, the site only"); a place under a twentieth of it is a misreading beside it ("Sremska
Mitroviia"), anything more another place, and the value stays ("Hrvatski karlov": Karlovac 4, Karlovec 1). A value that ends where a known place ends stays ("Bosanska Dubica", "Grubišino
Polje"), as does a case the site prints as a place ("Savinjski dolini"). The area after a village (Places.area): joined by a hyphen or comma ("Duga resa-karlo"), the place it begins five
times above the next, as the table read areas since 2026-11-03; joined by a space ("Topolšica slove", "Sutjeska zeleng"), only an area the column itself writes after villages, one it writes
rarely only near the village; where several stand close, the one that is a region or lies within NEAR_KM of the village ("Brodarevo Prije" Prijepolje, not Prijedor). No Slovene
region after a village GeoNames (its dumps, local: data-extraction/.cache/map1941/geonames) knows only outside Slovenia, nor another republic's after one only in it: "Bosiljevo slove"
stays, Bosiljevo being in Croatia only. The places counted are
the records' own, not those borrowed from the census (record_sources.py) nor those after a preposition ("kod Žabljaka"). --write writes the whole table, which reads every value again; on
2026-11-20 only the cut values' rows were written into the table then on disk (728), the other 21 values today's data reads otherwise left as they were ("Crna gora").

    python scripts/make_census_forms.py --sample 30
    python scripts/make_census_forms.py --cuts          # every completion of a cut value, its count and entries
    python scripts/make_census_forms.py --write
"""
import argparse
import bisect
import collections
import glob
import io
import json
import math
import os
import random
import re
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from name_utils import BRIGADE_CONFIGS  # noqa: E402
from standardize_fields import REGIONS, scan_marks  # noqa: E402

OUT = os.path.join(ROOT, 'data-extraction', 'places', 'census_forms.json')
RESOLVED = os.path.join(ROOT, 'data-extraction', 'places', 'resolved.json')
CENSUS_HOST = 'muzejgenocida'
FOLD = str.maketrans('čćžšđ', 'cczsd')
LOW = 'a-zčćžšđ'
UP = 'A-ZČĆŽŠĐ'
CARON = re.compile('[čćžšđČĆŽŠĐ]')
# common nouns after the place, which stay small
NOUNS = {'stalag', 'bolnica', 'zbeg', 'logor', 'šuma', 'pruga', 'selo', 'grad', 'most', 'groblje', 'zarobljeništvo', 'zatvor', 'stan', 'kuća', 'boln', 'bolnic'}
# the column's abbreviations and what its width left of the commonest names
PARTS = {
    'crna gora': 'Crna Gora', 'c.gora': 'Crna Gora', 'c.g': 'Crna Gora', 'c. go': 'Crna Gora', 'c. gora': 'Crna Gora', 'cr.gora': 'Crna Gora', 'sk.c.gor': 'Skopska Crna Gora', 'sl.brod': 'Sl. Brod', 'sl.br': 'Sl. Brod', 'b.luka': 'Banja Luka', 'bo.luka': 'Banja Luka',
    's.most': 'Sanski Most', 'sl.požega': 'Sl. Požega', 'sl.pože': 'Sl. Požega', 's.pož': 'Sl. Požega', 's.po': 'Sl. Požega', 'd.la': 'D. Lapac', 'd.lap': 'D. Lapac', 'd.l': 'D. Lapac', 'd.lapac': 'D. Lapac', 'p.slat': 'P. Slatina',
    'bos.grahov': 'Bos. Grahovo', 'sr.mitrovic': 'Sr. Mitrovica', 't.už': 'T. Užice', 'k.var': 'K. Varoš', 'g. kotar': 'Gorski Kotar', 'g.kotar': 'Gorski Kotar',
    'slavon': 'Slavonija', 'slav': 'Slavonija', 'slavonij': 'Slavonija', 'bosn': 'Bosna', 'bos': 'Bosna', 'lik': 'Lika', 'bjelov': 'Bjelovar', 'bjelova': 'Bjelovar', 'bjelovar': 'Bjelovar', 'bijeljin': 'Bijeljina', 'bijelj': 'Bijeljina', 'bjeljina': 'Bijeljina', 'bjeljin': 'Bijeljina',
    'zagre': 'Zagreb', 'zagr': 'Zagreb', 'zag': 'Zagreb', 'sloveni': 'Slovenija', 'sloven': 'Slovenija', 'slovenij': 'Slovenija', 'dalmac': 'Dalmacija', 'dalmaci': 'Dalmacija', 'dalm': 'Dalmacija', 'hercegov': 'Hercegovina', 'herceg': 'Hercegovina', 'hercegovin': 'Hercegovina',
    'kosmet': 'Kosmet', 'kosm': 'Kosmet', 'kordun': 'Kordun', 'banij': 'Banija', 'il.bis': 'Il. Bistrica', 'baran': 'Baranja', 'baranj': 'Baranja', 'ljubljan': 'Ljubljana', 'ljublja': 'Ljubljana', 'dolenjs': 'Dolenjska', 'korošk': 'Koroška', 'savinjsk': 'Savinjska',
    'srebren': 'Srebrenica', 'koprivni': 'Koprivnica', 'hrvatsk': 'Hrvatska', 'kičev': 'Kičevo', 'bjeljev': 'Bjelajevci', 'romanij': 'Romanija',
}
# whole values no rule reads
WHOLE = {'Babino Polje-ml': 'Babino Polje, Mljet',  # the entry: "poginuo n Mljetu" (0036001759; the lead, 2026-11-23)
         'Vlaške njive-zv': 'Vlaške njive, Zvornik',  # the user, 2026-11-23 (0096000637's census entry)
         'Han-pjesak': 'Han Pijesak', 'Han-pijesak': 'Han Pijesak', 'Srem.front': 'Sremski front', 'Srem-front': 'Sremski front', 'Srem front': 'Sremski front', 'Blato-korčula': 'Blato, Korčula', 'Ivan-planina': 'Ivan-planina', 'Ivan-sedlo': 'Ivan-sedlo', 'Nov-ci': 'Novci',
         'Šar-planina': 'Šar-planina', 'Šator-planina': 'Šator-planina', 'Zelen-gora': 'Zelengora', 'Šaren-grad': 'Šarengrad', 'Cetin-grad': 'Cetingrad', 'Oslobađ.bgd-a': 'Beograd'}
# a Slovene name's second word is small by its own rule
KEEP_SMALL = re.compile(rf'(?:\bNovo mesto\b|\s(?:vas|trg|gorica|dolina)$)')
ABBR = re.compile(rf'^([{UP}][{LOW}]{{0,4}})\.([{LOW}])')
ABBR_UP = re.compile(rf'^([{UP}][{LOW}]{{0,4}})\.([{UP}])')
# joined without a space after a comma or around a hyphen: "Doboj-tuzla", "Stol,pirot", "Babina greda- b" (a comma and a space is a reader's, "Sutjeska, kod Popovog Mosta")
TWO_PARTS = re.compile(rf'^(.*?[{LOW}.])(-\s*|,)([{LOW}][^-,]*)$')
NOT_A_PLACE = re.compile(r'(?i)\b(?:nov|nob|noo)-[aeu]$|\btbc-a$')
# a cut value's completion: a place the site prints this often is known without GeoNames, one printed fewer than KNOWN times
# is no place to complete to, and a misreading beside the known place ("Sremska Mitroviia") is one under a twentieth of it
KNOWN, SURE, BESIDE = 3, 30, 20
# an area after a village: the commonest of the places it begins, five times the next, printed eight times where GeoNames
# didn't resolve it (as the table read areas since 2026-11-03)
AREA_BESIDE, AREA_LEAST = 5, 8
# what opens a reader's phrase or a note, never a village before its area ("Okolina bijelji" is okolina Bijeljine)
NO_VILLAGE = re.compile(r'(?i)^(?:kod|u|na|oko|okolina|okolica|okol\.|granica|planina|blizu|prema|pored|preko|ispod|iznad|između|iza|za|od|do|pri|v|pog\.|poginuo|umro|ubijen|strijeljan|streljan)\b')
# words the column writes after a place that are no area ("Zvijezda planina", "Sarajevo-bolnica"), folded
AREA_NOUNS = {'planina', 'polje', 'bolnica', 'selo', 'brdo', 'gora', 'dolina', 'logor', 'suma', 'front', 'groblje', 'zatvor', 'stan', 'kuca', 'most', 'grad', 'pruga', 'zbeg', 'zbjeg'}
# completions read on 2026-11-20 and found false, left as printed: Bijeljina printed "beljina" (the site's Beljin lies elsewhere),
# a place the cut leaves no more than a guess at ("crn", "marij"), a garble ("zvij"), a place the site barely knows ("Zminec")
READ_AS_PRINTED = {'Patkovača belji', 'Patkovača-belji', 'Ravna gora zvij', 'Crna reka-marij', 'Sopetinci-žmine', 'Tifino selo-crn'}
# a whole word after a place that is no cut area: a preposition, a common noun (folded)
NO_AREA = {'pri', 'pod', 'nad', 'na', 'ob', 'kod', 'v', 'u', 'iz', 'od', 'do', 'za', 'pre', 'pred', 'kraj', 'mlin', 'most', 'grad', 'selo',
           'polje', 'brdo', 'suma', 'stan', 'kuca', 'put', 'cesta', 'pruga', 'reka', 'rijeka', 'gora', 'dol', 'vrh', 'kosa', 'voda',
           'potok', 'jezero', 'kotar', 'srez', 'okrug', 'front', 'fronta', 'zbeg', 'zbjeg', 'brana'}
# a cut word after a place that can only be one of these: "Psunjska bolnic" is Psunjska bolnica
CUT_NOUNS = ('bolnica', 'groblje', 'logor', 'zatvor', 'zarobljeništvo', 'okolina')


def fold(t):
    return t.lower().translate(FOLD)


# an area after a village lies near it ("Duga resa-karlo" is Karlovac, not Karlovčić or Karlobag; "Brodarevo Prije" Prijepolje,
# not Prijedor), or is a region, which has no one place to measure from (folded)
NEAR_KM = 60
REGION_AREAS = {fold(r) for r in REGIONS} | {
    'bosanska krajina', 'krajina', 'baranja', 'primorska', 'hrvatsko primorje', 'slovensko primorje', 'dolenjska', 'dolenjsko', 'gorenjska',
    'gorenjsko', 'notranjska', 'stajerska', 'koroska', 'bela krajina', 'semberija', 'kosmet', 'metohija', 'sumadija', 'pomoravlje', 'zumberak',
    'hrvatsko zagorje', 'slavonska posavina', 'istocna bosna', 'zapadna bosna', 'centralna bosna', 'srednja bosna', 'albanija', 'bugarska',
    'italija', 'madarska', 'austrija', 'nemacka', 'njemacka', 'grcka', 'rumunija', 'srbija', 'jugoslavija'}


# the republics (GeoNames' countries) a region lies in, for Places.in_land ("Bosiljevo slove": Bosiljevo is in Croatia only,
# so no Slovenija; GeoNames 3203639)
REGION_LANDS = {
    'slovenija': 'SI', 'dolenjska': 'SI', 'dolenjsko': 'SI', 'gorenjska': 'SI', 'gorenjsko': 'SI', 'notranjska': 'SI',
    'stajerska': 'SI', 'koroska': 'SI', 'primorska': 'SI', 'bela krajina': 'SI', 'slovensko primorje': 'SI',
    'hrvatska': 'HR', 'slavonija': 'HR', 'lika': 'HR', 'dalmacija': 'HR', 'kordun': 'HR', 'banija': 'HR', 'baranja': 'HR',
    'moslavina': 'HR', 'podravina': 'HR', 'gorski kotar': 'HR', 'hrvatsko zagorje': 'HR', 'hrvatsko primorje': 'HR',
    'slavonska posavina': 'HR', 'istra': 'HR SI', 'zagorje': 'HR SI', 'zumberak': 'HR SI', 'primorje': 'HR SI ME',
    'posavina': 'HR BA RS', 'krajina': 'HR BA RS', 'srem': 'RS HR',
    'bosna': 'BA', 'bih': 'BA', 'hercegovina': 'BA', 'bosanska krajina': 'BA', 'semberija': 'BA', 'istocna bosna': 'BA',
    'zapadna bosna': 'BA', 'centralna bosna': 'BA', 'srednja bosna': 'BA', 'romanija': 'BA', 'kozara': 'BA', 'majevica': 'BA',
    'srbija': 'RS XK', 'vojvodina': 'RS', 'banat': 'RS', 'backa': 'RS', 'sumadija': 'RS', 'pomoravlje': 'RS',
    'kosovo': 'XK RS', 'kosmet': 'XK', 'metohija': 'XK', 'sandzak': 'RS ME', 'crna gora': 'ME', 'c. gora': 'ME',
    'makedonija': 'MK', 'jugoslavija': 'SI HR BA RS XK ME MK'}


def geonames_dir():
    """the GeoNames dumps our places tool caches (data-extraction/.cache/map1941/geonames, local), in this checkout or the main one"""
    roots = [ROOT]
    try:
        common = subprocess.run(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        roots.append(os.path.dirname(os.path.abspath(os.path.join(ROOT, common))))
    except OSError:
        pass
    for root in roots:
        d = os.path.join(root, 'data-extraction', '.cache', 'map1941', 'geonames')
        if os.path.isdir(d):
            return d
    return None


def place_lands():
    """folded place name -> the countries GeoNames knows a place of the name in (settlements, municipalities, mountains, rivers)"""
    lands = collections.defaultdict(set)
    d = geonames_dir()
    if not d:
        print('no GeoNames dumps found: no area after a village is checked against its land, none of a region is taken')
        return lands
    for path in sorted(glob.glob(os.path.join(d, '*.zip'))):
        cc = os.path.basename(path)[:2]
        with zipfile.ZipFile(path) as z:
            for line in io.TextIOWrapper(z.open(f'{cc}.txt'), encoding='utf-8'):
                f = line.rstrip('\n').split('\t')
                if f[6] not in ('P', 'A', 'T', 'H', 'L'):
                    continue
                for name in [f[1], f[2]] + f[3].split(','):
                    if name and not re.search('[Ѐ-ӿ]', name):
                        lands[fold(name)].add(cc)
    return lands


def km(a, b):
    dlat, dlon = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    x = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(x))


def place_parts(v):
    for part in re.split(r',\s*|\s*\(|\)', v):
        part = re.sub(r'^(?:kod|u|na|s\.|selo|sela|selu)\s+', '', part.strip())
        if len(part) > 1 and part[0].isupper():
            yield part


# a place after a preposition is in a case ("kod Žabljaka", "v Savinjski dolini"): no name to complete a cut one to
AFTER_PREPOSITION = re.compile(r'(?i)^(?:kod|u|na|v|pri|pod|nad|blizu|iznad|ispod|oko|prema|pored|kraj|između|iza|od|do|za|iz|ob|po)\s')


def own_parts(v):
    for part in re.split(r',\s*|\s*\(|\)', v):
        part = part.strip()
        if AFTER_PREPOSITION.match(part):
            continue
        part = re.sub(r'^(?:s\.|selo|sela|selu)\s+', '', part)
        if len(part) > 1 and part[0].isupper():
            yield part


class Places:
    """The places the site knows, read one unit's file at a time (add), then finish()"""

    def __init__(self):
        self.known = collections.Counter()
        # what a cut value is completed from: the records' own places, not those they borrowed from the census's column
        # (record_sources.py) or a 122 record holds from it, which may be the cut value itself
        self.own = collections.Counter()

    def add(self, code, rs):
        census = 131 <= code <= 138
        for s in rs:
            lent = set(s.get('borrowed') or ()) | set(s.get('from_columns') or ())
            for k in ('birth_place', 'death_place'):
                v = s.get(k) or ''
                if not v:
                    continue
                # the column itself is what is being read, so only its short values, which it didn't cut, and no joined ones
                if census and k == 'death_place' and (len(v) >= 14 or TWO_PARTS.match(v)):
                    continue
                own = k not in lent and not (code == 122 and k == 'death_place' and len(v) in (14, 15)
                                             and any(CENSUS_HOST in (o.get('source_url') or '') for o in s.get('other_sources', ())))
                for part in place_parts(v):
                    self.known[part] += 1
                if own:
                    for part in own_parts(v):
                        self.own[part] += 1

    @staticmethod
    def folded(counts):
        by_fold = collections.defaultdict(collections.Counter)
        for k, n in counts.items():
            by_fold[fold(k)][k] += n
        return by_fold, sorted(by_fold)

    def finish(self, census_values):
        """census_values: the column's values as the entries print them, which give its areas ("Klane slovenija", "Doboj-tuzla")"""
        self.by_fold, self.keys = self.folded(self.known)
        self.own_fold, self.own_keys = self.folded(self.own)
        self.words = collections.Counter()
        for k, n in self.own.items():
            for word in fold(k).split():
                self.words[word] += n
        # known places: those GeoNames resolved (not a census value the column cut) and those the site prints often
        self.sure = {fold(k) for k, n in self.own.items() if n >= SURE}
        # and where a place is: every place GeoNames resolved its name to (Duga Resa one, Glavičica several)
        ids = collections.defaultdict(collections.Counter)
        points = {}
        if os.path.exists(RESOLVED):
            with open(RESOLVED, encoding='utf-8') as f:
                resolved = json.load(f)
            points = {int(k): v for k, v in resolved['places'].items()}
            for unit, fields in resolved['units'].items():
                for field, texts in fields.items():
                    for text, r in texts.items():
                        if unit.startswith('ostali-borci-') and field == 'death_place' and len(text) >= 14:
                            continue
                        name = fold((r[1] if isinstance(r, list) else text).split(',')[0].strip())
                        self.sure.add(name)
                        ids[name][r[0] if isinstance(r, list) else r] += 1
        self.spots = {name: [points[i] for i in c if i in points] for name, c in ids.items()}
        self.spots = {name: s for name, s in self.spots.items() if s}
        self.lands = place_lands()
        # the areas the column writes after a village, where both are known places ("Klane slovenija", "Doboj-tuzla")
        self.areas = collections.Counter()
        for v, n in census_values.items():
            m = TWO_PARTS.match(v)
            if m:
                b = fold(m.group(3).strip())
                if len(v) <= 13 or b in self.sure:
                    self.areas[b] += n
                continue
            w = v.split(' ')
            for i in range(1, len(w)):
                a, b = fold(' '.join(w[:i])), fold(' '.join(w[i:]))
                if a in self.sure and b in self.sure and (len(v) >= 14 or fold(v) not in self.own_fold):
                    self.areas[b] += n
                    break

    def prefixed(self, w):
        i = bisect.bisect_left(self.own_keys, w)
        while i < len(self.own_keys) and self.own_keys[i].startswith(w):
            yield self.own_keys[i]
            i += 1

    def exact(self, word, least=3):
        """the place of this spelling, carons and all, in the capitals the site prints most"""
        c = [(n, k) for k, n in self.by_fold.get(fold(word), {}).items() if k.lower() == word.lower()]
        if not c:
            return None
        c.sort(reverse=True)
        return c[0][1] if sum(n for n, _ in c) >= least else None

    def count(self, word):
        return sum(n for k, n in self.by_fold.get(fold(word), {}).items() if k.lower() == word.lower())

    def spelled(self, names, printed=''):
        """The site's spelling: the commonest, the one with more capitals between two as common; where the column prints a
        caron, one that keeps the printed letters, unless it is a misspelling beside the commonest ("Črna na koroške" Črna na
        Koroškem, not Crna; "parač" Paraćin); a Slovene name's small words small ("Šmihel nad Mozirjem")"""
        def best(names):
            return max(names.items(), key=lambda s: (s[1], sum(ch.isupper() for ch in s[0])))
        top = best(names)
        if CARON.search(printed):
            own = {k: n for k, n in names.items() if k.lower().startswith(printed.lower())}
            if own and best(own)[1] * AREA_BESIDE >= top[1]:
                top = best(own)
        return re.sub(rf'(?<=[{LOW}]) (Pri|Pod|Nad|Ob|Na|V) (?=[{UP}])', lambda m: f' {m.group(1).lower()} ', top[0])

    def candidates(self, value):
        """The known places a value begins: (how often the site prints it as it stands, {completion: [count, spelling]}). A
        completion is the place whose word the cut ends in ("Sremska mitrovi" Sremska Mitrovica), or the whole name where the
        place goes on after it five times as often as it stands alone ("Radeče pri zid" Radeče pri Zidanem mostu, "zidani"
        Zidani Most, "mrkonji" Mrkonjić Grad). Where the column prints a caron its letters count: "gradač" is no Gradac"""
        w = fold(value)
        carons = bool(CARON.search(value))

        def keeps(names):
            return not carons or any(k.lower().startswith(value.lower()) for k in names)
        # the places that keep the printed carons, where any does (else the column misprinted one: "Komarna vas-črm" Crmnica)
        kept = [k for k in self.prefixed(w) if k[len(w):] and keeps(self.own_fold[k])]
        same, words, on = 0, collections.defaultdict(lambda: [0, collections.Counter(), collections.Counter()]), {}
        for k in self.prefixed(w):
            names = self.own_fold[k]
            n = sum(names.values())
            rest = k[len(w):]
            if not rest:
                same += sum(m for x, m in names.items() if x.lower() == value.lower()) if carons else n
            elif kept and k not in kept:
                continue
            elif not rest[0].isalpha():
                # a whole word the place goes on after: a known place, or one the value cuts after its preposition
                # ("Stari grad Pri" Stari Grad pri Vidmu; not "Vukosavljevića" Vukosavljevića Sokolac, which the site prints thrice)
                if k in self.sure or re.search(r'\s(?:pri|pod|nad|na|ob|v|kod)$', w):
                    on[k] = [n, self.spelled(names, value)]
            else:
                c = w + re.match(r'[^\W\d_]+', rest).group(0)
                g = words[c]
                g[0] += n
                if k == c:
                    g[1].update(names)
                else:
                    g[2][k] += n
        found = dict(on)
        for c, (n, exact, longer) in words.items():
            k = max(longer, key=longer.get, default=None)
            if exact and (not k or sum(exact.values()) * AREA_BESIDE >= longer[k]):
                found[c] = [n, self.spelled(exact, value)]
            elif any(x != k and m * BESIDE >= longer[k] for x, m in longer.items()):
                # the longer names: one, or one far above the rest
                found[c] = [n, self.spelled(exact, value) if exact else None]
            else:
                found[k] = [n, self.spelled(self.own_fold[k], value)]
        return same, found

    def cut(self, value):
        """A value the column's width cut: (the one known place it begins, how), else (None, why): 'whole' where a known place
        ends where it ends, 'several', 'none known' (only names the site prints now and then), 'none'. Known: a place GeoNames
        resolved or the site prints SURE times ('cut'), else one it prints KNOWN times ('cut, the site only'); another
        place beside it is any under a twentieth of it, or a known one beside one the site only prints"""
        w = fold(value)
        same, found = self.candidates(value)
        top = max(found, key=lambda k: found[k][0], default=None)
        # a value a few records print cut ("Sremska Mitrovi") is no whole name beside the place it begins
        if same and (w in self.sure or not top or same * BESIDE >= found[top][0]):
            return None, 'whole'
        if not top:
            return None, 'none'
        n, out = found[top]
        sure = fold(out or top) in self.sure
        if not out or any(k != top and (m * BESIDE >= n or (not sure and fold(o or k) in self.sure)) for k, (m, o) in found.items()):
            return None, 'several'
        if sure:
            return out, 'cut'
        # a case the site prints as a place ("Savinjski dolini", of dolina) is no name to complete to; one after the name's
        # own preposition is ("Grahovo pri Cerknici")
        last = fold(out).split()[-1]
        if last.endswith('i') and self.words[last[:-1] + 'a'] >= SURE and not re.search(r'\s(?:pri|pod|nad|na|ob|v|kod)\s', out):
            return None, 'case'
        return (out, 'cut, the site only') if n >= KNOWN else (None, 'none known')

    def in_land(self, area, village):
        """Whether a region may follow the village, read where GeoNames is complete: it lists every Slovene settlement (6,640
        places against the register's 6,035), while elsewhere it misses many villages (Klasnić by Glina, Pađani). So a
        Slovene region only after a village of the name in Slovenia ("Bosiljevo slove": Bosiljevo is in Croatia only, no
        Slovenija; "Ludbreg sloveni", "Županja sloveni" stay), and no other republic's region after a village GeoNames knows
        only in Slovenia ("Dravograd-slavo" is no Slavonija). Towns, villages GeoNames doesn't know, a village that is a
        region or a noun ("Crna gora-sutje", "Bolnica karlova") are not checked"""
        if not village or fold(village) in REGION_AREAS or fold(village).split()[0] in AREA_NOUNS | NO_AREA:
            return True
        f = fold(area)
        home = self.lands.get(fold(village), set())
        if f not in REGION_LANDS or not home:
            return True
        region = set(REGION_LANDS[f].split())
        if region == {'SI'}:
            return 'SI' in home
        return not (home == {'SI'} and 'SI' not in region)

    def area(self, part, village=None, beside=None, areas_only=False):
        """A cut area after a village ("Topolšica slove", "Duga resa-karlo"): the known place it begins, the column's own areas
        too, where it stands five times above the next (AREA_BESIDE, as the table read areas since 2026-11-03: Karlovac, not
        Karlovčić). Where several stand close, the one that is a region or lies within NEAR_KM of the village, every other
        known to lie farther ("Topolšica slove" Slovenija, not Slovenj Gradec; "Brodarevo Prije" Prijepolje, not Prijedor).
        Never a region of a land the village lies outside (in_land): "Bosiljevo slove" stays, Bosiljevo being in Croatia only"""
        p = fold(part)
        # a preposition the cut left ("Vinkov vrh Pri" is Vinkov vrh pri ..., no Primorska), a common word ("Cezanjevci mlin")
        if p in NO_AREA:
            return None
        beside = beside or AREA_BESIDE
        same, cands = self.candidates(part)
        # a completion of several places ("bosans": Bosanska Gradiška, Krupa, Dubica...) stands beside the others unnamed;
        # after a space only the areas the column writes count ("Topolšica slove": Slovenija, never Slovenj Gradec there)
        found = {} if areas_only else {fold(out or k): [n, out] for k, (n, out) in cands.items()}
        # the column's own areas the site doesn't print as places, in the site's spelling; after a space one it writes
        # rarely only where it lies near a village of the name ("Jabuka Prijepol"; not "Kralje andrijev" Andrijevci, 164 km)
        spots = self.spots.get(fold(village)) if village and fold(village) not in REGION_AREAS else None

        def near(a):
            return a in REGION_AREAS or bool(spots and a in self.spots and
                                              any(km(x, y) <= NEAR_KM for x in self.spots[a] for y in spots))
        for a, n in self.areas.items():
            if areas_only and n < KNOWN and not near(a):
                continue
            if a.startswith(p) and a != p and a not in found and (a in self.sure or n >= SURE or areas_only) and a in self.own_fold:
                names = self.own_fold[a]
                if not CARON.search(part) or any(k.lower().startswith(part.lower()) for k in names):
                    found[a] = [n, self.spelled(names, part)]
        found = {f: v for f, v in found.items() if f.split()[0] not in AREA_NOUNS}
        known = [f for f, (n, out) in found.items() if out and ((f in self.sure and (n >= KNOWN or areas_only)) or n >= AREA_LEAST)]
        if not known:
            return None
        top = max(known, key=lambda f: found[f][0])
        if not self.in_land(top, village):
            return None
        # a whole word the site prints as a place stays, unless a hamlet of the name beside the town it begins, under a
        # twentieth of it ("Opatovac-vukova" Vukovar, "Lasinja-karlova" Karlovac; "Negotino-vardar" stays, not Vardarac)
        if (p in self.sure or same) and same * BESIDE >= found[top][0]:
            return None
        # where the cut leaves two letters (after a space three) any other place it begins is another ("Gladno Polje-sa" is
        # no Sarajevo for sure; "Glavatičevo-kon" Konjic, as the table read it)
        rivals = [f for f, (n, _) in found.items() if f != top and (n * beside >= found[top][0] or len(p) < (4 if areas_only else 3))]
        if not rivals:
            return found[top][1]
        # several: the one that is a region or lies near the village, every other lying far from it, the same one from each
        # village of the name the site knows (Topolšica: Slovenija; Brodarevo: Prijepolje, Prijedor far off)
        if not spots or any(f not in REGION_AREAS and f not in self.spots for f in [top] + rivals):
            return None
        close = {tuple(f for f in [top] + rivals if (f in REGION_AREAS and self.in_land(f, village))
                       or (f in self.spots and any(km(x, at) <= NEAR_KM for x in self.spots[f]))) for at in spots}
        if len(close) != 1:
            return None
        close = close.pop()
        return found[close[0]][1] if len(close) == 1 and close[0] in known else None


ADJECTIVE_END = re.compile(r'(?i)^(?:gornj[iae]|donj[iae]|velik[ioa]|mal[ioa]|nov[ioa]|star[ioa]|sv\.?|svet[iao]|srednj[iea]|zgornj[ia]|spodnj[ia])$')


def two_words(v, places):
    """"Topolšica slove": a known village and its area joined by a space, the area cut: "Topolšica, Slovenija" """
    if ' ' not in v or NO_VILLAGE.match(v):
        return None
    a, b = v.rsplit(' ', 1)
    # "Gornji milan": one name, which Places.cut reads whole or not at all (a village must be a known place: "Bosanska" is none)
    if len(b) < 3 or not b.isalpha() or ADJECTIVE_END.search(a.split(' ')[-1]):
        return None
    if fold(a) not in places.sure and places.count(a) < KNOWN:
        return None
    # one name misprinted in its last letter, no village and area: "Sveti ivan zele" is Sveti Ivan Zelina, not Zelengora
    w = fold(v)
    if any(k[len(w) - 1:len(w)].isalpha() and k[len(w) - 1] != w[-1] or k == w[:-1] for k in places.prefixed(w[:-1])):
        return None                 # ... or a place and a stray letter ("Mrkonjić grada")
    first = places.exact(a, KNOWN)
    if not first or sum(c.isupper() for c in first) < sum(c.isupper() for c in a):
        first = a
    # a mountain ("Zvijezda Planin", as the column writes "Ivan-planina"), a noun after the place
    if len(b) >= 4 and 'planina'.startswith(fold(b)) and fold(b) != 'planina':
        return f'{first} planina'
    nouns = [x for x in CUT_NOUNS if x.startswith(b.lower()) and x != b.lower()]
    if len(b) >= 4 and len(nouns) == 1:
        return f'{first}, {nouns[0]}'
    area = places.area(b, first, BESIDE, areas_only=True)
    if not area or fold(area) == fold(a):
        return None
    return f'{first}, {area}'


def small_words(v):
    """"Janče Pri litij" Janče pri Litij, as the Slovene names are written"""
    return re.sub(rf'(?<=[{LOW}]) (Pri|Pod|Nad|Ob) (?=[{LOW}{UP}])', lambda m: f' {m.group(1).lower()} ', v)


def part_up(p):
    p = p.strip()
    if p in PARTS:
        return PARTS[p]
    m = re.match(rf'^([{LOW}]{{1,5}})\.\s*([{LOW}].*)$', p)
    if m:
        return f'{m.group(1).capitalize()}. {m.group(2).capitalize()}'
    return p[:1].upper() + p[1:]


def form(v, places):
    """the value in one form, and how it was read"""
    if v in WHOLE:
        return WHOLE[v], 'whole'
    if NOT_A_PLACE.search(v):
        return '', 'no place'
    # a reader's value, or the words of a clause after a hyphen, are no joined parts
    m = TWO_PARTS.match(v) if ', ' not in v and not re.search(r'-\s*(?:na|u|kod|protiv|prema|za)\s', v) else None
    if m:
        a, sep, b = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        cut = len(v) >= 14 and v not in READ_AS_PRINTED
        # one place with a hyphen for its space ("Škofja-loka"), where its second word isn't a town of its own
        whole = f'{a} {b[:1].upper()}{b[1:]}'
        strong = places.count(b) >= 50 or b in PARTS
        if sep == '-' and places.count(whole) >= (30 if strong else 5):
            return places.exact(whole, 5), 'one place'
        hyph = f'{a}-{b[:1].upper()}{b[1:]}'
        if sep == '-' and places.count(hyph) >= (30 if strong else 5):
            return places.exact(hyph, 5), 'one place'
        if sep == '-' and b == 'planina':
            return f'{a} planina', 'planina'
        if len(b) == 1:
            return ABBR.sub(lambda x: f'{x.group(1)}. {x.group(2).upper()}', a), 'one letter left'
        first = ABBR.sub(lambda x: f'{x.group(1)}. {x.group(2).upper()}', a)
        known_first = places.exact(first, 5)
        # the site's spelling only where it has as many capitals ("G. mlinoga" is no better than "G. Mlinoga")
        if known_first and sum(c.isupper() for c in known_first) >= sum(c.isupper() for c in first):
            first = known_first
        if b in NOUNS:
            return f'{first}, {"bolnica" if b.startswith("boln") else b}', 'noun'
        if b in PARTS:
            return f'{first}, {PARTS[b]}', 'two parts'
        # cut: a mountain ("Kukavica-planin"), a noun ("Novi sad-okolin")
        if cut and len(b) >= 4 and 'planina'.startswith(b) and b != 'planina':
            return f'{first} planina', 'two parts'
        nouns = [x for x in CUT_NOUNS if x.startswith(b) and x != b]
        if cut and len(b) >= 4 and len(nouns) == 1:
            return f'{first}, {nouns[0]}', 'two parts'
        second = places.exact(b) or (cut and places.area(b, first))
        if second:
            second = ABBR_UP.sub(lambda x: f'{x.group(1)}. {x.group(2)}', ABBR.sub(lambda x: f"{x.group(1)}. {x.group(2).upper()}", second))
            return f'{first}, {second}', 'two parts'
        return f'{first}, {part_up(b)}', 'second unknown'
    v2 = small_words(v)
    if len(v2) in (14, 15) and v not in READ_AS_PRINTED:
        c, how = places.cut(v2)
        if c:
            return c, how
        if how in ('none', 'none known'):
            c = two_words(v2, places)
            if c:
                return c, 'area cut'
    # one abbreviation before one name; "Boln.u zagrebu", "Nar.bol.pljevlj" are no such thing
    n = v2 if re.search(rf'^[^.]*\.[{LOW}]*\.|^[^.]*\.(?:u|na|kod|pri|za)\s', v2) else ABBR.sub(lambda x: f'{x.group(1)}. {x.group(2).upper()}', v2)
    if re.search(rf'\s[{LOW}]', n) and not KEEP_SMALL.search(n):
        c = places.exact(n, 5)
        if c and c != n and c.lower() == n.lower():
            return c, 'small letter'
    if n != v:
        return n, 'abbreviation'
    return v, ''


def rivals(v, how, places):
    """for the dry run: what the completion was chosen among (count, place; areas as the column writes them)"""
    if how.startswith('cut'):
        same, found = places.candidates(small_words(v))
        top = sorted(((n, o or k) for k, (n, o) in found.items()), reverse=True)[:4]
        return (f'as printed {same}; ' if same else '') + ', '.join(f'{n} {o}' for n, o in top)
    village, part = v.rsplit(' ', 1) if how == 'area cut' else re.split(r'[-,]\s*', v, maxsplit=1)
    spots = places.spots.get(fold(ABBR.sub(lambda x: f'{x.group(1)}. {x.group(2)}', village.strip())))
    p = fold(part)
    areas = sorted(((n, a) for a, n in places.areas.items() if a.startswith(p)), reverse=True)[:4]
    same, found = places.candidates(part)
    top = sorted(((n, o or k) for k, (n, o) in found.items()), reverse=True)[:4]

    def far(name):
        f = fold(name)
        return '' if not spots or f not in places.spots else f' {min(km(x, y) for x in spots for y in places.spots[f]):.0f}km'
    return ((f'village in {len(spots)} places' if spots else 'village unlocated') + ' | areas ' + ', '.join(f'{n} {a}' for n, a in areas)
            + ' | places ' + ', '.join(f'{n} {o}{far(o)}' for n, o in top))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--sample', type=int, default=0)
    ap.add_argument('--cuts', action='store_true', help='every completion of a cut value, its count and entries')
    ap.add_argument('--diff', action='store_true', help='every value read otherwise than the table on disk')
    args = ap.parse_args()
    # a table already written has changed what the files hold: read its keys again too, so a re-run keeps them
    old = {}
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            old = json.load(f)
    places = Places()
    vals = collections.Counter(old.keys())
    # one unit's file at a time: the places it knows, and the census's values its records hold
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        p = os.path.join(ROOT, 'website', 'public', cfg['json_file'])
        if not os.path.exists(p):
            continue
        with open(p, encoding='utf-8') as f:
            rs = json.load(f)
        places.add(code, rs)
        census = 131 <= code <= 138
        for s in rs:
            v = s.get('death_place') or ''
            if v and (census or (TWO_PARTS.match(v) and v[0].isupper())):
                vals[v] += 1
        del rs
    # the census's own entries, whichever record holds them; a reader's place opens with its preposition ("na Bilo-gori") and is left
    printed, samples = collections.Counter(), collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, 'data-extraction', 'zrtve-rata', '*-entries.json'))):
        with open(path, encoding='utf-8') as f:
            for e in json.load(f):
                v = scan_marks(e.get('death_place') or '')
                if v:
                    vals[v] += 1
                    printed[v] += 1
                    if len(samples[v]) < 3:
                        samples[v].append(f"{e['soldier_id']} {e.get('name', '')}")
    places.finish(printed)
    vals = collections.Counter({v: n for v, n in vals.items() if v[0].isupper()})
    table, hows, ex = {}, collections.Counter(), collections.defaultdict(list)
    for v, n in vals.items():
        new, how = form(v, places)
        if new is not None and new != v:
            table[v] = new
            hows[how] += n
            ex[how].append((v, new, n))
    print(len(vals), 'values,', len(table), 'in the table')
    print(hows.most_common())
    if args.sample:
        random.seed(5)
        for how, rows in ex.items():
            print('===', how, len(rows))
            rows.sort(key=lambda r: -r[2])
            for r in rows[:args.sample // 2] + random.sample(rows, min(args.sample // 2, len(rows))):
                print('  ', r[2], repr(r[0]), '->', repr(r[1]))
    changed = {v: (old.get(v), table.get(v)) for v in set(old) | set(table) if old.get(v) != table.get(v)}
    print(len(changed), 'values read otherwise than the table on disk')
    if args.diff:
        for v, (a, b) in sorted(changed.items(), key=lambda r: (-vals.get(r[0], 0), r[0])):
            print(f'  {vals.get(v, 0):4} {v!r}: {a!r} -> {b!r}')
    if args.cuts:
        for how in ('cut', 'cut, the site only', 'area cut', 'two parts'):
            rows = sorted(ex.get(how, ()), key=lambda r: (-r[2], r[0]))
            if how == 'two parts':
                # a joined value's cut area ("Sv.marija-slove")
                rows = [r for r in rows if len(r[0]) >= 14 and fold(r[1].split(', ')[-1]) != fold(r[0].split('-')[-1].split(',')[-1].strip())]
            print(f'=== {how}: {len(rows)} values, {sum(r[2] for r in rows)} records')
            for v, new, n in rows:
                print(f'  {n:4} {v!r} -> {new!r}   [{rivals(v, how, places)}]   ' + '; '.join(samples.get(v, ())[:2]))
    if args.write:
        with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(dict(sorted(table.items())), f, ensure_ascii=False, indent=0)
        print('written', OUT)


if __name__ == '__main__':
    main()
