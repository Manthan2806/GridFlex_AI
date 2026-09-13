import type { DataAdapter } from "../../data/adapters/types"
import type { DispatchData } from "../../data/types/domain/dispatch"
import type { SimulationResult } from "../../data/types/domain"
import type { DispatchState } from "./types"

export class DispatchAPI {
  constructor(private adapter: DataAdapter) {}

  async getDispatchData(): Promise<DispatchData> {
    return this.adapter.getDispatchData()
  }

  async loadDispatch(): Promise<DispatchState> {
    try {
      const data = await this.adapter.getDispatchData()
      return {
        status: "success",
        data,
        error: null,
        lastFetched: Date.now(),
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Unable to load dispatch data"
      return {
        status: "error",
        data: null,
        error: message,
        lastFetched: null,
      }
    }
  }

  async runSimulation(): Promise<SimulationResult> {
    return this.adapter.runSimulation()
  }

  async runFullSimulation(): Promise<SimulationResult> {
    return this.adapter.runFullSimulation()
  }
}

export function createDispatchAPI(adapter: DataAdapter) {
  return new DispatchAPI(adapter)
}