/**
 * ============================================================================
 * File: webapp/src/components/OrcaLogo.tsx
 * Purpose:
 *   Inline ORCA catfish-inspired mark for React surfaces. Designed to read
 *   clearly at small sizes while matching the platform's security-forward UI.
 * ============================================================================
 */

type OrcaLogoVariant = "color" | "mono" | "outline" | "inverted";

type OrcaLogoProps = {
  className?: string;
  title?: string;
  variant?: OrcaLogoVariant;
};

const variantTokens: Record<OrcaLogoVariant, Record<string, string>> = {
  color: {
    ring: "rgba(0, 229, 255, 0.16)",
    shield: "var(--orca-electric-cyan)",
    bodyPrimary: "var(--orca-electric-cyan)",
    bodySecondary: "var(--orca-ocean-blue)",
    bodyFinal: "var(--orca-black)",
    eye: "var(--orca-white)",
    whiskerPrimary: "var(--orca-electric-cyan)",
    whiskerSecondary: "var(--orca-ocean-blue)",
  },
  mono: {
    ring: "rgba(255, 255, 255, 0.14)",
    shield: "currentColor",
    bodyPrimary: "currentColor",
    bodySecondary: "currentColor",
    bodyFinal: "currentColor",
    eye: "var(--orca-white)",
    whiskerPrimary: "currentColor",
    whiskerSecondary: "currentColor",
  },
  outline: {
    ring: "transparent",
    shield: "var(--orca-electric-cyan)",
    bodyPrimary: "transparent",
    bodySecondary: "transparent",
    bodyFinal: "transparent",
    eye: "var(--orca-electric-cyan)",
    whiskerPrimary: "var(--orca-electric-cyan)",
    whiskerSecondary: "var(--orca-ocean-blue)",
  },
  inverted: {
    ring: "rgba(255, 255, 255, 0.16)",
    shield: "var(--orca-white)",
    bodyPrimary: "var(--orca-white)",
    bodySecondary: "var(--orca-white)",
    bodyFinal: "var(--orca-white)",
    eye: "var(--orca-black)",
    whiskerPrimary: "var(--orca-white)",
    whiskerSecondary: "var(--orca-white)",
  },
};

export default function OrcaLogo({
  className,
  title = "ORCA logo",
  variant = "color",
}: OrcaLogoProps) {
  const palette = variantTokens[variant];
  const outlineOnly = variant === "outline";

  return (
    <svg
      aria-label={title}
      className={className}
      role="img"
      viewBox="0 0 512 512"
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <defs>
        <linearGradient
          id={`orca-mark-body-${variant}`}
          x1="112"
          x2="384"
          y1="92"
          y2="408"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor={palette.bodyPrimary} />
          <stop offset="0.52" stopColor={palette.bodySecondary} />
          <stop offset="1" stopColor={palette.bodyFinal} />
        </linearGradient>
      </defs>

      <path
        d="M256 48 401 111c28 12 47 39 49 69v80c0 105-68 165-194 204C130 425 62 365 62 260v-80c2-30 21-57 49-69Z"
        fill={palette.ring}
      />
      <path
        d="M256 76 380 129c20 8 34 27 36 49v74c0 87-54 136-160 175-106-39-160-88-160-175v-74c2-22 16-41 36-49Z"
        fill="none"
        stroke={palette.shield}
        strokeLinejoin="round"
        strokeWidth="16"
      />
      <path
        d="M152 305c26-29 54-44 87-52-28-20-42-46-43-77 0-54 41-94 102-94 22 0 45 5 69 15-32 3-60 20-75 43 35 9 58 34 58 68 0 40-30 73-77 87 31 9 56 25 79 50-26-8-54-11-82-9-24 31-61 52-114 62 23-24 37-50 42-77-20-1-35-4-46-16Z"
        fill={outlineOnly ? "none" : `url(#orca-mark-body-${variant})`}
        stroke={outlineOnly ? palette.bodySecondary : "none"}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={outlineOnly ? 16 : 0}
      />
      <circle cx="275" cy="181" r="7" fill={palette.eye} />
      <circle cx="316" cy="177" r="6" fill={palette.eye} opacity="0.88" />
      <path
        d="M173 231c-36 8-63 26-80 57 35-10 64-11 90-6"
        fill="none"
        stroke={palette.whiskerPrimary}
        strokeLinecap="round"
        strokeWidth="10"
      />
      <path
        d="M183 249c-46 14-75 39-89 77 44-17 81-22 110-15"
        fill="none"
        opacity="0.9"
        stroke={palette.whiskerSecondary}
        strokeLinecap="round"
        strokeWidth="8"
      />
      <path
        d="M335 231c37 8 64 26 81 57-35-10-65-11-91-6"
        fill="none"
        stroke={palette.whiskerPrimary}
        strokeLinecap="round"
        strokeWidth="10"
      />
      <path
        d="M327 249c45 14 74 39 88 77-44-17-80-22-109-15"
        fill="none"
        opacity="0.9"
        stroke={palette.whiskerSecondary}
        strokeLinecap="round"
        strokeWidth="8"
      />
      <path
        d="M255 402c-29 14-58 24-89 32 16-16 28-36 34-59"
        fill="none"
        stroke={
          variant === "inverted"
            ? palette.whiskerPrimary
            : palette.whiskerSecondary
        }
        strokeLinecap="round"
        strokeWidth="9"
      />
    </svg>
  );
}