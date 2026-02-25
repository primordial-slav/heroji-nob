"""
Unified name normalization, parsing, and validation utilities.

Handles South Slavic naming conventions across Serbian, Croatian,
Slovenian, Bosnian, Montenegrin, and foreign names (Italian, Russian).

Usage:
    from name_utils import normalize_soldier, validate_soldier

    record = normalize_soldier(raw_record, brigade_code=1)
    issues = validate_soldier(record)
"""

import re


# ─────────────────────────────────────────────
# BRIGADE CONFIGURATION
# ─────────────────────────────────────────────

BRIGADE_CONFIGS = {
    1: {
        'name': 'Prva Proleterska',
        'json_file': 'prva-proleterska-soldiers.json',
        'language': 'sr',
        'name_format': 'merged',  # first_name often contains "FirstName FATHERSNAME"
        'has_fathers_name': True,
        'fathers_name_form': 'genitive',
        'original_casing': 'upper_last',
    },
    2: {
        'name': 'Prva Lička Proleterska',
        'json_file': 'soldiers.json',
        'language': 'sr',
        'name_format': 'standard',  # LAST middle FIRST, additional
        'has_fathers_name': True,
        'fathers_name_form': 'genitive',
        'original_casing': 'upper_last',
    },
    3: {
        'name': 'Druga Lička Proleterska',
        'json_file': 'druga-licka-soldiers.json',
        'language': 'sr',
        'name_format': 'standard',
        'has_fathers_name': True,
        'fathers_name_form': 'genitive',
        'original_casing': 'upper_all',
    },
    4: {
        'name': 'Ljubljanska (10. SNOUB)',
        'json_file': 'ljubljanska-soldiers.json',
        'language': 'sl',
        'name_format': 'slovenian',  # Lastname Firstname, year, place
        'has_fathers_name': False,
        'fathers_name_form': None,
        'original_casing': 'title',
    },
}


# ─────────────────────────────────────────────
# GENITIVE → NOMINATIVE CONVERSION
# ─────────────────────────────────────────────

# Known conversions (genitive → nominative)
# Covers the most common South Slavic father's name patterns
GENITIVE_TO_NOMINATIVE = {
    # -a endings (most common genitive)
    'Lazara': 'Lazar',
    'Milorada': 'Milorad',
    'Petra': 'Petar',
    'Dmitra': 'Dmitar',
    'Marka': 'Marko',
    'Jovana': 'Jovan',
    'Milana': 'Milan',
    'Bogoljuba': 'Bogoljub',
    'Vojislava': 'Vojislav',
    'Stevana': 'Stevan',
    'Dragana': 'Dragan',
    'Dušana': 'Dušan',
    'Svetozara': 'Svetozar',
    'Bogdana': 'Bogdan',
    'Radovana': 'Radovan',
    'Živana': 'Živan',
    'Mihajla': 'Mihajlo',
    'Todora': 'Todor',
    'Nikole': 'Nikola',
    'Đorđa': 'Đorđe',
    'Luke': 'Luka',
    'Đure': 'Đuro',
    'Ilije': 'Ilija',
    'Andrije': 'Andrija',
    'Matije': 'Matija',
    'Save': 'Sava',
    'Koste': 'Kosta',
    'Voje': 'Voja',
    'Josipa': 'Josip',
    'Jakova': 'Jakov',
    'Ivana': 'Ivan',
    'Stojana': 'Stojan',
    'Miloja': 'Miloje',
    'Radoja': 'Radoje',
    'Slavka': 'Slavko',
    'Branka': 'Branko',
    'Marka': 'Marko',
    'Danka': 'Danko',
    'Ranka': 'Ranko',
    'Zdravka': 'Zdravko',
    'Mirka': 'Mirko',
    'Željka': 'Željko',
    'Rajka': 'Rajko',
    'Darka': 'Darko',
    'Milka': 'Milko',
    'Stanka': 'Stanko',
    'Blagoja': 'Blagoje',
    'Mileta': 'Milet',
    'Aleksandra': 'Aleksandar',
    'Vladimira': 'Vladimir',
    'Rada': 'Rade',
    'Vlade': 'Vlada',
    'Mitra': 'Mitar',
    'Sime': 'Sima',
    'Milije': 'Milija',
    'Tome': 'Toma',
    'Pante': 'Panta',
    'Obrada': 'Obrad',
    'Života': 'Život',
    'Vukašina': 'Vukašin',
    'Veselina': 'Veselin',
    'Ljubomira': 'Ljubomir',
    'Momčila': 'Momčilo',
    'Dragoljuba': 'Dragoljub',
    'Milovana': 'Milovan',
    'Mihaila': 'Mihailo',
    'Stanoja': 'Stanoje',
    'Miladina': 'Miladin',
    'Milisava': 'Milisav',
    'Velimira': 'Velimir',
    'Borivoja': 'Borivoje',
    'Dobrivoja': 'Dobrivoje',
    'Ljubivoja': 'Ljubivoje',
    'Milivoja': 'Milivoje',
    'Časlava': 'Časlav',
    'Tomislava': 'Tomislav',
    'Miroslava': 'Miroslav',
    'Borislava': 'Borislav',
    'Stanislava': 'Stanislav',
    'Vladislava': 'Vladislav',
    'Vidoja': 'Vidoje',
    'Sredoja': 'Sredoje',

    # -ov/-ev possessive endings (patronymic form)
    'Živanov': 'Živan',
    'Petrov': 'Petar',
    'Radovanov': 'Radovan',
    'Markov': 'Marko',
    'Jovanov': 'Jovan',
    'Milanov': 'Milan',
    'Pavlov': 'Pavle',
    'Stevanov': 'Stevan',
    'Ivanov': 'Ivan',
    'Bogdanov': 'Bogdan',
    'Vasiljev': 'Vasilije',
    'Vasilijev': 'Vasilije',
    'Dušanov': 'Dušan',
    'Lazarev': 'Lazar',
    'Tošev': 'Toše',
    'Nikolajev': 'Nikolaj',
    'Stojanov': 'Stojan',
    'Todorov': 'Todor',

    # Muslim/Bosniak patronymic -ov forms
    'Alilov': 'Alija',
    'Hasanov': 'Hasan',
    'Huseinov': 'Husein',
    'Ibrahimov': 'Ibrahim',
    'Mehmedov': 'Mehmed',
    'Mustafin': 'Mustafa',
    'Omerov': 'Omer',
    'Sulejman': 'Sulejman',
    'Salkov': 'Salko',
    'Šaćirov': 'Šaćir',
    'Arelana': 'Arelan',

    # -in possessive endings (less common)
    'Nikin': 'Nika',
    'Lukin': 'Luka',
    'Ilijin': 'Ilija',
    'Jovankin': 'Jovanka',
    'Savkin': 'Savka',
}

