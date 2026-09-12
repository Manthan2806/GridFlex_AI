import type {
  FlexibilityResource,
  OverviewData,
  SimulationResult,
} from "../types/domain"
import type { DispatchData } from "../types/domain/dispatch"

export interface DataAdapter {
  getOverviewData(): Promise<OverviewData>
  getFlexibilityResources(): Promise<FlexibilityResource[]>
  runSimulation(): Promise<SimulationResult>
  getDispatchData(): Promise<DispatchData>
}