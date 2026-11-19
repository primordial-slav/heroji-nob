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
