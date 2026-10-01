// Box around a soldier's entry on its PDF page, in PDF points. The extent comes from
// data-extraction/entry_boxes.py; records without one get a one-line box.
export function highlightBox(x: number, y: number, xLeft?: number, xEnd?: number, yEnd?: number) {
  const left = xLeft ?? x
  const right = xEnd != null && xEnd > left ? xEnd : left + (x > 150 ? 200 : 250)
  const bottom = yEnd != null && yEnd > y ? yEnd : y + 11
  const padX = 3, padY = 2
  return { left: left - padX, top: y - padY, width: right - left + 2 * padX, height: bottom - y + 2 * padY }
}
