import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export type StatusType =
  | "available"
  | "dispatched"
  | "completed"
  | "unavailable"
  | "normal"
  | "violation"
  | "warning"

export interface StatusIndicatorProps {
  status: StatusType
  label?: string
  className?: string
}

const burgundy = colors.primary
const burgundyRgb = "107, 30, 46"

const tint = (amount: number) => `rgba(${burgundyRgb}, ${amount})`

const statusConfig: Record<
  StatusType,
  { color: string; bgColor: string }
> = {
  available: { color: burgundy, bgColor: tint(0.06) },
  dispatched: { color: burgundy, bgColor: tint(0.16) },
  completed: { color: colors.neutrals.white, bgColor: tint(0.64) },
  unavailable: { color: colors.neutrals.grey, bgColor: colors.neutrals.mist },
  normal: { color: colors.neutrals.charcoal, bgColor: colors.neutrals.white },
  violation: { color: colors.neutrals.white, bgColor: burgundy },
  warning: { color: colors.neutrals.charcoal, bgColor: tint(0.24) },
}

export function StatusIndicator({
  status,
  label,
  className,
}: StatusIndicatorProps) {
  const config = statusConfig[status] || statusConfig.normal

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: spacing.xs,
        padding: `${spacing.xs} ${spacing.md}`,
        background: config.bgColor,
        borderRadius: radii.round,
        fontFamily: fonts.body,
        fontSize: fontSizes.xs,
        fontWeight: fontWeights.semibold,
        color: config.color,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
      className={className}
      role="status"
      aria-label={label || status}
    >
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: radii.round,
          background: config.color,
          display: "inline-block",
          flexShrink: 0,
        }}
        aria-hidden="true"
      />
      {label || status}
    </div>
  )
}