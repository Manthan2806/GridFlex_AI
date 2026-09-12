import type { DispatchFlexibilityState } from "../../data/types/domain/dispatch"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface RelevantFlexibilityProps {
  flexibility: DispatchFlexibilityState
}

export function RelevantFlexibility({ flexibility }: RelevantFlexibilityProps) {
  const calculateProgressPercentage = (value: number, total: number) => {
    return Math.min(100, Math.max(0, (value / total) * 100))
  }

  const getProgressColor = (value: number, total: number) => {
    const percentage = (value / total) * 100
    if (percentage < 33) return colors.neutrals.grey
    if (percentage < 66) return colors.neutrals.lightGrey
    return colors.primary
  }

  const total = 520

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
        Relevant Flexibility
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
            flexDirection: "column",
            gap: spacing.lg,
          }}
        >
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                marginBottom: spacing.xs,
              }}
            >
              <span
                style={{
                  fontSize: fontSizes.sm,
                  fontWeight: fontWeights.semibold,
                  color: colors.neutrals.ink,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Potential
              </span>
              <span
                style={{
                  fontSize: fontSizes.lg,
                  fontWeight: fontWeights.semibold,
                  color: colors.primary,
                }}
              >
                {flexibility.potentialKw} kW
              </span>
            </div>
            <div
              style={{
                height: "8px",
                background: colors.neutrals.lightGrey,
                borderRadius: radii.sm,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${calculateProgressPercentage(flexibility.potentialKw, total)}%`,
                  height: "100%",
                  background: getProgressColor(flexibility.potentialKw, total),
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </div>

          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                marginBottom: spacing.xs,
              }}
            >
              <span
                style={{
                  fontSize: fontSizes.sm,
                  fontWeight: fontWeights.semibold,
                  color: colors.neutrals.ink,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Expected
              </span>
              <span
                style={{
                  fontSize: fontSizes.lg,
                  fontWeight: fontWeights.semibold,
                  color: colors.neutrals.charcoal,
                }}
              >
                {flexibility.expectedKw} kW
              </span>
            </div>
            <div
              style={{
                height: "8px",
                background: colors.neutrals.lightGrey,
                borderRadius: radii.sm,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${calculateProgressPercentage(flexibility.expectedKw, total)}%`,
                  height: "100%",
                  background: getProgressColor(flexibility.expectedKw, total),
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </div>

          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                marginBottom: spacing.xs,
              }}
            >
              <span
                style={{
                  fontSize: fontSizes.sm,
                  fontWeight: fontWeights.semibold,
                  color: colors.neutrals.ink,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Trusted
              </span>
              <span
                style={{
                  fontSize: fontSizes.lg,
                  fontWeight: fontWeights.semibold,
                  color: colors.primary,
                }}
              >
                {flexibility.trustedKw} kW
              </span>
            </div>
            <div
              style={{
                height: "8px",
                background: colors.neutrals.lightGrey,
                borderRadius: radii.sm,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${calculateProgressPercentage(flexibility.trustedKw, total)}%`,
                  height: "100%",
                  background: getProgressColor(flexibility.trustedKw, total),
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </div>
        </div>

        <div
          style={{
            marginTop: spacing.lg,
            padding: spacing.md,
            background: colors.neutrals.mist,
            borderRadius: radii.sm,
          }}
        >
          <span
            style={{
              fontSize: fontSizes.xs,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.medium,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Confidence Level
          </span>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: spacing.sm,
              marginTop: spacing.xs,
            }}
          >
            <span
              style={{
                fontSize: fontSizes.lg,
                fontWeight: fontWeights.bold,
                color: colors.primary,
              }}
            >
              {Math.round(flexibility.confidence * 100)}%
            </span>
            <span
              style={{
                fontSize: fontSizes.sm,
                color: colors.neutrals.charcoal,
              }}
            >
              {flexibility.confidence < 0.5 ? "Low reliability" : flexibility.confidence < 0.8 ? "Moderate reliability" : "High reliability"}
            </span>
          </div>

          <div
            style={{
              width: "100%",
              height: "8px",
              background: colors.neutrals.lightGrey,
              borderRadius: radii.sm,
              overflow: "hidden",
              marginTop: spacing.sm,
            }}
          >
            <div
              style={{
                width: `${flexibility.confidence * 100}%`,
                height: "100%",
                background: flexibility.confidence < 0.5 ? colors.neutrals.grey : flexibility.confidence < 0.8 ? colors.neutrals.lightGrey : colors.primary,
                borderRadius: radii.sm,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </div>
      </div>
    </section>
  )
}
