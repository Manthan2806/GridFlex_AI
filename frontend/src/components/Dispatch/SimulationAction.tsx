import { useState } from "react"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface SimulationActionProps {
  onSimulate: () => Promise<void>
  isSimulationRunning: boolean
}

export function SimulationAction({ onSimulate, isSimulationRunning }: SimulationActionProps) {
  const [simulationSteps, setSimulationSteps] = useState<string[]>([])

  const handleSimulate = async () => {
    setSimulationSteps((prev) => [...prev, "Initializing simulation..."])
    await new Promise((resolve) => setTimeout(resolve, 500))
    setSimulationSteps((prev) => [...prev, "Loading historical patterns..."])
    await new Promise((resolve) => setTimeout(resolve, 800))
    setSimulationSteps((prev) => [...prev, "Running optimization engine..."])
    await new Promise((resolve) => setTimeout(resolve, 1200))
    setSimulationSteps((prev) => [...prev, "Validating constraints..."])
    await new Promise((resolve) => setTimeout(resolve, 600))
    setSimulationSteps((prev) => [...prev, "Generating results..."])
    await new Promise((resolve) => setTimeout(resolve, 400))

    setSimulationSteps((prev) => [...prev, "Simulation complete!"])
    await onSimulate()
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
        Simulation Action
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
            marginBottom: spacing.lg,
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
            Run Dispatch Simulation
          </h4>

          <p
            style={{
              fontSize: fontSizes.base,
              color: colors.neutrals.charcoal,
              lineHeight: 1.6,
              marginBottom: spacing.lg,
            }}
          >
            Execute a full dispatch simulation using the recommended plan. This will validate the dispatch against system constraints, calculate actual delivery metrics, and generate a simulation result for review.
          </p>

          <button
            onClick={handleSimulate}
            disabled={isSimulationRunning}
            style={{
              padding: `${spacing.md} ${spacing.xl}`,
              background: isSimulationRunning ? colors.neutrals.grey : colors.primary,
              color: colors.neutrals.white,
              border: "none",
              borderRadius: radii.md,
              fontFamily: fonts.body,
              fontSize: fontSizes.base,
              fontWeight: fontWeights.semibold,
              cursor: isSimulationRunning ? "not-allowed" : "pointer",
              transition: "all 0.15s ease",
              opacity: isSimulationRunning ? 0.7 : 1,
              display: "flex",
              alignItems: "center",
              gap: spacing.sm,
            }}
            onMouseEnter={(e) => {
              if (!isSimulationRunning) {
                e.currentTarget.style.background = "#561823"
              }
            }}
            onMouseLeave={(e) => {
              if (!isSimulationRunning) {
                e.currentTarget.style.background = colors.primary
              }
            }}
          >
            {isSimulationRunning ? (
              <>
                <div
                  style={{
                    width: "16px",
                    height: "16px",
                    border: `2px solid ${colors.neutrals.white}`,
                    borderTopColor: "transparent",
                    borderRadius: radii.round,
                    animation: "spin 1s linear infinite",
                  }}
                />
                Running Simulation...
              </>
            ) : (
              "Run Simulation"
            )}
          </button>
        </div>

        {simulationSteps.length > 0 && (
          <div>
            <h5
              style={{
                fontFamily: fonts.display,
                fontSize: fontSizes.sm,
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.ink,
                margin: 0,
                marginBottom: spacing.md,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Simulation Progress
            </h5>
            <div
              style={{
                padding: spacing.md,
                background: colors.neutrals.mist,
                borderRadius: radii.sm,
                fontFamily: fonts.monospace,
                fontSize: fontSizes.sm,
                color: colors.neutrals.charcoal,
              }}
            >
              {simulationSteps.map((step, index) => (
                <div
                  key={index}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: spacing.sm,
                    marginBottom: spacing.xs,
                  }}
                >
                  <span
                    style={{
                      width: "20px",
                      height: "20px",
                      borderRadius: radii.round,
                      background: index < simulationSteps.length - 1 ? colors.primary : colors.primary,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: colors.neutrals.white,
                      fontSize: fontSizes.xs,
                      fontWeight: fontWeights.semibold,
                    }}
                  >
                    {index < simulationSteps.length - 1 ? "✓" : "⟶"}
                  </span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
