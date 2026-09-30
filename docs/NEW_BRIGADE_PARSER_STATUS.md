# New brigade parsers — status

Source PDFs come from znaci.org (see [ZNACI_ORG_SOLDIER_LIST_CATALOG.md](ZNACI_ORG_SOLDIER_LIST_CATALOG.md)). Every parser except 18. Slavonska calls the shared runner in [`_parser_scaffold.py`](../data-extraction/_parser_scaffold.py). Brigade codes 10–30 are registered in [`soldier_id_utils.py`](../scripts/soldier_id_utils.py) and [`name_utils.py`](../scripts/name_utils.py).

## All shipped (wired into units.ts / sources.ts)

| Code | Unit | Soldiers | Lists in the book | Notes |
|-----:|---|---:|---|---|
| 10 | 3. Krajiška Proleterska | 2,268 | fallen | Two columns; gutter found per page (`col_split_x='auto'`); "NARODNI HEROJ" photo captions dropped |
| 11 | 4. Krajiška | 1,663 | fallen, died, missing | Cyrillic, poor OCR: `repair_cyrillic_ocr` (Ћ read as Б/Е/Н/К/В, Ђ as Б), "roćen" → rođen, Л read as "Ј1", О read as 0; pp. 106-128 are photo captions |
| 12 | 5. Kozaračka | 1,007 | fallen, missing, died | Diacritics restored against brigades 1-9 |
| 13 | 6. Krajiška | 1,825 | fallen + "Dopunski spisak" + "Naknadno prikupljeni podaci" | Single column (not two); the book itself lists ~30 soldiers twice (both kept, each links to its own entry) |
| 14 | 8. Krajiška | 1,171 | fallen, died | Garbled father's initials ("(£>)", "(š)") repaired before grouping; TOC from p.58 dropped |
| 15 | 1. Šumadijska | 319 | fallen; survivors | Both parents given: the mother goes to the bio ("majka Stanislava; ..."), as do nicknames |
| 16 | 17. Slavonska | 3,613 | fallen (759); survivors (2,852) | Two PDFs, two columns; municipality headings added to the bio as "(općina X)" |
| 17 | 18. Slavonska | 1,548 | fallen (table, 357); survivors (1,191) | Custom table reader (`parse_18_slavonska.py`); survivors' street addresses and house numbers left out; pp. 58-66 of the scan are an unrelated publication |
| 18 | 2. Vojvođanska | 2,143 | soldiers and officers | `*` marks killed/died → `death_type` |
| 19 | 25. Srpska divizija | 881 | fallen | Numbered 1-883; alias notes ("(ili RAJKOV)", "(moguće X)", "(?)") move to the bio as "ili X;" |
| 20 | 4. Banijska | 2,147 | soldiers (one list) | Entries start at the page's left margin; one-name entries ("ANDREJ, rodom iz SSSR", Soviet volunteers) and mixed-case given names ("GRUBOR Gojko") get their own name parser; OCR-split surnames rejoined ("CA VIĆ" → Čavić) |
| 21 | 4. Srpska | 6,322 | soldiers (one list), then unidentified soldiers (N. N.) and foreign volunteers | Cyrillic; margin entry starts (page margins measured before reading, so a continuation line at the top of a page isn't an entry); the scan's own misreads fixed in given, father and surnames (и read as н/п/нј, л as т/ч/јј, т as г: Mnjlana → Milana, Sganković → Stanković); "(и X)" is another surname |
| 22 | 7. Vojvođanska | 3,577 | soldiers (one list: survivors, fallen, died after the war; 4. (Russian) battalion included) | Cyrillic; no fathers except a few Novi Sad entries ("SIMIĆ KOSTE ALEKSANDAR"). The scan never reads a capital Ћ: final Ћ comes out as Н/Б/Е/К and initial Ћ as Н, so a surname in "-in" unknown elsewhere becomes "-ić" when that spelling is known (real Vojvodina "-in" names stay); a given name before an uncommon word is name + nickname ("JEREMIĆ EVICA KANA") |
| 23 | 19. Birčanska | 1,982 | soldiers (one list) | Cyrillic, two columns (auto gutter). Capital Ћ never read (shared `repair_capital_c`, plus "-in" → "-ić" for this Bosnian brigade unless the soldier is from Vojvodina); lowercase н read as и in the bios, repaired against the other books' vocabulary ("godiie" → "godine"); Љ as "Л>"; a name broken across lines or a surname alone on its line is joined to the entry; NAME-NICKNAME split by known given names |
| 24 | 2. Krajiška | 1,549 | fallen and died (the book counts 1,565) | Margin entry starts. Every even page is cropped at the left edge: surnames that lost 1-3 letters are rebuilt from the alphabetical range between the neighbouring (uncropped) pages and known surnames; the book sorts Đ before DŽ. Pages 58-59 are a rescan of 56-57 and are skipped. OCR-spaced names rejoined ("MILO RAD", "KA URIN") |
| 25 | Tuzlanski NOP odred | 1,110 | soldiers (one list; many with a portrait) | Pages are a grid of cells, not columns of text: `read_cells` (an `extract_fn` for run_parser) finds each page's gutter as the widest word-free band and a cell as lines sharing a left edge; beside a portrait the name is stacked and letter-spaced ("M EH MED"). Fathers are possessives (Omerov, Mujin), converted by `convert_fathers_genitive.py` (`fathers_name_form: 'possessive'`); the birth year follows the duty ("borac, 1921. Lukavac") |
| 26 | Užički NOP odred | 1,282 | the fallen, 1941-1945 | Margin entry starts; the text layer mixes Cyrillic, Latin and Latin look-alikes of Cyrillic capitals ("ABPAMOBHR", "Bu 4hrebhr" = Вучићевић), decoded against corpus names; Ћ read as К/В in Latin-read names (`ik_is_ic`); a running head on some pages is dropped; nicknames after the given name go to "zvani" |
| 27 | 14. Srpska | 1,006 | the fallen (odred and brigade) | Cyrillic; margin entry starts; the birth year opens the bracket after the name ("(1921, Manjinac, ...)"); a nickname after the given name goes to "zvani" |
| 28 | 7. Crnogorska omladinska | 439 | the fallen (a numbered table) | A five-column table (no. / name / born / unit / killed), one row per soldier, the name cell stacked SURNAME / Father / GIVEN. `read_rows` takes each page's column edges from its header row of column numbers (odd and even pages differ); a row starts at a caps line once the row has its surname and given name, or at a numbered caps line the next line follows at the line pitch (row numbers are sometimes read on the row's last line, and a blank father line leaves the same gap as a new row). Page 4's right column is cut off in the scan |
| 29 | 17. Majevička | 898 | the fallen and died (with the 3rd Majevica detachment) | "SURNAME (FATHER) GIVEN [zv. NICK], rođen ..." with the father in the nominative (`fathers_name_form: 'nominative'`); an entry's first line is indented; OCR-spaced surnames rejoined ("MI JATO VIĆ"), double surnames with a spaced dash joined ("LUKIĆ — VEJNOVIĆ (VOJO)"), l read for I in caps names; one-name entries (Italian volunteers) become given names |
| 30 | 25. Brodska | 926 | the fallen (612) and the roster of October 1943 (314) | Two lists from Nail Redžić's monograph, each soldier keeps a record per list. "SURNAME GIVEN, rođen ..." (fallen) and "SURNAME GIVEN — borac, Hrvat, rođen ..." (roster: the dash ends the name); continuation lines are indented (`_margin_entries`); a second caps given name is a nickname ("BARDAK TEODOR TEDO"), "ing"/"dr" read as a father go to the bio; l read for I in caps names |

