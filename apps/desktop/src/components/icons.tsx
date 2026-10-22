/**
 * UnionPDF icon set - simple geometric line icons drawn for this project.
 * All icons share a 16x16 box, 1.5 stroke width and `currentColor`.
 */
interface IconProps {
  size?: number;
  className?: string;
}

function Svg({ size = 16, className, children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      {children}
    </svg>
  );
}

export const IconOpen = (p: IconProps) => (
  <Svg {...p}>
    <path d="M1.5 4.5h4l1.5 2h7.5v6a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1z" />
    <path d="M1.5 6.5h13" />
  </Svg>
);

export const IconSave = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 2.5h8l2.5 2.5v8a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1z" />
    <path d="M5 2.5v3.5h5V2.5M5 13.5v-4h6v4" />
  </Svg>
);

export const IconRotateLeft = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 7a5 5 0 1 1 1.2 5" />
    <path d="M2 3.5V7h3.5" />
  </Svg>
);

export const IconRotateRight = (p: IconProps) => (
  <Svg {...p}>
    <path d="M13 7a5 5 0 1 0-1.2 5" />
    <path d="M14 3.5V7h-3.5" />
  </Svg>
);

export const IconExtract = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 2.5h5v5H4z" />
    <path d="M9 2.5h3.5v11H9" />
    <path d="M1.5 9.5h4M4 7l2 2.5L4 12" />
  </Svg>
);

export const IconMerge = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2 2.5h4.5v4.5H2z" />
    <path d="M9.5 2.5H14v4.5H9.5z" />
    <path d="M4.25 7v3.5a1 1 0 0 0 1 1h6.5" />
    <path d="M10 9.5 12 11.5 10 13.5" />
  </Svg>
);

export const IconHighlight = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 11.5h10" strokeWidth="2.6" />
    <path d="M4.5 8.5 9 4l3 3-4.5 4.5H4.5z" />
  </Svg>
);

export const IconUnderline = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4.5 3v4.5a3.5 3.5 0 0 0 7 0V3" />
    <path d="M3 13.5h10" strokeWidth="2" />
  </Svg>
);

export const IconNote = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2.5 3.5h11v7h-4.5L6 13.5v-3H2.5z" />
    <path d="M5 6.5h6" />
  </Svg>
);

export const IconTextBox = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2.5 3.5h11v9h-11z" strokeDasharray="2 1.5" />
    <path d="M6 6.5h4M8 6.5v4" />
  </Svg>
);

export const IconForm = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2.5 3.5h11v9h-11z" />
    <path d="M5 6.5h2M5 9.5h2M9 6.5h3M9 9.5h3" />
  </Svg>
);

export const IconZoomIn = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="7" cy="7" r="4.5" />
    <path d="M10.5 10.5 14 14M7 5v4M5 7h4" />
  </Svg>
);

export const IconZoomOut = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="7" cy="7" r="4.5" />
    <path d="M10.5 10.5 14 14M5 7h4" />
  </Svg>
);

export const IconFitWidth = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2 2.5v11M14 2.5v11" />
    <path d="M5 8h6M5 8l1.5-1.5M5 8l1.5 1.5M11 8 9.5 6.5M11 8l-1.5 1.5" />
  </Svg>
);

export const IconFitPage = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3.5 1.5h9v13h-9z" />
    <path d="M1.5 8h2M12.5 8h2" />
  </Svg>
);

export const IconContinuous = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 1.5h8v5H4zM4 9.5h8v5H4z" />
  </Svg>
);

export const IconSinglePage = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 1.5h8v13H4z" />
  </Svg>
);

export const IconSidebar = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2.5 3h11v10h-11z" />
    <path d="M6.5 3v10" />
  </Svg>
);

export const IconPrev = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9.5 3 5 8l4.5 5" />
  </Svg>
);

export const IconNext = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6.5 3 11 8l-4.5 5" />
  </Svg>
);

export const IconClose = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 4l8 8M12 4l-8 8" />
  </Svg>
);

export const IconWarning = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8 2 14.5 13.5h-13z" />
    <path d="M8 6.5v3.5M8 11.8v.2" />
  </Svg>
);

export const IconChevronDown = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 6.5 8 10.5l4-4" />
  </Svg>
);

export const IconToolbar = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2 4h12M2 8h12M2 12h12" />
  </Svg>
);

export const IconSearch = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="7" cy="7" r="4.5" />
    <path d="M10.5 10.5 14 14" />
  </Svg>
);

export const IconAutoScroll = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8 2.5v9M5 8.5l3 3 3-3" />
    <path d="M2.5 13.5h11" />
  </Svg>
);

export const IconBookmark = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 2.5h8v11l-4-3-4 3z" />
  </Svg>
);

export const IconSplit = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8 2v5" />
    <path d="M4.5 4.5 8 7.5l3.5-3" />
    <path d="M3 9.5h10v4H3z" />
  </Svg>
);

export const IconConvert = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2.5 4.5h6v7h-6z" />
    <path d="M11 8.5h3M12.5 7l1.5 1.5-1.5 1.5" />
  </Svg>
);

export const IconChevronUp = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 9.5 8 5.5l4 4" />
  </Svg>
);
