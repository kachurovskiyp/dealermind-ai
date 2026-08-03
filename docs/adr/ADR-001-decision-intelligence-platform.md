# ADR-001: Build a decision-intelligence platform

- Status: Accepted
- Date: 2026-08-03

## Context

The business needs market monitoring, acquisition analysis, preparation tracking, cross-market profitability and explainable recommendations. A chatbot-first or scraper-first architecture would couple the product to interfaces and external websites.

## Decision

DealerMind AI will be built in three layers:

1. Data Platform
2. Decision Engine
3. AI Copilot

Core business calculations remain deterministic. AI is used for extraction, normalization assistance, explanation and natural-language interaction.

## Consequences

- Domain and event history are designed before UI.
- External marketplace collectors are adapters.
- Recommendations must be reproducible.
- Development starts with lifecycle data and scoring foundations.
