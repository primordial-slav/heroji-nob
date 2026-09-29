"""
Parser for 2. Dalmatinska Proleterska Udarna Brigada soldier list.

Source: znaci.org/00001/33_25.pdf (197 pages, 5543 numbered entries)
Format: Numbered entries, single column.
  N. LASTNAME FIRSTNAME, Father_genitive. birth_info. place. nationality, ...

Entry boundaries: each entry starts with a number (1-5543) followed by period.
Father's name is between the comma and first period.
"""

import sys
import re
import json
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')
from scripts.soldier_id_utils import assign_ids_to_soldiers

PDF_FILE = 'website/public/pdfs/2-dalmatinska-proleterska.pdf'
OUTPUT_FILE = 'website/public/2-dalmatinska-soldiers.json'
BRIGADE_CODE = 7

START_PAGE = 2
END_PAGE = 197

# "SURNAME FIRST [(Nick)], Father[-Name] [(nick)]" followed by ".", "," or a date.
# No period or digit may come before the comma (else that comma is inside the biography).
_U, _L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FATHER_RE = re.compile(
    rf"^(?P<name>[^,.\d]{{3,80}}?)\s*,\s*(?P<father>[{_U}][{_L}]+(?:-[{_U}][{_L}]+)?)"
    rf"\s*(?:\([^)]*\))?\s*(?=[.,]|\s+\d)")
# Words the book prints in the father's slot that are not names (entries with no father)
NOT_FATHERS = {'Talijan', 'Hrvat', 'Poginuo', 'Split', 'Šibenik', 'Sinj', 'Trogir', 'Solin', 'Muć',
               'Zagvozd', 'Makovac', 'Jesenice', 'Zrmanja', 'Ruišta', 'Ivoševci', 'Mrcine', 'Jeklenica',
               'Avieno', 'Nedima', 'Orličev'}


def extract_entries_from_pdf(pdf_path):
    """Extract raw text and split into numbered entries."""
    pdf = pdfplumber.open(pdf_path)

    all_text = ""
    for i in range(START_PAGE - 1, min(END_PAGE, len(pdf.pages))):
        page_text = pdf.pages[i].extract_text()
        if page_text:
            # Remove page headers like "POPIS BORACA 2. DALMATINSKE..."
            lines = page_text.split('\n')
            filtered = []
            for line in lines:
                if line.strip().startswith('POPIS BORACA 2. DALMATINS'):
                    continue
                # Skip page numbers (standalone digits at end)
                if re.match(r'^\d{1,3}$', line.strip()):
                    continue
                filtered.append(line)
            all_text += '\n'.join(filtered) + "\n"

    pdf.close()

    # Split on entry numbers: "N. LASTNAME" where N is 1-5999
    # Entry number is at line start, followed by period, space, then uppercase name
    entry_pattern = re.compile(r'(?:^|\n)\s*(\d{1,4})\.\s+([A-ZČĆŽŠĐ])')

    entries = []
    matches = list(entry_pattern.finditer(all_text))

    for idx, match in enumerate(matches):
        entry_num = int(match.group(1))
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(all_text)

        raw = all_text[start:end].strip()
        # Remove leading number
        raw = re.sub(r'^\d{1,4}\.\s*', '', raw)
        # Join multi-line
        raw = re.sub(r'\n\s*', ' ', raw)
        raw = re.sub(r'\s+', ' ', raw).strip()

        entries.append({
            'entry_num': entry_num,
            'raw_text': raw,
        })

    return entries


