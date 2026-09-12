import type { DataAdapter } from "../types"
import type { OverviewData } from "../../types/domain"

const overviewData: OverviewData = {
  scenario: {
    id: "DR-2026-Q3-001",
    name: "GridFlex Peak Shaving Scenario",
    timeHorizon: 8,
    seed: 42,
    category: "demand_response",
    mode: "simulation",
  },
  simulationMode: true,
  systemSnapshot: {
    renewableOpportunityKwh: 1250,
    trustedFlexibilityKw: 385,
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
    potentialKw: 520,
    expectedKw: 440,
    trustedKw: 385,
    confidence: 0.72,
  },
  nextDispatch: {
    id: "dispatch-2026-09-12-001",
    timeWindow: "2026-09-12T15:00:00Z/2026-09-12T17:00:00Z",
    resources: [
      {
        id: "ev-fleet-01",
        name: "EV Fleet Charger 01",
        dispatchedKw: 120,
      },
      {
        id: "wh-building-a",
        name: "Water Heater Bank A",
        dispatchedKw: 85,
      },
      {
        id: "industrial-batch-02",
        name: "Industrial Batch 02",
        dispatchedKw: 180,
      },
    ],
    totalDispatchedKw: 385,
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
        "Scenario DR-2026-Q3-001 simulated with seed 42 across 8-hour horizon.",
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
        "Industrial Batch 02 trust score updated to 0.91 following successful dispatch.",
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
}
