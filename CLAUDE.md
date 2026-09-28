# Knjiga Boraca - WWII Yugoslav Partisan Soldier Database

## Project Overview
Historical archive website for searching ~64,300 WWII Yugoslav partisan soldiers across 19 units (18 brigades and one division). Next.js frontend with Python data extraction pipeline. Data comes from OCR'd PDF books ("Knjiga boraca").

## Git
- **Two remotes**: `origin` and `prod` — always push to both
- **Branch**: `main` only

## Brigades

| Code | Name | Parser | JSON | PDF | Count |
|------|------|--------|------|-----|-------|
| 1 | Prva Proleterska | `data-extraction/parse_prva_proleterska.py` | `prva-proleterska-soldiers.json` | 3 PDFs (vol 1-3) | 14,090 |
| 2 | Prva Lička "Marko Orešković" | `data-extraction/parse_soldiers.py` | `soldiers.json` | 1 PDF | 9,757 |
| 3 | Druga Lička | via `scripts/` | `druga-licka-soldiers.json` | 1 PDF | 1,487 |
| 4 | Ljubljanska (10. SNOUB) | `data-extraction/parse_ljubljanska_v2.py` | `ljubljanska-soldiers.json` | 1 PDF | 3,133 |
| 5 | Treća Proleterska (Sandžačka) | `data-extraction/parse_treca_proleterska.py` | `treca-proleterska-soldiers.json` | 1 PDF | 894 |
| 6 | 13. Proleterska "Rade Končar" | `data-extraction/parse_13_proleterska.py` | `13-proleterska-soldiers.json` | 1 PDF | 8,255 |
| 7 | 2. Dalmatinska Proleterska | `data-extraction/parse_2_dalmatinska.py` | `2-dalmatinska-soldiers.json` | 1 PDF | 5,542 |
| 8 | 4. Splitska Udarna | `data-extraction/parse_4_splitska.py` | `4-splitska-soldiers.json` | 1 PDF | 3,093 |
| 9 | Prva Vojvođanska | `data-extraction/parse_prva_vojvodjanska.py` | `prva-vojvodjanska-soldiers.json` | 1 PDF | 1,592 |
| 10 | 3. Krajiška Proleterska | `data-extraction/parse_3_krajiska_proleterska.py` | `3-krajiska-proleterska-soldiers.json` | 1 PDF (two columns) | 2,268 |
| 11 | 4. Krajiška | `data-extraction/parse_4_krajiska.py` | `4-krajiska-soldiers.json` | 1 PDF (Cyrillic) | 1,663 |
| 12 | 5. Kozaračka | `data-extraction/parse_5_kozaracka.py` | `5-kozaracka-soldiers.json` | 1 PDF | 1,007 |
| 13 | 6. Krajiška | `data-extraction/parse_6_krajiska.py` | `6-krajiska-soldiers.json` | 1 PDF | 1,825 |
| 14 | 8. Krajiška | `data-extraction/parse_8_krajiska.py` | `8-krajiska-soldiers.json` | 1 PDF | 1,171 |
| 15 | 1. Šumadijska | `data-extraction/parse_1_sumadijska.py` | `1-sumadijska-soldiers.json` | 1 PDF (Cyrillic) | 319 |
| 16 | 17. Slavonska | `data-extraction/parse_17_slavonska.py` | `17-slavonska-soldiers.json` | 2 PDFs (fallen, survivors) | 3,613 |
| 17 | 18. Slavonska | `data-extraction/parse_18_slavonska.py` (table reader) | `18-slavonska-soldiers.json` | 1 PDF | 1,548 |
| 18 | 2. Vojvođanska | `data-extraction/parse_2_vojvodjanska.py` | `2-vojvodjanska-soldiers.json` | 1 PDF (Cyrillic) | 2,143 |
| 19 | 25. Srpska divizija | `data-extraction/parse_25_srpska_divizija.py` | `25-srpska-divizija-soldiers.json` | 1 PDF (Cyrillic) | 881 |

Brigade configs are defined in `scripts/name_utils.py` (BRIGADE_CONFIGS dict) and `website/app/data/units.ts`. Parsers for codes 10-19 share `data-extraction/_parser_scaffold.py`; see `docs/NEW_BRIGADE_PARSER_STATUS.md`.
Parser IDs are assigned after sorting by name, so re-running a parser keeps IDs only if the set of parsed records is unchanged — re-check corrections for that brigade after any parser change.

## Data Pipeline

When fixing parsing bugs or adding brigades, run these steps in order:

