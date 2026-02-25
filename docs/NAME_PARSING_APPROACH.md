# Name Parsing Approach

**Date:** 2026-02-08
**Status:** Brainstorming / Future Reference

## Problem Statement

We're parsing soldier records from Yugoslav WWII memorial books. Each line contains a soldier's information, but:

- Different sources have different formats
- Name ordering varies (LAST FATHER FIRST vs LAST FIRST)
- Cyrillic and Latin scripts
- Multiple ethnicities with different naming conventions
- Father's names in genitive case (need conversion to nominative)
- OCR errors, Unicode issues, parsing errors
- Sometimes two soldiers merged into one line
- Nicknames sometimes present, sometimes not

## Failed Approaches

### Pure Rule-Based
Won't work because data is too messy and inconsistent. No single pattern fits all cases.

### Pure AI
Makes mistakes even with detailed prompts. Examples:
- Puts first name in nickname field
- Confuses father's name (genitive) with first name
- Invents data that isn't there

## Chosen Approach: AI + Field-by-Field Validation

Let AI handle the messy parsing, then validate each field against reference data.

```
Raw line → AI parses → Validator checks each field → Flag issues → Human reviews
                                                           ↓
                                              Corrections update reference tables
                                                           ↓
                                                   Next batch improves
```

## Validation Checks

### 1. First Name Validation
- Check against known first names list (by ethnicity/gender)
- If not in list: flag as `unknown_first_name`
- If looks like genitive (ends in -a, -e): flag as `first_name_looks_like_genitive`

### 2. Father's Name Validation
- Check if value looks like genitive (ends in -a, -e, -ov, -ev, -in)
- Lookup nominative form in reference table
- If not found: flag as `unknown_genitive`

### 3. Last Name Validation
- Check it's not a place name
- Check format looks like surname

### 4. Cross-Field Validation
- If first_name looks like genitive AND father is empty → possible swap needed
- If first_name == last_name → flag
- If nickname is a full name (not diminutive) → flag

### 5. Ethnicity Consistency
- Slovenian with father's name → flag (Slovenians don't use patronymics)
- Italian with Slavic genitive → flag

### 6. Data Quality
- Birth year outside 1880-1935 → flag
- Death year outside 1941-1945 → flag
- Line suspiciously long → might be 2 soldiers merged

## Reference Tables Needed

| Table | Purpose |
|-------|---------|
| `first_names_male.json` | Known male first names by ethnicity |
| `first_names_female.json` | Known female first names by ethnicity |
| `genitive_to_nominative.json` | Verified genitive→nominative mappings |
| `places.txt` | Place names (to avoid parsing as person names) |
| `nicknames.json` | Known nickname mappings (Radomir→Raco) |
| `ocr_fixes.json` | Common OCR corrections (Dordevic→Đorđević) |

## Genitive Transformation Rules

### Apply transformation (Serbian/Croatian/Montenegrin):
- `-a` ending: Milana→Milan, Dragutina→Dragutin, Božidara→Božidar
- `-e` ending: Nikole→Nikola, Ilije→Ilija (names ending in -a become -e)
- `-ov/-ev` ending: Milošev→Miloš, Vojinov→Vojin (possessive)
- `-in` ending: Danin→Dane, Mićin→Mića (possessive from -a names)

### Verified Genitive→Nominative Mappings (from manual review)

These conversions were verified in the 2026-02-08 experiment:

| Genitive | Nominative | Notes |
|----------|------------|-------|
| Teodora | Teodor | |
| Bogdana | Bogdan | |
| Milije | Milija | |
| Miloja | Miloje | |
| Dobrosava | Dobrosav | |
| Krste | Krsto | |
| Janka | Janko | |
| Koste | Kosta | |
| Mate | Mato | Croatian |
| Dušana | Dušan | |
| Velimira | Velimir | |
| Velizara | Velizar | |
| Dragomira | Dragomir | |
| Mateje | Mateja | |
| Riste | Risto/Rista | |
| Ivana | Ivan | |
| Ljubomira | Ljubomir | |
| Ranka | Ranko | |
| Borivoja | Borivoj | |
| Momčila | Momčilo | |
| Mila | Milo | |
| Mirka | Mirko | |
| Ibrahima | Ibrahim | Muslim name |
| Jovana | Jovan | |
| Alberta | Albert | Foreign origin |

### Do NOT transform:
- Slovenian names (no patronymic tradition)
- Italian names (middle name, not patronymic)
- Names that don't match genitive patterns

## Feedback Loop

1. AI parses soldiers
2. Validator flags issues
3. Human reviews flagged records
4. Human corrects mistakes
5. Corrections update reference tables
6. Next batch benefits from better tables
7. Over time: fewer flags, better accuracy

## Known Issues from Manual Review (2026-02-08)

### 1. PDF/OCR Parsing Errors (Split Last Names)

The PDF extraction sometimes introduces spaces in the middle of surnames:

| Raw Text | Correct | Issue |
|----------|---------|-------|
| `MIJAJLO VIĆ` | `MIJAJLOVIĆ` | Space before -VIĆ suffix |
| `CARD ARO` | `CARDARO` | Space in Italian surname |
| `STANKO VIĆ` | `STANKOVIĆ` | Space before -VIĆ suffix |
| `DUB ROJA` | `DUBROJA` | Space in surname |
| `INSEL VINI` | `INSELVINI` | Space in Italian surname |
| `SELM AN` | `SELMAN` | Space in first name |

