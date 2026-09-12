import { BrowserRouter, useLocation } from "react-router-dom"
import { AppShell } from "../components/Shell/AppShell"
import { DataAdapterProvider } from "./providers/DataAdapterProvider"
import { SimulationContextProvider } from "./providers/SimulationContextProvider"
import { Router } from "./routes/Router"
import "../styles/global.css"

const defaultScenario = {
  id: "DR-2026-Q3-001",
  name: "GridFlex Peak Shaving Scenario",
  timeHorizon: 8,
  seed: 42,
  category: "demand_response",
  mode: "simulation" as const
}

const pageMap: Record<string, "overview" | "flexibility" | "dispatch" | "experiments"> = {
  "/overview": "overview",
  "/flexibility": "flexibility",
  "/dispatch": "dispatch",
  "/experiments": "experiments",
}

function AppShellWrapper() {
  const location = useLocation()
  const currentPage = pageMap[location.pathname] ?? "overview"

  return (
    <AppShell currentPage={currentPage} scenario={defaultScenario}>
      <Router />
    </AppShell>
  )
}

export function App() {
  return (
    <BrowserRouter>
      <DataAdapterProvider>
        <SimulationContextProvider>
          <AppShellWrapper />
        </SimulationContextProvider>
      </DataAdapterProvider>
    </BrowserRouter>
  )
}