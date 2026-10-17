import localFont from 'next/font/local'

// ISO 3098 lettering, the drafting pen's hand the war books letter their sketches in (osifont, GPL with the font
// exception), cut to Latin and Cyrillic. The page sets its variable once, for the map and its legends
export const lettering = localFont({ src: './fonts/osifont-italic.woff2', variable: '--font-lettering', display: 'block' })
