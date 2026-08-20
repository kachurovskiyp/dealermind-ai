# Vehicle Variant Intelligence v1

DealerMind treats a model name as a family, not as a sufficient comparable group. An Audi A6 C8 40 TDI quattro S line and an Audi A6 C7 petrol sedan must not silently receive the same market valuation.

## Normalized identity

The first version records generation, body type, facelift, marketed engine name, engine code, capacity, power, fuel, gearbox, drivetrain, trim line and performance variant. `S line`, `M Sport`, `AMG Line` and `R-Line` are equipment lines; true performance derivatives remain a separate `performance_variant` field.

Every extracted characteristic can have append-only evidence containing its source, raw value, normalized value, confidence and confirmation status. A later correction adds a new observation and updates the current vehicle projection; it does not erase the earlier fact.

## Comparable hierarchy

Valuation selects the narrowest cohort that contains the configured minimum sample:

1. exact variant — known characteristics agree and power is within 20 hp;
2. close variant — no conflict in generation, body type or fuel, with close power;
3. broad model — last-resort model-level sample.

The selected cohort is stored in the valuation explanation as `variant_cohort`. This keeps a fallback usable while making reduced precision visible.

## Market knowledge

The Poland dashboard groups a selected make/model by normalized variant and displays sample size, median, range, premium/discount versus the model median, evidence completeness and confidence. These figures are market observations, not claims about mechanical reliability.

Reliability, maintenance risk and desirability will be introduced as separately versioned knowledge with cited evidence. They must not be inferred from price alone.
