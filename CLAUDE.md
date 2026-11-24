# Knjiga Boraca - WWII Yugoslav Partisan Soldier Database

## Project Overview
Historical archive website for searching ~509,000 WWII Yugoslav partisan soldiers across 152 units (106 brigades, fourteen divisions, nineteen detachments, seven battalions, the 1. and 2. eskadrila NOVJ, a naval coastal sector, a company, a corps' artillery, the Vrhovni štab and the Centralna bolnica), and the soldiers of the books across units whose unit is not on the site ("Ostali borci", code 122, and the 1964 census's fallen partisans in eight parts, 131-138). Next.js frontend with Python data extraction pipeline. Data comes from OCR'd PDF books ("Knjiga boraca").

## How these notes are kept

This file is the core: what every session needs. The rest is in `docs/claude/`, a file to a topic: read the topic's file before working in it (the table says when). New notes go into the topic's file, not here, so that this file stays short: a rule that holds everywhere gets a line here and its history goes to the topic. The notes were one file of 46,600 words until 2026-11-08, when the user had them split (too much context costs more and works worse); the topic files hold that text as it was, nothing was dropped. A section named in quotes there ("Resolved places", "Ostali borci") may now be in another topic's file: search `docs/claude/` for it.

| File | What it holds | Read it before |
|---|---|---|
| `docs/claude/units.md` | every unit's parser, books, PDFs and count (the table); each second book's ID range; formation dates, kind and republic | adding or re-parsing a unit or a unit's second book |
| `docs/claude/corrections.md` | fathers in the nominative, undoing merges, deserters, rule corrections; one soldier in several books (merges, links); the identity pass and its review page | merging or linking records, answering the identity queue |
| `docs/claude/books-across-units.md` | every book across units (the hero books, the 1964 census, regional and village lists, staff lists), activists, the family archive, re-matching, the Poreklo library | adding a book across units, matching references |
| `docs/claude/ostali-borci.md` | Borci drugih jedinica (122) and the census's parts (131-138): how they are built, and the chain that rebuilds them | rebuilding them, touching `build_ostali_borci.py` |
| `docs/claude/fields.md` | the structured fields and their readers, birthplaces, standardized forms, the card's rows, field checks and their review page, life events, a man in several units | touching `extract_structured_fields.py`, `standardize_fields.py`, `check_fields.py`, `record_sources.py`, `extract_life_events.py` or the card |
| `docs/claude/places.md` | the places index (the comrades tree) and resolved places (GeoNames, case forms) | touching birthplaces or places of death, `build_relations.py`, `resolved_places.py` |
| `docs/claude/pdfs.md` | book PDFs (repacking), scans without a text layer (OCR), entry boxes | adding a PDF, OCR, the viewer's boxes |
| `docs/claude/ocr-issues.md` | known OCR issues book by book, and the rounds of fixes read against the pages | writing a parser, mending names or entries |
| `docs/claude/site.md` | the home page's news and icons, languages, unit photos, band posters, medals, the map and unit pages, server search, data files, a record's own address | work on the site |
| `docs/claude/portraits.md` | soldiers' portraits: every source and how it was paired, the gallery, the rails, the embroidered frames | adding or moving portraits |
| `docs/claude/email.md` | the contact account and its forward, reading and sending mail, the user's rules for mail, the forms' mail, notes to families, the outreach letters and their replies | reading, answering or drafting any mail |
| `docs/claude/feedback-rules.md` | every rule for what families and readers send: what runs by itself, what is done by hand, the eleven adopted on 2026-11-24 to read forms and mail automatically | reading a form or a mail about a card, changing /pregled or Pošta |
| `docs/claude/releases.md` | when the site goes live (the 21:00 window, the lanes, who pushes) and its version X.Y.Z | committing anything meant for the live site |

