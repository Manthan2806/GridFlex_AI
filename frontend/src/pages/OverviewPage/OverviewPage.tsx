import { useEffect, useState } from "react"
import { useDataAdapter } from "../../app/providers/DataAdapterProvider"
import { useSimulationMode } from "../../app/providers/SimulationContextProvider"
import { MetricDisplay } from "../../components/Indicators/MetricDisplay"
import { PageHeader } from "../../components/Header/PageHeader"
import { SectionHeader } from "../../components/Layout/SectionHeader"
import { SimulationModeIndicator } from "../../components/Indicators/SimulationModeIndicator"
import { StateMessage } from "../../components/State/StateMessage"
import { OverviewData } from "../../data/types/domain"
import { getOverviewData } from "../../data"

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
          const result = await getOverviewData()
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
    recentActivity
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
          <MetricDisplay label="Renewable opportunity" value={systemSnapshot.renewableOpportunityKwh} unit="kWh" state="success" />
          <MetricDisplay label="Trusted flexibility" value={systemSnapshot.trustedFlexibilityKw} unit="kW" state="success" />
          <MetricDisplay label="Grid headroom" value={systemSnapshot.gridHeadroomKw} unit="kW" state="success" />
        </div>
      </section>

      <section className="renewable-opportunity">
        <SectionHeader title="Renewable Opportunity" subtitle="Current / near‑term renewable availability window" />
        <div className="renewable-content">
          <div className="renewable-info">
            <p className="timestamp">{renewableOpportunity.opportunityWindow}</p>
            <p className="value">
              {renewableOpportunity.renewableKwh} kWh
              <span className="confidence">
                Confidence: {Math.round(renewableOpportunity.confidence * 100)}%
              </span>
            </p>
            <p className="description">{renewableOpportunity.description}</p>
          </div>
          <div className="renewable-visual">
            <div className="visual-track">
              <div className="visual-fill" style={{ width: `${renewableOpportunity.confidence * 100}%` }} />
            </div>
            <p className="visual-label">{renewableOpportunity.renewableKwh} kWh</p>
          </div>
        </div>
      </section>

      <section className="flexibility-state">
        <SectionHeader title="Flexibility State" subtitle="Potential vs expected vs trusted flexibility (tonal progression)" />
        <div className="flexibility-metrics">
          <MetricDisplay label="Potential" value={flexibilityState.potentialKw} unit="kW" state="success" />
          <MetricDisplay label="Expected" value={flexibilityState.expectedKw} unit="kW" state="success" />
          <MetricDisplay label="Trusted" value={flexibilityState.trustedKw} unit="kW" state="success" />
        </div>
        <div className="flexibility-explanation">
          <div className="explanation-left">
            <p className="label">Potential flexibility</p>
            <p className="detail">Theoretical maximum deliverable capacity (potential_kw)</p>
          </div>
          <div className="explanation-center">
            <p className="label">Expected flexibility</p>
            <p className="detail">Evidence‑adjusted deliverable (expected_kw)</p>
          </div>
          <div className="explanation-right">
            <p className="label">Trusted flexibility</p>
            <p className="detail">Confidence‑weighted deliverable capacity (trusted_kw)</p>
          </div>
          <div className="confidence-meter">
            <p className="label">Confidence level</p>
            <div className="confidence-track">
              <div className="confidence-fill" style={{ width: `${flexibilityState.confidence * 100}%` }} />
            </div>
            <p className="confidence-value">{Math.round(flexibilityState.confidence * 100)}%</p>
          </div>
        </div>
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
              Note: Dispatch is simulated in the GridFlex AI environment; no physical devices are controlled.
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