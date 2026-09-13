# GridFlex AI EV model card

## Release status

**Experimental — not approved for deployment.**

This model may be shown in the hackathon as an offline prototype. It must not be used to promise or dispatch real power.

## What it predicts

The model estimates the fraction of requested EV power likely to be delivered. It reports a raw `expected_kw` value and a more conservative `trusted_kw` value.

## Model and data

- Algorithm: `RandomForestRegressor` (`shallower` configuration)
- Input features: 18
- Safety target selected before final testing: 85%
- Final holdout rows: 3,150
- Data basis: ACN session structure combined with synthetic EV behaviour

## Final holdout results

| Measure | Rolling-history baseline | Random Forest expected estimate | Trusted estimate |
| --- | ---: | ---: | ---: |
| Delivery-ratio MAE | 0.149405 | 0.148648 | 0.292454 |
| Power MAE | 0.735653 kW | 0.727312 kW | 1.509180 kW |

The trusted estimate retained 58.44% of expected power. Its overall overprediction rate was 14.41% against a maximum of 15.00%.

| Dispatch group | Overprediction rate | Limit | Result |
| --- | ---: | ---: | --- |
| Small | 15.79% | 15.00% | Fail |
| Medium | 15.96% | 15.00% | Fail |
| Large | 11.98% | 15.00% | Pass |

## Decision

The candidate was rejected because it failed: `all_dispatch_groups_pass_overprediction_limit`. Small and medium dispatches crossed the pre-declared 15% limit. The production model artifact was therefore not saved.

## Allowed use

- Demonstrate the data pipeline and prediction flow.
- Show expected and trusted estimates with the label **experimental offline estimate**.
- Discuss the final result as an example of an honest model-validation gate.

## Not allowed

- Do not call the model production-ready, validated for Ahmedabad, or safe for real grid dispatch.
- Do not change the safety threshold after seeing the final results and then claim the same holdout as independent evidence.
- Do not reuse the consumed holdout for tuning.

## Next valid experiment

Develop the next candidate using training and validation evidence only. Evaluate it against a genuinely new untouched dataset with acceptance rules fixed in advance.
