import { useMemo } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { colors } from "../../styles/tokens/colors"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"

export type PageKey = "overview" | "flexibility" | "dispatch" | "experiments"

export interface PrimaryNavigationProps {
  activePage?: PageKey
  onNavigate?: (page: PageKey) => void
  className?: string
  orientation?: "horizontal" | "vertical"
}

const navItems: { key: PageKey; label: string; path: string; icon: string }[] = [
  { key: "overview", label: "Overview", path: "/overview", icon: "▦" },
  { key: "flexibility", label: "Flexibility", path: "/flexibility", icon: "◈" },
  { key: "dispatch", label: "Dispatch", path: "/dispatch", icon: "▶" },
  { key: "experiments", label: "Experiments", path: "/experiments", icon: "◎" },
]

export function PrimaryNavigation({
  activePage,
  onNavigate,
  className,
  orientation = "vertical",
}: PrimaryNavigationProps) {
  const navigate = useNavigate()
  const location = useLocation()

  const currentActive = useMemo(() => {
    if (activePage) return activePage
    const pathname = location.pathname
    for (const item of navItems) {
      if (pathname === item.path || pathname.startsWith(item.path + "/")) {
        return item.key
      }
    }
    return undefined
  }, [activePage, location.pathname])

  const handleNavigate = (page: PageKey, path: string) => {
    navigate(path)
    onNavigate?.(page)
  }

  const handleKeyDown = (e: React.KeyboardEvent, page: PageKey, path: string) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      handleNavigate(page, path)
    }
  }

  const isHorizontal = orientation === "horizontal"

  const navStyles: React.CSSProperties = isHorizontal
    ? {
        display: "flex",
        gap: "4px",
        padding: "6px",
        borderRadius: "6px",
        background: colors.neutrals.mist,
        minWidth: "280px",
        height: "40px",
        alignItems: "center",
      }
    : {
        display: "flex",
        flexDirection: "column",
        gap: "2px",
      }

  return (
    <nav
      role="tablist"
      aria-label="Primary navigation"
      className={className}
      style={navStyles}
    >
      {navItems.map((item) => {
        const isActive = currentActive === item.key
        return (
          <button
            key={item.key}
            role="tab"
            aria-selected={isActive}
            aria-current={isActive ? "page" : undefined}
            tabIndex={isActive ? 0 : -1}
            onClick={() => handleNavigate(item.key, item.path)}
            onKeyDown={(e) => handleKeyDown(e, item.key, item.path)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: spacing.sm,
              padding: isHorizontal ? "8px 16px" : "12px 16px",
              background: isActive ? colors.primary : "transparent",
              color: isActive ? colors.neutrals.warmCream : colors.neutrals.charcoal,
              border: "none",
              borderRadius: radii.sm,
              cursor: "pointer",
              fontSize: fontSizes.base,
              fontFamily: fonts.display,
              fontWeight: isActive ? fontWeights.semibold : fontWeights.normal,
              transition: "all 0.15s ease",
              width: isHorizontal ? "auto" : "100%",
              textAlign: isHorizontal ? "center" : "left",
              outline: "none",
              position: "relative",
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = colors.neutrals.lightGrey
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = "transparent"
              }
            }}
            onFocus={(e) => {
              e.currentTarget.style.outline = `2px solid ${colors.primary}`
              e.currentTarget.style.outlineOffset = "2px"
            }}
            onBlur={(e) => {
              e.currentTarget.style.outline = "none"
            }}
          >
            <span style={{ fontSize: fontSizes.lg, lineHeight: 1 }} aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}