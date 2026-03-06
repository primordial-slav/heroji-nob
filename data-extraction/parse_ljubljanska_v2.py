"""
Parser for Ljubljanska (10. SNOUB) brigade soldier data.

The PDF has a two-column layout. Previous versions used extract_text() which
merges both columns into single lines, causing soldiers from the right column
to get merged into entries from the left column.

This version uses extract_words() to get word positions, then splits into
left/right columns by x-coordinate before grouping into lines. This gives
clean per-column text and eliminates cross-column merging.

PDF structure:
  - Page 394: "SEZNAM BORCEV" header
  - Pages 396-447: Soldier list (two columns per page)
  - Page 448+: "Kazalo osebnih imen" (name index)

Soldier entry format (Slovenian):
  Surname Firstname - PartisanName, year, place, info
  e.g. "Amon Ervin - Žarko, 1914, Kranj, utonil 22.8.1944 v Krki"
"""
import pdfplumber
import csv
import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Page range for soldier list
SOLDIER_START_PAGE = 396
SOLDIER_END_PAGE = 447


def is_soldier_entry(text):
    """Check if a line starts a new soldier entry.

    Slovenian format: Capitalized Surname followed by capitalized Firstname.
    Examples: "Abranovič Jože", "Amon Ervin - Žarko, 1914"

    Also handles OCR errors where diacritical characters get lowercased:
    "špiler Anton" (should be "Špiler"), "šrok Prane" (should be "Šrok")
    """
    text = text.strip()
    if not text:
        return False

    # Skip single-letter section headers (A, B, C, ...)
    if len(text) <= 2 and text.isupper():
        return False

    # Skip page numbers
    if re.match(r'^\d{1,3}$', text):
        return False

    # Pattern 1: Normal capitalized surname + space + capitalized first name
    # Includes Slovenian diacritics: č, ć, ž, š, đ
    if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]', text):
        return True

    # Pattern 2: OCR error - lowercase diacritical first character (š, ž, č, ć, đ)
    # followed by rest of surname (3+ chars) and capitalized first name
    # Examples: "špiler Anton", "šrok Prane", "špolar Ivan"
    if re.match(r'^[šžčćđ][a-zčćžšđ]{2,}\s+[A-ZČĆŽŠĐ][a-zčćžšđ]', text):
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


def extract_soldiers_from_pdf(pdf_path):
    """Extract soldier entries using word-level two-column splitting."""
    all_entries = []  # List of raw entry strings

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        print(f"Processing soldier list pages {SOLDIER_START_PAGE}-{SOLDIER_END_PAGE}")

        for page_idx in range(SOLDIER_START_PAGE - 1, min(SOLDIER_END_PAGE, total_pages)):
            page_num = page_idx + 1
            page = pdf.pages[page_idx]

            # Check for end marker
            page_text = page.extract_text() or ''
            if 'Kazalo osebnih' in page_text or 'Kazalo krajevnih' in page_text:
                print(f"  Found index on page {page_num}, stopping")
                break

            # Get word-level data
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=True
            )

            if not words:
                continue

            # Column boundary: left column max x0 ≈ 264, right column min x0 ≈ 293
            # Use 280 as threshold (midpoint of the gap between columns)
            col_boundary = 280

            # Split words into left and right columns
            left_words = [w for w in words if w['x0'] < col_boundary]
            right_words = [w for w in words if w['x0'] >= col_boundary]

            # Process each column independently
            for col_name, col_words in [('L', left_words), ('R', right_words)]:
                if not col_words:
                    continue

                lines = group_words_into_lines(col_words)

                for line in lines:
                    text = line['text'].strip()
                    if not text:
                        continue

                    # Skip page numbers at bottom
                    if re.match(r'^\d{1,3}$', text):
                        continue

                    if is_soldier_entry(text):
                        # Start a new entry
                        all_entries.append(text)
                    else:
                        # Continuation of previous entry
                        if all_entries:
                            all_entries[-1] += ' ' + text

            if page_num % 10 == 0:
                print(f"  Page {page_num}... ({len(all_entries)} entries so far)")

    print(f"  Extracted {len(all_entries)} raw entries")
    return all_entries


