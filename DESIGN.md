---
name: Knjiga boraca
description: Spiskovi boraca partizanskih jedinica, pretraživi po imenu, sa stranom iz knjige uz svaki zapis.
colors:
  partisan-red: "#9a2226"
  partisan-red-deep: "#7b1a1d"
  red-ink: "#8e1f20"
  on-red: "#ffffff"
  on-red-muted: "#f3d9d6"
  ground: "#f0eeea"
  surface: "#fbfaf8"
  surface-sunk: "#e4e1db"
  ink: "#1c1a18"
  ink-muted: "#58534d"
  rule: "#d8d4cd"
  rule-strong: "#b6b0a8"
  highlight: "#fff0a8"
  highlight-edge: "#c79a00"
  dark-ground: "#1f1e1c"
  dark-surface: "#292826"
  dark-ink: "#ebe8e3"
  dark-ink-muted: "#a8a29a"
  dark-partisan-red: "#7a1c1f"
  dark-red-ink: "#eb8a80"
typography:
  name:
    fontFamily: "PT Serif, Georgia, Times New Roman, serif"
    fontSize: "1.0625rem"
    fontWeight: 700
    lineHeight: 1.3
  heading:
    fontFamily: "PT Serif, Georgia, Times New Roman, serif"
    fontSize: "1.5rem"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  page-title:
    fontFamily: "PT Serif, Georgia, Times New Roman, serif"
    fontSize: "1.875rem"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Golos Text, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
  small:
    fontFamily: "Golos Text, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.45
rounded:
  control: "2px"
  none: "0"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "24px"
  "6": "32px"
  "7": "40px"
  "8": "56px"
components:
  button-primary:
    backgroundColor: "{colors.partisan-red}"
    textColor: "{colors.on-red}"
    rounded: "{rounded.control}"
    height: "36px"
    padding: "0 12px"
  button-primary-hover:
    backgroundColor: "{colors.partisan-red-deep}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    height: "36px"
    padding: "0 12px"
  search-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    height: "44px"
    padding: "0 16px 0 40px"
  unit-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.none}"
    padding: "12px 16px 16px"
  masthead:
    backgroundColor: "{colors.partisan-red}"
    textColor: "{colors.on-red}"
---

# Design System: Knjiga boraca

## Overview

**Creative North Star: "Red cloth and brigade photographs"**

Knjiga boraca is where a family member types a remembered name and finds one person in the printed rosters of Partisan units. The design keeps that job in front: a solid Partisan red band holds the search, the brigades' own black-and-white photographs carry the feeling, and every record ends with the scanned line from the book. Everything else stays quiet: neutral ground, ink text, 1px rules, square corners, small restrained type.

The photographs are the only emotional material. They are real, black and white, and shown large: behind the red band on the home page (multiplied into the red), as the whole top of each unit card, full width on a unit page, and as a strip above a person's record. There is no decoration beyond them.

**Key Characteristics:**
- A solid red band (header, and on the home page the search) with one brigade photograph multiplied into it.
- Black-and-white brigade photographs, large, never thumbnails.
- Names in PT Serif, surname first and bold, as the books print them; everything else in Golos Text.
- Neutral ground, ink text, hairline rules, square corners, no shadows except the record popup.
- Small, calm type scale; nothing shouts.

## Colors

A restrained palette: warm neutrals do almost all the work, one Partisan red owns the band and the primary action, and a highlighter yellow exists only on the scanned page.

### Primary
- **Partisan red** (partisan-red): the header band, the home search band, primary buttons, the 3px rule under a record's photo strip. In dark mode it deepens (dark-partisan-red) so the band does not glare.
- **Red ink** (red-ink): links, soldier counts on unit cards, hover state of names. Lighter in dark mode (dark-red-ink) to hold contrast.

### Neutral
- **Ground** (ground): the page background, a warm light grey, never cream.
- **Surface** (surface): unit cards, the search field, the record popup's scan viewer frame.
- **Sunk surface** (surface-sunk): image placeholders, hover fills on small controls.
- **Ink / Muted ink** (ink, ink-muted): text; muted for bios, descriptions and labels.
- **Rules** (rule, rule-strong): 1px dividers between results, around the scan viewer, under the results count.

### Tertiary
- **Highlighter** (highlight, highlight-edge): only the box that marks a soldier's entry on the scanned page, with a 2px darker bottom edge.

### Named Rules
**The One Red Rule.** Red is for the band, the primary action and links. It never fills cards, never tints text blocks, and never appears as a decorative border.

**The Photograph Carries the Feeling Rule.** Emotion comes from the real brigade photographs, shown in black and white. Do not add colour washes, textures, stars or symbols to supply feeling instead.

## Typography

**Name Font:** PT Serif (with Georgia, Times New Roman)
**UI Font:** Golos Text (with Segoe UI, Roboto, Arial)

Both are self-hosted through next/font with Latin, Latin Extended and Cyrillic subsets, so č ć đ š ž and Cyrillic names render in the real faces.

### Hierarchy
- **Page title** (400, 1.875rem, PT Serif): unit page and Izvori titles; the home band's heading ("Pretraga boraca") uses the heading size.
- **Heading** (400, 1.5rem, PT Serif): section heads such as "Jedinice", the record name in the popup (1.25rem there).
- **Name** (700 surname + 400 given names, 1.0625rem, PT Serif): result rows and unit card names. The surname is always bold and first.
- **Body** (400, 0.9375rem / 15px, Golos Text, line-height 1.55): bios, descriptions, UI text.
- **Small** (400, 0.8125rem / 13px, Golos Text): labels, counts, captions, the photo credit.

