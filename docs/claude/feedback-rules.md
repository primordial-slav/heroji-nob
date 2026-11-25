# Rules for forms and mail

Every rule we apply to what families and readers send (the site's three forms, a form sent by mail through the site's
"Otvori mejl" fallback, and people's own mails), in one list: what runs by itself, what a session still does by hand, and
the eleven the user adopted on 2026-11-24 ("i agree wit hall 11 suggestions") to make reading them automatic. The how
of each step is in `email.md` (the mail, permissions, telling the family) and `corrections.md` (corrections, merges).
A new rule the user gives goes here, with its date and the user's words.

## Automatic (in code)

- A unit an entry names that is on the site takes the record into it; not on the site, it stands under the name
  (`unit_name`) in place of "Borci drugih jedinica" (`scripts/unit_named.py`, the builder of 122; the user, 2026-11-20 and
  2026-11-23). KNOJ's brigades count only where KNOJ is named; the order of battle's misprints are mended (2026-11-24).
  An entry naming two units on the site or more goes to the first it names, the others in his row (unit_detail); one
  naming a unit on the site and another goes to the one on the site, the other in his row (the user, 2026-11-24, on
  Janković Radoš: "1, and count", "for both groups"; `unit_named.unit_of`, `others_named`).
- What a family tells of a battle is a step of the life line and a line under the facts: Sutjeska, Neretva (any entry
  that says he was in it), Igman (`scripts/make_war_events.py`; the user, 2026-11-23 and 2026-11-24).
- A life line is drawn from two dated steps (`extract_life_events.shows_line`; 2026-11-23).
- A nickname stands by the name, in quotes (`lib/records.ts`, `nicknameOf`; 2026-11-23).
- A form naming the Partizanska spomenica is flagged on /pregled (`make_pregled.spomenica_mentions`).
- The forms about one person, and the records they touch, are one case on /pregled (`make_pregled.make_cases`).
- A book's portrait a family's photo replaced stays on the card, last in the album (`portraits.replacedPortrait`; 2026-11-24).
- A form that came by mail is a form, with its fields (Pošta, `posta.forma_mejlom`; 2026-11-24).
- A card a family added to carries the family's dot (`components/FamilyMark.tsx`; 2026-11-23).
- **The life line's joinings** (`extract_life_events.py`): a joining of the NOB, SKOJ or KPJ dated after the death gives
  way to another entry's that fits (2026-11-25); a joining of the NOB dated after the day the same entry has him join his
  unit ("u brigadi od") gives way too, and with none that fits the unit's step stands alone (the user, 2026-11-26).
  `fields.md`, "Life events".
- **A field a correction empties** stays empty where the record's text would read another man's value back into it
  (`"keep_blank": true` on an edit: Bućan Aleksandar's brother's death; a family's or review answer's empty field
  stays so by itself). **A birth day set by hand** (`patch_record.py`) on a record of 122 or a census part stays.
- **Addresses follow the man**: a record moved to another unit, back to Borci drugih jedinica or joined to another
  record keeps its old address, which forwards (`moved-ids.json`, `prepare-data.ts`), and references to a record merged
  away follow to the record it joined; the builder of 122 writes every record's name (2026-11-25).

## By hand (05-ENTRY FIXES, form by form)

- **Permissions.** "Objava sadržaja: Ne": only the facts are corrected. Without "Objava imena": the note goes up unsigned,
  "iz porodične arhive". A mailed form has no permission lines: facts and an unsigned note (until rule 4 below is live).
- **Credit**: initial + surname + relation ("F. Adžić, rođak"); a correction's reason names the family ("Form <date>,
  family (<credit>): ...").
- **The family wins** and stands alone on the card, no "ili <book>"; "ili" only where books disagree and no family spoke.
  Death: the family's > a book's exact date and place > the census's year and place.
- **The Spomenica** a family mentions goes on the card.
- **Photos.** A family's photo of the man himself is his portrait, cut from a group or family photo; a postwar photo, other
  people, graves and documents go in the album. The portrait is head and shoulders; the album's whole photo is trimmed of
  a torn or stained edge (Lapčević, 2026-11-24).
- **Places.** A report fixing a birthplace changes the village only; općina and srez stay as at birth.
- **Rows match the text.** Every fact a card's text or papers give shows in its rows and life line (joined the NOB, unit,
  wounds, SKOJ, KPJ); life after the war stays in the note; no rows the site doesn't use.
