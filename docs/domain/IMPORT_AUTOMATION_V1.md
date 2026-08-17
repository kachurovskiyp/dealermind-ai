# Import Automation v1

`ImportSource` defines a trusted JSON endpoint, interval, enabled state and next execution time.
`ImportRun` records every attempt with trigger (`manual` or `schedule`), timestamps, import counters,
status and error details.

```text
due ImportSource → HTTP JSON fetch → ListingProvider → Market Intelligence
→ deduplication + price history → Opportunity Ranking → ImportRun
```

Run statuses:

- `completed`: every record succeeded;
- `partial`: valid records were imported and at least one record failed;
- `failed`: the source could not be fetched or its response was invalid.

Disabling a source clears its next execution time. Enabling it schedules the next run according to
its interval. Manual execution remains available for diagnosis. A failed source is not retried in a
tight loop; its next attempt follows the configured interval.

The local installation includes `/assets/automation-demo.json`. A source configured with
`http://localhost:8000/assets/automation-demo.json` exercises the entire scheduled pipeline without
an external dependency.
