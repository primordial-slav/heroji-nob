'use client'

import type { ReactNode } from 'react'
import type { Lang } from './config'
import { MESSAGES } from './index'
import { UNIT_TEXTS } from './units'
import { LangPackProvider, type LangPack } from './LangContext'

// The provider of the pages under /sr-cyrl, /sl, /mk, /en and of the 404 page, which learns its language in the
// browser: they load the text of every language (the plain addresses load Serbo-Croatian alone, LangContext.tsx)
const PACKS = Object.fromEntries(
  (Object.keys(MESSAGES) as Lang[]).map((lang) => [lang, { lang, t: MESSAGES[lang], units: UNIT_TEXTS[lang] }]),
) as Record<Lang, LangPack>

export default function AnyLanguage({ lang, children }: { lang: Lang; children: ReactNode }) {
  return <LangPackProvider pack={PACKS[lang]}>{children}</LangPackProvider>
}
