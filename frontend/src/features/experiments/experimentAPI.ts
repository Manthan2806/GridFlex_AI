import type { DataAdapter } from "../../data/adapters/types"
import type { HorizonSimulationResult } from "../../data/types/domain/experiment"

export class ExperimentAPI {
  constructor(private adapter: DataAdapter) {}

  async getExperimentData(): Promise<HorizonSimulationResult> {
    return this.adapter.runFullHorizonSimulation()
  }

  async runFullHorizonSimulation(): Promise<HorizonSimulationResult> {
    return this.adapter.runFullHorizonSimulation()
  }
}

export function createExperimentAPI(adapter: DataAdapter) {
  return new ExperimentAPI(adapter)
}