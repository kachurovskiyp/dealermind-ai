# DealerMind AI — Developer Bible

## 1. Product purpose

DealerMind AI is a decision-intelligence platform for automotive dealers. It must help answer four questions:

1. What should we buy?
2. At what maximum acquisition price?
3. In which market should we sell it?
4. Why is this decision appropriate for this dealer at this moment?

The platform is not a generic CRM and not an AI chatbot. Chat is one interface over a traceable data and decision platform.

## 2. Non-negotiable principles

1. **Data before opinion.** Scores and recommendations must be based on stored facts, explicit assumptions and versioned rules.
2. **Explain every decision.** Every score stores inputs, factor values, weights, rule-set version and explanation.
3. **Never overwrite history.** New observations and decisions are appended. Corrections are represented as new events or revisions.
4. **Market and dealer are separate.** Market attractiveness is not the same as suitability for a specific business.
5. **Vehicle and offer are separate.** One vehicle can appear in multiple listings and markets.
6. **Configuration over magic numbers.** Weights and thresholds are versioned configuration, not literals scattered through code.
7. **AI does not perform accounting.** Deterministic code calculates money, durations and scores. AI summarizes and explains.
8. **Adapters at the boundary.** Marketplace collectors, payment systems and messaging integrations do not leak into the domain model.
9. **Build vertical slices.** Each increment must solve a real business task end to end.
10. **Privacy and tenant isolation by design.** Company-specific data and learned dealer behavior must never mix across tenants.

## 3. Core scores

### Market Score

Answers: **How attractive is this vehicle for a selected sales market?**

Typical factors: liquidity, demand, price position, reliability, competition, seasonality and expected days to sale.

### Dealer Score

Answers: **How suitable is this opportunity for this dealer?**

Typical factors: predicted net profit, ROI, preparation duration, preparation complexity, internal capability fit, external-service dependency, capital turnover and operational risk.

### Opportunity Score

Answers: **Should the dealer act on this specific offer now?**

Typical factors: discount to market, listing freshness, seller type, distance, data completeness, negotiation potential and urgency.

Scores must remain separate. A combined recommendation may reference all three, but must never erase their distinctions.

## 4. Preparation intelligence

Preparation is a first-class lifecycle, not a single expense field. Each job records:

- category and work type;
- planned and actual dates;
- active labor time and waiting time;
- internal team, external provider or mixed execution;
- parts, labor and external-service costs;
- blocker and dependency information;
- before/after evidence;
- expected versus actual outcome.

This enables estimation of hidden costs: waiting, capacity consumption, capital lock-up and external dependency.

## 5. Decision memory

Every recommendation stores:

- decision timestamp;
- rule-set and model versions;
- exact inputs available at that time;
- factor contributions;
- uncertainty and missing data;
- recommendation and rationale;
- eventual business outcome when known.

Historical decisions are immutable and reproducible.

## 6. Delivery standard

A feature is complete only when it has:

- an explicit business problem;
- domain terminology;
- API or application behavior;
- automated tests;
- migration where needed;
- documentation and observability;
- acceptance criteria verified with realistic examples.
