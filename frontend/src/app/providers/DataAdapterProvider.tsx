import { ReactNode, createContext, useContext } from "react"
import { DataAdapter } from "../../data/adapters/types"
import { MockOverviewAdapter } from "../../data/adapters/mock/overview"
import { MockResourcesAdapter } from "../../data/adapters/mock/resources"
import { MockDispatchAdapter } from "../../data/adapters/mock/dispatch"

const isMockMode = import.meta.env.VITE_MOCK_MODE !== "false"

const mockDataAdapter: DataAdapter = {
  getOverviewData: () => {
    return Promise.resolve(new MockOverviewAdapter().getOverviewData())
  },
  getFlexibilityResources: () => {
    return Promise.resolve(new MockResourcesAdapter().getFlexibilityResources())
  },
  runSimulation: () => {
    return Promise.resolve(new MockOverviewAdapter().runSimulation())
  },
  getDispatchData: () => {
    return Promise.resolve(new MockDispatchAdapter().getDispatchData())
  },
}

export interface DataAdapterContextType {
  dataAdapter: DataAdapter
}

const DataAdapterContext = createContext<DataAdapterContextType | undefined>(undefined)

export function DataAdapterProvider({ children }: { children: ReactNode }) {
  const dataAdapter = isMockMode ? mockDataAdapter : null

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
