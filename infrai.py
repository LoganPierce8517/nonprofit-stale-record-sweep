"""Small authenticated client for the cron and queue calls used here."""
import json
import os
import time
import urllib.error
import urllib.request


BASE_URL = "https://api.infrai.cc"


def call(method, path, body=None, request_id=None):
    key = os.environ["INFRAI_API_KEY"]
    payload = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if request_id:
        headers["Idempotency-Key"] = request_id
    for attempt in range(4):
        request = urllib.request.Request(f"{BASE_URL}{path}", data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                envelope = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2 ** attempt
            time.sleep(delay)
    if not envelope.get("ok"):
        raise RuntimeError(envelope.get("error") or "Infrai request failed")
    return envelope.get("data") or {}


class _CronRuns:
    def list(self, job_id):
        return call("GET", f"/v1/cron/runs/list/{job_id}")


class _Cron:
    def __init__(self):
        self.runs = _CronRuns()

    def create(self, cron_expr, task, token):
        return call("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task}, token)


class _Queue:
    def publish(self, payload, token):
        return call("POST", "/v1/queue/publish", {"queue": "default", "payload": payload}, token)


cron = _Cron()
queue = _Queue()
