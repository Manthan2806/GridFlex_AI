import { useEffect, type ReactNode } from "react"
import { PrimaryNavigation } from "../Navigation/PrimaryNavigation"

export interface AppShellProps {
  currentPage: "overview" | "flexibility" | "dispatch" | "experiments"
  scenario: { id: string; name: string; timeHorizon: number; seed: number; category: string; mode: "simulation" | "live" } | null
  children: ReactNode
  className?: string
}

export function AppShell({ currentPage, scenario, children, className }: AppShellProps) {
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible")
          observer.unobserve(entry.target)
        }
      }
    }, { threshold: 0.12, rootMargin: "0px 0px -40px" })

    const selector = "#main-content .page-frame > main > :not(header), #main-content section, #main-content figure"
    const registerElements = () => {
      const elements = Array.from(document.querySelectorAll<HTMLElement>(selector))
      elements.forEach((element, index) => {
        if (element.classList.contains("reveal-on-scroll")) return
        element.classList.add("reveal-on-scroll")
        element.style.setProperty("--reveal-delay", `${Math.min(index, 4) * 55}ms`)
        observer.observe(element)
      })
    }

    registerElements()
    const mutationObserver = new MutationObserver(registerElements)
    mutationObserver.observe(document.querySelector("#main-content") ?? document.body, {
      childList: true,
      subtree: true,
    })

    return () => {
      mutationObserver.disconnect()
      observer.disconnect()
    }
  }, [currentPage])

  return (
    <div className={`app-shell ${className ?? ""}`}>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="site-header">
        <div className="site-header__inner">
          <a className="brand" href="/overview" aria-label="UrjaSarathi overview">
            <span className="brand__name">URJASARATHI</span>
            <span className="brand__edition">AI // OPERATIONS</span>
          </a>
          <PrimaryNavigation activePage={currentPage} orientation="horizontal" />
          <div className="system-reference" aria-label="Current scenario">
            <span className="system-reference__dot" aria-hidden="true" />
            <span>[{scenario?.id ?? "NO-SCENARIO"} // {scenario?.mode ?? "simulation"}]</span>
          </div>
        </div>
      </header>
      <main className="site-main" id="main-content"><div className="page-frame">{children}</div></main>
      <footer className="site-footer">
        <span>URJASARATHI</span>
        <span>SIMULATED DECISION SUPPORT</span>
      </footer>
    </div>
  )
}
