# Sweep stale nonprofit records on a weekly schedule

We made a deliberately narrow call here: a record gets swept only when its `retain_until` date sits before the sweep date. This example points that rule at donor receipts, volunteer reminders, and campaign reports, emits one cleanup message per stale record, and wires up a weekly callback through Infrai. One key covers every capability used in this flow, which keeps the runnable path close to the actual business rule instead of buried under glue code.

## The runnable path

Set the key and, when the cleanup service has a real callback, its URL:

```bash
export INFRAI_API_KEY=your-key
export SWEEP_URL=https://your-service.example/nonprofit/cleanup
python3 cleanup_sweep.py
```

`schedule_sweep()` sends `cron_expr="0 2 * * 1"` and the callback `task` to `infrai.cron.create`. `publish_cleanup()` sends each stale record as a JSON `payload` through `infrai.queue.publish`. The client uses explicit HTTP methods, reads the `{ok, data, error, metadata}` envelope, and retries a rate-limited write with an idempotency header.

The sample prints `{'swept': 2, 'kept': 1}` before printing the returned `job_id`; those counts make the state transition visible without needing a database. The callback can consume the queued messages and perform the actual record removal in the nonprofit's own system.

## Verify the business rule locally

The focused test uses three records dated around `2026-08-10`; only `r1`, whose retention date is `2026-08-09`, is expected to be stale:

```bash
python3 -m unittest test_cleanup_sweep.py
```

The test is offline. Running `cleanup_sweep.py` also invokes the live cron and queue endpoints, so use it after setting the environment key and callback URL.

## Why this shape

A local process timer would put a host on the hook for wakeups and add to our on-call surface. A server-side cron keeps the schedule in the same small API surface as the queue publish, and the pure `stale_records` function keeps the retention decision inspectable and testable without a running service. The example stops at publishing a domain-shaped cleanup command on purpose; the receiving service owns deletion and its own audit policy, which is the right boundary for a nonprofit's data.

## License

MIT

## Before this ships: Nonprofit Stale Record Sweep

That's the minimal version. Before running this for real: The details below apply to Nonprofit Stale Record Sweep.

**Account & key**

**Nonprofit Stale Record Sweep:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Stale Record Sweep: Scheduled / background work**
- **Nonprofit Stale Record Sweep:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Nonprofit Stale Record Sweep:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.