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

async function createRealAdapter(): Promise<DataAdapter> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://localhost:8000"

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
        const dispatch = await fetchJson<import("../../data/types/domain/dispatch").DispatchData>("/dispatch")
        const runs = await fetchJson<Array<{ run_id: string; created_at: string; total_dispatched_kw: number; total_delivered_kw: number }>>("/runs")

        return {
          scenario: {
            id: dispatch.scenario.id,
            mode: import.meta.env.VITE_MOCK_MODE !== "false" ? "simulation" : "live"
          },
          simulationMode: import.meta.env.VITE_MOCK_MODE !== "false",
          systemSnapshot: {
            trustedFlexibilityKw: dispatch.flexibility.trustedKw
          },
          flexibilityState: dispatch.flexibility,
          nextDispatch: dispatch.recommendedDispatch,
          recentActivity: runs.map(r => ({
            id: r.run_id,
            type: "simulation",
            description: `Simulation run completed with ${r.total_delivered_kw} kW delivered`,
            timestamp: r.created_at
          }))
        }
      } catch (err) {
        if (import.meta.env.VITE_MOCK_MODE === "false") {
          throw err
        }
        return new MockOverviewAdapter().getOverviewData()
      }
    },
    async getFlexibilityResources() {
      try {
        return await fetchJson<import("../../data/types/domain").FlexibilityResource[]>("/resources")
      } catch (err) {
        if (import.meta.env.VITE_MOCK_MODE === "false") {
          throw err
        }
        return new MockResourcesAdapter().getFlexibilityResources()
      }
    },
    async runSimulation() {
      try {
        return await fetchJson<import("../../data/types/domain").SimulationResult>("/simulate", { method: "POST" })
      } catch {
        return new MockOverviewAdapter().runSimulation()
      }
    },
    async getDispatchData() {
      try {
        return await fetchJson<import("../../data/types/domain/dispatch").DispatchData>("/dispatch")
      } catch (err) {
        if (import.meta.env.VITE_MOCK_MODE === "false") {
          throw err
        }
        return new MockDispatchAdapter().getDispatchData()
      }
    },
    async getRuns() {
      try {
        const backendRuns = await fetchJson<Array<{ run_id: string; created_at: string; total_dispatched_kw: number; total_delivered_kw: number }>>("/runs")
        return backendRuns.map(run => ({
          id: run.run_id,
          timestamp: run.created_at,
          status: "COMPLETED"
        }))
      } catch {
        return new MockOverviewAdapter().getRuns()
      }
    },
    async getRun(id: string) {
      try {
        const run = await fetchJson<{ run_id: string; created_at: string; results: any }>(`/runs/${id}`)
        return {
          id: run.run_id,
          timestamp: run.created_at,
          status: "COMPLETED"
        }
      } catch {
        return new MockOverviewAdapter().getRun(id)
      }
    },
    async runFullSimulation() {
      try {
        return await fetchJson<import("../../data/types/domain").SimulationResult>("/simulate/full", { method: "POST" })
      } catch {
        return new MockOverviewAdapter().runFullSimulation()
      }
    },
    async runFullHorizonSimulation() {
      try {
        return await fetchJson<import("../../data/types/domain/experiment").HorizonSimulationResult>("/simulate/full", { method: "POST" })
      } catch {
        return new MockExperimentAdapter().runFullHorizonSimulation()
      }
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