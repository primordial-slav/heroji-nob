import { messagesFor } from '../i18n'
import type { Lang } from '../i18n/config'

// The site's address for mail: the one the forms send to (website/.env)
const EMAIL = process.env.NEXT_PUBLIC_REPORT_EMAIL

// The foot of every page: the site's name and where to write. The sources are named on Izvori alone.
export default function SiteFooter({ lang }: { lang: Lang }) {
  const t = messagesFor(lang)
  const f = t.footer
  return (
    <footer className="site-footer">
      <div className="container site-footer-inner">
        <p className="site-footer-name">{t.site.name}</p>
        {EMAIL && (
          <div className="site-footer-contact">
            <p className="site-footer-label">{f.contact}</p>
            <p><a href={`mailto:${EMAIL}`}>{EMAIL}</a></p>
            <p>{f.records}</p>
          </div>
        )}
      </div>
    </footer>
  )
}
