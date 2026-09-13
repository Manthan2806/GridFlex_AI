import { ReactNode, createContext, useContext, useEffect, useState } from "react"
import { DataAdapter } from "../../data/adapters/types"
import { MockOverviewAdapter } from "../../data/adapters/mock/overview"
import { MockResourcesAdapter } from "../../data/adapters/mock/resources"
import { MockDispatchAdapter } from "../../data/adapters/mock/dispatch"
import { MockExperimentAdapter } from "../../data/adapters/mock/experiment"

const isMockMode = import.meta.env.VITE_MOCK_MODE !== "false"

const mockDataAdapter: DataAdapter = {
  getOverviewData: () => Promise.resolve(new MockOverviewAdapter().getOverviewData()),
  getFlexibilityResources: () => Promise.resolve(new MockResourcesAdapter().getFlexibilityResources()),
  runSimulation: () => Promise.resolve(new MockOverviewAdapter().runSimulation()),
  getDispatchData: () => Promise.resolve(new MockDispatchAdapter().getDispatchData()),
  getRuns: () => Promise.resolve(new MockOverviewAdapter().getRuns()),
  getRun: (id: string) => Promise.resolve(new MockOverviewAdapter().getRun(id)),
  runFullSimulation: () => Promise.resolve(new MockOverviewAdapter().runFullSimulation()),
  runFullHorizonSimulation: () => Promise.resolve(new MockExperimentAdapter().runFullHorizonSimulation()),
}

interface EVBackendRun {
  run_id?: string
  dispatch_plan?: { dispatch_plan?: Array<{ time_step: string; power_kw: number }> }
  simulation?: { actual_response?: Array<{ time_step: string; delivered_kw: number }> }
  verification?: { passed?: boolean; violations?: string[]; deadline_violations?: string[] }
}

function normalizeEVRun(payload: EVBackendRun): import("../../data/types/domain").SimulationResult {
  const dispatched = payload.dispatch_plan?.dispatch_plan ?? []
  const delivered = payload.simulation?.actual_response ?? []
  const totalDispatched = dispatched.reduce((sum, row) => sum + row.power_kw, 0)
  const totalDelivered = delivered.reduce((sum, row) => sum + row.delivered_kw, 0)
  const peakByTime = new Map<string, number>()
  for (const row of delivered) peakByTime.set(row.time_step, (peakByTime.get(row.time_step) ?? 0) + row.delivered_kw)

  return {
    id: payload.run_id ?? `ev-run-${Date.now()}`,
    status: payload.verification?.passed ? "committed" : "failed",
    actualFlexibilityKw: Math.max(0, ...peakByTime.values()),
    renewableAbsorptionKwh: totalDelivered * 0.25,
    constraintViolations: payload.verification?.violations ?? [],
    deadlineViolations: payload.verification?.deadline_violations ?? [],
    reboundKwh: 0,
    deliveryRatio: totalDispatched > 0 ? totalDelivered / totalDispatched : 0,
    timestamp: new Date().toISOString(),
  }
}

async function createRealAdapter(): Promise<DataAdapter> {
  const baseUrl = import.meta.env.VITE_API_URL || "/api"

  async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${baseUrl}${url}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    })
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`)
    }
    return res.json()
  }

  return {
    async getOverviewData() {
      try {
        return await fetchJson<import("../../data/types/domain").OverviewData>("/overview")
      } catch {
        return new MockOverviewAdapter().getOverviewData()
      }
    },
    async getFlexibilityResources() {
      try {
        return await fetchJson<import("../../data/types/domain").FlexibilityResource[]>("/resources")
      } catch {
        return new MockResourcesAdapter().getFlexibilityResources()
      }
    },
    async runSimulation() {
      return normalizeEVRun(await fetchJson<EVBackendRun>("/simulate", { method: "POST" }))
    },
    async getDispatchData() {
      try {
        return await fetchJson<import("../../data/types/domain/dispatch").DispatchData>("/dispatch")
      } catch {
        return new MockDispatchAdapter().getDispatchData()
      }
    },
    async getRuns() {
      try {
        return await fetchJson<Array<{ id: string; status: string; timestamp: string }>>("/runs")
      } catch {
        return new MockOverviewAdapter().getRuns()
      }
    },
    async getRun(id: string) {
      try {
        return await fetchJson<{ id: string; status: string; timestamp: string }>(`/runs/${id}`)
      } catch {
        return new MockOverviewAdapter().getRun(id)
      }
    },
    async runFullSimulation() {
      return normalizeEVRun(await fetchJson<EVBackendRun>("/simulate/full", { method: "POST" }))
    },
    async runFullHorizonSimulation() {
      return new MockExperimentAdapter().runFullHorizonSimulation()
    },
  }
}

export interface DataAdapterContextType {
  dataAdapter: DataAdapter
}

const DataAdapterContext = createContext<DataAdapterContextType | undefined>(undefined)

export function DataAdapterProvider({ children }: { children: ReactNode }) {
  const [dataAdapter, setDataAdapter] = useState<DataAdapter>(mockDataAdapter)

  useEffect(() => {
    if (isMockMode) {
      setDataAdapter(mockDataAdapter)
    } else {
      createRealAdapter().then(setDataAdapter).catch(() => setDataAdapter(mockDataAdapter))
    }
  }, [])

  return (
    <DataAdapterContext.Provider value={{ dataAdapter }}>
      {children}
    </DataAdapterContext.Provider>
  )
}

export function useDataAdapter() {
  const context = useContext(DataAdapterContext)
  if (!context) {
    throw new Error("useDataAdapter must be used within a DataAdapterProvider")
  }
  return context.dataAdapter
}
