# Data Processing Guide - Heroji NOB

This document describes how we process soldier records, including AI-assisted extraction, quality tracking, and the unique ID system.

---

## Table of Contents

1. [Data Pipeline Overview](#data-pipeline-overview)
2. [AI Extraction Process](#ai-extraction-process)
3. [Confidence & Issue Tracking](#confidence--issue-tracking)
4. [Unique Soldier ID System](#unique-soldier-id-system)
5. [Adding New Brigades](#adding-new-brigades)
6. [Quality Assurance Workflow](#quality-assurance-workflow)
7. [Scripts Reference](#scripts-reference)
8. [Cost Estimates](#cost-estimates)

---

## Data Pipeline Overview

```
Raw Source (PDF/Book/Website)
         ↓
    OCR / Manual Copy
         ↓
    Raw Text File (01-data/raw/)
         ↓
    Initial Parsing (regex-based)
         ↓
    AI Extraction (OpenAI GPT-4o-mini)
         ↓
    Quality Review (confidence + issues)
         ↓
    Final JSON (website/public/)
         ↓
    Standardized Excel (01-data/processed/)
```

---

## AI Extraction Process

### Why AI Extraction?

Traditional regex parsing struggles with:
- OCR errors (broken words like "pogi-nuo" instead "poginuo")
- Inconsistent formatting across different sources
- Complex name patterns (genitive father's names)
- Merged records (two soldiers in one line)
- Missing field separators

AI (GPT-4o-mini) handles these intelligently and provides confidence scores.

### How It Works

1. **Load raw soldier text** from source files
2. **Batch soldiers** (20 per API call for efficiency)
3. **Send to OpenAI** with detailed extraction prompt
4. **Receive structured JSON** with parsed fields + confidence
5. **Save results** with quality metadata

### Running AI Extraction

```bash
# Set up API key
echo "OPENAI_API_KEY=sk-your-key-here" > 01-data/openai-api.txt

# Run batched extraction (recommended - more efficient)
python scripts/extract_with_ai_batched.py

# Or single-record extraction (slower, more detailed)
python scripts/extract_with_ai.py
```

### Extraction Prompt

The AI is given detailed instructions about:
- Yugoslav WWII Partisan context
- Name ordering (LASTNAME Father's_genitive FIRSTNAME)
- Converting genitive names to nominative (Marka → Marko)
- Common abbreviations (s. = selo/village, u NOB od = joined war)
- Death causes (poginuo, umro, nestao, streljan)

See `scripts/extract_with_ai_batched.py` for the full prompt.

---

## Confidence & Issue Tracking

### Confidence Levels

Each AI-extracted record gets a confidence score:

| Level | Meaning | Action |
|-------|---------|--------|
| `high` | All fields clear, no ambiguity | Ready for production |
| `medium` | Some fields uncertain or incomplete | Review recommended |
| `low` | Significant parsing problems | Manual review required |

### Parsing Issues

The AI flags specific problems:

| Issue | Description | Example |
|-------|-------------|---------|
| `OCR error` | Garbled text from scanning | "Stje-pan" instead of "Stjepan" |
| `merged text` | Multiple soldiers in one record | Two names separated by period |
| `incomplete data` | Missing expected fields | No birthplace or unit |
| `unclear format` | Unusual record structure | Non-standard field order |
| `ambiguous name` | Can't determine name parts | Middle vs father's name |

### Output Files

After AI extraction:

```
01-data/processed/
├── ai_extraction_batched_100.json    # All results with metadata
├── ai_extraction_issues.json         # Only problematic records
└── ai_extraction_sample_100.xlsx     # Excel for review
```

### Excel Review Format

The Excel file includes columns for easy comparison:

| Column | Purpose |
|--------|---------|
| `_global_index` | Original row number for reference |
| `_raw_input` | Original unparsed text |
| `last_name` | Extracted surname |
| `first_name` | Extracted given name |
| `fathers_name` | Father's name (nominative) |
| `confidence` | high/medium/low |
| `parsing_issues` | List of problems |

---

## Unique Soldier ID System

### ID Format: 10-Digit Number

```
BBBBNNNNNN
│   │
│   └── 6-digit sequence number (000001-999999)
│
└── 4-digit brigade code
```

### Brigade Codes

| Code | Brigade | Max Soldiers |
|------|---------|--------------|
| `0001` | Prva Proleterska | 999,999 |
| `0002` | Prva Lička Proleterska | 999,999 |
| `0003` | Druga Lička Proleterska | 999,999 |
| `0004` | Ljubljanska (10. SNOUB) | 999,999 |
| `0005` | (reserved) | - |
| ... | ... | ... |
| `9999` | (reserved for future) | - |

### Example IDs

```
0001000001  → First soldier in Prva Proleterska
0002004521  → Soldier #4521 in Prva Lička
0003001509  → Soldier #1509 in Druga Lička (last one)
0004003079  → Soldier #3079 in Ljubljanska (last one)
```

### ID Generation Script

```python
def generate_soldier_id(brigade_code: int, sequence: int) -> str:
    """Generate a unique 10-digit soldier ID."""
    if not (1 <= brigade_code <= 9999):
        raise ValueError("Brigade code must be 1-9999")
    if not (1 <= sequence <= 999999):
        raise ValueError("Sequence must be 1-999999")
    return f"{brigade_code:04d}{sequence:06d}"

def parse_soldier_id(soldier_id: str) -> dict:
    """Parse a soldier ID into components."""
    if len(soldier_id) != 10 or not soldier_id.isdigit():
        raise ValueError("Invalid soldier ID format")
    return {
        'brigade_code': int(soldier_id[:4]),
        'sequence': int(soldier_id[4:]),
        'full_id': soldier_id
    }
```

### Benefits of This System

1. **Unique across all brigades** - No collisions possible
2. **Sortable** - Natural ordering by brigade then sequence
3. **Human-readable** - Easy to identify brigade from ID
4. **Database-friendly** - Fixed length, numeric, indexable
5. **Expandable** - Room for 9,999 brigades × 999,999 soldiers each

---

## Adding New Brigades

### Step-by-Step Process

#### 1. Prepare Raw Data

```bash
# Create directory for new brigade
mkdir -p 01-data/brigades/nova-brigada/

# Add source files (PDFs, scans, text)
# 01-data/brigades/nova-brigada/source.pdf
# 01-data/brigades/nova-brigada/raw_text.txt
```

#### 2. Initial Parsing

Create a parsing script or copy an existing one:

```bash
cp scripts/extract_druga_licka.py scripts/extract_nova_brigada.py
# Edit to match new source format
```

#### 3. Run AI Extraction (Sample First)

```python
# In your extraction script, start with a sample:
sample_size = 100  # Test with 100 first
# Review results before processing all
```

#### 4. Review Quality

```bash
# Check the Excel output
# Review confidence distribution
# Fix any systematic issues in the prompt
```

#### 5. Full AI Extraction

```python
# Once satisfied with sample quality:
sample_size = len(all_soldiers)  # Process all
```

#### 6. Assign Unique IDs

```python
# Add to your processing script:
BRIGADE_CODE = 5  # Next available code

for i, soldier in enumerate(soldiers, 1):
    soldier['soldier_id'] = f"{BRIGADE_CODE:04d}{i:06d}"
```

#### 7. Generate Output Files

```bash
# JSON for website
website/public/nova-brigada-soldiers.json

# CSV/Excel for analysis
01-data/processed/nova_brigada_soldiers.csv
01-data/processed/nova_brigada_soldiers.xlsx
```

#### 8. Update Website

Add the new brigade to:
- `website/src/app/page.tsx` (brigade selector)
- `website/public/` (JSON file)

---

## Quality Assurance Workflow

### Before Adding to Production

```
┌─────────────────────────────────────────────────────────┐
│                    QA Checklist                         │
├─────────────────────────────────────────────────────────┤
│ □ AI extraction completed                               │
│ □ High confidence rate > 70%                            │
│ □ Low confidence records reviewed manually              │
│ □ "merged text" issues fixed (split into separate rows) │
│ □ Unique IDs assigned                                   │
│ □ Duplicate check passed                                │
│ □ Excel export for archival                             │
│ □ JSON validated (proper UTF-8, valid structure)        │
└─────────────────────────────────────────────────────────┘
```

### Handling Low-Confidence Records

1. **Export to Excel** - Filter by confidence = "low"
2. **Manual review** - Check against original source
3. **Fix in spreadsheet** - Correct any errors
4. **Re-import** - Update the JSON from corrected Excel
5. **Mark as reviewed** - Add `"manually_reviewed": true`

### Duplicate Detection

```python
def find_duplicates(soldiers):
    """Find potential duplicate entries."""
    seen = {}
    duplicates = []

    for s in soldiers:
        # Create a fuzzy key
        key = (
            s.get('last_name', '').upper(),
            s.get('first_name', '').upper(),
            s.get('birth_year', '')
        )

        if key in seen:
            duplicates.append((seen[key], s))
        else:
            seen[key] = s

    return duplicates
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `extract_with_ai.py` | Single-record AI extraction (detailed) |
| `extract_with_ai_batched.py` | Batched AI extraction (efficient) |
| `extract_druga_licka.py` | Parse Druga Lička from source |
| `extract_prva_licka_full.py` | Parse Prva Lička from source |
| `standardize_names.py` | Normalize name formats |
| `validate_soldiers_openai.py` | Validate records with AI |
| `add_page_numbers.py` | Add source page references |

---

## Cost Estimates

### GPT-4o-mini Pricing (as of Jan 2025)

| Metric | Cost |
|--------|------|
| Input tokens | $0.15 / 1M tokens |
| Output tokens | $0.60 / 1M tokens |

### Batch Processing Costs

| Soldiers | Batches (20/batch) | Est. Tokens | Est. Cost |
|----------|-------------------|-------------|-----------|
| 100 | 5 | ~15,000 | ~$0.01 |
| 1,000 | 50 | ~150,000 | ~$0.10 |
| 10,000 | 500 | ~1,500,000 | ~$1.00 |
| 25,000 | 1,250 | ~3,750,000 | ~$2.50 |

### Full Database Estimate

Current total: ~25,000 soldiers across all brigades
**Estimated cost for full AI extraction: $2-3**

---

## Future Improvements

### Planned Enhancements

1. **Automated confidence threshold alerts**
   - Flag batches with >30% low confidence
   - Pause and notify for manual review

2. **Source page tracking**
   - Link each soldier to original PDF page
   - Enable verification against source

3. **Change tracking**
   - Log all edits with timestamps
   - Maintain audit trail

4. **Cross-brigade duplicate detection**
   - Some soldiers served in multiple brigades
   - Link related records

5. **Family relationship detection**
   - Same last name + location = potential relatives
   - Flag for genealogy research

### Database Schema (Future)

```sql
CREATE TABLE soldiers (
    soldier_id CHAR(10) PRIMARY KEY,  -- BBBBNNNNNN
    brigade_code INT NOT NULL,
    sequence_num INT NOT NULL,

    -- Parsed fields
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    fathers_name VARCHAR(100),
    birth_year CHAR(4),
    birthplace VARCHAR(200),
    military_unit VARCHAR(200),
    death_date DATE,
    death_cause VARCHAR(100),

    -- Quality metadata
    confidence ENUM('high', 'medium', 'low'),
    parsing_issues JSON,
    manually_reviewed BOOLEAN DEFAULT FALSE,

    -- Audit
    raw_input TEXT,
    source_page INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_brigade ON soldiers(brigade_code);
CREATE INDEX idx_confidence ON soldiers(confidence);
CREATE INDEX idx_last_name ON soldiers(last_name);
```

---

## Quick Reference

### Add a new brigade

```bash
# 1. Create extraction script
python scripts/extract_new_brigade.py

# 2. Run AI extraction (sample)
python scripts/extract_with_ai_batched.py --brigade new --sample 100

# 3. Review Excel output
# 4. Run full extraction
# 5. Assign IDs (brigade code + sequence)
# 6. Export to website/public/
# 7. Update website UI
```

### Re-process existing brigade

```bash
# 1. Load from raw source
# 2. Run AI extraction with updated prompt
# 3. Compare with existing data
# 4. Merge improvements (keep IDs stable!)
```

### Export for external use

```bash
# Generate Excel with all metadata
python -c "
import json, pandas as pd
data = json.load(open('website/public/soldiers.json'))
pd.DataFrame(data).to_excel('export.xlsx', index=False)
"
```

---

*Last updated: February 2025*
