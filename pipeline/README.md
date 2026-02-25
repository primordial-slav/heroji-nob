# Data Extraction Pipeline

Quick reference for processing new brigade books.

## Full Documentation
See: `docs/DATA_EXTRACTION_PIPELINE.md`

## Quick Start

```bash
# 1. Create workspace and add source files
mkdir -p pipeline/workspaces/new_brigade/source
# Copy PDF/images to source/

# 2. Create/adapt parser
cp pipeline/01_parsers/_template_parser.py pipeline/01_parsers/new_brigade.py
# Edit parser for book format

# 3. Run pipeline
python pipeline/01_parsers/new_brigade.py
python pipeline/02_ai_validate.py --workspace new_brigade
python pipeline/03_ai_extract.py --workspace new_brigade
python pipeline/04_import_to_db.py --workspace new_brigade --brigade-code X

# 4. Export for website
python scripts/db_export.py
```

## Pipeline Stages

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| 1. Parse | `01_parsers/{book}.py` | PDF/OCR | `01_raw_lines.xlsx` |
| 2. Validate | `02_ai_validate.py` | raw lines | `02_validated_lines.xlsx` |
| 3. Extract | `03_ai_extract.py` | valid lines | `03_extracted_data.xlsx` |
| 4. Import | `04_import_to_db.py` | extracted data | Database |

## Cost

~$0.20 per 1000 soldiers (GPT-4o-mini)
