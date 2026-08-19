# Market Analytics UI v1

The collection progress banner makes a user-triggered comparable collection visible while
the synchronous v1 collector is working. It names the target vehicle and displays elapsed
time. Duplicate clicks are disabled until the request finishes.

`/market` is a read-only market evidence view. It shows aggregate counts, append-only
valuation history, comparable collection history, and the exact listing observations in
each collection. Comparable links open the original public listing in a new tab.

The dashboard reads dedicated `/api/v1/market-intelligence/*` endpoints and never mutates
valuation evidence.
