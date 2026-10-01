// Line icons drawn on a 24px grid, 1.75 stroke, so every control shares one style.
type IconProps = { size?: number }

function Svg({ size = 18, children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  )
}

export const SearchIcon = (p: IconProps) => (
  <Svg {...p}><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></Svg>
)
export const ArrowLeftIcon = (p: IconProps) => (
  <Svg {...p}><path d="M19 12H5" /><path d="m11 6-6 6 6 6" /></Svg>
)
export const ArrowRightIcon = (p: IconProps) => (
  <Svg {...p}><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></Svg>
)
export const ChevronLeftIcon = (p: IconProps) => (
  <Svg {...p}><path d="m15 6-6 6 6 6" /></Svg>
)
export const ChevronRightIcon = (p: IconProps) => (
  <Svg {...p}><path d="m9 6 6 6-6 6" /></Svg>
)
export const CloseIcon = (p: IconProps) => (
  <Svg {...p}><path d="M6 6l12 12" /><path d="M18 6 6 18" /></Svg>
)
export const PlusIcon = (p: IconProps) => (
  <Svg {...p}><path d="M12 5v14" /><path d="M5 12h14" /></Svg>
)
export const MinusIcon = (p: IconProps) => (
  <Svg {...p}><path d="M5 12h14" /></Svg>
)
export const TargetIcon = (p: IconProps) => (
  <Svg {...p}><circle cx="12" cy="12" r="7" /><circle cx="12" cy="12" r="2" /></Svg>
)
export const DownloadIcon = (p: IconProps) => (
  <Svg {...p}><path d="M12 4v11" /><path d="m7 10 5 5 5-5" /><path d="M5 20h14" /></Svg>
)
export const DocumentIcon = (p: IconProps) => (
  <Svg {...p}><path d="M7 3h7l4 4v14H7z" /><path d="M14 3v4h4" /><path d="M10 12h5M10 16h5" /></Svg>
)
export const ShareIcon = (p: IconProps) => (
  <Svg {...p}><circle cx="18" cy="5" r="2.5" /><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="19" r="2.5" /><path d="m8.2 10.8 7.6-4.4" /><path d="m8.2 13.2 7.6 4.4" /></Svg>
)
export const PrintIcon = (p: IconProps) => (
  <Svg {...p}><path d="M7 9V3h10v6" /><path d="M7 17H4v-7h16v7h-3" /><path d="M7 14h10v7H7z" /></Svg>
)
export const QuoteIcon = (p: IconProps) => (
  <Svg {...p}><path d="M5 18c2.5-1.5 3.5-3.5 3.5-6.5H5V6h6v5.5C11 15 9.5 17.5 6.5 19" /><path d="M14 18c2.5-1.5 3.5-3.5 3.5-6.5H14V6h6v5.5c0 3.5-1.5 6-4.5 7.5" /></Svg>
)
export const CopyIcon = (p: IconProps) => (
  <Svg {...p}><rect x="8" y="8" width="12" height="12" rx="1" /><path d="M16 8V4H4v12h4" /></Svg>
)
// A memorial candle: marks the year and place of a death
export const CandleIcon = (p: IconProps) => (
  <Svg {...p}><path d="M9.5 20.5V11h5v9.5" /><path d="M12 11V9.5" /><path d="M12 8c-1.4-1.1-1.4-2.9 0-4.5 1.4 1.6 1.4 3.4 0 4.5z" /><path d="M7 20.5h10" /></Svg>
)
export const GlobeIcon = (p: IconProps) => (
  <Svg {...p}><circle cx="12" cy="12" r="8.5" /><path d="M3.5 12h17" /><path d="M12 3.5c2.4 2.4 3.6 5.2 3.6 8.5s-1.2 6.1-3.6 8.5c-2.4-2.4-3.6-5.2-3.6-8.5s1.2-6.1 3.6-8.5z" /></Svg>
)
export const ChevronDownIcon = (p: IconProps) => (
  <Svg {...p}><path d="m6 9 6 6 6-6" /></Svg>
)
export const FilterIcon = (p: IconProps) => (
  <Svg {...p}><path d="M4 7h9" /><path d="M19 7h1" /><circle cx="16" cy="7" r="2.5" /><path d="M4 17h1" /><path d="M11 17h9" /><circle cx="8" cy="17" r="2.5" /></Svg>
)
