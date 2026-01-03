import re
import csv
import json
import sys
from pathlib import Path

# Set UTF-8 encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

def is_new_entry(line):
    """
    Check if a line starts a new soldier entry.
    A new entry starts with ALL CAPS LASTNAME followed by a name.
    """
    line = line.strip()

    # Skip empty lines, page markers, numbers
    if not line or line.startswith('PAGE') or line.startswith('=='):
        return False

    if re.match(r'^\d+$', line):
        return False

    # Single letter section headers
    if len(line) <= 2 and line.isupper():
        return False

    # Check if it starts with all-caps word (last name)
    # Should be all caps, at least 2 chars, followed by space and a capitalized word (first name)
    pattern = r'^[A-ZČĆŽŠĐ]{2,}(\s+[A-ZČĆŽŠĐ]{2,})*\s+[A-ZČĆŽŠĐ][a-zčćžšđ]'
    return bool(re.match(pattern, line))


def parse_soldier_entry(entry_text):
    """
    Parse a complete soldier entry (possibly from multiple lines) into components.

    Format: LASTNAME [MiddleName] Firstname, additional info

    Returns: dict with 'last_name', 'middle_name', 'first_name', 'additional_info'
    """
    entry_text = entry_text.strip()

    if not entry_text:
        return None

    # Try to split by comma first
    if ',' in entry_text:
        name_part, additional_info = entry_text.split(',', 1)
        additional_info = additional_info.strip()
    else:
        # No comma, so no additional info
        name_part = entry_text
        additional_info = ''

    # Split name_part into components
    # Format: LASTNAME [MiddleName(s)] FirstName
    parts = name_part.split()

    if len(parts) == 0:
        return None
    elif len(parts) == 1:
        # Only last name
        return {
            'last_name': parts[0],
            'middle_name': '',
            'first_name': '',
            'additional_info': additional_info
        }
    elif len(parts) == 2:
        # Last name and first name only
        return {
            'last_name': parts[0],
            'middle_name': '',
            'first_name': parts[1],
            'additional_info': additional_info
        }
    else:
        # Last name, middle name(s), and first name
        # parts[0] = last name
        # parts[1:-1] = middle name(s) (patronymic, etc.)
        # parts[-1] = first name
        return {
            'last_name': parts[0],
            'middle_name': ' '.join(parts[1:-1]),
            'first_name': parts[-1],
            'additional_info': additional_info
        }


def extract_soldiers_from_file(input_path, start_line=28107, end_line=46300):
    """
    Extract soldier entries from the text file, handling multi-line entries.

    Args:
        input_path: Path to the extracted text file
        start_line: Line number where soldier list starts (default: 28107)
        end_line: Line number where soldier list ends (approximate)

    Returns:
        List of soldier dictionaries
    """
    soldiers = []

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Processing lines {start_line} to {end_line}...")

    current_entry = ""

    for i, line in enumerate(lines[start_line-1:end_line], start=start_line):
        line = line.strip()

        # Skip empty lines and page markers
        if not line or line.startswith('==') or re.match(r'^\d+$', line):
            continue

        # Skip PAGE markers
        if line.startswith('PAGE'):
            continue

        # Check if this is a new entry
        if is_new_entry(line):
            # Save previous entry if exists
            if current_entry:
                soldier = parse_soldier_entry(current_entry)
                if soldier:
                    soldiers.append(soldier)

                    # Print progress every 1000 entries
                    if len(soldiers) % 1000 == 0:
                        print(f"Processed {len(soldiers)} soldiers...")

            # Start new entry
            current_entry = line
        else:
            # Continuation of previous entry
            if current_entry:
                current_entry += " " + line

    # Don't forget the last entry
    if current_entry:
        soldier = parse_soldier_entry(current_entry)
        if soldier:
            soldiers.append(soldier)

    return soldiers


def save_to_csv(soldiers, output_path):
    """Save soldiers list to CSV file with UTF-8 BOM for Excel compatibility."""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['last_name', 'middle_name', 'first_name', 'additional_info'])
        writer.writeheader()
        writer.writerows(soldiers)

    print(f"Saved {len(soldiers)} soldiers to CSV: {output_path}")


def save_to_json(soldiers, output_path):
    """Save soldiers list to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(soldiers)} soldiers to JSON: {output_path}")


if __name__ == "__main__":
    # Paths
    input_file = Path("../01-data/processed/extracted_text.txt")
    output_csv = Path("../01-data/processed/soldiers.csv")
    output_json = Path("../01-data/processed/soldiers.json")

    print("Extracting soldier names from text file...")
    soldiers = extract_soldiers_from_file(input_file)

    print(f"\nTotal soldiers extracted: {len(soldiers)}")

    # Show first few entries as examples
    print("\nFirst 10 entries:")
    for i, soldier in enumerate(soldiers[:10], 1):
        middle = f" ({soldier['middle_name']})" if soldier['middle_name'] else ""
        info_preview = soldier['additional_info'][:60] if soldier['additional_info'] else "(no info)"
        print(f"{i}. {soldier['last_name']}{middle} {soldier['first_name']}")
        print(f"   {info_preview}...")

    # Save to both formats
    save_to_csv(soldiers, output_csv)
    save_to_json(soldiers, output_json)

    print("\nDone!")
