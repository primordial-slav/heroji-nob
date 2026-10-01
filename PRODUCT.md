# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: families and descendants looking for a relative who fought in a Partisan unit. They arrive with a surname or a name remembered from family stories, often on a phone, and are often not comfortable with technology. Secondary: historians and genealogists who check a record against the scanned source page.

## Product Purpose
Knjiga boraca makes the printed rosters of Yugoslav Partisan units ("knjige boraca") searchable by name. Success is a visitor typing a name, finding the person, and seeing the exact line in the original book that the record came from.

## Positioning
Every record links back to its line on the scanned page of the printed book, so a visitor can verify it with their own eyes. The records are transcriptions, not a new compilation.

## Operating Context
- Data comes from OCR'd PDF books, one or more per unit; records carry the page and position of the entry.
- Serbo-Croatian UI (Latin script, mostly ekavian with some ijekavian unit texts); names may carry diacritics that visitors type without (č/c, ć/c, š/s, ž/z, đ/dj).
- Static site (Next.js static export), dark and light themes, error reports go through a form.

## Capabilities and Constraints
- Global search across all units on the home page; per-unit search on each unit page; a record view with the PDF viewer and highlight; Izvori lists the source PDFs. The O nama and Kontakt pages were removed at the owner's request (2026-09-30); errors are reported from each record.
- The page structure above stays: home = search plus unit photo cards, a page per unit, record popup with the PDF viewer, Izvori.
- Keep the unit photos, the light/dark/system theme toggle, and a Partisan red accent.

## Brand Commitments
- Name: Knjiga boraca.
- Partisan red stays part of the identity.
- Must not feel like a startup/SaaS product, and must not feel academic or like a library catalogue.
- The owner does not want statistics (totals, charts). Units on the home page are grouped by the year they were formed, oldest first (owner's request, 2026-10-01).
- The owner likes unit cards with a large photograph on top; keep them.

## Evidence on Hand
Unit photos (`website/public/images/`), source PDFs (`website/public/pdfs/`), PDF thumbnails, per-unit descriptions in `website/app/data/units.ts`.

## Product Principles
1. The name is the content: finding one person matters more than browsing the collection.
2. Show the source: the printed line is the proof.
3. Plain language for people who are not researchers.
4. Respect without costume: no fake age, no decorative symbols.
