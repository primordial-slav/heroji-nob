import { messagesFor } from '../i18n'
import { localePath, type Lang } from '../i18n/config'
import { MISSING_FORM_HASH } from '../lib/missingForm'
import ThemeToggle from './ThemeToggle'

// The site's address for mail: the one the forms send to (website/.env)
const EMAIL = process.env.NEXT_PUBLIC_REPORT_EMAIL

// The site's page for donations (the user's, set up 2026-11-20): a plain link, never Ko-fi's widget, which would load
// their script on every page
const KOFI = 'https://ko-fi.com/knjigaboraca'

// The foot of every page: the site's name, where to give and where to write. The sources are named on Izvori alone. On
// a phone the theme switch is here, not at the top of the screen (globals.css).
export default function SiteFooter({ lang }: { lang: Lang }) {
  const t = messagesFor(lang)
  const f = t.footer
  return (
    <footer className="site-footer">
      <div className="container site-footer-inner">
        <div>
          <p className="site-footer-name">{t.site.name}</p>
          <div className="site-footer-theme"><ThemeToggle /></div>
          <div className="site-footer-support">
            <p className="site-footer-label">{f.support}</p>
            <p>{f.supportText} <a href={KOFI}>{f.supportLink}</a>.</p>
          </div>
        </div>
        {EMAIL && (
          <div className="site-footer-contact">
            <p className="site-footer-label">{f.contact}</p>
            <p><a href={`mailto:${EMAIL}`}>{EMAIL}</a></p>
            <p>{f.records}</p>
            {/* opens the form for a fighter not on the site under the home page's band (HomePage); a plain link, so it
                works from every page and in every language */}
            <p>{f.missingAsk} <a href={`${localePath(lang, '/')}#${MISSING_FORM_HASH}`}>{f.missingLink}</a>.</p>
          </div>
        )}
      </div>
    </footer>
  )
}
