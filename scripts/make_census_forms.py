"""The census's place column in one form: data-extraction/places/census_forms.json, the stored value and the place, which standardize_fields.place_form reads.

The column prints a village and its area joined in small letters ("Doboj-tuzla", "Stol,pirot"), abbreviates without a space ("D.lapac", "Sv.križ"), writes a name's second word small ("Banja luka", "Crna gora")
and cuts everything at 15 characters ("Kestenovac-d.la", "Kosovska mitrov"). What it means is read here against the places the site knows, every part of every birthplace and place of death; a part it doesn't know
only takes a capital. Run after a batch of new census records; dry run without --write.

    python scripts/make_census_forms.py --sample 30
    python scripts/make_census_forms.py --write
"""
import argparse
import bisect
import collections
import glob
import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from name_utils import BRIGADE_CONFIGS  # noqa: E402
from standardize_fields import scan_marks  # noqa: E402

OUT = os.path.join(ROOT, 'data-extraction', 'places', 'census_forms.json')
FOLD = str.maketrans('čćžšđ', 'cczsd')
LOW = 'a-zčćžšđ'
UP = 'A-ZČĆŽŠĐ'
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
WHOLE = {'Han-pjesak': 'Han Pijesak', 'Han-pijesak': 'Han Pijesak', 'Srem.front': 'Sremski front', 'Srem-front': 'Sremski front', 'Srem front': 'Sremski front', 'Blato-korčula': 'Blato, Korčula', 'Ivan-planina': 'Ivan-planina', 'Ivan-sedlo': 'Ivan-sedlo', 'Nov-ci': 'Novci',
         'Šar-planina': 'Šar-planina', 'Šator-planina': 'Šator-planina', 'Zelen-gora': 'Zelengora', 'Šaren-grad': 'Šarengrad', 'Cetin-grad': 'Cetingrad', 'Oslobađ.bgd-a': 'Beograd'}
# a Slovene name's second word is small by its own rule
KEEP_SMALL = re.compile(rf'(?:\bNovo mesto\b|\s(?:vas|trg|gorica|dolina)$)')
ABBR = re.compile(rf'^([{UP}][{LOW}]{{0,4}})\.([{LOW}])')
# joined without a space after a comma or around a hyphen: "Doboj-tuzla", "Stol,pirot", "Babina greda- b" (a comma and a space is a reader's, "Sutjeska, kod Popovog Mosta")
TWO_PARTS = re.compile(rf'^(.*?[{LOW}.])(-\s*|,)([{LOW}][^-,]*)$')
NOT_A_PLACE = re.compile(r'(?i)\b(?:nov|nob|noo)-[aeu]$|\btbc-a$')


def fold(t):
    return t.lower().translate(FOLD)


class Places:
    def __init__(self, units):
        known = collections.Counter()
        for code, rs in units.items():
            census = 131 <= code <= 138
            for s in rs:
                for k in ('birth_place', 'death_place'):
                    v = s.get(k) or ''
                    # the column itself is what is being read, so only its short values, which it didn't cut, and no joined ones
                    if census and k == 'death_place' and (len(v) >= 14 or TWO_PARTS.match(v)):
                        continue
                    for part in re.split(r',\s*|\s*\(|\)', v):
                        part = re.sub(r'^(?:kod|u|na|s\.|selo|sela|selu)\s+', '', part.strip())
                        if len(part) > 1 and part[0].isupper():
                            known[part] += 1
        self.known = known
        self.by_fold = collections.defaultdict(collections.Counter)
        for k, n in known.items():
            self.by_fold[fold(k)][k] += n
        self.keys = sorted(self.by_fold)

    def exact(self, word, least=3):
        """the place of this spelling, carons and all, in the capitals the site prints most"""
        c = [(n, k) for k, n in self.by_fold.get(fold(word), {}).items() if k.lower() == word.lower()]
        if not c:
            return None
        c.sort(reverse=True)
        return c[0][1] if sum(n for n, _ in c) >= least else None

    def count(self, word):
        return sum(n for k, n in self.by_fold.get(fold(word), {}).items() if k.lower() == word.lower())

    def complete(self, word, least=8):
        """a place the column's width cut: the place it begins, where one stands far above the rest"""
        w = fold(word)
        i = bisect.bisect_left(self.keys, w)
        found = []
        while i < len(self.keys) and self.keys[i].startswith(w):
            if self.keys[i] != w:
                found.append((sum(self.by_fold[self.keys[i]].values()), self.by_fold[self.keys[i]].most_common(1)[0][0]))
            i += 1
        found.sort(reverse=True)
        if not found or found[0][0] < least or (len(found) > 1 and found[0][0] < found[1][0] * 5):
            return None
        return found[0][1]


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
        cut = len(v) >= 14
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
        second = places.exact(b) or (cut and places.complete(b))
        if second:
            return f'{first}, {ABBR.sub(lambda x: f"{x.group(1)}. {x.group(2).upper()}", second)}', 'two parts'
        return f'{first}, {part_up(b)}', 'second unknown'
    v2 = small_words(v)
    if len(v2) in (14, 15) and not places.known.get(v2):
        c = places.complete(v2)
        if c:
            return c, 'cut'
    # one abbreviation before one name; "Boln.u zagrebu", "Nar.bol.pljevlj" are no such thing
    n = v2 if re.search(rf'^[^.]*\.[{LOW}]*\.|^[^.]*\.(?:u|na|kod|pri|za)\s', v2) else ABBR.sub(lambda x: f'{x.group(1)}. {x.group(2).upper()}', v2)
    if re.search(rf'\s[{LOW}]', n) and not KEEP_SMALL.search(n):
        c = places.exact(n, 5)
        if c and c != n and c.lower() == n.lower():
            return c, 'small letter'
    if n != v:
        return n, 'abbreviation'
    return v, ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--sample', type=int, default=0)
    args = ap.parse_args()
    units = {}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        p = os.path.join(ROOT, 'website', 'public', cfg['json_file'])
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                units[code] = json.load(f)
    # a table already written has changed what the files hold: read its keys again too, so a re-run keeps them
    old = {}
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            old = json.load(f)
    places = Places(units)
    vals = collections.Counter(old.keys())
    # the census's own entries, whichever record holds them; a reader's place opens with its preposition ("na Bilo-gori") and is left
    for path in glob.glob(os.path.join(ROOT, 'data-extraction', 'zrtve-rata', '*-entries.json')):
        with open(path, encoding='utf-8') as f:
            for e in json.load(f):
                v = scan_marks(e.get('death_place') or '')
                if v:
                    vals[v] += 1
    for code, rs in units.items():
        census = 131 <= code <= 138
        for s in rs:
            v = s.get('death_place') or ''
            if v and (census or (TWO_PARTS.match(v) and v[0].isupper())):
                vals[v] += 1
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
    if args.write:
        with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(dict(sorted(table.items())), f, ensure_ascii=False, indent=0)
        print('written', OUT)


if __name__ == '__main__':
    main()