**Detection strategy**: Look for surname fragments like VIĆ, OVIĆ, OVA that appear as separate words.

### 2. Italian Name Pattern

Italian soldiers follow: **LASTNAME FathersName FIRSTNAME**

Unlike Slavic names, the father's name is NOT in genitive case:

| Raw | Last | Father | First |
|-----|------|--------|-------|
| `DE ROSA Mariano SALVADORE` | DE ROSA | Mariano | SALVADORE |
| `CALESSENI Giuseppe NUNZIO` | CALESSENI | Giuseppe | NUNZIO |
| `SPADON Felice GIOCONDO` | SPADON | Felice | GIOCONDO |
| `MENONCELLO Valentino GUERRINO` | MENONCELLO | Valentino | GUERRINO |
| `ZANELLATI Enrico ALDO` | ZANELLATI | Enrico | ALDO |
| `GALANTI Ermenegildo LIBERO` | GALANTI | Ermenegildo | LIBERO |
| `BACCHERINI Adamo VIRGILIO` | BACCHERINI | Adamo | VIRGILIO |
| `PIANO Giuseppe ANTONIO` | PIANO | Giuseppe | ANTONIO |

**Common Italian first names** (to recognize as father's name): Giuseppe, Giovanni, Francesco, Antonio, Angelo, Felice, Valentino, Enrico, Ermenegildo, Adamo, Alfredo

### 3. Missed Father's Names

AI sometimes fails to recognize middle name as father's name:

| Raw | Last | Father | First |
|-----|------|--------|-------|
| `TOLPAN Rala JOZEF` | TOLPAN | Rala | JOZEF |
| `ĐUKIĆ Joše OSTOJA` | ĐUKIĆ | Joše (Jošo) | OSTOJA |
| `ALFIREV Mate STANKO` | ALFIREV | Mate (Mato) | STANKO |
| `JAKOTOVIĆ Cvetka ĐORĐE` | JAKOTOVIĆ | Cvetko | ĐORĐE |
| `MARTINAC Mate KAZIMIR` | MARTINAC | Mate (Mato) | KAZIMIR |
| `IVIĆ Pavia VLADO` | IVIĆ | Pavio | VLADO |

### 4. Confirmed Nicknames

True nicknames (not first names mistakenly parsed as nicknames):

| Full Name | First | Nickname | Notes |
|-----------|-------|----------|-------|
| `KOMADINA Marka JAKOV KUCIN` | JAKOV | KUCIN | Likely |
| `PETRONIĆ Save MITAR PETRONIJE` | MITAR | PETRONIJE | Diminutive form |
| `TATAREVIĆ Alije NEDŽIB TATAR` | NEDŽIB | TATAR | From surname |
| `ŠUPE Jakova ANTE LONGO` | ANTE | LONGO | Italian nickname |

**Nickname patterns**: Tend to be short (4-6 chars), often derived from surname or diminutive.

### 5. Hungarian Names

Hungarian names may have double-barrel surnames:

| Raw | Interpretation |
|-----|----------------|
| `NAĐ PAL Andrije ĐORĐE` | NAĐ PAL is double surname, Andrije is father, ĐORĐE is first |

### 6. Diacritics Issues

Some father's names missing proper Serbian diacritics:

| Parsed | Correct |
|--------|---------|
| Zivka | Živka (→Živko) |

## Source-Specific Context

Before parsing a new book, document:
- Name pattern (LAST FATHER FIRST vs LAST FIRST)
- Primary script (Cyrillic/Latin)
- Dominant ethnicities
- Typical data completeness

This context can be included in the AI prompt.

## Experiment Files

From our 2026-02-08 experiment with 1000 names:

```
experiments/name_parsing/
├── data/
│   └── sampled_names.json          # 1000 sampled soldiers
├── output/
│   ├── analysis_results_*.xlsx     # AI parsing results
│   ├── patterns_first_names.json   # First names by ethnicity
│   ├── patterns_genitive_raw.json  # Genitive mappings found
│   ├── patterns_nicknames.json     # Nickname examples
│   └── summary_stats.json          # Statistics
├── 01_sample_names.py              # Sample extraction script
├── 02_analyze_names.py             # AI analysis script
├── 03_extract_patterns.py          # Pattern extraction script
└── BRAINSTORM_parsing_approach.txt # Full brainstorming notes
```

## Key Learnings

1. **AI needs very explicit instructions** - vague guidelines lead to mistakes
2. **The LAST word before comma is usually the first name** - AI often got this wrong initially
3. **Nicknames are rare** - AI over-detected them initially
4. **Genitive detection works** - AI can identify -a/-e endings, but needs nominative lookup
5. **Ethnicity matters** - different rules for Slovenian/Italian/Serbian names
6. **Validation catches mistakes** - checking against reference data finds AI errors

## Future Implementation

When ready to implement:

1. Clean up reference tables from experiment (human verification needed)
2. Build `validator.py` with checks above
3. Test validator on existing parsed data
4. Integrate into pipeline: parse → validate → flag → review
5. Build simple review interface for flagged records
6. Run on new brigades, iterate
