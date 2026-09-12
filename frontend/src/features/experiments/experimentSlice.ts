export interface ExperimentUIState {
  simulationRunning: boolean
  simulationComplete: boolean
  selectedStep: number | null
  activeTab: "feasibility" | "horizon" | "comparison" | "trust"
}

export const initialExperimentUIState: ExperimentUIState = {
  simulationRunning: false,
  simulationComplete: false,
  selectedStep: null,
  activeTab: "feasibility",
}

export type ExperimentUIReducerAction =
  | { type: "setSimulationRunning"; payload: boolean }
  | { type: "setSimulationComplete"; payload: boolean }
  | { type: "setSelectedStep"; payload: number | null }
  | { type: "setActiveTab"; payload: ExperimentUIState["activeTab"] }

export function experimentReducer(
  state: ExperimentUIState,
  action: ExperimentUIReducerAction,
): ExperimentUIState {
  switch (action.type) {
    case "setSimulationRunning":
      return { ...state, simulationRunning: action.payload }
    case "setSimulationComplete":
      return { ...state, simulationComplete: action.payload }
    case "setSelectedStep":
      return { ...state, selectedStep: action.payload }
    case "setActiveTab":
      return { ...state, activeTab: action.payload }
    default:
      return state
  }
}