"""
Parser for 13. proleterska udarna brigada "Rade Končar" soldier data.

The PDF has a two-column layout with soldier entries in this format:
    LAST_NAME [Father's_genitive] FIRST_NAME [NICKNAME], year. Place, Municipality. [Death info]

Examples:
    ALEKSIĆ Velisava LEPOSAVA, 1927. Velika Ivanča, Mladenovac. Poginula februara 1945.
    ABRAHAM IVAN, rođen 1906 u selu Virje, općina Đurđevac. *
    ABRAM Jožeta ALOJZ, 1925. Artviže, Sežana.
    ALFIREVIĆ Mate MIROSLAV MIRO, 1922. Zaostrog, Makarska. Poginuo 6. XII 1944. kod Tovarnika.

Source PDF: znaci.org/00001/69_14.pdf (Part 3 of the monograph)
Total pages: 109, soldier list pages 4-109 (0-indexed: 3-108)
Two columns: left (x0 ~109-287), right (x0 ~296-472), split at x=290
"""
import pdfplumber
import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Page range for soldier list (1-indexed)
SOLDIER_START_PAGE = 4
SOLDIER_END_PAGE = 109

# Column boundary (midpoint between left max ~287 and right min ~296)
COL_BOUNDARY = 290


def is_soldier_entry(text):
    """Check if a line starts a new soldier entry.

    New entries start with an ALL CAPS last name (2+ chars).
    Examples:
        "ALEKSIĆ Velisava LEPOSAVA, 1927..."
        "ABRAHAM IVAN, rođen 1906..."
        "ABRAM Jožeta ALOJZ, 1925..."
    """
    text = text.strip()
    if not text:
        return False

    # Skip single-letter section headers (A, B, C, Č, ...)
    if len(text) <= 2:
        return False

    # Skip page numbers
    if re.match(r'^\d{1,3}$', text):
        return False

    # Skip book page numbers like "340", "341" etc. at start/end of lines
    if re.match(r'^\d{3,4}\s*$', text):
        return False

    # Pattern 1: ALL CAPS last name (2+ chars) followed by space and more text
    # The last name must be mostly uppercase letters (allowing for OCR errors)
    # Examples: "ALEKSIĆ Velisava LEPOSAVA", "ABRAHAM IVAN"
    match = re.match(r'^([A-ZČĆŽŠĐa-zčćžšđ\-]{2,})\s+(.+)', text)
    if not match:
        return False

    first_word = match.group(1)

    # First word must be mostly uppercase (>=70% threshold for OCR errors)
    upper_count = sum(1 for c in first_word if c.isupper() or c in 'ČĆŽŠĐ')
    if len(first_word) > 0 and upper_count / len(first_word) < 0.7:
        return False

    # Must have at least 2 uppercase letters
    if upper_count < 2:
        return False

    # The rest after the last name should have something meaningful
    rest = match.group(2).strip()
    if not rest:
        return False

    # Check that rest starts with either:
    # - A capitalized word (father's name or first name): "Velisava", "IVAN"
    # - An uppercase first name: "IVAN", "ALOJZ"
    if re.match(r'^[A-ZČĆŽŠĐa-zčćžšđ]', rest):
        return True

    return False


def group_words_into_lines(words, y_tolerance=4):
    """Group words into lines based on Y-coordinate proximity.

    Returns list of dicts: [{'text': '...', 'top': float, 'x0': float}, ...]
    """
    if not words:
        return []

    words = sorted(words, key=lambda w: (w['top'], w['x0']))
    lines = []
    current_line = [words[0]]
    current_top = words[0]['top']

    for w in words[1:]:
        if abs(w['top'] - current_top) <= y_tolerance:
            current_line.append(w)
        else:
            current_line.sort(key=lambda ww: ww['x0'])
            text = ' '.join(ww['text'] for ww in current_line)
            avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
            x0 = current_line[0]['x0']
            lines.append({'text': text.strip(), 'top': avg_top, 'x0': x0})
            current_line = [w]
            current_top = w['top']

    if current_line:
        current_line.sort(key=lambda ww: ww['x0'])
        text = ' '.join(ww['text'] for ww in current_line)
        avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
        x0 = current_line[0]['x0']
        lines.append({'text': text.strip(), 'top': avg_top, 'x0': x0})

    return lines


def rejoin_hyphenated(text):
    """Rejoin words split across lines with hyphens.

    Examples: "Svr- ljig" -> "Svrljig", "Lajko- vac" -> "Lajkovac"
    """
    # Pattern: word ending with "- " followed by lowercase continuation
    text = re.sub(r'(\w)- (\w)', r'\1\2', text)
    # Also handle "word-\n" style (already joined as "word- continuation")
    text = re.sub(r'(\w)-\s+([a-zčćžšđ])', r'\1\2', text)
    return text


