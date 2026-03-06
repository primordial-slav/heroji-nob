"""
Parser for Treća Proleterska (Sandžačka) Brigada soldier data.

PDF format: Each soldier starts with ALL CAPS name (optionally ending with * or •),
followed by rank/bio info on subsequent lines.

Example:
    KNEŽEVIĆ VLADIMIR VOLOĐA *
    komandant, rođen 1915, Vaškovo, Pljevlja, ...
"""
import pdfplumber
import re
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Section headers to skip (also in ALL CAPS)
SECTION_HEADERS = {
    'STAB BRIGADE', 'ŠTAB BRIGADE',
    'POLITODJEL BRIGADE', 'POL1TODJEL BRIGADE',
    'BRIGADNA INTENDANTURA', 'BRIGADNI SANITET',
    'ŠTAB BATALJONA', 'STAB BATALJONA',
    'BATALJONSKA INTENDANTURA', 'BATALJONSKA INTENDANTURA I SANITET',
    'BATALJONSKI SANITET',
    'PRATEĆA ČETA', 'PRATECA CETA',
}

HEADER_PATTERNS = [
    r'^(PRVI|DRUGI|TREĆI|TREČI|ČETVRTI|PETI)\s+(BATALJON|ČETA)',
    r'^(STAB|ŠTAB)\s+(BRIGADE|BATALJONA)',
    r'^(POLITODJEL|POL1TODJEL)',
    r'^BRIGADN[AIO]',
    r'^BATALJONSK[AIO]',
    r'^PRATEĆ[AIO]',
    r'^\d+\.\s*(ČETA|CETA|VODA?)\b',
    r'^MINOBACAČK',
    r'^MITRALJESK',
    r'^IZVIĐAČK',
    r'^SPOJNIČK',
    r'^BOMBAŠ',
    r'^NERASPOREĐEN',
    r'^MILEŠEVSK',
    r'^BJELOPOLJSK',
    r'^NOP\b',
    r'^NAPOMENA\b',
    r'^SPISAK\s+BORACA',
    r'^NA DAN FORMIRANJA',
    r'^IZVORI\s+I\s+LITERATURA',
    r'^UKUPNO\s+\d',
    r'^Brojno\s+stanje',
    r'^NNAAZZIIVV',
    r'^U spisak boraca',
]


def is_section_header(text):
    """Check if a line is a section header (not a soldier name)."""
    text_clean = text.strip().rstrip('*•— ·')
    if text_clean.upper() in SECTION_HEADERS:
        return True
    for pattern in HEADER_PATTERNS:
        if re.match(pattern, text_clean, re.IGNORECASE):
            return True
    return False


def is_new_entry(line):
    """Check if a line starts a new soldier entry."""
    line = line.strip()
    if not line:
        return False

    # Skip section headers
    if is_section_header(line):
        return False

    # Pattern 1: ALL CAPS name followed by mixed-case first name
    # Examples: "KOVAČEVIĆ Marko", "APOSTOLOVIĆ M. Slobodan"
    pattern1 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+)*\s+([A-ZČĆŽŠĐ]\.?\s+)*[A-ZČĆŽŠĐ][a-zčćžšđ]'

    # Pattern 2: ALL CAPS names with optional middle initials, may end with * or •
    # Examples: "KNEŽEVIĆ VLADIMIR VOLOĐA *", "MAMUŠIN P. MIJO,"
    pattern2 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+\s+([A-ZČĆŽŠĐ]\.?\s+)*[A-ZČĆŽŠĐ]{2,}\*?(\s*[,*•·]|\s+[A-ZČĆŽŠĐ])'

    # Pattern 3: Names ending with * or • marker (strong boundary signal)
    # Examples: "GUJANIČIĆ BOGDAN*", "TANOVIĆ SLOBODANKA DANA*"
    pattern3 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ]{2,})+\s*[*•·]'

    # Pattern 4: ALL CAPS name followed by space then * or • (with space before marker)
    # Examples: "KNEŽEVIĆ VLADIMIR VOLOĐA *", "JAKIĆ VELIMIR •"
    pattern4 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ]{2,})+\s*$'

    # Pattern 5: OCR-corrupted ALL CAPS names (1-2 lowercase letters mixed in due to OCR errors)
    # Examples: "DROBNJAKOVie GLIGORIJE", "ZEKAVClC MILOJE", "CULAFiC VUK"
    # These are names that are "mostly uppercase" with OCR errors on diacritics
    pattern5 = r'^[A-ZČĆŽŠĐa-z][A-ZČĆŽŠĐa-z\-]{3,}\s+[A-ZČĆŽŠĐ]{2,}(\s*[*•·]|\s*,|\s+[A-ZČĆŽŠĐ]|\s*$)'

    if (bool(re.match(pattern1, line)) or
            bool(re.match(pattern2, line)) or
            bool(re.match(pattern3, line)) or
            bool(re.match(pattern4, line))):
        return True

    # For pattern5 (OCR names), require at least 70% uppercase in first word
    m5 = re.match(pattern5, line)
    if m5:
        first_word = line.split()[0]
        upper_count = sum(1 for c in first_word if c.isupper() or c in 'ČĆŽŠĐ')
        if upper_count / len(first_word) >= 0.7:
            return True

    return False


