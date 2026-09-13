# Frontend Feature Audit

Audited against `FRONTEND_PRODUCT_SPEC.md`, the Viraj frontend branch, the current backend, and the supplied Stitch screens.

| Area | UI present | Backend connection | Honest status |
|---|---:|---:|---|
| Overview | Yes | Partial | Complete screen; overview values currently use the mock adapter because the backend has no `/overview` endpoint. |
| Flexibility portfolio | Yes | Partial | Table, search, filters, resource drawer, trust values, status and constraints are present; `/resources` is not implemented in the backend. |
| EV dispatch | Yes | Yes | Recommendation, rationale, checks, simulation action and result are present. Real mode calls `/simulate` and normalizes the backend result; mock mode remains available for frontend-only demos. |
| Water-heater dispatch | Yes | Yes | Dispatch screen calls `/simulate/water-heater` and displays the saved prototype model totals. |
| Experiments | Yes | Partial | Feasibility, horizon, comparison, instruction matrix and trust updates are present; the UI uses its experiment adapter because no dedicated experiment endpoint exists. |
| Loading, empty and error states | Yes | — | Included on the main data-driven pages and the water-heater action. |
| Responsive navigation/layout | Yes | — | Top navigation collapses into a scrollable mobile row and content grids stack. |

## Important limits

- EV and water-heater results are hackathon/MVP prototype results, not field validation or permission for live dispatch.
- Water-heater evidence is fully synthetic, and the UI labels it accordingly.
- Industrial resources are intentionally excluded because no industrial model or backend integration exists yet.
- Stitch was used as the visual reference only. Sample claims and sample measurements from its static HTML were not treated as project facts.

## Recommended follow-up

1. Add backend `/overview` and `/resources` contracts so those pages no longer depend on mock data.
2. Add a dedicated experiment-results endpoint backed by the saved experiment JSON.
3. Add the industrial dataset/model only after the EV and water-heater paths are stable.
