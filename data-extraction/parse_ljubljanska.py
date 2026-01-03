import pdfplumber
import csv
import json
import re

def extract_text_from_pdf(pdf_path):
    """Extract text from all pages of the PDF"""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")

        for i, page in enumerate(pdf.pages):
            if i % 50 == 0:
                print(f"Processing page {i+1}/{total_pages}...")
            text = page.extract_text()
            if text:
                pages_text.append(text)

    return pages_text

def split_two_column_line(line):
    """Split a line that may contain two soldier entries (from 2-column PDF layout)"""
    # Pattern: Last name (capitalized) followed by first name
    # e.g., "Abranovič Jože" or "Aleš Ivan"
    pattern = r'[A-ZČĆŽŠĐ][a-zčćžšđčćžšđ]+\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+'

    # Find all matches
    matches = list(re.finditer(pattern, line))

    if len(matches) <= 1:
        # Single entry or no matches
        return [line]

    # Split at the position of the second match
    split_pos = matches[1].start()
    return [line[:split_pos].strip(), line[split_pos:].strip()]

def parse_soldiers(pages_text):
    """Parse soldier information from extracted text"""
    soldiers = []

    # Combine all pages into one text
    full_text = '\n'.join(pages_text)
    lines = full_text.split('\n')

    # Find where the actual soldier list starts
    # Look for "SEZNAM BORCEV" header
    start_index = 0
    for i, line in enumerate(lines):
        if 'SEZNAM BORCEV' in line:
            # Skip the introduction and start from the "A" section
            for j in range(i, min(i + 60, len(lines))):
                # Look for first actual name entry (starts with "A " or similar)
                if re.match(r'^[A-Z]\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+', lines[j]):
                    start_index = j
                    print(f"Found soldier list starting at line {start_index}")
                    try:
                        print(f"First entry: {lines[j][:80]}...")
                    except UnicodeEncodeError:
                        print("First entry: [Contains special characters]")
                    break
            if start_index > 0:
                break

    if start_index == 0:
        print("Warning: Could not find soldier list start. Starting from beginning.")

    lines = lines[start_index:]

    # Split two-column entries and collect all entries
    all_entries = []
    current_entry = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Stop at table of contents or index
        if 'Kazalo' in line or 'kazalo' in line or 'KAZALO' in line:
            break

        # Split potential two-column lines
        split_lines = split_two_column_line(line)

        for split_line in split_lines:
            # Check if this looks like the start of a new entry
            # Pattern: Capitalized word at start (could be continuation or new entry)
            if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđčćžšđ]+\s+[A-ZČĆŽŠĐ]', split_line):
                # This is likely a new entry
                if current_entry:
                    all_entries.append(' '.join(current_entry))
                current_entry = [split_line]
            else:
                # Continuation of current entry
                if current_entry:
                    current_entry.append(split_line)

    # Don't forget the last entry
    if current_entry:
        all_entries.append(' '.join(current_entry))

    # Parse each entry
    for entry in all_entries:
        soldier = parse_soldier_entry(entry)
        if soldier['last_name']:  # Only add if we got a valid name
            soldiers.append(soldier)

    return soldiers

def parse_soldier_entry(entry_text):
    """Parse a single soldier entry into structured data"""
    # Slovenian format: Last_name First_name - Partisan_name, year, place, additional info
    # Example: "Abranovič Jože, 1920, Ljubljana"
    # Example: "Amon Ervin - Žarko, 1914, Kranj, utonil 22.8.1944 v Krki"

    # Split by comma to separate name from year/place/info
    parts = entry_text.split(',', 1)
    name_part = parts[0].strip()
    additional_info = parts[1].strip() if len(parts) > 1 else ''

    # Parse the name part
    # Could have: Last First, Last First - Partisan, or variations
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
        # Split on dash to separate real name from partisan name
        before_dash = name_part.split('-')[0].strip()
        name_words = before_dash.split()

    if len(name_words) == 1:
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
        # 3 or more: last name, middle name(s), first name
        return {
            'last_name': name_words[0],
            'middle_name': ' '.join(name_words[1:-1]),
            'first_name': name_words[-1],
            'additional_info': additional_info
        }

def save_to_csv(soldiers, output_path):
    """Save soldiers data to CSV file"""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['last_name', 'middle_name', 'first_name', 'additional_info']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for soldier in soldiers:
            writer.writerow(soldier)

    print(f"Saved {len(soldiers)} soldiers to {output_path}")

def save_to_json(soldiers, output_path):
    """Save soldiers data to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(soldiers, jsonfile, ensure_ascii=False, indent=2)

    print(f"Saved {len(soldiers)} soldiers to {output_path}")

if __name__ == '__main__':
    pdf_path = '../01-data/raw/ljubljanska brigada.pdf'

    print("Extracting text from PDF...")
    pages_text = extract_text_from_pdf(pdf_path)

    # Save extracted text for inspection
    extracted_text_path = '../01-data/processed/ljubljanska_extracted.txt'
    with open(extracted_text_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(pages_text))
    print(f"Saved extracted text to {extracted_text_path}")

    print("\nParsing soldiers...")
    soldiers = parse_soldiers(pages_text)

    print(f"\nTotal soldiers found: {len(soldiers)}")

    # Save to CSV and JSON
    csv_path = '../01-data/processed/ljubljanska_soldiers.csv'
    json_path = '../website/public/ljubljanska-soldiers.json'

    save_to_csv(soldiers, csv_path)
    save_to_json(soldiers, json_path)

    print("\nDone!")
