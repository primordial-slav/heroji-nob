// Box around a soldier's entry on its PDF page, in PDF points. The extent comes from
// data-extraction/entry_boxes.py; records without one get a one-line box.
export function highlightBox(x: number, y: number, xLeft?: number, xEnd?: number, yEnd?: number) {
  const left = xLeft ?? x
  const right = xEnd != null && xEnd > left ? xEnd : left + (x > 150 ? 200 : 250)
  const bottom = yEnd != null && yEnd > y ? yEnd : y + 11
  const padX = 3, padY = 2
  return { left: left - padX, top: y - padY, width: right - left + 2 * padX, height: bottom - y + 2 * padY }
}

// The boxes to draw: the entry's box, or, for a name its parser boxed word by word (a list that runs the names on,
// comma after comma), one box for each line the name takes: rects as [left, top, right, bottom] in PDF points
export function highlightBoxes(x: number, y: number, xLeft?: number, xEnd?: number, yEnd?: number, rects?: number[][]) {
  if (!rects?.length) return [highlightBox(x, y, xLeft, xEnd, yEnd)]
  return rects.map(([left, top, right, bottom]) => highlightBox(left, top, undefined, right, bottom))
}
