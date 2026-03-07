"""
Parser for 4. Splitska Udarna Brigada soldier list.

Source: znaci.org/00001/89_15.pdf (112 pages)
Format: Numbered entries, single column, two sections:
  - Pages 4-22:  POGINULI (killed) - numbered 1-533
  - Pages 23-110: PREŽIVJELI (survivors) - numbered 1-~3500

Entry format: N. LASTNAME (FATHER) FIRSTNAME, r. year, place, unit, role, fate;
Father's name in parentheses within the name part.
"""

import sys
import re
import json
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')
from scripts.soldier_id_utils import assign_ids_to_soldiers

PDF_FILE = 'website/public/pdfs/4-splitska-brigada.pdf'
OUTPUT_FILE = 'website/public/4-splitska-soldiers.json'
BRIGADE_CODE = 8

# Section boundaries (1-indexed pages)
POGINULI_START = 4
POGINULI_END = 22
PREZIVJELI_START = 23
PREZIVJELI_END = 110


def extract_text_for_pages(pdf, start_page, end_page):
    """Extract and clean text from a page range."""
    all_text = ""
    for i in range(start_page - 1, min(end_page, len(pdf.pages))):
        text = pdf.pages[i].extract_text()
        if text:
            lines = text.split('\n')
            filtered = []
            for line in lines:
                # Skip section headers
                if 'POGINULI' in line and 'UMRLI' in line:
                    continue
                if line.strip().startswith('POPIS PREŽIVJELIH'):
                    continue
                # Skip standalone page numbers
                if re.match(r'^\d{1,3}$', line.strip()):
                    continue
                filtered.append(line)
            all_text += '\n'.join(filtered) + "\n"
    return all_text


def split_into_entries(text):
    """Split text into numbered entries."""
    # Entries start with "N. LASTNAME" where N is a number
    entry_pattern = re.compile(r'(?:^|\n)\s*(\d{1,4})\.\s+([A-ZČĆŽŠĐ~])')

    entries = []
    matches = list(entry_pattern.finditer(text))

    for idx, match in enumerate(matches):
        entry_num = int(match.group(1))
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)

        raw = text[start:end].strip()
        raw = re.sub(r'^\d{1,4}\.\s*', '', raw)
        raw = re.sub(r'\n\s*', ' ', raw)
        raw = re.sub(r'\s+', ' ', raw).strip()
        # Remove trailing semicolons
        raw = raw.rstrip(';').strip()

        entries.append({
            'entry_num': entry_num,
            'raw_text': raw,
        })

    return entries


def parse_entry(entry):
    """
    Parse entry like:
      AFRIC (MARINA) ANTE, r. 1927, K. Kambelovac, Split, poginuo 31. 5. 1944
      ACALIJA DUŠAN, r. ..., K. Štafilić, Split, borac, 3. bat.
      ~BAKULJAS MIRA, r .., 3. bat., bolničarka
    """
    text = entry['raw_text']

    # Remove leading ~ or other markers
    text = re.sub(r'^[~\-\*]+\s*', '', text)

    last_name = ''
    first_name = ''
    fathers_name = ''
    additional_info = ''

    # Split at ", r." or ", r " which separates name from data
    r_match = re.search(r',\s*r\.?\s', text)
    if r_match:
        name_part = text[:r_match.start()].strip()
        additional_info = text[r_match.end():].strip()
    else:
        # No "r." marker - try first comma
        comma_idx = text.find(',')
        if comma_idx > 0:
            name_part = text[:comma_idx].strip()
            additional_info = text[comma_idx + 1:].strip()
        else:
            name_part = text
            additional_info = ''

    # Extract father's name from parentheses in name_part
    # e.g. "AFRIC (MARINA) ANTE" -> last=AFRIC, father=MARINA, first=ANTE
    paren_match = re.search(r'\(([^)]+)\)', name_part)
    if paren_match:
        fathers_name = paren_match.group(1).strip()
        name_part = re.sub(r'\s*\([^)]+\)\s*', ' ', name_part).strip()

    # Split remaining name into last name (ALL CAPS) and first name
    words = name_part.split()
    if len(words) >= 2:
        # Find boundary between ALL CAPS last name and first name
        last_parts = []
        first_parts = []
        found_first = False
        for w in words:
            if not found_first and (w.isupper() or is_ocr_uppercase(w)):
                last_parts.append(w)
            else:
                found_first = True
                first_parts.append(w)

        if first_parts:
            last_name = ' '.join(last_parts)
            first_name = ' '.join(first_parts)
        else:
            last_name = ' '.join(words[:-1])
            first_name = words[-1]
    elif len(words) == 1:
        last_name = words[0]

    # Title case
    last_name = title_case_name(last_name)
    first_name = title_case_name(first_name)
    fathers_name = title_case_name(fathers_name)

    # Extract birth year: the year right after "r." is birth year
    # additional_info starts after "r. " so birth year is at the very beginning
    # e.g. "1927, K. Kambelovac" or "..., K. Štafilić" (no birth year)
    birth_year = ''
    # Birth year is the first thing in additional_info if it's a 4-digit year
    clean_start = additional_info.lstrip('. ,')
    year_match = re.match(r'^(1[89]\d{2})\b', clean_start)
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


