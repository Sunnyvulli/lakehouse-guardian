# Independent technical review requested

**Status: awaiting an independent human review.** Test results, automated analysis and author self-review are not independent peer review, journal review or acceptance. No reviewer identity, affiliation or endorsement is claimed.

## Review the working change

The dimensional mart extends the existing approval-gated local lakehouse. After README setup, run `make test mart run`; run `make run` again and confirm `status: unchanged`. `make mart` writes source/model hashes, package versions, check statuses and the full monthly output to `results/mart.json`. The two mart integration tests execute dbt itself. Existing workflow tests cover approval refusal/hash mismatch.

Please comment on the linked public review issue or PR with the commit tested, environment, commands and observed result. State whether you have any collaboration/conflict with the owner. Negative findings are welcome; include a minimal failing example and expected behavior. Do not include personal or confidential data.

## Questions for a data engineer

1. Is one fact per dataset-wide date/hour defensible, and are missing hours correctly retained as unknown rather than zero?
2. Can the calendar/weather joins multiply or silently drop facts despite the tests? Provide a counterexample.
3. Do the independent fixture and four negative candidates catch meaningful defects? Which failure is still untested?
4. Is rentals per observed hour a useful descriptive metric, and are denominator and month-over-month limitations clear?
5. Is the temporary dbt gate before Iceberg publication sufficient for its stated local scope? What additional failure injection should precede a persistent incremental mart?

## Acceptance and response record

A response is recorded as independent technical feedback only when an identifiable external participant supplies an actual assessment. Preserve the original comment/link, reviewed commit, reproduced finding, resolution commit, regression evidence and unresolved limitation. Never convert a review invitation or passing CI into a peer-reviewed badge.

## External channels assessed

[Code Review Stack Exchange](https://codereview.stackexchange.com/help/on-topic) permits focused review of working code maintained by the requester; it requires a self-contained question with relevant code, not a request to inspect an entire repository. A focused question about fact grain and reconciliation would fit better than a whole-portfolio request. No post has been submitted there from this session because no posting connection/account is available.

[pyOpenSci scope](https://www.pyopensci.org/software-peer-review/about/package-scope.html) covers reusable scientific Python software and has packaging/scope requirements. This local portfolio reference is not represented as an accepted/in-scope package; a formal submission is not made merely to obtain an endorsement. No manuscript is submitted by this change. Primary guidance checked 2026-10-19.
