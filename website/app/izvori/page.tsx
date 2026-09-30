import { sources } from '@/app/data/sources'
import { DocumentIcon, DownloadIcon } from '@/app/components/Icons'

export const metadata = {
  title: 'Izvori — Knjiga boraca',
  description: 'Izvorni dokumenti korišćeni za bazu podataka boraca NOB-a.',
}

export default function IzvoriPage() {
  return (
    <div className="container page-content">
      <h1 className="page-title">Izvorni dokumenti</h1>

      <p className="sources-intro">
        Podaci o borcima prikupljeni su iz monografija brigada i spiskova boraca
        objavljenih u izdanjima Vojnoistorijskog instituta. Ovde možete pregledati
        i preuzeti originalne PDF dokumente.
      </p>

      <ul className="sources-list">
        {sources.map((source) => (
          <li className="source-row" id={source.id} key={source.id}>
            <img src={source.thumbnail} alt="" className="source-thumb" loading="lazy" />
            <div>
              <h2 className="source-title">{source.title}</h2>
              <p className="source-author">{source.author}</p>
              {source.description && <p className="source-desc">{source.description}</p>}
              <div className="source-actions">
                {source.pdfPath.endsWith('.pdf') ? (
                  <>
                    <a href={source.pdfPath} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                      <DocumentIcon size={16} /> Otvori PDF
                    </a>
                    <a href={source.pdfPath} download className="btn btn-secondary">
                      <DownloadIcon size={16} /> Preuzmi
                    </a>
                  </>
                ) : (
                  // a list published only as a web page (no scan)
                  <a href={source.pdfPath} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                    <DocumentIcon size={16} /> Otvori spisak
                  </a>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
