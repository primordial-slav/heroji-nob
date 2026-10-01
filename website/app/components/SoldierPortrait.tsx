import type { Soldier } from '@/app/lib/types'
import type { ShownPortrait } from '@/app/data/portraits'
import { standInFor } from '@/app/lib/standIn'
import StandInPortrait from './StandInPortrait'

// The soldier's portrait as a small 3:4 print: his or her photograph where we have one (it opens full size),
// otherwise an anonymous outline of a partisan in a cap
export default function SoldierPortrait({ soldier, unitId, portrait, className }: {
  soldier: Soldier
  unitId?: string
  portrait: ShownPortrait | null
  className: string
}) {
  if (portrait) {
    return (
      <figure className={className}>
        <a href={portrait.src} target="_blank" rel="noopener noreferrer" aria-label="Fotografija u punoj veličini">
          <img src={portrait.src} alt="" style={{ objectPosition: `50% ${portrait.focus}%` }} />
        </a>
      </figure>
    )
  }
  return (
    <figure className={`${className} is-standin`} title="Fotografija ovog borca nije poznata">
      <StandInPortrait silhouette={standInFor(soldier, unitId)} />
    </figure>
  )
}
