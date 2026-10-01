// Phone photos are often 4-8 MB; the form service takes 10 MB per message. A photo is sent as a JPEG of at
// most MAX_SIDE pixels on its longer side, which keeps old family photos sharp enough to publish.
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
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
  if (scale === 1 && file.type === 'image/jpeg' && file.size < 3_000_000) return file
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(bitmap.width * scale)
  canvas.height = Math.round(bitmap.height * scale)
  canvas.getContext('2d')!.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  bitmap.close()
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob ?? file), 'image/jpeg', QUALITY)
  })
}
