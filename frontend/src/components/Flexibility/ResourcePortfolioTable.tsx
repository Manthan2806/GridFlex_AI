import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { StatusIndicator } from "../Indicators/StatusIndicator"
import type { FlexibilityResource } from "../../data/types/domain"

export interface ResourcePortfolioTableProps {
  resources: FlexibilityResource[]
  selectedId?: string
  onRowSelect: (resource: FlexibilityResource) => void
  className?: string
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
        style={{
          padding: spacing.xl,
          background: colors.neutrals.white,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: "6px",
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
      className={className}
      style={{
        overflowX: "auto",
        background: colors.neutrals.white,
        border: `1px solid ${colors.neutrals.mist}`,
        borderRadius: "6px",
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
          <tr
            style={{
              background: colors.neutrals.mist,
              borderBottom: `1px solid ${colors.neutrals.lightGrey}`,
            }}
          >
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "left",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              ID
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "left",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Type
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "left",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Location
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "right",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Potential
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "right",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Expected
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "right",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Trusted
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "right",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Confidence
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "left",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Status
            </th>
            <th
              style={{
                padding: `${spacing.sm} ${spacing.md}`,
                textAlign: "left",
                fontWeight: fontWeights.semibold,
                color: colors.neutrals.charcoal,
                whiteSpace: "nowrap",
              }}
            >
              Constraint
            </th>
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
                style={{
                  cursor: "pointer",
                  background: isSelected
                    ? "rgba(107, 30, 46, 0.08)"
                    : colors.neutrals.white,
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
                    e.currentTarget.style.background = colors.neutrals.white
                  }
                }}
              >
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    color: colors.neutrals.ink,
                    fontWeight: fontWeights.medium,
                    fontFamily: fonts.monospace,
                    whiteSpace: "nowrap",
                  }}
                >
                  {resource.id}
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    color: colors.neutrals.charcoal,
                    whiteSpace: "nowrap",
                  }}
                >
                  {resource.type.replace("_", " ")}
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    color: colors.neutrals.charcoal,
                    whiteSpace: "nowrap",
                  }}
                >
                  {resource.location_id}
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    textAlign: "right",
                    color: colors.neutrals.ink,
                    fontFamily: fonts.monospace,
                    whiteSpace: "nowrap",
                  }}
                >
                  {resource.potential_kw}
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    textAlign: "right",
                    color: colors.neutrals.ink,
                    fontFamily: fonts.monospace,
                    whiteSpace: "nowrap",
                  }}
                >
                  {resource.expected_kw}
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    textAlign: "right",
                    color: colors.neutrals.ink,
                    fontFamily: fonts.monospace,
                    whiteSpace: "nowrap",
                  }}
                >
                  {resource.trusted_kw}
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    textAlign: "right",
                    color: colors.neutrals.charcoal,
                    fontFamily: fonts.monospace,
                    whiteSpace: "nowrap",
                  }}
                >
                  {Math.round(resource.confidence * 100)}%
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    whiteSpace: "nowrap",
                  }}
                >
                  <StatusIndicator status={resource.state} />
                </td>
                <td
                  style={{
                    padding: `${spacing.sm} ${spacing.md}`,
                    whiteSpace: "nowrap",
                  }}
                >
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