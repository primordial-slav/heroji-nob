# Knjiga Boraca - WWII Yugoslav Partisan Soldier Database

## Project Overview
Historical archive website for searching ~29,400 WWII Yugoslav partisan soldiers across 5 brigades. Next.js frontend with Python data extraction pipeline. Data comes from OCR'd PDF books ("Knjiga boraca").

## Git
- **Two remotes**: `origin` and `prod` — always push to both
- **Branch**: `main` only

## Brigades

| Code | Name | Parser | JSON | PDF | Count |
|------|------|--------|------|-----|-------|
| 1 | Prva Proleterska | `data-extraction/parse_prva_proleterska.py` | `prva-proleterska-soldiers.json` | 3 PDFs (vol 1-3) | 14,068 |
| 2 | Prva Lička "Marko Orešković" | `data-extraction/parse_soldiers.py` | `soldiers.json` | 1 PDF | 9,797 |
| 3 | Druga Lička | via `scripts/` | `druga-licka-soldiers.json` | 1 PDF | 1,509 |
| 4 | Ljubljanska (10. SNOUB) | `data-extraction/parse_ljubljanska_v2.py` | `ljubljanska-soldiers.json` | 1 PDF | 3,172 |
| 5 | Treća Proleterska (Sandžačka) | `data-extraction/parse_treca_proleterska.py` | `treca-proleterska-soldiers.json` | 1 PDF | 859 |

Brigade configs are defined in `scripts/name_utils.py` (BRIGADE_CONFIGS dict) and `website/app/data/units.ts`.

## Data Pipeline

When fixing parsing bugs or adding brigades, run these steps in order:

1. **Parse**: `python data-extraction/parse_<brigade>.py` — extracts soldiers from PDF
2. **Normalize**: `python scripts/normalize_all_json.py --apply` — cleans names, extracts birth years, converts genitive father's names to nominative
3. **Extract positions**: `python data-extraction/extract_pdf_positions.py --brigade <name>` — matches soldiers to PDF page/Y coordinates for the viewer
4. **Apply corrections**: `python scripts/apply_corrections.py --apply` — applies individual record fixes from `corrections.json` (edits, deletes, splits). Also auto-updates soldierCount in `units.ts`.
5. **Build**: `cd website && npm run build` — verify no errors
6. **Push**: `git push origin main && git push prod main`

Corrections run LAST before build so they always win over automated pipeline output.

## Corrections System

For fixing individual soldier records (OCR errors, merged entries, duplicates) without re-running the parser:

- **File**: `corrections.json` (project root) — array of correction objects
- **Script**: `scripts/apply_corrections.py` — applies corrections to brigade JSONs
- **Actions**: `edit` (update fields), `delete` (remove record), `split` (replace one record with N new records)
- **Dry run by default**: Run without `--apply` to preview changes
- **Auto-updates**: Recalculates `full_name`, `birth_year`, and `units.ts` soldierCount

```json
[
  {"id": 1, "action": "edit", "soldier_id": "0001005432", "fields": {"last_name": "Kovačević"}, "reason": "OCR error"},
  {"id": 2, "action": "delete", "soldier_id": "0004002633", "reason": "Duplicate of 0004002634"},
  {"id": 3, "action": "split", "soldier_id": "0004002415", "into": [
    {"last_name": "Štefane", "first_name": "Vinko", "additional_info": "Kovača vas"},
    {"last_name": "Štrajher", "first_name": "Ignac", "additional_info": "1917, Trbovlje"}
  ], "reason": "Two soldiers merged into one entry"}
]
```

## Soldier JSON Schema

```json
{
  "soldier_id": "0001000001",
  "last_name": "Kovačević",
  "middle_name": "",
  "first_name": "Marko",
  "fathers_name": "Petar",
  "full_name": "Kovačević Marko",
  "additional_info": "rođen 1920, Beograd, poginuo 1943",
  "birth_year": "1920",
  "pdf_page": 42,
  "pdf_y": 310.5,
  "pdf_x": 72.0,
  "pdf_file": "prva-proleterska-1.pdf"
}
```

Soldier IDs: 10 digits — first 4 = brigade code (0001-0005), last 6 = sequence.

## Known OCR Issues

PDF text extraction has recurring patterns that break name-boundary detection:

- **Lowercase diacritical first chars**: OCR renders Š→š, Ž→ž, Č→č (especially in Slovenian text). Handle with secondary regex pattern for `[šžčćđ]` start.
- **Asterisk markers**: Names like `BOGDAN*` — need pattern3 for asterisk-terminated names.
- **Middle initials before ALL CAPS**: `MAMUŠIN P. MIJO` — pattern2 must allow `([A-ZČĆŽŠĐ]\.?\s+)*` before the first name.
- **Two-column layouts**: Ljubljanska PDF has left/right columns. Use `extract_words()` with x-coordinate splitting at x=280, NOT `extract_text()` which merges columns.
- **Leading punctuation**: Lines starting with `- `, `^ `, `^-` before names (Treća Proleterska). Strip with `clean_line()`.
- **OCR-corrupted diacritics**: `DROBNJAKOVie` instead of `DROBNJAKOVIĆ`. Use 70% uppercase threshold heuristic.

## Project Structure

```
website/                          # Next.js 14 frontend
  app/
    page.tsx                      # Homepage — loads all brigades, global search
    units/[id]/UnitPageClient.tsx # Brigade detail page with search
    components/
      SoldierModal.tsx            # Soldier detail modal + PDF viewer
      PdfViewer.tsx               # react-pdf viewer with position highlighting
      Navigation.tsx              # Top nav bar
    lib/
      useFuseSearch.ts            # Fuzzy search hook (diacritics-aware)
      diacritics.ts               # č→c, š→s normalization for search
      types.ts                    # Soldier interface
    data/
      units.ts                    # Brigade definitions (counts, files, names)
      sources.ts                  # PDF source metadata for Izvori page
  public/
    *.json                        # Soldier data files (served statically)
    pdfs/                         # Source PDF files for viewer

data-extraction/                  # PDF parsing scripts
  parse_*.py                      # One parser per brigade
  extract_pdf_positions.py        # Maps soldiers → PDF coordinates

scripts/                          # Data transformation
  normalize_all_json.py           # Unified normalization (all brigades)
  name_utils.py                   # Name parsing, genitive conversion, brigade configs
  apply_corrections.py            # Applies corrections.json to soldier JSONs
  soldier_id_utils.py             # Soldier ID generation/parsing

corrections.json                  # Individual record corrections (edit/delete/split)
```

## Tech Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Fuse.js (search), react-pdf (PDF viewer)
- **Data extraction**: Python 3.7, pdfplumber
- **Deployment**: Vercel (static export)

## Windows Notes
- Python console needs `sys.stdout.reconfigure(encoding='utf-8')` for Serbian/Slovenian diacritics
- PDF paths use forward slashes in code but backslashes in Windows shell
