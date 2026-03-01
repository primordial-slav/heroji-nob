"""
Extract soldier names from Treća Proleterska (Sandžačka) Brigada PDF.

Source: Žarko Vidović: TREĆA PROLETERSKA BRIGADA
Pages 375-446: "SPISAK BORACA I STAREŠINA NA DAN FORMIRANJA BRIGADE"

Format in PDF:
LASTNAME FIRSTNAME [NICKNAME] [*|•]
role, rođen YEAR, Birthplace, occupation; party membership. Fate info.

Example:
KNEŽEVIĆ VLADIMIR VOLOĐA *
komandant, rođen 1915, Vaškovo, Pljevlja, poručnik bivše jugoslovenske
vojske; član KPJ od 1941. Poginuo 2/3. oktobra 1942. kod Mrkonjić-Grada.
"""

import re
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pdfplumber'])
    import pdfplumber


# Source PDF
PDF_PATH = Path("E:/Projects/113-nasi-heroji/01-data/brigades/Treća Proleterska/Žarko_Vidović_TREĆA_PROLETERSKA_BRIGADA.pdf")

# Pages containing the soldier list (1-indexed)
START_PAGE = 376  # Page 375 is just the title, actual list starts on 376
END_PAGE = 446

# Output
OUTPUT_PATH = Path("website/public/treca-proleterska-soldiers.json")

# Brigade code for soldier IDs
BRIGADE_CODE = 5

# Section headers to skip (organizational units within the brigade)
SECTION_HEADERS = {
    'STAB BRIGADE', 'ŠTAB BRIGADE',
    'POLITODJEL BRIGADE', 'POL1TODJEL BRIGADE',
    'BRIGADNA INTENDANTURA', 'BRIGADNI SANITET',
    'ŠTAB BATALJONA', 'STAB BATALJONA',
    'BATALJONSKA INTENDANTURA', 'BATALJONSKA INTENDANTURA I SANITET',
    'BATALJONSKI SANITET',
    'PRATEĆA ČETA', 'PRATECA CETA',
}

# Patterns that indicate section/chapter headers (not soldier entries)
HEADER_PATTERNS = [
    r'^(PRVI|DRUGI|TREĆI|TREČI|ČETVRTI|PETI)\s+(BATALJON|ČETA)',
    r'^(STAB|ŠTAB)\s+(BRIGADE|BATALJONA)',
    r'^(POLITODJEL|POL1TODJEL)',
    r'^BRIGADN[AIO]',
    r'^BATALJONSK[AIO]',
    r'^PRATEĆ[AIO]',
    r'^\d+\.\s*(ČETA|CETA|VODA?)\b',  # "1. ČETA", "2. ČETA"
    r'^MINOBACAČK',  # MINOBACAČKI VOD etc.
    r'^MITRALJESK',  # MITRALJESKO ODELJENJE etc.
    r'^IZVIĐAČK',
    r'^SPOJNIČK',
    r'^BOMBAŠ',
    r'^NERASPOREĐEN',  # "NERASPOREĐENI PRI INTENDANTURI"
    r'^MILEŠEVSK',  # "MILEŠEVSKA (PRIJEPOLJSKA) ČETA"
    r'^BJELOPOLJSK',  # "BJELOPOLJSKA ČETA"
    r'^NOP\b',  # "NOP odreda"
    r'^NAPOMENA\b',
    r'^SPISAK\s+BORACA',
    r'^NA DAN FORMIRANJA',
    r'^IZVORI\s+I\s+LITERATURA',
    r'^UKUPNO\s+\d',
    r'^Brojno\s+stanje',
    r'^NNAAZZIIVV',  # OCR garbled table header
    r'^U spisak boraca',
]

