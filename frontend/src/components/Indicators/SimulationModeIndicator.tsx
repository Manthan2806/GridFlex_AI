import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface SimulationModeIndicatorProps {
  active?: boolean
  className?: string
}

export function SimulationModeIndicator({
  active = true,
  className,
}: SimulationModeIndicatorProps) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: spacing.sm,
        padding: `${spacing.xs} ${spacing.md}`,
        background: colors.primary,
        borderRadius: radii.round,
        marginTop: spacing.lg,
        alignSelf: "flex-start",
      }}
      className={className}
      role="status"
      aria-label="Simulation mode active"
    >
      <span
        style={{
          width: "8px",
          height: "8px",
          borderRadius: radii.round,
          background: "#FFFFFF",
          display: "inline-block",
        }}
        aria-hidden="true"
      />
      <span
        style={{
          fontFamily: fonts.body,
          fontSize: fontSizes.xs,
          fontWeight: fontWeights.semibold,
          color: "#FFFFFF",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        Simulation Mode
      </span>
    </div>
  )
}