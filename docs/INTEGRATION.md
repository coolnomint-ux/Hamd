# Wonderlife / dot integration foundation

## Current scope

The GitHub connector can read and write this repository. The repository provides an offline CSV consistency checker; it is not a running bridge or a scheduler. No direct dot/Work dispatch tool was available in the implementation session. Existing schedules and production records were not modified.

Google Sheets remains the operational source of truth. Do not copy private queue instructions, media references, computer paths, task-session identifiers or logs into this public repository.

## Local audit

Requires Python 3; uses only the standard library, with no network calls or paid APIs.

Export the existing Agent_Queue and Agent_Log tabs as CSV into a private local folder outside this repository. Run:

```sh
python tools/audit_queue.py --queue /path/to/private/Agent_Queue.csv --log /path/to/private/Agent_Log.csv
python -m unittest discover -s tests
```

The program prints a JSON report to stdout and never edits the inputs. Treat output as private because it includes request/event identifiers. It checks required headers, missing or duplicate IDs, budget values, missing scopes and log references. A missing Evidence URL requires manual review of the summary: it does not mean that evidence is absent. Logs may refer to requests outside a partial export; that finding is a warning, not proof of a bad record.

Exit codes: 0 = no structural errors detected (warnings may remain); 1 = structural errors found; 2 = invalid/unreadable input. None of these means that a task executed or that approval was granted. Nonzero budgets always require review; no approval is inferred from arbitrary cell text.

## Operational boundary

1. Keep existing Agent_Queue, Agent_Log and schedules; do not create duplicate requests or retry active tasks.
2. Before dispatch, establish an actually supported native dot/Work action and its allowed scope.
3. Confirm whether the request already has an active or completed run.
4. Use one request ID across submission, receipt, actual execution and result evidence.
5. Mark completion only after checking the real output; distinguish reported evidence from independent verification.
6. Preserve production approvals and originals. Paid work, publication and external uploads require explicit owner authorization.

## Next integration gate

A native dispatch capability and a verifiable result-return path are required before implementing automatic execution. GitHub commits and spreadsheet updates alone do not provide that capability. Existing operational rules can be stale relative to newer logs; reconcile them only with verified evidence and owner authorization, not by enabling a flag in this repository.
