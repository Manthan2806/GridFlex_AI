import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

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
  const isDetailed = view === "detailed"

  return (
    <div className={className} style={{ width: "100%" }}>
      <div
        style={{
          fontFamily: fonts.display,
          fontSize: fontSizes.base,
          fontWeight: fontWeights.semibold,
          color: colors.neutrals.ink,
          marginBottom: spacing.sm,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {title}
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "stretch",
          gap: spacing.xs,
          width: "100%",
          minHeight: isDetailed ? "60px" : "40px",
        }}
      >
        {steps.map((step, idx) => {
          const isLast = idx === steps.length - 1
          const statusColor = step.color || (step.status === "complete" ? colors.primary : colors.neutrals.grey)

          return (
            <div
              key={idx}
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: spacing.xs,
                position: "relative",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: isDetailed ? "40px" : "24px",
                  background: colors.neutrals.lightGrey,
                  borderRadius: radii.sm,
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${step.value}%`,
                    height: "100%",
                    background: statusColor,
                    borderRadius: radii.sm,
                    transition: "width 0.3s ease",
                  }}
                />
                {step.status === "active" && (
                  <div
                    style={{
                      position: "absolute",
                      top: 0,
                      left: "50%",
                      width: "2px",
                      height: "100%",
                      background: colors.primary,
                      animation: "pulse 2s infinite",
                    }}
                  />
                )}
              </div>

              <div
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.xs,
                  color: colors.neutrals.charcoal,
                  textAlign: "center",
                }}
              >
                {step.label}
              </div>

              {isDetailed && (
                <div
                  style={{
                    fontFamily: fonts.monospace,
                    fontSize: fontSizes.xs,
                    color: colors.neutrals.grey,
                    textAlign: "center",
                  }}
                >
                  {step.time}
                </div>
              )}

              {!isLast && (
                <div
                  style={{
                    position: "absolute",
                    right: "-8px",
                    top: "50%",
                    width: "16px",
                    height: "2px",
                    background: colors.neutrals.grey,
                    transform: "translateY(-50%)",
                  }}
                />
              )}
            </div>
          )
        })}
      </div>

      <style>
        {`@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }`}
      </style>
    </div>
  )
}