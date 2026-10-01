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
     from: 'Ana Petrović, unuka',          // name and relation, as the sender gave them
     date: '2026-10',                      // month it was sent
   },
   ```

3. Build and push. The photo and story appear in the record under **Od porodice**, and the first photo
   also on the soldier's memorial card (`/kartica`).

An entry can point at an ID that was later merged into another record (`other_sources[].soldier_id`); it is
still shown on the merged record. Never publish the sender's email address.
