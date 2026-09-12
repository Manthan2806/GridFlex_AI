import { ReactNode, createContext, useContext } from "react"
import { DataAdapter } from "../../data/adapters/types"
import { MockOverviewAdapter } from "../../data/adapters/mock/overview"
import { MockResourcesAdapter } from "../../data/adapters/mock/resources"

const isMockMode = import.meta.env.VITE_MOCK_MODE !== "false"

const mockDataAdapter: DataAdapter = {
  getOverviewData: () => {
    return Promise.resolve(new MockOverviewAdapter().getOverviewData())
  },
  getFlexibilityResources: () => {
    return Promise.resolve(new MockResourcesAdapter().getFlexibilityResources())
  }
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
