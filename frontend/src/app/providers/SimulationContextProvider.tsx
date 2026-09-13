import { ReactNode, createContext, useContext, useState, useEffect } from "react"

export interface DispatchSimulationState {
  dispatchId: string | null
  isDispatched: boolean
  simulationResult: {
    id: string
    status: "committed" | "partial" | "failed"
    actualFlexibilityKw: number
    renewableAbsorptionKwh: number
    constraintViolations: string[]
    deadlineViolations: string[]
    reboundKwh: number
    deliveryRatio: number
    timestamp: string
  } | null
}

export interface SimulationContextType {
  isSimulationMode: boolean
  toggleSimulationMode: () => void
  dispatchState: DispatchSimulationState
  setDispatchId: (id: string | null) => void
  setDispatched: (value: boolean) => void
  setSimulationResult: (result: DispatchSimulationState["simulationResult"]) => void
  resetDispatchState: () => void
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined)

const DEFAULT_DISPATCH_STATE: DispatchSimulationState = {
  dispatchId: null,
  isDispatched: false,
  simulationResult: null,
}

export function SimulationContextProvider({ children }: { children: ReactNode }) {
  const [isSimulationMode, setIsSimulationMode] = useState(true)

  const [dispatchState, setDispatchState] = useState<DispatchSimulationState>(
    DEFAULT_DISPATCH_STATE
  )

  const toggleSimulationMode = () => {
    setIsSimulationMode((prev) => !prev)
  }

  const setDispatchId = (id: string | null) => {
    setDispatchState((prev) => ({ ...prev, dispatchId: id }))
  }

  const setDispatched = (value: boolean) => {
    setDispatchState((prev) => ({ ...prev, isDispatched: value }))
  }

  const setSimulationResult = (
    result: DispatchSimulationState["simulationResult"]
  ) => {
    setDispatchState((prev) => ({ ...prev, simulationResult: result }))
  }

  const resetDispatchState = () => {
    setDispatchState(DEFAULT_DISPATCH_STATE)
  }

  // Persist to localStorage
  useEffect(() => {
    const saved = localStorage.getItem("urjasarathi-simulation-mode")
    if (saved !== null) {
      setIsSimulationMode(saved === "true")
    }
  }, [])

  useEffect(() => {
    localStorage.setItem("urjasarathi-simulation-mode", String(isSimulationMode))
  }, [isSimulationMode])

  return (
    <SimulationContext.Provider
      value={{
        isSimulationMode,
        toggleSimulationMode,
        dispatchState,
        setDispatchId,
        setDispatched,
        setSimulationResult,
        resetDispatchState,
      }}
    >
      {children}
    </SimulationContext.Provider>
  )
}

export function useSimulationMode() {
  const context = useContext(SimulationContext)
  if (!context) {
    throw new Error("useSimulationMode must be used within a SimulationContextProvider")
  }
  return context
}