# Build case-insensitive lookup
_GENITIVE_LOOKUP = {k.lower(): v for k, v in GENITIVE_TO_NOMINATIVE.items()}


def genitive_to_nominative(name):
    """
    Convert a father's name from genitive/possessive to nominative form.

    Tries exact dictionary match first, then applies rule-based conversion.

    Args:
        name: Father's name, possibly in genitive case

    Returns:
        Name in nominative form (best guess), or original if no conversion found
    """
    if not name or not name.strip():
        return ''

    name = name.strip()

    # Dictionary lookup (case-insensitive)
    nominative = _GENITIVE_LOOKUP.get(name.lower())
    if nominative:
        # Preserve original capitalization style
        if name[0].isupper():
            return nominative[0].upper() + nominative[1:]
        return nominative

    # Rule-based fallbacks are INTENTIONALLY conservative.
    # It's better to keep a genitive form than to produce a wrong nominative.
    # Names not in the dictionary are returned as-is.
    # The dictionary should be expanded over time as new patterns are found.

    return name


# ─────────────────────────────────────────────
# NAME CLEANING & NORMALIZATION
# ─────────────────────────────────────────────

# South Slavic special characters for regex
_SC = 'čćžšđČĆŽŠĐ'

# Common Slavic name prefixes that should stay lowercase in title case
# (currently none - all Yugoslav names capitalize every word)


def to_title_case(name):
    """
    Convert a name to Title Case, handling South Slavic characters.

    - ALL CAPS → Title Case (KOVAČEVIĆ → Kovačević)
    - Already title/mixed → preserved
    - Single letters/initials → preserved (M. stays M.)
    - Handles đ/Đ correctly

    Args:
        name: Name string in any casing

    Returns:
        Name in Title Case
    """
    if not name or not name.strip():
        return ''

    name = name.strip()

    # Don't touch single characters or initials
    if len(name) <= 2:
        return name

    # If not all caps, assume it's already in correct form
    # (preserves "de Groot", "von Braun" if they exist)
    if not name.isupper():
        return name

    # Convert each word to Title Case
    words = name.split()
    result = []
    for word in words:
        if len(word) <= 2:
            # Keep initials as-is (M. stays M.)
            result.append(word)
        else:
            # Standard title case - first letter upper, rest lower
            result.append(word[0].upper() + word[1:].lower())
    return ' '.join(result)


