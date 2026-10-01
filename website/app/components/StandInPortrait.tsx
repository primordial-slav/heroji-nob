import type { Silhouette } from '@/app/lib/standIn'

// A soldier we have no photograph of: the grey outline of a partisan in a cap, and the cap's red star the only
// colour (the outlines: data/silhouettes.ts; the colours come from the page, .standin in globals.css)

function star(cx: number, cy: number, r: number): string {
  return Array.from({ length: 10 }, (_, i) => {
    const a = -Math.PI / 2 + (i * Math.PI) / 5
    const rr = i % 2 === 0 ? r : r * 0.4
    return `${(cx + rr * Math.cos(a)).toFixed(1)},${(cy + rr * Math.sin(a)).toFixed(1)}`
  }).join(' ')
}

export default function StandInPortrait({ silhouette }: { silhouette: Silhouette }) {
  const [x, y] = silhouette.star
  return (
    <svg className="standin" viewBox="0 0 300 400" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
      <rect className="standin-paper" width="300" height="400" />
      <path className="standin-figure" d={silhouette.d} />
      <polygon className="standin-star" points={star((x / 100) * 300, (y / 100) * 400, 10)} />
    </svg>
  )
}
