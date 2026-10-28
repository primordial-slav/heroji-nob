import type { Lang } from './config'
import type { Unit } from '@/app/data/units'
import { quoteMarks } from './format'
import { toCyrillic } from './cyrillic'

// A unit's name and card in a language, given that language's texts (i18n/units.ts); without them the
// Serbo-Croatian text of data/units.ts. Apart from the texts, so that a page in Serbo-Croatian doesn't load them.

export interface UnitText {
  name: string
  description: string
}

export type UnitTexts = Record<string, UnitText>

// Serbo-Croatian in Cyrillic is the Latin text of data/units.ts, letter for letter
function inScript(lang: Lang, text: string): string {
  return lang === 'sr-cyrl' ? toCyrillic(text) : text
}

export function unitNameIn(unit: Unit, lang: Lang, texts?: UnitTexts): string {
  return inScript(lang, quoteMarks(lang, texts?.[unit.id]?.name ?? unit.name))
}

export function unitShortNameIn(unit: Unit, lang: Lang, texts?: UnitTexts): string {
  return inScript(lang, (texts?.[unit.id]?.name ?? unit.name).split(/\s+["„]/)[0])
}

export function unitDescriptionIn(unit: Unit, lang: Lang, texts?: UnitTexts): string {
  return inScript(lang, texts?.[unit.id]?.description ?? unit.description)
}
