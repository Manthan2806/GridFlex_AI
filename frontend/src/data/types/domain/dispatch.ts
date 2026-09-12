export interface DispatchRenewableOpportunity {
  readonly opportunityWindow: string
  readonly renewableKwh: number
  readonly confidence: number
  readonly description: string
}

export interface DispatchFlexibilityState {
  readonly potentialKw: number
  readonly expectedKw: number
  readonly trustedKw: number
  readonly confidence: number
}

export interface DispatchResource {
  readonly id: string
  readonly name: string
  readonly type: string
  readonly dispatchedKw: number
  readonly state: string
}

export interface RecommendedDispatch {
  readonly id: string
  readonly timeWindow: string
  readonly resources: DispatchResource[]
  readonly totalDispatchedKw: number
  readonly rationale: string
  readonly status: string
}

export interface ConstraintCheckResult {
  readonly constraints: string[]
  readonly violations: string[]
  readonly deadlineViolations: string[]
  readonly passed: boolean
}

export interface DispatchData {
  readonly scenario: import("./overview").Scenario
  readonly renewableOpportunity: DispatchRenewableOpportunity
  readonly flexibility: DispatchFlexibilityState
  readonly recommendedDispatch: RecommendedDispatch
  readonly constraintCheck: ConstraintCheckResult
}

export type DispatchUIState =
  | "idle"
  | "loading"
  | "success"
  | "error"
  | "simulating"
  | "simulated"