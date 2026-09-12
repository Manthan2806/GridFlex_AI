import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export type CapacityBarIntent = "primary" | "subtle" | "neutral" | "success"

export interface CapacityBarProps {
  value: number
  max: number
  label: string
  unit?: string
  intent?: CapacityBarIntent
  /** Visual label shown at the bar end (e.g. "Potential", "Expected", "Trusted") */
  visualLabel?: string
  className?: string
}

const intentColors: Record<CapacityBarIntent, { bg: string; fill: string; text: string }> = {
  primary: {
    bg: colors.neutrals.mist,
    fill: colors.primary,
    text: colors.neutrals.ink,
  },
  subtle: {
    bg: colors.neutrals.lightGrey,
    fill: colors.neutrals.grey,
    text: colors.neutrals.charcoal,
  },
  neutral: {
    bg: colors.neutrals.mist,
    fill: colors.neutrals.lightGrey,
    text: colors.neutrals.charcoal,
  },
  success: {
    bg: colors.neutrals.mist,
    fill: colors.primary,
    text: colors.neutrals.ink,
  },
}

export function CapacityBar({
  value,
  max,
  label,
  unit,
  intent = "primary",
  visualLabel,
  className,
}: CapacityBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  const cfg = intentColors[intent]
  const displayValue = unit ? `${value} ${unit}` : String(value)

  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: spacing.xs,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          gap: spacing.md,
          marginBottom: spacing.xs,
        }}
      >
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: fontSizes.sm,
            fontWeight: fontWeights.semibold,
            color: cfg.text,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          {visualLabel || label}
        </span>
        <span
          style={{
            fontFamily: fonts.monospace,
            fontSize: fontSizes.xl,
            fontWeight: fontWeights.semibold,
            color: cfg.fill,
          }}
          aria-label={`${value} ${unit || ""}`}
        >
          {displayValue}
        </span>
      </div>
      <div
        style={{
          position: "relative",
          height: "20px",
          background: cfg.bg,
          borderRadius: radii.sm,
          overflow: "hidden",
        }}
        role="img"
        aria-label={`${label}: ${value} out of ${max} ${unit || ""}`}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: cfg.fill,
            borderRadius: radii.sm,
            transition: "width 0.2s ease",
          }}
        />
      </div>
    </div>
  )
}
