#!/usr/bin/env python3
"""Offline, read-only audit of Agent_Queue and Agent_Log CSV exports."""
import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation

QUEUE_HEADERS = ["Request ID", "Project", "Scene/Task", "Created by", "Assigned to",
                 "Instruction / Deliverable", "Status", "Evidence URL",
                 "Permission Scope", "Max USD", "Owner Approval", "Updated (UTC)"]
LOG_HEADERS = ["Event ID", "Request ID", "From", "To", "Event Type", "Summary",
               "Evidence URL", "Timestamp (UTC)"]

def read_csv(path, required):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = [name for name in required if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("Missing columns: " + ", ".join(missing))
        rows = []
        for row in reader:
            if not any(str(v or "").strip() for v in row.values()):
                continue
            if None in row:
                raise ValueError("CSV row has more values than headers")
            rows.append({key: (value or "").strip() for key, value in row.items()})
        return rows

def audit(queue, logs):
    findings = []
    def flag(level, kind, identifier):
        findings.append({"level": level, "kind": kind, "id": identifier})
    for rows, key in ((queue, "Request ID"), (logs, "Event ID")):
        counts = Counter(row.get(key, "") for row in rows)
        if counts.get("", 0):
            flag("error", "missing_" + key.replace(" ", "_").lower(), "")
        for identifier, count in counts.items():
            if identifier and count > 1:
                flag("error", "duplicate_" + key.replace(" ", "_").lower(), identifier)
    known = {row.get("Request ID", "") for row in queue} - {""}
    references = {row.get("Request ID", "") for row in logs} - {""}
    for row in logs:
        if row.get("Request ID", "") not in known:
            flag("warning", "log_request_not_in_supplied_queue", row.get("Event ID", ""))
        if not row.get("Evidence URL", ""):
            flag("review", "no_evidence_url_review_summary_manually", row.get("Event ID", ""))
    for row in queue:
        identifier = row.get("Request ID", "")
        try:
            amount = Decimal(row.get("Max USD", ""))
            if not amount.is_finite() or amount < 0:
                raise InvalidOperation
            if amount > 0:
                flag("warning", "nonzero_budget_requires_explicit_review", identifier)
        except InvalidOperation:
            flag("error", "invalid_budget", identifier)
        if identifier not in references:
            flag("review", "no_log_in_supplied_export", identifier)
        if not row.get("Permission Scope", ""):
            flag("error", "missing_permission_scope", identifier)
        if not row.get("Owner Approval", ""):
            flag("review", "missing_owner_approval", identifier)
    return {"mode": "offline_read_only", "queue_rows": len(queue),
            "log_rows": len(logs), "findings": findings,
            "execution_verified": False,
            "note": "CSV consistency only. A log, status, or URL does not prove execution. "
                    "No task dispatch, authorization, or completion is inferred."}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--log", required=True)
    args = parser.parse_args()
    try:
        result = audit(read_csv(args.queue, QUEUE_HEADERS), read_csv(args.log, LOG_HEADERS))
    except (OSError, ValueError, csv.Error, UnicodeError):
        print(json.dumps({"error": "Cannot read valid CSV files with the required headers."}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if any(f["level"] == "error" for f in result["findings"]) else 0

if __name__ == "__main__":
    raise SystemExit(main())
