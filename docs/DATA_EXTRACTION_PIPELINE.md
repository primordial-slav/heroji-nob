# Data Extraction Pipeline

This document describes our standardized pipeline for extracting soldier data from historical source books and importing it into the main database.

## Overview

```
Source Book (PDF/Scan) → Stage 1 → Stage 2 → Stage 3 → Stage 4 → Database
                         Parse     Validate   Extract   Review    Import
```

## Pipeline Stages

### Stage 1: Raw Parsing
**Goal:** Convert source material into line-by-line text (one soldier per line)

- **Input:** PDF, scanned images, or OCR text
- **Output:** `01_raw_lines.xlsx` with single column `raw_line`
- **Script:** Book-specific parser (may reuse patterns from previous books)
- **Human effort:** High (each book has different format)

**Output format:**
| raw_line |
|----------|
| ADAMOVIĆ Petra MILAN, rođ. 1920, s. Korenica... |
| BABIĆ Marka JOVO, rođ. 1918, s. Bunić... |

### Stage 2: AI Validation
**Goal:** Verify each line contains exactly ONE soldier (no merges, splits, or garbage)

- **Input:** `01_raw_lines.xlsx`
- **Output:** `02_validated_lines.xlsx` with validation results
- **Script:** `pipeline/02_ai_validate.py` (reusable)
- **Batch size:** 50 lines per API call
- **Human effort:** Low (review flagged issues only)

**Output format:**
| raw_line | is_valid | issue_type | suggested_fix |
|----------|----------|------------|---------------|
| ADAMOVIĆ Petra MILAN... | yes | | |
| BABIĆ Marka JOVO MARIĆ Ive... | no | merged_soldiers | Split into two entries |
| (continuation from above) | no | incomplete | Merge with previous line |

**Issue types:**
- `merged_soldiers` - Multiple soldiers in one line
- `incomplete` - Line is continuation or fragment
- `garbage` - Headers, page numbers, non-soldier text
- `formatting` - Fixable OCR/formatting issues

### Stage 3: AI Extraction
**Goal:** Extract structured data from validated soldier lines

- **Input:** `02_validated_lines.xlsx` (valid lines only)
- **Output:** `03_extracted_data.xlsx` with all fields
- **Script:** `pipeline/03_ai_extract.py` (reusable)
- **Batch size:** 30 soldiers per API call
- **Human effort:** Low (review low-confidence extractions)

**Output format:**
| raw_line | last_name | first_name | fathers_name | birth_year | birthplace | death_date | death_place | death_cause | military_unit | rank_or_role | other_info | confidence | parsing_issues |
|----------|-----------|------------|--------------|------------|------------|------------|-------------|-------------|---------------|--------------|------------|------------|----------------|

### Stage 4: Human Review & Import
**Goal:** Final review and import to main database

- **Input:** `03_extracted_data.xlsx`
- **Output:** Records in `soldiers.db`
- **Script:** `pipeline/04_import_to_db.py`
- **Human effort:** Medium (review spreadsheet, fix errors, approve import)

**Review checklist:**
- [ ] Check rows with `confidence = low`
- [ ] Check rows with `parsing_issues`
- [ ] Spot-check random samples
- [ ] Verify total count matches expected
- [ ] Run import script

---

## Folder Structure

```
pipeline/
├── README.md                    # Quick reference
├── 01_parsers/                  # Book-specific parsing scripts
│   ├── _template_parser.py      # Template for new parsers
│   ├── prva_proleterska.py      # Parser for Prva Proleterska book
│   ├── prva_licka.py            # Parser for Prva Lička book
│   ├── druga_licka.py           # Parser for Druga Lička book
│   └── ...
│
├── 02_ai_validate.py            # Stage 2: AI validation (reusable)
├── 03_ai_extract.py             # Stage 3: AI extraction (reusable)
├── 04_import_to_db.py           # Stage 4: Database import (reusable)
│
├── prompts/                     # AI prompts (version controlled)
│   ├── validate_prompt.txt      # Stage 2 prompt
│   └── extract_prompt.txt       # Stage 3 prompt
│
└── workspaces/                  # Active processing workspaces
    ├── .gitignore               # Ignore workspace contents
    └── {brigade_name}/          # One folder per book being processed
        ├── source/              # Original PDF/images
        ├── 01_raw_lines.xlsx
        ├── 02_validated_lines.xlsx
        ├── 03_extracted_data.xlsx
        └── processing.log
```

