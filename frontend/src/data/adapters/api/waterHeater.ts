export interface WaterHeaterRun {
  run_id: string
  demo_mode: boolean
  label: string
  release_status: string
  deployment_allowed: boolean
  feeder_capacity_kw: number
  total_potential_kw: number
  total_expected_kw: number
  total_trusted_kw: number
  total_dispatched_kw: number
  total_delivered_kw: number
  resources: Array<{
    resource_id: string
    confidence: number
    trusted_kw: number
    dispatched_kw: number
    delivered_kw: number
  }>
  limitations: string[]
}

const apiBase = import.meta.env.VITE_API_URL || "/api"

export async function runWaterHeaterSimulation(): Promise<WaterHeaterRun> {
  const response = await fetch(`${apiBase}/simulate/water-heater`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
  if (!response.ok) throw new Error(`Backend returned ${response.status}`)
  return response.json() as Promise<WaterHeaterRun>
}
