import { ScenarioContext } from "../Scenario/ScenarioContext"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"

export type PageHeaderState = "loading" | "success" | "empty" | "error"

export interface PageHeaderProps {
  title: string
  state?: PageHeaderState
  scenario?: {
    id: string
    name: string
    timeHorizon: number | string
    seed: number
    category: string
    mode: "simulation" | "live"
  } | null
  message?: string
  className?: string
}

export function PageHeader({
  title,
  state = "success",
  scenario,
  message,
  className,
}: PageHeaderProps) {
  const stateMessage = {
    loading: "Loading page context...",
    empty: "No page context is available.",
    error: message || "Unable to load page context.",
  }

  return (
    <header
      style={{
        marginBottom: spacing.xl,
        paddingBottom: spacing.lg,
        borderBottom: `1px solid ${colors.neutrals.mist}`,
      }}
      className={className}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: spacing.lg,
          flexWrap: "wrap",
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: fonts.display,
              fontSize: fontSizes["2xl"],
              fontWeight: fontWeights.bold,
              lineHeight: "30px",
              color: colors.neutrals.ink,
              margin: 0,
            }}
          >
            {title}
          </h1>

          {state === "loading" ? (
            <p
              style={{
                color: colors.neutrals.charcoal,
                fontSize: fontSizes.sm,
                marginTop: spacing.sm,
              }}
            >
              {stateMessage.loading}
            </p>
          ) : state === "empty" ? (
            <p
              style={{
                color: colors.neutrals.charcoal,
                fontSize: fontSizes.sm,
                marginTop: spacing.sm,
              }}
            >
              {stateMessage.empty}
            </p>
          ) : state === "error" ? (
            <p
              style={{
                color: colors.primary,
                fontSize: fontSizes.sm,
                marginTop: spacing.sm,
              }}
            >
              {stateMessage.error}
            </p>
          ) : null}
        </div>

        {state === "success" && scenario ? (
          <ScenarioContext scenario={scenario} />
        ) : null}
      </div>
    </header>
  )
}