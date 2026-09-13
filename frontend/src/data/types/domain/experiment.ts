export type FeasibilityStatus = "FEASIBLE" | "INFEASIBLE"

export interface HorizonStep {
  readonly stepNumber: number
  readonly timeLabel: string
  readonly renewableKwh: number
  readonly demandKwh: number
  readonly feederCapacityKw: number
  readonly totalDispatchedKw: number
  readonly totalDeliveredKw: number
  readonly totalErrorKw: number
  readonly resourceStates: ResourceStateTransition[]
}

export interface ResourceStateTransition {
  readonly resourceId: string
  readonly state: "DISPATCHED" | "AVAILABLE" | "COMPLETED" | "UNAVAILABLE"
  readonly dispatchedKw: number
  readonly deliveredKw: number
}

export interface InstructionMatrixEntry {
  readonly resourceId: string
  readonly ratedPowerKw: number
  readonly requiredEnergyKwh: number
  readonly horizonState: string
  readonly dispatchedKw: number
  readonly deliveredKw: number
}

export interface ExperimentComparison {
  readonly baseline: {
    flexibilityDeliveryErrorKw: number
    overcommitmentKw: number
    renewableAbsorptionKwh?: number
    constraintViolations: number
    deadlineViolations: number
    reboundKwh?: number
    committedFlexibilityKw?: number
    actualFlexibilityKw?: number
    actualCommittedReliability: number
  } | null
  readonly trustAware: {
    flexibilityDeliveryErrorKw: number
    overcommitmentKw: number
    renewableAbsorptionKwh?: number
    constraintViolations: number
    deadlineViolations: number
    reboundKwh?: number
    committedFlexibilityKw?: number
    actualFlexibilityKw?: number
    actualCommittedReliability: number
  } | null
}

export interface HorizonSimulationResult {
  readonly id: string
  readonly feasibility: FeasibilityStatus
  readonly feasibilityReason?: string
  readonly steps: HorizonStep[]
  readonly instructionMatrix: InstructionMatrixEntry[]
  readonly comparison: ExperimentComparison
  readonly trustUpdates: TrustUpdate[]
  readonly runId: string
  readonly executionTimestamp: string
  readonly feederCapacityKw?: number
  readonly totalTrustedKw?: number
  readonly totalDispatchedKw?: number
  readonly totalDeliveredKw?: number
  readonly totalErrorKw?: number
}

export interface TrustUpdate {
  readonly resourceId: string
  readonly before: {
    overrideRate: number
    availabilityRate: number
    confidence: number
  }
  readonly after: {
    overrideRate: number
    availabilityRate: number
    confidence: number
  }
  readonly observedResponse: number
}

export interface RunHistoryEntry {
  readonly id: string
  readonly timestamp: string
  readonly feederLimitKw: number
  readonly totalTrustedKw: number
  readonly totalDispatchedKw: number
  readonly totalDeliveredKw: number
}

export interface RunDetail {
  readonly id: string
  readonly runId: string
  readonly timestamp: string
  readonly executionTimestamp: string
  readonly feederCapacityKw: number
  readonly totalTrustedKw: number
  readonly totalDispatchedKw: number
  readonly totalDeliveredKw: number
  readonly totalErrorKw: number
  readonly peakAlignmentScore: number | null
  readonly solarAlignmentScore: number | null
  readonly threeEvResults: EvResult[]
  readonly scaleDownApplied: boolean
  readonly scaleDownReason?: string
  readonly rawResponse?: Record<string, unknown>
}

export interface EvResult {
  readonly resourceId: string
  readonly ratedPowerKw: number
  readonly availabilityRate: number
  readonly overrideRate: number
  readonly confidenceScore: number
  readonly potentialKw: number
  readonly expectedKw: number
  readonly trustedKw: number
  readonly dispatchedKw: number
  readonly deliveredKw: number
  readonly dispatchStatus: "SCALED_DOWN" | "OPTIMAL"
  readonly errorKw: number
  readonly peakAlignmentScore: number
}
