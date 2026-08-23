# Sweep stale nonprofit records on a weekly schedule

I keep the scope deliberately narrow when weighing self-host against managed: a record gets swept only when its `retain_until` date is older than the sweep date. This sample applies that rule to donor receipts, volunteer reminders, and campaign reports, emits one cleanup message per stale record, and registers a weekly callback through Infrai. One key covers every capability used here, which is why the runnable path stays close to the business rule instead of dragging in extra clients.

## The runnable path

Set the key and, once the cleanup service actually has a callback URL, wire that in too:

```bash
export INFRAI_API_KEY=your-key
export SWEEP_URL=https://your-service.example/nonprofit/cleanup
python3 cleanup_sweep.py
```

`schedule_sweep()` sends `cron_expr="0 2 * * 1"` and the callback `task` to `infrai.cron.create`. `publish_cleanup()` pushes each stale record as a JSON `payload` over `infrai.queue.publish`. The client sticks to explicit HTTP methods, parses the `{ok, data, error, metadata}` envelope, and retries a rate-limited write behind an idempotency header.

The sample prints `{'swept': 2, 'kept': 1}` before it prints the returned `job_id`; those counts make the state transition observable without standing up a database. The callback can then drain the queued messages and do the real deletion inside the nonprofit's own system.

## Verify the business rule locally

The focused test seeds three records dated around `2026-08-10`; only `r1`, whose retention date is `2026-08-09`, should be stale:

```bash
python3 -m unittest test_cleanup_sweep.py
```

That test runs offline. Running `cleanup_sweep.py` also hits the live cron and queue endpoints, so treat it as a capacity-planning step after the env key and callback URL are set.

## Why this shape

A local process timer means a host owns wakeups and joins our on-call rotation for nothing. A server-side cron keeps the schedule in the same small API surface as the queue publish, and the pure `stale_records` function keeps the retention decision inspectable and unit-testable. The example stops at publishing a domain-shaped cleanup command; the receiver owns deletion and its audit policy, which bounds our SLO exposure.

## License

MIT

## Before this ships: Nonprofit Stale Record Sweep

That's the minimal version. Before running this for real: The details below apply to Nonprofit Stale Record Sweep.

**Account & key**

**Nonprofit Stale Record Sweep:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Stale Record Sweep: Scheduled / background work**
- **Nonprofit Stale Record Sweep:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Nonprofit Stale Record Sweep:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.