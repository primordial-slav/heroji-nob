# Voice: Knjiga boraca

How the site's own text is written: unit cards, headings, buttons, hints, messages. `DESIGN.md` covers how it looks; this covers how it reads. The entries from the books are never rewritten to fit these rules (see the end).

The site speaks Serbo-Croatian at the plain addresses (/, /units/<id>), the same Serbo-Croatian in Cyrillic under /sr-cyrl, and Slovene, Macedonian and English under /sl, /mk and /en. All of its own text lives in `website/app/i18n/messages/<lang>.ts` (`sr.ts` is the reference and sets the shape the others follow); unit names and cards in other languages are in `i18n/units.ts`, what the Izvori page says about each book in `i18n/sources.ts`. The rules below are written for Serbo-Croatian; each other language follows them in its own way (see "Other languages").

## Who reads it

Mostly families and descendants: someone types a name they heard at home and hopes to find one person. Some are researchers. Many read on a phone, and not all are at home in the language of the books. So the text is plain, short and calm. The books and the photographs carry the feeling; the site only points to them.

## Language

- **Serbo-Croatian in Latin script, ekavica**: "preživeli", "starešine", "mesto", "reči".
- **Plain words a person would say aloud.** "Poginuli i preživeli borci", not "Spisak poginulih i preživelih boraca i starešina brigade".
- **Short sentences; one thing each.** No chains of genitives, no passive bureaucratic forms ("izvršeno je", "vrši se").
- **Not translated from English.** Watch for calques: "da vidite" after a command, "u cilju", "baziran na", "kreirati", "kliknite ovde".
- **No pathos, slogans or marketing.** Not "heroji koji su dali živote za slobodu", not "Otkrijte", "Istražite", "Saznajte više". "Narodni heroj" is a title and is written only where the record has it.
- **No exclamation marks.** No statistics as decoration (see `DESIGN.md`); a count is said where it helps ("Pretražite 108.150 imena", "Pronađeno 15 boraca").

## Addressing the visitor

- Prose and hints use polite plural: "Pokušajte samo prezime", "Proverite internet vezu".
- Buttons use the short form: "Podeli zapis", "Citiraj", "Kopiraj", "Pošalji prijavu", "Otkaži".
- Keep it gender-neutral: no singular adjectives about the visitor ("siguran", "zainteresovan"); ask about the soldier instead ("Šta znate o ovom borcu?").

## Words

