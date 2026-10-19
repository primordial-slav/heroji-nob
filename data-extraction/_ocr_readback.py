"""
Read back the words Tesseract garbles in the scans without a text layer (data-extraction/ocr_scan.py), as the
spellings the site already knows: each letter the OCR confuses is tried as each of its look-alikes, and the reading
the site's names (or places) know best is taken.

Its slips on the Cyrillic books (srp model): Б, В and Ђ for one another at a word's start ("ЂУЛАЈИЋ" = Булајић,
"ЂОЖО" = Божо), Г read as Т ("ДРАТО", "Тацко" = Гацко), К as Ж ("Жопривице"), a word begun twice, small then capital
("вБОЈОВИЋ", "кКљаковица", "ЂБогетићи"), a capital read small ("цетиње"), and Latin look-alikes inside a word ("JOBO").
On the Latin books (hrv model): carons lost or added (Ć/C, Š/S, Ž/Z, Č/C), I for l, rn for m.

    corpus = Corpus()                       # the units' records, the census's entries, Montenegro's Spomenica
    corpus.surname('ЂУЛАЈИЋ')  -> 'Bulajić'   (Latin, the site's case)
    corpus.given('ДРАТО')      -> 'Drago'
    corpus.genitive('Ђорђија') -> 'Đorđija'  (a father as printed, in the genitive)
    corpus.place('Тацко')      -> 'Gacko'
A word no reading of which the site knows is returned as read (in Latin).
"""
from __future__ import annotations

import itertools
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import cyrillic_to_latin

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')

# the OCR's misreadings, as {the letter read: {the letter printed: the odds that it was}}: Tesseract's slips on the
# Cyrillic print of these books (Б read as Ђ often, as В seldom; Г as Т; К as Ж; в as р; о as с; м as н)
CYR = {'Ђ': {'Б': 0.4, 'В': 0.03}, 'В': {'Б': 0.1, 'Ђ': 0.03}, 'Б': {'В': 0.03, 'Ђ': 0.03},
       'Т': {'Г': 0.3}, 'т': {'г': 0.2}, 'Ж': {'К': 0.3}, 'ж': {'к': 0.1}, 'К': {'Ж': 0.03},
       'р': {'в': 0.15}, 'в': {'р': 0.03}, 'Р': {'В': 0.1}, 'с': {'о': 0.15}, 'С': {'О': 0.15}, 'о': {'с': 0.03},
       'н': {'м': 0.1}, 'м': {'н': 0.03}, 'ђ': {'б': 0.1}, 'Ш': {'Щ': 0.01},
       # Latin look-alikes in a Cyrillic word are the Cyrillic letter (best() maps them before reading back)
       'A': {'А': 1}, 'B': {'В': 1}, 'C': {'С': 1}, 'E': {'Е': 1}, 'H': {'Н': 1}, 'J': {'Ј': 1}, 'K': {'К': 1},
       'M': {'М': 1}, 'O': {'О': 1}, 'P': {'Р': 1}, 'T': {'Т': 1}, 'X': {'Х': 1}, 'Y': {'У': 1}, 'a': {'а': 1},
       'c': {'с': 1}, 'e': {'е': 1}, 'j': {'ј': 1}, 'o': {'о': 1}, 'p': {'р': 1}, 'x': {'х': 1}, 'y': {'у': 1},
       'r': {'г': 1}, 'n': {'п': 1}, 'u': {'и': 1}}
LOOKALIKE = {ch: next(iter(v)) for ch, v in CYR.items() if 'A' <= ch <= 'z'}
# the same for Latin print: carons lost or added, I for l
LAT = {'C': {'Ć': 0.2, 'Č': 0.2}, 'Ć': {'Č': 0.1, 'C': 0.05}, 'Č': {'Ć': 0.1, 'C': 0.05}, 'S': {'Š': 0.2},
       'Š': {'S': 0.05}, 'Z': {'Ž': 0.2}, 'Ž': {'Z': 0.05}, 'D': {'Đ': 0.1}, 'Đ': {'D': 0.05},
       'c': {'ć': 0.2, 'č': 0.2}, 'ć': {'č': 0.1, 'c': 0.05}, 'č': {'ć': 0.1, 'c': 0.05}, 's': {'š': 0.2},
       'š': {'s': 0.05}, 'z': {'ž': 0.2}, 'ž': {'z': 0.05}, 'd': {'đ': 0.1}, 'đ': {'d': 0.05},
       'l': {'I': 0.1}, 'I': {'l': 0.1}, '0': {'O': 0.5}, '1': {'I': 0.3, 'l': 0.3}}


