# Link Intake v1

Link Intake is a user-directed adapter for previewing a real listing URL before it enters the
DealerMind domain.

```text
Public URL → network safety checks → JSON-LD / Open Graph extraction
→ editable preview → user confirmation → Market Intelligence import
```

## Principles

- Preview is side-effect free; it writes nothing to the database.
- The user confirms and can correct every extracted value.
- JSON-LD and Open Graph metadata are preferred over marketplace-specific HTML selectors.
- Confirmed links enter through the existing import service, so offer identity, VIN reuse, price
  history, Opportunity creation and Ranking v1 behave exactly like file and scheduled imports.
- Repeating the same link updates or leaves the existing offer unchanged instead of duplicating it.

## Network boundaries

- Only HTTP and HTTPS URLs are accepted.
- DNS is resolved before every request and redirect.
- Loopback, private, link-local and reserved addresses are rejected.
- Redirects are limited to three and are not followed implicitly.
- Only HTML responses up to 2 MB are processed.
- The adapter identifies itself with a dedicated user agent and is intended for user-requested
  previews, not uncontrolled crawling.

Extraction quality depends on metadata published by the source page. Missing make, model, price or
currency is reported as a warning and must be filled manually before confirmation.
