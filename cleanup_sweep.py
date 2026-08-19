"""Periodic cleanup for donor receipts, volunteer reminders, and campaign reports."""
import os
from datetime import date, timedelta

import infrai


SWEEP_URL = os.environ.get("SWEEP_URL", "https://example.org/nonprofit/cleanup")


def stale_records(records, today):
    """Return records whose retention date is before the sweep date."""
    return [record for record in records if record["retain_until"] < today]


def publish_cleanup(records, today=None):
    today = today or date.today().isoformat()
    stale = stale_records(records, today)
    for record in stale:
        payload = {"record_id": record["record_id"], "kind": record["kind"], "action": "remove"}
        infrai.queue.publish(payload, f"cleanup-{record['record_id']}")
    return {"swept": len(stale), "kept": len(records) - len(stale)}


def schedule_sweep():
    """Ask Infrai to call the cleanup endpoint every Monday at 02:00 UTC."""
    job = infrai.cron.create("0 2 * * 1", SWEEP_URL, "nonprofit-cleanup-weekly")
    return job["job_id"]


if __name__ == "__main__":
    sample = [
        {"record_id": "receipt-104", "kind": "donor_receipt", "retain_until": (date.today() - timedelta(days=1)).isoformat()},
        {"record_id": "volunteer-22", "kind": "volunteer_reminder", "retain_until": (date.today() + timedelta(days=7)).isoformat()},
        {"record_id": "campaign-spring", "kind": "campaign_report", "retain_until": (date.today() - timedelta(days=3)).isoformat()},
    ]
    print(publish_cleanup(sample))
    print("scheduled:", schedule_sweep())
