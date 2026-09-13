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

export type DispatchUIAction =
  | { type: "setSelectedResourceId"; payload: string | null }
  | { type: "setFilterText"; payload: string }
  | { type: "setFilterType"; payload: string }
  | { type: "setSimulationRunning"; payload: boolean }
  | { type: "setSimulationComplete"; payload: boolean }
  | { type: "reset" }

export function dispatchReducer(state: DispatchUIStateModel, action: DispatchUIAction) {
  switch (action.type) {
    case "setSelectedResourceId":
      return { ...state, selectedResourceId: action.payload }
    case "setFilterText":
      return { ...state, filterText: action.payload }
    case "setFilterType":
      return { ...state, filterType: action.payload }
    case "setSimulationRunning":
      return { ...state, simulationRunning: action.payload }
    case "setSimulationComplete":
      return { ...state, simulationComplete: action.payload }
    case "reset":
      return { ...initialDispatchUIState }
    default:
      return state
  }
}