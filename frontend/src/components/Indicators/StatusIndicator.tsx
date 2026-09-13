import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export type StatusIndicatorColor = "primary" | "neutral" | "success" | "warning" | "error"

export type StatusIndicatorStatus =
  | "active"
  | "inactive"
  | "pending"
  | "complete"
  | "available"
  | "dispatched"
  | "completed"
  | "unavailable"
  | "normal"
  | "warning"
  | "violation"

export interface StatusIndicatorProps {
  status: StatusIndicatorStatus
  label?: string
  color?: StatusIndicatorColor
  className?: string
}

const colorConfig: Record<StatusIndicatorColor, { bg: string; border: string; text: string }> = {
  primary: {
    bg: colors.primary,
    border: colors.primary,
    text: colors.neutrals.warmCream,
  },
  neutral: {
    bg: colors.neutrals.mist,
    border: colors.neutrals.mist,
    text: colors.neutrals.ink,
  },
  success: {
    bg: colors.primary,
    border: colors.primary,
    text: colors.neutrals.warmCream,
  },
  warning: {
    bg: colors.neutrals.grey,
    border: colors.neutrals.grey,
    text: colors.neutrals.warmCream,
  },
  error: {
    bg: colors.neutrals.charcoal,
    border: colors.neutrals.charcoal,
    text: colors.neutrals.warmCream,
  },
}

const defaultColorForStatus: Record<StatusIndicatorStatus, StatusIndicatorColor> = {
  active: "primary",
  inactive: "neutral",
  pending: "warning",
  complete: "success",
  available: "primary",
  dispatched: "primary",
  completed: "success",
  unavailable: "neutral",
  normal: "success",
  warning: "warning",
  violation: "error",
}

export function StatusIndicator({
  status,
  label,
  color = defaultColorForStatus[status],
  className,
}: StatusIndicatorProps) {
  const cfg = colorConfig[color]

  const statusText =
    status === "active" || status === "available" || status === "dispatched" ? "Active" :
    status === "inactive" || status === "unavailable" ? "Inactive" :
    status === "pending" ? "Pending" :
    status === "complete" || status === "completed" ? "Complete" :
    status === "normal" ? "Normal" :
    status === "warning" ? "Warning" :
    status === "violation" ? "Violation" : "Unknown"

  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: spacing.xs,
        padding: `2px ${spacing.sm}`,
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        borderRadius: radii.xs,
        fontFamily: fonts.monospace,
        fontSize: fontSizes.xs,
        fontWeight: fontWeights.medium,
        color: cfg.text,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        whiteSpace: "nowrap",
      }}
      role="status"
      aria-label={`${statusText} status`}
    >
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          background: cfg.text,
          opacity: status === "inactive" || status === "unavailable" ? 0.4 : 1,
        }}
        aria-hidden="true"
      />
      {label || statusText}
    </span>
  )
}
