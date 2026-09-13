import type { HorizonStep } from "../../data/types/domain/experiment"

export function HorizonChart({ steps }: { steps: HorizonStep[] }) {
  if (!steps.length) return null
  const width = 720
  const height = 230
  const pad = 32
  const max = Math.max(...steps.flatMap((step) => [step.renewableKwh, step.demandKwh, step.totalDeliveredKw]), 1)
  const point = (value: number, index: number) => {
    const x = pad + (index * (width - pad * 2)) / Math.max(steps.length - 1, 1)
    const y = height - pad - (value / max) * (height - pad * 2)
    return `${x},${y}`
  }

  return (
    <figure className="horizon-chart" aria-labelledby="horizon-chart-title">
      <figcaption id="horizon-chart-title">
        <span>Energy horizon</span>
        <small>RENEWABLE // DEMAND // DELIVERED</small>
      </figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Renewable energy, demand and delivered flexibility across the simulation horizon">
        {[0.25, 0.5, 0.75, 1].map((ratio) => <line key={ratio} x1={pad} x2={width - pad} y1={height - pad - ratio * (height - pad * 2)} y2={height - pad - ratio * (height - pad * 2)} className="horizon-chart__grid" />)}
        <polyline points={steps.map((step, index) => point(step.renewableKwh, index)).join(" ")} className="horizon-chart__line horizon-chart__line--renewable" />
        <polyline points={steps.map((step, index) => point(step.demandKwh, index)).join(" ")} className="horizon-chart__line horizon-chart__line--demand" />
        <polyline points={steps.map((step, index) => point(step.totalDeliveredKw, index)).join(" ")} className="horizon-chart__line horizon-chart__line--delivered" />
      </svg>
      <div className="horizon-chart__legend"><span>Renewable</span><span>Demand</span><span>Delivered</span></div>
    </figure>
  )
}
