# GridFlex AI water-heater candidate v1 model card

## Status

**Accepted for the hackathon/MVP prototype. Not approved for real deployment.**

## What it predicts

For each 15-minute water-heater flexibility event, the bundle returns:

- `potential_kw`: physical power that could be adjusted;
- `expected_kw`: the model's most likely delivered flexibility;
- `trusted_kw`: a deliberately conservative amount suitable for the prototype;
- `confidence`: `trusted_kw / expected_kw`, a conservatism indicator rather than a calibrated probability.

The expected estimate uses histogram gradient boosting. The trusted estimate is
the smaller of the expected prediction and a separately trained 10th-percentile
gradient-boosting prediction.

## Evidence boundary

- Dataset: 700 fully synthetic water heaters and 21,000 synthetic response events
- Training: 490 heaters / 14,700 events
- Validation and policy selection: 105 heaters / 3,150 events
- Final resource-disjoint test: 105 heaters / 3,150 events
- Training/test resource overlap: zero
- Final test was opened only after the feature, model and safety policy were frozen

## Final test results

| Measure | Result |
| --- | ---: |
| Baseline response-ratio MAE | 0.368521 |
| Candidate response-ratio MAE | 0.335084 |
| Baseline power MAE | 1.331304 kW |
| Candidate power MAE | 1.210335 kW |
| Overall trusted overprediction | 9.78% |
| Heat-pump overprediction | 9.29% |
| Resistance-heater overprediction | 10.76% |
| Small/medium/large maximum overprediction | 10.12% |
| Trusted kW retained | 5.22% |

The candidate beats the selected baseline and every predeclared group stays
below the 15% overprediction ceiling.

## Important limitation

The 5.22% retention result means the safe estimate is extremely conservative.
It is useful for demonstrating the GridFlex `potential_kw -> expected_kw ->
trusted_kw` pipeline, but it would release very little water-heater capacity in
practice. This must not be presented as a production-quality fleet controller.

All response outcomes are synthetic. The BPA source informed heater mix and
CTA-2045 command vocabulary only; it did not provide 700 real household event
histories. Real-device pilots, geographic data, drift monitoring and dynamic
replanning are required before any field use.

## Reproduction

From the repository root, run the baseline, candidate-development and safety
calibration modules in order. The committed final report and model bundle are
the one-time test outputs; the evaluator intentionally refuses to overwrite the
report and consume the same holdout again.

The demo-only backend adapter returns the shared `TrustState` structure. Because
the current backend resource schema lacks water-heater physical state, it uses
recorded training medians for those missing values and lists every fallback in
the result. Backend routing is intentionally left unchanged for team review.
