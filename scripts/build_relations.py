"""
Group soldiers born in the same place, across all units, for the record dialog's "Iz istog mesta" tree.

birth_place is printed many ways ("Široka Kula, Gospić", "Šir. Kula", "Kladari Doboj", "u Gradcu, Virovitica",
"Budisava (Titel)"), so each one is reduced to a key: the village and its municipality, both folded (no case, no
diacritics). The rules, in order:
    split into segments at commas, dashes and brackets; drop countries and regions ("Srbija", "SR BiH", "Lika")
    "Kladari Doboj"   a known municipality glued to the village is split off
    "G. Vukovsko"     an abbreviation is expanded when the corpus spells it out one way only
    "Gradcu"          a rare locative/genitive becomes a common nominative (Gradac)
    "Solin"           a village printed without its municipality gets the one the other records give it
Precision over recall: a village name printed in several municipalities and given none here is left unlinked.

Writes website/public/relations/places.json; the data JSONs are not touched.

Usage:
    python scripts/build_relations.py              # stats and samples only
    python scripts/build_relations.py --write
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from name_utils import BRIGADE_CONFIGS  # noqa: E402
from cleanup_text_fields import live_json_files  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'website' / 'public' / 'relations' / 'places.json'

# Not a place one could be "from the same village" of
REGIONS = {
    'srbija', 'bih', 'bosna', 'hercegovina', 'bosna i hercegovina', 'hrvatska', 'crna gora', 'slovenija', 'makedonija',
    'vojvodina', 'kosovo', 'kosmet', 'sandzak', 'jugoslavija', 'sfrj', 'italija', 'sssr', 'ssr', 'rusija', 'ukrajina',
    'madjarska', 'madarska', 'austrija', 'nemacka', 'njemacka', 'ceska', 'cssr', 'csr', 'slovacka', 'rumunija',
    'rumunjska', 'bugarska', 'albanija', 'grcka', 'poljska', 'francuska', 'lika', 'kordun', 'banija', 'slavonija',
    'srem', 'dalmacija', 'zagorje', 'hrvatsko zagorje', 'primorje', 'hrvatsko primorje', 'istra', 'gorski kotar',
    'boka', 'boka kotorska', 'sumadija', 'posavina', 'podravina', 'pomoravlje', 'banat', 'backa', 'baranja',
    'krajina', 'bosanska krajina', 'podrinje', 'romanija', 'majevica', 'semberija', 'posavina', 'zumberak',
    'n/m', 'nn', 'nepoznato', 'nepoznat', 'isto', 'isti', 'kod', 'opcina', 'opstina', 'kotar', 'srez', 'okrug',
    # ethnicities and the like that the field extractor occasionally leaves in
    'srbin', 'srpkinja', 'hrvat', 'hrvatica', 'jevrej', 'jevrejin', 'jevrejka', 'zidov', 'musliman', 'muslimanka',
    'crnogorac', 'slovenac', 'slovenec', 'makedonac', 'madjar', 'slovak', 'rus', 'italijan', 'talijan', 'nijemac',
    'nemac', 'cigan', 'ciganin', 'rom', 'zemljoradnik', 'radnik', 'djak', 'student', 'borac', 'jugosloven',
    'jugoslovenka', 'jugoslaven', 'jugoslavenka',
}
# The first word of a two-word village name, never a village by itself ("Gornje Plužine")
PREFIX = {
    'gornji', 'gornja', 'gornje', 'donji', 'donja', 'donje', 'veliki', 'velika', 'veliko', 'mali', 'mala', 'malo',
    'novi', 'nova', 'novo', 'stari', 'stara', 'staro', 'srednji', 'srednja', 'srednje', 'sveti', 'sveta', 'sveto',
    'bosanski', 'bosanska', 'bosansko', 'slavonski', 'slavonska', 'slavonsko', 'srpski', 'srpska', 'srpsko',
    'hrvatski', 'hrvatska', 'crni', 'crna', 'crno', 'beli', 'bela', 'belo', 'bijeli', 'bijela', 'bijelo', 'gorni',
    'dolnji', 'dolnja', 'mladi', 'zlatni', 'kraljevo', 'banja', 'titov', 'titova', 'titovo', 'sv', 'g', 'd', 'v', 'm', 'n',
}
LEAD = re.compile(r'^(?:rođen[a]?\s+(?:je\s+)?|u\s+s(?:elu)?\.?\s+|iz\s+s(?:ela)?\.?\s+|s\.\s*|sel[oau]\s+|zaselak\s+|'
                  r'u\s+|iz\s+|kod\s+|op(?:ć|š|c|s)?(?:ina|tina)?\.?\s+|kotar\s+|srez\s+|kot\.\s+|o\.\s+)', re.I)
TITOV = re.compile(r'^titov[aoe]?\s+')


def fold(s: str) -> str:
    s = s.lower().replace('đ', 'dj').replace('dž', 'dz')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9. ]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip(' .')


def segments(raw: str) -> list[str]:
    raw = raw.replace('SI.', 'Sl.').replace('Sl ', 'Sl. ')
    parts = re.split(r'\s*[,;()/]\s*|\s+[-–—]\s+', raw)
    out = []
    for p in parts:
        p = p.strip(' .-–—')
        for _ in range(2):
            p = LEAD.sub('', p).strip()
        f = fold(p)
        if not f or len(f) < 2 or f in REGIONS or re.fullmatch(r'[\d. ]+', f) or re.match(r'^(?:sr|sap|nr)\s', f):
            continue
        out.append(p)
    return out


def load():
    live = live_json_files()
    files, recs = [], []
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if cfg['json_file'] not in live:
            continue
        idx = len(files)
        files.append(cfg['json_file'])
        for s in json.loads((ROOT / 'website' / 'public' / cfg['json_file']).read_text(encoding='utf-8')):
            recs.append((idx, s))
    return files, recs


class Places:
    def __init__(self, raws: Counter):
        self.raws = raws
        self.seg = {r: segments(r) for r in raws}
        # how often each folded segment is printed first (a village) and later (a municipality)
        self.first, self.later, self.spelled = Counter(), Counter(), defaultdict(Counter)
        for r, n in raws.items():
            for i, p in enumerate(self.seg[r]):
                (self.first if i == 0 else self.later)[fold(p)] += n
                self.spelled[fold(p)][p] += n
        self.known = self.first + self.later
        self.rule_hits = Counter()
        self.samples = defaultdict(list)

    def hit(self, rule, before, after):
        self.rule_hits[rule] += 1
        if len(self.samples[rule]) < 8:
            self.samples[rule].append(f'{before} -> {after}')

    def expand(self, f: str) -> str:
        """'g. vukovsko' -> 'gornje vukovsko' when the corpus spells it out one way only"""
        toks = f.split()
        if not any(t.endswith('.') for t in toks):
            return f
        rx = re.compile('^' + ' '.join(re.escape(t[:-1]) + r'[a-z]*' if t.endswith('.') else re.escape(t) for t in toks) + '$')
        full = {k for k in self.known if '.' not in k and rx.match(k)}
        if len(full) == 1:
            out = full.pop()
            self.hit('abbreviation', f, out)
            return out
        return f

    # locative ("u Gradcu", "u Jasenjanima") and genitive ("iz Drašnice") endings, back to the nominative
    LOCATIVE = [('cu', 'ac'), ('ku', 'ak'), ('u', ''), ('u', 'o'), ('u', 'e'), ('i', 'a'), ('ima', 'i'),
                ('ama', 'e'), ('oj', 'a'), ('e', 'a'), ('ca', 'ac'), ('ka', 'ak')]

    def nominative(self, f: str) -> str:
        """'gradcu' -> 'gradac': only a rare form, only to a common known one"""
        if self.known[f] >= 3:
            return f
        head, _, last = f.rpartition(' ')
        best = None
        for end, repl in self.LOCATIVE:
            if last.endswith(end) and len(last) - len(end) >= 3:
                cand = ((head + ' ') if head else '') + last[:len(last) - len(end)] + repl
                if self.known[cand] >= 5 and self.known[cand] >= 4 * max(1, self.known[f]):
                    if best is None or self.known[cand] > self.known[best]:
                        best = cand
        if best:
            self.hit('locative', f, best)
            return best
        return f

    def norm(self, p: str) -> str:
        f = self.expand(fold(p))
        f = self.nominative(f)
        return f

    def muni(self, f: str) -> str:
        return TITOV.sub('', f)

    def split_glued(self, segs: list[str]) -> list[str]:
        """'Kladari Doboj' -> 'Kladari', 'Doboj' when Doboj is a common municipality and the whole is rare"""
        if len(segs) != 1:
            return segs
        f = fold(segs[0])
        words = f.split()
        if len(words) < 2 or self.known[f] > 1:
            return segs
        for k in (2, 1):
            if len(words) <= k:
                continue
            tail, rest = ' '.join(words[-k:]), ' '.join(words[:-k])
            if (self.later[tail] >= 10 and self.first[rest] >= 2 and len(rest) >= 3
                    and rest.split()[-1].rstrip('.') not in PREFIX and tail.split()[0] not in PREFIX):
                self.hit('glued municipality', segs[0], f'{rest} | {tail}')
                orig = segs[0].split()
                return [' '.join(orig[:-k]), ' '.join(orig[-k:])]
        return segs

    def is_town(self, v: str) -> bool:
        """Other villages are printed with it as their municipality"""
        return self.later[v] >= 10

    def parse(self, raw: str):
        segs = self.split_glued(self.seg[raw])
        if not segs:
            return None
        village = self.norm(segs[0])
        munis = [self.muni(self.norm(p)) for p in segs[1:]]
        # a municipality printed only once or twice in the whole corpus is noise ("Mostar, Mtostar")
        munis = [m for m in munis if m and m != village and m not in REGIONS and self.known[m] >= 3]
        return village, (munis[0] if munis else None)

    def keys(self, recs):
        """(file, birth_place) -> (village, municipality); municipality '' when the village is the town itself"""
        parsed = {r: self.parse(r) for r in self.raws}
        given, given_in = defaultdict(Counter), defaultdict(Counter)   # municipalities a village is printed with
        bare, bare_in = Counter(), Counter()
        for fi, s in recs:
            p = parsed.get((s.get('birth_place') or '').strip())
            if not p:
                continue
            v, m = p
            if m:
                given[v][m] += 1
                given_in[fi, v][m] += 1
            else:
                bare[v] += 1
                bare_in[fi, v] += 1

        def dominant(c: Counter):
            top, n = c.most_common(1)[0]
            return top if len(c) == 1 or (n >= 0.85 * sum(c.values()) and n >= 4) else None

        out, ambiguous = {}, Counter()
        for fi, s in recs:
            r = (s.get('birth_place') or '').strip()
            if not parsed.get(r) or (fi, r) in out:
                continue
            v, m = parsed[r]
            town_muni = self.is_town(v) and given.get(v) and dominant(given[v])
            if m and self.is_town(v) and (m == town_muni or not self.is_town(m) and self.later[m] < 3 * self.later[v]):
                m = None                                     # "Solin, Split", "Banja Luka, X": the town itself
            if m is None:
                here = given_in.get((fi, v))
                if self.is_town(v):
                    # the town, unless this unit mostly prints a village of that name with its municipality (Mionica, Gradačac)
                    m = dominant(here) if here and dominant(here) and sum(here.values()) >= bare_in[fi, v] else ''
                    if m == town_muni:
                        m = ''
                    if m:
                        self.hit('town name, village in this unit', v, f'{v} | {m}')
                elif here and dominant(here):
                    m = dominant(here)                       # the unit's own records place it
                    self.hit('municipality from the same unit', v, f'{v} | {m}')
                elif not given.get(v) or bare[v] >= 3 * sum(given[v].values()):
                    m = ''                                   # a village no record (or hardly any) places
                elif dominant(given[v]) and given[v].most_common(1)[0][1] >= 2:
                    m = dominant(given[v])
                    self.hit('municipality from other units', v, f'{v} | {m}')
                else:
                    ambiguous[v] += 1
                    continue
            out[fi, r] = (v, m)
        return out, ambiguous


def display(spelled: Counter) -> str:
    # the commonest spelling with diacritics and a capital
    best = max(spelled.items(), key=lambda kv: (kv[1] * (2 if re.search('[čćžšđČĆŽŠĐ]', kv[0]) else 1), kv[1]))[0]
    return best[:1].upper() + best[1:]


def life(s: dict) -> str:
    born = re.search(r'\d{4}', s.get('birth_year') or '')
    died = re.search(r'(?:18|19)\d\d', s.get('death_date') or '')
    return f"{born.group(0) if born else ''}–{died.group(0) if died else ''}".strip('–') if born or died else ''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    files, recs = load()
    raws = Counter(s['birth_place'].strip() for _, s in recs if s.get('birth_place'))
    places = Places(raws)
    keyed, ambiguous = places.keys(recs)

    members = defaultdict(list)
    vspell, mspell = defaultdict(Counter), defaultdict(Counter)
    for fi, s in recs:
        r = (s.get('birth_place') or '').strip()
        if (fi, r) not in keyed:
            continue
        key = keyed[fi, r]
        members[key].append([s['soldier_id'], s.get('full_name') or '', fi, life(s)])
        segs = places.split_glued(places.seg[r])
        vspell[key][segs[0]] += 1
        if key[1] and len(segs) > 1:
            mspell[key][segs[1]] += 1

    linked = {k: v for k, v in members.items() if len(v) >= 2}
    with_bp = sum(1 for _, s in recs if s.get('birth_place'))
    n_linked = sum(len(v) for v in linked.values())
    print(f'records {len(recs)}, with birth_place {with_bp}, distinct spellings {len(raws)}')
    print(f'places {len(members)}, with 2+ soldiers {len(linked)}, soldiers linked {n_linked} ({n_linked / with_bp:.0%} of those with a birthplace)')
    print(f'ambiguous villages left unlinked: {len(ambiguous)} ({sum(ambiguous.values())} records), e.g.',
          ', '.join(f'{v} ({n})' for v, n in ambiguous.most_common(12)))
    for rule, n in places.rule_hits.most_common():
        print(f'\n{rule}: {n}\n  ' + '\n  '.join(places.samples[rule]))
    print('\nlargest places:')
    for k, v in sorted(linked.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(f'  {display(vspell[k])}{", " + display(mspell[k]) if mspell[k] else ""}: {len(v)}  ({len({m[2] for m in v})} units)')

    if args.write:
        order = sorted(linked, key=lambda k: -len(linked[k]))
        index = {k: i for i, k in enumerate(order)}
        doc = {
            'files': files,
            # [village, municipality, [[soldier_id, name, file, years], ...]]; the site finds a record's place by its id
            'places': [[display(vspell[k]), display(mspell[k]) if mspell[k] else '', sorted(linked[k], key=lambda m: m[1])]
                       for k in order],
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'\nwrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()
