import { useEffect } from "react"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"
import { StatusIndicator } from "../Indicators/StatusIndicator"
import type { FlexibilityResource } from "../../data/types/domain"

export interface ResourceDetailDrawerProps {
  resource: FlexibilityResource | null
  onClose: () => void
  className?: string
}

export function ResourceDetailDrawer({
  resource,
  onClose,
  className,
}: ResourceDetailDrawerProps) {
  useEffect(() => {
    if (!resource) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [resource, onClose])

  if (!resource) return null

  const constraintIndicator = (() => {
    const now = new Date(resource.deadline).getTime()
    const horizon = new Date(resource.latest_end).getTime()
    const diffHours = (now - horizon) / (1000 * 60 * 60)
    if (diffHours < 0) return "normal"
    if (diffHours < 2) return "warning"
    return "violation"
  })()

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        justifyContent: "flex-end",
        background: "rgba(23, 20, 18, 0.4)",
      }}
      onClick={onClose}
    >
      <aside
        className={className}
        style={{
          width: "420px",
          maxHeight: "100vh",
          overflowY: "auto",
          background: colors.neutrals.white,
          borderLeft: `1px solid ${colors.neutrals.mist}`,
          boxShadow: "-4px 0 16px rgba(23, 20, 18, 0.12)",
          padding: spacing.xl,
        }}
        role="dialog"
        aria-modal="true"
        aria-label={`Resource detail: ${resource.id}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: spacing.lg,
          }}
        >
          <div>
            <h2
              style={{
                fontFamily: fonts.display,
                fontSize: fontSizes.xl,
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.ink,
                margin: "0 0 4px 0",
              }}
            >
              {resource.id}
            </h2>
            <p
              style={{
                fontFamily: fonts.body,
                fontSize: fontSizes.sm,
                color: colors.neutrals.charcoal,
                margin: 0,
              }}
            >
              {resource.type.replace("_", " ")} · {resource.location_id}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: `${spacing.xs} ${spacing.md}`,
              background: colors.neutrals.mist,
              border: `1px solid ${colors.neutrals.lightGrey}`,
              borderRadius: radii.md,
              fontFamily: fonts.body,
              fontSize: fontSizes.sm,
              color: colors.neutrals.charcoal,
              cursor: "pointer",
            }}
            aria-label="Close resource detail"
          >
            ✕
          </button>
        </div>

        <StatusIndicator status={resource.state} label={resource.state} />
        <StatusIndicator
          status={constraintIndicator}
          label={
            constraintIndicator === "violation"
              ? "Constraint violation"
              : constraintIndicator === "warning"
              ? "Constraint warning"
              : "Constraint normal"
          }
        />

        <div
          style={{
            marginTop: spacing.lg,
            border: `1px solid ${colors.neutrals.mist}`,
            borderRadius: radii.lg,
            padding: spacing.lg,
          }}
        >
margin: `0 0 ${spacing.md} 0`,
          <div style={{ display: "grid", gap: spacing.md }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Potential
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.potential_kw} kW
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Expected
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.expected_kw} kW
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Trusted
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.trusted_kw} kW
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Confidence
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {Math.round(resource.confidence * 100)}%
              </span>
            </div>
          </div>
        </div>

        <div
          style={{
            marginTop: spacing.lg,
            border: `1px solid ${colors.neutrals.mist}`,
            borderRadius: radii.lg,
            padding: spacing.lg,
          }}
        >
          <h3
            style={{
              fontFamily: fonts.display,
              fontSize: fontSizes.lg,
              fontWeight: fontWeights.semibold,
              color: colors.neutrals.ink,
              margin: `0 0 ${spacing.md} 0`,
              marginBottom: spacing.md,
            }}
          >
            Constraints
          </h3>
          <div style={{ display: "grid", gap: spacing.sm }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Deadline
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.deadline}
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Earliest Start
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.earliest_start}
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Latest End
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.latest_end}
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Power Range
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.min_power}–{resource.max_power} kW
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Duration Range
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {resource.minimum_duration}–{resource.maximum_duration} h
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
                borderBottom: `1px solid ${colors.neutrals.mist}`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Override Rate
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {Math.round(resource.override_rate * 100)}%
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: `${spacing.xs} 0`,
              }}
            >
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                Availability Rate
              </span>
              <span
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                }}
              >
                {Math.round(resource.availability_rate * 100)}%
              </span>
            </div>
          </div>
        </div>

        <div
          style={{
            marginTop: spacing.lg,
            border: `1px solid ${colors.neutrals.mist}`,
            borderRadius: radii.lg,
            padding: spacing.lg,
          }}
        >
          <h3
            style={{
              fontFamily: fonts.display,
              fontSize: fontSizes.lg,
              fontWeight: fontWeights.semibold,
              color: colors.neutrals.ink,
              margin: `0 0 ${spacing.md} 0`,
              marginBottom: spacing.md,
            }}
          >
            Response History
          </h3>
          <div
            style={{
              borderLeft: `2px solid ${colors.neutrals.mist}`,
              paddingLeft: spacing.md,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: spacing.md,
                marginBottom: spacing.sm,
              }}
            >
              <div>
                <p
                  style={{
                    fontFamily: fonts.body,
                    fontSize: fontSizes.sm,
                    color: colors.neutrals.charcoal,
                    margin: "0 0 2px 0",
                  }}
                >
                  Actual vs. Dispatched
                </p>
                <p
                  style={{
                    fontFamily: fonts.monospace,
                    fontSize: fontSizes.sm,
                    color: colors.neutrals.ink,
                    margin: 0,
                  }}
                >
                  {Math.round(resource.historical_response * 100)}% delivered
                </p>
              </div>
              <div
                style={{
                  fontFamily: fonts.monospace,
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.ink,
                  fontWeight: fontWeights.medium,
                  textAlign: "right",
                }}
              >
                {Math.round(resource.override_rate * 100)}% override
              </div>
            </div>
            <p
              style={{
                fontFamily: fonts.body,
                fontSize: fontSizes.sm,
                color: colors.neutrals.charcoal,
                margin: "0",
              }}
            >
              Compact history of past dispatch responses, override occurrences,
              and delivery reliability for this resource.
            </p>
          </div>
        </div>
      </aside>
    </div>
  )
}