def clean_name_field(name):
    """
    Clean a name field: remove artifacts, trailing punctuation, years, etc.

    Args:
        name: Raw name string

    Returns:
        Cleaned name string
    """
    if not name or name.strip() in ('', 'nan', 'None'):
        return ''

    name = name.strip()

    # Remove parenthetical content (partisan aliases etc.)
    # e.g., "(Adola)" → remove
    name = re.sub(r'\([^)]*\)', '', name).strip()

    # Remove trailing punctuation (periods, commas)
    name = name.rstrip('.,;:').strip()

    # Remove years that leaked into names
    name = re.sub(r'\b(18|19)\d{2}\b\.?', '', name).strip()

    # Remove text after "rođen" that leaked into name fields
    for keyword in ['rođen', 'rođena', 'poginuo', 'poginula', 'umro', 'umrla',
                     'nestao', 'nestala', 'streljan', 'padel', 'padla',
                     'borac', 'vodnik', 'komandir']:
        pos = name.lower().find(keyword)
        if pos != -1:
            name = name[:pos].strip()

    # Remove trailing punctuation again after keyword removal
    name = name.rstrip('.,;:').strip()

    # Collapse multiple spaces
    name = ' '.join(name.split())

    return name


def split_merged_first_name(first_name, middle_name=''):
    """
    Split a first_name field that contains both first name and father's name.

    Common in Prva Proleterska where parsing produced:
        first_name = "Vittorio SALVATORE"  (FirstName FATHERSNAME)
        first_name = "Alilov DEMIR"        (FathersName FIRSTNAME)

    Detection logic:
    - If there are 2+ words and one is ALL CAPS while another isn't,
      the ALL CAPS word is likely the father's name or first name
    - In Yugoslav convention: "FathersGenitive FIRSTNAME" or "FirstName FATHERSNAME"

    Args:
        first_name: The raw first_name field
        middle_name: Existing middle_name (won't overwrite if present)

    Returns:
        (cleaned_first_name, fathers_name)
    """
    if not first_name:
        return '', middle_name

    parts = first_name.split()

    # Only try to split if there are exactly 2 parts (most common case)
    # and one is all caps while the other isn't
    if len(parts) == 2:
        p0_upper = parts[0].isupper() and len(parts[0]) > 1
        p1_upper = parts[1].isupper() and len(parts[1]) > 1
        p0_mixed = parts[0][0].isupper() and not parts[0].isupper() and len(parts[0]) > 1
        p1_mixed = parts[1][0].isupper() and not parts[1].isupper() and len(parts[1]) > 1

        if p0_mixed and p1_upper:
            # Pattern: "Vittorio SALVATORE" → first=Vittorio, father=SALVATORE
            # or: "Alilov DEMIR" → father=Alilov, first=DEMIR
            # In Yugoslav lists, the CAPS word at end is often the FIRST name
            # and the mixed-case word before it is the father's name
            # But for Italian/foreign names, pattern is different.
            # Convention in Prva Proleterska: FathersName FIRSTNAME
            fathers = parts[0] if not middle_name else middle_name
            first = parts[1]
            return first, fathers

        elif p0_upper and p1_mixed:
            # Pattern: "MARKO Petrov" → first=MARKO, father=Petrov
            first = parts[0]
            fathers = parts[1] if not middle_name else middle_name
            return first, fathers

        elif p0_upper and p1_upper:
            # Both caps: "MARKO PETAR" - can't determine, keep first as-is
            # Unless middle_name already set, just return as-is
            return first_name, middle_name

    # For 3+ parts, try to identify the split
    if len(parts) >= 3:
        # Look for pattern: mixed CAPS mixed... or mixed mixed CAPS
        caps_indices = [i for i, p in enumerate(parts) if p.isupper() and len(p) > 1]
        mixed_indices = [i for i, p in enumerate(parts)
                         if p[0].isupper() and not p.isupper() and len(p) > 1]

        if len(caps_indices) == 1 and caps_indices[0] == len(parts) - 1:
            # Last word is caps: "Alilov Ahmet DEMIR" → father=Alilov Ahmet, first=DEMIR
            first = parts[-1]
            fathers = ' '.join(parts[:-1]) if not middle_name else middle_name
            return first, fathers

    # Can't split confidently, return as-is
    return first_name, middle_name


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

