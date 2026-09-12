import { useEffect, useState } from "react"
import { SectionHeader } from "../../components/Layout/SectionHeader"
import { PortfolioSnapshot } from "../../components/Flexibility/PortfolioSnapshot"
import { ResourceSearchFilters } from "../../components/Flexibility/ResourceSearchFilters"
import { ResourcePortfolioTable } from "../../components/Flexibility/ResourcePortfolioTable"
import { ResourceDetailDrawer } from "../../components/Flexibility/ResourceDetailDrawer"
import { useDataAdapter } from "../../app/providers/DataAdapterProvider"
import { colors } from "../../styles/tokens/colors"
import { fonts, fontSizes, fontWeights } from "../../styles/tokens/typography"
import { spacing } from "../../styles/tokens/spacing"
import type { FlexibilityResource } from "../../data/types/domain"

export function FlexibilityPage() {
  const dataAdapter = useDataAdapter()
  const [resources, setResources] = useState<FlexibilityResource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [locationFilter, setLocationFilter] = useState("")
  const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const loadResources = async () => {
      try {
        const result = await dataAdapter.getFlexibilityResources()
        if (!cancelled) {
          setResources(result)
          setError(null)
        }
      } catch (e) {
        if (!cancelled) {
          setError("Unable to load flexibility resources")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadResources()
    return () => {
      cancelled = true
    }
  }, [dataAdapter])

  const filteredResources = resources.filter((r) => {
    const matchesSearch = r.id.toLowerCase().includes(search.toLowerCase())
    const matchesType = !typeFilter || r.type === typeFilter
    const matchesStatus = !statusFilter || r.state === statusFilter
    const matchesLocation = !locationFilter || r.location_id === locationFilter
    return matchesSearch && matchesType && matchesStatus && matchesLocation
  })

  const selectedResource = resources.find((r) => r.id === selectedResourceId) || null

  const snapshot = {
    resourceCount: resources.length,
    potentialKw: resources.reduce((sum, r) => sum + r.potential_kw, 0),
    expectedKw: resources.reduce((sum, r) => sum + r.expected_kw, 0),
    trustedKw: resources.reduce((sum, r) => sum + r.trusted_kw, 0),
  }

  if (loading) {
    return (
      <main
        className="flexibility-page"
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: spacing.xl,
          background: colors.neutrals.white,
          border: `1px solid ${colors.neutrals.mist}`,
          borderRadius: "6px",
          textAlign: "center",
          color: colors.neutrals.charcoal,
          fontFamily: fonts.body,
          fontSize: fontSizes.sm,
        }}
      >
        Loading flexibility resources...
      </main>
    )
  }

  if (error) {
    return (
      <main
        className="flexibility-page"
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: spacing.xl,
          background: colors.neutrals.white,
          border: `1px solid ${colors.primary}`,
          borderRadius: "6px",
          textAlign: "center",
          color: colors.primary,
          fontFamily: fonts.body,
          fontSize: fontSizes.sm,
        }}
      >
        {error}
      </main>
    )
  }

  return (
    <main
      className="flexibility-page"
      style={{
        maxWidth: "1200px",
        margin: "0 auto",
        width: "100%",
        padding: spacing.lg,
        overflow: "hidden",
      }}
    >
      <header
        style={{
          marginBottom: spacing.xl,
          paddingBottom: spacing.lg,
          borderBottom: `1px solid ${colors.neutrals.mist}`,
        }}
      >
        <SectionHeader
          title="Flexibility"
          subtitle="Portfolio of flexible resources and their trust/reliability"
        />
      </header>

      <div className="flexibility-page-layout">
        <PortfolioSnapshot
          resourceCount={snapshot.resourceCount}
          potentialKw={snapshot.potentialKw}
          expectedKw={snapshot.expectedKw}
          trustedKw={snapshot.trustedKw}
        />

        <ResourceSearchFilters
          search={search}
          onSearchChange={setSearch}
          typeFilter={typeFilter}
          onTypeFilterChange={setTypeFilter}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          locationFilter={locationFilter}
          onLocationFilterChange={setLocationFilter}
        />

        <ResourcePortfolioTable
          resources={filteredResources}
          selectedId={selectedResourceId || undefined}
          onRowSelect={(resource) => setSelectedResourceId(resource.id)}
        />
      </div>

      <ResourceDetailDrawer
        resource={selectedResource}
        onClose={() => setSelectedResourceId(null)}
      />
    </main>
  )
}

export default FlexibilityPage