import type { DataAdapter } from "../types"
import type {
  FlexibilityResource,
  OverviewData,
  SimulationResult,
} from "../../types/domain"
import type { DispatchData } from "../../types/domain/dispatch"
import type {
  HorizonSimulationResult,
  ResourceStateTransition,
} from "../../types/domain/experiment"

interface BackendResource {
  id: string
  type: string
  location_id: string
  rated_power_kw: number
  earliest_start: string
  latest_end: string
  required_kwh: number
  minimum_kwh: number
  maximum_kwh: number
  minimum_duration: number
  maximum_duration: number
  deadline: string
  min_power: number
  max_power: number
  override_rate: number
  availability_rate: number
}

interface BackendTrustState {
  resource_id: string
  potential_kw: number
  expected_kw: number
  trusted_kw: number
  confidence: number
}

interface BackendDispatchRow {
  resource_id: string
  time_step: string
  power_kw: number
}

interface BackendActualRow {
  resource_id: string
  time_step: string
  delivered_kw: number
}

interface BackendStateRow {
  resource_id: string
  time_step: string
  state: string
}

export interface BackendEVRun {
  run_id?: string
  feeder_capacity_kw: number
  label: string
  release_status: string
  warning: string
  scenario: {
    scenario_id: string
    resources: BackendResource[]
    seeds: Record<string, number>
  }
  trust_states: BackendTrustState[]
  dispatch_plan: {
    status: string
    dispatch_plan: BackendDispatchRow[]
  }
  simulation: {
    actual_response: BackendActualRow[]
    resource_state_evolution: BackendStateRow[]
  }
  verification: {
    passed?: boolean
    violations?: string[]
    deadline_violations?: string[]
  }
}

interface BackendWaterHeaterRow extends BackendResource, BackendTrustState {
  dispatched_kw: number
  delivered_kw: number
  overcommitment_kw: number
}

interface BackendWaterHeaterRun {
  run_id?: string
  event_time: string
  feeder_capacity_kw: number
  total_potential_kw: number
  total_expected_kw: number
  total_trusted_kw: number
  total_dispatched_kw: number
  total_delivered_kw: number
  resources: BackendWaterHeaterRow[]
}

interface BackendPortfolio {
  mode: string
  deployment_allowed: boolean
  ev: BackendEVRun
  water_heater: BackendWaterHeaterRun
}

interface BackendRunSummary {
  run_id: string
  created_at: string
}

const REFERENCE_RENEWABLE = {
  opportunityWindow: "11:00-15:00",
  renewableKwh: 1250,
  confidence: 0.84,
  description:
    "Reference Ahmedabad solar opportunity used for the prototype display. Flexibility, dispatch, and delivery values below come from the running backend models.",
}

function sum(values: number[]) {
  return values.reduce((total, value) => total + value, 0)
}

function round(value: number, digits = 2) {
  const scale = 10 ** digits
  return Math.round(value * scale) / scale
}

function peakByTime<T>(rows: T[], time: (row: T) => string, value: (row: T) => number) {
  const totals = new Map<string, number>()
  rows.forEach((row) => totals.set(time(row), (totals.get(time(row)) ?? 0) + value(row)))
  return Math.max(0, ...totals.values())
}

function resourceState(value: string): FlexibilityResource["state"] {
  const normalized = value.toLowerCase()
  if (normalized === "dispatched" || normalized === "completed" || normalized === "unavailable") {
    return normalized
  }
  return "available"
}

function toResources(payload: BackendPortfolio): FlexibilityResource[] {
  const dispatchIds = new Set(payload.ev.dispatch_plan.dispatch_plan.map((row) => row.resource_id))
  const trusts = new Map(payload.ev.trust_states.map((row) => [row.resource_id, row]))
  const evResources = payload.ev.scenario.resources.map((resource): FlexibilityResource => {
    const trust = trusts.get(resource.id)
    if (!trust) throw new Error(`Backend omitted trust state for ${resource.id}`)
    return {
      ...resource,
      historical_response: resource.availability_rate,
      potential_kw: round(trust.potential_kw),
      expected_kw: round(trust.expected_kw),
      trusted_kw: round(trust.trusted_kw),
      confidence: round(trust.confidence, 3),
      state: dispatchIds.has(resource.id) ? "dispatched" : "available",
    }
  })

  const waterHeaters = payload.water_heater.resources.map((resource): FlexibilityResource => ({
    ...resource,
    id: resource.resource_id,
    potential_kw: round(resource.potential_kw),
    expected_kw: round(resource.expected_kw),
    trusted_kw: round(resource.trusted_kw),
    confidence: round(resource.confidence, 3),
    historical_response: resource.availability_rate,
    state: resourceState(resource.dispatched_kw > 0 ? "dispatched" : "available"),
  }))
  return [...evResources, ...waterHeaters]
}

