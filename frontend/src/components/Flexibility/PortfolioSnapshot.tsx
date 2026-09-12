import { MetricDisplay } from "../Indicators/MetricDisplay"
import { SectionHeader } from "../Layout/SectionHeader"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"

export interface PortfolioSnapshotProps {
  resourceCount: number
  potentialKw: number
  expectedKw: number
  trustedKw: number
  className?: string
}

export function PortfolioSnapshot({
  resourceCount,
  potentialKw,
  expectedKw,
  trustedKw,
  className,
}: PortfolioSnapshotProps) {
  return (
    <section
      className={className}
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: spacing.md,
        marginBottom: spacing.xl,
      }}
    >
      <div
        style={{
          padding: `${spacing.md} ${spacing.lg}`,
          background: colors.neutrals.white,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: "6px",
        }}
      >
        <span
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
          Resources
        </span>
        <span
          style={{
            fontFamily: fonts.body,
            fontSize: fontSizes.xl,
            fontWeight: fontWeights.semibold,
            color: colors.neutrals.ink,
          }}
        >
          {resourceCount}
        </span>
      </div>
      <MetricDisplay label="Potential" value={potentialKw} unit="kW" state="success" />
      <MetricDisplay label="Expected" value={expectedKw} unit="kW" state="success" />
      <MetricDisplay label="Trusted" value={trustedKw} unit="kW" state="success" />
    </section>
  )
}