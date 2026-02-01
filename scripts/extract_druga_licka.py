"""
Extract soldier names from Druga Lička Proleterska Brigada PDF.
The PDF contains a list of fallen soldiers (spisak poginulih).

Format in PDF:
LASTNAME Father's_name FIRSTNAME, rođen YEAR. u BIRTHPLACE. MILITARY_INFO. DEATH_INFO.

Example:
ADAMOVIĆ Dmitra DANILO, rođen 1924. u s. Mekinjar. Borac 3. bataljona. Poginuo na Udbini 21/22. 08. 1942. godine.
"""

import re
import sys
import pandas as pd
from pathlib import Path

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pdfplumber'])
    import pdfplumber


def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def parse_soldier_entry(entry):
    """
    Parse a single soldier entry.

    Expected format:
    LASTNAME Father's_name FIRSTNAME, additional_info

    Where additional_info contains: rođen YEAR, birthplace, military unit, death info
    """
    entry = entry.strip()
    if not entry:
        return None

    # Split at the first comma to separate name from additional info
    comma_split = entry.split(',', 1)
    name_part = comma_split[0].strip()
    additional_info = comma_split[1].strip() if len(comma_split) > 1 else ""

    # Parse the name part: LASTNAME Father's_name FIRSTNAME
    # LASTNAME is all caps, Father's name is mixed case, FIRSTNAME is all caps
    words = name_part.split()

    if len(words) < 2:
        return None

    last_name = ""
    middle_name = ""  # Father's name
    first_name = ""

    # Find where the last name ends (all caps words at the beginning)
    # Then father's name (mixed case), then first name (all caps at end)

    i = 0
    # Collect last name parts (all uppercase at the start)
    while i < len(words) and words[i].isupper():
        if last_name:
            last_name += " "
        last_name += words[i]
        i += 1

    # Next should be father's name (mixed case or with genitive endings)
    if i < len(words) and not words[i].isupper():
        middle_name = words[i]
        i += 1

    # Rest should be first name (usually uppercase)
    while i < len(words):
        if first_name:
            first_name += " "
        first_name += words[i]
        i += 1

    # Extract birth year from additional info if present
    birth_year = ""
    birth_year_match = re.search(r'rođen[a]?\s+(\d{4})', additional_info)
    if birth_year_match:
        birth_year = birth_year_match.group(1)

    # Also check for date format like "15. 3. 1923"
    if not birth_year:
        date_match = re.search(r'(\d{1,2}\.\s*\d{1,2}\.\s*(\d{4}))', additional_info)
        if date_match:
            birth_year = date_match.group(2)

    return {
        'last_name': last_name,
        'middle_name': middle_name,  # Father's name
        'first_name': first_name,
        'birth_year': birth_year,
        'additional_info': additional_info
    }


def extract_soldiers_from_text(text):
    """
    Extract soldier entries from the PDF text.

    Soldiers are listed in entries that start with an uppercase name.
    """
    soldiers = []

    # Split text into lines
    lines = text.split('\n')

    current_entry = ""

    for line in lines:
        line = line.strip()

        # Skip empty lines and headers
        if not line:
            continue

        # Skip page numbers and headers
        if re.match(r'^\d+$', line):
            continue
        if 'SPISAK' in line.upper() or 'POGINUL' in line.upper():
            continue
        if line.startswith('Slovo') or line.startswith('SLOVO'):
            continue

        # Check if this line starts a new entry (starts with uppercase word followed by more text)
        # A new entry typically starts with an ALL CAPS surname
        starts_new_entry = bool(re.match(r'^[A-ZČĆŽŠĐ]{2,}[\s,]', line))

        if starts_new_entry:
            # Save the previous entry if exists
            if current_entry:
                parsed = parse_soldier_entry(current_entry)
                if parsed and parsed['last_name']:
                    soldiers.append(parsed)
            current_entry = line
        else:
            # Continue the previous entry
            if current_entry:
                current_entry += " " + line

    # Don't forget the last entry
    if current_entry:
        parsed = parse_soldier_entry(current_entry)
        if parsed and parsed['last_name']:
            soldiers.append(parsed)

    return soldiers


def main():
    # Path to the PDF
    pdf_path = Path("01-data/brigades/Druga Lička/spisak poginulih.pdf")

    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return

    print(f"Extracting text from {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)

    print(f"Parsing soldier entries...")
    soldiers = extract_soldiers_from_text(text)

    print(f"Found {len(soldiers)} soldiers")

    # Create DataFrame
    df = pd.DataFrame(soldiers)

    # Reorder columns to match other brigade files
    df = df[['last_name', 'middle_name', 'first_name', 'birth_year', 'additional_info']]

    # Save to CSV
    output_csv = Path("01-data/processed/druga_licka_proleterska_soldiers.csv")
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Saved to {output_csv}")

    # Show first few entries
    print("\nFirst 10 entries:")
    print(df.head(10).to_string())

    # Show some stats
    print(f"\nTotal soldiers: {len(df)}")
    print(f"With birth year: {df['birth_year'].notna().sum()}")

    return df


if __name__ == "__main__":
    main()