def extract_soldiers_from_pdf(pdf_path):
    """Extract soldier entries using word-level two-column splitting."""
    all_entries = []  # List of (text, page_num, top_y, x0) tuples

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        print(f"Processing soldier list pages {SOLDIER_START_PAGE}-{SOLDIER_END_PAGE}")

        for page_idx in range(SOLDIER_START_PAGE - 1, min(SOLDIER_END_PAGE, total_pages)):
            page_num = page_idx + 1
            page = pdf.pages[page_idx]

            # Get word-level data
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=True
            )

            if not words:
                continue

            # Split words into left and right columns
            left_words = [w for w in words if w['x0'] < COL_BOUNDARY]
            right_words = [w for w in words if w['x0'] >= COL_BOUNDARY]

            # Process each column independently (left first, then right)
            for col_name, col_words in [('L', left_words), ('R', right_words)]:
                if not col_words:
                    continue

                lines = group_words_into_lines(col_words)

                for line in lines:
                    text = line['text'].strip()
                    if not text:
                        continue

                    # Skip page numbers at bottom
                    if re.match(r'^\d{1,4}$', text):
                        continue

                    # Skip section letter headers (single letter like "A", "B", etc.)
                    if len(text) <= 2 and text.isalpha():
                        continue

                    if is_soldier_entry(text):
                        # Start a new entry
                        all_entries.append({
                            'text': text,
                            'page': page_num,
                            'top': line['top'],
                            'x0': line['x0'],
                        })
                    else:
                        # Continuation of previous entry
                        if all_entries:
                            all_entries[-1]['text'] += ' ' + text

            if page_num % 20 == 0:
                print(f"  Page {page_num}... ({len(all_entries)} entries so far)")

    print(f"  Extracted {len(all_entries)} raw entries")
    return all_entries


def parse_soldier_entry(entry_text):
    """Parse a single soldier entry into structured data.

    Format: LAST_NAME [Father's_genitive] FIRST_NAME [NICKNAME], year. Place, Municipality. [Death/fate info]

    The tricky part: distinguishing father's name (genitive, mixed case) from
    first name (ALL CAPS). Father's name is optional.

    Examples:
        "ALEKSIĆ Velisava LEPOSAVA, 1927. Velika Ivanča, Mladenovac."
         -> last=ALEKSIĆ, fathers=Velisava, first=LEPOSAVA, info="1927. Velika Ivanča, Mladenovac."

        "ABRAHAM IVAN, rođen 1906 u selu Virje, općina Đurđevac. *"
         -> last=ABRAHAM, first=IVAN, info="rođen 1906 u selu Virje, općina Đurđevac."

        "ALFIREVIĆ Mate MIROSLAV MIRO, 1922. Zaostrog, Makarska."
         -> last=ALFIREVIĆ, fathers=Mate, first=MIROSLAV, middle=MIRO, info="1922. Zaostrog, Makarska."
    """
    entry_text = rejoin_hyphenated(entry_text.strip())

    # Remove trailing asterisk markers
    entry_text = entry_text.rstrip('* •·').strip()

    if not entry_text:
        return None

    # Split name part from info part at the FIRST COMMA.
    # In this brigade's format, the first comma always separates the name block
    # from the additional info (year, place, death info, etc.)
    comma_idx = entry_text.find(',')
    if comma_idx > 0:
        name_part = entry_text[:comma_idx].strip()
        additional_info = entry_text[comma_idx + 1:].strip()
    else:
        # No comma - entire text might be just a name, or has a period separator
        # Try splitting at first year pattern
        year_match = re.search(r'(?<=\s)(19|18)\d{2}\.', entry_text)
        if year_match:
            name_part = entry_text[:year_match.start()].strip()
            additional_info = entry_text[year_match.start():].strip()
        else:
            name_part = entry_text
            additional_info = ''

    # Clean up name part
    name_part = name_part.rstrip('.,*•· ').strip()

    # Parse the name block
    # Expected patterns:
    #   "LAST_NAME FIRST_NAME" (no father's name)
    #   "LAST_NAME Father FIRST_NAME"
    #   "LAST_NAME Father FIRST NICKNAME"
    #   "LAST_NAME FIRST NICKNAME" (no father's name, but two first names)

    name_words = name_part.split()
    if not name_words:
        return None

    last_name = name_words[0]
    fathers_name = ''
    first_name = ''
    middle_name = ''

    if len(name_words) == 1:
        pass  # Just last name
    elif len(name_words) == 2:
        first_name = name_words[1]
    else:
        # 3+ words: need to figure out if word[1] is father's name or first name
        # Father's name: mixed case (starts uppercase, has lowercase), e.g. "Velisava", "Mate", "Jožeta"
        # First name: ALL CAPS, e.g. "IVAN", "LEPOSAVA", "ALOJZ"

        remaining = name_words[1:]

        # Check if the second word is a father's name (mixed case, not all caps)
        second_word = remaining[0]
        is_fathers = (
            second_word[0].isupper() and
            not second_word.isupper() and
            len(second_word) >= 2 and
            any(c.islower() for c in second_word[1:])
        )

        if is_fathers:
            fathers_name = second_word
            rest = remaining[1:]
        else:
            rest = remaining

        if len(rest) == 0:
            # Father's name was the only remaining word - treat as first name
            if fathers_name:
                first_name = fathers_name
                fathers_name = ''
        elif len(rest) == 1:
            first_name = rest[0]
        else:
            # Multiple remaining words - first is first_name, rest is middle/nickname
            first_name = rest[0]
            middle_name = ' '.join(rest[1:])

    # Handle entries like "rođ. JELIĆ" in name (maiden name)
    # These are rare edge cases

    return {
        'last_name': last_name,
        'middle_name': middle_name,
        'first_name': first_name,
        'fathers_name': fathers_name,
        'additional_info': additional_info,
    }