**Sessions, the board, the people.** Each session's own file (its job, what it owns, its rules), the board of tasks, the daily handover log, everyone who reported something, the letters sent and the reply templates are in the private local repo `E:\Projects\knjiga-boraca-ops` (local git only, never pushed: it holds names and addresses). Read its README and your session's file when you start; commit there what you change there (2026-11-22, the user's request).

Other docs: `VOICE.md` (the site's text), `DESIGN.md` (how it looks), `docs/ZNACI_ORG_SOLDIER_LIST_CATALOG.md` (which books on znaci.org have soldier lists), `docs/NEW_BRIGADE_PARSER_STATUS.md` (the parsers on the scaffold), `docs/UNIT_PHOTOS.md` (each unit photo's source).

## Git
- **Two remotes**: `origin` and `prod` — a release goes to both
- **Releases**: only the lead pushes, at the daily 21:00 window (large runs on Sundays), at once for an emergency, or on the user's word; each is tagged `vX.Y.Z` by how serious it is (`docs/claude/releases.md`). Every other session commits and tells the lead
- **Branch**: `main` only

## Data Pipeline

When fixing parsing bugs or adding brigades, run these steps in order:

1. **Parse**: `python data-extraction/parse_<brigade>.py` — extracts soldiers from PDF
2. **Normalize**: `python scripts/normalize_all_json.py --apply` — cleans names, extracts birth years, converts genitive father's names to nominative (a father already in the nominative, i.e. `fathers_name` set and different from `middle_name`, is kept). `--brigade N [N ...]` limits it to those units
3. **Extract positions**: `python data-extraction/extract_pdf_positions.py --brigade <name>` — matches soldiers to PDF page/Y coordinates for the viewer
4. **Apply corrections**: `python scripts/apply_corrections.py --apply` — applies individual record fixes from `corrections.json` (edits, deletes, splits, adds). Also auto-updates soldierCount in `units.ts`, then writes a woman's nickname clause as "zvana X;" rather than "zvani" (`scripts/feminine_alias.py`, which tells women's records by the bio's word forms, a married or maiden name ("por. Ciglar", "roj. Leban"), or the given name; the site's `isWoman` in `lib/standIn.ts`, for "Rođena", "Poginula" and the stand-in portrait, reads the same rule from the name lists it writes to `website/app/data/name-genders.json`), then fills empty structured fields from each bio, then puts a birthplace or place of death that resolved through a case in the nominative ("Resolved places", `docs/claude/places.md`), then gives the fields one form ("Standardized fields", `docs/claude/fields.md`), then recomputes every unit's entry boxes ("Entry boxes", `docs/claude/pdfs.md`), then checks the fields against their entries ("Field checks", `docs/claude/fields.md`), and last checks every answer given on the two review pages against the data ("Your answers", `docs/claude/corrections.md`). `--brigade N [N ...]` limits it to those units (e.g. while another session is re-parsing a different one).
5. **Build**: `cd website && npm run build` — verify no errors
6. **Release**: not by the session that made the change: the lead pushes at the 21:00 window (`docs/claude/releases.md`)

Corrections run LAST before build so they always win over automated pipeline output.

**Totals on the site** follow `soldierCount`: the line under the home page search field ("110.430 imena", `t.home.total`) is the sum of every unit's `soldierCount` in `units.ts`, computed at build time in `website/app/lib/totals.ts`, and each unit card shows its own count. Never hard-code a total in page text. When records or units are added or removed, make sure `soldierCount` is current (step 4 does it; a new unit's entry needs its count) and rebuild.

## Rules that hold everywhere

- **IDs.** Parser IDs are assigned after sorting by name, so re-running a parser keeps IDs only if the set of parsed records is unchanged — re-check corrections for that brigade after any parser change. A unit's second book writes into the unit's file with `run_parser(..., id_start=10001, keep_other_sources=True)`, in an ID range of its own (the list is in `docs/claude/units.md`), and a re-run replaces only its own records. A new record's id must be free of older corrections too: an id merged away is free in the file, but the old merge still names it.
- **Entries stay as printed.** The books' entries are shown and stored as printed; a field gets one form (`scripts/standardize_fields.py`), never what the entry doesn't say.
- **Who is on the site.** The war of 1941-1945 only: never another war, never civilians. Deserters and traitors get no record; a man who came over to us, or deserted and came back to fight, does (`docs/claude/corrections.md`). A list that mixes fighters with others gives its fighters (`parse_mosorski_odred_2.FIGHTER`), and the movement's other people go in marked `role: 'activist'`, or `'participant'` where nothing tells (`docs/claude/books-across-units.md`). Every soldier a book names has a place on the site: an entry no unit's record takes is a record of Borci drugih jedinica (122) or of the census's parts (131-138).
- **122 and 131-138** take no reference, link or vocabulary, and a correction never points at a 0122 record (it goes when its man finds his unit). After references change, rebuild them by the chain in `docs/claude/ostali-borci.md`.
- **Check before committing.** After a change to a reader or a rule, or a new unit or book, compare the rebuilt files with HEAD field by field (`quality/field_diff.py`, local): a new book changes other units' fields through the field extractor.
- **Boxes** come from `entry_boxes.py`, which `apply_corrections.py` runs: never set `pdf_y_end` in corrections.
- **The main checkout** holds other sessions' uncommitted work: stage only your own files.
- **Local only, never on the site:** `/sastav`, `/problemi`, `docs/ENTRY_PROBLEMS.md`, `quality/`, the JNA topographic maps.
- **A link to a record** is a plain `<a>`, never `next/link`, whose prefetch would run `/borac/<id>` for every record in sight; that route never reads the search's data or renders a PDF (`docs/claude/site.md`).
- **Photos.** The home page's rails show wartime portraits only; a unit's card photo shows a group of that unit's own soldiers, and its description names the unit.

