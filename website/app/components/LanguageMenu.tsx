'use client'

import { useEffect, useId, useRef, useState } from 'react'
import { usePathname } from 'next/navigation'
import { FINISHED_LANGS, HTML_LANG, LANG_NAMES, localePath, splitPath, type Lang } from '@/app/i18n/config'
import { useLang, useT } from '@/app/i18n/LangContext'
import { ChevronDownIcon, GlobeIcon } from './Icons'

// The language choice in the header, beside the light/dark switch: a globe with the page language's code
// (SH, СХ, SL, MK, EN) opens the same page in each finished language, named in that language. The search,
// the filters and an open record (?q=…&borac=…) come along, so a record read in one language opens in the
// other. A page in a language not yet finished lists itself as well. The links stay in the page while the
// list is closed, so search engines find each language's version of the page.
export default function LanguageMenu() {
  const lang = useLang()
  const t = useT()
  const { path } = splitPath(usePathname())
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const listId = useId()

  const shown: readonly Lang[] = FINISHED_LANGS.includes(lang) ? FINISHED_LANGS : [...FINISHED_LANGS, lang]

  // Closes on Escape (back to the button), on a click beside it, and when focus moves elsewhere
  useEffect(() => {
    if (!open) return
    const onPointer = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      setOpen(false)
      buttonRef.current?.focus()
    }
    const onFocus = (e: FocusEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    document.addEventListener('focusin', onFocus)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('focusin', onFocus)
    }
  }, [open])

  if (shown.length < 2) return null

  return (
    <nav className="lang-menu" ref={rootRef} aria-label={t.language.label}>
      <button
        ref={buttonRef}
        type="button"
        className="lang-menu-button"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={`${t.language.label}: ${LANG_NAMES[lang].name}`}
        onClick={() => setOpen((o) => !o)}
      >
        <GlobeIcon size={15} />
        <span aria-hidden="true">{LANG_NAMES[lang].code}</span>
        <ChevronDownIcon size={13} />
      </button>
      <ul id={listId} className="lang-menu-list" hidden={!open}>
        {shown.map((l) => {
          const href = localePath(l, path)
          return (
            <li key={l}>
              <a
                href={href}
                hrefLang={HTML_LANG[l]}
                lang={HTML_LANG[l]}
                aria-current={l === lang ? 'true' : undefined}
                onClick={(e) => {
                  if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return
                  e.preventDefault()
                  setOpen(false)
                  if (l === lang) return
                  window.location.assign(href + window.location.search + window.location.hash)
                }}
              >
                {LANG_NAMES[l].name}
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