def save_to_json(soldiers, output_path):
    """Save soldiers data to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(soldiers)} soldiers to {output_path}")


if __name__ == '__main__':
    # Try multiple possible PDF locations
    pdf_paths = [
        '../01-data/raw/13-proleterska-spisak.pdf',
        '01-data/raw/13-proleterska-spisak.pdf',
    ]

    pdf_path = None
    for p in pdf_paths:
        if os.path.exists(p):
            pdf_path = p
            break

    if not pdf_path:
        print("Error: PDF not found! Expected at 01-data/raw/13-proleterska-spisak.pdf")
        sys.exit(1)

    print(f"Using PDF: {pdf_path}")
    print("Extracting soldiers from PDF using word-level column splitting...")
    raw_entries = extract_soldiers_from_pdf(pdf_path)

    print("\nParsing soldier entries...")
    soldiers = []
    failed = []
    for entry in raw_entries:
        soldier = parse_soldier_entry(entry['text'])
        if soldier and soldier['last_name']:
            soldiers.append(soldier)
        else:
            failed.append(entry['text'])

    print(f"\nTotal soldiers parsed: {len(soldiers)}")
    print(f"Failed to parse: {len(failed)}")

    # Check for entries with very long additional_info (possibly merged)
    long_entries = [s for s in soldiers if len(s.get('additional_info', '')) > 250]
    print(f"Entries with additional_info > 250 chars: {len(long_entries)}")
    if long_entries:
        print("\nSuspect entries (possibly merged):")
        for s in long_entries[:5]:
            name = f"{s['last_name']} {s['first_name']}"
            print(f"  {name}: {s['additional_info'][:120]}...")

    # Show first 15 entries
    print("\nFirst 15 entries:")
    for i, s in enumerate(soldiers[:15], 1):
        name = f"{s['last_name']} {s['first_name']}"
        father = f" (otac: {s['fathers_name']})" if s['fathers_name'] else ""
        mid = f" [{s['middle_name']}]" if s['middle_name'] else ""
        info = s['additional_info'][:70] if s['additional_info'] else "(no info)"
        print(f"  {i}. {name}{mid}{father}")
        print(f"     {info}")

    # Show some entries from the middle
    mid_idx = len(soldiers) // 2
    print(f"\nEntries from middle (#{mid_idx}-{mid_idx+5}):")
    for i, s in enumerate(soldiers[mid_idx:mid_idx + 5], mid_idx + 1):
        name = f"{s['last_name']} {s['first_name']}"
        father = f" (otac: {s['fathers_name']})" if s['fathers_name'] else ""
        info = s['additional_info'][:70] if s['additional_info'] else "(no info)"
        print(f"  {i}. {name}{father}")
        print(f"     {info}")

    # Stats
    with_father = sum(1 for s in soldiers if s['fathers_name'])
    with_info = sum(1 for s in soldiers if s['additional_info'])
    with_first = sum(1 for s in soldiers if s['first_name'])
    print(f"\nStats:")
    print(f"  With father's name: {with_father} ({100*with_father/len(soldiers):.1f}%)")
    print(f"  With first name: {with_first} ({100*with_first/len(soldiers):.1f}%)")
    print(f"  With additional info: {with_info} ({100*with_info/len(soldiers):.1f}%)")

    if failed:
        print(f"\nFailed entries (first 10):")
        for f_entry in failed[:10]:
            print(f"  {f_entry[:100]}")

    # Save to JSON
    json_path = '../website/public/13-proleterska-soldiers.json'
    if not os.path.exists(os.path.dirname(json_path)):
        json_path = 'website/public/13-proleterska-soldiers.json'

    save_to_json(soldiers, json_path)
    print("\nDone!")
