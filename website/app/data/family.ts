// Photos and stories that families sent through "Znam ovog borca" and that were checked and approved
// for publishing (the sender gave permission). How to add one: docs/FAMILY_CONTRIBUTIONS.md

export interface FamilyContribution {
  soldierId: string     // the record it belongs to
  photo?: string        // file in website/public/porodica/, e.g. '0002000003-1.jpg'
  photoCaption?: string // what the photo shows and when, in the sender's words
  text?: string         // the story, as sent (lightly edited for spelling only)
  from: string          // credit line, e.g. 'Ana Petrović, unuka'
  date: string          // when it was sent, 'YYYY-MM'
}

export const familyContributions: FamilyContribution[] = []

export function contributionsFor(soldierId: string, otherIds: (string | undefined)[] = []): FamilyContribution[] {
  const ids = new Set([soldierId, ...otherIds.filter(Boolean)])
  return familyContributions.filter((c) => ids.has(c.soldierId))
}