# Role keywords that mark the start of biographical info (not part of a name)
ROLE_KEYWORDS = [
    'komandant', 'komandir', 'komesar', 'politički', 'zamenik',
    'borac', 'vodnik', 'desetar', 'četni', 'bolničar', 'bolnička',
    'bolničarka',
    'intendant', 'referent', 'kurir', 'puškomitraljezac',
    'načelnik', 'pomoćnik', 'rukovodilac', 'član', 'sekretar',
    'ekonom', 'telefonist', 'izviđač', 'bombarder', 'mitraljezac',
    'trubač', 'obaveštajac', 'obavještajac', 'vođa',
    'rođen', 'rođena',
]


def extract_text_from_pdf(pdf_path, start_page, end_page):
    """Extract text from specified page range."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(start_page - 1, min(end_page, len(pdf.pages))):
            page_text = pdf.pages[i].extract_text()
            if page_text:
                pages_text.append(page_text)
    return '\n'.join(pages_text)


def fix_ocr_artifacts(text):
    """Fix common OCR misreadings in the PDF."""
    # Fix common OCR substitutions in name lines:
    # '1' used as 'l' or 'I' in names like "PERUNlClC" → "PERUNIČIĆ"
    # '2' used as 'Ž' in names like "2IVOJIN" → "ŽIVOJIN"

    # Fix '2' at start of words that should be 'Ž'
    text = re.sub(r'\b2(?=[A-ZČĆŠĐA-z])', 'Ž', text)

    # Fix 'l' that should be 'I' in all-caps words (e.g., "POLlTODJEL" → "POLITODJEL")
    # Only in uppercase context
    def fix_l_in_caps(match):
        word = match.group(0)
        # If the word is mostly uppercase, replace lowercase 'l' with 'I'
        upper_count = sum(1 for c in word if c.isupper())
        if upper_count > len(word) * 0.5:
            return word.replace('l', 'I')
        return word

    text = re.sub(r'\b[A-ZČĆŽŠĐ][A-ZČĆŽŠĐa-zčćžšđ]*l[A-ZČĆŽŠĐa-zčćžšđ]*\b', fix_l_in_caps, text)

    return text


def is_section_header(line):
    """Check if a line is a section/organizational header, not a soldier entry."""
    line_clean = line.strip().rstrip('*•— ')

    # Exact match against known headers
    if line_clean.upper() in SECTION_HEADERS:
        return True

    # Regex pattern match
    for pattern in HEADER_PATTERNS:
        if re.match(pattern, line_clean, re.IGNORECASE):
            return True

    return False


def is_new_soldier_entry(line):
    """
    Check if a line starts a new soldier entry.

    Soldier entries start with an ALL CAPS surname (2+ chars) followed by space.
    We also need to exclude section headers which are also in caps.
    """
    line = line.strip()
    if not line:
        return False

    # Must start with uppercase word of 2+ chars
    if not re.match(r'^[A-ZČĆŽŠĐ]{2,}[\s,]', line):
        return False

    # Exclude section headers
    if is_section_header(line):
        return False

    # Exclude page numbers (just digits)
    if re.match(r'^\d+$', line.strip()):
        return False

    return True


def parse_soldier_entry(entry):
    """
    Parse a single soldier entry.

    Format: LASTNAME FIRSTNAME [NICKNAME] [*•]
    role, rođen YEAR, Birthplace, occupation; party info. Fate.

    The name is on the first line, and the bio/role starts on the next line
    or after a comma.
    """
    entry = entry.strip()
    if not entry:
        return None

    name_part = entry
    additional_info = ""

    # Strategy 1: Split at newline followed by role keyword
    # This is the most common case: name on first line, role on next
    for keyword in ROLE_KEYWORDS:
        pattern = r'\n\s*' + re.escape(keyword) + r'\b'
        match = re.search(pattern, entry, re.IGNORECASE)
        if match:
            name_part = entry[:match.start()].strip()
            additional_info = entry[match.start():].strip()
            break

    # Strategy 2: If name is on same line, split at comma + role keyword
    if not additional_info:
        for keyword in ROLE_KEYWORDS:
            pattern = r',\s*' + re.escape(keyword) + r'\b'
            match = re.search(pattern, entry, re.IGNORECASE)
            if match:
                name_part = entry[:match.start()].strip()
                additional_info = entry[match.start() + 1:].strip()
                break

    # Strategy 3: Split at first occurrence of "rođen" anywhere
    if not additional_info:
        match = re.search(r'\b(rođen[a]?)\s+\d{4}', entry, re.IGNORECASE)
        if match:
            # Walk back to find where the role text starts before rođen
            before = entry[:match.start()].rstrip(' ,;')
            # Find the last comma or newline before rođen
            last_sep = max(before.rfind(','), before.rfind('\n'))
            if last_sep > 0:
                name_part = entry[:last_sep].strip()
                additional_info = entry[last_sep + 1:].strip()
            else:
                name_part = before.strip()
                additional_info = entry[match.start():].strip()

    # Clean up the name part - remove fate markers
    name_part = re.sub(r'[*•—~\-]+\s*$', '', name_part).strip()
    name_part = re.sub(r'\s+[*•—~\-]+\s*', ' ', name_part).strip()

    # Parse the name: LASTNAME FIRSTNAME [NICKNAME]
    # Everything after the initial caps word(s) is first name / nickname
    name_words = name_part.split()
    if not name_words:
        return None

    last_name = ""
    first_name = ""

    # Collect last name parts (consecutive uppercase words at start)
    i = 0
    while i < len(name_words):
        word = name_words[i]
        # Check if word is all caps (allowing for OCR artifacts like "1" in place of "I")
        clean_word = re.sub(r'[^A-ZČĆŽŠĐa-zčćžšđ]', '', word)
        if clean_word and clean_word.isupper():
            if last_name:
                last_name += " "
            last_name += word
            i += 1
        else:
            break

    # Rest is first name (and possibly nickname)
    remaining = name_words[i:]
    if remaining:
        first_name = ' '.join(remaining)

    # If we got no first name but have multiple uppercase "words",
    # the last one might be the first name
    if not first_name and ' ' in last_name:
        parts = last_name.rsplit(' ', 1)
        last_name = parts[0]
        first_name = parts[1]

    if not last_name:
        return None

    # Clean additional info - normalize whitespace
    additional_info = ' '.join(additional_info.split())

    # Extract birth year
    birth_year = ""
    birth_match = re.search(r'rođen[a]?\s+(\d{4})', additional_info)
    if birth_match:
        birth_year = birth_match.group(1)

    return {
        'last_name': last_name,
        'middle_name': '',  # This source doesn't include father's name
        'first_name': first_name,
        'birth_year': birth_year,
        'additional_info': additional_info,
    }


def extract_soldiers_from_text(text):
    """Extract soldier entries from the PDF text."""
    soldiers = []
    lines = text.split('\n')
    current_entry = ""

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip standalone page numbers
        if re.match(r'^\d{1,3}$', line):
            continue

        # Stop at NAPOMENA section (end of soldier list)
        if line.startswith('NAPOMENA'):
            break

        # Stop at summary table
        if 'Brojno stanje' in line or 'UKUPNO' in line:
            break

        # Check if this starts a new soldier entry
        if is_new_soldier_entry(line):
            # Save previous entry
            if current_entry:
                parsed = parse_soldier_entry(current_entry)
                if parsed and parsed['last_name']:
                    soldiers.append(parsed)
            current_entry = line
        elif is_section_header(line):
            # Save previous entry and skip header
            if current_entry:
                parsed = parse_soldier_entry(current_entry)
                if parsed and parsed['last_name']:
                    soldiers.append(parsed)
            current_entry = ""
        else:
            # Continue previous entry
            if current_entry:
                current_entry += "\n" + line

    # Don't forget the last entry
    if current_entry:
        parsed = parse_soldier_entry(current_entry)
        if parsed and parsed['last_name']:
            soldiers.append(parsed)

    return soldiers


def post_process_cleanup(soldiers):
    """Clean up common issues after extraction."""
    cleaned = []
    for s in soldiers:
        # Skip entries with no real last name (garbage entries)
        if not s['last_name'] or len(s['last_name'].strip()) < 2:
            continue

        # Skip entries where last_name looks like data rather than a name
        ln = s['last_name'].strip()
        if re.match(r'^\d', ln):
            continue
        if any(kw in ln.lower() for kw in ['ukupno', 'brojno', 'spisak', 'napomena']):
            continue

        # Skip entries that are clearly text fragments, not names
        # These have lowercase words, sentence fragments, or keywords as "last name"
        ln_lower = ln.lower()
        garbage_indicators = [
            'kpj', 'skoj', 'noo', 'nob', 'jna', 'ozn',  # abbreviations
            'od ', 'u ', 'na ', 'za ', 'iz ', 'do ', 'sa ',  # prepositions
            'član', 'borac', 'ranjen', 'radu', 'pri',  # role/info fragments
        ]
        if any(ln_lower.startswith(kw) for kw in garbage_indicators):
            continue

        # Skip entries where last_name contains lowercase-starting words
        # (real last names are always capitalized)
        if ln[0].islower():
            continue

        # Skip section sub-headers that look like names
        # e.g., "Na Radu Pri Stabu Brigade", "Ranjenici U Brigadnom Sanitetu"
        if not s['additional_info'] and not s['birth_year']:
            # No bio info at all — likely a header or fragment
            # Check if it has too many words for a name (names are 1-3 words)
            if len(ln.split()) > 3:
                continue
            # Check if first_name also looks like a header
            fn = s['first_name'].strip()
            if fn and len(fn.split()) > 3:
                continue

        # Fix hyphenated words from PDF line breaks in additional_info
        # e.g., "jugoslo- venske" → "jugoslovenske"
        if s['additional_info']:
            s['additional_info'] = re.sub(r'(\w)- (\w)', r'\1\2', s['additional_info'])

        # Fix "Vic" that should be "vić" (OCR space in surname)
        # Common OCR issue: "KUJO VIC" → "KUJOVIC", "MARKO VIC" → "MARKOVIC"
        # Also handles: "SA VIC" → "SAVIC", "CA VIC" → "CAVIC"
        s['last_name'] = re.sub(r'\s+Vic$', 'vić', s['last_name'], flags=re.IGNORECASE)
        s['last_name'] = re.sub(r'\s+VIC$', 'VIĆ', s['last_name'])
        # Handle cases like "Nes Toro Vic" → "Nestorović"
        if re.search(r'\s+Vic$', s['last_name'], re.IGNORECASE):
            s['last_name'] = re.sub(r'\s+Vic$', 'vić', s['last_name'], re.IGNORECASE)
        # Fix multi-space splits: "Gomilano Vic" → "Gomilanović"
        s['last_name'] = re.sub(r'(\w)\s+(\w)\s+Vic$', r'\1\2vić', s['last_name'], flags=re.IGNORECASE)

        # Fix first_name too (but only the "Vic" part, not trailing text)
        s['first_name'] = re.sub(r'\s+Vic\b', 'vić', s['first_name'], flags=re.IGNORECASE)

        # Clean role/rank text that leaked into first_name
        # e.g., "Stevan* vođa 2. mitraljeskog odeljenja" → "Stevan"
        if s['first_name']:
            # Remove fate markers from first_name
            s['first_name'] = re.sub(r'[*•—~]+', '', s['first_name']).strip()
            # If first_name contains role keywords, move them to additional_info
            fn = s['first_name']
            for kw in ROLE_KEYWORDS:
                pos = fn.lower().find(kw)
                if pos > 0:
                    leaked = fn[pos:].strip()
                    s['first_name'] = fn[:pos].strip()
                    if s['additional_info']:
                        s['additional_info'] = leaked + ', ' + s['additional_info']
                    else:
                        s['additional_info'] = leaked
                    break

        # Fix other OCR space-splits in last names
        # "Nes Toro Vic" type issues - collapse internal spaces in what should be one word
        # Only do this for last_name when it has 3+ short parts
        ln_parts = s['last_name'].split()
        if len(ln_parts) >= 3 and all(len(p) <= 4 for p in ln_parts):
            s['last_name'] = ''.join(ln_parts)

        cleaned.append(s)

    return cleaned


def add_ids_and_fullnames(soldiers):
    """Add soldier IDs and full names."""
    for i, soldier in enumerate(soldiers, 1):
        soldier['soldier_id'] = f"{BRIGADE_CODE:04d}{i:06d}"
        # Build full_name
        parts = [soldier['last_name'], soldier['middle_name'], soldier['first_name']]
        soldier['full_name'] = ' '.join(p for p in parts if p).strip()
        # Convert father's name placeholder
        soldier['fathers_name'] = ''


def title_case_name(name):
    """Convert ALL CAPS name to Title Case, handling South Slavic chars."""
    if not name or not name.strip():
        return ''
    words = name.split()
    result = []
    for word in words:
        if len(word) <= 2:
            result.append(word)
        elif word.isupper():
            result.append(word[0].upper() + word[1:].lower())
        else:
            result.append(word)
    return ' '.join(result)


def normalize_names(soldiers):
    """Normalize name casing to Title Case."""
    for soldier in soldiers:
        soldier['last_name'] = title_case_name(soldier['last_name'])
        # First name is usually already mixed case in this source,
        # but normalize just in case
        soldier['first_name'] = title_case_name(soldier['first_name'])


def main():
    if not PDF_PATH.exists():
        print(f"Error: PDF not found at {PDF_PATH}")
        return

    print(f"Extracting text from pages {START_PAGE}-{END_PAGE}...")
    text = extract_text_from_pdf(PDF_PATH, START_PAGE, END_PAGE)

    print(f"Text length: {len(text)} characters")

    # Fix OCR artifacts
    text = fix_ocr_artifacts(text)

    print("Parsing soldier entries...")
    soldiers = extract_soldiers_from_text(text)
    print(f"Found {len(soldiers)} soldiers")

    # Post-process cleanup
    soldiers = post_process_cleanup(soldiers)
    print(f"After cleanup: {len(soldiers)} soldiers")

    # Normalize names
    normalize_names(soldiers)

    # Add IDs and full names
    add_ids_and_fullnames(soldiers)

    # Reorder fields for consistency
    ordered_soldiers = []
    for s in soldiers:
        ordered_soldiers.append({
            'soldier_id': s['soldier_id'],
            'last_name': s['last_name'],
            'middle_name': s['middle_name'],
            'first_name': s['first_name'],
            'additional_info': s['additional_info'],
            'fathers_name': s['fathers_name'],
            'full_name': s['full_name'],
            'birth_year': s['birth_year'],
        })

    # Save JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(ordered_soldiers, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_PATH}")

    # Show stats
    with_birth_year = sum(1 for s in ordered_soldiers if s['birth_year'])
    with_additional = sum(1 for s in ordered_soldiers if s['additional_info'])
    print(f"\nStats:")
    print(f"  Total soldiers: {len(ordered_soldiers)}")
    print(f"  With birth year: {with_birth_year}")
    print(f"  With additional info: {with_additional}")

    # Show first 10 entries
    print(f"\nFirst 10 entries:")
    for s in ordered_soldiers[:10]:
        print(f"  {s['soldier_id']}: {s['last_name']} {s['first_name']}"
              f" | born: {s['birth_year']}"
              f" | info: {s['additional_info'][:60]}...")

    # Show last 5 entries
    print(f"\nLast 5 entries:")
    for s in ordered_soldiers[-5:]:
        print(f"  {s['soldier_id']}: {s['last_name']} {s['first_name']}"
              f" | born: {s['birth_year']}"
              f" | info: {s['additional_info'][:60]}...")

    return ordered_soldiers


if __name__ == "__main__":
    main()
