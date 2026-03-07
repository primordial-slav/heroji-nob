"""
Extract PDF page positions for each soldier entry.

For each soldier in the existing JSON files, determines which PDF page
and Y coordinate they appear at. This metadata enables the website's
PDF viewer to jump directly to the soldier's entry.

Uses pdfplumber's word-level extraction (extract_words) to get precise
coordinates, then matches entries to existing soldier JSON records.
"""

import re
import json
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pdfplumber'])
    import pdfplumber


# ============================================================
# Generic word-level extraction utilities
# ============================================================

def extract_lines_with_positions(page, y_tolerance=3):
    """
    Extract text lines from a PDF page with their Y positions.

    Uses page.extract_words() to get word-level data, then groups
    words into lines based on Y coordinate proximity.

    Returns: list of dicts: {'text': str, 'top': float, 'page_height': float}
    """
    words = page.extract_words(
        x_tolerance=3,
        y_tolerance=y_tolerance,
        keep_blank_chars=True
    )

    if not words:
        return []

    page_height = float(page.height)

    # Group words into lines by 'top' proximity
    lines = []
    current_line_words = [words[0]]
    current_top = words[0]['top']

    for word in words[1:]:
        if abs(word['top'] - current_top) <= y_tolerance:
            # Same line
            current_line_words.append(word)
        else:
            # New line - save current
            # Sort words by x position
            current_line_words.sort(key=lambda w: w['x0'])
            line_text = ' '.join(w['text'] for w in current_line_words)
            avg_top = sum(w['top'] for w in current_line_words) / len(current_line_words)
            lines.append({
                'text': line_text,
                'top': avg_top,
                'x0': current_line_words[0]['x0'],
                'page_height': page_height
            })
            current_line_words = [word]
            current_top = word['top']

    # Don't forget last line
    if current_line_words:
        current_line_words.sort(key=lambda w: w['x0'])
        line_text = ' '.join(w['text'] for w in current_line_words)
        avg_top = sum(w['top'] for w in current_line_words) / len(current_line_words)
        lines.append({
            'text': line_text,
            'top': avg_top,
            'x0': current_line_words[0]['x0'],
            'page_height': page_height
        })

    return lines


def compute_end_positions(positions):
    """
    For each position, compute end_top = top of next entry on same page/column.
    This allows the highlight box to span the full entry height.
    """
    if not positions:
        return positions

    # Sort by (pdf_file, page, top) to get sequential order
    positions.sort(key=lambda p: (p.get('pdf_file', ''), p['page'], p['top']))

    for i in range(len(positions)):
        pos = positions[i]
        # Look for the next position on the same page
        if i + 1 < len(positions):
            next_pos = positions[i + 1]
            if next_pos['page'] == pos['page'] and next_pos.get('pdf_file') == pos.get('pdf_file'):
                # Only use next entry if it's reasonably close (same column or nearby)
                # For two-column layouts, next entry on same page might be in other column
                # Use it if the gap is reasonable (< 200 points)
                gap = next_pos['top'] - pos['top']
                if 0 < gap < 200:
                    pos['end_top'] = next_pos['top'] - 1
                else:
                    pos['end_top'] = pos['top'] + 30  # default ~2 lines
            else:
                pos['end_top'] = pos['top'] + 30
        else:
            pos['end_top'] = pos['top'] + 30

    return positions


def match_positions_to_soldiers(positions, soldiers_json):
    """
    Match extracted positions to existing soldier JSON records by name.
    Falls back to index-based matching only if name matching fails badly.
    """
    if not positions:
        print("  WARNING: No positions extracted!")
        return soldiers_json

    # Clear old position data
    for s in soldiers_json:
        s.pop('pdf_page', None)
        s.pop('pdf_y', None)
        s.pop('pdf_x', None)
        s.pop('pdf_y_end', None)
        s.pop('pdf_file', None)

    # Compute end positions for highlight height
    positions = compute_end_positions(positions)

    # Always use name-based matching for robustness
    return match_positions_by_name(positions, soldiers_json)


# ============================================================
# Brigade-specific extraction functions
# ============================================================

