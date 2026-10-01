import { sources } from '@/app/data/sources'
import { DocumentIcon, DownloadIcon } from '@/app/components/Icons'
import RichText from '@/app/i18n/RichText'
import { messagesFor } from '@/app/i18n'
import { pageMetadata } from '@/app/i18n/metadata'
import { sourceAuthor, sourceDescription } from '@/app/i18n/sources'
import type { Lang } from '@/app/i18n/config'

export function sourcesMetadata(lang: Lang) {
  const t = messagesFor(lang).sources
  return pageMetadata(lang, '/izvori', { title: t.metaTitle, description: t.metaDescription })
}

// The Izvori page: every book, with its scan to open or download. Titles stay as the books print them.
export default function SourcesPage({ lang }: { lang: Lang }) {
  const t = messagesFor(lang).sources
  const external = (href: string, label: string) => (
    <a href={href} target="_blank" rel="noopener noreferrer">{label}</a>
  )

  return (
    <div className="container page-content">
      <h1 className="page-title">{t.title}</h1>

      <p className="sources-intro">{t.intro}</p>

      <ul className="sources-list">
        {sources.map((source) => {
          const description = sourceDescription(source, lang)
          return (
            <li className="source-row" id={source.id} key={source.id}>
              <img src={source.thumbnail} alt="" className="source-thumb" loading="lazy" />
              <div>
                <h2 className="source-title">{source.title}</h2>
                <p className="source-author">{sourceAuthor(source, lang)}</p>
                {description && <p className="source-desc">{description}</p>}
                <div className="source-actions">
                  {source.pdfPath.endsWith('.pdf') ? (
                    <>
                      <a href={source.pdfPath} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                        <DocumentIcon size={16} /> {t.openPdf}
                      </a>
                      <a href={source.pdfPath} download className="btn btn-secondary">
                        <DownloadIcon size={16} /> {t.download}
                      </a>
                    </>
                  ) : (
                    // a list published only as a web page (no scan)
                    <a href={source.pdfPath} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                      <DocumentIcon size={16} /> {t.openList}
                    </a>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ul>

      <section className="sources-credits" id="odlikovanja">
        <h2>{t.medalsTitle}</h2>
        <p>
          <RichText
            text={t.hero}
            render={(part, i) => external(
              i === 0 ? 'https://commons.wikimedia.org/wiki/File:Orden_narodnog_heroja_1.png' : t.heroLicense,
              part,
            )}
          />
        </p>
        <p>
          <RichText
            text={t.spomenica}
            render={(part) => external('https://commons.wikimedia.org/wiki/File:R45-yo0357-Partizanska-spomenica-1941.png', part)}
          />
        </p>
      </section>
    </div>
  )
}
