'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowLeftIcon } from './Icons'
import SiteFrame from './SiteFrame'
import { DEFAULT_LANG, HTML_LANG, localePath, splitPath, type Lang } from '@/app/i18n/config'
import { messagesFor } from '@/app/i18n'

// An address the site doesn't have. The page is built once for every language, so it reads the language from the
// address in the browser: /en/xyz answers in English, /units/xyz in Serbo-Croatian.
export default function NotFoundPage() {
  const [lang, setLang] = useState<Lang>(DEFAULT_LANG)
  useEffect(() => {
    const found = splitPath(window.location.pathname).lang
    const t = messagesFor(found)
    document.documentElement.lang = HTML_LANG[found]
    document.title = `${t.notFound.title} · ${t.site.name}`
    setLang(found)
  }, [])
  const t = messagesFor(lang)
  return (
    <SiteFrame lang={lang}>
      <div className="container page-content">
        <h1 className="page-title">{t.notFound.title}</h1>
        <p>{t.notFound.text}</p>
        <Link href={localePath(lang, '/')} className="back-link"><ArrowLeftIcon size={16} /> {t.unit.backHome}</Link>
      </div>
    </SiteFrame>
  )
}
