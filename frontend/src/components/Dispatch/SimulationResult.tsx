import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface SimulationResultProps {
  simulationResult: {
    id: string
    status: "committed" | "partial" | "failed"
    actualFlexibilityKw: number
    renewableAbsorptionKwh: number
    constraintViolations: string[]
    deadlineViolations: string[]
    reboundKwh: number
    deliveryRatio: number
    timestamp: string
  } | null
  isDispatched: boolean
  isSimulationComplete: boolean
}

export function SimulationResult({ simulationResult, isDispatched, isSimulationComplete }: SimulationResultProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "committed": return colors.primary
      case "partial": return colors.neutrals.lightGrey
      case "failed": return colors.neutrals.charcoal
      default: return colors.neutrals.grey
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "committed": return "Simulation Committed"
      case "partial": return "Simulation Partially Committed"
      case "failed": return "Simulation Failed"
      default: return "Unknown Status"
    }
  }

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
        Simulation Result
      </h3>

      <div
        style={{
          padding: spacing.lg,
          background: colors.neutrals.white,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.lg,
        }}
      >
        {!simulationResult && !isSimulationComplete ? (
          <div
            style={{
              textAlign: "center",
              padding: spacing.xl,
              color: colors.neutrals.charcoal,
            }}
          >
            <p
              style={{
                fontSize: fontSizes.base,
                fontStyle: "italic",
                marginBottom: spacing.sm,
              }}
            >
              No simulation has been run yet.
            </p>
            <p
              style={{
                fontSize: fontSizes.sm,
                color: colors.neutrals.grey,
              }}
            >
              Click "Run Simulation" to execute the dispatch plan and view results.
            </p>
          </div>
        ) : simulationResult ? (
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: spacing.md,
                marginBottom: spacing.lg,
                padding: spacing.md,
                background: colors.neutrals.mist,
                borderRadius: radii.sm,
              }}
            >
              <div
                style={{
                  width: "50px",
                  height: "50px",
                  borderRadius: radii.round,
                  background: getStatusColor(simulationResult.status),
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: colors.neutrals.white,
                  fontWeight: fontWeights.bold,
                  fontSize: fontSizes.lg,
                }}
              >
                {simulationResult.status === "committed" ? "✓" : simulationResult.status === "partial" ? "⚠" : "✗"}
              </div>
              <div>
                <h4
                  style={{
                    fontFamily: fonts.display,
                    fontSize: fontSizes.base,
                    fontWeight: fontWeights.semibold,
                    color: colors.neutrals.ink,
                    margin: 0,
                    marginBottom: spacing.xs,
                  }}
                >
                  {getStatusText(simulationResult.status)}
                </h4>
                <p
                  style={{
                    fontSize: fontSizes.sm,
                    color: colors.neutrals.charcoal,
                    margin: 0,
                  }}
                >
                  Simulation ID: {simulationResult.id}
                </p>
              </div>
              <div style={{ marginLeft: "auto" }}>
                <p
                  style={{
                    fontSize: fontSizes.sm,
                    color: colors.neutrals.charcoal,
                    margin: 0,
                  }}
                >
                  {simulationResult.timestamp}
                </p>
              </div>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: spacing.lg,
                marginBottom: spacing.lg,
              }}
            >
              <div
                style={{
                  padding: spacing.md,
                  background: colors.neutrals.mist,
                  borderRadius: radii.md,
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
                  Actual Flexibility
                </span>
                <span
                  style={{
                    fontSize: fontSizes["2xl"],
                    fontWeight: fontWeights.bold,
                    color: colors.primary,
                  }}
                >
                  {simulationResult.actualFlexibilityKw} kW
                </span>
              </div>

              <div
                style={{
                  padding: spacing.md,
                  background: colors.neutrals.mist,
                  borderRadius: radii.md,
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
                  Renewable Absorption
                </span>
                <span
                  style={{
                    fontSize: fontSizes["2xl"],
                    fontWeight: fontWeights.bold,
                    color: colors.primary,
                  }}
                >
                  {simulationResult.renewableAbsorptionKwh} kWh
                </span>
              </div>

              <div
                style={{
                  padding: spacing.md,
                  background: colors.neutrals.mist,
                  borderRadius: radii.md,
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
                  Delivery Ratio
                </span>
                <span
                  style={{
                    fontSize: fontSizes["2xl"],
                    fontWeight: fontWeights.bold,
                    color: simulationResult.deliveryRatio >= 1 ? colors.primary : colors.neutrals.charcoal,
                  }}
                >
                  {(simulationResult.deliveryRatio * 100).toFixed(1)}%
                </span>
              </div>

              <div
                style={{
                  padding: spacing.md,
                  background: colors.neutrals.mist,
                  borderRadius: radii.md,
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
                  Rebound Energy
                </span>
                <span
                  style={{
                    fontSize: fontSizes["2xl"],
                    fontWeight: fontWeights.bold,
                    color: colors.neutrals.ink,
                  }}
                >
                  {simulationResult.reboundKwh} kWh
                </span>
              </div>
            </div>

            {(simulationResult.constraintViolations.length > 0 || simulationResult.deadlineViolations.length > 0) && (
              <div
                style={{
                  marginTop: spacing.lg,
                }}
              >
                <h5
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
                  Issues Found
                </h5>
                {simulationResult.constraintViolations.length > 0 && (
                  <div style={{ marginBottom: simulationResult.deadlineViolations.length > 0 ? spacing.md : 0 }}>
                    <span
                      style={{
                        fontSize: fontSizes.sm,
                        fontWeight: fontWeights.semibold,
                        color: colors.primary,
                        marginBottom: spacing.xs,
                        display: "block",
                      }}
                    >
                      Constraint Violations
                    </span>
                    <ul
                      style={{
                        padding: 0,
                        margin: 0,
                        listStyle: "none",
                      }}
                    >
                      {simulationResult.constraintViolations.map((violation, index) => (
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

                {simulationResult.deadlineViolations.length > 0 && (
                  <div>
                    <span
                      style={{
                        fontSize: fontSizes.sm,
                        fontWeight: fontWeights.semibold,
                        color: colors.primary,
                        marginBottom: spacing.xs,
                        display: "block",
                      }}
                    >
                      Deadline Violations
                    </span>
                    <ul
                      style={{
                        padding: 0,
                        margin: 0,
                        listStyle: "none",
                      }}
                    >
                      {simulationResult.deadlineViolations.map((violation, index) => (
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
            )}

            <div
              style={{
                marginTop: spacing.lg,
                padding: spacing.md,
                background: colors.neutrals.mist,
                borderRadius: radii.sm,
                fontSize: fontSizes.sm,
                color: colors.neutrals.charcoal,
              }}
            >
              <strong>Simulation Status:</strong> The dispatch has been {isDispatched ? "committed to the grid" : "prepared for potential dispatch"}
            </div>
          </div>
        ) : (
          <div
            style={{
              textAlign: "center",
              padding: spacing.xl,
              color: colors.neutrals.charcoal,
            }}
          >
            <p
              style={{
                fontSize: fontSizes.base,
                fontStyle: "italic",
                marginBottom: spacing.sm,
              }}
            >
              Simulation in progress...
            </p>
            <p
              style={{
                fontSize: fontSizes.sm,
                color: colors.neutrals.grey,
              }}
            >
              The simulation is currently being processed. Please wait.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}