All pass `normalize_all_json.py --brigade <code>`; structured fields are filled by `scripts/extract_structured_fields.py`.

## What the scaffold handles

- Cyrillic → Latin before matching (including caps digraphs: ЉУБОМИР → LJUBOMIR)
- Entry starts: `SURNAME[.] [(MAIDEN) | , rođ. MAIDEN] [(F) | F. | Lj.] [Father-gen [i Mother]] GIVEN`, double surnames (`DRAŽIĆ — NINKOVIĆ`), OCR `l`→`I` in caps names, stray scan specks before a name (also without a space: `'PURIĆ`), mostly-caps surnames with OCR junk
- Line clustering via `extract_text_lines` (robust to skewed scans), junk page-number lines, hyphenated line breaks
- Two columns with a fixed split or `col_split_x='auto'` (per-page gutter: the x the fewest words cross)
- Nicknames and maiden names go to `additional_info` (`zvani Branko`, `rođ. Ćosić`), because `normalize_all_json` strips parentheticals from name fields
- Birth year via `name_utils.extract_birth_info` (never the first year found; also "Rođen 20. II 1923", and after an alias clause like "zvani X; ")
- PDF coordinates in the viewer's page space via `pdf_coords.viewer_offset` (identical on pdfplumber 0.9 and 0.11); `pdf_y_end` from the entry's last line on the page (replaced at the end of the pipeline by `entry_boxes.py`, which also sets `pdf_x_end`)
- Optional hooks: `line_filter` (headings, footnotes, back matter, per-book OCR repairs), `post_fn`, `parse_entry_fn`, `asterisk_marks_death`
- Post-processing helpers, all checked against the names already on the site: `restore_diacritics` (ACIMOVIC → Aćimović), `repair_lj_ocr` (KRAGUU → Kragulj), `repair_cyrillic_ocr` (АДАМОВИБ → Adamović, БОРБЕ → Đorđe)

Parser IDs are assigned after sorting by name: re-running a parser keeps its IDs only while the set of parsed records is unchanged, so re-check that brigade's corrections after any parser change.
