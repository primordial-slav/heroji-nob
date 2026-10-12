import type { Metadata } from 'next'
import { SiteDocument } from './components/SiteShell'
import NotFoundPage from './components/NotFoundPage'
import { siteMetadata } from './i18n/metadata'
import { messagesFor } from './i18n'

// The site has two root layouts ((sr) and (intl)/[lang]), so an address neither knows comes here
// (experimental.globalNotFound in next.config.js)
export const metadata: Metadata = { ...siteMetadata('sr'), title: `${messagesFor('sr').notFound.title} · ${messagesFor('sr').site.name}` }

export default function GlobalNotFound() {
  return (
    <SiteDocument lang="sr">
      <NotFoundPage />
    </SiteDocument>
  )
}
