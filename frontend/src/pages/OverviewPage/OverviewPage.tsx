import { useEffect, useState } from "react"
import { useDataAdapter } from "../../app/providers/DataAdapterProvider"
import { useSimulationMode } from "../../app/providers/SimulationContextProvider"
import { CapacityBar } from "../../components/Visualization/CapacityBar"
import { MetricDisplay } from "../../components/Indicators/MetricDisplay"
import { PageHeader } from "../../components/Header/PageHeader"
import { SectionHeader } from "../../components/Layout/SectionHeader"
import { SimulationModeIndicator } from "../../components/Indicators/SimulationModeIndicator"
import { StateMessage } from "../../components/State/StateMessage"
import { Timeline } from "../../components/Visualization/Timeline"
import { OpportunityVis } from "../../components/Visualization/OpportunityVis"
import { FlexibilityChart } from "../../components/Visualization/FlexibilityChart"
import { colors } from "../../styles/tokens/colors"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"
import type { OverviewData } from "../../data/types/domain"

function OverviewPage() {
  const dataAdapter = useDataAdapter()
  const [state, setState] = useState<"loading" | "success" | "error" | "empty">("loading")
  const [data, setData] = useState<OverviewData | null>(null)
  const { isSimulationMode } = useSimulationMode()

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      if (dataAdapter?.getOverviewData) {
        try {
          const result = await dataAdapter.getOverviewData()
          if (!cancelled) {
            setData(result)
            setState("success")
          }
        } catch (e) {
          if (!cancelled) {
            setState("error")
          }
        }
      } else {
        try {
          const result = await import("../../data/adapters/mock/overview").then(
            (m) => new m.MockOverviewAdapter().getOverviewData()
          )
          if (!cancelled) {
            setData(result)
            setState("success")
          }
        } catch (e) {
          if (!cancelled) {
            setState("error")
          }
        }
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [dataAdapter])

  if (state === "loading") {
    return (
      <main className="overview-page">
        <StateMessage
          type="loading"
          title="Loading page context..."
          message="Fetching system overview data. Please wait."
        />
      </main>
    )
  }

  if (state === "error") {
    return (
      <main className="overview-page">
        <StateMessage
          type="error"
          title="Unable to load"
          message="An error occurred while loading this overview."
        />
      </main>
    )
  }

  if (!data) {
    return (
      <main className="overview-page">
        <StateMessage
          type="empty"
          title="No data available"
          message="There is no overview data to display for the current context."
        />
      </main>
    )
  }

  // Extract data for easier access
  const {
    scenario,
    simulationMode,
    systemSnapshot,
    renewableOpportunity,
    flexibilityState,
    nextDispatch,
    recentActivity,
  } = data

  return (
    <main className="overview-page">
      <header className="overview-header">
        <PageHeader title="Overview" scenario={{ ...scenario, mode: simulationMode ? "simulation" : "live" }} />
        <SimulationModeIndicator active={isSimulationMode} />
      </header>

      <section className="system-snapshot">
        <SectionHeader title="System Snapshot" />
        <div className="snapshot-metrics">
          <CapacityBar
            value={systemSnapshot.renewableOpportunityKwh}
            max={1500}
            label="Renewable opportunity"
            unit="kWh"
            intent="primary"
          />
          <CapacityBar
            value={systemSnapshot.trustedFlexibilityKw}
            max={500}
            label="Trusted flexibility"
            unit="kW"
            intent="success"
          />
          <CapacityBar
            value={systemSnapshot.gridHeadroomKw}
            max={600}
            label="Grid headroom"
            unit="kW"
            intent="subtle"
          />
        </div>
      </section>

      <section className="renewable-opportunity">
        <SectionHeader title="Renewable Opportunity" subtitle="Current / near‑term renewable availability window" />
        <div className="renewable-content">
          <div className="renewable-info">
            <Timeline
              title="Opportunity Window"
              steps={[
                { label: "Start", value: 25, unit: "%", time: "14:00", status: "complete" },
                { label: "Peak", value: 70, unit: "%", time: "16:00", status: "active" },
                { label: "End", value: 100, unit: "%", time: "18:00", status: "pending" },
              ]}
            />
            <div className="renewable-value">
              <OpportunityVis
                opportunity={{
                  id: "solar-window",
                  name: renewableOpportunity.opportunityWindow,
                  valueKw: renewableOpportunity.renewableKwh,
                  maxKw: 1500,
                  active: true,
                  constraints: ["Grid capacity", "Storage level"],
                }}
                onChange={() => {}}
              />
            </div>
          </div>
          <div className="renewable-visual">
            <CapacityBar
              value={renewableOpportunity.renewableKwh}
              max={1500}
              label="Renewable availability"
              unit="kWh"
              intent="primary"
              visualLabel={`${Math.round(renewableOpportunity.confidence * 100)}% confidence`}
            />
            <p className="visual-label" style={{ marginTop: spacing.xs }}>
              {renewableOpportunity.renewableKwh} kWh
            </p>
          </div>
        </div>
      </section>

      <section className="flexibility-state">
        <SectionHeader title="Flexibility State" subtitle="Potential vs expected vs trusted flexibility (tonal progression)" />
        <div className="flexibility-metrics">
          <CapacityBar
            value={flexibilityState.potentialKw}
            max={flexibilityState.potentialKw + 200}
            label="Potential"
            unit="kW"
            intent="subtle"
          />
          <CapacityBar
            value={flexibilityState.expectedKw}
            max={flexibilityState.potentialKw + 200}
            label="Expected"
            unit="kW"
            intent="subtle"
          />
          <CapacityBar
            value={flexibilityState.trustedKw}
            max={flexibilityState.potentialKw + 200}
            label="Trusted"
            unit="kW"
            intent="success"
          />
        </div>
        <div className="flexibility-explanation">
          <div className="explanation-left">
            <p className="label">Potential flexibility</p>
            <p className="detail">Theoretical maximum deliverable capacity</p>
          </div>
          <div className="explanation-center">
            <p className="label">Expected flexibility</p>
            <p className="detail">Evidence‑adjusted deliverable</p>
          </div>
          <div className="explanation-right">
            <p className="label">Trusted flexibility</p>
            <p className="detail">Confidence‑weighted deliverable capacity</p>
          </div>
          <div className="confidence-meter">
            <p className="label">Confidence level</p>
            <div
              style={{
                width: "100%",
                height: "8px",
                background: colors.neutrals.lightGrey,
                borderRadius: radii.sm,
                overflow: "hidden",
                marginTop: spacing.xs,
              }}
            >
              <div
                style={{
                  width: `${flexibilityState.confidence * 100}%`,
                  height: "100%",
                  background: colors.primary,
                  borderRadius: radii.sm,
                  transition: "width 0.3s ease",
                }}
              />
            </div>
            <p className="confidence-value" style={{ marginTop: spacing.xs }}>
              {Math.round(flexibilityState.confidence * 100)}%
            </p>
          </div>
        </div>
        <FlexibilityChart
          potential={flexibilityState.potentialKw}
          expected={flexibilityState.expectedKw}
          trusted={flexibilityState.trustedKw}
        />
      </section>

      <section className="next-dispatch">
        <SectionHeader title="Next Dispatch" subtitle="Recommended dispatch plan for the current window" />
        {nextDispatch ? (
          <div className="next-dispatch-content">
            <div className="dispatch-info">
              <p className="label">Dispatch ID</p>
              <p className="value"><code>{nextDispatch.id}</code></p>
              <p className="label">Window</p>
              <p className="value">{nextDispatch.timeWindow}</p>
              <p className="label">Total dispatched</p>
              <p className="value">{nextDispatch.totalDispatchedKw} kW</p>
              <p className="label">Rationale</p>
              <p className="value">{nextDispatch.rationale}</p>
            </div>
            <div className="dispatch-resources">
              <p className="label">Resources dispatched</p>
              <ul className="resource-list">
                {nextDispatch.resources.map((res) => (
                  <li key={res.id} className="resource-item">
                    <span className="resource-name">{res.name}</span>
                    <span className="resource-value">{res.dispatchedKw} kW</span>
                  </li>
                ))}
              </ul>
            </div>
            <p className="dispatch-note">
              Note: Dispatch is simulated in the UrjaSarathi environment; no physical devices are controlled.
            </p>
          </div>
        ) : (
          <StateMessage
            type="empty"
            title="No dispatch recommendation"
            message="There is currently no dispatch recommendation available for the active scenario."
          />
        )}
      </section>

      <section className="recent-activity">
        <SectionHeader title="Recent Activity" subtitle="Timeline of recent dispatches, simulations, and verifications" />
        {recentActivity.length > 0 ? (
          <ol className="activity-list">
            {recentActivity.map((item) => (
              <li key={item.id} className="activity-item">
                <span className="timestamp">{item.timestamp}</span>
                <span className="description">{item.description}</span>
              </li>
            ))}
          </ol>
        ) : (
          <StateMessage
            type="empty"
            title="No recent activity"
            message="There are no recent dispatches, simulations, or verifications to display."
          />
        )}
      </section>
    </main>
  )
}

export default OverviewPage
