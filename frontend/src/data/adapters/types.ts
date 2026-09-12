import type {
  FlexibilityResource,
  OverviewData,
} from "../types/domain"

export interface DataAdapter {
  getOverviewData(): Promise<OverviewData>
  getFlexibilityResources(): Promise<FlexibilityResource[]>
}