### Named Rules
**The Surname First Rule.** Names are written as the books print them: surname (bold), then father's name and given name (regular). Never reorder to "First Last" in lists.

**The Quiet Scale Rule.** The largest text on any page is 1.875rem, with one exception: the year markers over the units on the home page (PT Serif regular, up to 4rem). Headings are regular weight; bold is reserved for surnames and counts.

## Layout

One centred column (max 72rem) with a 24px side gutter (16px on phones). Content that runs full width (the home band photograph, the unit page photograph) aligns its text with the column edge.

- **Home:** red band with a short heading, the search field (max 34rem) and example searches; under it "Na današnji dan", then "Jedinice": the photo cards grouped by the year the unit was formed, oldest first. Each year is a large PT Serif number, right-aligned, sitting on a 2px red rule, with that year's cards below (three per row on desktop, min 20rem per card; one per row on phones). Formation dates live in `website/app/data/formation.ts`. When the visitor searches, results replace all of this in place.
- **Results:** one row per person, 1px rule between rows: name, a bio line (up to 2 lines), unit name in muted small text. Pagination below.
- **Unit page:** full-width photograph (about 11–21rem tall), then back link, unit name and description, then the unit search and its results.
- **Record popup:** max 40rem wide; unit photo strip, name, unit, book line, details as a two-column label/value list, then the scanned page ("Strana u knjizi").
- **Spacing:** a 4px-based scale (4, 8, 12, 16, 24, 32, 40, 56px); more space above a group than inside it.
- **Breakpoint:** 640px. Below it the nav drops to its own row, cards stack, the popup fills the screen.

## Elevation & Depth

Flat. Structure comes from the red band, photographs and 1px rules, not shadows.

### Shadow Vocabulary
- **Popup lift** (0 24px 48px -12px rgba(0,0,0,0.45)): only the record popup, over a dark overlay.
- **Search field** (0 1px 2px rgba(0,0,0,0.18)): a hairline lift so the white field sits on the photograph in the band.

### Named Rules
**The Flat Page Rule.** Cards, rows and panels have no shadow and never lift on hover. Hover changes colour or border, never position.

## Shapes

Square. Cards and photographs have no radius. Inputs and buttons have a barely-there 2px radius so they read as controls. No pills, no rounded cards.

## Components

### Buttons
- **Primary** (partisan-red, white text, 2px radius, 36px tall): "Otvori PDF", "Pošalji prijavu". Hover darkens to partisan-red-deep.
- **Secondary** (transparent, ink text, 1px rule-strong border): "Preuzmi", "Otkaži". Hover darkens the border to ink.
- Icons are line icons from the site's own set (1.75 stroke, 24px grid), never unicode glyphs or emoji.

### Cards / Containers
- **Unit card:** the photograph is the card: a 4:3 black-and-white photo (slightly enlarged so scan edges stay out of frame, a gentle 1.04→1.06 zoom on hover), then name, description and the soldier count in red ink on the surface colour. No border, no shadow, no radius. A book-page image that stands in for a missing photograph is shown whole (contained), not cropped, and not greyscaled.

- **Na današnji dan:** the name, then a small line candle (14px, muted ink) before the year and place of death, and the age in bold: "23 godine", or "22/23 godine" when only the birth year is known. No crosses or other religious marks.

### Inputs / Fields
- **Search field:** white surface, 44px tall, 2px radius, search icon inside on the left, placeholder "Prezime, ime ili mesto". Inside the red band it has no border; on the unit page it has a 1px rule-strong border. Focus: 2px ink border.
- **Filters:** "Filteri" at the end of the search field (with a small red count when any are set) opens a row of small labelled fields under it: birth year with ±, place, unit (home only), fate, and "Samo cele reči". Fields are 2.25rem tall, 2px radius; in the band, white with no border.

### Navigation
- Site name in PT Serif bold, links "Početna" and "Izvori" in white on the band with a 2px white underline for the current page, and a three-way light/dark/system toggle (segmented, white on red).

### Record popup
- A strip of the unit's photograph (about 6.5rem tall, black and white) with a 3px red rule under it, then the person. The scan viewer opens at the zoom where the whole highlighted entry fits the width (140% minimum on phones), scrolled to the entry, with page and zoom controls.
- At its foot, a bar held at the window's edge names the previous and next entries of the unit's list ("Prethodni" / "Sledeći", the name in PT Serif); the arrow keys do the same.

## Do's and Don'ts

### Do:
- **Do** show real brigade photographs large and in black and white.
- **Do** write names surname first, surname bold, in PT Serif.
- **Do** keep every record one click from its scanned line in the book.
- **Do** use Serbo-Croatian typography: „…“ quotes, dates like 29. 12. 1924, dot thousands (9.814).
- **Do** keep both themes working; the dark theme is a warm charcoal (not near-black) with a deepened red.

### Don't:
- **Don't** add statistics blocks, totals tiles or charts.
- **Don't** order units any other way than by formation date, oldest first.
- **Don't** add stars, glow, fake paper or scanline textures, or other wartime costume.
- **Don't** add eyebrow labels above headings, coloured side borders on cards, gradient text, or hover lift.
- **Don't** set text larger than 1.875rem (except the home page year markers) or make headings bold.
