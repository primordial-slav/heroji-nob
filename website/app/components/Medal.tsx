import type { Soldier } from '@/app/lib/types'
import { decorationsOf } from '@/app/lib/records'

// The decorations the books name, shown as the real ones: Orden narodnog heroja and Partizanska spomenica 1941.
// Both looks are made from photographs by scripts/make_medal_images.py:
// 'foto' is the photograph itself (the soldier popup, the Spomen-kartica),
// 'gravira' an engraving traced from it, drawn in the text colour through a CSS mask (search results).
export type MedalKind = 'heroj' | 'spomenica'
export type MedalLook = 'foto' | 'gravira'

export const MEDAL_LABEL: Record<MedalKind, string> = {
  heroj: 'Narodni heroj',
  spomenica: 'Nosilac Partizanske spomenice 1941',
}

// Image sizes, as the script prints them
const SIZE: Record<MedalLook, Record<MedalKind, [number, number]>> = {
  foto: { heroj: [184, 300], spomenica: [186, 180] },
  gravira: { heroj: [746, 1293], spomenica: [1194, 1150] },
}

export function Medal({ kind, look }: { kind: MedalKind; look: MedalLook }) {
  const [width, height] = SIZE[look][kind]
  const label = MEDAL_LABEL[kind]
  return (
    <span className={`medal medal-${kind}`} role="img" aria-label={label} title={label}>
      {look === 'foto' ? (
        <img src={`/medalje/${kind}-foto.webp`} alt="" width={width} height={height} />
      ) : (
        <span
          className="medal-gravira"
          style={{ aspectRatio: `${width} / ${height}`, ['--src' as string]: `url(/medalje/${kind}-gravira.svg)` }}
        />
      )}
    </span>
  )
}

/** The soldier's decorations, the order last (it stands at the edge) */
export function SoldierMedals({ soldier, look, className }: { soldier: Soldier; look: MedalLook; className?: string }) {
  const { heroj, spomenica } = decorationsOf(soldier)
  if (!heroj && !spomenica) return null
  return (
    <span className={className ? `medals ${className}` : 'medals'}>
      {spomenica && <Medal kind="spomenica" look={look} />}
      {heroj && <Medal kind="heroj" look={look} />}
    </span>
  )
}

/** "Narodni heroj · Nosilac Partizanske spomenice 1941", or null */
export function honoursLine(soldier: Soldier): string | null {
  const { heroj, spomenica } = decorationsOf(soldier)
  const parts = [heroj && MEDAL_LABEL.heroj, spomenica && MEDAL_LABEL.spomenica].filter(Boolean)
  return parts.length ? parts.join(' · ') : null
}