- **A family-named unit** on the site: the record moves into it (a census record too); not on the site: under the name.
- **Relatives** a form names who fought get a record if they have none (Perkov Mladin, Ujević Antica); civilians,
  deserters and traitors get none.
- **No field from nowhere.** Before committing forms, `python quality/check_form_fields.py` (local) lists every field of
  a card a family or visitor touched whose words no text of the card, the family's note or the form itself says
  (the Brajdićs had Zagreb as a birthplace no form gave; the user, 2026-11-24: "make sure no stupid mistakes like
  mesto rođenja mistake"). A value it lists is fixed or explained before the commit.
- **Names' diacritics.** `check_form_fields.py` also lists a name (surname, father, given name) that another spelling on
  the card prints with a mark it lacks, in an entry, another book, the family's note or the form ("Spire" beside "od oca
  Špire"), or a father as printed whose marks disagree with his nominative (Spire / Špiro). It is mended only where the
  scan prints the mark or a family or another book gives it; the entry stays as printed. `--all` lists the same over
  every unit for review, in `quality/name-diacritics-all.json` (2,420 names on 2026-11-26, none mended unseen). The
  user, 2026-11-26: "make a check or rule for future to not make the špiro spiro mistake again" (Kanazir Špire Maksim,
  and 19 more of the 4. pomorski sektor by the scan, d7996a69).
- **A living person's office** is dated ("predsednik ... u novembru 2026"), never "sada".
- **A place correction ticked "Koristi kao pravilo"** on /pregled is kept in `quality/pregled-pravila.json` (so far
  Sindija → Sirdija).

## Adopted 2026-11-26, strictly, for feedback, new records and edits of old ones

The lead's list of the day's practices (2026-11-25), which the user adopted on 2026-11-26: "aside from point 7, enforce
all the others strictly when getting feedback and adding new names and editing previous entries". Every session that
reads a form or a mail, adds a record or edits one keeps them.

- **What the family isn't sure of is a note, not a fact.** "Imala je informaciju", "kažu", "mislim da", "navodno": the
  words go in the family's note as theirs; the card's fields keep what the books give. No date or place is made from a
  memory (Pavlović Veljko Dušan's "Mama je imala informaciju da je poginuo na Sutjesci": the census's 1944 stays, the
  Sutjeska in the note; Runtić Ante "went to the partisans the day the Italians entered Split": no joining date; Vuletić
  Bruno "first across the Neretva bridge": a neighbour's memory).
- **Someone who isn't family is signed as who they are**: "sused" (Vuletić Bruno), the reader's initial and surname
  with no relation (A. Krstulović on Lukin Branko), "E. Goldrick, istoričar" (Čolnik Karel). With the name tick "Ne", a
  neighbour is still signed by what they are ("sused"), not "iz porodične arhive", which is for family alone.
- **A paper they send counts more than what they type.** A book's clip, a booklet, a certificate or a letter of the time
  wins over the form's own words, and goes on the card as a paper (Bilandžić Filip: the form swapped him and his father,
  the clip prints "pok. Ivana FILIP"; Šiliegović-Vučković Milka's Spomenica booklet; Babić Rade's Gračac book, which a
  reader pointed to).
- **A report asking for what the card already shows changes nothing**, and the reply says where it is (Črv Ivan: "Anton
  is his father", already printed between surname and name; Čelebić Jovan: "you have him twice", already joined; Bubrić
  Ante: the census already had him).
- **A plain mail without permission lines** gets the facts and an unsigned note, "iz porodične arhive"; the reply offers
  to sign it with the sender's credit (Runtić Ante, Ujević Zdravko, Perkov Ante).

Not adopted: "probably changes nothing" (the lead's point 7). The user took both of S. Gojkov's "verovatno" surnames
(Bermanov Jova is Đermanov, Bukin Milan is Đukić, 6bb3bc3d), so a sender's "verovatno" about a name does not by itself
hold the change back (the entry stays as printed, as always).

## Adopted 2026-11-24, to make the reading automatic

Each is a task on the ops board (51-61); this list says what each one does once built.

1. **Proposals on /pregled.** Each form or mail is read with the card's own readers (`extract_structured_fields`) and the
   rules above, and /pregled shows the changes it would make, row by row, for one click to accept; 05 checks and applies.
2. **Relatives.** Every relative a form names (brat, sestra, otac, stric, sin, ...) is looked up on the site; /pregled
   shows "found: <record>" or "missing: propose a record" (a fighter only).
3. **Name variants** in the search and in matching: Mato/Mate, Ive/Ivo/Ivan, Jure/Juraj, Šime/Šimun, Mladin/Mladen,
   Nediljka/Nedeljka and the like (the user: "mato ujevic missing on website?").
4. **Permission lines in the mail fallback**: the mail the forms open carries the form's "Dozvola" answers, so a mailed
   form's permission is known.
5. **More war events** in the life line, wherever an entry says he took part: Kozara 1942, the liberation of Belgrade 1944,
   the Srem front 1944-45, Drvar 1944, Trieste 1945 (with the Sutjeska, the Neretva and Igman).
6. **Typos and broken letters in mailed forms**: a birth year "2025" read as 1925; a mail program's broken letters
   ("Kolund%5%Eija") read back as Kolundžija.
7. **"Koristi kao pravilo" acts**: a ticked place correction is looked for in the other entries of the same area, and
   the fixes are proposed.
8. **Photos**: a face crop is proposed for the portrait; the whole photo goes to the album without its torn edge; a book's
   portrait is never dropped.
9. **The unit he is known for stands under his name**: when the family names the unit he served or commanded in and his
   record is in another unit's book, that unit goes under the name (Antolović Josip: the 12. slavonska, not the
   Mačvanski odred).
10. **After each release**: the nob labels move 1 → 2/3/4 and the "your card is live" mails are drafted for the user to
   send. The panel can move the labels itself once the user gives it Gmail's permission to change labels (their click);
   until then the lead does it at the window.
11. **Questions and corrections in plain mail**: a mail that asks (Rubeša's "Podatak") is labelled "waiting for an answer"
   with a drafted reply, apart from one that corrects a card.

## State of the eleven (2026-11-24)

- **1, 2, 9, 11 on /pregled**: `quality/pregled_predlozi.py` (local, with `make_pregled.py`) adds rows to "Pomenuto u
  formama", each with its "Prihvatam" tick: Predlog (a field: added where the card is empty, put first where the family
  differs, a duty or unit added to the card's), Životni put (a dated step), Bitka (a war event, which make_war_events then
  writes by itself), Jedinica (into a unit on the site, or under the name: rule 9 for a brigade, division, odred or
  corps), Rodbina (each relative looked up through the site's search on :3000; "isti otac" first; a civilian gets no
  record), Pitanje (a mail that asks). Only his own sentences are read for his fields and battles: a sentence naming a
  relative tells of the relative. Test forms (TEST, PROBA, "(Claude)") are left out. Applying stays 05's.
- **3**: in the site's search (`lib/soldierSearch.ts`, NAME_VARIANTS, 4cc0b214) and in matching (`match_references.py`
  `candidates`, used by `rematch_references.py` and so the identity pass): a find through another form of the name
  carries the doubt "given?", weighed like "father?" (sure only with birth year, birthplace and death; else review).
- **4**: in the forms (4cc0b214), live with the next release.
- **5**: `make_war_events.py` (3c534cf4): kozara, neretva, sutjeska, drvar, beograd, srem, trst; the data at 05's chain.
- **6**: in Pošta (`posta.popravi_slova`, `popravi_godinu`, claude/admin-posta e4edf7b5).
- **7**: a ticked rule's "Ista greška još u N zapisa" on /pregled is filled through the site's search (needs :3000);
  applying the fixes stays 05's.
- **8**: `quality/predlog_isecaka.py` (local; run with the Python 3.7 that has OpenCV) finds the faces in every photo a
  form brought and writes a head-and-shoulders crop for each (a face with an eye, or high in the picture, first: a
  stain on the trousers is often larger than a full-length man's face) and the album's photo without a plain margin,
  or a full-length man's figure inside a torn edge, to `%USERPROFILE%\.knjiga-boraca\posta\predlozi-isecaka`; /pregled
  shows them as thumbnails in a "Fotografija" row (route `/pregled/isecak/...`). A fixer chooses and copies.
- **10**: the label moves are a step of the release window (ops `releases/README.md`); the panel moving them itself waits
  for the user's Google permission to change labels.
