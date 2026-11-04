import { BAND_POSTERS, type BandPoster } from '@/app/data/bandPosters'
import s from './BandPosters.module.css'

function Margin({ side, posters }: { side: 'left' | 'right'; posters: BandPoster[] }) {
  const fromColumn = side === 'left' ? 'right' : 'left'
  return (
    <div className={`${s.margin} ${s[side]}`} aria-hidden="true">
      {posters.map((p) => (
        <img
          key={p.id}
          className={s.poster}
          src={`/plakati-band/${p.id}.webp`}
          alt=""
          width={p.w}
          height={p.h}
          loading="lazy"
          decoding="async"
          style={{ [fromColumn]: p.o, top: p.y, width: p.w, height: p.h, rotate: `${p.turn}deg` }}
        />
      ))}
    </div>
  )
}

// The Partisans' wartime posters, faint, pasted in the band's margins as on a wall
export default function BandPosters() {
  return (
    <>
      <Margin side="left" posters={BAND_POSTERS.left} />
      <Margin side="right" posters={BAND_POSTERS.right} />
    </>
  )
}
