# Market Valuation v1

Market Valuation estimates a vehicle's likely retail price from comparable active listings.
It is separate from Market Score: valuation produces money and a confidence range, while
scoring produces a 0–100 decision signal.

For the same make and model, v1 selects listings within two model years and 60,000 km,
normalizes prices for year and mileage, and uses the median adjusted price. The expected
sale price is the estimate minus a conservative 4% discount. Default preparation costs are
versioned per currency.

Every calculation appends a `ValuationSnapshot` containing the estimate, low/high range,
sample size, confidence, configuration version, and explanation. A later calculation never
rewrites history. Dealer-entered expected sale prices take precedence over automatic values.

Confidence thresholds are explicit: 2–3 comparables is low, 4–7 medium, and 8+ high.
