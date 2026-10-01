# Voice: Knjiga boraca

How the site's own text is written: unit cards, headings, buttons, hints, messages. `DESIGN.md` covers how it looks; this covers how it reads. The entries from the books are never rewritten to fit these rules (see the end).

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

- Quotes „…“; unit names keep their honorary name in them: Prva lička proleterska brigada „Marko Orešković“ (`sqQuotes`).
- Dates in figures as the books print them: 29. 12. 1924. In prose, the month by name: 8. jula 1942.
- Thousands with a dot: 9.814, 108.150. Ranges with an en dash: 1941–1945.
- Counts agree with the number: 1 borac, 2 borca, 5 boraca, 11 boraca, 21 borac; 1 ime, 2 imena (`countBorci`, `searchAllPlaceholder`).
- Headings and buttons in sentence case: "Saborci i zemljaci", not "Saborci I Zemljaci".
- Names surname first, as printed: "Petrović Milan", with the father's name between where the book gives it.

## Messages

Say what happened and what to do next, without blame and without apology:

> Nema boraca za „Petrović“ s ovim filterima. Proverite filtere ili ih uklonite.

> Spiskovi se nisu učitali. Proverite internet vezu i osvežite stranu.

An empty result suggests the next search ("Pokušajte samo prezime…"), and explains a habit of the books when it is the likely cause ("očevo ime u genitivu, na primer „Milorada“ umesto „Milorad“").

## The books' text is theirs

Entries, names and places are shown as each book prints them: its ijekavica or Slovenian, its abbreviations, its spelling of a village. Corrections fix reading errors (OCR), not the book's language. When the site's text quotes a book, it quotes it exactly.
