export interface Scenario {
  readonly id: string
  readonly name: string
  readonly timeHorizon: number
  readonly seed: number
  readonly category: string
  readonly mode: "simulation" | "live"
}

export interface SystemSnapshot {
  readonly renewableOpportunityKwh: number
  readonly trustedFlexibilityKw: number
  readonly gridHeadroomKw: number
}

export interface RenewableOpportunity {
  readonly opportunityWindow: string
  readonly renewableKwh: number
  readonly confidence: number
  readonly description: string
}

export interface FlexibilityState {
  readonly potentialKw: number
  readonly expectedKw: number
  readonly trustedKw: number
  readonly confidence: number
}

export interface NextDispatchResource {
  readonly id: string
  readonly name: string
  readonly dispatchedKw: number
}

export interface NextDispatch {
  readonly id: string
  readonly timeWindow: string
  readonly resources: NextDispatchResource[]
  readonly totalDispatchedKw: number
  readonly rationale: string
  readonly status: string
}

export interface RecentActivity {
  readonly id: string
  readonly type: string
  readonly description: string
  readonly timestamp: string
}

export interface SimulationResult {
  readonly id: string
  readonly status: "committed" | "partial" | "failed"
  readonly actualFlexibilityKw: number
  readonly renewableAbsorptionKwh: number
  readonly constraintViolations: string[]
  readonly deadlineViolations: string[]
  readonly reboundKwh: number
  readonly deliveryRatio: number
  readonly timestamp: string
}

export interface OverviewData {
  readonly scenario: Scenario
  readonly simulationMode: boolean
  readonly systemSnapshot: SystemSnapshot
  readonly renewableOpportunity: RenewableOpportunity
  readonly flexibilityState: FlexibilityState
  readonly nextDispatch: NextDispatch
  readonly recentActivity: RecentActivity[]
}