# Vehicle Knowledge Base v1

The knowledge base separates factory facts, observed market facts and reviewed judgement. These kinds of information must not be conflated.

Profiles are versioned per model generation and market. A recommendation remains `unreviewed` until evidence is attached. Missing evidence is rendered visibly; the UI must not silently convert folklore or a price correlation into a mechanical reliability claim.

The pilot catalog is file-backed YAML so changes are reviewable in Git. A later editorial workflow may project the same schema into the database while retaining append-only revisions and citations.

## Focus catalog linkage

The Poland focus catalog is the source of truth for the coverage list. On every read,
DealerMind compares catalog makes and models with reviewed knowledge profiles. A model
added to the catalog appears immediately as an automatically generated `draft` profile.
It intentionally contains no engine claims, reliability verdicts or sources. A reviewed
YAML profile for the same make and model supersedes that placeholder, while retaining the
catalog tier (`core` or `review`). This makes catalog expansion visible without silently
inventing automotive knowledge.
