import { Navigate, NavLink, Route, Routes, useLocation } from "react-router-dom"
import { OverviewPage } from "../../pages/OverviewPage"
import { FlexibilityPage } from "../../pages/FlexibilityPage"
import { DispatchPage } from "../../pages/DispatchPage"
import { ExperimentsPage } from "../../pages/ExperimentsPage"

export const Router = () => {
  const location = useLocation()
  const pathname = location.pathname

  // For deep linking: if we land on root /, redirect to /overview
  // Also handle unknown routes by redirecting to / (which will redirect to /overview)
  return (
    <>
      <Routes>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/flexibility" element={<FlexibilityPage />} />
        <Route path="/dispatch" element={<DispatchPage />} />
        <Route path="/experiments" element={<ExperimentsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}