import type { HorizonSimulationResult } from "../../types/domain/experiment"
import { MockOverviewAdapter } from "./overview"
import { MockDispatchAdapter } from "./dispatch"

const mockExperimentData: HorizonSimulationResult = {
  id: "sim-experiment-2026-09-12-001",
  feasibility: "FEASIBLE",
  feasibilityReason: "All horizon steps respect feeder capacity constraints and resource availability schedules.",
  steps: [
    {
      stepNumber: 1,
      timeLabel: "14:00 - 15:00",
      renewableKwh: 125,
      demandKwh: 110,
      feederCapacityKw: 200,
      totalDispatchedKw: 180,
      totalDeliveredKw: 175,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 80, deliveredKw: 78 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 50, deliveredKw: 48 },
      ],
    },
    {
      stepNumber: 2,
      timeLabel: "15:00 - 16:00",
      renewableKwh: 110,
      demandKwh: 130,
      feederCapacityKw: 200,
      totalDispatchedKw: 170,
      totalDeliveredKw: 165,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 80, deliveredKw: 78 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 3,
      timeLabel: "16:00 - 17:00",
      renewableKwh: 95,
      demandKwh: 145,
      feederCapacityKw: 200,
      totalDispatchedKw: 160,
      totalDeliveredKw: 155,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 70, deliveredKw: 68 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 4,
      timeLabel: "17:00 - 18:00",
      renewableKwh: 80,
      demandKwh: 160,
      feederCapacityKw: 200,
      totalDispatchedKw: 150,
      totalDeliveredKw: 145,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 60, deliveredKw: 58 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 5,
      timeLabel: "18:00 - 19:00",
      renewableKwh: 65,
      demandKwh: 175,
      feederCapacityKw: 200,
      totalDispatchedKw: 140,
      totalDeliveredKw: 135,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 50, deliveredKw: 48 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 6,
      timeLabel: "19:00 - 20:00",
      renewableKwh: 50,
      demandKwh: 185,
      feederCapacityKw: 200,
      totalDispatchedKw: 130,
      totalDeliveredKw: 125,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 7,
      timeLabel: "20:00 - 21:00",
      renewableKwh: 35,
      demandKwh: 195,
      feederCapacityKw: 200,
      totalDispatchedKw: 120,
      totalDeliveredKw: 115,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 30, deliveredKw: 29 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 8,
      timeLabel: "21:00 - 22:00",
      renewableKwh: 20,
      demandKwh: 210,
      feederCapacityKw: 200,
      totalDispatchedKw: 110,
      totalDeliveredKw: 105,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 20, deliveredKw: 19 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 9,
      timeLabel: "22:00 - 23:00",
      renewableKwh: 10,
      demandKwh: 200,
      feederCapacityKw: 200,
      totalDispatchedKw: 100,
      totalDeliveredKw: 95,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 10, deliveredKw: 9 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 10,
      timeLabel: "23:00 - 00:00",
      renewableKwh: 5,
      demandKwh: 195,
      feederCapacityKw: 200,
      totalDispatchedKw: 90,
      totalDeliveredKw: 85,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 5, deliveredKw: 5 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 11,
      timeLabel: "00:00 - 01:00",
      renewableKwh: 2,
      demandKwh: 180,
      feederCapacityKw: 200,
      totalDispatchedKw: 80,
      totalDeliveredKw: 75,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 2, deliveredKw: 2 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 40, deliveredKw: 38 },
      ],
    },
    {
      stepNumber: 12,
      timeLabel: "01:00 - 02:00",
      renewableKwh: 1,
      demandKwh: 165,
      feederCapacityKw: 200,
      totalDispatchedKw: 70,
      totalDeliveredKw: 65,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 1, deliveredKw: 1 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 35, deliveredKw: 33 },
      ],
    },
    {
      stepNumber: 13,
      timeLabel: "02:00 - 03:00",
      renewableKwh: 0,
      demandKwh: 150,
      feederCapacityKw: 200,
      totalDispatchedKw: 60,
      totalDeliveredKw: 55,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "DISPATCHED", dispatchedKw: 0, deliveredKw: 0 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 30, deliveredKw: 28 },
      ],
    },
    {
      stepNumber: 14,
      timeLabel: "03:00 - 04:00",
      renewableKwh: 0,
      demandKwh: 135,
      feederCapacityKw: 200,
      totalDispatchedKw: 50,
      totalDeliveredKw: 45,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "AVAILABLE", dispatchedKw: 0, deliveredKw: 0 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 25, deliveredKw: 23 },
      ],
    },
    {
      stepNumber: 15,
      timeLabel: "04:00 - 05:00",
      renewableKwh: 0,
      demandKwh: 120,
      feederCapacityKw: 200,
      totalDispatchedKw: 40,
      totalDeliveredKw: 35,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "AVAILABLE", dispatchedKw: 0, deliveredKw: 0 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 20, deliveredKw: 18 },
      ],
    },
    {
      stepNumber: 16,
      timeLabel: "05:00 - 06:00",
      renewableKwh: 0,
      demandKwh: 105,
      feederCapacityKw: 200,
      totalDispatchedKw: 30,
      totalDeliveredKw: 25,
      totalErrorKw: 5,
      resourceStates: [
        { resourceId: "ev-fleet-01", state: "COMPLETED", dispatchedKw: 0, deliveredKw: 0 },
        { resourceId: "wh-building-a", state: "DISPATCHED", dispatchedKw: 15, deliveredKw: 13 },
      ],
    },
  ],
  instructionMatrix: [
    {
      resourceId: "ev-fleet-01",
      ratedPowerKw: 150,
      requiredEnergyKwh: 800,
      horizonState: "DISPATCHED",
      dispatchedKw: 510,
      deliveredKw: 489,
    },
    {
      resourceId: "wh-building-a",
      ratedPowerKw: 120,
      requiredEnergyKwh: 600,
      horizonState: "DISPATCHED",
      dispatchedKw: 530,
      deliveredKw: 507,
    },
  ],
  comparison: {
    baseline: {
      flexibilityDeliveryErrorKw: 18.5,
      overcommitmentKw: 22.3,
      renewableAbsorptionKwh: 1120,
      constraintViolations: 3,
      deadlineViolations: 2,
      reboundKwh: 45,
      committedFlexibilityKw: 385,
      actualFlexibilityKw: 366,
      actualCommittedReliability: 0.92,
    } as const,
    trustAware: {
      flexibilityDeliveryErrorKw: 9.2,
      overcommitmentKw: 11.1,
      renewableAbsorptionKwh: 1195,
      constraintViolations: 1,
      deadlineViolations: 0,
      reboundKwh: 23,
      committedFlexibilityKw: 385,
      actualFlexibilityKw: 376,
      actualCommittedReliability: 0.97,
    } as const,
  } as const,
  trustUpdates: [
    {
      resourceId: "ev-fleet-01",
      before: { overrideRate: 0.12, availabilityRate: 0.88, confidence: 0.71 },
      after: { overrideRate: 0.07, availabilityRate: 0.93, confidence: 0.84 },
      observedResponse: 42,
    },
    {
      resourceId: "wh-building-a",
      before: { overrideRate: 0.15, availabilityRate: 0.85, confidence: 0.68 },
      after: { overrideRate: 0.08, availabilityRate: 0.92, confidence: 0.81 },
      observedResponse: 38,
    },
  ],
  runId: "run-experiment-2026-09-12-001",
  executionTimestamp: "2026-09-12T08:30:00Z",
  feederCapacityKw: 200,
  totalTrustedKw: 385,
  totalDispatchedKw: 5100,
  totalDeliveredKw: 4890,
  totalErrorKw: 80,
}

