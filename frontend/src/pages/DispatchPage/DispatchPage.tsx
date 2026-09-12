import { SectionHeader } from "../../components/Layout/SectionHeader"
import { StateMessage } from "../../components/State/StateMessage"
import { useDispatch } from "../../features/dispatch/useDispatch"
import { useSimulationMode } from "../../app/providers/SimulationContextProvider"
import { SimulationModeIndicator } from "../../components/Indicators/SimulationModeIndicator"
import {
  RenewableOpportunityDetail,
  RelevantFlexibility,
  RecommendedDispatch,
  DecisionRationale,
  ConstraintCheck,
  SimulationAction,
  SimulationResult,
} from "../../components/Dispatch"
import { spacing } from "../../styles/tokens/spacing"

export function DispatchPage() {
  const { isSimulationMode } = useSimulationMode()
  const {
    dispatchState,
    runSimulation,
    simulationResult,
    uiSlice,
  } = useDispatch()

  const { simulationRunning, simulationComplete } = uiSlice.getState()

  const dispatchData = dispatchState.data
  const dispatchStatus = dispatchState.status
  const dispatchError = dispatchState.error

  if (dispatchStatus === "loading") {
    return (
      <main className="dispatch-page" style={{ maxWidth: "1400px", margin: "0 auto", padding: spacing.lg }}>
        <SectionHeader title="Dispatch" subtitle="Analyze, recommend, and execute dispatch plans" />
        <StateMessage
          type="loading"
          title="Loading dispatch data..."
          message="Fetching system context and generating dispatch recommendation. Please wait."
        />
      </main>
    )
  }

  if (dispatchStatus === "error") {
    return (
      <main className="dispatch-page" style={{ maxWidth: "1400px", margin: "0 auto", padding: spacing.lg }}>
        <SectionHeader title="Dispatch" subtitle="Analyze, recommend, and execute dispatch plans" />
        <StateMessage
          type="error"
          title="Unable to load dispatch"
          message={dispatchError || "An error occurred while loading dispatch data."}
        />
      </main>
    )
  }

  if (!dispatchData) {
    return (
      <main className="dispatch-page" style={{ maxWidth: "1400px", margin: "0 auto", padding: spacing.lg }}>
        <SectionHeader title="Dispatch" subtitle="Analyze, recommend, and execute dispatch plans" />
        <StateMessage
          type="empty"
          title="No dispatch data available"
          message="There is no dispatch data to display for the current context."
        />
      </main>
    )
  }

  const {
    scenario,
    renewableOpportunity,
    flexibility,
    recommendedDispatch,
    constraintCheck,
  } = dispatchData

  return (
    <main className="dispatch-page" style={{ maxWidth: "1400px", margin: "0 auto", padding: spacing.lg }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: spacing.lg,
          flexWrap: "wrap",
          marginBottom: spacing.xl,
        }}
      >
        <div>
          <SectionHeader title="Dispatch" subtitle={`Scenario: ${scenario.name}`} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: spacing.md }}>
          <SimulationModeIndicator active={isSimulationMode} />
        </div>
      </header>

      <section className="dispatch-sections">
        <RenewableOpportunityDetail data={dispatchData} />
        <RelevantFlexibility flexibility={flexibility} />
        <RecommendedDispatch recommended={recommendedDispatch} />
        <DecisionRationale dispatch={recommendedDispatch} />
        <ConstraintCheck constraints={constraintCheck} />
        <SimulationAction
          onSimulate={async () => {
            uiSlice.setSimulationRunning(true)
            try {
              await runSimulation()
              uiSlice.setSimulationComplete(true)
              uiSlice.setSimulationRunning(false)
            } catch (error) {
              uiSlice.setSimulationRunning(false)
              console.error("Simulation failed:", error)
            }
          }}
          isSimulationRunning={simulationRunning}
        />
        <SimulationResult
          simulationResult={simulationResult}
          isDispatched={recommendedDispatch.status === "dispatched"}
          isSimulationComplete={simulationComplete}
        />
      </section>
    </main>
  )
}

export default DispatchPage