1. **Parse**: `python data-extraction/parse_<brigade>.py` — extracts soldiers from PDF
2. **Normalize**: `python scripts/normalize_all_json.py --apply` — cleans names, extracts birth years, converts genitive father's names to nominative
3. **Extract positions**: `python data-extraction/extract_pdf_positions.py --brigade <name>` — matches soldiers to PDF page/Y coordinates for the viewer
4. **Apply corrections**: `python scripts/apply_corrections.py --apply` — applies individual record fixes from `corrections.json` (edits, deletes, splits, adds). Also auto-updates soldierCount in `units.ts`, then fills empty structured fields from each bio (see below).
5. **Build**: `cd website && npm run build` — verify no errors
6. **Push**: `git push origin main && git push prod main`

Corrections run LAST before build so they always win over automated pipeline output.

**Structured fields** (`birth_place`, `ethnicity`, `occupation`, `rank`, `unit_detail`, `death_type`, `death_date`, `death_place`) are read from `additional_info` by `scripts/extract_structured_fields.py` (per-book rules; death places are put in the nominative only when that form is a known place). Only empty fields are filled; values set in corrections are never overwritten. `apply_corrections.py` runs it automatically; run the script alone for coverage stats and samples (`--brigade N --sample 20`), or with `--apply` for brigades that had no corrections.

## Corrections System

For fixing individual soldier records (OCR errors, merged entries, duplicates) without re-running the parser:

- **File**: `corrections.json` (project root) — array of correction objects
- **Script**: `scripts/apply_corrections.py` — applies corrections to brigade JSONs
- **Actions**: `edit` (update fields), `delete` (remove record), `split` (replace one record with N new records), `add` (insert a soldier the parser missed, with a fixed `new_id`, right after `soldier_id`)
- **Dry run by default**: Run without `--apply` to preview changes
- **Idempotent**: re-applying the whole file is a no-op (an `add` whose `new_id` exists is skipped)
- **Auto-updates**: Recalculates `full_name`, `birth_year`, and `units.ts` soldierCount. Include `birth_year` in `fields` to pin it.

```json
[
  {"id": 1, "action": "edit", "soldier_id": "0001005432", "fields": {"last_name": "Kovačević"}, "reason": "OCR error"},
  {"id": 2, "action": "delete", "soldier_id": "0004002633", "reason": "Duplicate of 0004002634"},
  {"id": 3, "action": "split", "soldier_id": "0004002415", "into": [
    {"last_name": "Štefane", "first_name": "Vinko", "additional_info": "Kovača vas"},
    {"last_name": "Štrajher", "first_name": "Ignac", "additional_info": "1917, Trbovlje"}
  ], "reason": "Two soldiers merged into one entry"},
  {"id": 4, "action": "add", "soldier_id": "0009000108", "new_id": "0009001594", "record": {
    "last_name": "Bogdanov", "middle_name": "Božidar", "fathers_name": "Božidar", "first_name": "Aleksandar",
    "additional_info": "1924, Bavanište (Kovin), dimničar, borac, nestao", "birth_year": "1924",
    "pdf_file": "prva-vojvodjanska.pdf", "pdf_page": 4, "pdf_y": 496.9, "pdf_x": 47.9
  }, "reason": "Missing soldier: PDF page never parsed"}
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
- **Duplicated scan pages**: `prva-licka-proleterska.pdf` pages 913-914 repeat 911-912, `prva-proleterska-1.pdf` pages 176-177 repeat 174-175, and `13-proleterska-spisak.pdf` page 105 is a shifted rescan of page 103 (a whole-page hash misses it; compare entry lines); records read from the copies were deleted in corrections. Check new PDFs for repeated pages before parsing.
- **Glued entries**: a missed entry start leaves the next soldier inside the previous bio ("... na planini Tari. DONOVIĆ (ili DONOVSKI) PANTA Pane, komandir ..."); two-column pages can also mix the columns. Fix with an `edit` that trims the bio plus an `add`.

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
- Two Pythons are installed: `python` on PATH is miniconda 3.10 (pdfplumber 0.11.8); `Python37\python.exe` has pdfplumber 0.9.0. They report **different coordinates** on scanned PDFs whose MediaBox origin isn't (0,0) — nearly all of ours, by up to ~320pt. Stored `pdf_x`/`pdf_y` are in the page space the website's PDF viewer draws in; always read coordinates through `data-extraction/pdf_coords.py` (`viewer_words` / `viewer_offset`), which gives the same result on either version.
