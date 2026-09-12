import React from "react"
import { PrimaryNavigation } from "../Navigation/PrimaryNavigation"
import { ScenarioContext } from "../Scenario/ScenarioContext"
import { SimulationModeIndicator } from "../Indicators/SimulationModeIndicator"
import { SectionHeader } from "../Layout/SectionHeader"
import { colors } from "../../styles/tokens/colors"
import { spacing } from "../../styles/tokens/spacing"
import { radii } from "../../styles/tokens/radii"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"

export interface AppShellProps {
  currentPage: "overview" | "flexibility" | "dispatch" | "experiments"
  scenario: {
    id: string
    name: string
    timeHorizon: number
    seed: number
    category: string
    mode: "simulation" | "live"
  } | null
  children: React.ReactNode
  className?: string
}

const shellStyle: React.CSSProperties = {
  display: "flex",
  minHeight: "100vh",
  background: colors.neutrals.warmCream,
  color: colors.neutrals.ink,
  fontFamily: fonts.sans,
}

const sidebarStyle: React.CSSProperties = {
  width: "240px",
  minWidth: "240px",
  background: colors.neutrals.warmCream,
  borderRight: `1px solid ${colors.neutrals.lightGrey}`,
  display: "flex",
  flexDirection: "column",
  padding: spacing.lg,
  position: "sticky",
  top: 0,
  height: "100vh",
  overflowY: "auto",
}

const mainStyle: React.CSSProperties = {
  flexGrow: 1,
  padding: spacing.lg,
  maxWidth: "1400px",
  width: "100%",
}

const headerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: spacing.lg,
  gap: spacing.md,
  flexWrap: "wrap",
}

const brandStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: spacing.sm,
}

const brandLogoStyle: React.CSSProperties = {
  width: "32px",
  height: "32px",
  background: colors.primary,
  borderRadius: radii.sm,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: colors.neutrals.warmCream,
  fontFamily: fonts.display,
  fontWeight: fontWeights.bold,
  fontSize: fontSizes.base,
}

const brandNameStyle: React.CSSProperties = {
  fontFamily: fonts.display,
  fontSize: fontSizes.lg,
  fontWeight: fontWeights.semibold,
  color: colors.neutrals.ink,
  letterSpacing: "-0.01em",
}

export function AppShell({
  currentPage,
  scenario,
  children,
  className,
}: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false)

  return (
    <div style={shellStyle} className={className}>
      <a
        href="#main-content"
        style={{
          position: "absolute",
          left: "-9999px",
          top: "0",
          zIndex: 10000,
          background: colors.primary,
          color: colors.neutrals.warmCream,
          padding: spacing.sm,
          borderRadius: radii.sm,
          fontFamily: fonts.body,
          fontSize: fontSizes.sm,
          fontWeight: fontWeights.semibold,
        }}
        onFocus={(e) => {
          e.currentTarget.style.left = "12px"
          e.currentTarget.style.top = "12px"
        }}
        onBlur={(e) => {
          e.currentTarget.style.left = "-9999px"
          e.currentTarget.style.top = "0"
        }}
      >
        Skip to main content
      </a>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            zIndex: 999,
            display: "flex",
          }}
          onClick={() => setSidebarOpen(false)}
          role="button"
          aria-label="Close navigation"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Escape" || e.key === "Enter") setSidebarOpen(false)
          }}
        >
          <aside
            style={{
              ...sidebarStyle,
              width: "280px",
              height: "100vh",
              position: "relative",
              borderRight: "none",
              boxShadow: "0 0 40px rgba(0,0,0,0.3)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <PrimaryNavigation activePage={currentPage} />
          </aside>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside style={sidebarStyle} aria-label="Primary navigation">
        <div style={{ ...brandStyle, marginBottom: spacing.lg }}>
          <div style={brandLogoStyle}>G</div>
          <div style={brandNameStyle}>GridFlex</div>
        </div>
        <PrimaryNavigation activePage={currentPage} />
      </aside>

      <main style={mainStyle} id="main-content">
        <header style={headerStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: spacing.md }}>
            {/* Mobile hamburger */}
            <button
              className="mobile-menu-button"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle navigation"
              aria-expanded={sidebarOpen}
              style={{
                display: "none",
                background: "none",
                border: `1px solid ${colors.neutrals.lightGrey}`,
                borderRadius: radii.sm,
                padding: spacing.xs,
                cursor: "pointer",
                color: colors.neutrals.ink,
              }}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M2 5h16M2 10h16M2 15h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
            <SectionHeader title={currentPage} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: spacing.md }}>
            {scenario ? <ScenarioContext scenario={scenario} /> : null}
            <SimulationModeIndicator />
          </div>
        </header>

        {children}
      </main>

      <style>
        {`
          @media (max-width: 768px) {
            .mobile-menu-button {
              display: flex !important;
            }
            aside {
              display: none !important;
            }
            main {
              padding: 16px !important;
            }
          }
        `}
      </style>
    </div>
  )
}