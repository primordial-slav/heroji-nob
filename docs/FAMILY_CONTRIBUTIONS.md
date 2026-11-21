# Family photos and stories ("Znam ovog borca")

Every soldier's record has a **Znam ovog borca** button. A visitor writes who they are to the soldier, what
they know, optionally attaches a photograph, gives their name (and optionally an email), and says whether it
may be published. It is sent through FormSubmit (`NEXT_PUBLIC_REPORT_EMAIL`, the same address as error
reports) with the subject `Znam ovog borca: <name> (<id>)`. The email contains the soldier's ID, unit and
link, and the photo as an attachment (resized in the browser to at most 2,400 px, JPEG).

Nothing is published automatically.

## Publishing an approved submission

Only publish when the sender ticked **Dozvola za objavu: Da**. Corrections to the record itself go into
`corrections.json` as usual.

1. Save the photo as `website/public/porodica/<soldier_id>-1.jpg` (`-2.jpg` for a second one).
   Keep it under ~500 KB; crop away scanner borders, don't retouch.
2. Add an entry to `familyContributions` in `website/app/data/family.ts`:

   ```ts
   {
     soldierId: '0002000003',
     photo: '0002000003-1.jpg',            // optional
     photoCaption: 'Petar 1946. u Bogatiću', // optional, the sender's words
     text: 'Posle rata se vratio u Belotić…', // optional, as sent; fix only spelling
     from: 'A. Petrović, unuka',            // initial, surname and relation (the user's rule of 2026-11-19: never the full name)
     date: '2026-10',                      // month it was sent
   },
   ```

3. Build and push. The photo and story appear in the record under **Od porodice**, and the first photo
   also on the soldier's memorial card (`/kartica`).

**The card's rows and life line must carry what the text says** (the user's rule of 2026-11-20, "absolutely crucial").
Before a card counts as done, open it and check every fact its text, entries and the family's papers give against the
rows and the life line ("Životni put"):
- every unit the text names in the unit row ("U jedinici" / "Jedinice"): Ćulibrk Svetko's text named the Prva and the
  Treća krajiška brigada and his card had no unit row;
