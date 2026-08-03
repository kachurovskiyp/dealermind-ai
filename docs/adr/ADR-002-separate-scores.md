# ADR-002: Separate Market, Dealer and Opportunity scores

- Status: Accepted
- Date: 2026-08-03

## Context

A vehicle may be attractive in a market but unsuitable for a dealer because of repair capacity, preparation delays, capital constraints or external-service dependence. A good vehicle may also be a poor opportunity at the current asking price.

## Decision

The platform will calculate and persist three independent scores:

- Market Score
- Dealer Score
- Opportunity Score

Each score is composed from versioned factors and weights. Combined recommendations reference the scores without collapsing their meaning.

## Consequences

- Different dealers can receive different Dealer Scores for the same offer.
- The same offer can receive different Market Scores for Poland and Ukraine.
- Historical results can calibrate each score independently.