def is_ocr_uppercase(word):
    """Check if word is mostly uppercase."""
    if len(word) <= 1:
        return True
    upper = sum(1 for c in word if c.isupper())
    return upper / len(word) >= 0.6


def title_case_name(name):
    """Convert ALL CAPS to title case."""
    if not name:
        return name
    parts = name.split('-')
    result = []
    for part in parts:
        words = part.split()
        titled = []
        for word in words:
            if len(word) <= 1:
                titled.append(word.upper())
            else:
                titled.append(word[0].upper() + word[1:].lower())
        result.append(' '.join(titled))
    return '-'.join(result)


def main():
    print(f"Parsing {PDF_FILE}...")
    pdf = pdfplumber.open(PDF_FILE)

    # Parse both sections
    print("Extracting poginuli (killed) section...")
    pog_text = extract_text_for_pages(pdf, POGINULI_START, POGINULI_END)
    pog_entries = split_into_entries(pog_text)
    print(f"  Found {len(pog_entries)} entries")

    print("Extracting preživjeli (survivors) section...")
    prez_text = extract_text_for_pages(pdf, PREZIVJELI_START, PREZIVJELI_END)
    prez_entries = split_into_entries(prez_text)
    print(f"  Found {len(prez_entries)} entries")

    pdf.close()

    # Parse all entries
    soldiers = []
    for entry in pog_entries:
        soldier = parse_entry(entry)
        soldiers.append(soldier)

    for entry in prez_entries:
        soldier = parse_entry(entry)
        soldiers.append(soldier)

    # Assign IDs
    soldiers = assign_ids_to_soldiers(soldiers, BRIGADE_CODE)

    # Print samples
    print(f"\nFirst 10 (poginuli):")
    for s in soldiers[:10]:
        print(f"  {s['soldier_id']}: {s['full_name']}, father: {s['fathers_name']}, "
              f"birth: {s['birth_year']}, info: {s['additional_info'][:80]}")

    pog_count = len(pog_entries)
    print(f"\nFirst 5 (preživjeli):")
    for s in soldiers[pog_count:pog_count + 5]:
        print(f"  {s['soldier_id']}: {s['full_name']}, father: {s['fathers_name']}, "
              f"birth: {s['birth_year']}, info: {s['additional_info'][:80]}")

    # Stats
    with_birth = sum(1 for s in soldiers if s['birth_year'])
    with_father = sum(1 for s in soldiers if s['fathers_name'])
    empty_first = sum(1 for s in soldiers if not s['first_name'])
    print(f"\nTotal: {len(soldiers)} soldiers ({len(pog_entries)} killed + {len(prez_entries)} survivors)")
    print(f"With birth year: {with_birth} ({100*with_birth/len(soldiers):.1f}%)")
    print(f"With father's name: {with_father} ({100*with_father/len(soldiers):.1f}%)")
    print(f"Empty first name: {empty_first}")

    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
