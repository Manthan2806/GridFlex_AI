import React from "react"
import { PrimaryNavigation } from "../Navigation/PrimaryNavigation"
import { ScenarioContext } from "../Scenario/ScenarioContext"
import { SimulationModeIndicator } from "../Indicators/SimulationModeIndicator"
import { SectionHeader } from "../Layout/SectionHeader"

export interface AppShellProps {
  currentPage: "overview" | "flexibility" | "dispatch" | "experiments"
  scenario: {
    id: string
    name: string
    timeHorizon: number
    seed: number
    category: string
    mode: "simulation" | "live"
  } | null
  children: React.ReactNode
  className?: string
}

const appShellStyles = {
  maxWidth: "1400px",
  margin: "0 auto",
  padding: "24px",
  background: "var(--color-secondary)",
  minHeight: "100vh",
}

const navRailStyles = {
  display: "flex",
  gap: "4px",
  background: "var(--color-primary)",
  padding: "8px 12px",
  borderRadius: "6px",
  minWidth: "280px",
}

const contentStyles = {
  flexGrow: 1,
  marginLeft: "24px",
}

export function AppShell({
  currentPage,
  scenario,
  children,
  className,
}: AppShellProps) {
  return (
    <div
      style={appShellStyles}
      className={className}
    >
      <nav style={navRailStyles}>
        <PrimaryNavigation activePage={currentPage} />
      </nav>

      <main style={contentStyles}>
        {scenario ? (
          <ScenarioContext scenario={scenario} />
        ) : null}

        <SectionHeader title={currentPage} />

        {children}

        <SimulationModeIndicator />
      </main>
    </div>
  )
}