def extract_druga_licka(pdf_path, json_path):
    """Extract positions for Druga Licka Proleterska Brigada."""
    print(f"\n{'='*60}")
    print(f"DRUGA LICKA PROLETERSKA BRIGADA")
    print(f"{'='*60}")

    pdf_filename = 'druga-licka-spisak.pdf'
    positions = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}")

        for page_idx, page in enumerate(pdf.pages):
            page_num = page_idx + 1
            lines = extract_lines_with_positions(page)

            for line in lines:
                text = line['text'].strip()
                if not text:
                    continue

                # Skip page numbers and headers
                if re.match(r'^\d+$', text):
                    continue
                if 'SPISAK' in text.upper() or 'POGINUL' in text.upper():
                    continue
                if text.startswith('Slovo') or text.startswith('SLOVO'):
                    continue

                # Check if this starts a new soldier entry
                if re.match(r'^[A-ZČĆŽŠĐ]{2,}[\s,]', text):
                    positions.append({
                        'page': page_num,
                        'top': line['top'],
                        'x0': line.get('x0', 0),
                        'pdf_file': pdf_filename,
                        'text_preview': text[:80]
                    })

    print(f"  Found {len(positions)} soldier positions")

    # Load existing JSON and match
    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def extract_treca_proleterska(pdf_path, json_path):
    """Extract positions for Treca Proleterska (Sandzacka) Brigada."""
    print(f"\n{'='*60}")
    print(f"TRECA PROLETERSKA (SANDZACKA) BRIGADA")
    print(f"{'='*60}")

    pdf_filename = 'treca-proleterska-brigada.pdf'
    START_PAGE = 376
    END_PAGE = 446

    # Section headers to skip
    SECTION_HEADERS = {
        'STAB BRIGADE', 'ŠTAB BRIGADE',
        'POLITODJEL BRIGADE', 'POL1TODJEL BRIGADE',
        'BRIGADNA INTENDANTURA', 'BRIGADNI SANITET',
        'ŠTAB BATALJONA', 'STAB BATALJONA',
        'BATALJONSKA INTENDANTURA', 'BATALJONSKA INTENDANTURA I SANITET',
        'BATALJONSKI SANITET',
        'PRATEĆA ČETA', 'PRATECA CETA',
    }

    HEADER_PATTERNS = [
        r'^(PRVI|DRUGI|TREĆI|TREČI|ČETVRTI|PETI)\s+(BATALJON|ČETA)',
        r'^(STAB|ŠTAB)\s+(BRIGADE|BATALJONA)',
        r'^(POLITODJEL|POL1TODJEL)',
        r'^BRIGADN[AIO]',
        r'^BATALJONSK[AIO]',
        r'^PRATEĆ[AIO]',
        r'^\d+\.\s*(ČETA|CETA|VODA?)\b',
        r'^MINOBACAČK',
        r'^MITRALJESK',
        r'^IZVIĐAČK',
        r'^SPOJNIČK',
        r'^BOMBAŠ',
        r'^NERASPOREĐEN',
        r'^MILEŠEVSK',
        r'^BJELOPOLJSK',
        r'^NOP\b',
        r'^NAPOMENA\b',
        r'^SPISAK\s+BORACA',
        r'^NA DAN FORMIRANJA',
        r'^IZVORI\s+I\s+LITERATURA',
        r'^UKUPNO\s+\d',
        r'^Brojno\s+stanje',
        r'^NNAAZZIIVV',
        r'^U spisak boraca',
    ]

    def is_section_header(text):
        text_clean = text.strip().rstrip('*•— ')
        if text_clean.upper() in SECTION_HEADERS:
            return True
        for pattern in HEADER_PATTERNS:
            if re.match(pattern, text_clean, re.IGNORECASE):
                return True
        return False

    positions = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}, processing {START_PAGE}-{END_PAGE}")

        for page_idx in range(START_PAGE - 1, min(END_PAGE, len(pdf.pages))):
            page = pdf.pages[page_idx]
            page_num = page_idx + 1
            lines = extract_lines_with_positions(page)

            for line in lines:
                text = line['text'].strip()
                if not text:
                    continue

                # Skip page numbers
                if re.match(r'^\d{1,3}$', text):
                    continue

                # Stop at NAPOMENA
                if text.startswith('NAPOMENA'):
                    break
                if 'Brojno stanje' in text or 'UKUPNO' in text:
                    break

                # Skip section headers
                if is_section_header(text):
                    continue

                # Check if this is a soldier entry
                if re.match(r'^[A-ZČĆŽŠĐ]{2,}[\s,]', text):
                    positions.append({
                        'page': page_num,
                        'top': line['top'],
                        'x0': line.get('x0', 0),
                        'pdf_file': pdf_filename,
                        'text_preview': text[:80]
                    })

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def extract_prva_proleterska(pdf_paths, json_path):
    """Extract positions for Prva Proleterska Brigada (3 PDFs)."""
    print(f"\n{'='*60}")
    print(f"PRVA PROLETERSKA BRIGADA")
    print(f"{'='*60}")

    pdf_filenames = {
        0: 'prva-proleterska-1.pdf',
        1: 'prva-proleterska-2.pdf',
        2: 'prva-proleterska-3.pdf',
    }

    def is_new_entry(text):
        pattern1 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+)*\s+([A-ZČĆŽŠĐ]\.?\s+)*[A-ZČĆŽŠĐ][a-zčćžšđ]'
        pattern2 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+\s+([A-ZČĆŽŠĐ]\.?\s+)*[A-ZČĆŽŠĐ]{2,}\*?(\s*,|\s+[A-ZČĆŽŠĐ])'
        pattern3 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ]{2,})+\*'
        return bool(re.match(pattern1, text)) or bool(re.match(pattern2, text)) or bool(re.match(pattern3, text))

    positions = []
    found_start = False
    past_header = False

    for pdf_idx, pdf_path in enumerate(pdf_paths):
        pdf_filename = pdf_filenames[pdf_idx]
        print(f"  Processing {pdf_filename}...")

        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1

                # Use page.extract_text() for start marker detection
                # (word-level grouping may split marker text differently)
                if not found_start:
                    page_text = page.extract_text() or ''
                    if 'Spisak pripadnika' in page_text or 'spisak pripadnika' in page_text.lower():
                        found_start = True
                        print(f"    Found 'Spisak pripadnika' on page {page_num} of {pdf_filename}")
                        if '1945' in page_text:
                            past_header = True
                    else:
                        continue

                lines = extract_lines_with_positions(page)

                for line in lines:
                    text = line['text'].strip()
                    if not text:
                        continue

                    # Skip header lines until we're past the intro
                    if not past_header:
                        if '1945' in text:
                            past_header = True
                        continue

                    # Skip residual header text
                    if 'Spisak pripadnika' in text or 'spisak' in text.lower():
                        continue
                    if '1945. godine' in text:
                        continue

                    if is_new_entry(text):
                        positions.append({
                            'page': page_num,
                            'top': line['top'],
                            'x0': line.get('x0', 0),
                            'pdf_file': pdf_filename,
                            'text_preview': text[:80]
                        })

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def extract_prva_licka(pdf_path, json_path):
    """Extract positions for Prva Licka Proleterska Brigada."""
    print(f"\n{'='*60}")
    print(f"PRVA LICKA PROLETERSKA BRIGADA")
    print(f"{'='*60}")

    pdf_filename = 'prva-licka-proleterska.pdf'

    def is_new_entry(text):
        if not text or text.startswith('PAGE') or text.startswith('=='):
            return False
        if re.match(r'^\d+$', text):
            return False
        if len(text) <= 2 and text.isupper():
            return False
        pattern1 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+)*\s+([A-ZČĆŽŠĐ]\.?\s+)*[A-ZČĆŽŠĐ][a-zčćžšđ]'
        pattern2 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+\s+([A-ZČĆŽŠĐ]\.?\s+)*[A-ZČĆŽŠĐ]{2,}\*?(\s*,|\s+[A-ZČĆŽŠĐ])'
        pattern3 = r'^[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+(\s+[A-ZČĆŽŠĐ]{2,})+\*'
        return bool(re.match(pattern1, text)) or bool(re.match(pattern2, text)) or bool(re.match(pattern3, text))

    positions = []
    # The soldier list starts deep in this PDF (around page 557+ based on line 28107)
    # We need to find where it starts by looking for specific patterns

    # First pass: find the approximate start page by looking for the soldier list
    # The text file had soldier data starting at line 28107
    # Each page has roughly 50 lines, so ~ page 562
    # But let's be safe and scan from page 500
    START_SCAN = 500

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"  Total pages: {total_pages}")

        # We know from the extraction script that soldiers start at line 28107
        # of the extracted text. Let's scan pages to find the first soldier entry.
        found_soldiers = False

        for page_idx in range(START_SCAN - 1, total_pages):
            page = pdf.pages[page_idx]
            page_num = page_idx + 1

            if page_num % 50 == 0:
                print(f"  Scanning page {page_num}/{total_pages}...")

            lines = extract_lines_with_positions(page)

            for line in lines:
                text = line['text'].strip()
                if not text:
                    continue

                if is_new_entry(text):
                    found_soldiers = True
                    positions.append({
                        'page': page_num,
                        'top': line['top'],
                        'x0': line.get('x0', 0),
                        'pdf_file': pdf_filename,
                        'text_preview': text[:80]
                    })

            # If we found soldiers and then hit a page with none, we might be past the list
            # But don't break too early - there might be blank pages between

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def normalize_name(name):
    """Normalize a name for fuzzy matching: lowercase, strip diacritics, remove punctuation."""
    import unicodedata
    if not name:
        return ''
    # Lowercase
    name = name.lower().strip()
    # Strip diacritics
    nfkd = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in nfkd if not unicodedata.combining(c))
    # Remove punctuation and extra spaces
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def match_positions_by_name(positions, soldiers_json):
    """
    Match extracted PDF positions to soldiers by name instead of index.
    Used for Ljubljanska where column order differs from JSON order.
    """
    if not positions:
        print("  WARNING: No positions extracted!")
        return soldiers_json

    # Build a lookup: normalized name -> list of positions
    # Each position's text_preview starts with the soldier name
    # For brigades with father's names (genitive), the format is:
    #   "LAST_NAME Father's_gen FIRST_NAME, ..."
    # So we index by multiple keys: word[0]+word[1], word[0]+word[2], etc.
    pos_by_name = {}

    def add_pos_key(key, pos):
        if key not in pos_by_name:
            pos_by_name[key] = []
        pos_by_name[key].append(pos)

    for pos in positions:
        preview = pos['text_preview']
        parts = preview.split(',')[0].strip().split()

        if len(parts) >= 2:
            # Primary key: word[0] + word[1] (Surname + Father/First)
            add_pos_key(normalize_name(parts[0] + ' ' + parts[1]), pos)

        if len(parts) >= 3:
            # Secondary key: word[0] + word[2] (Surname + First, skipping father's genitive)
            # This handles "ALEKSIĆ Velisava LEPOSAVA" -> key "aleksic leposava"
            add_pos_key(normalize_name(parts[0] + ' ' + parts[2]), pos)

        if len(parts) == 1:
            add_pos_key(normalize_name(parts[0]), pos)

    matched = 0
    unmatched = 0

    for soldier in soldiers_json:
        # Build the lookup key from JSON soldier data
        last = soldier.get('last_name', '')
        first = soldier.get('first_name', '')
        full = soldier.get('full_name', '')

        # Try last_name + first_name
        key = normalize_name(last + ' ' + first)
        pos_list = pos_by_name.get(key)

        # Fallback: try from full_name (first two words)
        if not pos_list and full:
            full_parts = full.split()
            if len(full_parts) >= 2:
                key2 = normalize_name(full_parts[0] + ' ' + full_parts[1])
                pos_list = pos_by_name.get(key2)
                if pos_list:
                    key = key2

        if pos_list:
            # Use the first available match, then remove it to handle duplicates
            pos = pos_list.pop(0)
            if not pos_list:
                del pos_by_name[key]
            soldier['pdf_page'] = pos['page']
            soldier['pdf_y'] = round(pos['top'], 1)
            soldier['pdf_x'] = round(pos.get('x0', 0), 1)
            soldier['pdf_y_end'] = round(pos.get('end_top', pos['top'] + 30), 1)
            soldier['pdf_file'] = pos['pdf_file']
            matched += 1
        else:
            unmatched += 1

    print(f"  Name-matched: {matched}, Unmatched: {unmatched} (positions: {len(positions)}, soldiers: {len(soldiers_json)})")
    return soldiers_json