function dispatchPeaks(rows: BackendDispatchRow[]) {
  const byResource = new Map<string, number>()
  rows.forEach((row) => byResource.set(row.resource_id, Math.max(byResource.get(row.resource_id) ?? 0, row.power_kw)))
  return byResource
}

function toDispatch(payload: BackendPortfolio): DispatchData {
  const resources = toResources(payload)
  const evResources = payload.ev.scenario.resources
  const peaks = dispatchPeaks(payload.ev.dispatch_plan.dispatch_plan)
  const dispatchRows = payload.ev.dispatch_plan.dispatch_plan
  const times = dispatchRows.map((row) => row.time_step).sort()
  const start = times[0] ?? payload.water_heater.event_time
  const end = times[times.length - 1] ?? payload.water_heater.event_time
  const potentialKw = sum(resources.map((row) => row.potential_kw))
  const expectedKw = sum(resources.map((row) => row.expected_kw))
  const trustedKw = sum(resources.map((row) => row.trusted_kw))
  const confidence = potentialKw > 0
    ? sum(resources.map((row) => row.confidence * row.potential_kw)) / potentialKw
    : 0

  return {
    scenario: {
      id: payload.ev.scenario.scenario_id,
      name: "UrjaSarathi EV + Water Heater Prototype",
      timeHorizon: new Set(times).size,
      seed: payload.ev.scenario.seeds.master ?? 42,
      category: "demand_response",
      mode: "simulation",
    },
    renewableOpportunity: REFERENCE_RENEWABLE,
    flexibility: {
      potentialKw: round(potentialKw),
      expectedKw: round(expectedKw),
      trustedKw: round(trustedKw),
      confidence: round(confidence, 3),
    },
    recommendedDispatch: {
      id: payload.ev.run_id ?? "current-ev-plan",
      timeWindow: `${start}/${end}`,
      resources: evResources.map((resource) => ({
        id: resource.id,
        name: `EV Charger ${resource.id.replace("ev-", "")}`,
        type: resource.type,
        dispatchedKw: round(peaks.get(resource.id) ?? 0),
        state: peaks.has(resource.id) ? "dispatched" : "available",
      })),
      totalDispatchedKw: round(peakByTime(dispatchRows, (row) => row.time_step, (row) => row.power_kw)),
      rationale: "The backend optimizer limits every EV instruction by trusted model output and the 15 kW feeder constraint. Water heaters run through their separate real model channel below.",
      status: payload.ev.dispatch_plan.status.toLowerCase(),
    },
    constraintCheck: {
      constraints: ["15 kW EV feeder capacity", "Per-resource trusted power", "Energy deadline"],
      violations: payload.ev.verification.violations ?? [],
      deadlineViolations: payload.ev.verification.deadline_violations ?? [],
      passed: payload.ev.verification.passed ?? false,
    },
  }
}

