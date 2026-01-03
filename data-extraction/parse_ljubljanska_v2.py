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

def smart_split_two_columns(line):
    """
    Intelligently split a line that contains two soldier entries from a two-column layout.
    Strategy: Look for patterns where two capitalized names appear close together,
    indicating the boundary between left and right columns.
    """
    # Pattern: Find positions where we have "Name1 Name2" where both are capitalized
    # and Name2 starts a new entry (followed by year or more names)

    # Find all capitalized words (potential last names)
    cap_pattern = r'[A-ZČĆŽŠĐ][a-zčćžšđčćžšđ]+'
    matches = list(re.finditer(cap_pattern, line))

    if len(matches) < 3:
        # Not enough matches for two columns
        return [line]

    # Look for the split point: where we have a capitalized word followed by another
    # capitalized word that likely starts a new entry
    # Heuristic: If we see "Word1 Word2" where Word2 is followed by a comma and numbers (birth year),
    # or followed by another capitalized word, it's likely a new entry

    for i in range(1, len(matches) - 1):
        # Check if this could be the start of the right column
        pos = matches[i].start()
        # Get text after this position
        after = line[pos:]

        # Check if it looks like the start of a new entry:
        # Pattern: "LastName FirstName, year" or "LastName FirstName - Partisan"
        if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+\s*[-,]', after):
            # This looks like a new entry
            left = line[:pos].strip()
            right = after.strip()
            return [left, right]

    # If no clear split found, return as is
    return [line]

def parse_soldiers(pages_text):
    """Parse soldier information from extracted text"""
    soldiers = []

    # Combine all pages into one text
    full_text = '\n'.join(pages_text)
    lines = full_text.split('\n')

    # Find where the actual soldier list starts
    start_index = 0
    for i, line in enumerate(lines):
        if 'SEZNAM BORCEV' in line:
            # Skip the introduction and start from the "A" section
            for j in range(i, min(i + 60, len(lines))):
                # Look for first actual name entry (starts with "A " or similar)
                if re.match(r'^[A-Z]\s+[A-ZČĆŽŠĐ][a-zčćžšđ]+', lines[j]):
                    start_index = j
                    print(f"Found soldier list starting at line {start_index}")
                    break
            if start_index > 0:
                break

    if start_index == 0:
        print("Warning: Could not find soldier list start. Starting from beginning.")

    lines = lines[start_index:]

    # Parse soldiers by processing lines and handling two-column layout
    left_entry = []
    right_entry = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Stop at table of contents
        if 'Kazalo' in line or 'kazalo' in line or 'KAZALO' in line:
            break

        # Try to split into two columns
        split_lines = smart_split_two_columns(line)

        if len(split_lines) == 2:
            # We have both columns
            left_part = split_lines[0]
            right_part = split_lines[1]

            # Check if left_part is a new entry or continuation
            if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]', left_part):
                # New entry on left
                if left_entry:
                    # Save previous left entry
                    soldiers.append(parse_soldier_entry(' '.join(left_entry)))
                left_entry = [left_part]
            else:
                # Continuation of left entry
                left_entry.append(left_part)

            # Check if right_part is a new entry or continuation
            if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]', right_part):
                # New entry on right
                if right_entry:
                    # Save previous right entry
                    soldiers.append(parse_soldier_entry(' '.join(right_entry)))
                right_entry = [right_part]
            else:
                # Continuation of right entry
                right_entry.append(right_part)

        else:
            # Single column or unclear - check if it's a new entry
            if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]', line):
                # Looks like a new entry - save to left column by default
                if left_entry:
                    soldiers.append(parse_soldier_entry(' '.join(left_entry)))
                left_entry = [line]
            else:
                # Continuation - add to left entry
                if left_entry:
                    left_entry.append(line)

    # Don't forget last entries
    if left_entry:
        soldiers.append(parse_soldier_entry(' '.join(left_entry)))
    if right_entry:
        soldiers.append(parse_soldier_entry(' '.join(right_entry)))

    # Filter out invalid entries
    soldiers = [s for s in soldiers if s['last_name']]

    return soldiers

def parse_soldier_entry(entry_text):
    """Parse a single soldier entry into structured data"""
    # Slovenian format: Last_name First_name - Partisan_name, year, place, additional info
    # Example: "Abranovič Jože, 1920, Ljubljana"
    # Example: "Amon Ervin - Žarko, 1914, Kranj, utonil 22.8.1944 v Krki"
    # Example: "Kočevar Franc. 1926. Suhor, Metlika" (name stops at year)

    # First, separate the name from additional info
    # Strategy: Look for year patterns (4 digits) which indicate start of additional info

    # Split by comma to get rough separation
    parts = entry_text.split(',', 1)
    name_and_maybe_year = parts[0].strip()
    rest_info = parts[1].strip() if len(parts) > 1 else ''

    # Check if name_and_maybe_year contains a year (4 digits)
    # Pattern: Look for year like "1926" or "1926."
    year_match = re.search(r'\b(19\d{2}|18\d{2})\b', name_and_maybe_year)

    if year_match:
        # Split at the year - everything before is name, year and after is additional info
        year_start = year_match.start()
        name_part = name_and_maybe_year[:year_start].strip()
        year_and_rest = name_and_maybe_year[year_start:].strip()

        # Combine year_and_rest with rest_info
        if rest_info:
            additional_info = year_and_rest + ', ' + rest_info
        else:
            additional_info = year_and_rest
    else:
        # No year found in first part, use original split
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
        # Split on dash to separate real name from partisan name
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
    # Use already extracted text to save time
    extracted_text_path = '../01-data/processed/ljubljanska_extracted.txt'

    print("Loading extracted text...")
    with open(extracted_text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    pages_text = text.split('\n')

    print("\nParsing soldiers with improved two-column handling...")
    soldiers = parse_soldiers([text])

    print(f"\nTotal soldiers found: {len(soldiers)}")

    # Save to CSV and JSON
    csv_path = '../01-data/processed/ljubljanska_soldiers_v2.csv'
    json_path = '../website/public/ljubljanska-soldiers.json'

    save_to_csv(soldiers, csv_path)
    save_to_json(soldiers, json_path)

    print("\nDone! Check the CSV file to verify the data quality.")
