import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface Opportunity {
  id: string
  name?: string
  valueKw: number
  maxKw: number
  active: boolean
  constraints: string[]
  activated?: boolean
}

export interface OpportunityVisProps {
  opportunity: Opportunity
  onChange?: (id: string, value: number) => void
  className?: string
}

export function OpportunityVis({ opportunity, onChange, className }: OpportunityVisProps) {
  const pct = opportunity.maxKw > 0 ? (opportunity.valueKw / opportunity.maxKw) * 100 : 0

  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: spacing.sm,
        padding: spacing.sm,
        borderRadius: radii.sm,
        background: colors.neutrals.lightGrey,
      }}
      role="group"
      aria-label={`Opportunity: ${opportunity.id}`}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: fontSizes.base,
            fontWeight: fontWeights.semibold,
            color: colors.neutrals.ink,
          }}
        >
          {opportunity.name || opportunity.id}
        </span>
        <span
          style={{
            fontFamily: fonts.monospace,
            fontSize: fontSizes.lg,
            fontWeight: fontWeights.semibold,
            color: opportunity.active ? colors.primary : colors.neutrals.grey,
          }}
        >
          {opportunity.valueKw}{" "}
          <span style={{ fontSize: fontSizes.sm, color: colors.neutrals.grey }}>kW</span>
        </span>
      </div>

      {/* Proportional opportunity bar */}
      <div style={{ position: "relative" }}>
        <div
          style={{
            display: "flex",
            height: "28px",
            borderRadius: radii.sm,
            overflow: "hidden",
            background: colors.neutrals.white,
          }}
        >
          {/* Filled portion */}
          <div
            style={{
              width: `${pct}%`,
              background: opportunity.active ? colors.primary : colors.neutrals.grey,
              borderRadius: radii.sm,
              transition: "width 0.3s ease",
            }}
          />
          {/* Remaining portion */}
          <div
            style={{
              flex: 1,
              background: colors.neutrals.mist,
            }}
          />
        </div>

        {/* Tick marks at 25/50/75/100 */}
        <div
          style={{
            position: "relative",
            height: "8px",
            marginTop: spacing.xs,
          }}
        >
          {[25, 50, 75, 100].map((tick) => (
            <div
              key={tick}
              style={{
                position: "absolute",
                left: `${tick}%`,
                width: "1px",
                height: "4px",
                background: colors.neutrals.grey,
                transform: "translateX(-50%)",
              }}
            />
          ))}
        </div>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontFamily: fonts.monospace,
          fontSize: fontSizes.xs,
          color: colors.neutrals.charcoal,
        }}
      >
        <span>{opportunity.maxKw} kW max</span>
        <span>{Math.round(pct)}% allocated</span>
      </div>

      {opportunity.constraints.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: spacing.xs,
            marginTop: spacing.xs,
          }}
        >
          {opportunity.constraints.map((c) => (
            <span
              key={c}
              style={{
                display: "inline-block",
                padding: `2px ${spacing.xs}`,
                borderRadius: radii.xs,
                background: colors.neutrals.mist,
                color: colors.neutrals.charcoal,
                fontFamily: fonts.monospace,
                fontSize: fontSizes.xs,
              }}
            >
              {c}
            </span>
          ))}
        </div>
      )}

      {opportunity.activated && onChange && (
        <input
          type="range"
          min={0}
          max={opportunity.maxKw}
          value={opportunity.valueKw}
          onChange={(e) => onChange(opportunity.id, Number(e.target.value))}
          style={{ width: "100%", marginTop: spacing.xs }}
          aria-label={`Adjust ${opportunity.id} value`}
        />
      )}
    </div>
  )
}
