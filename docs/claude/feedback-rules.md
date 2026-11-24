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
- What a family tells of a battle is a step of the life line and a line under the facts: Sutjeska, Neretva (any entry
  that says he was in it), Igman (`scripts/make_war_events.py`; the user, 2026-11-23 and 2026-11-24).
- A life line is drawn from two dated steps (`extract_life_events.shows_line`; 2026-11-23).
- A nickname stands by the name, in quotes (`lib/records.ts`, `nicknameOf`; 2026-11-23).
- A form naming the Partizanska spomenica is flagged on /pregled (`make_pregled.spomenica_mentions`).
- The forms about one person, and the records they touch, are one case on /pregled (`make_pregled.make_cases`).
- A book's portrait a family's photo replaced stays on the card, last in the album (`portraits.replacedPortrait`; 2026-11-24).
- A form that came by mail is a form, with its fields (Pošta, `posta.forma_mejlom`; 2026-11-24).
- A card a family added to carries the family's dot (`components/FamilyMark.tsx`; 2026-11-23).

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
- **A living person's office** is dated ("predsednik ... u novembru 2026"), never "sada".
- **A place correction ticked "Koristi kao pravilo"** on /pregled is kept in `quality/pregled-pravila.json` (so far
  Sindija → Sirdija).

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
