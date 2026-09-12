import type { DispatchData } from "../../data/types/domain/dispatch"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export interface RenewableOpportunityDetailProps {
  data: DispatchData
}

export function RenewableOpportunityDetail({ data }: RenewableOpportunityDetailProps) {
  return (
    <section
      style={{
        marginBottom: spacing.xl,
      }}
    >
      <h3
        style={{
          fontFamily: fonts.display,
          fontSize: fontSizes.lg,
          fontWeight: fontWeights.semibold,
          marginBottom: spacing.md,
          color: colors.primary,
        }}
      >
        Renewable Opportunity
      </h3>

      <div
        style={{
          padding: spacing.lg,
          background: colors.neutrals.white,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: radii.lg,
        }}
      >
        <div style={{ marginBottom: spacing.md }}>
          <span
            style={{
              fontSize: fontSizes.xs,
              color: colors.neutrals.charcoal,
              fontWeight: fontWeights.medium,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Opportunity Window
          </span>
          <p
            style={{
              fontSize: fontSizes.lg,
              fontWeight: fontWeights.semibold,
              color: colors.primary,
              marginTop: spacing.xs,
            }}
          >
            {data.renewableOpportunity.opportunityWindow}
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: spacing.lg,
            flexWrap: "wrap",
          }}
        >
          <div style={{ flex: 1, minWidth: "200px" }}>
            <span
              style={{
                fontSize: fontSizes.xs,
                color: colors.neutrals.charcoal,
                fontWeight: fontWeights.medium,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "4px",
                display: "block",
              }}
            >
              Available kWh
            </span>
            <span
              style={{
                fontSize: fontSizes["2xl"],
                fontWeight: fontWeights.bold,
                color: colors.primary,
              }}
            >
              {data.renewableOpportunity.renewableKwh} kWh
            </span>
          </div>

          <div style={{ flex: 1, minWidth: "200px" }}>
            <span
              style={{
                fontSize: fontSizes.xs,
                color: colors.neutrals.charcoal,
                fontWeight: fontWeights.medium,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "4px",
                display: "block",
              }}
            >
              Confidence
            </span>
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: spacing.sm,
              }}
            >
              <span
                style={{
                  fontSize: fontSizes["2xl"],
                  fontWeight: fontWeights.bold,
                  color: colors.primary,
                }}
              >
                {Math.round(data.renewableOpportunity.confidence * 100)}%
              </span>
              <span
                style={{
                  fontSize: fontSizes.sm,
                  color: colors.neutrals.charcoal,
                }}
              >
                {data.renewableOpportunity.confidence < 0.5 ? "Low" : data.renewableOpportunity.confidence < 0.8 ? "Medium" : "High"}
              </span>
            </div>
          </div>
        </div>

        <p
          style={{
            marginTop: spacing.lg,
            fontSize: fontSizes.sm,
            color: colors.neutrals.charcoal,
            lineHeight: 1.5,
          }}
        >
          {data.renewableOpportunity.description}
        </p>
      </div>
    </section>
  )
}
