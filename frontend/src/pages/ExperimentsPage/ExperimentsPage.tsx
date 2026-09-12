import { AppShell } from "../../components/Shell/AppShell"
import { SectionHeader } from "../../components/Layout/SectionHeader"
import { StateMessage } from "../../components/State/StateMessage"

function ExperimentsPage() {
  return (
    <AppShell currentPage="experiments" scenario={null}>
      <SectionHeader title="Experiments" />
      <StateMessage
        type="empty"
        title="Experiments workspace"
        message="The Experiments workspace is available in F4."
      />
    </AppShell>
  )
}

export default ExperimentsPage