# Known place names that sometimes end up in name fields
# (from the Ljubljana parsing bugs where column splitting went wrong)
_KNOWN_PLACES = {
    'ribnica', 'črnomelj', 'celje', 'maribor', 'kranj', 'kočevje',
    'ljubljana', 'novo mesto', 'trbovlje', 'ptuj', 'velenje', 'kamnik',
    'domžale', 'jesenice', 'škofja loka', 'krško', 'brežice', 'litija',
    'sevnica', 'trebnje', 'grosuplje', 'vrhnika', 'logatec', 'idrija',
    'tolmin', 'ajdovščina', 'ilirska bistrica', 'sežana', 'koper',
    'piran', 'izola', 'postojna',
}


def validate_soldier(record):
    """
    Validate a soldier record and return a list of detected issues.

    Args:
        record: Dict with soldier fields

    Returns:
        List of issue strings (empty = no issues)
    """
    issues = []
    ln = record.get('last_name', '') or ''
    fn = record.get('first_name', '') or ''
    mn = record.get('middle_name', '') or ''
    fathers = record.get('fathers_name', '') or ''

    # Missing names
    if not fn.strip():
        issues.append('missing_first_name')
    if not ln.strip():
        issues.append('missing_last_name')

    # Year leaked into name
    for field_name, val in [('last_name', ln), ('first_name', fn), ('middle_name', mn)]:
        if re.search(r'\b(18|19)\d{2}\b', val):
            issues.append(f'year_in_{field_name}')

    # Place name as surname (Ljubljanska parsing issue)
    if ln.lower().strip() in _KNOWN_PLACES:
        issues.append('place_as_last_name')

    # Merged names still in first_name (multiple words with CAPS)
    fn_parts = fn.split()
    if len(fn_parts) >= 2:
        caps_words = [p for p in fn_parts if p.isupper() and len(p) > 1]
        mixed_words = [p for p in fn_parts if p[0].isupper() and not p.isupper() and len(p) > 1]
        if caps_words and mixed_words:
            issues.append('merged_names_in_first')

    # Additional info leaked into name (keywords in name fields)
    for field_name, val in [('first_name', fn), ('last_name', ln)]:
        val_lower = val.lower()
        for kw in ['rođen', 'poginuo', 'umro', 'nestao', 'borac', 'bataljona']:
            if kw in val_lower:
                issues.append(f'info_leaked_into_{field_name}')
                break

    # Parentheses in name (usually partisan alias not stripped)
    for field_name, val in [('first_name', fn), ('last_name', ln), ('middle_name', mn)]:
        if '(' in val or ')' in val:
            issues.append(f'parentheses_in_{field_name}')

    # Single character name (probably initial, might be incomplete)
    if len(fn.strip()) == 1:
        issues.append('first_name_single_char')
    if len(ln.strip()) == 1:
        issues.append('last_name_single_char')

    return issues


# ─────────────────────────────────────────────
# MAIN NORMALIZATION
# ─────────────────────────────────────────────

def normalize_soldier(record, brigade_code):
    """
    Normalize a soldier record to standard format.

    Applies all cleaning, casing, name splitting, and genitive conversion.

    Args:
        record: Dict with raw soldier data (last_name, first_name, middle_name, etc.)
        brigade_code: Brigade code (1-4) to apply brigade-specific logic

    Returns:
        New dict with normalized fields (original record is not modified)
    """
    config = BRIGADE_CONFIGS.get(brigade_code, {})
    result = dict(record)  # shallow copy

    # --- Step 1: Clean all name fields ---
    last_name = clean_name_field(record.get('last_name', ''))
    first_name = clean_name_field(record.get('first_name', ''))
    middle_name = clean_name_field(record.get('middle_name', ''))

    # --- Step 2: Split merged first names (Prva Proleterska mainly) ---
    if config.get('name_format') == 'merged' or _has_merged_names(first_name):
        first_name, fathers_name = split_merged_first_name(first_name, middle_name)
        if fathers_name and not middle_name:
            middle_name = fathers_name
    else:
        fathers_name = middle_name

    # --- Step 3: Normalize casing → Title Case ---
    last_name = to_title_case(last_name)
    first_name = to_title_case(first_name)
    middle_name = to_title_case(middle_name)

    # --- Step 4: Convert genitive father's name to nominative ---
    fathers_name_nominative = ''
    if config.get('has_fathers_name') and middle_name:
        fathers_name_nominative = genitive_to_nominative(middle_name)
        if not fathers_name_nominative:
            fathers_name_nominative = middle_name

    # --- Step 5: Build result ---
    result['last_name'] = last_name
    result['first_name'] = first_name
    result['middle_name'] = middle_name  # keep original field (now title-cased)
    result['fathers_name'] = fathers_name_nominative  # new field: nominative form

    # Update full_name
    name_parts = [last_name, middle_name, first_name]
    result['full_name'] = ' '.join(p for p in name_parts if p).strip()

    return result


