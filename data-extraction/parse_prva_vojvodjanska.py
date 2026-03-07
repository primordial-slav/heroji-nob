"""
Parser for Prva Vojvođanska Brigada soldier list.

Source: znaci.org/00001/132_7.pdf (33 pages, ~570 soldiers)
Format: Two-column, no entry numbers, alphabetical.
  LastName (Father) First, year, place, role, fate

Column split at x=195. Entries start with a capitalized last name at the
left margin of each column (x≈46 for left, x≈200 for right).
"""

import sys
import re
import json
import pdfplumber
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')
from scripts.soldier_id_utils import assign_ids_to_soldiers

PDF_FILE = 'website/public/pdfs/prva-vojvodjanska.pdf'
OUTPUT_FILE = 'website/public/prva-vojvodjanska-soldiers.json'
BRIGADE_CODE = 9

START_PAGE = 2   # First data page (1-indexed)
END_PAGE = 33    # Last data page

COL_SPLIT_X = 195  # X coordinate splitting left/right columns


def extract_column_lines(pdf_path):
    """Extract text as left/right column lines from each page."""
    pdf = pdfplumber.open(pdf_path)

    left_lines = []
    right_lines = []

    for page_num in range(START_PAGE - 1, min(END_PAGE, len(pdf.pages))):
        page = pdf.pages[page_num]
        words = page.extract_words()
        if not words:
            continue

        # Group words by y-position (line)
        lines_by_y = defaultdict(list)
        for w in words:
            y_key = round(w['top'] / 9) * 9
            lines_by_y[y_key].append(w)

        for y_key in sorted(lines_by_y.keys()):
            ws = sorted(lines_by_y[y_key], key=lambda w: w['x0'])

            # Split into left/right columns
            left_ws = [w for w in ws if w['x0'] < COL_SPLIT_X]
            right_ws = [w for w in ws if w['x0'] >= COL_SPLIT_X]

            if left_ws:
                left_text = ' '.join(w['text'] for w in left_ws)
                left_x = left_ws[0]['x0']
                left_lines.append({'text': left_text, 'x': left_x, 'page': page_num + 1})

            if right_ws:
                right_text = ' '.join(w['text'] for w in right_ws)
                right_x = right_ws[0]['x0']
                right_lines.append({'text': right_text, 'x': right_x, 'page': page_num + 1})

    pdf.close()
    return left_lines, right_lines


def group_into_entries(lines, col_start_x):
    """Group lines into entries. New entry starts when a line begins near column margin with a capital letter."""
    entries = []
    current_entry = None

    for line in lines:
        text = line['text'].strip()
        if not text:
            continue

        # Skip headers
        if 'SPISAK BORACA' in text or 'VOJVOĐANSKE' in text or 'BRIGADE' in text:
            continue
        # Skip page numbers
        if re.match(r'^\d{1,3}$', text):
            continue
        if text in ('570',):  # Known page number at end
            continue

        # Detect new entry: line starts near column margin AND first word starts with capital
        is_new_entry = False
        x_near_margin = abs(line['x'] - col_start_x) < 15

        if x_near_margin:
            first_word = text.split()[0] if text.split() else ''
            # New entry starts with a capitalized surname
            # But not continuation lines (which are lowercase or start with common words)
            if first_word and first_word[0].isupper() and len(first_word) > 1:
                # Check it's not a continuation (common words that start entries on continuation)
                cont_words = {'Sahranjen', 'Sahra', 'Poginuo', 'Pogi', 'Umro', 'Mjesto', 'Mesto', 'Ranjen'}
                # If it looks like a name (ends with ić, ov, ek, etc), it's a new entry
                if not any(first_word.startswith(cw) for cw in cont_words):
                    is_new_entry = True

        if is_new_entry:
            if current_entry:
                entries.append(current_entry)
            current_entry = text
        elif current_entry is not None:
            current_entry += ' ' + text
        else:
            # First line might not be at margin exactly
            current_entry = text

    if current_entry:
        entries.append(current_entry)

    return entries


