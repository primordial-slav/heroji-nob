# Releases: when the site goes live, and its version

The user's rules of 2026-11-23 (every push to `prod` is a Vercel build, which costs; and families wait for "it's live"
before they are told). What happens at each window, step by step, is in the private ops repo,
`E:\Projects\knjiga-boraca-ops\releases\README.md`; its release notes are there too, one file a version.

## When

- **Only the lead pushes** (00-TEAM LEAD). Every other session commits to `main` (or its branch) and tells the lead;
  it never pushes, to either remote.
- **The daily window, 21:00.** Everything committed and checked goes out together once a day: one production build
  check, the push to `origin` and `prod`, a look at the live site, then the sessions waiting on it (13 for families'
  notices) are told. A day with nothing new has no release. An app scheduled task opens the window, so it runs whether
  or not a lead session is open.
- **Three lanes:**
  - **At once** (outside the window): the site is broken; someone asks us to take something down (privacy); a card
    says something gravely wrong that a family flagged (a man shown as fallen who lived). A Z version.
  - **The daily window:** everything else: family notes and photos, form fixes, new records, small features.
  - **Sunday's window:** large runs: a new book or unit, a rule that changes thousands of cards, a change of design.
    They stay on their branches during the week and the lead merges them on Sunday before the window; the Dopune item
    for them is drafted on Saturday for the user to read.
- **The user's word overrides all of it.** "Push now" from the user goes at once, whatever the window or the lane.

## Version: X.Y.Z, by how serious the release is

Each release is an annotated git tag `vX.Y.Z` on the commit that went live (pushed with it, `--follow-tags`), its
message the date and a line on what it carries. `v1.0.0` is the site as it was live on 2026-11-23 before these rules
(aada8268; knjigaboraca.org since 2026-11-21).

- **Z (1.0.0 → 1.0.1): fixes.** Data fixes, families' notes and photos, corrections from the forms, a new record a
  form asked for, a small bug fixed. Nothing a visitor has not seen before.
- **Y (1.0.1 → 1.1.0): something new to see or use.** A new book or unit; a new field in a form, a new row or mark on
  the card, a new page; a rule that changes more than about a thousand cards; a change of design.
- **X (1.1.0 → 2.0.0): the site's shape changes.** A new section, a new language, a redesign of the whole, addresses
  that change. Only with the user's word.

When one release carries several kinds, the most serious decides. A rollback is Vercel's own (promote the previous
deployment: no build); the tag says which deployment that is.
