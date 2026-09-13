import type {
  FlexibilityResource,
  OverviewData,
  SimulationResult,
} from "../types/domain"
import type { DispatchData } from "../types/domain/dispatch"
import type { HorizonSimulationResult } from "../types/domain/experiment"

export interface DataAdapter {
  getOverviewData(): Promise<OverviewData>
  getFlexibilityResources(): Promise<FlexibilityResource[]>
  runSimulation(): Promise<SimulationResult>
  getDispatchData(): Promise<DispatchData>
  getRuns(): Promise<Array<{ id: string; status: string; timestamp: string }>>
  getRun(id: string): Promise<{ id: string; status: string; timestamp: string }>
  runFullSimulation(): Promise<SimulationResult>
  runFullHorizonSimulation(): Promise<HorizonSimulationResult>
}