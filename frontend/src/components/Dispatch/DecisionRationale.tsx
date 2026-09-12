import type { RecommendedDispatch } from "../../data/types/domain/dispatch"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface DecisionRationaleProps {
  dispatch: RecommendedDispatch
}

export function DecisionRationale({ dispatch }: DecisionRationaleProps) {
  return (
    <section
      style={{
        marginBottom: spacing.xl,
      }}
    >
      <h3
        style={{
          fontFamily: fonts.display,
          fontSize: fontSizes.lg,
          fontWeight: fontWeights.semibold,
          marginBottom: spacing.md,
          color: colors.primary,
        }}
      >
        Decision Rationale
      </h3>

      <div
        style={{
          padding: spacing.lg,
          background: colors.neutrals.white,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.lg,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: spacing.xl,
            flexWrap: "wrap",
            marginBottom: spacing.lg,
          }}
        >
          <div
            style={{
              flex: 1,
              minWidth: "300px",
            }}
          >
            <h4
              style={{
                fontFamily: fonts.display,
                fontSize: fontSizes.base,
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.ink,
                margin: 0,
                marginBottom: spacing.md,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Technical Justification
            </h4>
            <p
              style={{
                fontSize: fontSizes.base,
                color: colors.neutrals.charcoal,
                lineHeight: 1.6,
              }}
            >
              {dispatch.rationale}
            </p>
          </div>

          <div
            style={{
              flex: 1,
              minWidth: "300px",
            }}
          >
            <h4
              style={{
                fontFamily: fonts.display,
                fontSize: fontSizes.base,
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.ink,
                margin: 0,
                marginBottom: spacing.md,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Decision Factors
            </h4>
            <ul
              style={{
                padding: 0,
                margin: 0,
                listStyle: "none",
              }}
            >
              <li
                style={{
                  padding: spacing.sm,
                  marginBottom: spacing.xs,
                  background: colors.neutrals.mist,
                  borderRadius: radii.sm,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                <strong style={{ color: colors.primary }}>Resource Availability:</strong> Selected {dispatch.resources.length} resources from available pool
              </li>
              <li
                style={{
                  padding: spacing.sm,
                  marginBottom: spacing.xs,
                  background: colors.neutrals.mist,
                  borderRadius: radii.sm,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                <strong style={{ color: colors.primary }}>Trust Scores:</strong> Resources ranked by historical reliability (85-91%)
              </li>
              <li
                style={{
                  padding: spacing.sm,
                  marginBottom: spacing.xs,
                  background: colors.neutrals.mist,
                  borderRadius: radii.sm,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                <strong style={{ color: colors.primary }}>Time Alignment:</strong> Dispatch window optimized for solar surplus (14:00-18:00)
              </li>
              <li
                style={{
                  padding: spacing.sm,
                  marginBottom: spacing.xs,
                  background: colors.neutrals.mist,
                  borderRadius: radii.sm,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                <strong style={{ color: colors.primary }}>Grid Impact:</strong> Maximizes renewable absorption while reducing peak load
              </li>
            </ul>
          </div>
        </div>

        <div
          style={{
            padding: spacing.md,
            background: colors.neutrals.mist,
            borderRadius: radii.sm,
            fontSize: fontSizes.sm,
            color: colors.neutrals.charcoal,
            fontStyle: "italic",
          }}
        >
          <strong>Note:</strong> This dispatch plan is simulated in the GridFlex AI environment and does not control physical devices. All decisions are based on historical data patterns and current system constraints.
        </div>
      </div>
    </section>
  )
}
