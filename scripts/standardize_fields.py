"""
The structured fields in one form, whatever book or reader they came from (2026-10-26). Each rule is a small function of
a record that returns the fields it changes, listed in RULES with its name; apply_corrections.py runs them on every
unit it writes, after the places step, so they hold on every run and for every new book. Alone:

    python scripts/standardize_fields.py                           # every rule, every unit: counts and samples
    python scripts/standardize_fields.py --rule death_date --sample 30
    python scripts/standardize_fields.py --brigade 70 --apply      # write (outside apply_corrections.py)

The rules (the user's decisions of 2026-10-26):
    captured     a fate "zarobljen" read again in the clause after the capture: "zarobljen ... i strijeljan" is streljan,
                 "ujet in obešen" ubijen, "umro u nemačkom logoru" umro, "i nestao" nestao; a man let go ("pušten kući")
                 has none; else a fate his entries name elsewhere (the extractor took "zarobljeni ustaša" for his);
                 only captured, it stays (the dialog says "Zarobljen")
    after_war    a survivor who has died since, with no year: "po osvoboditvi", "po vojni" (the Slovene rosters' "†")
                 leave the date and set death_after_war; the dialog says "Umro posle rata" in the page's language
    death_date   a date in numbers, DD.MM.YYYY: "14. februara 1941" is 14.02.1941, "15. VI 1943" 15.06.1943, "juna
                 1943" 06.1943, a night "4/5. decembra 1944" 04/05.12.1944; a date with words besides ("krajem 1942",
                 "proljeće 1944", "početkom februara 1943") stays as printed
    albanian     the census's "Šiptar" is Albanac (Šiptarka Albanka); the entries' text keeps the census's word
The books' own forms stay otherwise: ekavian and ijekavian duties as each book prints them (zamenik, zamjenik).

A rule changes a field's form, never what the entry says, and the entries' text is never touched. A field corrections
set is standardized too by a rule that only changes its form (FORM_ONLY); a rule that reads the text again leaves it.

To add a rule: write `def rule(s: dict) -> dict | None` returning {field: new value} (None removes the field), and list
it in RULES; `--rule NAME` shows what it would change before it runs with the pipeline.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_life_events import MONTH_OF, ROMAN_OF  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# ── captured: the fate after a capture ──────────────────────────────────────
CAUGHT_RE = re.compile(r'(?:zarobljen[a]?|zarobili|ujet[a]?)\b(?P<after>.{0,160})', re.I | re.S)
# the first fate the clause after the capture names
AFTER_CAUGHT = [
    ('streljan', re.compile(r'\b(?:stri?jelja\w*|strelja\w*|ustreljen\w*)', re.I)),
    ('ubijen', re.compile(r'\b(?:ubi(?:jen|li|o)\w*|zaklan\w*|zaklali|obe[šs]en\w*|obje[šs]en\w*|likvidir\w*)', re.I)),
    ('umro', re.compile(r'\b(?:umro|umrla|umr[lj]\w*|podlega\w*\s+ranama|podlegao|podlegla)', re.I)),
    ('poginuo', re.compile(r'\b(?:poginu\w*|padel|padla)', re.I)),
    ('nestao', re.compile(r'\b(?:nesta[oli]\w*|nije se (?:živ\s+)?vratio|nije se vratila|sudbina nepoznata|'
                          r'više se nije ništa saznalo|ništa se ne zna)', re.I)),
]
# a man let go or exchanged lived through the capture: "posle dva meseca ... pušten kući", "razmijenjen"
RELEASED = re.compile(r'\b(?:pu[šs]ten\w*|razmenjen\w*|razmijenjen\w*|zamenjen\w*|zamijenjen\w*|pobegao|pobjegao|'
                      r'pobegla|pobjegla|uspeo da pobegne|uspio pobjeći|oslobođen\w*)', re.I)


def first_fate(text: str) -> tuple[int, str] | None:
    """Where the first fate the text names stands, and which"""
    hits = [(m.start(), fate) for fate, r in AFTER_CAUGHT for m in [r.search(text)] if m]
    return min(hits) if hits else None


def captured(s: dict) -> dict | None:
    """The fate after a capture, read from the man's entries (a linked unit's too: the field may have come from it):
    the fate the clause after the capture names; none if he was let go; else a fate his entries name elsewhere ("zarobljen
    7. mj 1944, Knin" in one book, "streljan u Kninu od četnika" in the other), or the extractor's "zarobljen" read from
    someone else's capture ("ranio ga je zarobljeni ustaša", "pobegao iz nemačkog zarobljeništva")"""
    if s.get('death_type') != 'zarobljen':
        return None
    texts = [s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources') or []
                                                 if not o.get('ref_book')]
    released = False
    for text in texts:
        for m in CAUGHT_RE.finditer(text):
            after = m.group('after')
            fate, free = first_fate(after), RELEASED.search(after)
            if fate and not (free and free.start() < fate[0]):
                return {'death_type': fate[1]}
            released = released or bool(free)
    if released:
        return {'death_type': None}
    for text in texts:
        fate = first_fate(text)
        if fate:
            return {'death_type': fate[1]}
    return None


# ── after_war: a survivor who has died since ────────────────────────────────
AFTER_WAR = re.compile(r'(?:po\s+osvoboditvi|po\s+vojni|posle\s+rata|poslije\s+rata|nakon\s+rata|po\s+vojnoj)\.?', re.I)


def after_war(s: dict) -> dict | None:
    if AFTER_WAR.fullmatch((s.get('death_date') or '').strip()):
        return {'death_date': None, 'death_after_war': True}
    return None


# ── death_date: a date in numbers ───────────────────────────────────────────
MONTH = '|'.join(sorted(MONTH_OF, key=len, reverse=True))
ROMAN = '(?-i:XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)'          # in capitals only: the Slovene "v" is a word
DAYS = r'(?P<day>\d{1,2}(?:\s?[/–—-]\s?\d{1,2})?)'
YEAR = r'(?P<year>1[89]\d\d|20\d\d)'
DATE_FORMS = [
    # 14. 2. 1941 / 14.02.1941 / 14. II 1941 / 14. II. 1941 / 4/5. 12. 1944
    re.compile(rf'{DAYS}\s*[.,]\s*(?P<month>\d{{1,2}}|{ROMAN})\s*[.,]?\s*{YEAR}', re.I),
    # 14. februara 1941 / 14 avgusta 1942 / 4/5. decembra 1944 / 15. juna mjeseca 1943
    re.compile(rf'{DAYS}\s*\.?\s*(?P<word>{MONTH})\s+(?:mjeseca\s+|meseca\s+)?{YEAR}', re.I),
    # juna 1943 / u junu 1943 / VI 1943 / VI. 1943 / 06.1943
    re.compile(rf'(?:u\s+)?(?P<word>{MONTH})\s+(?:mjeseca\s+|meseca\s+)?{YEAR}', re.I),
    re.compile(rf'(?P<month>{ROMAN}|\d{{1,2}})\s*\.\s*{YEAR}', re.I),
    re.compile(rf'(?P<month>{ROMAN})\s+{YEAR}', re.I),
    re.compile(YEAR),
]
DAYS_IN = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def date_form(value: str) -> str:
    """'14. februara 1941' -> '14.02.1941', 'juna 1943' -> '06.1943', '1943. god.' -> '1943'; a date with other words
    ('krajem 1942', 'proljeće 1944') or one no rule reads ('9.11944', '6. 2. 45') stays as printed"""
    v = re.sub(r'\s+', ' ', value.strip())
    v = re.sub(r'\.?\s*god(?:ine|\.|\b)\.?$', '', v).strip().rstrip('.').strip()
    for form in DATE_FORMS:
        m = form.fullmatch(v)
        if not m:
            continue
        g = m.groupdict()
        year = g['year']
        month = None
        if g.get('word'):
            month = MONTH_OF[g['word'].lower()]
        elif g.get('month'):
            month = ROMAN_OF.get(g['month']) or int(g['month'])
        if month is not None and not 1 <= month <= 12:
            return value
        if month is None:
            return year
        days = g.get('day')
        if not days:
            return f'{month:02d}.{year}'
        parts = re.split(r'\s?([/–—-])\s?', days)
        nums = parts[::2]
        if any(not 0 <= int(d) <= DAYS_IN[month - 1] for d in nums):
            return value                            # "31. 4.": a misprint, as printed
        if all(int(d) == 0 for d in nums):
            return f'{month:02d}.{year}'            # "00. 03. 1944": the day isn't known
        sep = '/' if '/' in days else '-'
        return f"{sep.join(f'{int(d):02d}' for d in nums)}.{month:02d}.{year}"
    return value


def death_date(s: dict) -> dict | None:
    v = s.get('death_date')
    if not v:
        return None
    new = date_form(v)
    return {'death_date': new} if new != v else None


# ── albanian: the census's word ─────────────────────────────────────────────
ETHNICITY = {'Šiptar': 'Albanac', 'Šiptarka': 'Albanka', 'šiptar': 'Albanac', 'šiptarka': 'Albanka',
             'Siptar': 'Albanac', 'Siptarka': 'Albanka'}


def albanian(s: dict) -> dict | None:
    new = ETHNICITY.get(s.get('ethnicity') or '')
    return {'ethnicity': new} if new else None


RULES = [
    ('captured', captured),
    ('after_war', after_war),
    ('death_date', death_date),
    ('albanian', albanian),
]
# the rules that change only a field's form: they apply to a field corrections set too
FORM_ONLY = {'after_war', 'death_date', 'albanian'}


def standard(field: str, value):
    """one field's value as the rules would leave it (extract_structured_fields.forget_stale compares by it)"""
    if field == 'death_date' and value:
        return None if AFTER_WAR.fullmatch(value.strip()) else date_form(value)
    if field == 'ethnicity' and value:
        return ETHNICITY.get(value, value)
    return value


def apply(soldiers: list[dict], manual: dict | None = None, only: str | None = None, samples: dict | None = None) -> collections.Counter:
    """run the rules on a unit's records in place; manual: soldier_id -> the fields corrections set"""
    done = collections.Counter()
    for s in soldiers:
        kept = (manual or {}).get(s.get('soldier_id'), ())
        for name, rule in RULES:
            if only and name != only:
                continue
            change = rule(s)
            if not change or (name not in FORM_ONLY and set(change) & set(kept)):
                continue
            before = {k: s.get(k) for k in change}
            for k, v in change.items():
                if v is None:
                    s.pop(k, None)
                else:
                    s[k] = v
            done[name] += 1
            if samples is not None and len(samples.setdefault(name, [])) < samples.get('_n', 5):
                samples[name].append((s['soldier_id'], before, change))
    return done


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    from name_utils import BRIGADE_CONFIGS          # noqa: E402
    from cleanup_text_fields import live_json_files  # noqa: E402
    import apply_corrections                         # noqa: E402

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--brigade', type=int)
    ap.add_argument('--rule', choices=[n for n, _ in RULES])
    ap.add_argument('--sample', type=int, default=4)
    args = ap.parse_args()
    manual = {}
    for c in apply_corrections.load_corrections(ROOT / 'corrections.json'):
        got = set(c.get('fields', {})) | set(c.get('record', {}))
        if got:
            manual.setdefault(c.get('new_id') or c['soldier_id'], set()).update(got)
    live, total = live_json_files(), collections.Counter()
    samples: dict = {'_n': args.sample}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if (args.brigade and code != args.brigade) or cfg['json_file'] not in live:
            continue
        path = ROOT / 'website' / 'public' / cfg['json_file']
        text = path.read_text(encoding='utf-8')
        soldiers = json.loads(text)
        done = apply(soldiers, manual, args.rule, samples)
        if not done:
            continue
        total.update(done)
        print(f"{code:4} {cfg['json_file']}: {dict(done)}")
        if args.apply:
            path.write_text(json.dumps(soldiers, ensure_ascii=False, indent=2), encoding='utf-8')
    for name, rows in samples.items():
        if name == '_n':
            continue
        print(f'\n{name}:')
        for sid, before, change in rows:
            print(f'   {sid}  {before} -> {change}')
    print(f'\ntotal {dict(total)}' + ('' if args.apply else ' (dry run)'))


if __name__ == '__main__':
    main()
