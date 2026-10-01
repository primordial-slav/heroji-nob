'use client'

import { createContext, useContext, type ReactNode } from 'react'
import { DEFAULT_LANG, localePath, type Lang } from './config'
import { MESSAGES, type Messages } from './index'

// The page's language, set by its root layout from the address (/ for Serbo-Croatian, /sl, /mk, /en)
const LangContext = createContext<Lang>(DEFAULT_LANG)

export function LangProvider({ lang, children }: { lang: Lang; children: ReactNode }) {
  return <LangContext.Provider value={lang}>{children}</LangContext.Provider>
}

export function useLang(): Lang {
  return useContext(LangContext)
}

/** The page language's text */
export function useT(): Messages {
  return MESSAGES[useLang()]
}

/** A path in the page's language: '/izvori' -> '/en/izvori' */
export function useLocalePath(): (path: string) => string {
  const lang = useLang()
  return (path: string) => localePath(lang, path)
}
