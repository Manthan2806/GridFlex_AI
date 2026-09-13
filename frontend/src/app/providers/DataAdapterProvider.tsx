import { ReactNode, createContext, useContext } from "react"
import { DataAdapter } from "../../data/adapters/types"
import { MockOverviewAdapter } from "../../data/adapters/mock/overview"
import { MockResourcesAdapter } from "../../data/adapters/mock/resources"
import { MockDispatchAdapter } from "../../data/adapters/mock/dispatch"
import { MockExperimentAdapter } from "../../data/adapters/mock/experiment"
import { createApiDataAdapter } from "../../data/adapters/api/backend"

const isMockMode = import.meta.env.VITE_MOCK_MODE === "true"

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

const dataAdapter = isMockMode
  ? mockDataAdapter
  : createApiDataAdapter(import.meta.env.VITE_API_URL || "/api")

export interface DataAdapterContextType {
  dataAdapter: DataAdapter
}

const DataAdapterContext = createContext<DataAdapterContextType | undefined>(undefined)

export function DataAdapterProvider({ children }: { children: ReactNode }) {
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