def extract_ljubljanska(pdf_path, json_path):
    """Extract positions for Ljubljanska Brigada (two-column layout)."""
    print(f"\n{'='*60}")
    print(f"LJUBLJANSKA BRIGADA (10. SNOUB)")
    print(f"{'='*60}")

    pdf_filename = 'ljubljanska-brigada.pdf'

    def is_soldier_entry(text):
        # Normal: "Surname Firstname" with uppercase first char
        if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]', text):
            return True
        # OCR fix: lowercase diacritical first char (š, ž, č, ć, đ)
        if re.match(r'^[šžčćđ][a-zčćžšđ]{2,}\s+[A-ZČĆŽŠĐ][a-zčćžšđ]', text):
            return True
        return False

    positions = []
    found_start = False

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}")

        for page_idx, page in enumerate(pdf.pages):
            page_num = page_idx + 1

            # Get word-level data for this page
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

            # Check for start marker
            page_text = page.extract_text() or ''
            if not found_start:
                if 'SEZNAM BORCEV' in page_text:
                    found_start = True
                else:
                    continue

            # Stop at table of contents
            if 'Kazalo' in page_text or 'kazalo' in page_text or 'KAZALO' in page_text:
                break

            # For two-column layout, split words into left and right columns
            left_words = [w for w in words if w['x0'] < col_boundary]
            right_words = [w for w in words if w['x0'] >= col_boundary]

            # Process each column separately
            for col_words in [left_words, right_words]:
                if not col_words:
                    continue

                # Group into lines by Y
                col_words.sort(key=lambda w: (w['top'], w['x0']))
                lines = []
                current_line = [col_words[0]]
                current_top = col_words[0]['top']

                for w in col_words[1:]:
                    if abs(w['top'] - current_top) <= 3:
                        current_line.append(w)
                    else:
                        current_line.sort(key=lambda ww: ww['x0'])
                        text = ' '.join(ww['text'] for ww in current_line)
                        avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
                        lines.append({'text': text, 'top': avg_top})
                        current_line = [w]
                        current_top = w['top']

                if current_line:
                    current_line.sort(key=lambda ww: ww['x0'])
                    text = ' '.join(ww['text'] for ww in current_line)
                    avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
                    lines.append({'text': text, 'top': avg_top})

                # Find soldier entries in this column
                for line in lines:
                    text = line['text'].strip()
                    if not text:
                        continue

                    if is_soldier_entry(text):
                        positions.append({
                            'page': page_num,
                            'top': line['top'],
                            'x0': col_words[0]['x0'],
                            'pdf_file': pdf_filename,
                            'text_preview': text[:80]
                        })

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def extract_13_proleterska(pdf_path, json_path):
    """Extract positions for 13. Proleterska Brigada 'Rade Končar' (two-column layout)."""
    print(f"\n{'='*60}")
    print(f"13. PROLETERSKA BRIGADA 'RADE KONČAR'")
    print(f"{'='*60}")

    pdf_filename = '13-proleterska-spisak.pdf'
    START_PAGE = 4
    END_PAGE = 109
    COL_BOUNDARY = 290

    def is_soldier_entry(text):
        """Check if line starts a new soldier entry (ALL CAPS last name)."""
        text = text.strip()
        if not text or len(text) <= 2:
            return False
        if re.match(r'^\d{1,4}$', text):
            return False
        match = re.match(r'^([A-ZČĆŽŠĐa-zčćžšđ\-]{2,})\s+(.+)', text)
        if not match:
            return False
        first_word = match.group(1)
        upper_count = sum(1 for c in first_word if c.isupper() or c in 'ČĆŽŠĐ')
        return len(first_word) > 0 and upper_count / len(first_word) >= 0.7 and upper_count >= 2

    positions = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}, processing {START_PAGE}-{END_PAGE}")

        for page_idx in range(START_PAGE - 1, min(END_PAGE, len(pdf.pages))):
            page = pdf.pages[page_idx]
            page_num = page_idx + 1

            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=True
            )

            if not words:
                continue

            left_words = [w for w in words if w['x0'] < COL_BOUNDARY]
            right_words = [w for w in words if w['x0'] >= COL_BOUNDARY]

            for col_words in [left_words, right_words]:
                if not col_words:
                    continue

                # Group into lines by Y
                col_words.sort(key=lambda w: (w['top'], w['x0']))
                lines = []
                current_line = [col_words[0]]
                current_top = col_words[0]['top']

                for w in col_words[1:]:
                    if abs(w['top'] - current_top) <= 4:
                        current_line.append(w)
                    else:
                        current_line.sort(key=lambda ww: ww['x0'])
                        text = ' '.join(ww['text'] for ww in current_line)
                        avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
                        lines.append({'text': text, 'top': avg_top, 'x0': current_line[0]['x0']})
                        current_line = [w]
                        current_top = w['top']

                if current_line:
                    current_line.sort(key=lambda ww: ww['x0'])
                    text = ' '.join(ww['text'] for ww in current_line)
                    avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
                    lines.append({'text': text, 'top': avg_top, 'x0': current_line[0]['x0']})

                for line in lines:
                    text = line['text'].strip()
                    if not text:
                        continue

                    if is_soldier_entry(text):
                        positions.append({
                            'page': page_num,
                            'top': line['top'],
                            'x0': line.get('x0', 0),
                            'pdf_file': pdf_filename,
                            'text_preview': text[:80]
                        })

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def extract_2_dalmatinska(pdf_path, json_path):
    """Extract positions for 2. Dalmatinska Proleterska Brigada (numbered entries, single column)."""
    print(f"\n{'='*60}")
    print(f"2. DALMATINSKA PROLETERSKA BRIGADA")
    print(f"{'='*60}")

    pdf_filename = '2-dalmatinska-proleterska.pdf'
    START_PAGE = 2
    END_PAGE = 197

    positions = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}, processing {START_PAGE}-{END_PAGE}")

        for page_idx in range(START_PAGE - 1, min(END_PAGE, len(pdf.pages))):
            page = pdf.pages[page_idx]
            page_num = page_idx + 1
            lines = extract_lines_with_positions(page)

            for line in lines:
                text = line['text'].strip()
                if not text:
                    continue

                # Skip page numbers and headers
                if re.match(r'^\d{1,3}$', text):
                    continue
                if text.startswith('POPIS BORACA 2. DALMATINS'):
                    continue

                # Entry starts with a number followed by period: "1. LASTNAME..."
                entry_match = re.match(r'^\d{1,4}\.\s+(.+)', text)
                if entry_match:
                    name_part = entry_match.group(1)
                    positions.append({
                        'page': page_num,
                        'top': line['top'],
                        'x0': line.get('x0', 0),
                        'pdf_file': pdf_filename,
                        'text_preview': name_part[:80]
                    })

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def extract_4_splitska(pdf_path, json_path):
    """Extract positions for 4. Splitska Udarna Brigada (numbered entries, two sections)."""
    print(f"\n{'='*60}")
    print(f"4. SPLITSKA UDARNA BRIGADA")
    print(f"{'='*60}")

    pdf_filename = '4-splitska-brigada.pdf'
    # Section 1: Poginuli (killed) pages 4-22
    # Section 2: Preživjeli (survivors) pages 23-110
    START_PAGE = 4
    END_PAGE = 110

    positions = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}, processing {START_PAGE}-{END_PAGE}")

        for page_idx in range(START_PAGE - 1, min(END_PAGE, len(pdf.pages))):
            page = pdf.pages[page_idx]
            page_num = page_idx + 1
            lines = extract_lines_with_positions(page)

            for line in lines:
                text = line['text'].strip()
                if not text:
                    continue

                # Skip page numbers and headers
                if re.match(r'^\d{1,3}$', text):
                    continue
                if 'POGINULI' in text and 'UMRLI' in text:
                    continue
                if text.startswith('POPIS PREŽIVJELIH'):
                    continue

                # Entry starts with a number followed by period: "1. LASTNAME..."
                entry_match = re.match(r'^\d{1,4}\.\s+(.+)', text)
                if entry_match:
                    name_part = entry_match.group(1)
                    positions.append({
                        'page': page_num,
                        'top': line['top'],
                        'x0': line.get('x0', 0),
                        'pdf_file': pdf_filename,
                        'text_preview': name_part[:80]
                    })

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def extract_prva_vojvodjanska(pdf_path, json_path):
    """Extract positions for Prva Vojvođanska Brigada (two-column, no numbers)."""
    print(f"\n{'='*60}")
    print(f"PRVA VOJVOĐANSKA BRIGADA")
    print(f"{'='*60}")

    pdf_filename = 'prva-vojvodjanska.pdf'
    START_PAGE = 2
    END_PAGE = 33
    COL_SPLIT_X = 195

    positions = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}, processing {START_PAGE}-{END_PAGE}")

        for page_idx in range(START_PAGE - 1, min(END_PAGE, len(pdf.pages))):
            page = pdf.pages[page_idx]
            page_num = page_idx + 1

            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=True
            )

            if not words:
                continue

            left_words = [w for w in words if w['x0'] < COL_SPLIT_X]
            right_words = [w for w in words if w['x0'] >= COL_SPLIT_X]

            for col_words, col_start_x in [(left_words, 47), (right_words, 200)]:
                if not col_words:
                    continue

                # Group into lines by Y
                col_words.sort(key=lambda w: (w['top'], w['x0']))
                lines = []
                current_line = [col_words[0]]
                current_top = col_words[0]['top']

                for w in col_words[1:]:
                    if abs(w['top'] - current_top) <= 4:
                        current_line.append(w)
                    else:
                        current_line.sort(key=lambda ww: ww['x0'])
                        text = ' '.join(ww['text'] for ww in current_line)
                        avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
                        lines.append({'text': text, 'top': avg_top, 'x0': current_line[0]['x0']})
                        current_line = [w]
                        current_top = w['top']

                if current_line:
                    current_line.sort(key=lambda ww: ww['x0'])
                    text = ' '.join(ww['text'] for ww in current_line)
                    avg_top = sum(ww['top'] for ww in current_line) / len(current_line)
                    lines.append({'text': text, 'top': avg_top, 'x0': current_line[0]['x0']})

                for line in lines:
                    text = line['text'].strip()
                    if not text:
                        continue

                    # Skip headers and page numbers
                    if 'SPISAK BORACA' in text or 'VOJVOĐANSKE' in text or 'BRIGADE' in text:
                        continue
                    if re.match(r'^\d{1,3}$', text):
                        continue

                    # Detect new entry: line starts near column margin AND first word is capitalized
                    x_near_margin = abs(line['x0'] - col_start_x) < 15
                    if x_near_margin:
                        first_word = text.split()[0] if text.split() else ''
                        if first_word and first_word[0].isupper() and len(first_word) > 1:
                            cont_words = {'Sahranjen', 'Sahra', 'Poginuo', 'Pogi', 'Umro', 'Mjesto', 'Mesto', 'Ranjen'}
                            if not any(first_word.startswith(cw) for cw in cont_words):
                                positions.append({
                                    'page': page_num,
                                    'top': line['top'],
                                    'x0': line.get('x0', 0),
                                    'pdf_file': pdf_filename,
                                    'text_preview': text[:80]
                                })

    print(f"  Found {len(positions)} soldier positions")

    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    print(f"  Existing JSON has {len(soldiers)} soldiers")
    soldiers = match_positions_to_soldiers(positions, soldiers)

    return soldiers