- the dated steps in the life line: born, joined the NOB, came to a unit, wounded, demobilised, death. A family's entry
  is written in the phrasing `scripts/extract_life_events.py` reads ("U NOB od 15. decembra 1943, u XVI jastrebačkom
  odredu; demobilisana 15. maja 1945.", "ranjen 10. oktobra 1943. kod Oboraca"), not in prose it misses ("U NOB-u od
  ... do ...", "posle ranjavanja", "Učesnik NOR-a od 1944"). The line shows only with three dated steps, or two between
  birth and death (`shows_line`); a record with fewer has none, and no date is made up for it;
- duty, birth, death, as anywhere.
Only the rows the site already uses: the "Majka" row is for a census entry that names the mother of a man whose father
is unknown, so other parents stay in the text. For a unit record the fields go in `corrections.json`; for a Porodična
arhiva record in the entry's `fields` (`build_ostali_borci.py` copies them into the record on every rebuild, as the
field reader can't read a unit from prose) and in the record, then `extract_life_events.py --write --brigade 122`.

An entry can point at an ID that was later merged into another record (`other_sources[].soldier_id`); it is
still shown on the merged record. Never publish the sender's email address.

## More photos and documents: the album

A family may send more than one photo, and documents (a soldier's booklet, a decision on a decoration, a letter). The
first `photo` stays his portrait at the top of the record; everything else goes in `pieces`, and once there is more than
the one photo the record shows all of them, the portrait's photo first, as an album under "Od porodice" (the user's
choice of 2026-11-19, variant A of the mockups on the `admin-panel` branch, `admin/mockups/kartica-album.html`). A click
opens a piece large, with its pages and what it says; the arrows go page by page, then piece by piece.

```ts
pieces: [
  { kind: 'photo', file: '0002000242-2.jpg', caption: 'U uniformi' },     // the sender's words; none is fine
  {
    kind: 'document',
    file: '0002000242-7.jpg',                 // the first page
    pages: ['0002000242-7b.jpg'],             // the other pages, in order
    caption: 'Povelja o odlikovanju, 1984.',
    transcripts: ['What page 1 says, as written', 'What page 2 says'],  // where it is handwritten or hard to read
  },
],
```

- Photos show black and white like every portrait on the site; documents keep their paper.
- Crop a photo of a print to the print (no fingers, table or background); don't retouch. JPEG, the longer side at most
  1,600 px.
- Before a document goes up, cover anything that identifies a living person (an address, an ID number).
- Photos that show other people (family groups) go up only with the family's word for each.
- A transcription is the document's own words; write `[potpis]` for a signature and `[nečitko]` where it can't be read.

## A fighter who is not on the site

Since 2026-11-19 (the user's promise in the Reddit thread) a second form, `components/MissingSoldierForm.tsx`, stands where
a home search finds no one and under the results: "Nema ga u knjigama na sajtu? Pošaljite nam šta znate o njemu." The
line under the home search field offers it too, after the count ("508.897 imena · Nema vašeg borca? Pošaljite nam šta znate
o njemu", `MissingSoldierAsk`; the user chose it from seven versions): the form then opens right under the band, and the
copies at the end of a search wait until it is closed. A unit's page offers it the same way where its search finds no
one and under its results, with the unit's name already in the unit field (not on Borci drugih jedinica or the census's
parts). The footer of every page ends "Ako borca nema na sajtu, pošaljite nam šta znate o njemu." with a link to
`/#prijava` (`lib/missingForm.ts`), which opens the form under the home page's band. It asks
for the fighter's name (the search fills it in), father, year and place of birth, unit, fate, what the family knows, and
up to six photos of him and of his papers, then the sender's name, relation and email, and the permission to publish.

It arrives at the same address: one email "Borac kojeg nema na sajtu: <name>" with the fields (and the search that found
nothing), and one email per file, "Prilog: <name> (1/3)". Nothing is published by itself. A man it names is checked first
against the site (the search, the census of the fallen, the books across units; he may be there under another spelling),
then added by hand like the family archive's (Porodična arhiva: a record of Borci drugih jedinica with his entry as the
family gave it), his photos and papers as `pieces` (above), the sender credited by initial, surname and relation.

## Telling the family

When a family's contribution is live, its sender gets one short email with the record's address (the user's wish of
2026-11-19). Only senders who left an email; nothing goes out without the user reading it and pressing Send.

1. **Live first.** Open the record on the live site and see the story or photo under "Od porodice". A commit that is
   not pushed is not live (Sekulić Miloš's, 27653388, was not on 2026-11-19).
2. **The address** is the row "Email pošiljaoca" of the submission's table. FormSubmit's emails carry no Reply-To,
   even though the forms send `_replyto` (two submissions checked on 2026-11-19), so "Reply" would go to FormSubmit.
   The address stays in Gmail: never in the repo, a commit, a file or a note.
3. **The language** is the one the sender wrote their own text in; the row "Jezik" is only the site's language they
   had open (V. Mihić's three forms say English, he wrote Serbian), so it decides only when they wrote nothing. The
   link goes to the record in that language.
4. **One note per sender**: someone who sent two fighters (F. Adžić: Novaković and Đoković) gets one note with both.
5. **A new message**, not a reply in the submission's thread (a reply quotes the whole FormSubmit table and its ad), and
   no Gmail signature (it may carry the user's name).
6. **From nob.borci.kontakt@gmail.com**, written in that account itself, never in the personal one (the user's
   decision; see "Sending" below), and the link checked before Send: it must be the site's own address, not a
   google.com one.

### Before writing: every sentence checked against the live card

Read on 2026-11-21 against every form so far (the audit is local, `quality/odgovori-pregled-2026-11-21.md`). A reply
says only what the sender can see when they open the link, and the generic note below ("what you sent is now on the
site") is true only when all of it went up. For each sender:

1. **All their messages first.** Every form they sent (the same man may come in several forms, one a record:
   V. Mihić's three), their answers to earlier emails in the contact inbox (Z. Rutešić gave his permission in a reply,
   unseen for 16 hours), and what was already sent to them ("Told so far").
2. **Count the files.** Each form's "Prilozi" row says how many follow; count the "Fotografija: …" / "Prilog: …"
   messages that came. One a form over three forms is three; the same form sent four times is one (M. Palčič). Lost
   files are named in the reply ("the three photos you attached: the portrait from …"), with the ask to send them as
   an attachment to a reply.
3. **Open the card on the live site** (in a browser: the family notes render in the page) and list what the sender
   gave, fact by fact, against it: in the note, in a row, in the album, or left out. Each goes in the reply as it
   stands:
   - on the card: say where ("on his card, credited to you" / "without your name, as you asked");
   - shown beside the book's version ("1976 ili 1984"): say both are shown and why ("the 1. bataljon book prints
     1984"), never "corrected";
   - in the note but not in the rows (Kovačević's Srem front in April 1945, the rows say May 1945, Slavonija): first
     fix the rows by the card-rows rule above; if it stays out, say so;
   - translated (E. Goldrick's English, shown in Serbo-Croatian): say so;
   - not used: say what and why (no permission to publish the text, only the dates were taken; unclear; not a war
     fact).
4. **Ask only for what the card and the forms both lack.** Read the rows and every reference first ("where did he
   fall" was asked of a card that gives 8 March 1945, Ritešić, from two books). At most one or two asks.
5. **Links** go to the record where the change shows: of linked records, the one with the corrected name (Mihić's
   14. srednjobosanska record keeps the book's "G Maksim"); for a split or a new record, its new ID.
6. **Doubts on the card come first.** If the card disagrees with the family on who he was (M. Palčič's great-grandfather
   lived to 2007, the only reference is a list of the fallen; Gaković's rows say Banjani near Bosanska Krupa, the note
   near Bosanski Brod), settle it, or ask the sender, before writing "his card".
7. **Only what was seen working.** No "I fixed it" for the site until a real case went through; "I changed it" is true.
8. **Record the send** in "Told so far": the date, and what was promised ("adds the photos when they come"), so the
   next reply keeps the promise. A reply the user writes in the contact account goes in too (D. Krnić's of 11-19,
   Z. Rutešić's of 11-20 weren't).

The order of a reply, from the user's own two (D. Krnić 11-19, Z. Rutešić 11-20): greeting by first name, thanks,
what the card has now as a short list of the changes (photo, birth year, name taken off "as you asked in your later
form"), what isn't there and why, the one ask, the link, an invitation to write again if something is wrong. The
signature is open (the user signs "Projekat Heroji NOB-a", the outreach letters "Projekat Knjiga boraca", the photo
requests of 11-21 "Boris / Knjiga boraca"): ask the user until it is decided.

### The note

In the user's own formal voice (memory: their Reddit post; approved 2026-11-19): a plain greeting, the news, thanks,
why the site exists, an invitation to write back, "Hvala vam na vremenu." First person, as the user writes.

`{ime}` is the record's name as the site shows it ("Sekulić Mane Miloš"; names stay in Latin in every language),
`{id}` its ID. It names no gender and needs no case, so it fits every record. For two or more records the subject
names them all, "u zapisu {ime}:" becomes "u zapisima:" ("v zapisih:", "во записите:", "in the records:"), and the
address becomes one line per record: `{ime}: https://heroji-nob.vercel.app/borac/{id}`.

| Jezik | Subject | Body | Address |
|---|---|---|---|
| Srpskohrvatski | Knjiga boraca: {ime} | Pozdrav,<br><br>javljam vam da je ono što ste poslali sada na sajtu, u zapisu {ime}:<br>{address}<br><br>Hvala vam što ste ovo podelili. Sajt sam napravio da bi porodice lakše našle svoje borce, a priče i fotografije poput vaše ga čine mnogo bogatijim. Ako primetite nešto što treba ispraviti, ili imate još fotografija ili dokumenata, slobodno mi pišite.<br><br>Hvala vam na vremenu.<br>Knjiga boraca | `https://heroji-nob.vercel.app/borac/{id}` |
| Српскохрватски | Књига бораца: {ime} | Поздрав,<br><br>јављам вам да је оно што сте послали сада на сајту, у запису {ime}:<br>{address}<br><br>Хвала вам што сте ово поделили. Сајт сам направио да би породице лакше нашле своје борце, а приче и фотографије попут ваше га чине много богатијим. Ако приметите нешто што треба исправити, или имате још фотографија или докумената, слободно ми пишите.<br><br>Хвала вам на времену.<br>Књига бораца | `.../sr-cyrl/borac/{id}` |
| Slovenščina | Knjiga borcev: {ime} | Pozdravljeni,<br><br>sporočam vam, da je to, kar ste poslali, zdaj na strani, v zapisu {ime}:<br>{address}<br><br>Hvala, ker ste to delili. Stran sem naredil zato, da bi družine lažje našle svoje borce, zgodbe in fotografije, kot je vaša, pa jo zelo obogatijo. Če opazite kaj, kar je treba popraviti, ali imate še kakšne fotografije ali dokumente, mi kar pišite.<br><br>Hvala za vaš čas.<br>Knjiga borcev | `.../sl/borac/{id}` |
| Македонски | Книга на борците: {ime} | Поздрав,<br><br>ве известувам дека она што го испративте сега е на сајтот, во записот {ime}:<br>{address}<br><br>Ви благодарам што го споделивте ова. Сајтот го направив за семејствата полесно да ги најдат своите борци, а приказните и фотографиите како вашата го прават многу побогат. Ако забележите нешто што треба да се поправи, или имате уште фотографии или документи, слободно пишете ми.<br><br>Ви благодарам за вашето време.<br>Книга на борците | `.../mk/borac/{id}` |
| English | Knjiga boraca: {ime} | Hello,<br><br>I wanted to let you know that what you sent is now on the site, in the record for {ime}:<br>{address}<br><br>Thank you for sharing it. I built the site so families could find their relatives more easily, and stories and photos like yours make it much richer. If you notice anything that should be corrected, or have more photos or documents, feel free to write to me.<br><br>Thank you for your time.<br>Knjiga boraca | `.../en/borac/{id}` |

### Sending: what the test of 2026-11-19 showed

Three test drafts, addressed to the user's own address only:

- The Gmail connector in Claude reaches the personal account, and `create_draft` has no From: every draft it makes
  is From the personal account's name and address, a reply in the submission's thread too. No "Send mail as"
  address was set up, so Gmail's "reply from the same address the message was sent to" could not be tried.
- A draft made with `replyToMessageId` stays in the submission's thread (In-Reply-To set), with the subject
  "Re: Znam ovog borca: ...", and quotes the submission whole.
- The connector rewrites every link in a draft, in the plain text and in an HTML `href` alike, into a
  `google.com/url?q=...&ust=...` redirect; the text shown stays the true address. Such a link stops working once the
  `ust` time passes, so the link has to be put in again by hand in Gmail before Send.
- The contact inbox forwards to the personal one only since 2026-11-19, 00:30 UTC (Gmail's forwarding confirmation).
  Earlier submissions (F. Adžić's, J. Todosijević's, the nephew's, the Piperov report) are only in the contact inbox.

**Decided (the user, 2026-11-19): the notes go out from the nob.borci.kontakt account itself**, never from the
personal one, not even through "Send mail as". So the connector's drafts are not used for them. For each note Claude
gives the user the filled-in text and a link that opens it as a new message in the contact account (Gmail's compose
address: `https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=...&body=...`, the
subject and body URL-encoded, no address in it). The user, signed in to the contact account in the browser, opens it,
checks that From shows nob.borci.kontakt@gmail.com, pastes the address from the submission and presses Send. Gmail
makes the link itself, so it is the site's own. If the link opens the personal account instead, the note is copied
into a new message in the contact account by hand.

### Later: "Obavesti porodicu" in the admin panel

The local admin panel (branch `admin-panel`, publish step `admin/mockups/objavi.html`) should get an "Obavesti porodicu"
step after the push and the check of the live site: for each published contribution whose sender left an email, the
note above in the sender's language, read and changed there, then opened as a new message in the contact account to
be sent by hand (Gmail's compose address with the contact account's `authuser`, the subject and body filled, the
address taken from the mailbox when the button is pressed, never stored). Not built yet.

### Told so far

| Credit on the site | Record | Live | Told |
|---|---|---|---|
| F. Adžić, rođak / F. Adžić | 0126000703 Novaković Vuka Radomir, 0136021032 Đoković Miodrag Dragan | yes | not yet |
| J. Todosijević, bratanica | 0136006734 Todosijević Dragić Jelica | yes | not yet |
| nećak (Kovačević's) | 0122917644 Kovačević Pajov Dušan | yes | not yet |
| Ispravka po prijavi | 0135000797 Piperov Nikola Vlado | yes | not yet (a correction; tell if the reporter left an email) |
| B. Batalo, praunuk | 0122907839 Sekulić Mane Miloš, 0060000921 Kosanović Milovana Manojlo | yes (Žumberak since 90bb8d91) | not yet |
| N. Kaišarević | 0122957805 Kupres Marka Miloš | yes | not yet |
| nećak (the Eftimovskis') | 0122959606 Eftimovski Gjore, 0135001012 Eftimovski Božo Kiro | yes | not yet |
| B. Obradović, unuk | 0042000145 Gaković Gojka Milorad | yes | nobody to tell (no address given) |
| (no credit: his grandson's last form said "Ne" to his name, the user 11-19) | 0122959607 Krnić Blaž | yes (record, note, photo as portrait, born 1926) | 2026-11-19, by the user (photo, birth year, name taken off; the Bari note went up after) |
| (nothing published: "Ne") | 0041000831 Milović Petra Lazar | no | 2026-11-20, by the user (asked whether some war facts may go up unsigned); he answered 11-21: yes, with a new account, waiting for the user |
| E. Goldrick, istoričar | 0069002027 Čolnik Karel | yes (note, translated) | 2026-11-21: asked to resend his three photos by reply; promised to add them with his captions |
| V. Mihić (no credit yet: no text) | 0001007129, 0033000402, 0056001266 Mihić Maksim | yes (Maksim, linked) | 2026-11-21: asked to resend the photos by reply; promised to add them |
| M. Palčič, praunuk | 0067000827 Palčič Dino | yes (note, surname, death 2007) | 2026-11-21: asked to resend the photo by reply; promised to add it |

Mile Bakić's and Todor Bajić's pieces are from the family archive itself: nobody to tell.

### Ready to send (made 2026-11-19, the user sends them later)

Each link opens the note as a new message in the contact account, in Serbo-Croatian unless it says otherwise; the
address comes from the submission. Each must pass "Before writing" above first: the generic text is true as it stands for F. Adžić,
N. Kaišarević, B. Batalo and the Eftimovskis' nephew; Kovačević's card gives his death as the books do (May 1945,
Slavonija), not as the nephew wrote (the Srem front, early April 1945), so the row comes first; J. Todosijević's
reply says the census's 1945, Rušanj stays in the row and the family's account is in the note. Krnić's grandson was
told by the user on 11-19. If its "Jezik" row says another language, make that version from the table above.

- [F. Adžić: Novaković Vuka Radomir, Đoković Miodrag Dragan](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Novakovi%C4%87%20Vuka%20Radomir%2C%20%C4%90okovi%C4%87%20Miodrag%20Dragan&body=Pozdrav%2C%0A%0Ajavljam%20vam%20da%20je%20ono%20%C5%A1to%20ste%20poslali%20sada%20na%20sajtu%2C%20u%20zapisima%3A%0ANovakovi%C4%87%20Vuka%20Radomir%3A%20https%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0126000703%0A%C4%90okovi%C4%87%20Miodrag%20Dragan%3A%20https%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0136021032%0A%0AHvala%20vam%20%C5%A1to%20ste%20ovo%20podelili.%20Sajt%20sam%20napravio%20da%20bi%20porodice%20lak%C5%A1e%20na%C5%A1le%20svoje%20borce%2C%20a%20pri%C4%8De%20i%20fotografije%20poput%20va%C5%A1e%20ga%20%C4%8Dine%20mnogo%20bogatijim.%20Ako%20primetite%20ne%C5%A1to%20%C5%A1to%20treba%20ispraviti%2C%20ili%20imate%20jo%C5%A1%20fotografija%20ili%20dokumenata%2C%20slobodno%20mi%20pi%C5%A1ite.%0A%0AHvala%20vam%20na%20vremenu.%0AKnjiga%20boraca)
- [J. Todosijević: Todosijević Dragić Jelica](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Todosijevi%C4%87%20Dragi%C4%87%20Jelica&body=Pozdrav%2C%0A%0Ajavljam%20vam%20da%20je%20ono%20%C5%A1to%20ste%20poslali%20sada%20na%20sajtu%2C%20u%20zapisu%20Todosijevi%C4%87%20Dragi%C4%87%20Jelica%3A%0Ahttps%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0136006734%0A%0AHvala%20vam%20%C5%A1to%20ste%20ovo%20podelili.%20Sajt%20sam%20napravio%20da%20bi%20porodice%20lak%C5%A1e%20na%C5%A1le%20svoje%20borce%2C%20a%20pri%C4%8De%20i%20fotografije%20poput%20va%C5%A1e%20ga%20%C4%8Dine%20mnogo%20bogatijim.%20Ako%20primetite%20ne%C5%A1to%20%C5%A1to%20treba%20ispraviti%2C%20ili%20imate%20jo%C5%A1%20fotografija%20ili%20dokumenata%2C%20slobodno%20mi%20pi%C5%A1ite.%0A%0AHvala%20vam%20na%20vremenu.%0AKnjiga%20boraca)
- [nećak: Kovačević Pajov Dušan](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Kova%C4%8Devi%C4%87%20Pajov%20Du%C5%A1an&body=Pozdrav%2C%0A%0Ajavljam%20vam%20da%20je%20ono%20%C5%A1to%20ste%20poslali%20sada%20na%20sajtu%2C%20u%20zapisu%20Kova%C4%8Devi%C4%87%20Pajov%20Du%C5%A1an%3A%0Ahttps%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0122917644%0A%0AHvala%20vam%20%C5%A1to%20ste%20ovo%20podelili.%20Sajt%20sam%20napravio%20da%20bi%20porodice%20lak%C5%A1e%20na%C5%A1le%20svoje%20borce%2C%20a%20pri%C4%8De%20i%20fotografije%20poput%20va%C5%A1e%20ga%20%C4%8Dine%20mnogo%20bogatijim.%20Ako%20primetite%20ne%C5%A1to%20%C5%A1to%20treba%20ispraviti%2C%20ili%20imate%20jo%C5%A1%20fotografija%20ili%20dokumenata%2C%20slobodno%20mi%20pi%C5%A1ite.%0A%0AHvala%20vam%20na%20vremenu.%0AKnjiga%20boraca)
- [Ispravka po prijavi: Piperov Nikola Vlado (only if the reporter left an address)](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Piperov%20Nikola%20Vlado&body=Pozdrav%2C%0A%0Ajavljam%20vam%20da%20je%20ono%20%C5%A1to%20ste%20poslali%20sada%20na%20sajtu%2C%20u%20zapisu%20Piperov%20Nikola%20Vlado%3A%0Ahttps%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0135000797%0A%0AHvala%20vam%20%C5%A1to%20ste%20ovo%20podelili.%20Sajt%20sam%20napravio%20da%20bi%20porodice%20lak%C5%A1e%20na%C5%A1le%20svoje%20borce%2C%20a%20pri%C4%8De%20i%20fotografije%20poput%20va%C5%A1e%20ga%20%C4%8Dine%20mnogo%20bogatijim.%20Ako%20primetite%20ne%C5%A1to%20%C5%A1to%20treba%20ispraviti%2C%20ili%20imate%20jo%C5%A1%20fotografija%20ili%20dokumenata%2C%20slobodno%20mi%20pi%C5%A1ite.%0A%0AHvala%20vam%20na%20vremenu.%0AKnjiga%20boraca)
- [N. Kaišarević: Kupres Marka Miloš](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Kupres%20Marka%20Milo%C5%A1&body=Pozdrav%2C%0A%0Ajavljam%20vam%20da%20je%20ono%20%C5%A1to%20ste%20poslali%20sada%20na%20sajtu%2C%20u%20zapisu%20Kupres%20Marka%20Milo%C5%A1%3A%0Ahttps%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0122957805%0A%0AHvala%20vam%20%C5%A1to%20ste%20ovo%20podelili.%20Sajt%20sam%20napravio%20da%20bi%20porodice%20lak%C5%A1e%20na%C5%A1le%20svoje%20borce%2C%20a%20pri%C4%8De%20i%20fotografije%20poput%20va%C5%A1e%20ga%20%C4%8Dine%20mnogo%20bogatijim.%20Ako%20primetite%20ne%C5%A1to%20%C5%A1to%20treba%20ispraviti%2C%20ili%20imate%20jo%C5%A1%20fotografija%20ili%20dokumenata%2C%20slobodno%20mi%20pi%C5%A1ite.%0A%0AHvala%20vam%20na%20vremenu.%0AKnjiga%20boraca)
- [The Eftimovskis' nephew: Eftimovski Gjore, Eftimovski Božo Kiro, in Macedonian](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=%D0%9A%D0%BD%D0%B8%D0%B3%D0%B0%20%D0%BD%D0%B0%20%D0%B1%D0%BE%D1%80%D1%86%D0%B8%D1%82%D0%B5%3A%20Eftimovski%20Gjore%2C%20Eftimovski%20Bo%C5%BEo%20Kiro&body=%D0%9F%D0%BE%D0%B7%D0%B4%D1%80%D0%B0%D0%B2%2C%0A%0A%D0%B2%D0%B5%20%D0%B8%D0%B7%D0%B2%D0%B5%D1%81%D1%82%D1%83%D0%B2%D0%B0%D0%BC%20%D0%B4%D0%B5%D0%BA%D0%B0%20%D0%BE%D0%BD%D0%B0%20%D1%88%D1%82%D0%BE%20%D0%B3%D0%BE%20%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D1%82%D0%B8%D0%B2%D1%82%D0%B5%20%D1%81%D0%B5%D0%B3%D0%B0%20%D0%B5%20%D0%BD%D0%B0%20%D1%81%D0%B0%D1%98%D1%82%D0%BE%D1%82%2C%20%D0%B2%D0%BE%20%D0%B7%D0%B0%D0%BF%D0%B8%D1%81%D0%B8%D1%82%D0%B5%3A%0AEftimovski%20Gjore%3A%20https%3A%2F%2Fheroji-nob.vercel.app%2Fmk%2Fborac%2F0122959606%0AEftimovski%20Bo%C5%BEo%20Kiro%3A%20https%3A%2F%2Fheroji-nob.vercel.app%2Fmk%2Fborac%2F0135001012%0A%0A%D0%92%D0%B8%20%D0%B1%D0%BB%D0%B0%D0%B3%D0%BE%D0%B4%D0%B0%D1%80%D0%B0%D0%BC%20%D1%88%D1%82%D0%BE%20%D0%B3%D0%BE%20%D1%81%D0%BF%D0%BE%D0%B4%D0%B5%D0%BB%D0%B8%D0%B2%D1%82%D0%B5%20%D0%BE%D0%B2%D0%B0.%20%D0%A1%D0%B0%D1%98%D1%82%D0%BE%D1%82%20%D0%B3%D0%BE%20%D0%BD%D0%B0%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%B2%20%D0%B7%D0%B0%20%D1%81%D0%B5%D0%BC%D0%B5%D1%98%D1%81%D1%82%D0%B2%D0%B0%D1%82%D0%B0%20%D0%BF%D0%BE%D0%BB%D0%B5%D1%81%D0%BD%D0%BE%20%D0%B4%D0%B0%20%D0%B3%D0%B8%20%D0%BD%D0%B0%D1%98%D0%B4%D0%B0%D1%82%20%D1%81%D0%B2%D0%BE%D0%B8%D1%82%D0%B5%20%D0%B1%D0%BE%D1%80%D1%86%D0%B8%2C%20%D0%B0%20%D0%BF%D1%80%D0%B8%D0%BA%D0%B0%D0%B7%D0%BD%D0%B8%D1%82%D0%B5%20%D0%B8%20%D1%84%D0%BE%D1%82%D0%BE%D0%B3%D1%80%D0%B0%D1%84%D0%B8%D0%B8%D1%82%D0%B5%20%D0%BA%D0%B0%D0%BA%D0%BE%20%D0%B2%D0%B0%D1%88%D0%B0%D1%82%D0%B0%20%D0%B3%D0%BE%20%D0%BF%D1%80%D0%B0%D0%B2%D0%B0%D1%82%20%D0%BC%D0%BD%D0%BE%D0%B3%D1%83%20%D0%BF%D0%BE%D0%B1%D0%BE%D0%B3%D0%B0%D1%82.%20%D0%90%D0%BA%D0%BE%20%D0%B7%D0%B0%D0%B1%D0%B5%D0%BB%D0%B5%D0%B6%D0%B8%D1%82%D0%B5%20%D0%BD%D0%B5%D1%88%D1%82%D0%BE%20%D1%88%D1%82%D0%BE%20%D1%82%D1%80%D0%B5%D0%B1%D0%B0%20%D0%B4%D0%B0%20%D1%81%D0%B5%20%D0%BF%D0%BE%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%2C%20%D0%B8%D0%BB%D0%B8%20%D0%B8%D0%BC%D0%B0%D1%82%D0%B5%20%D1%83%D1%88%D1%82%D0%B5%20%D1%84%D0%BE%D1%82%D0%BE%D0%B3%D1%80%D0%B0%D1%84%D0%B8%D0%B8%20%D0%B8%D0%BB%D0%B8%20%D0%B4%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D0%B8%2C%20%D1%81%D0%BB%D0%BE%D0%B1%D0%BE%D0%B4%D0%BD%D0%BE%20%D0%BF%D0%B8%D1%88%D0%B5%D1%82%D0%B5%20%D0%BC%D0%B8.%0A%0A%D0%92%D0%B8%20%D0%B1%D0%BB%D0%B0%D0%B3%D0%BE%D0%B4%D0%B0%D1%80%D0%B0%D0%BC%20%D0%B7%D0%B0%20%D0%B2%D0%B0%D1%88%D0%B5%D1%82%D0%BE%20%D0%B2%D1%80%D0%B5%D0%BC%D0%B5.%0A%D0%9A%D0%BD%D0%B8%D0%B3%D0%B0%20%D0%BD%D0%B0%20%D0%B1%D0%BE%D1%80%D1%86%D0%B8%D1%82%D0%B5)
- [B. Batalo: Sekulić Mane Miloš, Kosanović Milovana Manojlo](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Sekuli%C4%87%20Mane%20Milo%C5%A1%2C%20Kosanovi%C4%87%20Milovana%20Manojlo&body=Pozdrav%2C%0A%0Ajavljam%20vam%20da%20je%20ono%20%C5%A1to%20ste%20poslali%20sada%20na%20sajtu%2C%20u%20zapisima%3A%0ASekuli%C4%87%20Mane%20Milo%C5%A1%3A%20https%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0122907839%0AKosanovi%C4%87%20Milovana%20Manojlo%3A%20https%3A%2F%2Fheroji-nob.vercel.app%2Fborac%2F0060000921%0A%0AHvala%20vam%20%C5%A1to%20ste%20ovo%20podelili.%20Sajt%20sam%20napravio%20da%20bi%20porodice%20lak%C5%A1e%20na%C5%A1le%20svoje%20borce%2C%20a%20pri%C4%8De%20i%20fotografije%20poput%20va%C5%A1e%20ga%20%C4%8Dine%20mnogo%20bogatijim.%20Ako%20primetite%20ne%C5%A1to%20%C5%A1to%20treba%20ispraviti%2C%20ili%20imate%20jo%C5%A1%20fotografija%20ili%20dokumenata%2C%20slobodno%20mi%20pi%C5%A1ite.%0A%0AHvala%20vam%20na%20vremenu.%0AKnjiga%20boraca)

When one is sent, mark it in "Told so far" (the month) and take it off this list.

