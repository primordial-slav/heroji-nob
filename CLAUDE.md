# Knjiga Boraca - WWII Yugoslav Partisan Soldier Database

## Project Overview
Historical archive website for searching ~213,500 WWII Yugoslav partisan soldiers across 83 units (70 brigades, five divisions, seven detachments and a corps' artillery). Next.js frontend with Python data extraction pipeline. Data comes from OCR'd PDF books ("Knjiga boraca").

## Git
- **Two remotes**: `origin` and `prod` — always push to both
- **Branch**: `main` only

## Brigades

| Code | Name | Parser | JSON | PDF | Count |
|------|------|--------|------|-----|-------|
| 1 | Prva Proleterska | `data-extraction/parse_prva_proleterska.py` | `prva-proleterska-soldiers.json` | 3 PDFs (vol 1-3); Borci Sutjeske chapter | 14,501 |
| 2 | Prva Lička "Marko Orešković" | `data-extraction/parse_soldiers.py` | `soldiers.json` | 1 PDF | 9,863 |
| 3 | Druga Lička | via `scripts/` (fallen); `data-extraction/parse_druga_licka_prezivjeli.py` (survivors); `data-extraction/parse_druga_licka_sjecanja_poginuli.py` (fallen, memoir book) | `druga-licka-soldiers.json` | 3 PDFs (fallen; survivors and fallen from the memoir book, two columns) | 7,591 |
| 4 | Ljubljanska (10. SNOUB) | `data-extraction/parse_ljubljanska_v2.py` | `ljubljanska-soldiers.json` | 1 PDF | 3,175 |
| 5 | Treća Proleterska (Sandžačka) | `data-extraction/parse_treca_proleterska.py` (at formation); `data-extraction/parse_treca_proleterska_poginuli.py` (fallen, memoir book); `data-extraction/parse_treca_proleterska_formiranje.py` (at formation, Cyrillic reprint) | `treca-proleterska-soldiers.json` | 3 PDFs (at formation; fallen and dead by year, Cyrillic; the formation list reprinted in Cyrillic); Borci Sutjeske chapter | 2,666 |
| 6 | 13. Proleterska "Rade Končar" | `data-extraction/parse_13_proleterska.py` | `13-proleterska-soldiers.json` | 1 PDF | 8,275 |
| 7 | 2. Dalmatinska Proleterska | `data-extraction/parse_2_dalmatinska.py` | `2-dalmatinska-soldiers.json` | 1 PDF; Borci Sutjeske chapter | 6,057 |
| 8 | 4. Splitska Udarna | `data-extraction/parse_4_splitska.py` | `4-splitska-soldiers.json` | 1 PDF | 3,078 |
| 9 | Prva Vojvođanska | `data-extraction/parse_prva_vojvodjanska.py` | `prva-vojvodjanska-soldiers.json` | 1 PDF | 1,592 |
| 10 | 3. Krajiška Proleterska | `data-extraction/parse_3_krajiska_proleterska.py` (fallen); `data-extraction/parse_3_krajiska_spisak.py` (roster, zbornik knj. 3) | `3-krajiska-proleterska-soldiers.json` | 3 PDFs (fallen, two columns; Borci Sutjeske chapter; the roster of everyone who fought in it, zbornik knj. 3, p. 579 on) | 7,297 |
| 11 | 4. Krajiška | `data-extraction/parse_4_krajiska.py` | `4-krajiska-soldiers.json` | 1 PDF (Cyrillic) | 1,670 |
| 12 | 5. Kozaračka | `data-extraction/parse_5_kozaracka.py` | `5-kozaracka-soldiers.json` | 1 PDF | 1,020 |
| 13 | 6. Krajiška | `data-extraction/parse_6_krajiska.py` (fallen); `data-extraction/parse_6_krajiska_prezivjeli.py` (survivors, Ratna sjećanja) | `6-krajiska-soldiers.json` | 2 PDFs (fallen; survivors, names only, Cyrillic, two columns) | 3,656 |
| 14 | 8. Krajiška | `data-extraction/parse_8_krajiska.py` | `8-krajiska-soldiers.json` | 1 PDF | 1,172 |
| 15 | 1. Šumadijska | `data-extraction/parse_1_sumadijska.py` | `1-sumadijska-soldiers.json` | 1 PDF (Cyrillic) | 324 |
| 16 | 17. Slavonska | `data-extraction/parse_17_slavonska.py` | `17-slavonska-soldiers.json` | 2 PDFs (fallen, survivors) | 3,648 |
| 17 | 18. Slavonska | `data-extraction/parse_18_slavonska.py` (table reader) | `18-slavonska-soldiers.json` | 1 PDF | 1,548 |
| 18 | 2. Vojvođanska | `data-extraction/parse_2_vojvodjanska.py` | `2-vojvodjanska-soldiers.json` | 1 PDF (Cyrillic) | 2,149 |
| 19 | 25. Srpska divizija | `data-extraction/parse_25_srpska_divizija.py` | `25-srpska-divizija-soldiers.json` | 1 PDF (Cyrillic) | 882 |
| 20 | 4. Banijska | `data-extraction/parse_4_banijska.py` | `4-banijska-soldiers.json` | 1 PDF | 2,147 |
| 21 | 4. Srpska | `data-extraction/parse_4_srpska.py` | `4-srpska-soldiers.json` | 1 PDF (Cyrillic) | 6,332 |
| 22 | 7. Vojvođanska | `data-extraction/parse_7_vojvodjanska.py` | `7-vojvodjanska-soldiers.json` | 1 PDF (Cyrillic) | 3,578 |
| 23 | 19. Birčanska | `data-extraction/parse_19_bircanska.py` | `19-bircanska-soldiers.json` | 1 PDF (Cyrillic, two columns) | 1,989 |
| 24 | 2. Krajiška | `data-extraction/parse_2_krajiska.py` | `2-krajiska-soldiers.json` | 1 PDF | 1,566 |
| 25 | Tuzlanski NOP odred | `data-extraction/parse_tuzlanski_odred.py` (cell grid) | `tuzlanski-odred-soldiers.json` | 1 PDF (two columns of cells with portraits) | 1,110 |
| 26 | Užički NOP odred | `data-extraction/parse_uzicki_odred.py` | `uzicki-odred-soldiers.json` | 1 PDF (Cyrillic, mixed scripts) | 1,283 |
| 27 | 14. Srpska | `data-extraction/parse_14_srpska.py` | `14-srpska-soldiers.json` | 1 PDF (Cyrillic) | 1,006 |
| 28 | 7. Crnogorska omladinska | `data-extraction/parse_7_crnogorska.py` (table) | `7-crnogorska-soldiers.json` | 1 PDF (table, Cyrillic and Latin) | 439 |
| 29 | 17. Majevička | `data-extraction/parse_17_majevicka.py` | `17-majevicka-soldiers.json` | 1 PDF | 902 |
| 30 | 25. Brodska | `data-extraction/parse_25_brodska.py` | `25-brodska-soldiers.json` | 2 PDFs (fallen; roster Oct 1943) | 825 |
| 31 | 25. Srpska brigada | `data-extraction/parse_25_srpska_brigada.py` | `25-srpska-brigada-soldiers.json` | 1 PDF (Cyrillic; fallen and wounded) | 368 |
| 32 | 21. Tuzlanska | `data-extraction/parse_21_tuzlanska.py` | `21-tuzlanska-soldiers.json` | 1 PDF | 211 |
| 33 | 53. Srednjobosanska divizija | `data-extraction/parse_53_srednjobosanska.py` (table) | `53-srednjobosanska-soldiers.json` | 1 PDF (table, landscape) | 800 |
| 34 | 21. Slavonska | `data-extraction/parse_21_slavonska.py` | `21-slavonska-soldiers.json` | 1 PDF | 1,117 |
| 35 | 32. Zagorska divizija | `data-extraction/parse_32_divizija.py` (roster); `data-extraction/parse_32_divizija_borci.py` ("Borci 32. divizije NOVJ", by unit) | `32-divizija-soldiers.json` | 2 PDFs (names only, four columns; the monograph's list by unit, two columns, book pp. 431-662) | 17,659 |
| 36 | 1. Dalmatinska | `data-extraction/parse_1_dalmatinska.py` | `1-dalmatinska-soldiers.json` | web page (znaci.org; no scan); Borci Sutjeske chapter | 2,980 |
| 37 | 16. Slavonska omladinska | `data-extraction/parse_16_slavonska_omladinska.py` (fallen); `data-extraction/parse_16_slavonska_rukovodioci.py` (leaders) | `16-slavonska-omladinska-soldiers.json` | 1 PDF (book pp. 389-428: two lists of the fallen, the leaders) | 1,122 |
| 38 | 8. Crnogorska | `data-extraction/parse_8_crnogorska.py` | `8-crnogorska-soldiers.json` | 1 PDF (Cyrillic; book pp. 471-501, 509-510) | 747 |
| 39 | Druga proleterska | `data-extraction/parse_druga_proleterska.py` (run-on names by place and date) | `druga-proleterska-soldiers.json` | 1 PDF (Cyrillic, three columns; monograph pp. 274-278); Borci Sutjeske chapter | 2,216 |
| 40 | 4. Proleterska (crnogorska) | `data-extraction/parse_borci_sutjeske.py` (Sutjeska); `data-extraction/parse_4_proleterska_poginuli.py` (the fallen 1942-45, Janković) | `4-proleterska-soldiers.json` | 2 PDFs (the Borci Sutjeske chapter; the monograph's list of the fallen, Cyrillic) | 3,496 |
| 41 | 5. Proleterska crnogorska | `data-extraction/parse_borci_sutjeske.py` | `5-proleterska-soldiers.json` | Borci Sutjeske, chapter (two columns) | 1,574 |
| 42 | 6. Istočnobosanska proleterska | `data-extraction/parse_borci_sutjeske.py` | `6-istocnobosanska-soldiers.json` | Borci Sutjeske, chapter (two columns) | 807 |
| 43 | 10. Hercegovačka | `data-extraction/parse_borci_sutjeske.py` | `10-hercegovacka-soldiers.json` | Borci Sutjeske, chapter (two columns) | 1,478 |
| 44 | 7. Banijska "Vasilj Gaćeša" | `data-extraction/parse_borci_sutjeske.py` | `7-banijska-soldiers.json` | Borci Sutjeske, chapter (two columns) | 890 |
| 45 | 8. Banijska | `data-extraction/parse_borci_sutjeske.py` | `8-banijska-soldiers.json` | Borci Sutjeske, chapter (two columns) | 834 |
| 46 | 3. Dalmatinska | `data-extraction/parse_borci_sutjeske.py` | `3-dalmatinska-soldiers.json` | Borci Sutjeske, chapter (two columns) | 1,322 |
| 47 | 16. Banijska | `data-extraction/parse_borci_sutjeske.py` | `16-banijska-soldiers.json` | Borci Sutjeske, chapter (two columns) | 591 |
| 48 | 7. Krajiška | `data-extraction/parse_borci_sutjeske.py` (Sutjeska); `data-extraction/parse_7_krajiska_spisak.py` (survivors and the fallen, knj. 2) | `7-krajiska-soldiers.json` | 2 PDFs (the Borci Sutjeske chapter; the zbornik's list, Cyrillic, two columns) | 4,336 |
| 49 | 15. Majevička (1. majevička at the Sutjeska) | `data-extraction/parse_borci_sutjeske.py` | `15-majevicka-soldiers.json` | Borci Sutjeske, chapter (two columns) | 510 |
| 50 | 12. Dalmatinska (1. otočka) | `data-extraction/parse_12_dalmatinska.py` (run-on entries under each battle) | `12-dalmatinska-soldiers.json` | 1 PDF (book pp. 353-366) | 361 |
| 51 | 3. Makedonska | `data-extraction/parse_3_makedonska.py` | `3-makedonska-soldiers.json` | 1 PDF (Cyrillic; book pp. 359-368, the fallen) | 232 |
| 52 | 18. Hrvatska istočnobosanska | `data-extraction/parse_18_hrvatska.py` | `18-hrvatska-soldiers.json` | 1 PDF (book pp. 582-696) | 1,738 |
| 53 | 11. Dalmatinska | `data-extraction/parse_11_dalmatinska.py` | `11-dalmatinska-soldiers.json` | 1 PDF (two columns; book pp. 479-600: fallen, missing, survivors) | 3,444 |
| 54 | 12. Krajiška | `data-extraction/parse_12_krajiska.py` | `12-krajiska-soldiers.json` | 2 PDFs (Cyrillic: fallen; survivors, one line each) | 3,855 |
| 55 | 17. Srpska | `data-extraction/parse_17_srpska.py` | `17-srpska-soldiers.json` | 1 PDF (Cyrillic; survivors, then the fallen; book pp. 317-373) | 989 |
| 56 | 14. Srednjobosanska | `data-extraction/parse_14_srednjobosanska.py` | `14-srednjobosanska-soldiers.json` | 1 PDF (fallen in one column, survivors in two, by municipality; book pp. 393-458) | 2,559 |
| 57 | 3. Vojvođanska | `data-extraction/parse_3_vojvodjanska.py` | `3-vojvodjanska-soldiers.json` | 1 PDF (Cyrillic; fallen, fate unknown, survivors; book p. 479 on) | 4,092 |
| 58 | Kalnički partizanski odred | `data-extraction/parse_kalnicki_odred.py` | `kalnicki-odred-soldiers.json` | 1 PDF (two columns; every member, fallen and surviving; book p. 311 on) | 3,273 |
| 59 | Posavsko-trebavski partizanski odred | `data-extraction/parse_posavsko_trebavski_odred.py` | `posavsko-trebavski-odred-soldiers.json` | 1 PDF (one column, by municipality; book p. 313 on) | 1,969 |
| 60 | 8. Kordunaška divizija | `data-extraction/parse_8_kordunaska_divizija.py` | `8-kordunaska-divizija-soldiers.json` | 1 PDF (two columns; the fallen, with their brigade; book p. 806 on) | 2,674 |
| 61 | Cankarjeva (5. SNOUB "Ivan Cankar") | `data-extraction/parse_cankarjeva.py` (via `_slovene_lists.py`) | `cankarjeva-soldiers.json` | 1 PDF (two columns; survivors "Seznam cankarjevcev", then "Padli"; book pp. 815-861) | 2,896 |
| 62 | Gubčeva (SNOUB "Matija Gubec") | `data-extraction/parse_gubceva.py` (via `_slovene_lists.py`) | `gubceva-soldiers.json` | 1 PDF (two columns; survivors "Seznam gubčevcev", then "Padli"; book pp. 979-1027) | 2,995 |
| 63 | Dvanajsta (XII. SNOUB) | `data-extraction/parse_dvanajsta.py` (via `_slovene_lists.py`) | `dvanajsta-soldiers.json` | 1 PDF (one column, a soldier a line; the fallen, then the survivors) | 1,662 |
| 64 | Gradnikova (Goriška) | `data-extraction/parse_gradnikova.py` (via `_slovene_lists.py`) | `gradnikova-soldiers.json` | 1 PDF (three columns; the fallen, then the others; book pp. 839-877) | 3,661 |
| 65 | Zidanškova | `data-extraction/parse_zidanskova.py` (via `_slovene_lists.py`) | `zidanskova-soldiers.json` | 1 PDF (two columns; one roster, the fallen with years of birth and death; book p. 731 on) | 1,151 |
| 66 | Škofjeloški odred | `data-extraction/parse_skofjeloski_odred.py` | `skofjeloski-odred-soldiers.json` | 1 PDF (two columns of numbered names; book p. 314 on) | 517 |
| 67 | Istrski odred | `data-extraction/parse_istrski_odred.py` (via `_slovene_lists.py`) | `istrski-odred-soldiers.json` | 1 PDF (two columns; the roster without the fallen, then the fallen with a short bio; book pp. 827-852) | 1,280 |
| 68 | Zapadnodolenjski odred | `data-extraction/parse_zapadnodolenjski_odred.py` (via `_slovene_lists.py`) | `zapadnodolenjski-odred-soldiers.json` | 1 PDF (three columns; the roster, then the fallen; book pp. 333-342) | 831 |
| 69 | Bračičeva (13. SNOUB "Mirko Bračič") | `data-extraction/parse_braciceva.py` | `braciceva-soldiers.json` | 1 PDF (II. del: the fallen in one column, the survivors in two; book pp. 722-792) | 2,216 |
| 70 | Tomšičeva (1. SNOUB "Tone Tomšič") | `data-extraction/parse_tomsiceva.py` | `tomsiceva-soldiers.json` | 3 PDFs (the rosters of knj. 2, 3 and 4, one soldier a line: 1942-43, names left out of it, 1943-44 and 1944-45) | 5,921 |
| 71 | 1. slovenska artilerijska | `data-extraction/parse_1_slovenska_artilerijska.py` | `1-slovenska-artilerijska-soldiers.json` | 1 PDF (two columns: the gunners, the fallen; book pp. 388-404) | 763 |
| 72 | Artilerija 9. korpusa | `data-extraction/parse_artilerija_9_korpusa.py` | `artilerija-9-korpusa-soldiers.json` | 1 PDF (the roster, a soldier a line; the fallen as a table; book pp. 316-329) | 414 |
| 73 | 19. Srpska | `data-extraction/parse_19_srpska.py` | `19-srpska-soldiers.json` | 1 PDF (Cyrillic; the fallen by unit, then the survivors; book pp. 411-614) | 3,557 |
| 74 | 22. Srpska kosmajska | `data-extraction/parse_22_srpska.py` | `22-srpska-soldiers.json` | 1 PDF (Cyrillic; the fallen, the survivors; book pp. 317-399, p. 360 typed from the image) | 1,300 |
| 75 | 12. Vojvođanska | `data-extraction/parse_12_vojvodjanska.py` | `12-vojvodjanska-soldiers.json` | 1 PDF (the roster by place, names only, two columns; the fallen; book pp. 207-258) | 2,540 |
| 76 | 4. Vojvođanska | `data-extraction/parse_4_vojvodjanska.py` | `4-vojvodjanska-soldiers.json` | 1 PDF (Cyrillic; the members on the day of formation, the fallen; book pp. 281-334) | 1,241 |
| 77 | 1. Kosovsko-metohijska | `data-extraction/parse_1_kosovsko_metohijska.py` | `1-kosovsko-metohijska-soldiers.json` | 1 PDF (two columns, five lists: the battalions' bios, joiners from Poreče and from Junik and Dečani, the fallen, the wounded; book pp. 351-383) | 1,074 |
| 78 | 8. Vojvođanska | `data-extraction/parse_8_vojvodjanska.py` | `8-vojvodjanska-soldiers.json` | 1 PDF (the fallen and missing; book pp. 675-722) | 1,113 |
| 79 | 19. Sjevernodalmatinska divizija | `data-extraction/parse_19_sjevernodalmatinska.py` | `19-sjevernodalmatinska-soldiers.json` | 1 PDF (the fallen and dead, two columns; book pp. 253-299) | 1,418 |
| 80 | 21. Srpska (2. šumadijska) | `data-extraction/parse_21_srpska.py` | `21-srpska-soldiers.json` | 1 PDF (Cyrillic; the fallen, the survivors, others who fought in it; book pp. 387-472) | 1,422 |
| 81 | 14. Hercegovačka (omladinska) | `data-extraction/parse_14_hercegovacka.py` | `14-hercegovacka-soldiers.json` | 1 PDF (everyone who served, a soldier a line; the fallen; book pp. 243-287) | 1,296 |
| 82 | 5. Vojvođanska | `data-extraction/parse_5_vojvodjanska.py` | `5-vojvodjanska-soldiers.json` | 1 PDF (the soldiers and officers, with birthplace, trade, duty and fate; book pp. 429-584) | 4,262 |
| 83 | 6. Vojvođanska | `data-extraction/parse_6_vojvodjanska.py` | `6-vojvodjanska-soldiers.json` | 1 PDF (the fallen, with birthplace, date and place of death, burial; book pp. 175-199) | 347 |

Brigade configs are defined in `scripts/name_utils.py` (BRIGADE_CONFIGS dict) and `website/app/data/units.ts`. Parsers for codes 10-38, 40-49 and 51-83 share `data-extraction/_parser_scaffold.py` (the Slovene Knjižnica NOV in POS lists, "Seznam borcev" and "Padli", also `_slovene_lists.py`); see `docs/NEW_BRIGADE_PARSER_STATUS.md`. Viktor Kučan's *Borci Sutjeske* (znaci.org 00001/129: every fighter at the Sutjeska, one PDF per brigade, `borci-sutjeske-<unit>.pdf`) is one parser for sixteen brigades: the ten it brings to the site (40-49) and, as a second book, six already here (1, 5, 7, 10, 36, 39; IDs from 100001). Which books on znaci.org have soldier lists is in `docs/ZNACI_ORG_SOLDIER_LIST_CATALOG.md`. Druga proleterska (39) prints no bios: its fallen run on, comma after comma, under each place and date ("Тјентиште (Сутјеска), 1. јуни."), so its parser reads the page itself and gives each soldier the heading's `death_place` and `death_date` (its `HEADINGS` table spells out each heading the text layer garbled).
A unit can hold more than one book: a second book's parser writes into the unit's file with `run_parser(..., id_start=10001, keep_other_sources=True)`, so its records get their own ID range (Druga lička survivors: 0003010001-, the memoir book's fallen: 0003020001-; Treća proleterska's fallen: 0005010001-, its reprinted formation list: 0005020001-; 3. krajiška's roster: 0010200001-; 6. krajiška's survivors: 0013010001-; the 32. division's monograph list: 0035100001-; 7. krajiška's knj. 2: 0048010001-; 4. proleterska's fallen: 0040010001-; Tomšičeva's knj. 3 and knj. 4: 0070010001-, 0070100001-) and a re-run replaces only the records read from its own PDFs.
Parser IDs are assigned after sorting by name, so re-running a parser keeps IDs only if the set of parsed records is unchanged — re-check corrections for that brigade after any parser change.

## Data Pipeline

When fixing parsing bugs or adding brigades, run these steps in order:

1. **Parse**: `python data-extraction/parse_<brigade>.py` — extracts soldiers from PDF
2. **Normalize**: `python scripts/normalize_all_json.py --apply` — cleans names, extracts birth years, converts genitive father's names to nominative (a father already in the nominative, i.e. `fathers_name` set and different from `middle_name`, is kept). `--brigade N` limits it to one unit
3. **Extract positions**: `python data-extraction/extract_pdf_positions.py --brigade <name>` — matches soldiers to PDF page/Y coordinates for the viewer
4. **Apply corrections**: `python scripts/apply_corrections.py --apply` — applies individual record fixes from `corrections.json` (edits, deletes, splits, adds). Also auto-updates soldierCount in `units.ts`, then writes a woman's nickname clause as "zvana X;" rather than "zvani" (`scripts/feminine_alias.py`, which tells women's records by the bio's word forms, a married or maiden name ("por. Ciglar", "roj. Leban"), or the given name), then fills empty structured fields from each bio, then recomputes every unit's entry boxes (see below). `--brigade N` limits it to one unit (e.g. while another session is re-parsing a different one).
5. **Build**: `cd website && npm run build` — verify no errors
6. **Push**: `git push origin main && git push prod main`

Corrections run LAST before build so they always win over automated pipeline output.

**Formation dates**: the home page groups units by the year they were formed, from `website/app/data/formation.ts` (`date` as `YYYY-MM-DD`, or `YYYY-MM`/`YYYY`, plus the source). A new unit needs an entry there, from its book or another source you checked; without one it is listed last, under "Ostale jedinice".

**Totals on the site** follow `soldierCount`: the line under the home page search field ("110.430 imena", `t.home.total`) is the sum of every unit's `soldierCount` in `units.ts`, computed at build time in `website/app/lib/totals.ts`, and each unit card shows its own count. Never hard-code a total in page text. When records or units are added or removed, make sure `soldierCount` is current (step 4 does it; a new unit's entry needs its count) and rebuild.

**Structured fields** (`birth_place`, `ethnicity`, `occupation`, `rank`, `unit_detail`, `death_type`, `death_date`, `death_place`) are read from `additional_info` by `scripts/extract_structured_fields.py` (per-book rules; death places are put in the nominative only when that form is a known place). Only empty fields are filled; values set in corrections are never overwritten. `apply_corrections.py` runs it automatically; run the script alone for coverage stats and samples (`--brigade N --sample 20`), or with `--apply` for brigades that had no corrections. Units whose parser sets the fields itself (`PARSER_FIELDS`: Druga proleterska) are not read. A record linked to another unit's takes the fields it lacks from it, except `unit_detail` (that unit's battalion is not this one's).

**Entry boxes** (`pdf_x_end`, `pdf_y_end`, and `pdf_x_left` where the box's left edge isn't `pdf_x`) are the box the PDF viewer highlights. `data-extraction/entry_boxes.py` computes them from the PDF text: from the entry start (`pdf_x`/`pdf_y`) down its column until the next known entry, a line that starts a new entry by the book's indentation (hanging, first-line or flush, measured per book and page; in a book that hangs, a page whose lines all start level, and an entry that starts one indent right of its column's starts, are flush, as in 7. crnogorska's unnumbered entries among its numbered ones; in a book that indents first lines, an indented line starts an entry only after a line that ends a sentence and if it doesn't begin in lowercase, since the text layer drops leading dashes, as in 2. vojvođanska's "Čortanovci / — Inđija"), a gap, or the column end. `apply_corrections.py` runs it last, for every unit on the site, so boxes always follow the final positions; they are never taken from corrections (don't set `pdf_y_end` there). Run it alone with `python data-extraction/entry_boxes.py [--brigade N] [--apply]`. Page lines are cached in `data-extraction/.cache/` (gitignored); the first run reads ~2,800 pages (~2 min). Two-column books must be listed in `entry_boxes.TWO_COLUMN` (or `TWO_COLUMN_PAGES` when only some pages are), books with more columns in `MULTI_COLUMN` (the 32. division's four-column roster), and lists that give each soldier one line in `ONE_LINE_ENTRIES` (else a box runs down the column); after adding one, delete its cached pages (`data-extraction/.cache/entry_boxes/<pdf>.json`), which were read as one column. Lists that run the names on in lines (`INLINE_ENTRIES`: `druga-proleterska.pdf`, `12-dalmatinska.pdf`), and 12. vojvođanska's roster of two names a line, keep the boxes their parser gives: around the name's own words, and as `pdf_rects` (one `[left, top, right, bottom]` per line, which the viewer draws each) when a name runs on to the next line or column.

**Life events** (`website/data/life-events/<unit data file>`, soldier_id → steps) are the dated steps of a soldier's life for the record dialog's line ("Životni put"): born, SKOJ/KPJ, joined the NOB, came to the unit, a duty from a date, sent or transferred, wounded, ill, captured, exchanged, discharged, the death. `scripts/extract_life_events.py` reads them where a keyword and a date stand together ("član KPJ od 1940", "u brigadi od decembra 1941", "ranjen 20. aprila 1945. kod Vrčin Dola"; a duty only with its own date, never one after a bare date); birth and death come from the fields. Each step is `{k, d, e?, at, x?, s?}` (`at` = where its words are in that entry's `additional_info`, `s` = which entry). Only soldiers with three or more steps are kept; the records route (`app/records/[unit]/[part]/route.ts`) merges them in as `life_events`. `apply_corrections.py --apply` rewrites the files of the units it processed; run the script alone with `--write [--brigade N]`, and without it for coverage per unit, `--check 15` for random steps of each kind, `--leftover 40` for dates no rule reads.

**Places index** (`website/public/relations/places.json`) groups soldiers of all units by birthplace (village + municipality, folded spellings) for the record popup's "Saborci i zemljaci" tree; its unit and same-day branches are worked out in the browser from `unit_detail` and `death_date`. It is not part of `apply_corrections.py`: after a run that adds records or changes birth places, rebuild it with `python scripts/build_relations.py --write` (dry run without `--write` prints coverage and the rules' samples). A village printed without its municipality is linked only when the unit's own records, or the corpus, give it one municipality.

## Site Text

Text written for the site (unit cards, headings, buttons, hints, messages) follows `VOICE.md`: ekavica, plain words, one formula for unit cards, Serbo-Croatian typography. The books' entries are shown as printed. How the site looks is in `DESIGN.md`.

**Languages.** The site is in Serbo-Croatian at the plain addresses (/, /units/<id>, /izvori, /galerija, /kartica), in Serbo-Croatian Cyrillic under /sr-cyrl, and in Slovene, Macedonian and English under /sl, /mk, /en (`app/(sr)/` and `app/(intl)/[lang]/`, two root layouts; both render the same pages from `app/views/`). Components never hard-code text: they take it from `useT()` (client) or `messagesFor(lang)` (server), from `app/i18n/messages/<lang>.ts`; `sr.ts` sets the keys, and the type check fails when another language lacks one. Each language is written for its readers, not translated word for word (`VOICE.md`, "Other languages"). The Cyrillic version has no text of its own: `messages/sr-cyrl.ts` is `sr.ts` written letter for letter in Cyrillic (`app/i18n/cyrillic.ts`), as are the unit cards and book descriptions, so a change to the Latin text shows in both scripts; strings a message function is given (a query, a name, a book title) stay as they are. Links inside the site go through `useLocalePath()` / `localePath()` so they stay in the page's language. The language menu in the header (`components/LanguageMenu.tsx`: a globe with the page language's code, beside the light/dark switch) offers the languages in `FINISHED_LANGS` (`app/i18n/config.ts`): add a language there once its text is finished and read through; until then its pages build at their address for checking, unlinked and kept out of search engines. A new unit needs its name and card in `app/i18n/units.ts`, a new book its description in `app/i18n/sources.ts`, in all three languages; the build warns about any that are missing (they fall back to the Serbo-Croatian text). Emails from the site's forms stay in Serbo-Croatian and name the visitor's language.

## Unit Photos

A unit's card photo must show a group of that unit's own soldiers, and the photo's description must name the unit. They come from the znaci.org photo gallery; `docs/UNIT_PHOTOS.md` lists each photo's source and description, plus which units have none that qualifies. When adding a unit, add it to `UNITS` in `scripts/find_unit_photos.py` and run `--candidates <key>`. It lists every photo tagged with or captioned for the unit, with contact sheets and the museum caption cards of photos that have no typed description. Then set `photo` and run `--apply <key>`. If the gallery has nothing, the unit's own book on znaci.org often has captioned photos: `--book <key> 00001/267.pdf` lists each photo with the caption printed under it (set `book=` instead of `photo`). Many site photos from before this rule turned out to be other units (`--identify` matches site images against the gallery). The cards, the band and the unit page load smaller copies of each photo (`public/images/w640/`, `w960/`, `w1280/`, through `lib/unitImage.ts`): after adding or changing a unit photo, run `python scripts/make_unit_image_sizes.py`.

## Soldier Portraits

The record popup and the memorial card show the soldier's own photograph as a small 3:4 print on the red rule beside the name (`website/app/data/portraits.ts`): a family's photo first (`data/family.ts`), then a portrait from `data/portrait-index.json` (files in `website/public/portreti/<soldier id>.jpg`). Only certain matches go in: a book that prints the portrait in the soldier's own entry (`scripts/extract_book_portraits.py`: Tuzlanski NOP odred, 299), or a znaci.org gallery photo of one person whose caption names the soldier and agrees with the record on more than the name (unit, duty, place or date of death, birthplace), checked by hand and listed with the reason in `GALLERY` in the same script (8), or a captioned photo in the unit's own book on znaci.org (`UNIT_BOOKS`, 85: one person, a name the only one of its kind in the unit, and the caption agreeing with the record; each caption checked against its page, since books print several photos side by side and "(levo)", "(gore)" pick one), or for a narodni heroj the lead photo of his or her Wikipedia article from Wikimedia Commons (`COMMONS`, 37: the article agrees on birth year or birthplace, the file is free, credited with its license; no drawings, graves or busts; the unit's book wins). The books are cached in `data-extraction/.cache/znaci_photos/books/`, the Commons files as 500-px thumbnails in `.cache/commons/` (Wikimedia rate-limits scripts that pull originals). A click on the print opens the photo over the page (`components/PhotoLightbox.tsx`), at most twice its size: from `<soldier id>-v.jpg` (up to 900 px high) where the source is at least half again as large as the print. The Galerija page (`app/views/GalleryPage.tsx`, at /galerija) shows every portrait, small and in a new random order on each visit; a click opens the record. On screens wide enough to have margins, the home page has wartime portraits drifting slowly up both sides (`components/PortraitRails.tsx`). These come only from `data/wartimePortraits.ts`: photos picked by eye from contact sheets (uniforms, partisan caps, young faces in period prints), plus every soldier in the index who died in the war, unless the print is too washed out to show a face. Most of the Tuzlanski book's portraits were taken decades after the war and stay out. A new portrait goes on that list only if it is a wartime photo. Search results never show photos. A soldier without one gets an anonymous grey outline of a partisan in a cap with its red star (`data/silhouettes.ts`, made from period portraits by `scripts/make_standin_silhouettes.py`; the šajkača goes to some Serbs of the units from Serbia and Bosnia, `lib/standIn.ts`).

## Medals

A soldier whose entry (or a merged entry) says "narodni heroj" ("proglašen za narodnog heroja", "Ordena narodnog heroja"; not "predložen za narodnog heroja") gets the Orden narodnog heroja, and one whose entry names the "spomenica" gets the Partizanska spomenica 1941 (`decorationsOf` in `website/app/lib/records.ts`). Search results and "Na današnji dan" show the engraving (`gravira`, drawn in the text colour); the soldier popup and the Spomen-kartica show the photograph (`foto`), hanging from the red rule under the unit photo, with "Narodni heroj · Nosilac Partizanske spomenice 1941" under the unit. The images in `website/public/medalje/` are made by `scripts/make_medal_images.py` (needs `pip install potracer`) from a Commons photo of the order (Pinki, CC BY-SA 4.0, credited on the Izvori page) and the WIPO register's image of the spomenica (public domain).

## Corrections System

For fixing individual soldier records (OCR errors, merged entries, duplicates) without re-running the parser:

- **File**: `corrections.json` (project root) — array of correction objects
- **Script**: `scripts/apply_corrections.py` — applies corrections to brigade JSONs
- **Actions**: `edit` (update fields), `delete` (remove record), `split` (replace one record with N new records), `add` (insert a soldier the parser missed, with a fixed `new_id`, right after `soldier_id`), `merge` (`merge_id` is the same soldier as `soldier_id` in another book: see below)
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

**One soldier, several books.** A soldier printed in two of a unit's books (or two lists of one book) is one record: a `merge` moves the other book's entry into the record's `other_sources` (the name as printed there, its text, and its place on the page), fills fields the record lacks from it, and removes that record (`merge_name` guards against a re-parse giving the id to someone else). The dialog shows every book's entry and switches the PDF between them; search also finds the other book's spelling; structured fields and entry boxes are read from merged entries too. Find candidates with `python scripts/find_source_duplicates.py --brigade N` (grades `sure`, `likely`, `name`, `review` by father, birth year and place, death year and place, and fate), check them, then `--write sure,likely` (plus `--only file` of reviewed `keep_id merge_id` pairs). A list of the fallen against a list of survivors (`LIST_FATE`) never merges by itself: there a matching name, father and village is as often a cousin as the same man (Druga lička, 17. Slavonska). A man one book prints twice gets both entries. A soldier in two units' books is linked, not merged: `python scripts/find_source_duplicates.py --across --write sure` writes `link` corrections (`link_id`, `link_name`; sure needs two agreements, one of them a village or the full father's name, and no disagreement), and `apply_corrections.py` ends with a pass over every unit that gives each linked record the other units' entries (with `unit_file`, the other unit's data file) and the fields it lacks; both records stay in their units. Don't re-run a second book's parser whose name repairs learn from the other units (Druga lička's memoir list uses the survivors' reader): the units change, so names, their order and the IDs shift, and while `merge_name` stops a merge with a warning, edits by id land on whoever has the id now.

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
A list published only as a web page (1. Dalmatinska) has no `pdf_*` fields; its records carry `source_url` instead, which the soldier dialog links, and its source in `sources.ts` has that URL as `pdfPath` (the Sources page then offers "Otvori spisak" rather than a PDF).

Soldier IDs: 10 digits — first 4 = brigade code (0001-0083), last 6 = sequence.

## Known OCR Issues

PDF text extraction has recurring patterns that break name-boundary detection:

- **Lowercase diacritical first chars**: OCR renders Š→š, Ž→ž, Č→č (especially in Slovenian text). Handle with secondary regex pattern for `[šžčćđ]` start.
- **Asterisk markers**: Names like `BOGDAN*` — need pattern3 for asterisk-terminated names.
- **Middle initials before ALL CAPS**: `MAMUŠIN P. MIJO` — pattern2 must allow `([A-ZČĆŽŠĐ]\.?\s+)*` before the first name.
- **Two-column layouts**: Ljubljanska PDF has left/right columns. Use `extract_words()` with x-coordinate splitting at x=280, NOT `extract_text()` which merges columns.
- **Leading punctuation**: Lines starting with `- `, `^ `, `^-` before names (Treća Proleterska). Strip with `clean_line()`.
- **OCR-corrupted diacritics**: `DROBNJAKOVie` instead of `DROBNJAKOVIĆ`. Use 70% uppercase threshold heuristic.
- **Lowercase l for capital I**: `ZlVKOVlC`, `LJUBlClC` (mostly 4. Splitska and 17. Slavonska). An `l` between consonants or before a final `-c` is an `I`; restore lost carons only from spellings the corpus agrees on. Slovenian surnames like Brulc and Drolc are real.
- **Duplicated scan pages**: `prva-licka-proleterska.pdf` pages 913-914 repeat 911-912, `2-krajiska.pdf` pages 58-59 rescan 56-57 (skipped by the parser), `prva-proleterska-1.pdf` pages 176-177 repeat 174-175, `13-proleterska-spisak.pdf` page 105 is a shifted rescan of page 103 (a whole-page hash misses it; compare entry lines), and the Prva proleterska volumes overlap by a page (`-2.pdf` page 1 = `-1.pdf` page 309, `-3.pdf` page 1 = `-2.pdf` page 355); records read from the copies were deleted in corrections. Some books also print an entry twice on purpose or by mistake (13. Proleterska, Prva lička, Prva proleterska); those are kept as printed. Check new PDFs for repeated pages before parsing.
- **Glued entries**: a missed entry start leaves the next soldier inside the previous bio ("... na planini Tari. DONOVIĆ (ili DONOVSKI) PANTA Pane, komandir ..."); two-column pages can also mix the columns. In Prva lička a bracket after the surname ("BALAĆ (udana BASTA) Danina Milica") hid ~60 entry starts this way. Fix with an `edit` that trims the bio plus an `add`. Before adding a "missing" soldier, check that the parser didn't keep them under a garbled name — several earlier adds duplicated such records.
- **Cropped scans**: `2-krajiska.pdf` cuts the left edge of every even page, so surnames lose their first letter(s); the parser rebuilds them from the alphabetical order and corpus surnames, page by page against coarse bounds. Corrections then fixed 102 more by choosing each even page's surnames together, in the order between the uncropped pages; about 30 remnants that neither decides stay as printed ("Ra", "Ljcić"). Seventeen soldiers whose cropped entry start was missed had been glued into the previous bio (split out as adds).
- **Latin look-alikes for Cyrillic**: the `uzicki-odred.pdf` text layer spells some Cyrillic names with the Latin letters they look like ("ABPAMOBHR" = АВРАМОВИЋ, "4" for Ч, "A>" for Љ); `parse_uzicki_odred.decode` reads them back, choosing among ambiguous letters (A = А/Л/Д, H = Н/И) by the names the corpus knows.
- **Ђ and Ћ read as Б or Н**: in `8-crnogorska.pdf` the Đ names come out as B names ("Bukić" = Đukić) and the Ć names as B or N names ("Nirić" = Ćirić); `parse_8_crnogorska.letter_sections` gives them the letter back where the alphabetical list is at Đ or Ć (this book puts Ć after C). Inside a name Ћ is often К or Н ("Pavinević" = Pavićević).
- **Italic н read as п or и**: the place-and-date headings of `druga-proleterska.pdf` come out as "Тјептиште (Сутјеска), 1. јупи" (Tjentište, 1. juni), and its names lose letters to ш ("Гапшћ" = Gašić, "Маншћ" = Milić, which its alphabetical order under the heading tells). znaci.org re-typeset this book from its OCR, so the page image shows the same errors: correct it from the place names other books print and from the list's order.
- **Missing text-layer lines**: the 13. Proleterska text layer drops some printed lines entirely (e.g. VUJIČIĆ Rade RADE, DABIĆ Vase ŽIVKO); check the page image (`crop` the page) before concluding an entry doesn't exist.
- **Borci Sutjeske**: the scan repeats pages (4. proleterska pp. 36-37 = 34-35; 3. dalmatinska pp. 22-23, 62-63 = 20-21, 60-61; skipped in the parser's `SKIP_PAGES`), garbles the first letter at a column's left edge ("3UDIĆ" = Budić, "Iulat" = Bulat; read back from the alphabetical order where the corpus knows the result, else left as printed), splits surnames ("DANILO VIĆ") and reads t as l, lj as li/lt, j as i or a dot in names ("Pelar", "Liubiša", "Vo.io"; repaired only where the printed form is unknown and the repaired one well known, surnames more strictly). The chapters' totals of fighters differ from their rolls by a few per cent.
- **19. srpska**: znaci.org re-typeset this book from its OCR, so the page shows the text layer's errors: А for Д or Л at a word's start ("Арагољуб", "Аукијановић"), ћ for ђ ("роћен", "Борћевић" = Đorđević), Љ as Л> and some names in Latin look-alikes ("Bopheeuh" = Đorđević, "Mwian" = Milan). The parser reads them back from the corpus, the book's own spellings and the alphabetical order (`LOOKALIKE_LAST`, `LOOKALIKE_FIRST`); a few it can't read stay as printed. It also sets each birthplace (the village in the nominative the book prints, else by declension rules), since the corpus holds this region's villages in the locative ("Boževcu").
- **4. Splitska name format**: `N. SURNAME (FATHER) FIRST (NICKNAME), r. ...` — the first parenthesis is the father (genitive), a parenthesis after the given name is a nickname (`zvani X; ...`).

## Project Structure

```
website/                          # Next.js 14 frontend
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
      useFuseSearch.ts            # Fuzzy search hook (diacritics-aware)
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
- **Frontend**: Next.js 14, React 18, TypeScript, Fuse.js (search), react-pdf (PDF viewer)
- **Data extraction**: Python 3.7, pdfplumber
- **Deployment**: Vercel (static export)

## Windows Notes
- Python console needs `sys.stdout.reconfigure(encoding='utf-8')` for Serbian/Slovenian diacritics
- PDF paths use forward slashes in code but backslashes in Windows shell
- Two Pythons are installed: `python` on PATH is miniconda 3.10 (pdfplumber 0.11.8); `Python37\python.exe` has pdfplumber 0.9.0. They report **different coordinates** on scanned PDFs whose MediaBox origin isn't (0,0) — nearly all of ours, by up to ~320pt. Stored `pdf_x`/`pdf_y` are in the page space the website's PDF viewer draws in; always read coordinates through `data-extraction/pdf_coords.py` (`viewer_words` / `viewer_offset`), which gives the same result on either version.
