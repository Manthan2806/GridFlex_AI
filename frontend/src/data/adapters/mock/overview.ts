import type { DataAdapter } from "../types"
import type { OverviewData } from "../../types/domain"
import type { SimulationResult } from "../../types/domain"
import type { HorizonSimulationResult } from "../../types/domain/experiment"

const overviewData: OverviewData = {
  scenario: {
    id: "DR-2026-Q3-001",
    name: "UrjaSarathi Renewable Alignment Scenario",
    timeHorizon: 8,
    seed: 42,
    category: "demand_response",
    mode: "simulation",
  },
  simulationMode: true,
  systemSnapshot: {
    renewableOpportunityKwh: 1250,
    trustedFlexibilityKw: 143,
    gridHeadroomKw: 520,
  },
  renewableOpportunity: {
    opportunityWindow: "14:00-18:00",
    renewableKwh: 1250,
    confidence: 0.84,
    description:
      "Projected solar surplus during midday peak hours; flexible loads can absorb up to 1,250 kWh while maintaining grid stability.",
  },
  flexibilityState: {
    potentialKw: 195,
    expectedKw: 155,
    trustedKw: 143,
    confidence: 0.72,
  },
  nextDispatch: {
    id: "dispatch-2026-09-12-001",
    timeWindow: "2026-09-12T15:00:00Z/2026-09-12T17:00:00Z",
    resources: [
      {
        id: "ev-fleet-01",
        name: "EV Fleet Charger 01",
        dispatchedKw: 85,
      },
      {
        id: "wh-building-a",
        name: "Water Heater Bank A",
        dispatchedKw: 58,
      },
    ],
    totalDispatchedKw: 143,
    rationale:
      "Dispatch scheduled during solar surplus window to maximize renewable absorption and reduce grid peak load. Resources ranked by trust score and availability.",
    status: "recommendation_ready",
  },
  recentActivity: [
    {
      id: "activity-001",
      type: "dispatch",
      description:
        "Dispatch recommendation generated for EV Fleet Charger 01 at 120 kW.",
      timestamp: "2026-09-12T08:15:00Z",
    },
    {
      id: "activity-002",
      type: "simulation",
      description:
        "Scenario DR-2026-Q3-001 simulated with seed 42 across 8-minute horizon.",
      timestamp: "2026-09-12T08:30:00Z",
    },
    {
      id: "activity-003",
      type: "verification",
      description:
        "Water Heater Bank A telemetry verified; 85 kW capacity confirmed.",
      timestamp: "2026-09-12T08:45:00Z",
    },
    {
      id: "activity-004",
      type: "trust_update",
      description:
        "Water Heater Bank A trust estimate updated after the simulated response.",
      timestamp: "2026-09-12T09:00:00Z",
    },
    {
      id: "activity-005",
      type: "learning",
      description:
        "Model retrained on last 24 hours of response data; confidence improved by 3%.",
      timestamp: "2026-09-12T09:15:00Z",
    },
  ],
}

export class MockOverviewAdapter implements DataAdapter {
  async getOverviewData(): Promise<OverviewData> {
    return overviewData
  }

  async getFlexibilityResources(): Promise<never> {
    throw new Error("Overview adapter does not provide flexibility resources")
  }

  async runSimulation(): Promise<SimulationResult> {
    // Deterministic mock simulation result for F3 Dispatch
    // This represents the authoritative simulation outcome for the recommended dispatch
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

  async getRuns(): Promise<Array<{ id: string; status: string; timestamp: string }>> {
    return [
      { id: "run-2026-09-12-001", status: "completed", timestamp: "2026-09-12T08:30:00Z" },
    ]
  }

  async getRun(id: string): Promise<{ id: string; status: string; timestamp: string }> {
    return { id, status: "completed", timestamp: "2026-09-12T08:30:00Z" }
  }

  async runFullSimulation(): Promise<SimulationResult> {
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

  async runFullHorizonSimulation(): Promise<HorizonSimulationResult> {
    throw new Error("Overview adapter does not provide horizon simulation")
  }
}