def parse_soldier_entry(entry_text):
    """Parse a soldier entry into structured data."""
    entry_text = entry_text.strip()
    if not entry_text:
        return None

    # Remove * and • markers from the name part
    # Split at first comma or at the boundary between name and description
    # The name is the ALL CAPS part at the beginning

    # Try to find where the description starts
    # Pattern: ALL CAPS name possibly with markers, then lowercase description
    lines = entry_text.split('\n')
    name_line = lines[0].strip().rstrip('*•· ')

    # The rest is additional info
    if len(lines) > 1:
        additional_info = ' '.join(l.strip() for l in lines[1:] if l.strip())
    else:
        # Try splitting on comma
        parts = name_line.split(',', 1)
        if len(parts) > 1:
            name_line = parts[0].strip()
            additional_info = parts[1].strip()
        else:
            additional_info = ''

    # Parse the name into components
    name_parts = name_line.split()

    if len(name_parts) == 0:
        return None
    elif len(name_parts) == 1:
        return {
            'last_name': name_parts[0],
            'middle_name': '',
            'first_name': '',
            'additional_info': additional_info
        }
    elif len(name_parts) == 2:
        return {
            'last_name': name_parts[0],
            'middle_name': '',
            'first_name': name_parts[1],
            'additional_info': additional_info
        }
    else:
        # Last name is first word, first name is last word(s), middle is in between
        return {
            'last_name': name_parts[0],
            'middle_name': ' '.join(name_parts[1:-1]),
            'first_name': name_parts[-1],
            'additional_info': additional_info
        }


def extract_text_from_pdf(pdf_path, start_page=376, end_page=446):
    """Extract text from specific page range of the PDF."""
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        print(f"PDF has {total} pages, extracting {start_page}-{end_page}")
        for i in range(start_page - 1, min(end_page, total)):
            text = pdf.pages[i].extract_text()
            if text:
                all_text.append(f"--- PAGE {i+1} ---")
                all_text.append(text)
    return '\n'.join(all_text)


def clean_line(line):
    """Clean OCR artifacts and leading punctuation from a line."""
    # Strip leading symbols: - ^ • · " and whitespace
    cleaned = re.sub(r'^[\-\^•·\"]+\s*', '', line.strip())
    return cleaned


def parse_soldiers_from_text(text):
    """Parse soldier entries from extracted text."""
    lines = text.split('\n')
    soldiers = []
    current_entry_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines, page markers, page numbers
        if not stripped or stripped.startswith('---'):
            continue
        if re.match(r'^\d{1,3}$', stripped):
            continue

        # Stop at certain markers
        if stripped.startswith('NAPOMENA') or 'Brojno stanje' in stripped or 'UKUPNO' in stripped:
            continue
        if stripped.startswith('IZVORI I LITERATURA') or stripped.startswith('U spisak boraca'):
            continue

        # Clean line (strip leading punctuation like - ^ before names)
        cleaned = clean_line(stripped)

        # Check if this is a new soldier entry
        if is_new_entry(cleaned):
            # Save previous entry
            if current_entry_lines:
                entry_text = '\n'.join(current_entry_lines)
                soldier = parse_soldier_entry(entry_text)
                if soldier:
                    soldiers.append(soldier)

            current_entry_lines = [cleaned]
        elif is_section_header(cleaned):
            # Save previous entry before header
            if current_entry_lines:
                entry_text = '\n'.join(current_entry_lines)
                soldier = parse_soldier_entry(entry_text)
                if soldier:
                    soldiers.append(soldier)
                current_entry_lines = []
        else:
            # Continuation line
            if current_entry_lines:
                current_entry_lines.append(stripped)

    # Don't forget the last entry
    if current_entry_lines:
        entry_text = '\n'.join(current_entry_lines)
        soldier = parse_soldier_entry(entry_text)
        if soldier:
            soldiers.append(soldier)

    return soldiers


def main():
    pdf_path = '../website/public/pdfs/treca-proleterska-brigada.pdf'

    if not os.path.exists(pdf_path):
        # Try alternate location
        pdf_path = 'website/public/pdfs/treca-proleterska-brigada.pdf'
        if not os.path.exists(pdf_path):
            print(f"Error: PDF not found!")
            return

    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    # Save extracted text
    os.makedirs('../01-data/processed', exist_ok=True)
    text_path = '../01-data/processed/treca_proleterska_extracted.txt'
    try:
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Saved extracted text to {text_path}")
    except Exception:
        pass

    print("\nParsing soldier entries...")
    soldiers = parse_soldiers_from_text(text)
    print(f"Found {len(soldiers)} soldier entries")

    # Check for long entries (likely still merged)
    long_entries = [s for s in soldiers if len(s.get('additional_info', '')) > 250]
    print(f"Entries with additional_info > 250 chars: {len(long_entries)}")

    # Save to JSON
    json_path = '../01-data/processed/treca_proleterska_soldiers.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to {json_path}")

    # Print sample entries
    print("\nSample entries (first 5):")
    for i, soldier in enumerate(soldiers[:5], 1):
        name = f"{soldier['last_name']} {soldier['middle_name']} {soldier['first_name']}".strip()
        info = soldier['additional_info'][:80] if soldier['additional_info'] else "(no info)"
        print(f"  {i}. {name}")
        print(f"     {info}")


if __name__ == '__main__':
    main()