function toOverview(payload: BackendPortfolio): OverviewData {
  const dispatch = toDispatch(payload)
  const resources = toResources(payload)
  const gridHeadroom = Math.max(0, payload.water_heater.feeder_capacity_kw - dispatch.recommendedDispatch.totalDispatchedKw)
  const now = new Date().toISOString()
  return {
    scenario: dispatch.scenario,
    simulationMode: true,
    systemSnapshot: {
      renewableOpportunityKwh: REFERENCE_RENEWABLE.renewableKwh,
      trustedFlexibilityKw: dispatch.flexibility.trustedKw,
      gridHeadroomKw: round(gridHeadroom),
    },
    renewableOpportunity: REFERENCE_RENEWABLE,
    flexibilityState: dispatch.flexibility,
    nextDispatch: {
      ...dispatch.recommendedDispatch,
      resources: dispatch.recommendedDispatch.resources.map(({ id, name, dispatchedKw }) => ({ id, name, dispatchedKw })),
    },
    recentActivity: [
      {
        id: "backend-ev",
        type: "simulation",
        description: `${payload.ev.trust_states.length} EV trust states loaded from Candidate v2 and verified by the backend.`,
        timestamp: now,
      },
      {
        id: "backend-water-heater",
        type: "simulation",
        description: `${payload.water_heater.resources.length} water-heater estimates loaded from the saved prototype model.`,
        timestamp: payload.water_heater.event_time,
      },
      {
        id: "backend-portfolio",
        type: "verification",
        description: `${resources.length} flexible resources available across the two trained model channels.`,
        timestamp: now,
      },
    ],
  }
}

export function normalizeEVRun(payload: BackendEVRun): SimulationResult {
  const dispatched = payload.dispatch_plan.dispatch_plan
  const delivered = payload.simulation.actual_response
  const totalDispatched = sum(dispatched.map((row) => row.power_kw))
  const totalDelivered = sum(delivered.map((row) => row.delivered_kw))
  return {
    id: payload.run_id ?? `ev-run-${Date.now()}`,
    status: payload.verification.passed ? "committed" : "failed",
    actualFlexibilityKw: round(peakByTime(delivered, (row) => row.time_step, (row) => row.delivered_kw)),
    renewableAbsorptionKwh: round(totalDelivered * 0.25),
    constraintViolations: payload.verification.violations ?? [],
    deadlineViolations: payload.verification.deadline_violations ?? [],
    reboundKwh: 0,
    deliveryRatio: round(totalDispatched > 0 ? totalDelivered / totalDispatched : 0, 4),
    timestamp: new Date().toISOString(),
  }
}

function horizonState(value: string): ResourceStateTransition["state"] {
  const normalized = value.toUpperCase()
  if (normalized === "DISPATCHED" || normalized === "COMPLETED" || normalized === "UNAVAILABLE") {
    return normalized
  }
  return "AVAILABLE"
}

