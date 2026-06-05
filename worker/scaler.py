"""
scaler.py — Dynamic Worker Scaler
===================================
Monitors Redis queue depth and auto-scales worker subprocesses.

Scaling policy:
  - MIN_WORKERS = 1 (always keep at least one)
  - MAX_WORKERS = 4 (upper bound)
  - SCALE_UP_THRESHOLD  = 3  → spawn another worker if queue has >= 3 tasks
  - SCALE_DOWN_THRESHOLD = 0 → kill an idle worker if queue empty for 30s

Usage:
    python worker/scaler.py

Environment variables:
    MIN_WORKERS          (default: 1)
    MAX_WORKERS          (default: 4)
    SCALE_UP_THRESHOLD   (default: 3)
    SCALE_DOWN_DELAY     (default: 30)
    REDIS_HOST/PORT/DB   (default: localhost:6379/0)
"""

import json
import os
import signal
import socket
import subprocess
import sys
import time

import redis

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
MIN_WORKERS = int(os.environ.get("SCALER_MIN_WORKERS", "1"))
MAX_WORKERS = int(os.environ.get("SCALER_MAX_WORKERS", "4"))
SCALE_UP_THRESHOLD = int(os.environ.get("SCALER_UP_THRESHOLD", "3"))
SCALE_DOWN_DELAY = int(os.environ.get("SCALER_DOWN_DELAY", "30"))
QUEUE_NAMES = ["inference_tasks:high", "inference_tasks:default", "inference_tasks:low"]
POLL_INTERVAL = 5


def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


def total_queue_depth(r: redis.Redis) -> int:
    total = 0
    for q in QUEUE_NAMES:
        total += r.llen(q)
    return total


class Scaler:
    def __init__(self):
        self.workers: list[subprocess.Popen] = []
        self._idle_since: float | None = None
        self._running = True

    def _worker_path(self) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "worker.py")

    def spawn_worker(self) -> subprocess.Popen:
        proc = subprocess.Popen(
            [sys.executable, self._worker_path()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(f"[SCALER] Spawned worker (PID {proc.pid}) — {len(self.workers) + 1}/{MAX_WORKERS}")
        return proc

    def kill_idlest_worker(self):
        for proc in self.workers:
            if proc.poll() is None:
                os.kill(proc.pid, signal.SIGTERM)
                print(f"[SCALER] Killed idle worker (PID {proc.pid})")
                self.workers.remove(proc)
                proc.wait(timeout=5)
                return
        print("[SCALER] No workers to kill (all already dead?)")

    def reap_dead_workers(self):
        self.workers = [p for p in self.workers if p.poll() is None]

    def run(self):
        r = get_redis()
        r.ping()
        print(f"[SCALER] Connected. Min={MIN_WORKERS} Max={MAX_WORKERS} "
              f"UpThreshold={SCALE_UP_THRESHOLD} DownDelay={SCALE_DOWN_DELAY}s")

        # Start with minimum workers
        for _ in range(MIN_WORKERS):
            self.workers.append(self.spawn_worker())

        while self._running:
            try:
                self.reap_dead_workers()
                depth = total_queue_depth(r)

                # Scale up
                if depth >= SCALE_UP_THRESHOLD and len(self.workers) < MAX_WORKERS:
                    print(f"[SCALER] Queue depth {depth} ≥ threshold {SCALE_UP_THRESHOLD} — scaling up")
                    self.workers.append(self.spawn_worker())
                    self._idle_since = None

                # Scale down
                if depth == 0:
                    if self._idle_since is None:
                        self._idle_since = time.time()
                    elif time.time() - self._idle_since >= SCALE_DOWN_DELAY:
                        if len(self.workers) > MIN_WORKERS:
                            print(f"[SCALER] Queue empty for {SCALE_DOWN_DELAY}s — scaling down")
                            self.kill_idlest_worker()
                            self._idle_since = None
                else:
                    self._idle_since = None

                print(f"[SCALER] Workers: {len(self.workers)} | Queue depth: {depth}")
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[SCALER] Error: {e}")
                time.sleep(POLL_INTERVAL)

        self.shutdown()

    def shutdown(self):
        print("[SCALER] Shutting down all workers...")
        for proc in self.workers:
            if proc.poll() is None:
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=5)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        os.kill(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        print("[SCALER] Done.")


if __name__ == "__main__":
    scaler = Scaler()
    try:
        scaler.run()
    except KeyboardInterrupt:
        scaler.shutdown()
