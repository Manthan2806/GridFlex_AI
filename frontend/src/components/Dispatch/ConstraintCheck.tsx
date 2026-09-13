import type { ConstraintCheckResult } from "../../data/types/domain/dispatch"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface ConstraintCheckProps {
  constraints: ConstraintCheckResult
}

export function ConstraintCheck({ constraints }: ConstraintCheckProps) {
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
        Constraint Check
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
            alignItems: "center",
            gap: spacing.md,
            marginBottom: spacing.lg,
          }}
        >
          <div
            style={{
              width: "60px",
              height: "60px",
              borderRadius: radii.round,
              background: constraints.passed ? colors.primary : colors.neutrals.charcoal,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: colors.neutrals.white,
              fontWeight: fontWeights.bold,
              fontSize: fontSizes.lg,
            }}
          >
            {constraints.passed ? "✓" : "✗"}
          </div>

          <div>
            <h4
              style={{
                fontFamily: fonts.display,
                fontSize: fontSizes.base,
                fontWeight: fontWeights.semibold,
                color: constraints.passed ? colors.primary : colors.neutrals.charcoal,
                margin: 0,
                marginBottom: spacing.xs,
              }}
            >
              {constraints.passed ? "All Constraints Passed" : "Constraint Violations Detected"}
            </h4>
            <p
              style={{
                fontSize: fontSizes.sm,
                color: colors.neutrals.charcoal,
                margin: 0,
              }}
            >
              {constraints.passed
                ? "The recommended dispatch plan meets all specified system constraints."
                : "The dispatch plan requires adjustments before implementation."}
            </p>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: spacing.lg,
            marginBottom: spacing.lg,
          }}
        >
          <div>
            <h5
              style={{
                fontFamily: fonts.display,
                fontSize: fontSizes.sm,
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.ink,
                margin: 0,
                marginBottom: spacing.sm,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Valid Constraints
            </h5>
            {constraints.constraints.length > 0 ? (
              <ul
                style={{
                  padding: 0,
                  margin: 0,
                  listStyle: "none",
                }}
              >
                {constraints.constraints.map((constraint, index) => (
                  <li
                    key={index}
                    style={{
                      padding: spacing.xs,
                      marginBottom: spacing.xs,
                      background: colors.neutrals.mist,
                      borderRadius: radii.sm,
                      fontSize: fontSizes.sm,
                      color: colors.neutrals.charcoal,
                      display: "flex",
                      alignItems: "center",
                      gap: spacing.xs,
                    }}
                  >
                    <span
                      style={{
                        width: "6px",
                        height: "6px",
                        borderRadius: radii.round,
                        background: colors.primary,
                        display: "inline-block",
                      }}
                    />
                    {constraint}
                  </li>
                ))}
              </ul>
            ) : (
              <p
                style={{
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                  fontStyle: "italic",
                }}
              >
                No constraints defined.
              </p>
            )}
          </div>

          <div>
            <h5
              style={{
                fontFamily: fonts.display,
                fontSize: fontSizes.sm,
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.ink,
                margin: 0,
                marginBottom: spacing.sm,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Violations & Warnings
            </h5>
            {(constraints.violations.length > 0 || constraints.deadlineViolations.length > 0) ? (
              <div>
                {constraints.violations.length > 0 && (
                  <div style={{ marginBottom: constraints.deadlineViolations.length > 0 ? spacing.md : 0 }}>
                    <h6
                      style={{
                        fontFamily: fonts.display,
                        fontSize: fontSizes.xs,
                        fontWeight: fontWeights.semibold,
                        color: colors.primary,
                        margin: 0,
                        marginBottom: spacing.xs,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}
                    >
                      System Constraints
                    </h6>
                    <ul
                      style={{
                        padding: 0,
                        margin: 0,
                        listStyle: "none",
                      }}
                    >
                      {constraints.violations.map((violation, index) => (
                        <li
                          key={index}
                          style={{
                            padding: spacing.xs,
                            marginBottom: spacing.xs,
                            background: `${colors.primary}15`,
                            borderRadius: radii.sm,
                            fontSize: fontSizes.sm,
                            color: colors.primary,
                            display: "flex",
                            alignItems: "center",
                            gap: spacing.xs,
                            border: `1px solid ${colors.primary}30`,
                          }}
                        >
                          <span style={{ fontWeight: fontWeights.bold }}>!</span> {violation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {constraints.deadlineViolations.length > 0 && (
                  <div>
                    <h6
                      style={{
                        fontFamily: fonts.display,
                        fontSize: fontSizes.xs,
                        fontWeight: fontWeights.semibold,
                        color: colors.primary,
                        margin: 0,
                        marginBottom: spacing.xs,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}
                    >
                      Deadline Violations
                    </h6>
                    <ul
                      style={{
                        padding: 0,
                        margin: 0,
                        listStyle: "none",
                      }}
                    >
                      {constraints.deadlineViolations.map((violation, index) => (
                        <li
                          key={index}
                          style={{
                            padding: spacing.xs,
                            marginBottom: spacing.xs,
                            background: `${colors.primary}15`,
                            borderRadius: radii.sm,
                            fontSize: fontSizes.sm,
                            color: colors.primary,
                            display: "flex",
                            alignItems: "center",
                            gap: spacing.xs,
                            border: `1px solid ${colors.primary}30`,
                          }}
                        >
                          <span style={{ fontWeight: fontWeights.bold }}>⚠</span> {violation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p
                style={{
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                  fontStyle: "italic",
                }}
              >
                No violations detected.
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
