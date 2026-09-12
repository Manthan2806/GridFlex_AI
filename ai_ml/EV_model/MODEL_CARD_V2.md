# GridFlex AI EV candidate v2 model card

## Status

**Accepted for the offline hackathon demo. Not approved for real deployment.**

## Prediction

Candidate v2 estimates an EV dispatch delivery ratio with Histogram Gradient
Boosting. A separate conditional quantile model and group-specific conformal
adjustments produce the conservative `trusted_kw` value.

## Evidence boundary

- Development fit rows: 14,700
- Disjoint model-selection rows: 1,740
- Disjoint safety-calibration rows: 1,410
- Final holdout: 210 new ACN-anchored resources and 6,300 synthetic response events
- ACN source overlap with the original 700 resources: zero
- Candidate 1 holdout rows reused: zero

## Final holdout results

| Measure | Result |
| --- | ---: |
| Baseline delivery-ratio MAE | 0.160162 |
| Candidate v2 delivery-ratio MAE | 0.153383 |
| Baseline power MAE | 0.707230 kW |
| Candidate v2 power MAE | 0.683852 kW |
| Overall trusted overprediction | 13.17% |
| Small-dispatch overprediction | 13.02% |
| Medium-dispatch overprediction | 14.83% |
| Large-dispatch overprediction | 11.67% |
| Trusted kW retained | 50.09% |

All predeclared offline checks passed. Every dispatch group stayed below the 15%
overprediction limit, and retained power stayed above the 50% usefulness floor.

## Limitations

- ACN supplies real US workplace charging-session structure, not Ahmedabad EV data.
- Availability, override, SOC, battery and repeated-response behaviour are synthetic.
- This evidence supports only an offline demonstration.
- Real grid commitments remain prohibited.
