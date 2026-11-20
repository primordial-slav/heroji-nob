// Phone photos are often 4-8 MB; the form service takes 10 MB per message. A photo is sent as a JPEG of at
// most MAX_SIDE pixels on its longer side, which keeps old family photos sharp enough to publish.
import { ROUTE_MAX_BYTES } from './attachments'

const MAX_SIDE = 2400
const QUALITY = 0.88

export async function shrinkPhoto(file: File): Promise<Blob> {
  let bitmap: ImageBitmap
  try {
    bitmap = await createImageBitmap(file)
  } catch {
    // A format the browser can't draw (e.g. HEIC on some phones): send it as it is
    return file
  }
  if (file.type === 'image/jpeg' && file.size < 3_000_000 && Math.max(bitmap.width, bitmap.height) <= MAX_SIDE) {
    bitmap.close()
    return file
  }
  // the site's /api/prilog takes a file of up to 4.3 MB (lib/attachments.ts): a photo that is still larger is drawn
  // again, smaller, which a rare very detailed 2400-pixel photo needs
  let blob: Blob = file
  for (const [side, quality] of [[MAX_SIDE, QUALITY], [1800, 0.82], [1400, 0.78]] as const) {
    blob = await draw(bitmap, side, quality) ?? file
    if (blob.size <= ROUTE_MAX_BYTES) break
  }
  bitmap.close()
  return blob
}

function draw(bitmap: ImageBitmap, side: number, quality: number): Promise<Blob | null> {
  const scale = Math.min(1, side / Math.max(bitmap.width, bitmap.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(bitmap.width * scale)
  canvas.height = Math.round(bitmap.height * scale)
  canvas.getContext('2d')!.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  return new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality))
}
