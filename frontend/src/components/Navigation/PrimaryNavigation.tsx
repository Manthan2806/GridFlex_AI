import { useMemo } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { colors } from "../../styles/tokens/colors"

export type PageKey = "overview" | "flexibility" | "dispatch" | "experiments"

export interface PrimaryNavigationProps {
  activePage?: PageKey
  onNavigate?: (page: PageKey) => void
  className?: string
}

const navItems: { key: PageKey; label: string; path: string }[] = [
  { key: "overview", label: "Overview", path: "/overview" },
  { key: "flexibility", label: "Flexibility", path: "/flexibility" },
  { key: "dispatch", label: "Dispatch", path: "/dispatch" },
  { key: "experiments", label: "Experiments", path: "/experiments" },
]

export function PrimaryNavigation({
  activePage,
  onNavigate,
  className,
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

  return (
    <nav
      role="tablist"
      aria-label="Primary navigation"
      className={className}
      style={{
        display: "flex",
        gap: "4px",
        background: colors.primary,
        padding: "6px",
        borderRadius: "6px",
        minWidth: "280px",
        height: "40px",
        alignItems: "center",
      }}
    >
      {navItems.map((item) => {
        const isActive = currentActive === item.key
        return (
          <button
            key={item.key}
            role="tab"
            aria-selected={isActive}
            aria-current={isActive ? "page" : undefined}
            onClick={() => handleNavigate(item.key, item.path)}
            style={{
              flex: 1,
              padding: "8px 16px",
              background: isActive
                ? "rgba(255,255,255,0.12)"
                : "transparent",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.95rem",
              fontWeight: isActive ? 600 : 400,
              transition: "background 0.15s ease",
              outline: "none",
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = "rgba(255,255,255,0.08)"
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = "transparent"
              }
            }}
            onFocus={(e) => {
              e.currentTarget.style.outline = "2px solid rgba(255,255,255,0.5)"
              e.currentTarget.style.outlineOffset = "2px"
            }}
            onBlur={(e) => {
              e.currentTarget.style.outline = "none"
            }}
          >
            {item.label}
          </button>
        )
      })}
    </nav>
  )
}