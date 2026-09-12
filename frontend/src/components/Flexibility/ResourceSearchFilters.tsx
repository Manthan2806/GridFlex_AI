import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"

export interface ResourceSearchFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  typeFilter: string
  onTypeFilterChange: (value: string) => void
  statusFilter: string
  onStatusFilterChange: (value: string) => void
  locationFilter: string
  onLocationFilterChange: (value: string) => void
  className?: string
}

export function ResourceSearchFilters({
  search,
  onSearchChange,
  typeFilter,
  onTypeFilterChange,
  statusFilter,
  onStatusFilterChange,
  locationFilter,
  onLocationFilterChange,
  className,
}: ResourceSearchFiltersProps) {
  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: spacing.md,
        marginBottom: spacing.xl,
        padding: spacing.md,
        background: colors.neutrals.white,
        border: `1px solid ${colors.neutrals.mist}`,
        borderRadius: "6px",
      }}
    >
      <div style={{ flex: "1 1 200px", minWidth: "180px" }}>
        <label
          style={{
            display: "block",
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.medium,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: "4px",
          }}
        >
          Search by ID
        </label>
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="e.g. ev-fleet-01"
          style={{
            width: "100%",
            padding: `${spacing.sm} ${spacing.md}`,
            border: `1px solid ${colors.neutrals.lightGrey}`,
            borderRadius: "6px",
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.ink,
            background: colors.neutrals.white,
          }}
        />
      </div>
      <div style={{ flex: "1 1 140px", minWidth: "120px" }}>
        <label
          style={{
            display: "block",
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.medium,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: "4px",
          }}
        >
          Type
        </label>
        <select
          value={typeFilter}
          onChange={(e) => onTypeFilterChange(e.target.value)}
          style={{
            width: "100%",
            padding: `${spacing.sm} ${spacing.md}`,
            border: `1px solid ${colors.neutrals.lightGrey}`,
            borderRadius: "6px",
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.ink,
            background: colors.neutrals.white,
          }}
        >
          <option value="">All types</option>
          <option value="ev">EV</option>
          <option value="water_heater">Water Heater</option>
          <option value="industrial_batch">Industrial Batch</option>
        </select>
      </div>
      <div style={{ flex: "1 1 140px", minWidth: "120px" }}>
        <label
          style={{
            display: "block",
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.medium,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: "4px",
          }}
        >
          Status
        </label>
        <select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
          style={{
            width: "100%",
            padding: `${spacing.sm} ${spacing.md}`,
            border: `1px solid ${colors.neutrals.lightGrey}`,
            borderRadius: "6px",
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.ink,
            background: colors.neutrals.white,
          }}
        >
          <option value="">All statuses</option>
          <option value="available">Available</option>
          <option value="dispatched">Dispatched</option>
          <option value="completed">Completed</option>
          <option value="unavailable">Unavailable</option>
        </select>
      </div>
      <div style={{ flex: "1 1 140px", minWidth: "120px" }}>
        <label
          style={{
            display: "block",
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.medium,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: "4px",
          }}
        >
          Location
        </label>
        <select
          value={locationFilter}
          onChange={(e) => onLocationFilterChange(e.target.value)}
          style={{
            width: "100%",
            padding: `${spacing.sm} ${spacing.md}`,
            border: `1px solid ${colors.neutrals.lightGrey}`,
            borderRadius: "6px",
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.ink,
            background: colors.neutrals.white,
          }}
        >
          <option value="">All locations</option>
          <option value="site-a">Site A</option>
          <option value="site-b">Site B</option>
          <option value="site-c">Site C</option>
        </select>
      </div>
    </div>
  )
}