def save_updated_json(soldiers, output_path):
    """Save soldiers with position metadata to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {output_path}")


# ============================================================
# Main
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Extract PDF positions for soldier entries')
    parser.add_argument('--brigade', type=str, default='all',
                       choices=['druga-licka', 'treca', 'prva-proleterska', 'prva-licka', 'ljubljanska', '13-proleterska', '2-dalmatinska', '4-splitska', 'prva-vojvodjanska', 'all'],
                       help='Which brigade to process (default: all)')
    parser.add_argument('--sample', type=int, default=0,
                       help='Print N sample positions for verification')
    args = parser.parse_args()

    # Base paths - resolve to absolute
    base_dir = Path(__file__).resolve().parent.parent
    pdf_dir = base_dir / 'website' / 'public' / 'pdfs'
    json_dir = base_dir / 'website' / 'public'

    print(f"Base dir: {base_dir}")
    print(f"PDF dir: {pdf_dir}")
    print(f"JSON dir: {json_dir}")

    brigades = {
        'druga-licka': {
            'pdf': pdf_dir / 'druga-licka-spisak.pdf',
            'json': json_dir / 'druga-licka-soldiers.json',
            'func': lambda p, j: extract_druga_licka(p, j),
        },
        'treca': {
            'pdf': pdf_dir / 'treca-proleterska-brigada.pdf',
            'json': json_dir / 'treca-proleterska-soldiers.json',
            'func': lambda p, j: extract_treca_proleterska(p, j),
        },
        'prva-proleterska': {
            'pdf': [
                pdf_dir / 'prva-proleterska-1.pdf',
                pdf_dir / 'prva-proleterska-2.pdf',
                pdf_dir / 'prva-proleterska-3.pdf',
            ],
            'json': json_dir / 'prva-proleterska-soldiers.json',
            'func': lambda p, j: extract_prva_proleterska(p, j),
        },
        'prva-licka': {
            'pdf': pdf_dir / 'prva-licka-proleterska.pdf',
            'json': json_dir / 'soldiers.json',
            'func': lambda p, j: extract_prva_licka(p, j),
        },
        'ljubljanska': {
            'pdf': pdf_dir / 'ljubljanska-brigada.pdf',
            'json': json_dir / 'ljubljanska-soldiers.json',
            'func': lambda p, j: extract_ljubljanska(p, j),
        },
        '13-proleterska': {
            'pdf': pdf_dir / '13-proleterska-spisak.pdf',
            'json': json_dir / '13-proleterska-soldiers.json',
            'func': lambda p, j: extract_13_proleterska(p, j),
        },
        '2-dalmatinska': {
            'pdf': pdf_dir / '2-dalmatinska-proleterska.pdf',
            'json': json_dir / '2-dalmatinska-soldiers.json',
            'func': lambda p, j: extract_2_dalmatinska(p, j),
        },
        '4-splitska': {
            'pdf': pdf_dir / '4-splitska-brigada.pdf',
            'json': json_dir / '4-splitska-soldiers.json',
            'func': lambda p, j: extract_4_splitska(p, j),
        },
        'prva-vojvodjanska': {
            'pdf': pdf_dir / 'prva-vojvodjanska.pdf',
            'json': json_dir / 'prva-vojvodjanska-soldiers.json',
            'func': lambda p, j: extract_prva_vojvodjanska(p, j),
        },
    }

    to_process = [args.brigade] if args.brigade != 'all' else list(brigades.keys())

    for brigade_key in to_process:
        config = brigades[brigade_key]

        # Check files exist
        pdf_paths = config['pdf'] if isinstance(config['pdf'], list) else [config['pdf']]
        for p in pdf_paths:
            if not p.exists():
                print(f"  ERROR: PDF not found: {p}")
                continue

        if not config['json'].exists():
            print(f"  ERROR: JSON not found: {config['json']}")
            continue

        # Run extraction
        if isinstance(config['pdf'], list):
            soldiers = config['func'](config['pdf'], config['json'])
        else:
            soldiers = config['func'](config['pdf'], config['json'])

        # Print samples if requested
        if args.sample > 0:
            print(f"\n  Sample entries with positions:")
            count = 0
            for s in soldiers:
                if 'pdf_page' in s and count < args.sample:
                    print(f"    {s.get('full_name', s['last_name'])} → page {s['pdf_page']}, y={s['pdf_y']}")
                    count += 1

        # Save updated JSON
        save_updated_json(soldiers, config['json'])

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == '__main__':
    main()
