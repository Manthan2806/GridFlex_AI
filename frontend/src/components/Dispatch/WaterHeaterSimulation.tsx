import { useState } from "react"
import { runWaterHeaterSimulation, type WaterHeaterRun } from "../../data/adapters/api/waterHeater"

export function WaterHeaterSimulation() {
  const [result, setResult] = useState<WaterHeaterRun | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)

  async function run() {
    setRunning(true)
    setError(null)
    try {
      setResult(await runWaterHeaterSimulation())
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to reach the backend")
    } finally {
      setRunning(false)
    }
  }

  return (
    <section className="water-heater-console" aria-labelledby="water-heater-title">
      <div className="water-heater-console__head">
        <div>
          <p className="water-heater-console__eyebrow">Model channel // water heater</p>
          <h3 id="water-heater-title">Water-heater prototype</h3>
          <p>Run the saved water-heater model through the real backend endpoint.</p>
        </div>
        <button className="water-heater-console__button" type="button" onClick={() => void run()} disabled={running}>
          {running ? "Running…" : "Run water-heater model"}
        </button>
      </div>

      {error && <p className="water-heater-console__error" role="alert">{error}. Start the FastAPI backend and try again.</p>}
      {result && (
        <div aria-live="polite">
          <div className="water-heater-console__metrics">
            <div className="water-heater-console__metric"><span>Potential</span><strong>{result.total_potential_kw.toFixed(2)} kW</strong></div>
            <div className="water-heater-console__metric"><span>Expected</span><strong>{result.total_expected_kw.toFixed(2)} kW</strong></div>
            <div className="water-heater-console__metric"><span>Trusted</span><strong>{result.total_trusted_kw.toFixed(2)} kW</strong></div>
            <div className="water-heater-console__metric"><span>Delivered</span><strong>{result.total_delivered_kw.toFixed(2)} kW</strong></div>
          </div>
          <p className="water-heater-console__note">RUN {result.run_id} // {result.resources.length} synthetic resources // {result.label} // live deployment disabled</p>
        </div>
      )}
    </section>
  )
}
