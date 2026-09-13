import { useState } from "react"
import { useExperiments } from "../../features/experiments/useExperiments"
import { SectionHeader } from "../../components/Layout/SectionHeader"
import { MetricDisplay } from "../../components/Indicators/MetricDisplay"
import { CapacityBar } from "../../components/Visualization/CapacityBar"
import type { HorizonSimulationResult, HorizonStep, FeasibilityStatus } from "../../data/types/domain/experiment"
import { HorizonChart } from "../../components/Visualization/HorizonChart"

function FeasibilityBadge({ feasibility }: { feasibility: FeasibilityStatus }) {
  const isFeasible = feasibility === "FEASIBLE"
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.5rem 1rem",
        borderRadius: "0.375rem",
        fontWeight: "600",
        fontSize: "0.875rem",
        backgroundColor: isFeasible ? "var(--color-bg-success, #dcfce7)" : "var(--color-bg-error, #fee2e2)",
        color: isFeasible ? "var(--color-fg-success, #166534)" : "var(--color-fg-error, #991b1b)",
        border: `1px solid ${isFeasible ? "var(--color-border-success, #22c55e)" : "var(--color-border-error, #ef4444)"}`,
      }}
    >
      <span
        style={{
          width: "0.5rem",
          height: "0.5rem",
          borderRadius: "50%",
          backgroundColor: "currentColor",
          display: "inline-block",
        }}
      />
      {feasibility === "FEASIBLE" ? "FEASIBLE" : "INFEASIBLE"}
    </span>
  )
}

function StepVisualization({ step, feederCapacityKw }: { step: HorizonStep; feederCapacityKw: number }) {
  const utilizationPct = feederCapacityKw > 0 ? (step.totalDispatchedKw / feederCapacityKw) * 100 : 0
  const isOverCapacity = step.totalDispatchedKw > feederCapacityKw

  return (
    <div
      style={{
        border: "1px solid var(--color-border-secondary, #e5e7eb)",
        borderRadius: "0.5rem",
        padding: "0.75rem",
        backgroundColor: "var(--color-bg-card, #ffffff)",
        boxShadow: "var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.05))",
      }}
    >
      <div style={{ fontSize: "0.75rem", fontWeight: "600", color: "var(--color-fg-muted, #6b7280)", marginBottom: "0.5rem" }}>
        Step {step.stepNumber}: {step.timeLabel}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem", fontSize: "0.75rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Renewable: {step.renewableKwh} kWh</span>
          <span>Demand: {step.demandKwh} kWh</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Dispatched: {step.totalDispatchedKw} kW</span>
          <span>Delivered: {step.totalDeliveredKw} kW</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Error: {step.totalErrorKw} kW</span>
          <span>Feeder Cap: {step.feederCapacityKw} kW</span>
        </div>
        <div style={{ marginTop: "0.25rem" }}>
          <CapacityBar
            value={step.totalDispatchedKw}
            max={feederCapacityKw}
            label="Feeder Capacity Utilization"
            unit="kW"
            intent={isOverCapacity ? "primary" : "success"}
          />
        </div>
      </div>
    </div>
  )
}

