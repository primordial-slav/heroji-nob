'use client'

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { DEFAULT_LANG, localePath, type Lang } from './config'
import { sr, type Messages } from './messages/sr'
import { unitDescriptionIn, unitNameIn, unitShortNameIn, type UnitTexts } from './unitNames'
import type { Unit } from '@/app/data/units'

// The page's language and its text, set by its root layout from the address (/ for Serbo-Croatian, /sl, /mk, /en).
// Each root layout renders its own provider, which loads only the text its pages may need: SerboCroatian below for
// the plain addresses, AnyLanguage (i18n/AnyLanguage.tsx) for the others and the 404 page.
export interface LangPack {
  lang: Lang
  t: Messages
  /** The units' names and cards in the language (i18n/units.ts); none in Serbo-Croatian, whose are data/units.ts */
  units?: UnitTexts
}

const SERBO_CROATIAN: LangPack = { lang: DEFAULT_LANG, t: sr }

const LangContext = createContext<LangPack>(SERBO_CROATIAN)

export function LangPackProvider({ pack, children }: { pack: LangPack; children: ReactNode }) {
  return <LangContext.Provider value={pack}>{children}</LangContext.Provider>
}

export function SerboCroatian({ children }: { lang: Lang; children: ReactNode }) {
  return <LangPackProvider pack={SERBO_CROATIAN}>{children}</LangPackProvider>
}

export function useLang(): Lang {
  return useContext(LangContext).lang
}

/** The page language's text */
export function useT(): Messages {
  return useContext(LangContext).t
}

/** A path in the page's language: '/izvori' -> '/en/izvori' */
export function useLocalePath(): (path: string) => string {
  const lang = useLang()
  return (path: string) => localePath(lang, path)
}

/** A unit's name and card in the page's language (i18n/unitNames.ts) */
export function useUnitText() {
  const { lang, units } = useContext(LangContext)
  return useMemo(() => ({
    /** With its quotation marks: Prva liška proletarska brigada »Marko Orešković« */
    name: (unit: Unit) => unitNameIn(unit, lang, units),
    /** Without its honorary name: "Prva liška proletarska brigada" */
    shortName: (unit: Unit) => unitShortNameIn(unit, lang, units),
    description: (unit: Unit) => unitDescriptionIn(unit, lang, units),
  }), [lang, units])
}

export type UnitNames = ReturnType<typeof useUnitText>
