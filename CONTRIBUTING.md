# Contributing

Keep exploratory and confirmatory work separate. Any change to a frozen
confirmatory specification must be documented in `docs/DECISION_LOG.md` before
results from the affected analysis are inspected.

Reusable analysis belongs in `src/`; scripts should remain thin entry points.
Every new measurement or split procedure should include a unit test or a
synthetic construct-validity test. Never commit participant data or credentials.
