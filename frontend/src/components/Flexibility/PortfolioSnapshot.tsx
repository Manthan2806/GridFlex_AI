import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

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
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: spacing.md,
        marginBottom: spacing.xl,
      }}
    >
      <div
        style={{
          padding: `${spacing.md} ${spacing.lg}`,
          background: colors.neutrals.warmCream,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.sm,
          display: "flex",
          flexDirection: "column",
          gap: spacing.xs,
        }}
      >
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.semibold,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Resources
        </span>
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: fontSizes.xxl,
            fontWeight: fontWeights.semibold,
            color: colors.neutrals.ink,
          }}
        >
          {resourceCount}
        </span>
      </div>

      <div
        style={{
          padding: `${spacing.md} ${spacing.lg}`,
          background: colors.neutrals.warmCream,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.sm,
          display: "flex",
          flexDirection: "column",
          gap: spacing.xs,
        }}
      >
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.semibold,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Potential
        </span>
        <span
          style={{
            fontFamily: fonts.monospace,
            fontSize: fontSizes.xxl,
            fontWeight: fontWeights.semibold,
            color: colors.neutrals.ink,
          }}
        >
          {potentialKw}{" "}
          <span style={{ fontSize: fontSizes.sm, color: colors.neutrals.grey }}>kW</span>
        </span>
      </div>

      <div
        style={{
          padding: `${spacing.md} ${spacing.lg}`,
          background: colors.neutrals.warmCream,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.sm,
          display: "flex",
          flexDirection: "column",
          gap: spacing.xs,
        }}
      >
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.semibold,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Expected
        </span>
        <span
          style={{
            fontFamily: fonts.monospace,
            fontSize: fontSizes.xxl,
            fontWeight: fontWeights.semibold,
            color: colors.neutrals.ink,
          }}
        >
          {expectedKw}{" "}
          <span style={{ fontSize: fontSizes.sm, color: colors.neutrals.grey }}>kW</span>
        </span>
      </div>

      <div
        style={{
          padding: `${spacing.md} ${spacing.lg}`,
          background: colors.neutrals.warmCream,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.sm,
          display: "flex",
          flexDirection: "column",
          gap: spacing.xs,
        }}
      >
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: fontSizes.xs,
            color: colors.neutrals.charcoal,
            fontWeight: fontWeights.semibold,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Trusted
        </span>
        <span
          style={{
            fontFamily: fonts.monospace,
            fontSize: fontSizes.xxl,
            fontWeight: fontWeights.semibold,
            color: colors.primary,
          }}
        >
          {trustedKw}{" "}
          <span style={{ fontSize: fontSizes.sm, color: colors.neutrals.grey }}>kW</span>
        </span>
      </div>
    </section>
  )
}