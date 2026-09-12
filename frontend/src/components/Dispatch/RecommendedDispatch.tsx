import type { RecommendedDispatch } from "../../data/types/domain/dispatch"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface RecommendedDispatchProps {
  recommended: RecommendedDispatch
}

export function RecommendedDispatch({ recommended }: RecommendedDispatchProps) {
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
        Recommended Dispatch
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
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: spacing.lg,
          }}
        >
          <div>
            <span
              style={{
                fontSize: fontSizes.xs,
                color: colors.neutrals.charcoal,
                fontWeight: fontWeights.medium,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "4px",
                display: "block",
              }}
            >
              Dispatch ID
            </span>
            <p
              style={{
                fontFamily: fonts.monospace,
                fontSize: fontSizes.lg,
                color: colors.primary,
                fontWeight: fontWeights.semibold,
              }}
            >
              {recommended.id}
            </p>
          </div>

          <div>
            <span
              style={{
                fontSize: fontSizes.xs,
                color: colors.neutrals.charcoal,
                fontWeight: fontWeights.medium,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "4px",
                display: "block",
              }}
            >
              Time Window
            </span>
            <p
              style={{
                fontSize: fontSizes.base,
                color: colors.neutrals.ink,
                fontWeight: fontWeights.regular,
              }}
            >
              {recommended.timeWindow}
            </p>
          </div>

          <div>
            <span
              style={{
                fontSize: fontSizes.xs,
                color: colors.neutrals.charcoal,
                fontWeight: fontWeights.medium,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "4px",
                display: "block",
              }}
            >
              Total Dispatched
            </span>
            <p
              style={{
                fontSize: fontSizes["2xl"],
                fontWeight: fontWeights.bold,
                color: colors.primary,
              }}
            >
              {recommended.totalDispatchedKw} kW
            </p>
          </div>
        </div>

        <div
          style={{
            marginBottom: spacing.lg,
          }}
        >
          <span
            style={{
              fontSize: fontSizes.xs,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.medium,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "4px",
              display: "block",
            }}
          >
            Rationale
          </span>
          <p
            style={{
              fontSize: fontSizes.base,
              color: colors.neutrals.charcoal,
              lineHeight: 1.5,
              fontStyle: "italic",
            }}
          >
            {recommended.rationale}
          </p>
        </div>

        <div>
          <span
            style={{
              fontSize: fontSizes.xs,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.medium,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "4px",
              display: "block",
            }}
          >
            Resources Dispatched
          </span>
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              marginTop: spacing.sm,
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
              gap: spacing.md,
            }}
          >
            {recommended.resources.map((resource) => (
              <li
                key={resource.id}
                style={{
                  padding: spacing.md,
                  background: colors.neutrals.mist,
                  borderRadius: radii.md,
                  border: `1px solid ${colors.neutrals.lightGrey}`,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                  }}
                >
                  <div>
                    <p
                      style={{
                        fontSize: fontSizes.sm,
                        fontWeight: fontWeights.semibold,
                        color: colors.neutrals.ink,
                        margin: 0,
                        marginBottom: spacing.xs,
                      }}
                    >
                      {resource.name}
                    </p>
                    <p
                      style={{
                        fontFamily: fonts.monospace,
                        fontSize: fontSizes.sm,
                        color: colors.neutrals.charcoal,
                        margin: 0,
                      }}
                    >
                      ID: {resource.id}
                    </p>
                  </div>
                  <div
                    style={{
                      textAlign: "right",
                    }}
                  >
                    <p
                      style={{
                        fontFamily: fonts.monospace,
                        fontSize: fontSizes.lg,
                        fontWeight: fontWeights.bold,
                        color: colors.primary,
                        margin: 0,
                      }}
                    >
                      {resource.dispatchedKw} kW
                    </p>
                    <span
                      style={{
                        fontSize: fontSizes.xs,
                        color: colors.neutrals.charcoal,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}
                    >
                      Capacity
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