function InstructionMatrix({ matrix }: { matrix: HorizonSimulationResult["instructionMatrix"] }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid var(--color-border-primary, #e5e7eb)" }}>
            <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Resource</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Rated Power (kW)</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Required Energy (kWh)</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Horizon State</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Dispatched (kW)</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Delivered (kW)</th>
          </tr>
        </thead>
        <tbody>
          {matrix.map((entry) => (
            <tr key={entry.resourceId} style={{ borderBottom: "1px solid var(--color-border-secondary, #f3f4f6)" }}>
              <td style={{ padding: "0.5rem", color: "var(--color-fg-secondary, #374151)" }}>
                <code style={{ fontSize: "0.75rem" }}>{entry.resourceId}</code>
              </td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{entry.ratedPowerKw}</td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{entry.requiredEnergyKwh}</td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{entry.horizonState}</td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{entry.dispatchedKw}</td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{entry.deliveredKw}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TrustUpdatesTable({ updates }: { updates: HorizonSimulationResult["trustUpdates"] }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid var(--color-border-primary, #e5e7eb)" }}>
            <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Resource</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Before Conf.</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>After Conf.</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Observed Response</th>
          </tr>
        </thead>
        <tbody>
          {updates.map((u) => (
            <tr key={u.resourceId} style={{ borderBottom: "1px solid var(--color-border-secondary, #f3f4f6)" }}>
              <td style={{ padding: "0.5rem", color: "var(--color-fg-secondary, #374151)" }}>
                <code style={{ fontSize: "0.75rem" }}>{u.resourceId}</code>
              </td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{(u.before.confidence * 100).toFixed(0)}%</td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{(u.after.confidence * 100).toFixed(0)}%</td>
              <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{u.observedResponse}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ExperimentComparison({ comparison }: { comparison: HorizonSimulationResult["comparison"] }) {
  const baseline = comparison.baseline
  const trustAware = comparison.trustAware

  const metrics = [
    { key: "flexibilityDeliveryErrorKw", label: "Delivery Error (kW)", baseline: baseline?.flexibilityDeliveryErrorKw, trustAware: trustAware?.flexibilityDeliveryErrorKw },
    { key: "overcommitmentKw", label: "Overcommitment (kW)", baseline: baseline?.overcommitmentKw, trustAware: trustAware?.overcommitmentKw },
    { key: "renewableAbsorptionKwh", label: "Renewable Absorption (kWh)", baseline: baseline?.renewableAbsorptionKwh, trustAware: trustAware?.renewableAbsorptionKwh },
    { key: "constraintViolations", label: "Constraint Violations", baseline: baseline?.constraintViolations, trustAware: trustAware?.constraintViolations },
    { key: "deadlineViolations", label: "Deadline Violations", baseline: baseline?.deadlineViolations, trustAware: trustAware?.deadlineViolations },
    { key: "reboundKwh", label: "Rebound (kWh)", baseline: baseline?.reboundKwh, trustAware: trustAware?.reboundKwh },
    { key: "committedFlexibilityKw", label: "Committed Flexibility (kW)", baseline: baseline?.committedFlexibilityKw, trustAware: trustAware?.committedFlexibilityKw },
    { key: "actualFlexibilityKw", label: "Actual Flexibility (kW)", baseline: baseline?.actualFlexibilityKw, trustAware: trustAware?.actualFlexibilityKw },
    { key: "actualCommittedReliability", label: "Committed Reliability", baseline: baseline?.actualCommittedReliability, trustAware: trustAware?.actualCommittedReliability, format: (v: number) => `${(v * 100).toFixed(0)}%` },
  ]

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid var(--color-border-primary, #e5e7eb)" }}>
            <th style={{ textAlign: "left", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Metric</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Baseline</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Trust-Aware</th>
            <th style={{ textAlign: "center", padding: "0.5rem", color: "var(--color-fg-muted, #6b7280)" }}>Delta</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => {
            const b = m.baseline ?? "—"
            const t = m.trustAware ?? "—"
            const delta = (m.baseline !== undefined && m.trustAware !== undefined) ? m.trustAware - m.baseline : undefined
            return (
              <tr key={m.key} style={{ borderBottom: "1px solid var(--color-border-secondary, #f3f4f6)" }}>
                <td style={{ padding: "0.5rem", color: "var(--color-fg-secondary, #374151)" }}>{m.label}</td>
                <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{typeof b === "number" ? (m.format ? m.format(b) : b.toFixed(2)) : b}</td>
                <td style={{ textAlign: "center", padding: "0.5rem", fontVariantNumeric: "tabular-nums" }}>{typeof t === "number" ? (m.format ? m.format(t) : t.toFixed(2)) : t}</td>
                <td style={{ textAlign: "center", padding: "0.5rem", color: delta !== undefined ? (delta < 0 ? "var(--color-fg-success, #166534)" : "var(--color-fg-error, #991b1b)") : "var(--color-fg-muted, #6b7280)", fontVariantNumeric: "tabular-nums" }}>
                  {delta !== undefined ? (delta < 0 ? "↓" : "↑") + " " + Math.abs(delta).toFixed(2) : "—"}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default function ExperimentsPage() {
  const { runHorizonSimulation, simulationResult, uiState } = useExperiments()
  const [activeTab, setActiveTab] = useState<"feasibility" | "horizon" | "comparison" | "trust">("feasibility")

  const tabs = [
    { key: "feasibility" as const, label: "Feasibility" },
    { key: "horizon" as const, label: "Horizon" },
    { key: "comparison" as const, label: "Comparison" },
    { key: "trust" as const, label: "Trust Updates" },
  ]

  return (
    <main className="page-page" style={{ maxWidth: "1200px", margin: "0 auto", padding: "1.5rem" }}>
      <SectionHeader title="Experiments" />

      <div style={{ marginBottom: "1.5rem" }}>
        <button
          onClick={() => void runHorizonSimulation()}
          disabled={uiState.simulationRunning}
          style={{
            padding: "0.625rem 1.25rem",
            borderRadius: "0.375rem",
            backgroundColor: uiState.simulationRunning ? "var(--color-bg-muted, #9ca3af)" : "var(--color-bg-primary, #3b82f6)",
            color: "white",
            border: "none",
            cursor: uiState.simulationRunning ? "not-allowed" : "pointer",
            fontSize: "0.875rem",
            fontWeight: "500",
          }}
        >
          {uiState.simulationRunning ? "Running Simulation..." : "Run Horizon Simulation (POST /simulate/full)"}
        </button>
      </div>

      {simulationResult && (
        <>
          <HorizonChart steps={simulationResult.steps} />
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
            <FeasibilityBadge feasibility={simulationResult.feasibility} />
            {simulationResult.feasibilityReason && (
              <span style={{ fontSize: "0.875rem", color: "var(--color-fg-secondary, #374151)" }}>
                {simulationResult.feasibilityReason}
              </span>
            )}
          </div>

          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", borderBottom: "1px solid var(--color-border-secondary, #e5e7eb)", paddingBottom: "0.5rem" }}>
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  padding: "0.5rem 1rem",
                  borderRadius: "0.375rem",
                  border: "none",
                  backgroundColor: activeTab === tab.key ? "var(--color-bg-primary, #3b82f6)" : "transparent",
                  color: activeTab === tab.key ? "white" : "var(--color-fg-secondary, #374151)",
                  cursor: "pointer",
                  fontSize: "0.875rem",
                  fontWeight: "500",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === "feasibility" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem" }}>
              <MetricDisplay label="Feeder Capacity (kW)" value={simulationResult.feederCapacityKw} />
              <MetricDisplay label="Total Trusted (kW)" value={simulationResult.totalTrustedKw} />
              <MetricDisplay label="Total Dispatched (kW)" value={simulationResult.totalDispatchedKw} />
              <MetricDisplay label="Total Delivered (kW)" value={simulationResult.totalDeliveredKw} />
              <MetricDisplay label="Total Error (kW)" value={simulationResult.totalErrorKw} />
              <MetricDisplay label="Steps" value={simulationResult.steps.length} />
            </div>
          )}

          {activeTab === "horizon" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {simulationResult.steps.map((step) => (
                <StepVisualization key={step.stepNumber} step={step} feederCapacityKw={simulationResult.feederCapacityKw} />
              ))}
            </div>
          )}

          {activeTab === "comparison" && (
            <ExperimentComparison comparison={simulationResult.comparison} />
          )}

          {activeTab === "trust" && (
            <TrustUpdatesTable updates={simulationResult.trustUpdates} />
          )}

          <div style={{ marginTop: "1.5rem" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: "600", marginBottom: "0.5rem", color: "var(--color-fg-primary, #111827)" }}>
              Instruction Matrix
            </h3>
            <InstructionMatrix matrix={simulationResult.instructionMatrix} />
          </div>
        </>
      )}
    </main>
  )
}
