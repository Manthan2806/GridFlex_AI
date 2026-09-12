import type { HorizonSimulationResult } from "../../data/types/domain/experiment"

export interface ExperimentState {
  status: "idle" | "loading" | "success" | "error"
  data: HorizonSimulationResult | null
  error: string | null
  lastFetched: number | null
}