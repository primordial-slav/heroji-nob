import { Fragment, type ReactNode } from 'react'

// A message with [bracketed] parts that become links or buttons: "Proverite filtere ili ih [uklonite]."
// Each bracketed part is passed, in order, to the render function with its index.
export default function RichText({ text, render }: { text: string; render: (part: string, index: number) => ReactNode }) {
  const pieces = text.split(/\[([^\]]+)\]/)
  return (
    <>
      {pieces.map((piece, i) => (i % 2 === 1 ? <Fragment key={i}>{render(piece, (i - 1) / 2)}</Fragment> : piece))}
    </>
  )
}
