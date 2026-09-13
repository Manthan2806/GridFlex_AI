import { useCallback, useMemo, useReducer, useState } from "react"
import { useDataAdapter } from "../../app/providers/DataAdapterProvider"
import { ExperimentAPI } from "./experimentAPI"
import type { HorizonSimulationResult } from "../../data/types/domain/experiment"
import type { ExperimentState } from "./types"
import { experimentReducer, initialExperimentUIState } from "./experimentSlice"

export function useExperiments() {
  const adapter = useDataAdapter()
  const api = useMemo(() => new ExperimentAPI(adapter), [adapter])
  const [experimentState, setExperimentState] = useState<ExperimentState>({
    status: "idle",
    data: null,
    error: null,
    lastFetched: null,
  })
  const [simulationResult, setSimulationResult] = useState<HorizonSimulationResult | null>(null)
  const [uiState, uiDispatch] = useReducer(experimentReducer, initialExperimentUIState)

  const runHorizonSimulation = useCallback(async () => {
    uiDispatch({ type: "setSimulationRunning", payload: true })
    setExperimentState((previous) => ({ ...previous, status: "loading", error: null }))
    try {
      const result = await api.runFullHorizonSimulation()
      setSimulationResult(result)
      setExperimentState({
        status: "success",
        data: result,
        error: null,
        lastFetched: Date.now(),
      })
      uiDispatch({ type: "setSimulationComplete", payload: true })
      uiDispatch({ type: "setSimulationRunning", payload: false })
      return result
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to run the horizon simulation"
      setExperimentState({ status: "error", data: null, error: message, lastFetched: null })
      uiDispatch({ type: "setSimulationRunning", payload: false })
      return null
    }
  }, [api])

  return {
    experimentState,
    runHorizonSimulation,
    simulationResult,
    uiState,
    uiDispatch,
    // Legacy compatibility
    getSimulationState: () => ({
      simulationRunning: uiState.simulationRunning,
      simulationComplete: uiState.simulationComplete,
    }),
  }
}