def parse_entry(entry):
    """
    Parse entry like:
      ABRAMOVIĆ BOŽO, Petra. Gornje Polje, Nikšić. Crnogorac, zemljoradnik...
      ABRAMOVIĆ JOZO, Mate. 18. 10 1914. Biorine, Imotski. Hrvat...

    Structure: LASTNAME FIRSTNAME, Father. [birth_date.] rest...
    """
    text = entry['raw_text']

    last_name = ''
    first_name = ''
    fathers_name = ''
    additional_info = ''

    # The first comma ends the name only when nothing but the name comes before it and a
    # father's name follows ("ALFIREV STIPE, Grge. 1914. ..."). Otherwise the book prints no
    # father and the comma belongs to the biography ("BARADA TOMO. Seget Donji, Trogir. ...",
    # "BELAMARIĆ MARICA, žena Jere. 1902. ..."), which must stay in additional_info.
    father_match = FATHER_RE.match(text)
    if father_match and father_match.group('father') not in NOT_FATHERS:
        name_part = father_match.group('name')
        fathers_name = father_match.group('father')
        # drop a nickname printed after the father, and the separator before the bio
        additional_info = text[father_match.end():].lstrip(' .,')
    else:
        name_end = re.match(r'^[^.,]*', text).end()
        name_part = text[:name_end]
        additional_info = text[name_end:].lstrip(' .,')

    # Name part: "LASTNAME FIRSTNAME" or "LASTNAME-LASTNAME FIRSTNAME"
    # Sometimes: "B AGO VIĆ ANTUN" (spaces in OCR). Nicknames "(Dane)" are not kept.
    name_words = re.sub(r'\s*\([^)]*\)', '', name_part).split()
    if len(name_words) >= 2:
        # Last name words are ALL CAPS, first name starts with uppercase then lowercase
        last_parts = []
        first_parts = []
        found_first = False
        for w in name_words:
            if not found_first and (w.isupper() or is_ocr_uppercase(w)):
                last_parts.append(w)
            else:
                found_first = True
                first_parts.append(w)

        if first_parts:
            last_name = ' '.join(last_parts)
            first_name = ' '.join(first_parts)
        else:
            # All words look uppercase - take last word as first name
            last_name = ' '.join(name_words[:-1])
            first_name = name_words[-1]
    elif len(name_words) == 1:
        last_name = name_words[0]

    # Clean up names
    last_name = title_case_name(last_name)
    first_name = title_case_name(first_name)
    fathers_name = title_case_name(fathers_name)

    # Extract birth year from additional_info
    # Birth year/date is always the FIRST thing in additional_info
    # Patterns: "1924. Ljubostinje..." or "18. 10 1914. Biorine..." or "Gornje Polje..."
    birth_year = ''

    # Try full date at start: "D. M. YYYY" or "DD. MM. YYYY"
    date_match = re.match(r'^\s*\d{1,2}\.\s*\d{1,2}\.?\s*(1[89]\d{2})', additional_info)
    if date_match:
        birth_year = date_match.group(1)
    else:
        # Try standalone year at start: "1924." or "1924,"
        year_match = re.match(r'^\s*(1[89]\d{2})(?:\.|,|\s)', additional_info)
        if year_match:
            birth_year = year_match.group(1)

    full_name = f"{last_name} {first_name}".strip()

    # The printed (genitive) father goes in middle_name, as in the other parsers:
    # normalize_all_json derives the nominative fathers_name from it.
    return {
        'last_name': last_name,
        'first_name': first_name,
        'middle_name': fathers_name,
        'fathers_name': fathers_name,
        'full_name': full_name,
        'additional_info': additional_info,
        'birth_year': birth_year,
    }


def is_ocr_uppercase(word):
    """Check if word is mostly uppercase (handles OCR errors like 'VIĆ')."""
    if len(word) <= 1:
        return True
    upper_count = sum(1 for c in word if c.isupper())
    return upper_count / len(word) >= 0.6


def title_case_name(name):
    """Convert ALL CAPS to title case, handling diacritics and hyphens."""
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
            elif word.startswith('(') and len(word) > 2:
                # Handle (JAKE) -> (Jake)
                titled.append('(' + word[1].upper() + word[2:].lower())
            else:
                titled.append(word[0].upper() + word[1:].lower())
        result.append(' '.join(titled))

    return '-'.join(result)


def main():
    print(f"Parsing {PDF_FILE}...")
    entries = extract_entries_from_pdf(PDF_FILE)
    print(f"Found {len(entries)} numbered entries")

    soldiers = []
    for entry in entries:
        soldier = parse_entry(entry)
        soldiers.append(soldier)

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
