import type { DispatchUIState } from "../../data/types/domain/dispatch"

export interface DispatchUIStateModel {
  selectedResourceId: string | null
  filterText: string
  filterType: string
  simulationRunning: boolean
  simulationComplete: boolean
}

export const initialDispatchUIState: DispatchUIStateModel = {
  selectedResourceId: null,
  filterText: "",
  filterType: "",
  simulationRunning: false,
  simulationComplete: false,
}

export function createDispatchUISlice() {
  let state = { ...initialDispatchUIState }

  return {
    getState() {
      return { ...state }
    },
    setSelectedResourceId(id: string | null) {
      state = { ...state, selectedResourceId: id }
    },
    setFilterText(text: string) {
      state = { ...state, filterText: text }
    },
    setFilterType(type: string) {
      state = { ...state, filterType: type }
    },
    setSimulationRunning(running: boolean) {
      state = { ...state, simulationRunning: running }
    },
    setSimulationComplete(complete: boolean) {
      state = { ...state, simulationComplete: complete }
    },
    reset() {
      state = { ...initialDispatchUIState }
    },
  }
}

export type DispatchUISlice = ReturnType<typeof createDispatchUISlice>