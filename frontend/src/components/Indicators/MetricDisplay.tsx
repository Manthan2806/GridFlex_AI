import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export type MetricDisplayState = "loading" | "success" | "empty" | "error"

export interface MetricDisplayProps {
  label: string
  value?: number | string | null
  unit?: string
  state?: MetricDisplayState
  error?: string
  className?: string
}

export function MetricDisplay({
  label,
  value,
  unit,
  state = "success",
  error,
  className,
}: MetricDisplayProps) {
  if (state === "loading") {
    return (
      <div
        style={{
          padding: `${spacing.lg} ${spacing.xl}`,
          background: "rgba(255,255,255,0.3)",
          borderRadius: radii.lg,
          border: `1px solid ${colors.neutrals.mist}`,
        }}
        className={className}
      >
        <p
          style={{
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.charcoal,
            margin: 0,
          }}
        >
          Loading metric...
        </p>
      </div>
    )
  }

  if (state === "error") {
    return (
      <div
        style={{
          padding: `${spacing.lg} ${spacing.xl}`,
          background: "rgba(255,255,255,0.3)",
          borderRadius: radii.lg,
          border: `1px solid ${colors.neutrals.mist}`,
        }}
        className={className}
        role="alert"
      >
        <p
          style={{
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.primary,
            margin: 0,
          }}
        >
          {error || "Unable to load metric."}
        </p>
      </div>
    )
  }

  if (state === "empty" || value === null || value === undefined || value === "") {
    return (
      <div
        style={{
          padding: `${spacing.lg} ${spacing.xl}`,
          background: "rgba(255,255,255,0.3)",
          borderRadius: radii.lg,
          border: `1px solid ${colors.neutrals.mist}`,
        }}
        className={className}
      >
        <p
          style={{
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.charcoal,
            margin: 0,
          }}
        >
          {label} is not available.
        </p>
      </div>
    )
  }

  return (
    <div
      style={{
        padding: `${spacing.lg} ${spacing.xl}`,
        background: "rgba(255,255,255,0.3)",
        borderRadius: radii.lg,
        border: `1px solid ${colors.neutrals.mist}`,
      }}
      className={className}
    >
      <span
        style={{
          display: "block",
          fontSize: fontSizes.xs,
          color: colors.neutrals.charcoal,
          fontWeight: fontWeights.medium,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          marginBottom: "4px",
        }}
      >
        {label}
      </span>
      <span
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: spacing.sm,
          fontFamily: fonts.body,
          fontSize: fontSizes.xl,
          fontWeight: fontWeights.semibold,
          color: colors.neutrals.ink,
        }}
      >
        <span style={{ fontFamily: fonts.monospace }}>{value}</span>
        {unit ? (
          <span
            style={{
              fontFamily: fonts.monospace,
              fontSize: fontSizes.sm,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.regular,
            }}
          >
            {unit}
          </span>
        ) : null}
      </span>
    </div>
  )
}