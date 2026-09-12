import { SectionHeader } from "../../components/Layout/SectionHeader"
import { StateMessage } from "../../components/State/StateMessage"

function ExperimentsPage() {
  return (
    <main className="page-page" style={{ maxWidth: "1200px", margin: "0 auto", padding: "1.5rem" }}>
      <SectionHeader title="Experiments" />
      <StateMessage
        type="empty"
        title="Experiments workspace"
        message="The Experiments workspace is available in F4."
      />
    </main>
  )
}

export default ExperimentsPage