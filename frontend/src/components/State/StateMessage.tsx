import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"

export type StateMessageType = "loading" | "empty" | "error" | "success"

export interface StateMessageProps {
  type: StateMessageType
  title?: string
  message?: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

const defaultMessages: Record<StateMessageType, { title: string; message: string }> = {
  loading: {
    title: "Loading...",
    message: "Fetching data. Please wait.",
  },
  empty: {
    title: "No data available",
    message: "There is no data to display for the current context.",
  },
  error: {
    title: "Unable to load",
    message: "An error occurred while loading this data.",
  },
  success: {
    title: "Success",
    message: "The operation completed successfully.",
  },
}

const typeStyles: Record<
  StateMessageType,
  { borderColor: string; iconColor: string; titleColor: string }
> = {
  loading: {
    borderColor: colors.neutrals.mist,
    iconColor: colors.neutrals.charcoal,
    titleColor: colors.neutrals.charcoal,
  },
  empty: {
    borderColor: colors.neutrals.lightGrey,
    iconColor: colors.neutrals.charcoal,
    titleColor: colors.neutrals.charcoal,
  },
  error: {
    borderColor: colors.primary,
    iconColor: colors.primary,
    titleColor: colors.primary,
  },
  success: {
    borderColor: colors.primary,
    iconColor: colors.primary,
    titleColor: colors.primary,
  },
}

export function StateMessage({
  type,
  title,
  message,
  action,
  className,
}: StateMessageProps) {
  const { borderColor, iconColor, titleColor } = typeStyles[type]
  const defaults = defaultMessages[type]

  return (
    <div
      style={{
        padding: `${spacing.xl} ${spacing["2xl"]}`,
        background: "rgba(255,255,255,0.5)",
        border: `1px solid ${borderColor}`,
        borderRadius: radii.lg,
        textAlign: "center",
      }}
      className={className}
      role={type === "error" ? "alert" : "status"}
      aria-live={type === "error" ? "assertive" : "polite"}
    >
      <div
        style={{
          width: "40px",
          height: "40px",
          borderRadius: radii.round,
          background: "rgba(0,0,0,0.05)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 12px",
        }}
        aria-hidden="true"
      >
        {type === "loading" && (
          <div
            style={{
              width: "24px",
              height: "24px",
              border: `3px solid ${iconColor}`,
              borderTopColor: "transparent",
              borderRadius: radii.round,
              animation: "spin 1s linear infinite",
            }}
          />
        )}
        {type === "empty" && (
          <span
            style={{
              fontSize: fontSizes.xl,
              color: iconColor,
            }}
          >
            —
          </span>
        )}
        {type === "error" && (
          <span
            style={{
              fontSize: fontSizes.xl,
              color: iconColor,
              fontWeight: fontWeights.bold,
            }}
          >
            !
          </span>
        )}
        {type === "success" && (
          <span
            style={{
              fontSize: fontSizes.xl,
              color: iconColor,
              fontWeight: fontWeights.bold,
            }}
          >
            ✓
          </span>
        )}
      </div>

      <h3
        style={{
          fontFamily: fonts.display,
          fontSize: fontSizes.lg,
          fontWeight: fontWeights.semibold,
          color: titleColor,
          margin: 0,
          marginBottom: spacing.xs,
        }}
      >
        {title || defaults.title}
      </h3>

      <p
        style={{
          fontFamily: fonts.body,
          fontSize: fontSizes.sm,
          color: colors.neutrals.charcoal,
          margin: 0,
          marginBottom: spacing.lg,
        }}
      >
        {message || defaults.message}
      </p>

      {action ? (
        <button
          onClick={action.onClick}
          style={{
            padding: `${spacing.sm} ${spacing.xl}`,
            background: colors.primary,
            color: "#FFFFFF",
            borderRadius: radii.md,
            fontFamily: fonts.body,
            fontSize: fontSizes.sm,
            fontWeight: fontWeights.medium,
            cursor: "pointer",
            transition: "background 0.15s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#561823"
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = colors.primary
          }}
        >
          {action.label}
        </button>
      ) : null}
    </div>
  )
}