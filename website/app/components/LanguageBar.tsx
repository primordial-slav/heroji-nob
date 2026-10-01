'use client'

import { usePathname } from 'next/navigation'
import { FINISHED_LANGS, HTML_LANG, LANG_NAMES, localePath, splitPath } from '@/app/i18n/config'
import { useLang, useT } from '@/app/i18n/LangContext'

// A thin bar above the header: the same page in each finished language, named in that language (Srpskohrvatski,
// Slovenščina, Македонски, English). The search, the filters and an open record (?q=…&borac=…) come along, so a
// record read in one language opens in the other. A page in a language not yet finished lists itself as well.
export default function LanguageBar() {
  const lang = useLang()
  const t = useT()
  const { path } = splitPath(usePathname())
  const shown = FINISHED_LANGS.includes(lang) ? FINISHED_LANGS : [...FINISHED_LANGS, lang]
  if (shown.length < 2) return null

  return (
    <nav className="lang-bar" aria-label={t.language.label}>
      <ul className="container">
        {shown.map((l) => {
          const href = localePath(l, path)
          return (
            <li key={l}>
              <a
                href={href}
                hrefLang={HTML_LANG[l]}
                lang={HTML_LANG[l]}
                aria-label={LANG_NAMES[l].name}
                aria-current={l === lang ? 'true' : undefined}
                onClick={(e) => {
                  if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return
                  e.preventDefault()
                  if (l === lang) return
                  window.location.assign(href + window.location.search + window.location.hash)
                }}
              >
                <span className="lang-name">{LANG_NAMES[l].name}</span>
                <span className="lang-code" aria-hidden="true">{LANG_NAMES[l].code}</span>
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
