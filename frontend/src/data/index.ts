const isMockMode = import.meta.env.VITE_MOCK_MODE === "true"

export const getOverviewData = (): Promise<any> => {
  if (isMockMode) {
    return import("./adapters/mock/overview").then(
      (m) => new m.MockOverviewAdapter().getOverviewData()
    )
  }
  return Promise.reject(new Error("Real adapter not configured"))
}

export const getFlexibilityResources = (): Promise<any> => {
  if (isMockMode) {
    return import("./adapters/mock/resources").then(
      (m) => new m.MockResourcesAdapter().getFlexibilityResources()
    )
  }
  return Promise.reject(new Error("Real adapter not configured"))
}