def parse_entry(raw_text):
    """
    Parse entry like:
      Abadžić Stevan
      Abazović Abaz, Šipalj (Kosovska Mitrovica), poginuo i sahranjen u Vinkovcima
      Aleksić Jovica, zamenik komesara, Čerević (Beočin)
      Arsenov (Živa) Ilija, 1922, Crepaja (Kovačica), poginuo i sahranjen u Bistrinicima
      Anučin Milan, 1909, Ugrinovci (Zemun); poginuo u Fruškoj gori
    """
    text = raw_text.strip()

    last_name = ''
    first_name = ''
    fathers_name = ''
    additional_info = ''

    # Extract father's name in parentheses if it appears in the name part
    # Pattern: "LastName (Father) FirstName, info"
    paren_in_name = re.match(r'^(\S+)\s+\(([^)]+)\)\s+(\S+)(.*)', text)
    if paren_in_name:
        last_name = paren_in_name.group(1)
        fathers_name = paren_in_name.group(2)
        first_name = paren_in_name.group(3).rstrip(',')
        rest = paren_in_name.group(4).strip().lstrip(',').strip()
        additional_info = rest
    else:
        # Split at first comma
        comma_idx = text.find(',')
        if comma_idx > 0:
            name_part = text[:comma_idx].strip()
            additional_info = text[comma_idx + 1:].strip()

            # Check for "LastName MiddleInitial. FirstName" pattern
            words = name_part.split()
            if len(words) >= 2:
                last_name = words[0]
                first_name = ' '.join(words[1:])
            else:
                last_name = name_part
        else:
            # No comma - entire text might just be a name
            words = text.split()
            if len(words) >= 2:
                last_name = words[0]
                first_name = ' '.join(words[1:])
            else:
                last_name = text

    # Extract birth year from additional_info (first 4-digit year)
    birth_year = ''
    if additional_info:
        year_match = re.search(r'\b(1[89]\d{2})\b', additional_info)
        if year_match:
            birth_year = year_match.group(1)

    full_name = f"{last_name} {first_name}".strip()

    return {
        'last_name': last_name,
        'first_name': first_name,
        'middle_name': '',
        'fathers_name': fathers_name,
        'full_name': full_name,
        'additional_info': additional_info,
        'birth_year': birth_year,
    }


def main():
    print(f"Parsing {PDF_FILE}...")

    left_lines, right_lines = extract_column_lines(PDF_FILE)
    print(f"  Left column: {len(left_lines)} lines")
    print(f"  Right column: {len(right_lines)} lines")

    # Detect column start x (mode of x for first-word lines)
    left_x = 47  # approximate
    right_x = 200  # approximate

    left_entries = group_into_entries(left_lines, left_x)
    right_entries = group_into_entries(right_lines, right_x)
    print(f"  Left entries: {len(left_entries)}")
    print(f"  Right entries: {len(right_entries)}")

    # Combine left + right (interleaved alphabetically? or just left then right?)
    # Since entries are alphabetical across both columns, merge them all
    all_raw = left_entries + right_entries

    soldiers = []
    for raw in all_raw:
        soldier = parse_entry(raw)
        if soldier['last_name']:  # Skip empty entries
            soldiers.append(soldier)

    # Sort alphabetically by last name, then first name
    soldiers.sort(key=lambda s: (s['last_name'].lower(), s['first_name'].lower()))

    # Assign IDs
    soldiers = assign_ids_to_soldiers(soldiers, BRIGADE_CODE)

    # Print samples
    print(f"\nFirst 10 entries:")
    for s in soldiers[:10]:
        print(f"  {s['soldier_id']}: {s['full_name']}, father: {s['fathers_name']}, "
              f"birth: {s['birth_year']}, info: {s['additional_info'][:80]}")

    print(f"\nLast 5 entries:")
    for s in soldiers[-5:]:
        print(f"  {s['soldier_id']}: {s['full_name']}, father: {s['fathers_name']}, "
              f"birth: {s['birth_year']}, info: {s['additional_info'][:80]}")

    # Stats
    with_birth = sum(1 for s in soldiers if s['birth_year'])
    with_father = sum(1 for s in soldiers if s['fathers_name'])
    empty_first = sum(1 for s in soldiers if not s['first_name'])
    print(f"\nTotal: {len(soldiers)} soldiers")
    print(f"With birth year: {with_birth} ({100*with_birth/len(soldiers):.1f}%)")
    print(f"With father's name: {with_father} ({100*with_father/len(soldiers):.1f}%)")
    print(f"Empty first name: {empty_first}")

    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
