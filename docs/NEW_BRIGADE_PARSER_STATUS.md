# New brigade parsers — status

Source PDFs come from znaci.org (see [ZNACI_ORG_SOLDIER_LIST_CATALOG.md](ZNACI_ORG_SOLDIER_LIST_CATALOG.md)). Every parser except 18. Slavonska calls the shared runner in [`_parser_scaffold.py`](../data-extraction/_parser_scaffold.py). Brigade codes 10–19 are registered in [`soldier_id_utils.py`](../scripts/soldier_id_utils.py) and [`name_utils.py`](../scripts/name_utils.py).

## All shipped (wired into units.ts / sources.ts)

| Code | Unit | Soldiers | Lists in the book | Notes |
|-----:|---|---:|---|---|
| 10 | 3. Krajiška Proleterska | 2,267 | fallen | Two columns; gutter found per page (`col_split_x='auto'`); "NARODNI HEROJ" photo captions dropped |
| 11 | 4. Krajiška | 1,650 | fallen, died, missing | Cyrillic, poor OCR: `repair_cyrillic_ocr` (Ћ read as Б/Е/Н/К/В, Ђ as Б), "roćen" → rođen, Л read as "Ј1", О read as 0; pp. 106-128 are photo captions |
| 12 | 5. Kozaračka | 1,007 | fallen, missing, died | Diacritics restored against brigades 1-9 |
| 13 | 6. Krajiška | 1,822 | fallen + "Dopunski spisak" + "Naknadno prikupljeni podaci" | Single column (not two); the book itself lists ~30 soldiers twice (both kept, each links to its own entry) |
| 14 | 8. Krajiška | 1,171 | fallen, died | Garbled father's initials ("(£>)", "(š)") repaired before grouping; TOC from p.58 dropped |
| 15 | 1. Šumadijska | 308 | fallen; survivors | Both parents given: the mother goes to the bio ("majka Stanislava; ..."), as do nicknames |
| 16 | 17. Slavonska | 3,611 | fallen (759); survivors (2,852) | Two PDFs, two columns; municipality headings added to the bio as "(općina X)" |
| 17 | 18. Slavonska | 1,548 | fallen (table, 357); survivors (1,191) | Custom table reader (`parse_18_slavonska.py`); survivors' street addresses and house numbers left out; pp. 58-66 of the scan are an unrelated publication |
| 18 | 2. Vojvođanska | 2,141 | soldiers and officers | `*` marks killed/died → `death_type` |
| 19 | 25. Srpska divizija | 877 | fallen | Numbered 1-883; alias notes ("(ili RAJKOV)", "(moguće X)", "(?)") move to the bio as "ili X;" |

All pass `normalize_all_json.py --brigade <code>`; structured fields are filled by `scripts/extract_structured_fields.py`.

## What the scaffold handles

- Cyrillic → Latin before matching (including caps digraphs: ЉУБОМИР → LJUBOMIR)
- Entry starts: `SURNAME[.] [(MAIDEN) | , rođ. MAIDEN] [(F) | F. | Lj.] [Father-gen [i Mother]] GIVEN`, double surnames (`DRAŽIĆ — NINKOVIĆ`), OCR `l`→`I` in caps names, stray scan specks before a name (also without a space: `'PURIĆ`), mostly-caps surnames with OCR junk
- Line clustering via `extract_text_lines` (robust to skewed scans), junk page-number lines, hyphenated line breaks
- Two columns with a fixed split or `col_split_x='auto'` (per-page gutter: the x the fewest words cross)
- Nicknames and maiden names go to `additional_info` (`zvani Branko`, `rođ. Ćosić`), because `normalize_all_json` strips parentheticals from name fields
- Birth year via `name_utils.extract_birth_info` (never the first year found; also "Rođen 20. II 1923", and after an alias clause like "zvani X; ")
- PDF coordinates in the viewer's page space via `pdf_coords.viewer_offset` (identical on pdfplumber 0.9 and 0.11); `pdf_y_end` from the entry's last line on the page
- Optional hooks: `line_filter` (headings, footnotes, back matter, per-book OCR repairs), `post_fn`, `parse_entry_fn`, `asterisk_marks_death`
- Post-processing helpers, all checked against the names already on the site: `restore_diacritics` (ACIMOVIC → Aćimović), `repair_lj_ocr` (KRAGUU → Kragulj), `repair_cyrillic_ocr` (АДАМОВИБ → Adamović, БОРБЕ → Đorđe)

Parser IDs are assigned after sorting by name: re-running a parser keeps its IDs only while the set of parsed records is unchanged, so re-check that brigade's corrections after any parser change.
