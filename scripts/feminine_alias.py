"""A woman's nickname is "zvana X", not "zvani X".

Parsers and corrections open a bio with the nickname clause ("zvani Radica; 1922, ...", after "majka X; " in
1. šumadijska). apply_corrections.py runs apply() on every unit after the corrections, so the rule holds whatever
wrote the bio. A record is a woman's when its bio uses more feminine forms (rođena, poginula, Srpkinja,
bolničarka, ...) than masculine ones; a bio that says neither, or as much of both, is decided by the given name:
the names the other bios show to be women's or men's, else a rare name ending in -a is a woman's.
"""
import re
from collections import Counter

FEM = re.compile(
    r'\b(rođena|rodjena|poginula|umrla|stupila|ranjena|nestala|streljana|ubijena|zarobljena|internirana|'
    r'demobilisana|demobilizirana|penzionisana|umirovljena|bila|živjela|živela|radila|padla|ubita|obešena|'
    r'obješena|borkinja|bolničarka|srpkinja|hrvatica|crnogorka|slovenka|muslimanka|jevrejka|židovka|makedonka|'
    r'ruskinja|italijanka|mađarica|slovakinja|učenica|domaćica|radnica|krojačica|studentkinja|kuharica|kuvarica|'
    r'sekretarka|komesarka|referentkinja|delegatkinja|desetarka|službenica|učiteljica|seljanka|zemljoradnica|'
    r'tkalja|švalja|partizanka|omladinka|skojevka|članica)\b', re.I)
# men's forms only: "borac", "referent", "komesar", "član" are said of women too
MASC = re.compile(
    r'\b(rođen|rodjen|poginuo|umro|stupio|nestao|streljan|ubijen|zarobljen|interniran|demobilisan|bio|živio|'
    r'živeo|radio|padel|umrl|ubit|srbin|hrvat|crnogorac|slovenac|musliman|jevrej|židov|makedonac|rus|italijan|'
    r'mađar|slovak|učenik|zemljoradnik|radnik|krojač|kuhar|kuvar|službenik|učitelj|seljak|tkač|kovač|stolar|'
    r'obućar|pekar|zidar|mesar|bravar|mehaničar|trgovac|omladinac|skojevac)\b', re.I)
# a married or maiden name, as the Slovene lists print it: "por. Ciglar", "ud. Zupan", "roj. Kos;" (a note: in
# "roj. 1915 Podgrad" or "roj. Sodražica, padel ..." the word is "rojen", born)
MAIDEN = re.compile(r'(?:^|;)\s*(?:(?:por|ud)\. [A-ZČĆŽŠĐ]|roj\. [A-ZČĆŽŠĐ][^\s;,\d]*;)')
# men's names ending in -a too rare in the data to be learned from it
MALE_A = {'Nikola', 'Luka', 'Ilija', 'Andrija', 'Sava', 'Jovica', 'Mića', 'Pera', 'Mika', 'Jaka', 'Miha', 'Saša',
          'Ljuba', 'Toma', 'Kosta', 'Vuka', 'Joža', 'Jura', 'Đura', 'Gligorija', 'Zaharija', 'Jeremija', 'Zosima',
          'Avdija', 'Hamza', 'Musa', 'Isa', 'Alija', 'Mitja'}
# Slovene men's names in -a, never women's, whatever other units' bios suggest
MALE_ALWAYS = {'Jaka', 'Miha', 'Mitja'}
WOMEN = {'0007001569',      # Filipi-Vedrina Dolores: her bio's forms are even, her name ends in -s
         '0004000242',      # Boštjančič Mija - Olga (Ljubljanska): Mija is a Slovene woman's name, a man's in the
                            # units from Serbia and Vojvodina, whose bios teach it as one
         '0048014036'}      # Štrbac Pantelije Lelija (7. krajiška): "rođena ... Srpkinja, domaćica"; the bios teach
                            # Lelija as a man's name
MEN = {'0009001168'}         # Stotjanović "Nilkola" (OCR for Nikola)

ALIAS = re.compile(r'(^|; )zvani(?= )')
_names = None


