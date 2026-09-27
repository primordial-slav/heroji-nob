# New brigade parsers — status

Source PDFs come from znaci.org (see [ZNACI_ORG_SOLDIER_LIST_CATALOG.md](ZNACI_ORG_SOLDIER_LIST_CATALOG.md)). Every parser calls the shared runner in [`_parser_scaffold.py`](../data-extraction/_parser_scaffold.py). Brigade codes 10–19 are registered in [`soldier_id_utils.py`](../scripts/soldier_id_utils.py) and [`name_utils.py`](../scripts/name_utils.py).

## Ready (wired into units.ts / sources.ts)

| Code | Brigade | Soldiers | Merged entries | Birth year | Father's name |
|-----:|---|---:|---:|---:|---:|
| 12 | 5. Kozaračka | 1,007 | 0 | 620 (all entries that state one) | 13 (initials only in source) |
| 18 | 2. Vojvođanska | 2,141 | 2 | 1,884 | 1,498 (733 converted gen→nom) |

Both pass `normalize_all_json.py --brigade <code>` with 0 issues. For 2. Vojvođanska, soldiers the book marks with `*` (killed or died) get `death_type` from their entry text, using the routine task's vocabulary; it's left unset where OCR garbled the word.

## Stubs (not wired in)

Counts after the shared regex fixes. Birth-year stats from earlier runs were wrong (the old extractor took death/enlistment years) and need re-measuring.

| Code | Brigade | Soldiers | Remaining problem |
|-----:|---|---:|---|
| 10 | 3. Krajiška Proleterska | 1,340 | Two-column split X is a guess (300); left/right text still splices |
| 11 | 4. Krajiška | 1,535 | OCR swaps Ћ for Б/К in some surnames (ALEKSIB, ŽIVOTIK) |
| 13 | 6. Krajiška | 1,644 | Verify column layout; some page-break merges |
| 14 | 8. Krajiška | 1,141 | Looks close to ready; needs an audit pass |
| 15 | 1. Šumadijska | 305 | Multi-paragraph biographies; parents' names in title case |
| 16 | 17. Slavonska | 1,595 | Two-column split X (310) unverified; city section headers |
| 17 | 18. Slavonska | — | Table layout; needs `extract_tables()`, not the line runner |
| 19 | 25. Srpska Divizija | 642 | Numbered entries; add unit_detail (brigade/bataljon) extraction |

## What the scaffold handles

- Cyrillic → Latin before matching (including caps digraphs: ЉУБОМИР → LJUBOMIR)
- Entry starts: `SURNAME[.] [(MAIDEN) | , rođ. MAIDEN] [(F) | F. | Lj.] [Father-gen [i Mother]] GIVEN`, double surnames (`DRAŽIĆ — NINKOVIĆ`), OCR `l`→`I` in caps names, stray scan specks before a name, mostly-caps surnames with OCR junk
- Line clustering via `extract_text_lines` (robust to skewed scans), junk page-number lines, hyphenated line breaks
- Nicknames and maiden names go to `additional_info` (`zvani Branko`, `rođ. Ćosić`), because `normalize_all_json` strips parentheticals from name fields
- Birth year via `name_utils.extract_birth_info` (never the first year found)
- PDF coordinates in the viewer's page space via `pdf_coords.viewer_offset` (identical on pdfplumber 0.9 and 0.11); `pdf_y_end` from the entry's last line on the page
- Optional hooks: `line_filter` (footnotes, back matter), `post_fn` (e.g. `restore_diacritics`, which fixes OCR-stripped names against the spellings in brigades 1–9), `asterisk_marks_death`
