import type { DataAdapter } from "../types"
import type { Scenario } from "../../types/domain"
import type { SimulationResult } from "../../types/domain"
import { MockOverviewAdapter } from "./overview"

const dispatchData = {
  scenario: {
    id: "DR-2026-Q3-001",
    name: "UrjaSarathi Renewable Alignment Scenario",
    timeHorizon: 8,
    seed: 42,
    category: "demand_response",
    mode: "simulation" as const,
  },
  renewableOpportunity: {
    opportunityWindow: "14:00-18:00",
    renewableKwh: 1250,
    confidence: 0.84,
    description:
      "Projected solar surplus during midday peak hours; flexible loads can absorb up to 1,250 kWh while maintaining grid stability.",
  },
  flexibility: {
    potentialKw: 195,
    expectedKw: 155,
    trustedKw: 143,
    confidence: 0.72,
  },
  recommendedDispatch: {
    id: "dispatch-2026-09-12-001",
    timeWindow: "2026-09-12T15:00:00Z/2026-09-12T17:00:00Z",
    resources: [
      { id: "ev-fleet-01", name: "EV Fleet Charger 01", type: "ev", dispatchedKw: 85, state: "dispatched" },
      { id: "wh-building-a", name: "Water Heater Bank A", type: "water_heater", dispatchedKw: 58, state: "dispatched" },
    ],
    totalDispatchedKw: 143,
    rationale:
      "Dispatch scheduled during solar surplus window to maximize renewable absorption and reduce grid peak load. Resources ranked by trust score and availability.",
    status: "recommendation_ready",
  },
  constraintCheck: {
    constraints: ["Grid capacity limit", "Storage level threshold", "Deadline compliance"],
    violations: [],
    deadlineViolations: [],
    passed: true,
  },
}

export class MockDispatchAdapter implements DataAdapter {
  async getOverviewData() {
    return new MockOverviewAdapter().getOverviewData()
  }

  async getFlexibilityResources() {
    return new MockOverviewAdapter().getFlexibilityResources()
  }

  async runSimulation(): Promise<SimulationResult> {
    return {
      id: "sim-2026-09-12-001",
      status: "committed",
      actualFlexibilityKw: 143,
      renewableAbsorptionKwh: 1250,
      constraintViolations: [],
      deadlineViolations: [],
      reboundKwh: 0,
      deliveryRatio: 1,
      timestamp: "2026-09-12T08:30:00Z",
    }
  }

  getDispatchData() {
    return Promise.resolve(dispatchData)
  }
}
