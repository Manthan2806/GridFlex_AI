import { AppShell } from "../../components/Shell/AppShell"
import { SectionHeader } from "../../components/Layout/SectionHeader"
import { StateMessage } from "../../components/State/StateMessage"

function DispatchPage() {
  return (
    <AppShell currentPage="dispatch" scenario={null}>
      <SectionHeader title="Dispatch" />
      <StateMessage
        type="empty"
        title="Dispatch workspace"
        message="The Dispatch workspace is available in F3."
      />
    </AppShell>
  )
}

export default DispatchPage