import { sources } from '@/app/data/sources'

export const metadata = {
  title: 'Izvori — Knjiga Boraca',
  description: 'Izvorni dokumenti korišćeni za bazu podataka boraca NOB-a.',
}

export default function IzvoriPage() {
  return (
    <div className="page-content">
      <h1 className="page-title">Izvorni dokumenti</h1>

      <p className="sources-intro">
        Podaci o borcima prikupljeni su iz monografija brigada i spiskova boraca
        objavljenih u izdanjima Vojnoistorijskog instituta. Ovde možete pregledati
        i preuzeti originalne PDF dokumente.
      </p>

      <div className="sources-grid">
        {sources.map((source) => (
          <div className="source-card" id={source.id} key={source.id}>
            <div className="source-card-thumb">
              <img
                src={source.thumbnail}
                alt={source.title}
                loading="lazy"
              />
            </div>
            <div className="source-card-body">
              <h3 className="source-card-title">{source.title}</h3>
              <p className="source-card-author">{source.author}</p>
              {source.description && (
                <p className="source-card-desc">{source.description}</p>
              )}
              <div className="source-card-actions">
                <a
                  href={source.pdfPath}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-btn source-btn-primary"
                >
                  Otvori PDF
                </a>
                <a
                  href={source.pdfPath}
                  download
                  className="source-btn source-btn-secondary"
                >
                  &#8681; Preuzmi
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
