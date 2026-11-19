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
3. **The language** is the row "Jezik"; the link goes to the record in that language.
4. **One note per sender**: someone who sent two fighters (F. Adžić: Novaković and Đoković) gets one note with both.
5. **A new message**, not a reply in the submission's thread (a reply quotes the whole FormSubmit table and its ad), and
   no Gmail signature (it may carry the user's name).
6. **From nob.borci.kontakt@gmail.com**, written in that account itself, never in the personal one (the user's
   decision; see "Sending" below), and the link checked before Send: it must be the site's own address, not a
   google.com one.

### The note

`{ime}` is the record's name as the site shows it ("Sekulić Mane Miloš"; names stay in Latin in every language),
`{id}` its ID. It names no gender and needs no case, so it fits every record. For two or more records the subject
names them all, "u zapisu {ime}:" becomes "u zapisima:" ("v zapisih:", "во записите:", "in the records:"), and the
address becomes one line per record: `{ime}: https://heroji-nob.vercel.app/borac/{id}`.

| Jezik | Subject | Body | Address |
|---|---|---|---|
| Srpskohrvatski | Knjiga boraca: {ime} | Dobar dan,<br><br>ono što ste nam poslali sada je na sajtu, u zapisu {ime}:<br>{address}<br><br>Hvala vam što ste nam pisali.<br><br>Knjiga boraca | `https://heroji-nob.vercel.app/borac/{id}` |
| Српскохрватски | Књига бораца: {ime} | Добар дан,<br><br>оно што сте нам послали сада је на сајту, у запису {ime}:<br>{address}<br><br>Хвала вам што сте нам писали.<br><br>Књига бораца | `.../sr-cyrl/borac/{id}` |
| Slovenščina | Knjiga borcev: {ime} | Dober dan,<br><br>kar ste nam poslali, je zdaj na strani, v zapisu {ime}:<br>{address}<br><br>Hvala, ker ste nam pisali.<br><br>Knjiga borcev | `.../sl/borac/{id}` |
| Македонски | Книга на борците: {ime} | Добар ден,<br><br>она што ни го испративте сега е на сајтот, во записот {ime}:<br>{address}<br><br>Ви благодариме што ни пишавте.<br><br>Книга на борците | `.../mk/borac/{id}` |
| English | Knjiga boraca: {ime} | Hello,<br><br>What you sent us is now on the site, in the record for {ime}:<br>{address}<br><br>Thank you for writing to us.<br><br>Knjiga boraca | `.../en/borac/{id}` |

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
| nećak | 0122917644 Kovačević Pajov Dušan | yes | not yet |
| Ispravka po prijavi | 0135000797 Piperov Nikola Vlado | yes | not yet (a correction; tell if the reporter left an email) |
| B. Batalo, praunuk | 0122907839 Sekulić Mane Miloš | no, until 27653388 is pushed | not yet |

Mile Bakić's and Todor Bajić's pieces are from the family archive itself: nobody to tell.

### Ready to send (made 2026-11-19, the user sends them later)

Each link opens the note in Serbo-Croatian as a new message in the contact account; the address comes from the
submission in the contact inbox. If its "Jezik" row says another language, make that version from the table above.

- [F. Adžić: Novaković Vuka Radomir, Đoković Miodrag Dragan](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Novakovi%C4%87%20Vuka%20Radomir%2C%20%C4%90okovi%C4%87%20Miodrag%20Dragan&body=Dobar%20dan%2C%0A%0Aono%20%C5%A1to%20ste%20nam%20poslali%20sada%20je%20na%20sajtu%2C%20u%20zapisima%3A%0ANovakovi%C4%87%20Vuka%20Radomir%3A%20https%3A//heroji-nob.vercel.app/borac/0126000703%0A%C4%90okovi%C4%87%20Miodrag%20Dragan%3A%20https%3A//heroji-nob.vercel.app/borac/0136021032%0A%0AHvala%20vam%20%C5%A1to%20ste%20nam%20pisali.%0A%0AKnjiga%20boraca)
- [J. Todosijević: Todosijević Dragić Jelica](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Todosijevi%C4%87%20Dragi%C4%87%20Jelica&body=Dobar%20dan%2C%0A%0Aono%20%C5%A1to%20ste%20nam%20poslali%20sada%20je%20na%20sajtu%2C%20u%20zapisu%20Todosijevi%C4%87%20Dragi%C4%87%20Jelica%3A%0Ahttps%3A//heroji-nob.vercel.app/borac/0136006734%0A%0AHvala%20vam%20%C5%A1to%20ste%20nam%20pisali.%0A%0AKnjiga%20boraca)
- [nećak: Kovačević Pajov Dušan](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Kova%C4%8Devi%C4%87%20Pajov%20Du%C5%A1an&body=Dobar%20dan%2C%0A%0Aono%20%C5%A1to%20ste%20nam%20poslali%20sada%20je%20na%20sajtu%2C%20u%20zapisu%20Kova%C4%8Devi%C4%87%20Pajov%20Du%C5%A1an%3A%0Ahttps%3A//heroji-nob.vercel.app/borac/0122917644%0A%0AHvala%20vam%20%C5%A1to%20ste%20nam%20pisali.%0A%0AKnjiga%20boraca)
- [Ispravka po prijavi: Piperov Nikola Vlado](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Piperov%20Nikola%20Vlado&body=Dobar%20dan%2C%0A%0Aono%20%C5%A1to%20ste%20nam%20poslali%20sada%20je%20na%20sajtu%2C%20u%20zapisu%20Piperov%20Nikola%20Vlado%3A%0Ahttps%3A//heroji-nob.vercel.app/borac/0135000797%0A%0AHvala%20vam%20%C5%A1to%20ste%20nam%20pisali.%0A%0AKnjiga%20boraca) (only if the reporter left an email)
- [B. Batalo: Sekulić Mane Miloš](https://mail.google.com/mail/?authuser=nob.borci.kontakt%40gmail.com&view=cm&fs=1&su=Knjiga%20boraca%3A%20Sekuli%C4%87%20Mane%20Milo%C5%A1&body=Dobar%20dan%2C%0A%0Aono%20%C5%A1to%20ste%20nam%20poslali%20sada%20je%20na%20sajtu%2C%20u%20zapisu%20Sekuli%C4%87%20Mane%20Milo%C5%A1%3A%0Ahttps%3A//heroji-nob.vercel.app/borac/0122907839%0A%0AHvala%20vam%20%C5%A1to%20ste%20nam%20pisali.%0A%0AKnjiga%20boraca): **only after 27653388 is pushed and his record shows the story**

When one is sent, mark it in "Told so far" (the month) and take it off this list.