---

## Scripts Reference

### Creating a New Book Parser

```bash
# Copy template
cp pipeline/01_parsers/_template_parser.py pipeline/01_parsers/new_brigade.py

# Edit for specific book format
# Run parser
python pipeline/01_parsers/new_brigade.py
```

### Running the Full Pipeline

```bash
# Stage 1: Parse (book-specific)
python pipeline/01_parsers/nova_brigada.py

# Stage 2: Validate
python pipeline/02_ai_validate.py --workspace nova_brigada

# Stage 3: Extract
python pipeline/03_ai_extract.py --workspace nova_brigada

# Stage 4: Review Excel, then import
python pipeline/04_import_to_db.py --workspace nova_brigada --brigade-code 5
```

---

## AI Prompts

### Stage 2: Validation Prompt

The validation prompt checks if each line contains exactly one soldier:

```
You are validating OCR-extracted text from WWII Yugoslav Partisan records.

For each line, determine:
1. Is this a valid single-soldier entry? (yes/no)
2. If no, what's the issue? (merged_soldiers, incomplete, garbage, formatting)
3. If fixable, suggest the fix

Common issues:
- Two soldiers merged into one line (split them)
- Line break split a soldier entry (mark for merging)
- Page headers/footers mixed in (mark as garbage)
- OCR artifacts that can be fixed (suggest correction)
```

### Stage 3: Extraction Prompt

Uses our existing extraction prompt with these key rules:
- Name order: LASTNAME Father's_genitive FIRSTNAME
- Convert father's name from genitive to nominative
- Extract: last_name, first_name, fathers_name, birth_year, birthplace, death_date, death_place, death_cause, military_unit, rank_or_role, other_info
- Confidence: high/medium/low
- Note any parsing_issues

---

## Cost Estimates

Based on GPT-4o-mini pricing ($0.15/1M input, $0.60/1M output):

| Stage | Batch Size | Tokens/Batch | Cost per 1000 soldiers |
|-------|------------|--------------|------------------------|
| Stage 2 (Validate) | 50 | ~3,000 | ~$0.05 |
| Stage 3 (Extract) | 30 | ~4,000 | ~$0.15 |
| **Total** | | | **~$0.20 per 1000 soldiers** |

For a typical book with 2,000 soldiers: **~$0.40**

---

## Adding a New Brigade

1. **Create workspace:**
   ```bash
   mkdir -p pipeline/workspaces/new_brigade/source
   # Copy PDF/images to source/
   ```

2. **Write parser** (or adapt existing):
   ```bash
   cp pipeline/01_parsers/_template_parser.py pipeline/01_parsers/new_brigade.py
   # Edit to match book format
   ```

3. **Run pipeline:**
   ```bash
   python pipeline/01_parsers/new_brigade.py
   python pipeline/02_ai_validate.py --workspace new_brigade
   # Review 02_validated_lines.xlsx, fix issues
   python pipeline/03_ai_extract.py --workspace new_brigade
   # Review 03_extracted_data.xlsx
   python pipeline/04_import_to_db.py --workspace new_brigade --brigade-code X
   ```

4. **Export for website:**
   ```bash
   python scripts/db_export.py
   ```

---

## Version History

| Date | Change |
|------|--------|
| 2025-02-01 | Initial pipeline design |

---

## Notes

- This pipeline is designed to be flexible. Individual steps can be re-run if issues are found.
- Always keep the original `01_raw_lines.xlsx` as backup.
- The `workspaces/` folder is gitignored - only final imported data goes to the database.
- Prompts may need tuning for books with unusual formats.
