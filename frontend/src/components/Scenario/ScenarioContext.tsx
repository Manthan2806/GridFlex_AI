import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export type ScenarioContextState = "loading" | "success"

export interface ScenarioContextProps {
  scenario: {
    id: string
    name: string
    timeHorizon: number | string
    seed: number
    category: string
    mode: "simulation" | "live"
  } | null
  state?: ScenarioContextState
  className?: string
}

export function ScenarioContext({
  scenario,
  state = "success",
  className,
}: ScenarioContextProps) {
  if (state === "loading") {
    return (
      <div
        style={{
          padding: `${spacing.md} ${spacing.lg}`,
          background: "rgba(255,255,255,0.3)",
          borderRadius: radii.lg,
          border: `1px solid ${colors.neutrals.mist}`,
        }}
        className={className}
        role="region"
        aria-label="Scenario context"
      >
        <p
          style={{
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.charcoal,
            margin: 0,
          }}
        >
          Loading scenario context...
        </p>
      </div>
    )
  }

  if (!scenario) {
    return null
  }

  return (
    <div
      style={{
        marginTop: spacing.sm,
        marginBottom: spacing.lg,
        padding: `${spacing.md} ${spacing.lg}`,
        background: "rgba(255,255,255,0.3)",
        borderRadius: radii.lg,
        border: `1px solid ${colors.neutrals.mist}`,
      }}
      className={className}
      role="region"
      aria-label="Scenario context"
    >
      <div style={{ display: "flex", gap: spacing.xl, flexWrap: "wrap" }}>
        <div>
          <span
            style={{
              display: "block",
              fontSize: fontSizes.xs,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.medium,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "2px",
            }}
          >
            Scenario ID
          </span>
          <span
            style={{
              fontFamily: fonts.monospace,
              fontSize: fontSizes.sm,
              color: colors.neutrals.ink,
              fontWeight: fontWeights.regular,
            }}
          >
            {scenario.id}
          </span>
        </div>
        <div>
          <span
            style={{
              display: "block",
              fontSize: fontSizes.xs,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.medium,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "2px",
            }}
          >
            Time Horizon
          </span>
          <span
            style={{
              fontFamily: fonts.monospace,
              fontSize: fontSizes.sm,
              color: colors.neutrals.ink,
              fontWeight: fontWeights.regular,
            }}
          >
            {typeof scenario.timeHorizon === "number"
              ? `${scenario.timeHorizon} minutes`
              : scenario.timeHorizon}
          </span>
        </div>
        <div>
          <span
            style={{
              display: "block",
              fontSize: fontSizes.xs,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.medium,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "2px",
            }}
          >
            Mode
          </span>
          <span
            style={{
              fontFamily: fonts.body,
              fontSize: fontSizes.sm,
              color: colors.neutrals.ink,
              fontWeight: fontWeights.regular,
            }}
          >
            {scenario.mode}
          </span>
        </div>
      </div>
    </div>
  )
}