"""
Template Parser for Brigade Books
=================================

Copy this file and adapt for each new book.

Usage:
    python pipeline/01_parsers/new_brigade.py

Output:
    pipeline/workspaces/{brigade}/01_raw_lines.xlsx
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import re
import pandas as pd
from pathlib import Path

# === CONFIGURE THESE ===
BRIGADE_NAME = "new_brigade"  # Workspace folder name
SOURCE_FILE = f"pipeline/workspaces/{BRIGADE_NAME}/source/source.txt"  # Or .pdf
# ========================

WORKSPACE = Path(f"pipeline/workspaces/{BRIGADE_NAME}")
OUTPUT_FILE = WORKSPACE / "01_raw_lines.xlsx"


def parse_source():
    """
    Parse the source file and extract soldier lines.

    Adapt this function for each book's specific format.
    """
    source_path = Path(SOURCE_FILE)

    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        print(f"Please add your source file to: {WORKSPACE / 'source/'}")
        return []

    # Read source (adapt based on file type)
    if source_path.suffix == '.txt':
        text = source_path.read_text(encoding='utf-8')
    elif source_path.suffix == '.pdf':
        # You'll need: pip install pypdf2 or pdfplumber
        # import pdfplumber
        # with pdfplumber.open(source_path) as pdf:
        #     text = '\n'.join(page.extract_text() for page in pdf.pages)
        raise NotImplementedError("Add PDF parsing code here")
    else:
        raise ValueError(f"Unknown file type: {source_path.suffix}")

    # === PARSING LOGIC ===
    # Adapt this section for each book's format

    lines = []

    # Example: Split by numbered entries
    # Pattern: "123. LASTNAME Name..."
    pattern = r'^\d+\.\s+'

    # Split text into entries
    entries = re.split(pattern, text, flags=re.MULTILINE)

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        # Clean up the entry
        # Remove extra whitespace, fix line breaks
        entry = ' '.join(entry.split())

        # Skip obvious non-soldier lines
        if len(entry) < 10:  # Too short
            continue
        if entry.startswith(('Page ', 'Stranica ', '---')):  # Headers
            continue

        lines.append(entry)

    return lines


def main():
    print("=" * 60)
    print(f"PARSING: {BRIGADE_NAME}")
    print("=" * 60)

    # Ensure workspace exists
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "source").mkdir(exist_ok=True)

    # Parse
    lines = parse_source()

    if not lines:
        print("No lines extracted. Check your parser configuration.")
        return

    print(f"Extracted {len(lines)} lines")

    # Preview
    print("\nFirst 5 lines:")
    for i, line in enumerate(lines[:5]):
        preview = line[:80] + "..." if len(line) > 80 else line
        print(f"  {i+1}. {preview}")

    # Save to Excel
    df = pd.DataFrame({'raw_line': lines})
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")

    print("\nNext step:")
    print(f"  python pipeline/02_ai_validate.py --workspace {BRIGADE_NAME}")


if __name__ == "__main__":
    main()