def _has_merged_names(first_name):
    """Check if a first_name field likely contains merged name components."""
    if not first_name:
        return False
    parts = first_name.split()
    if len(parts) < 2:
        return False
    has_caps = any(p.isupper() and len(p) > 1 for p in parts)
    has_mixed = any(p[0].isupper() and not p.isupper() and len(p) > 1 for p in parts)
    return has_caps and has_mixed


# ─────────────────────────────────────────────
# DATE EXTRACTION (consolidated from extract_dates.py)
# ─────────────────────────────────────────────

def extract_birth_info(additional_info):
    """
    Extract birth date/year from additional_info field.

    Only extracts BIRTH dates (from start of text).
    Ignores death-related dates.

    Args:
        additional_info: The additional_info field text

    Returns:
        (date_string, birth_year) tuple - both strings, may be empty
    """
    if not additional_info or not additional_info.strip():
        return '', ''

    info = additional_info.strip()

    # Only look before death keywords
    death_keywords = ['poginuo', 'poginula', 'padel', 'padla',
                      'nestao', 'nestala', 'umro', 'umrla', 'umrl',
                      'streljan', 'streljena']
    first_death_pos = len(info)
    for keyword in death_keywords:
        pos = info.lower().find(keyword)
        if pos != -1 and pos < first_death_pos:
            first_death_pos = pos

    search_text = info[:first_death_pos]

    # Pattern 1: Full date DD. MM. YYYY
    match = re.match(r'^(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})', search_text)
    if match:
        date_str = match.group(1)
        year_match = re.search(r'\d{4}', date_str)
        year = year_match.group(0) if year_match else ''
        return date_str.strip(), year

    # Pattern 2: Year with period YYYY. Location
    match = re.match(r'^(\d{4})\.\s+\w', search_text)
    if match:
        year = match.group(1)
        return year, year

    # Pattern 3: Year with comma YYYY, Location (most common)
    match = re.match(r'^(\d{4}),', search_text)
    if match:
        year = match.group(1)
        return year, year

    # Pattern 4: Year with space YYYY Location
    match = re.match(r'^(\d{4})\s+[A-ZČĆŽŠĐ]', search_text)
    if match:
        year = match.group(1)
        return year, year

    # Pattern 5: "rođen(a) YYYY" embedded in text
    match = re.search(r'rođen[a]?\s+(\d{4})', search_text)
    if match:
        year = match.group(1)
        return year, year

    return '', ''


def extract_birthplace(additional_info, birth_year=''):
    """
    Extract birthplace from additional_info field.

    Looks for the location text after the birth year.

    Args:
        additional_info: The additional_info field text
        birth_year: The already-extracted birth year (to skip past it)

    Returns:
        Birthplace string, may be empty
    """
    if not additional_info or not additional_info.strip():
        return ''

    info = additional_info.strip()

    # Find position after birth year
    if birth_year:
        pos = info.find(birth_year)
        if pos != -1:
            after_year = info[pos + len(birth_year):].strip()
            # Skip past separator (., ,, space)
            after_year = after_year.lstrip('.,; ').strip()

            # Take text until next comma or keyword
            stop_keywords = ['u nob', 'borac', 'vodnik', 'komandir', 'četa',
                             'bataljon', 'poginuo', 'umro', 'nestao', 'padel',
                             'zemljoradnik', 'radnik', 'đak', 'učenik', 'student',
                             'kovač', 'zidar', 'stolar', 'mehaničar', 'službenik']
            place = after_year
            for kw in stop_keywords:
                kw_pos = place.lower().find(kw)
                if kw_pos != -1:
                    place = place[:kw_pos]
            # Also stop at comma followed by non-place text
            comma_pos = place.find(',')
            if comma_pos != -1:
                # Check if text after comma looks like continuation of place
                after_comma = place[comma_pos + 1:].strip()
                if after_comma and not after_comma[0].isupper():
                    place = place[:comma_pos]

            return place.strip().rstrip('.,;: ')

    return ''
