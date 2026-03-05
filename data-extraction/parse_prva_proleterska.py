import pdfplumber
import re
import csv
import json
import os

def extract_text_from_pdfs(pdf_paths):
    """Extract text from multiple PDF files and combine them"""
    all_text = []

    for pdf_path in pdf_paths:
        print(f"Processing {os.path.basename(pdf_path)}...")
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text.append(f"--- PAGE {i+1} of {os.path.basename(pdf_path)} ---")
                    all_text.append(text)
        print(f"  Extracted {len(pdf.pages)} pages")

    return '\n'.join(all_text)

def is_new_entry(line):
    """Check if a line starts a new soldier entry"""
    # Pattern 1: All caps last name(s) (may be hyphenated), optional middle initial(s), capitalized first name
    # Examples: "KOVAČEVIĆ Marko", "APOSTOLOVIĆ M. Slobodan", "PAVIĆEVIĆ-LEKOVIĆ Ilije MILICA"
    pattern1 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+)*\s+([A-ZČĆŽŠĐ]\.?\s+)*[A-ZČĆŽŠĐ][a-zčćžšđ]'

    # Pattern 2: ALL CAPS names (for names that are entirely capitalized, may be hyphenated)
    # Examples: "KOVAČEVIĆ JOCO", "MARKOVIĆ PETAR"
    pattern2 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+\s+[A-ZČĆŽŠĐ]{2,}(\s*,|\s+[A-ZČĆŽŠĐ])'

    return bool(re.match(pattern1, line)) or bool(re.match(pattern2, line))

def parse_soldier_entry(entry_text):
    """Parse a soldier entry into structured data"""
    entry_text = entry_text.strip()

    # Split into name part and additional info
    # Look for common separators like birth year, location indicators
    parts = entry_text.split(',', 1)
    name_part = parts[0].strip()
    additional_info = parts[1].strip() if len(parts) > 1 else ''

    # Parse the name into last_name, middle_name, first_name
    name_parts = name_part.split()

    if len(name_parts) >= 2:
        # Find where the capitalized first name starts
        first_name_index = -1
        for i, part in enumerate(name_parts):
            if part and part[0].isupper() and len(part) > 1 and part[1].islower():
                first_name_index = i
                break

        if first_name_index > 0:
            last_name = name_parts[0]
            first_name = ' '.join(name_parts[first_name_index:])
            middle_name = ' '.join(name_parts[1:first_name_index]) if first_name_index > 1 else ''
        else:
            # Fallback: last name is first, everything else after
            last_name = name_parts[0]
            middle_name = ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else ''
            first_name = name_parts[-1]
    else:
        last_name = name_parts[0] if name_parts else ''
        middle_name = ''
        first_name = ''

    return {
        'last_name': last_name,
        'middle_name': middle_name,
        'first_name': first_name,
        'additional_info': additional_info
    }

def parse_soldiers_from_text(text):
    """Parse soldier entries from extracted text"""
    lines = text.split('\n')
    soldiers = []
    current_entry = []

    # Find where the actual soldier list starts
    start_parsing = False
    for i, line in enumerate(lines):
        if 'Spisak pripadnika' in line:
            # Skip the header section (next ~5 lines after "Spisak pripadnika")
            # Start from the line after "do 15. V 1945. godine"
            for j in range(i, min(i + 10, len(lines))):
                if '1945. godine' in lines[j]:
                    start_parsing = True
                    lines = lines[j+1:]  # Start from next line
                    break
            break

    if not start_parsing:
        print("Warning: Could not find 'Spisak pripadnika' header, parsing entire document")

    for line in lines:
        line = line.strip()

        # Skip empty lines and page markers
        if not line or line.startswith('---'):
            continue

        # Check if this is a new soldier entry
        if is_new_entry(line):
            # Save previous entry if exists
            if current_entry:
                entry_text = ' '.join(current_entry)
                soldier = parse_soldier_entry(entry_text)
                soldiers.append(soldier)

            # Start new entry
            current_entry = [line]
        else:
            # Continue current entry
            if current_entry:
                current_entry.append(line)

    # Don't forget the last entry
    if current_entry:
        entry_text = ' '.join(current_entry)
        soldier = parse_soldier_entry(entry_text)
        soldiers.append(soldier)

    return soldiers

def main():
    # Define the three PDF files
    base_path = '../01-data/raw'
    pdf_files = [
        os.path.join(base_path, 'prva proleterska 1.pdf'),
        os.path.join(base_path, 'prva proleterska 2.pdf'),
        os.path.join(base_path, 'prva proleterska 3.pdf')
    ]

    # Check if files exist
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            print(f"Error: {pdf_file} not found!")
            return

    print("Extracting text from PDFs...")
    combined_text = extract_text_from_pdfs(pdf_files)

    # Save extracted text
    output_text_path = '../01-data/processed/prva_proleterska_extracted.txt'
    with open(output_text_path, 'w', encoding='utf-8') as f:
        f.write(combined_text)
    print(f"Saved extracted text to {output_text_path}")

    print("\nParsing soldier entries...")
    soldiers = parse_soldiers_from_text(combined_text)

    print(f"Found {len(soldiers)} soldier entries")

    # Save to CSV with UTF-8 BOM for Excel compatibility
    csv_path = '../01-data/processed/prva_proleterska_soldiers.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['last_name', 'middle_name', 'first_name', 'additional_info'])
        writer.writeheader()
        writer.writerows(soldiers)
    print(f"Saved CSV to {csv_path}")

    # Save to JSON
    json_path = '../01-data/processed/prva_proleterska_soldiers.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to {json_path}")

    # Print sample entries
    print("\nSample entries (first 5):")
    for i, soldier in enumerate(soldiers[:5], 1):
        print(f"{i}. {soldier['last_name']} {soldier['middle_name']} {soldier['first_name']}")
        if soldier['additional_info']:
            print(f"   Info: {soldier['additional_info']}")

if __name__ == '__main__':
    main()
