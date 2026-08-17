# Opportunity Ranking v1

Ranking v1 turns stored facts into three immutable score snapshots whenever an opportunity is
created or explicitly recalculated.

## Evidence policy

The engine never invents a value for an unavailable factor. It calculates only what the current
record supports and reports every missing configured factor in the snapshot.

- **Market Score:** current price position derived from expected purchase and sale prices.
- **Dealer Score:** expected net margin, ROI and declared preparation-cost exposure.
- **Opportunity Score:** weighted Market Score, Dealer Score, listing freshness and data
  completeness.

The remaining configured Market and Dealer factors stay missing until Market Intelligence and
Preparation Intelligence provide real evidence.

## Priority bands

| Opportunity Score | Label | Meaning |
|---|---|---|
| 80–100 | Priority | Review first. |
| 60–79.99 | Requires analysis | Potentially interesting, but incomplete or borderline. |
| 0–59.99 | Low priority | Do not prioritise without new evidence. |

Every snapshot stores `scoring-v1`, normalized factor weights, factor contributions, explanations
and missing factors. Recalculation appends a snapshot; it never overwrites an earlier decision.

Appending a new price observation automatically updates the expected purchase price (when its
currency matches the opportunity), recalculates expected profit and appends fresh score snapshots.
