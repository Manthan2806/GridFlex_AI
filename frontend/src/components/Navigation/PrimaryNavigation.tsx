import { NavLink } from "react-router-dom"

export type PageKey = "overview" | "flexibility" | "dispatch" | "experiments"
export interface PrimaryNavigationProps {
  activePage?: PageKey
  onNavigate?: (page: PageKey) => void
  className?: string
  orientation?: "horizontal" | "vertical"
}
const navItems: { key: PageKey; label: string; path: string }[] = [
  { key: "overview", label: "Overview", path: "/overview" },
  { key: "flexibility", label: "Flexibility", path: "/flexibility" },
  { key: "dispatch", label: "Dispatch", path: "/dispatch" },
  { key: "experiments", label: "Experiments", path: "/experiments" },
]

export function PrimaryNavigation({ onNavigate, className }: PrimaryNavigationProps) {
  return (
    <nav className={`primary-nav ${className ?? ""}`} aria-label="Primary navigation">
      {navItems.map((item) => (
        <NavLink key={item.key} to={item.path} onClick={() => onNavigate?.(item.key)}
          className={({ isActive }) => `primary-nav__link${isActive ? " primary-nav__link--active" : ""}`}>
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