## Adding a unit

1. Its parser (most units share `data-extraction/_parser_scaffold.py`; the Slovene lists `_slovene_lists.py`) and its row in the table of `docs/claude/units.md`; a second book of a unit gets `id_start` and its range in that file.
2. Its config: `BRIGADE_CONFIGS` in `scripts/name_utils.py`; `website/app/data/units.ts` (with its count); `formation.ts` and `unitKinds.ts`; its name and card in `website/app/i18n/units.ts`; its books in `website/app/data/sources.ts` and `app/i18n/sources.ts` (all languages; the build warns about a missing one).
3. Its PDF in `website/public/pdfs`, then `python scripts/repack_pdfs.py <file>`; a book of two or more columns, or one soldier a line, goes in `entry_boxes.py`'s lists (`docs/claude/pdfs.md`).
4. The pipeline above; `scripts/convert_fathers_genitive.py` if it prints fathers.
5. Its men in other books: `python scripts/find_identities.py` (merges, links, references; twice after a large batch), then the rebuild of 122 and 131-138, `build_relations.py --write`, `build_vez.py --write`, `make_war_events.py`.
6. Its photo: `scripts/find_unit_photos.py` (`docs/UNIT_PHOTOS.md`), then `make_unit_image_sizes.py`.
7. Every unit compared with HEAD field by field before the commit.

## Adding a book across units

1. Its parser writes its entries file under `data-extraction/` (`poreklo/`, `znaci/`, ...), IDs `9` + the book's next free number + the entry's number. The numbers must stay put: `ostali_borci_ids.json` keys on them, so entries found later are numbered after the last.
2. Its source in `sources.ts` and `i18n/sources.ts`; its PDF on the site where it has a scan (a list of names alone in `NAME_LISTS` and `entry_boxes.INLINE_ENTRIES`).
3. `python scripts/match_references.py <book>` (or the identity pass), `--write` the pairs taken, then `apply_corrections.py --apply`.
4. The rebuild of 122 and 131-138 (`docs/claude/ostali-borci.md`), then `build_relations.py --write`.

## Corrections System

For fixing individual soldier records (OCR errors, merged entries, duplicates) without re-running the parser:

- **File**: `corrections.json` (project root) — array of correction objects
- **Script**: `scripts/apply_corrections.py` — applies corrections to brigade JSONs
- **Actions**: `edit` (update fields), `delete` (remove record), `split` (replace one record with N new records), `add` (insert a soldier the parser missed, with a fixed `new_id`, right after `soldier_id`), `merge` (`merge_id` is the same soldier as `soldier_id` in another book: `docs/claude/corrections.md`), `reference` (`ref_book`, `ref_id`: an entry of a book across units added to the record; `docs/claude/books-across-units.md`)
- **Dry run by default**: Run without `--apply` to preview changes
- **Idempotent**: re-applying the whole file is a no-op. An `add` whose `new_id` exists is not inserted again, but the record gets back the fields the correction sets (unless a later `edit` sets them), so the full pipeline (normalize all units, then apply corrections) leaves a committed tree unchanged
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
  }, "reason": "Missing soldier: PDF page never parsed"},
  {"id": 5, "action": "merge", "soldier_id": "0030000069", "merge_id": "0030000068", "merge_name": "Belić Momćilo",
   "reason": "Same soldier in 25-brodska-poginuli.pdf and 25-brodska-sastav.pdf; same death place, death year"}
]
```

Fathers in the nominative, undoing merges, deserters, merges of one man's books and links across units, the identity pass and its review page: `docs/claude/corrections.md`.

## Site Text

Text written for the site (unit cards, headings, buttons, hints, messages) follows `VOICE.md`: ekavica, plain words, one formula for unit cards, Serbo-Croatian typography. The books' entries are shown as printed. How the site looks is in `DESIGN.md`.

Languages, unit photos, band posters, medals, the map pages: `docs/claude/site.md`; portraits: `docs/claude/portraits.md`.

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
  "pdf_file": "prva-proleterska-1.pdf",
  "pdf_x_end": 368.4,
  "pdf_y_end": 339.8
}
```