| Use | For | Not |
|---|---|---|
| borac, borci | everyone on a list (the books' word) | vojnik, junak |
| starešina | an officer or commissar, as the books say | |
| zapis | one person's entry on the site | unos, rekord |
| spisak | a unit's list | baza, tabela |
| knjiga | the printed source | dokument, izvor (except the Izvori page) |
| strana | a page of a book ("strana u knjizi", "str. 42"); also a web page and a page of results ("osvežite stranu", "Po strani") | |
| jedinica | brigade, division or detachment together | formacija |
| poginuo, umro, nestao | as the books say | pao, stradao (unless the book says so) |

Where "strana" could mean the book or the screen, say which: "strana u knjizi".

## Unit cards

One formula for every card: **when and where the unit was formed, then who is on its list.**

> Formirana 23. septembra 1942. na Kozari. Poginuli, nestali i umrli borci i starešine.

- "Formirana" for a brigade or division, "Formiran" for an odred.
- The date with the month's name in the genitive and no "godine": "8. jula 1942.", "u septembru 1943." when the day is unknown.
- The place as it is said: "u Cazinu", "na Kozari", "kod Voćina", "u selu Dobro kod Livna".
- Who is on the list, in plain words: "Borci brigade.", "Poginuli i preživeli borci.", "Spisak je sa dana kad je brigada formirana."
- No book titles or authors (they are on Izvori). Dates and places come from `website/app/data/formation.ts`, i.e. from the unit's own book.

## Typography and numbers

- Quotes „…“; unit names keep their honorary name in them: Prva lička proleterska brigada „Marko Orešković“ (`quoteMarks` in `i18n/format.ts` puts in each language's marks).
- Dates in figures as the books print them: 29. 12. 1924. In prose, the month by name: 8. jula 1942.
- Thousands with a dot: 9.814, 108.150. Ranges with an en dash: 1941–1945.
- Counts agree with the number: 1 borac, 2 borca, 5 boraca, 11 boraca, 21 borac; 1 ime, 2 imena (`plural` in `i18n/format.ts`, used by `borci` and `home.placeholder` in each messages file).
- Headings and buttons in sentence case: "Saborci i zemljaci", not "Saborci I Zemljaci".
- Names surname first, as printed: "Petrović Milan", with the father's name between where the book gives it.

## Messages

Say what happened and what to do next, without blame and without apology:

> Nema boraca za „Petrović“ s ovim filterima. Proverite filtere ili ih uklonite.

> Spiskovi se nisu učitali. Proverite internet vezu i osvežite stranu.

An empty result suggests the next search ("Pokušajte samo prezime…"), and explains a habit of the books when it is the likely cause ("očevo ime u genitivu, na primer „Milorada“ umesto „Milorad“").

## Other languages

Each language is written for its own readers, not translated from Serbo-Croatian word for word: the text a Slovene, Macedonian or English writer would put on such a page, in that language's words for the war, its grammar and typography. Same rules as above: plain, short, calm, polite to the visitor, no pathos, no exclamation marks. Where a sentence only makes sense in Serbo-Croatian, it is rewritten, not carried over.

What stays as printed in every language: the books' entries, names and places, book titles (they are citations), and the values of a record's fields (birthplace, occupation, sub-unit). Only the labels around them are translated. A sub-unit the site numbers ("1. bataljon") is said in the language; one the book names ("3. kordunaški bataljon", "bataljon Garibaldi") is shown as printed.

Search examples on the home page suit each audience (Slovene names and places for /sl, Cyrillic for /mk, which search reads in the books' Latin).

### Српскохрватски (ћирилица)

- Not a translation: the Latin Serbo-Croatian text in Cyrillic, letter for letter (`i18n/cyrillic.ts`), so the rules above apply as they are and the two scripts never drift apart. Write and fix the Latin text; the Cyrillic follows.
- Stay in Latin: addresses, znaci.org, Wikimedia Commons, licences, file formats (PDF, JPG, MB) and words with q, w, x, y. A word the letters get wrong goes in `WORDS` there ("Email" is "Имејл").
- A word where "lj", "nj" or "dž" are two sounds ("injekcija", "nadživeti") comes out wrong; none is on the site now, so check a new one before using it.
- As in every language, the books' entries, names and titles stay in the script the site has them in (Latin).

### Slovenščina

- Vikanje: "Poskusite samo s priimkom", "Preverite internetno povezavo".
- The Slovene words for the partisan war: borec, borci; padli, umrli, pogrešani; soborci, rojaki; enota, seznam, zapis, knjiga.
- The dual: 2 borca, 2 leti; 3 borci, 5 borcev; 101 borec (by the last two digits).
- Quotes »…«; dates without a full stop after the year: "8. julija 1942"; thousands with a dot: 108.150.
- Three dots apart from a whole word: "Nalaganje …".
- Unit names as Slovene says them: Prva liška proletarska brigada »Marko Orešković«, 5. krajiška (kozaraška) udarna brigada.

### Македонски

- Cyrillic, with the polite plural: "Обидете се само со презимето", "Проверете ја интернет-врската".
- The definite article and the doubled object where Macedonian has them ("проверете ја врската", "го видите списокот").
- Words: борец, борци; загинати, починати, исчезнати; соборци, земјаци; единица, список, запис, книга.
- Ordinals as Macedonian writes them: 13-та бригада, 1-ви баталјон, 2-ра чета. Dates without a full stop: "8 јули 1942". Quotes „…“; thousands with a dot.
- Names from the books stay in the Latin the books print; the site does not transliterate them.

### English

- British spelling. Plain imperatives: "Try the surname alone", "Check your internet connection".
- "Partisan", "Partisans" (capitalised, as English-language histories write it) for the people on the lists; "roll" for a unit's list, "record" for a person's page on the site, "entry" for the printed text, "book" for the source.
- Unit names as English-language histories give them: 1st Lika Proletarian Brigade ‘Marko Orešković’, 2nd Proletarian Brigade.
- Dates day-month-year: "8 July 1942"; ‘single’ quotes; thousands with a comma: 108,150.
- Serbo-Croatian words that have no English equivalent are explained once, not left bare: "‘Milorada’ (Milorad’s)".

## The books' text is theirs

Entries, names and places are shown as each book prints them: its ijekavica or Slovenian, its abbreviations, its spelling of a village. Corrections fix reading errors (OCR), not the book's language. When the site's text quotes a book, it quotes it exactly.
