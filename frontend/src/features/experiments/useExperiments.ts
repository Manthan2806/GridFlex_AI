import { useCallback, useEffect, useMemo, useReducer, useState } from "react"
import { useDataAdapter } from "../../app/providers/DataAdapterProvider"
import { ExperimentAPI } from "./experimentAPI"
import type { HorizonSimulationResult } from "../../../data/types/domain/experiment"
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

  useEffect(() => {
    if (experimentState.status === "idle") {
      void loadExperiment()
    }
  }, [experimentState.status])

  const loadExperiment = useCallback(async () => {
    setExperimentState((prev) => ({ ...prev, status: "loading" }))
    try {
      const data = await api.getExperimentData()
      setExperimentState({
        status: "success",
        data,
        error: null,
        lastFetched: Date.now(),
      })
      return { status: "success" as const, data, error: null, lastFetched: Date.now() }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Unable to load experiment data"
      setExperimentState({
        status: "error",
        data: null,
        error: message,
        lastFetched: null,
      })
      return { status: "error" as const, data: null, error: message, lastFetched: null }
    }
  }, [api])

  const runHorizonSimulation = useCallback(async () => {
    uiDispatch({ type: "setSimulationRunning", payload: true })
    try {
      const result = await api.runFullHorizonSimulation()
      setSimulationResult(result)
      uiDispatch({ type: "setSimulationComplete", payload: true })
      uiDispatch({ type: "setSimulationRunning", payload: false })
      return result
    } catch (error) {
      uiDispatch({ type: "setSimulationRunning", payload: false })
      console.error("Horizon simulation failed:", error)
      throw error
    }
  }, [api])

  return {
    experimentState,
    loadExperiment,
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