# a capital printed (or read) twice, a look-alike before the letter: "ЂБОГЕТИЋИ", "ЖКАНКАРАШ", "МЦЕБАЛОВИЋ", "ТГрадичка"
TWICE = {'ЂБ', 'ВБ', 'БВ', 'ЂВ', 'ЖК', 'ТГ', 'МЦ', 'ШЩ'}
TWICE_LAT = {'ĐB', 'VB', 'BV', 'ĐV', 'ŽK', 'TG', 'MC', 'Đb', 'Žk', 'Tg'}


# the odds of one letter misread: a reading that changes d letters of the word counts SLIP**d times its frequency
SLIP = 0.08


def fold(text: str) -> str:
    return (text or '').translate(FOLD).lower()


def latin(word: str) -> str:
    return cyrillic_to_latin(word)


def title(word: str) -> str:
    return '-'.join(p[:1].upper() + p[1:].lower() for p in word.split('-'))


def _distance(a: str, b: str, most: int) -> int:
    """Levenshtein distance, cut off above most"""
    if abs(len(a) - len(b)) > most:
        return most + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > most:
            return most + 1
        prev = cur
    return prev[-1]


class Corpus:
    def __init__(self, skip_units: tuple[str, ...] = (), census: tuple[str, ...] = ('crg',),
                 entries: tuple[str, ...] = ('spomenica-crnogorskim-antifasistima',)):
        self.surnames, self.givens, self.fathers, self.places = Counter(), Counter(), Counter(), Counter()
        self._spellings: dict[str, Counter] = {}
        for f in sorted((ROOT / 'website' / 'public').glob('*soldiers.json')):
            if f.name in skip_units:
                continue
            for s in json.loads(f.read_text(encoding='utf-8')):
                self._person(s.get('last_name'), s.get('first_name'), s.get('middle_name'))
                for k in ('birth_place', 'death_place'):
                    self._place(s.get(k))
        for vol in census:
            path = HERE / 'zrtve-rata' / f'zrtve-rata-1964-{vol}-entries.json'
            for e in json.loads(path.read_text(encoding='utf-8')):
                self._person(e.get('last_name'), e.get('first_name'), '')
                for k in ('born_in', 'death_place'):
                    self._place(e.get(k))
        for book in entries:
            path = HERE / 'znaci' / f'{book}-entries.json'
            if path.exists():
                for e in json.loads(path.read_text(encoding='utf-8')):
                    self._person(e.get('last_name'), e.get('first_name'), '')
                    for k in ('born_in', 'death_place'):
                        self._place(e.get(k))

    def _person(self, last, first, father):
        for w in re.split(r'[\s-]+', last or ''):
            if len(w) > 1:
                self.surnames[fold(w)] += 1
                self._spellings.setdefault(fold(w), Counter())[w] += 1
        for w in (first or '').split():
            if len(w) > 1:
                self.givens[fold(w)] += 1
                self._spellings.setdefault(fold(w), Counter())[w] += 1
        if father and len(father) > 2 and not father.endswith('.'):
            self.fathers[fold(father)] += 1
            self._spellings.setdefault(fold(father), Counter())[father] += 1

    def _place(self, text):
        for part in re.split(r'\s*[,(]\s*|\)', text or ''):
            part = part.strip()
            if len(part) > 2:
                self.places[fold(part)] += 1
                for w in part.split():
                    if len(w) > 2:
                        self.places[fold(w)] += 1

    @property
    def given_spelling(self) -> dict:
        return self.spelling

    @property
    def spelling(self) -> dict:
        if not hasattr(self, '_spelling'):
            self._spelling = {k: c.most_common(1)[0][0] for k, c in self._spellings.items()}
        return self._spelling

    # -- reading a word back -------------------------------------------------------------------------------------
    @staticmethod
    def readings(word: str, opts: dict, limit: int = 400) -> dict[str, float]:
        """Every reading of word with its odds (1 for the word as read): each letter as the letters opts says the OCR
        mistakes for it, a speck or a doubled capital before it dropped, letters printed double collapsed"""
        words = {word: 1.0}
        # a speck read as a small letter before the word: "tštedim" = Štedim, "ttumadija" = Šumadija
        if len(word) > 4 and word[:1].islower():
            words[word[1:]] = max(words.get(word[1:], 0), SLIP)
            words[word[2:]] = max(words.get(word[2:], 0), SLIP * SLIP)
        # a word begun twice: "вБОЈОВИЋ", "кКљаковица", "ЂБогетићи", "ЖКопривице", "МЦЕБАЛОВИЋ"
        if len(word) > 3 and word[1].isupper() and (word[0].islower() or word[:2] in TWICE):
            words[word[1:]] = max(words.get(word[1:], 0), 0.3)
        # letters printed double, small and capital ("дДОоКкнНИЋ" = ДОКНИЋ, "Миittушковић")
        collapsed = re.sub(r'(.)\1+', r'\1', re.sub(r'(\w)(?=\1)', '', word, flags=re.I), flags=re.I)
        if collapsed != word and len(collapsed) >= 3:
            words[collapsed] = max(words.get(collapsed, 0), 0.3)
        # a capital read small at a word's start: "цетиње", "кљаковица", "пљевља"
        for w, p in list(words.items()):
            if w[:1].islower():
                up = w[:1].upper() + w[1:]
                words[up] = max(words.get(up, 0), p)
        out: dict[str, float] = {}
        for w, p0 in words.items():
            slots = [[(ch, 1.0)] + list(opts.get(ch, {}).items()) for ch in w]
            n = 1
            for s in slots:
                n *= len(s)
            if n > limit:          # too many: only the first three letters' readings (where most slips are)
                slots = [s if i < 3 else s[:1] for i, s in enumerate(slots)]
            for combo in itertools.product(*slots):
                c = ''.join(ch for ch, _ in combo)
                p = p0
                for _, q in combo:
                    p *= q
                if p > out.get(c, 0):
                    out[c] = p
        return out

    def word(self, word: str, opts: dict = CYR, alts: tuple = ()) -> str:
        """A word of a biography, read back from the words of the units' entries; in the word's own script"""
        if not hasattr(self, '_words'):
            self._words = Counter()
            for f in sorted((ROOT / 'website' / 'public').glob('*soldiers.json')):
                for s in json.loads(f.read_text(encoding='utf-8')):
                    for w in re.findall(r'[A-Za-zČĆŽŠĐčćžšđ]{3,}', s.get('additional_info') or ''):
                        self._words[fold(w)] += 1
        return self.best(word, self._words, opts, alts=alts, script=True)

    def best(self, word: str, table: Counter, opts: dict, alts: tuple = (), script: bool = False) -> str:
        """The reading of word that is likeliest, in Latin: how often the site has it, times the odds of the OCR's
        misreading it so. A name the OCR read right and the site knows wins over a commoner one a letter away
        (БАЊЕВИЋ stays Banjević, ЂОКО stays Đoko); an unknown one gives way (ЂУЛАЈИЋ is Bulajić). alts: the OCR's
        other readings of the word (ocr_scan.py's first reading of a word it read again), weighed alike. A word
        none of whose readings the site knows is returned as read."""
        if not word:
            return word
        if opts is CYR:                # a Latin look-alike in a Cyrillic book is the Cyrillic letter: "JOBO", "PAJOBAH"
            word = ''.join(LOOKALIKE.get(ch, ch) for ch in word)
            alts = tuple(''.join(LOOKALIKE.get(ch, ch) for ch in a) for a in alts)
        as_read = word if script else latin(word)
        best_score, best_form = 0.0, as_read
        for src in [word] + [a for a in alts if a and a != word]:
            for c, p in self.readings(src, opts).items():
                n = table[fold(latin(c))]
                if n and n * p > best_score:
                    best_score, best_form = n * p, (c if script else latin(c))
        # the table is kept without carons: a Latin word the OCR read with none ("STANISIC", "Dusan") takes the
        # spelling the site gives it most often (Stanišić, Dušan); one read with its carons keeps them
        if opts is LAT and not re.search('[čćžšđČĆŽŠĐ]', best_form):
            usual = self.spelling.get(fold(best_form))
            if usual and fold(usual) == fold(best_form) and len(usual) == len(best_form):
                best_form = ''.join(u.upper() if b.isupper() else u.lower() for u, b in zip(usual, best_form))
        return best_form

    def nearest(self, word: str, table: Counter, least: int = 2) -> str:
        """The name the site knows (at least `least` times) closest to word, one letter off (two in a long word) and
        no other as close: the OCR's slips no letter table foresees ("Kovačerić", "Mijuškorić", "Bapcković")"""
        w = fold(word)
        if len(w) < 5:
            return ''
        most = 1 if len(w) < 8 else 2
        best, ties = None, 0
        for k, n in table.items():
            # the first letter must agree, unless the word's first two are both capitals of a word begun twice
            if n < least or abs(len(k) - len(w)) > most or (k[:1] != w[:1] and not (word[:2] in TWICE_LAT and k[:1] == w[1:2])):
                continue
            d = _distance(w, k, most)
            if d <= most:
                if best is None or d < best[0] or (d == best[0] and n > best[1] * 4):
                    best, ties = (d, n, k), 0
                elif d == best[0] and n * 4 > best[1]:
                    ties += 1
        return best[2] if best and not ties else ''

    def surname(self, word: str, opts: dict = CYR, alts: tuple = (), fuzzy: bool = True) -> str:
        parts = word.split('-')
        alt_parts = [a.split('-') for a in alts if a and len(a.split('-')) == len(parts)]
        out = []
        for i, p in enumerate(parts):
            b = self.best(p, self.surnames, opts, alts=tuple(ap[i] for ap in alt_parts))
            if fuzzy and not self.surnames[fold(b)]:
                near = self.nearest(b, self.surnames)
                if near:
                    b = self._spelled(near, self.surnames)
            out.append(title(b))
        return '-'.join(out)

    def _spelled(self, folded: str, table: Counter) -> str:
        """The site's spelling (with its carons) of a folded name"""
        return self.spelling.get(folded, folded)

    def _fuzzy(self, b: str, table: Counter) -> str:
        if table[fold(b)]:
            return b
        near = self.nearest(b, table, least=3)
        return self.spelling_of(near) if near else b

    def spelling_of(self, folded: str) -> str:
        return self.spelling.get(folded) or self.given_spelling.get(folded) or folded

    def given(self, word: str, opts: dict = CYR, alts: tuple = ()) -> str:
        return title(self._fuzzy(self.best(word, self.givens, opts, alts=alts), self.givens))

    def genitive(self, word: str, opts: dict = CYR, alts: tuple = ()) -> str:
        if re.fullmatch(r'\w\.', word):          # an initial: a Latin look-alike is the Cyrillic letter ("P." = Р.)
            return title(latin(''.join(LOOKALIKE.get(ch, ch) for ch in word) if opts is CYR else word))
        return title(self._fuzzy(self.best(word, self.fathers, opts, alts=alts), self.fathers))

    def place(self, text: str, opts: dict = CYR, alts: tuple = ()) -> str:
        """A place of one or more words ("Бијело Поље", "Кос. Митровица"): each word read back, and the whole too"""
        words = text.split()
        if len(words) > 1:
            whole = latin(text)
            if self.places[fold(whole.strip('.,;:'))]:
                return whole.strip(',;:')
            # the whole place read back at once ("Вања Лука" is Banja Luka, though Vanja alone is a known word)
            options = []
            for w in words:
                core = w.strip('.,;:()')
                r = self.readings(core, opts) if len(core) > 2 else {core: 1.0}
                options.append(sorted(r.items(), key=lambda kv: -kv[1])[:6])
            best_score, best_phrase = 0.0, ''
            for combo in itertools.product(*options):
                phrase = latin(' '.join(c for c, _ in combo))
                n = self.places[fold(phrase)]
                if n:
                    score = n
                    for _, q in combo:
                        score *= q
                    if score > best_score:
                        best_score, best_phrase = score, phrase
            if best_phrase:
                return best_phrase
        alt_words = [a.split() for a in alts if a and len(a.split()) == len(words)]
        out = []
        for i, w in enumerate(words):
            core = w.strip('.,;:()')
            if len(core) <= 2 or not re.search(r'\w', core):
                out.append(latin(w))
                continue
            as_read = latin(''.join(LOOKALIKE.get(ch, ch) for ch in core) if opts is CYR else core)
            if self.places[fold(as_read)]:
                b = as_read                          # a place the site knows stays as read (villages are many and rare)
            else:
                b = self.best(core, self.places, opts, alts=tuple(aw[i].strip('.,;:()') for aw in alt_words))
            if b[:1].islower() and len(b) > 2:
                b = b[:1].upper() + b[1:]            # a capital read small: "mokra njiva", "vuči Do"
            out.append(latin(w).replace(latin(core), b) if latin(core) in latin(w) else b)
        return ' '.join(out)
