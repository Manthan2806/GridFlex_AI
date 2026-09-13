interface FlexibilityChartProps {
  potential: number
  expected: number
  trusted: number
}

export function FlexibilityChart({ potential, expected, trusted }: FlexibilityChartProps) {
  const max = Math.max(potential, expected, trusted, 1)
  const values = [
    { label: "Potential", value: potential, tone: "neutral" },
    { label: "Expected", value: expected, tone: "primary" },
    { label: "Trusted", value: trusted, tone: "success" },
  ]

  return (
    <figure className="flex-chart" aria-labelledby="flex-chart-title">
      <figcaption id="flex-chart-title">
        <span>Flexibility confidence funnel</span>
        <small>AVAILABLE POWER // kW</small>
      </figcaption>
      <div className="flex-chart__plot">
        {values.map((item) => (
          <div className="flex-chart__row" key={item.label}>
            <span>{item.label}</span>
            <div className="flex-chart__track">
              <div className={`flex-chart__bar flex-chart__bar--${item.tone}`} style={{ width: `${(item.value / max) * 100}%` }} />
            </div>
            <strong>{item.value.toFixed(0)}</strong>
          </div>
        ))}
      </div>
      <p>The gap between potential and trusted power is the safety margin applied before dispatch.</p>
    </figure>
  )
}