def _text(s: dict) -> str:
    t = ' '.join([s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources', ())])
    return re.sub(r'(^|; )(?:majka|otac|zvan[ai]|ili) [^;]*;', ' ', t)   # nicknames and parents say nothing of the soldier


def _marks(s: dict) -> tuple[int, int]:
    t = _text(s)
    return len(FEM.findall(t)) + len(MAIDEN.findall(t)), len(MASC.findall(t))


def name_genders(soldiers) -> tuple[set, set]:
    """Given names that the bios saying only one gender show to be women's, and men's (at least 2, 4 to 1)."""
    f, m = Counter(), Counter()
    for s in soldiers:
        fs, ms = _marks(s)
        if fs and not ms:
            f[s.get('first_name') or ''] += 1
        elif ms and not fs:
            m[s.get('first_name') or ''] += 1
    return ({n for n in f if f[n] >= 2 and f[n] >= 4 * m[n]},
            {n for n in m if m[n] >= 2 and m[n] >= 4 * f[n]})


# A nationality in its feminine form in the record's own field, with a given name that may be a woman's: a woman, whatever
# the bios' other words count ("Rođena ... Crnogorka" whose bio tells of her father; 2026-10-30). Not the masculine
# form: books print "Hrvat" for a woman (the Mosor odred)
FEMININE_NATIONALITY = {
    'Srpkinja', 'Hrvatica', 'Crnogorka', 'Slovenka', 'Muslimanka', 'Makedonka', 'Jevrejka', 'Židovka', 'Mađarica',
    'Slovakinja', 'Čehinja', 'Poljakinja', 'Ruskinja', 'Rusinka', 'Ukrajinka', 'Italijanka', 'Talijanka', 'Turkinja',
    'Rumunka', 'Romkinja', 'Albanka', 'Nemica', 'Njemica', 'Bugarka', 'Grkinja', 'Austrijanka', 'Jugoslovenka',
    'Jugoslavenka'}


def is_woman(s: dict, women: set, men: set) -> bool:
    if s['soldier_id'] in WOMEN or s['soldier_id'] in MEN:
        return s['soldier_id'] in WOMEN
    name = s.get('first_name') or ''
    if s.get('ethnicity') in FEMININE_NATIONALITY and name not in men and name not in MALE_A and name not in MALE_ALWAYS \
            and (name in women or name.endswith('a')):
        return True
    fs, ms = _marks(s)
    if fs != ms:
        return fs > ms
    name = s.get('first_name') or ''
    if name in MALE_ALWAYS:
        return False
    if name in women or name in men:
        return name in women
    return name.endswith('a') and name not in MALE_A


SITE_FILE = 'website/app/data/name-genders.json'


def site_genders(root) -> dict:
    """The site's name lists (SITE_FILE), for site_is_woman"""
    import json
    from pathlib import Path
    g = json.loads((Path(root) / SITE_FILE).read_text(encoding='utf-8'))
    return {'menA': set(g['menA']), 'women': set(g['women']), 'womenIds': set(g['womenIds']), 'menIds': set(g['menIds'])}


def site_is_woman(s: dict, g: dict) -> bool:
    """The site's isWoman (website/app/lib/standIn.ts), letter for letter: what the card says, "Rođena" or "Rođen"
    (standardize_fields.py gives the nationality the same form)"""
    if s['soldier_id'] in g['womenIds'] or s['soldier_id'] in g['menIds']:
        return s['soldier_id'] in g['womenIds']
    name = s.get('first_name') or ''
    named_woman = name not in g['menA'] and (name in g['women'] or name.endswith('a'))
    if s.get('ethnicity') in FEMININE_NATIONALITY and named_woman:
        return True
    fs, ms = _marks(s)
    if fs != ms:
        return fs > ms
    return named_woman


def write_site(names: tuple[set, set], root) -> bool:
    """The site's isWoman (website/app/lib/standIn.ts) reads the same rule: the men's names ending in -a and the
    women's names that don't, as is_woman() decides them, and the records set by hand. Returns whether it changed."""
    import json
    from pathlib import Path
    women, men = names
    data = {
        'menA': sorted(n for n in men | MALE_A | MALE_ALWAYS
                       if n.endswith('a') and (n in MALE_ALWAYS or n in men or n not in women)),
        'women': sorted(n for n in women if n and not n.endswith('a') and n not in MALE_ALWAYS),
        'womenIds': sorted(WOMEN),
        'menIds': sorted(MEN),
    }
    path = Path(root) / SITE_FILE
    text = json.dumps(data, ensure_ascii=False, indent=0) + '\n'
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return False
    path.write_text(text, encoding='utf-8')
    return True


def apply(soldiers: list[dict], names: tuple[set, set] | None = None) -> int:
    """Turn "zvani" into "zvana" in women's bios (and their merged entries), in place; returns how many changed.
    names: name_genders() of all units (default: of these soldiers only)."""
    women, men = names or name_genders(soldiers)
    changed = 0
    for s in soldiers:
        texts = [s] + list(s.get('other_sources', ()))
        if not any(ALIAS.search(t.get('additional_info') or '') for t in texts) or not is_woman(s, women, men):
            continue
        for t in texts:
            if t.get('additional_info'):
                t['additional_info'] = ALIAS.sub(r'\1zvana', t['additional_info'])
        changed += 1
    return changed