def parse_soldier_entry(entry_text):
    """Parse a single soldier entry into structured data.

    Slovenian format: Surname Firstname - PartisanName, year, place, info
    Examples:
        "Abranovič Jože, 1920, Ljubljana"
        "Amon Ervin - Žarko, 1914, Kranj, utonil 22.8.1944 v Krki"
        "Kočevar Franc. 1926. Suhor, Metlika"
    """
    # Separate the name from additional info
    # Strategy: Look for year patterns (4 digits) which indicate start of additional info

    # Split by comma to get rough separation
    parts = entry_text.split(',', 1)
    name_and_maybe_year = parts[0].strip()
    rest_info = parts[1].strip() if len(parts) > 1 else ''

    # Check if name_and_maybe_year contains a year (4 digits)
    year_match = re.search(r'\b(19\d{2}|18\d{2})\b', name_and_maybe_year)

    if year_match:
        # Split at the year
        year_start = year_match.start()
        name_part = name_and_maybe_year[:year_start].strip()
        year_and_rest = name_and_maybe_year[year_start:].strip()

        # Combine year_and_rest with rest_info
        if rest_info:
            additional_info = year_and_rest + ', ' + rest_info
        else:
            additional_info = year_and_rest
    else:
        name_part = name_and_maybe_year
        additional_info = rest_info

    # Remove trailing periods and commas from name
    name_part = name_part.rstrip('.,').strip()

    # Parse the name part
    name_words = name_part.split()

    if not name_words:
        return {
            'last_name': '',
            'middle_name': '',
            'first_name': '',
            'additional_info': entry_text
        }

    # Remove partisan name if present (after dash)
    if '-' in name_part:
        before_dash = name_part.split('-')[0].strip()
        name_words = before_dash.split()

    # Clean up each word - remove periods
    name_words = [w.rstrip('.,').strip() for w in name_words if w.rstrip('.,').strip()]

    if len(name_words) == 0:
        return {
            'last_name': '',
            'middle_name': '',
            'first_name': '',
            'additional_info': entry_text
        }
    elif len(name_words) == 1:
        return {
            'last_name': name_words[0],
            'middle_name': '',
            'first_name': '',
            'additional_info': additional_info
        }
    elif len(name_words) == 2:
        return {
            'last_name': name_words[0],
            'middle_name': '',
            'first_name': name_words[1],
            'additional_info': additional_info
        }
    else:
        return {
            'last_name': name_words[0],
            'middle_name': ' '.join(name_words[1:-1]),
            'first_name': name_words[-1],
            'additional_info': additional_info
        }


def save_to_csv(soldiers, output_path):
    """Save soldiers data to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['last_name', 'middle_name', 'first_name', 'additional_info']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for soldier in soldiers:
            writer.writerow(soldier)
    print(f"Saved {len(soldiers)} soldiers to {output_path}")


def save_to_json(soldiers, output_path):
    """Save soldiers data to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(soldiers, jsonfile, ensure_ascii=False, indent=2)
    print(f"Saved {len(soldiers)} soldiers to {output_path}")


if __name__ == '__main__':
    pdf_path = '../website/public/pdfs/ljubljanska-brigada.pdf'

    if not os.path.exists(pdf_path):
        pdf_path = 'website/public/pdfs/ljubljanska-brigada.pdf'
        if not os.path.exists(pdf_path):
            print("Error: PDF not found!")
            sys.exit(1)

    print("Extracting soldiers from PDF using word-level column splitting...")
    raw_entries = extract_soldiers_from_pdf(pdf_path)

    print("\nParsing soldier entries...")
    soldiers = []
    for entry in raw_entries:
        soldier = parse_soldier_entry(entry)
        if soldier['last_name']:
            soldiers.append(soldier)

    print(f"\nTotal soldiers found: {len(soldiers)}")

    # Check for entries with very long additional_info (likely still merged)
    long_entries = [s for s in soldiers if len(s.get('additional_info', '')) > 200]
    print(f"Entries with additional_info > 200 chars: {len(long_entries)}")
    if long_entries:
        print("\nSuspect entries (possibly merged):")
        for s in long_entries[:5]:
            name = f"{s['last_name']} {s['first_name']}"
            print(f"  {name}: {s['additional_info'][:120]}...")

    # Show first 10 entries
    print("\nFirst 10 entries:")
    for i, s in enumerate(soldiers[:10], 1):
        name = f"{s['last_name']} {s['first_name']}"
        info = s['additional_info'][:60] if s['additional_info'] else "(no info)"
        print(f"  {i}. {name}")
        print(f"     {info}")

    # Save
    os.makedirs('../01-data/processed', exist_ok=True)
    csv_path = '../01-data/processed/ljubljanska_soldiers_v2.csv'
    json_path = '../website/public/ljubljanska-soldiers.json'

    save_to_csv(soldiers, csv_path)
    save_to_json(soldiers, json_path)

    print("\nDone!")
