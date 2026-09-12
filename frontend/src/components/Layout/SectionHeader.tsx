import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"

export interface SectionHeaderProps {
  title: string
  subtitle?: string
  className?: string
}

export function SectionHeader({
  title,
  subtitle,
  className,
}: SectionHeaderProps) {
  return (
    <header
      style={{
        display: "flex",
        flexDirection: "column",
        gap: spacing.xs,
        marginBottom: spacing.xl,
      }}
      className={className}
    >
      <h2
        style={{
          fontFamily: fonts.display,
          fontSize: fontSizes.xl,
          fontWeight: fontWeights.semibold,
          margin: 0,
          color: colors.neutrals.ink,
          lineHeight: "24px",
        }}
      >
        {title}
      </h2>
      {subtitle ? (
        <p
          style={{
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            color: colors.neutrals.charcoal,
            margin: 0,
          }}
        >
          {subtitle}
        </p>
      ) : null}
      <div
        style={{
          width: "32px",
          height: "2px",
          background: colors.neutrals.lightGrey,
          marginTop: spacing.xs,
        }}
      />
    </header>
  )
}