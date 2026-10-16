'use client'

import { NEWS, newsText } from '@/app/data/news'
import { useLang, useT } from '@/app/i18n/LangContext'

// "Šta je novo" on the home page, after the doors: the last three big changes, each with a title and a sentence or
// two, then a few small ones a line each. "Prikaži starije" does nothing yet: older news has no page of its own.

const BIG = NEWS.filter((item) => item.title).slice(0, 3)
const SMALL = NEWS.filter((item) => !item.title).slice(0, 4)

export default function HomeNews() {
  const t = useT().home.news
  const lang = useLang()
  const when = (iso: string) => {
    const [y, m, d] = iso.split('-').map(Number)
    return t.date(d, m, y)
  }

  return (
    <section className="news" aria-labelledby="news-title">
      <h2 className="unit-year-head is-undated" id="news-title">{t.title}</h2>
      <ul className="news-big">
        {BIG.map((item) => (
          <li key={`${item.date} ${item.title!.sr}`}>
            <time className="news-date" dateTime={item.date}>{when(item.date)}</time>
            <h3 className="news-title">{newsText(item.title!, lang)}</h3>
            <p className="news-text">{newsText(item.text, lang)}</p>
          </li>
        ))}
      </ul>
      <ul className="news-small">
        {SMALL.map((item) => (
          <li key={`${item.date} ${item.text.sr.slice(0, 24)}`}>
            <time className="news-date" dateTime={item.date}>{when(item.date)}</time>
            <span>{newsText(item.text, lang)}</span>
          </li>
        ))}
      </ul>
      <button type="button" className="btn btn-secondary news-more">{t.more}</button>
    </section>
  )
}