`pdf_x`/`pdf_y` are the entry's first line; `pdf_x_end`/`pdf_y_end` (and optional `pdf_x_left`) are computed by `entry_boxes.py` (a run-on list's parser sets them, and `pdf_rects` for a name on two lines). A record that merged another book's entry has `other_sources: [{soldier_id, name, additional_info, pdf_file, pdf_page, pdf_x, pdf_y, pdf_x_end, pdf_y_end}]`; an entry from another unit (a link) also has `unit_file` and keeps the box its own unit computed.

A list published only as a web page (1. Dalmatinska, Mačvanski odred) has no `pdf_*` fields; its records carry `source_url` instead, which the soldier dialog links, and its source in `sources.ts` has that URL as `pdfPath` (the Sources page then offers "Otvori spisak" rather than a PDF).

Soldier IDs: 10 digits — first 4 = brigade code (0001-0172), last 6 = sequence.

## Project Structure

```
website/                          # Next.js 15 frontend
  app/
    (sr)/                         # Serbo-Croatian routes at the plain addresses (root layout lang="sr")
    (intl)/[lang]/                # The same routes under /sl, /mk, /en (root layout per language)
    views/
      HomePage.tsx                # Homepage — loads all brigades, global search
      UnitPageClient.tsx          # Brigade detail page with search
      SourcesPage.tsx, GalleryPage.tsx, MemorialCard.tsx
    i18n/
      messages/{sr,sl,mk,en}.ts   # All of the site's own text, per language
      units.ts, sources.ts        # Unit names and cards, book descriptions in sl, mk, en
      config.ts, format.ts        # Languages, addresses, plurals, numbers, quotation marks
    components/
      SoldierModal.tsx            # Soldier detail modal + PDF viewer
      PdfViewer.tsx               # react-pdf viewer with position highlighting
      Navigation.tsx              # Top nav bar
    lib/
      useServerSearch.ts          # Search hook: asks /api/search for a page of results
      soldierSearch.ts            # Word index and ranking (how each word matches, then where; see its header)
      searchData.ts               # The server's search data, a search's page and a record's kin
      dataFiles.ts                # The files scripts/prepare-data.ts writes to public/data/
      diacritics.ts               # č→c, š→s, đ/dj→d normalization for search
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
  entry_boxes.py                  # Each entry's highlight box (run by apply_corrections.py)

scripts/                          # Data transformation
  normalize_all_json.py           # Unified normalization (all brigades)
  name_utils.py                   # Name parsing, genitive conversion, brigade configs
  apply_corrections.py            # Applies corrections.json to soldier JSONs
  build_relations.py              # Places index for the popup's comrades/neighbours tree
  soldier_id_utils.py             # Soldier ID generation/parsing

corrections.json                  # Individual record corrections (edit/delete/split)
```

## Tech Stack
- **Frontend**: Next.js 15, React 19, TypeScript, react-pdf (PDF viewer); search is its own word index (`lib/soldierSearch.ts`)
- **Data extraction**: Python 3.7, pdfplumber
- **Search, data files, a record's own address**: `docs/claude/site.md`. `npm run build` runs `prepare-data` first, so Vercel's Build Command must stay `npm run build`, or the site has no data and the search answers 503.
- **Deployment**: Vercel, from the `prod` remote. Every page but the search and a record's own address is prerendered at build time, and the data the pages load are static files ("Data files", `docs/claude/site.md`), within two Vercel limits that fail the deploy without any sign in git: a server function may not pass 250 MB (`outputFileTracingExcludes` in `next.config.js` keeps `public/`, `data/life-events/` and `generated/` out; it takes effect only on Vercel's Linux build, so a Windows build's traces still list them), and no prerendered response may pass 19 MB. After pushing, check that the live site has the change.

## Windows Notes
- Python console needs `sys.stdout.reconfigure(encoding='utf-8')` for Serbian/Slovenian diacritics
- Writing a file on E: can fail for a moment with OSError 22, a watched data file or a plain script alike (it stopped a full rebuild on 2026-11-04). The pipeline's writes go through `scripts/safe_write.py` (`write_text`: a file beside it, replaced in one step, with retries); a new script that writes a data file should too.
- PDF paths use forward slashes in code but backslashes in Windows shell
- Two Pythons are installed: `python` on PATH is miniconda 3.10 (pdfplumber 0.11.8); `Python37\python.exe` has pdfplumber 0.9.0. They report **different coordinates** on scanned PDFs whose MediaBox origin isn't (0,0) — nearly all of ours, by up to ~320pt. Stored `pdf_x`/`pdf_y` are in the page space the website's PDF viewer draws in; always read coordinates through `data-extraction/pdf_coords.py` (`viewer_words` / `viewer_offset`), which gives the same result on either version.