function normalizeExperimentTotals(data: HorizonSimulationResult): HorizonSimulationResult {
  const steps = data.steps.map((step) => {
    const resourceStates = step.resourceStates
    const totalDispatchedKw = resourceStates.reduce((sum, row) => sum + row.dispatchedKw, 0)
    const totalDeliveredKw = resourceStates.reduce((sum, row) => sum + row.deliveredKw, 0)
    return {
      ...step,
      resourceStates,
      totalDispatchedKw,
      totalDeliveredKw,
      totalErrorKw: Math.max(0, totalDispatchedKw - totalDeliveredKw),
    }
  })
  return {
    ...data,
    steps,
    instructionMatrix: data.instructionMatrix,
    trustUpdates: data.trustUpdates,
    totalTrustedKw: 143,
    totalDispatchedKw: steps.reduce((sum, step) => sum + step.totalDispatchedKw, 0),
    totalDeliveredKw: steps.reduce((sum, step) => sum + step.totalDeliveredKw, 0),
    totalErrorKw: steps.reduce((sum, step) => sum + step.totalErrorKw, 0),
  }
}

export class MockExperimentAdapter {
  async getOverviewData() {
    return new MockOverviewAdapter().getOverviewData()
  }

  async runFullHorizonSimulation(): Promise<HorizonSimulationResult> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(normalizeExperimentTotals(mockExperimentData))
      }, 800)
    })
  }

  async runSimulation(): Promise<{ status: string; id: string }> {
    return {
      status: "committed",
      id: "sim-2026-09-12-001",
    }
  }

  getDispatchData() {
    return new MockDispatchAdapter().getDispatchData()
  }
}
