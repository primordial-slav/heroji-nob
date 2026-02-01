# Data Folder Structure

## Directory Layout

```
01-data/
├── soldiers.db              # PRIMARY SOURCE OF TRUTH
│
├── raw/                     # Original source materials (READ-ONLY)
│   ├── prva_proleterska/
│   │   └── source.pdf
│   ├── prva_licka/
│   │   └── source.pdf
│   └── ...
│
├── exports/                 # Generated outputs (can be regenerated)
│   ├── excel/
│   │   ├── all_soldiers.xlsx           # Full database export
│   │   └── ai_processed.xlsx           # AI extraction results
│   ├── json/                            # For website (auto-generated)
│   │   └── (symlink to website/public or copy)
│   └── csv/                             # For external tools
│       └── all_soldiers.csv
│
├── temp/                    # Temporary/working files (can be deleted)
│   ├── ai_extraction_test_100.json
│   └── ...
│
└── archive/                 # Old versions (dated backups)
    └── 2025-01-31_standardized_soldiers.xlsx
```

## Rules

### 1. Source of Truth
- **`soldiers.db`** is the ONLY source of truth
- Never edit Excel/JSON/CSV directly - always update the database
- All exports are generated FROM the database

### 2. Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Database | `soldiers.db` | - |
| Full export | `all_soldiers.{ext}` | `all_soldiers.xlsx` |
| Filtered export | `{filter}_soldiers.{ext}` | `ai_processed_soldiers.xlsx` |
| Temp files | `temp_{description}.{ext}` | `temp_test_100.json` |
| Archive | `{YYYY-MM-DD}_{name}.{ext}` | `2025-02-01_all_soldiers.xlsx` |

### 3. Export Workflow

```bash
# After ANY database changes, run:
python scripts/db_export.py

# This generates:
#   - exports/excel/all_soldiers.xlsx
#   - exports/excel/ai_processed.xlsx
#   - website/public/*.json (for website)
```

### 4. What Goes Where

| File Type | Location | Delete OK? |
|-----------|----------|------------|
| Original PDFs/scans | `raw/` | NO |
| SQLite database | `soldiers.db` | NO |
| Excel exports | `exports/excel/` | YES (regenerate) |
| JSON for website | `exports/json/` | YES (regenerate) |
| Test/temp files | `temp/` | YES |
| Old versions | `archive/` | YES (backups) |

### 5. Backup Strategy

Before major changes:
```bash
# Create dated backup
cp soldiers.db archive/$(date +%Y-%m-%d)_soldiers.db
```

### 6. Files to .gitignore

```gitignore
# Large generated files
01-data/exports/excel/*.xlsx
01-data/temp/
01-data/archive/

# Keep in git
01-data/soldiers.db        # Small enough, source of truth
01-data/raw/               # Original sources
```

## Migration Commands

To reorganize from current structure to new structure:

```bash
# Create new directories
mkdir -p 01-data/exports/excel
mkdir -p 01-data/exports/json
mkdir -p 01-data/exports/csv
mkdir -p 01-data/temp
mkdir -p 01-data/archive

# Move current files
mv 01-data/processed/*.xlsx 01-data/archive/
mv 01-data/processed/*.csv 01-data/archive/
mv 01-data/processed/*.json 01-data/temp/

# Remove old processed folder
rmdir 01-data/processed

# Regenerate clean exports
python scripts/db_export.py
```
