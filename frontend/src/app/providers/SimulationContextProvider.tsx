import { ReactNode, createContext, useContext, useState, useEffect } from "react"

export interface SimulationContextType {
  isSimulationMode: boolean
  toggleSimulationMode: () => void
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined)

export function SimulationContextProvider({ children }: { children: ReactNode }) {
  const [isSimulationMode, setIsSimulationMode] = useState(true)

  const toggleSimulationMode = () => {
    setIsSimulationMode(prev => !prev)
  }

  // Persist to localStorage
  useEffect(() => {
    const saved = localStorage.getItem("gridflex-simulation-mode")
    if (saved !== null) {
      setIsSimulationMode(saved === "true")
    }
  }, [])

  useEffect(() => {
    localStorage.setItem("gridflex-simulation-mode", String(isSimulationMode))
  }, [isSimulationMode])

  return (
    <SimulationContext.Provider value={{ isSimulationMode, toggleSimulationMode }}>
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