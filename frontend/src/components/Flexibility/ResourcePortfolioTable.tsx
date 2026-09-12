import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"
import { StatusIndicator } from "../Indicators/StatusIndicator"
import type { FlexibilityResource } from "../../data/types/domain"

export interface ResourcePortfolioTableProps {
  resources: FlexibilityResource[]
  selectedId?: string
  onRowSelect: (resource: FlexibilityResource) => void
  className?: string
}

const thStyle: React.CSSProperties = {
  padding: `${spacing.sm} ${spacing.md}`,
  textAlign: "left",
  fontWeight: fontWeights.semibold,
  color: colors.neutrals.charcoal,
  whiteSpace: "nowrap",
  fontSize: fontSizes.xs,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  background: colors.neutrals.mist,
  borderBottom: `1px solid ${colors.neutrals.lightGrey}`,
}

const tdStyle: React.CSSProperties = {
  padding: `${spacing.sm} ${spacing.md}`,
  color: colors.neutrals.charcoal,
  whiteSpace: "nowrap",
  fontSize: fontSizes.sm,
  borderBottom: `1px solid ${colors.neutrals.mist}`,
}

export function ResourcePortfolioTable({
  resources,
  selectedId,
  onRowSelect,
  className,
}: ResourcePortfolioTableProps) {
  if (resources.length === 0) {
    return (
      <div
        className="resource-portfolio-table"
        style={{
          padding: spacing.xl,
          background: colors.neutrals.warmCream,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.sm,
          textAlign: "center",
          color: colors.neutrals.charcoal,
          fontFamily: fonts.body,
          fontSize: fontSizes.sm,
        }}
      >
        No resources match the current filters.
      </div>
    )
  }

  return (
    <div
      className="resource-portfolio-table"
      style={{
        overflowX: "auto",
        maxWidth: "100%",
        background: colors.neutrals.warmCream,
        border: `1px solid ${colors.neutrals.mist}`,
        borderRadius: radii.sm,
      }}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontFamily: fonts.body,
          fontSize: fontSizes.sm,
        }}
      >
        <thead>
          <tr>
            <th style={thStyle}>ID</th>
            <th style={thStyle}>Type</th>
            <th style={thStyle}>Location</th>
            <th style={{ ...thStyle, textAlign: "right" }}>Potential</th>
            <th style={{ ...thStyle, textAlign: "right" }}>Expected</th>
            <th style={{ ...thStyle, textAlign: "right" }}>Trusted</th>
            <th style={{ ...thStyle, textAlign: "right" }}>Confidence</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Constraint</th>
          </tr>
        </thead>
        <tbody>
          {resources.map((resource) => {
            const isSelected = resource.id === selectedId
            const constraintIndicator = (() => {
              const now = new Date(resource.deadline).getTime()
              const horizon = new Date(resource.latest_end).getTime()
              const diffHours = (now - horizon) / (1000 * 60 * 60)
              if (diffHours < 0) return "normal"
              if (diffHours < 2) return "warning"
              return "violation"
            })()

            return (
              <tr
                key={resource.id}
                onClick={() => onRowSelect(resource)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault()
                    onRowSelect(resource)
                  }
                }}
                tabIndex={0}
                role="button"
                aria-selected={isSelected}
                style={{
                  cursor: "pointer",
                  background: isSelected
                    ? `rgba(${colors.primary.replace("#", "")}, 0.08)`
                    : colors.neutrals.warmCream,
                  borderBottom: `1px solid ${colors.neutrals.mist}`,
                  transition: "background 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = colors.neutrals.mist
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = colors.neutrals.warmCream
                  }
                }}
              >
                <td style={{ ...tdStyle, color: colors.neutrals.ink, fontWeight: fontWeights.medium, fontFamily: fonts.monospace }}>
                  {resource.id}
                </td>
                <td style={tdStyle}>{resource.type.replace("_", " ")}</td>
                <td style={tdStyle}>{resource.location_id}</td>
                <td style={{ ...tdStyle, textAlign: "right", color: colors.neutrals.ink, fontFamily: fonts.monospace }}>
                  {resource.potential_kw}
                </td>
                <td style={{ ...tdStyle, textAlign: "right", color: colors.neutrals.ink, fontFamily: fonts.monospace }}>
                  {resource.expected_kw}
                </td>
                <td style={{ ...tdStyle, textAlign: "right", color: colors.neutrals.ink, fontFamily: fonts.monospace }}>
                  {resource.trusted_kw}
                </td>
                <td style={{ ...tdStyle, textAlign: "right", fontFamily: fonts.monospace }}>
                  {Math.round(resource.confidence * 100)}%
                </td>
                <td style={tdStyle}>
                  <StatusIndicator status={resource.state} />
                </td>
                <td style={tdStyle}>
                  <StatusIndicator status={constraintIndicator} />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}