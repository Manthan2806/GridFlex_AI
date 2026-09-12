import { useCallback, useEffect, useMemo, useState } from "react"
import { useDataAdapter } from "../../app/providers/DataAdapterProvider"
import { DispatchAPI } from "./dispatchAPI"
import type { DispatchData } from "../../data/types/domain/dispatch"
import type { SimulationResult } from "../../data/types/domain"
import type { DispatchState } from "./types"
import { createDispatchUISlice } from "./dispatchSlice"

export function useDispatch() {
  const adapter = useDataAdapter()
  const api = useMemo(() => new DispatchAPI(adapter), [adapter])
  const [dispatchState, setDispatchState] = useState<DispatchState>({
    status: "idle",
    data: null,
    error: null,
    lastFetched: null,
  })
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null)
  const uiSlice = useMemo(() => createDispatchUISlice(), [])

  useEffect(() => {
    if (dispatchState.status === "idle") {
      void loadDispatch()
    }
  }, [dispatchState.status]) // eslint-disable-line react-hooks/exhaustive-deps

  const loadDispatch = useCallback(async () => {
    setDispatchState((prev) => ({ ...prev, status: "loading" }))
    try {
      const data = await api.getDispatchData()
      setDispatchState({
        status: "success",
        data,
        error: null,
        lastFetched: Date.now(),
      })
      return { status: "success" as const, data, error: null, lastFetched: Date.now() }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Unable to load dispatch data"
      setDispatchState({
        status: "error",
        data: null,
        error: message,
        lastFetched: null,
      })
      return { status: "error" as const, data: null, error: message, lastFetched: null }
    }
  }, [api])

  const runSimulation = useCallback(async () => {
    const result = await api.runSimulation()
    setSimulationResult(result)
    return result
  }, [api])

  return {
    dispatchState,
    loadDispatch,
    runSimulation,
    simulationResult,
    uiSlice,
  }
}