export type TimelineView = "compact" | "detailed"

export interface TimelineStep {
  label: string
  value: number
  unit?: string
  time?: string
  color?: string
  status?: "complete" | "active" | "pending"
}

export interface TimelineProps {
  title: string
  steps: TimelineStep[]
  view?: TimelineView
  className?: string
}

export function Timeline({ title, steps, view = "compact", className }: TimelineProps) {
  return (
    <div className={`opportunity-timeline ${className ?? ""}`}>
      <p className="opportunity-timeline__title">{title}</p>
      <div className="opportunity-timeline__axis" role="img" aria-label={`${title}: ${steps.map((step) => `${step.label} ${step.time ?? ""}`).join(", ")}`}>
        <div className="opportunity-timeline__line" aria-hidden="true" />
        {steps.map((step) => (
          <div className={`opportunity-timeline__step opportunity-timeline__step--${step.status ?? "pending"}`} key={`${step.label}-${step.time}`}>
            <span className="opportunity-timeline__node" aria-hidden="true" />
            <strong>{step.label}</strong>
            <span>{step.time ?? `${step.value}${step.unit ?? ""}`}</span>
            {view === "detailed" && step.time && <small>{step.value}{step.unit ?? ""}</small>}
          </div>
        ))}
      </div>
    </div>
  )
}