function toHorizon(payload: BackendEVRun): HorizonSimulationResult {
  const dispatchAt = new Map<string, BackendDispatchRow[]>()
  const deliveredAt = new Map<string, BackendActualRow[]>()
  const statesAt = new Map<string, BackendStateRow[]>()
  payload.dispatch_plan.dispatch_plan.forEach((row) => dispatchAt.set(row.time_step, [...(dispatchAt.get(row.time_step) ?? []), row]))
  payload.simulation.actual_response.forEach((row) => deliveredAt.set(row.time_step, [...(deliveredAt.get(row.time_step) ?? []), row]))
  payload.simulation.resource_state_evolution.forEach((row) => statesAt.set(row.time_step, [...(statesAt.get(row.time_step) ?? []), row]))
  const times = [...new Set([...dispatchAt.keys(), ...deliveredAt.keys(), ...statesAt.keys()])].sort()
  const trusted = new Map(payload.trust_states.map((row) => [row.resource_id, row]))

  const steps = times.map((time, index) => {
    const dispatched = dispatchAt.get(time) ?? []
    const delivered = deliveredAt.get(time) ?? []
    const deliveredByResource = new Map(delivered.map((row) => [row.resource_id, row.delivered_kw]))
    const dispatchedByResource = new Map(dispatched.map((row) => [row.resource_id, row.power_kw]))
    const stateByResource = new Map((statesAt.get(time) ?? []).map((row) => [row.resource_id, row.state]))
    const totalDispatchedKw = sum(dispatched.map((row) => row.power_kw))
    const totalDeliveredKw = sum(delivered.map((row) => row.delivered_kw))
    return {
      stepNumber: index + 1,
      timeLabel: new Date(time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      renewableKwh: 0,
      demandKwh: 0,
      feederCapacityKw: payload.feeder_capacity_kw,
      totalDispatchedKw: round(totalDispatchedKw),
      totalDeliveredKw: round(totalDeliveredKw),
      totalErrorKw: round(Math.abs(totalDispatchedKw - totalDeliveredKw)),
      resourceStates: payload.scenario.resources.map((resource) => ({
        resourceId: resource.id,
        state: horizonState(stateByResource.get(resource.id) ?? "AVAILABLE"),
        dispatchedKw: round(dispatchedByResource.get(resource.id) ?? 0),
        deliveredKw: round(deliveredByResource.get(resource.id) ?? 0),
      })),
    }
  })

  const deliveredByResource = new Map<string, number>()
  payload.simulation.actual_response.forEach((row) => deliveredByResource.set(row.resource_id, (deliveredByResource.get(row.resource_id) ?? 0) + row.delivered_kw))
  const dispatchedByResource = new Map<string, number>()
  payload.dispatch_plan.dispatch_plan.forEach((row) => dispatchedByResource.set(row.resource_id, (dispatchedByResource.get(row.resource_id) ?? 0) + row.power_kw))

  return {
    id: payload.run_id ?? `horizon-${Date.now()}`,
    feasibility: payload.dispatch_plan.status === "FEASIBLE" && payload.verification.passed ? "FEASIBLE" : "INFEASIBLE",
    feasibilityReason: payload.verification.passed
      ? "Backend optimizer and verifier accepted every EV dispatch instruction."
      : (payload.verification.violations ?? []).join("; "),
    steps,
    instructionMatrix: payload.scenario.resources.map((resource) => ({
      resourceId: resource.id,
      ratedPowerKw: resource.rated_power_kw,
      requiredEnergyKwh: resource.required_kwh,
      horizonState: steps[steps.length - 1]?.resourceStates.find((row) => row.resourceId === resource.id)?.state ?? "AVAILABLE",
      dispatchedKw: round(dispatchedByResource.get(resource.id) ?? 0),
      deliveredKw: round(deliveredByResource.get(resource.id) ?? 0),
    })),
    comparison: { baseline: null, trustAware: null },
    trustUpdates: [],
    runId: payload.run_id ?? "non-persisted-run",
    executionTimestamp: new Date().toISOString(),
    feederCapacityKw: payload.feeder_capacity_kw,
    totalTrustedKw: round(sum([...trusted.values()].map((row) => row.trusted_kw))),
    totalDispatchedKw: round(sum(steps.map((step) => step.totalDispatchedKw))),
    totalDeliveredKw: round(sum(steps.map((step) => step.totalDeliveredKw))),
    totalErrorKw: round(sum(steps.map((step) => step.totalErrorKw))),
  }
}

export function createApiDataAdapter(baseUrl = "/api"): DataAdapter {
  let portfolioPromise: Promise<BackendPortfolio> | undefined

  async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    })
    if (!response.ok) {
      const body = await response.json().catch(() => null) as { detail?: string } | null
      throw new Error(body?.detail ?? `Backend request failed (${response.status})`)
    }
    return response.json() as Promise<T>
  }

  function getPortfolio() {
    portfolioPromise ??= fetchJson<BackendPortfolio>("/portfolio")
    return portfolioPromise
  }

  function refreshPortfolio() {
    portfolioPromise = undefined
  }

  return {
    async getOverviewData() {
      return toOverview(await getPortfolio())
    },
    async getFlexibilityResources() {
      return toResources(await getPortfolio())
    },
    async getDispatchData() {
      return toDispatch(await getPortfolio())
    },
    async runSimulation() {
      const result = await fetchJson<BackendEVRun>("/simulate", { method: "POST" })
      refreshPortfolio()
      return normalizeEVRun(result)
    },
    async runFullSimulation() {
      const result = await fetchJson<BackendEVRun>("/simulate/full", { method: "POST" })
      refreshPortfolio()
      return normalizeEVRun(result)
    },
    async runFullHorizonSimulation() {
      const result = await fetchJson<BackendEVRun>("/simulate/full", { method: "POST" })
      refreshPortfolio()
      return toHorizon(result)
    },
    async getRuns() {
      const rows = await fetchJson<BackendRunSummary[]>("/runs")
      return rows.map((row) => ({ id: row.run_id, status: "completed", timestamp: row.created_at }))
    },
    async getRun(id: string) {
      const row = await fetchJson<BackendEVRun>(`/runs/${encodeURIComponent(id)}`)
      return { id: row.run_id ?? id, status: "completed", timestamp: new Date().toISOString() }
    },
  }
}
