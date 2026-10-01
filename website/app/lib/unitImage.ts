import imageSizes from '@/app/data/unitImageSizes.json'

// Each unit photo's width and height, and the widths of the narrower copies scripts/make_unit_image_sizes.py
// writes of it (/images/w<width>/<file>, only the widths below the original's)
const SIZES = imageSizes.photos as Record<string, number[]>
const COPY_WIDTHS = imageSizes.widths

export interface UnitImageProps {
  src: string
  srcSet?: string
  sizes?: string
  width?: number
  height?: number
}

// The img attributes for a unit photo: the browser picks the smallest copy that fills `sizes`
// (how wide the photo is drawn). src stays the original, which CSS tells apart by its path
// (img[src*="pdf-thumbs"]); a photo the script hasn't measured gets only its src.
export function unitImageProps(src: string, sizes: string): UnitImageProps {
  const size = SIZES[src]
  if (!size || !src.startsWith('/images/')) return { src }
  const [width, height] = size
  const name = src.slice('/images/'.length)
  const copies = COPY_WIDTHS.filter((w) => w < width).map((w) => `/images/w${w}/${name} ${w}w`)
  return { src, srcSet: [...copies, `${src} ${width}w`].join(', '), sizes, width, height }
}
