"""
cluster_worker.py — Distributed Cluster Worker Sidecar
=======================================================
Auto-connects to the coordinator, starts llama-rpc-server to
contribute this machine's compute to the cluster.

Usage:
    python cluster_worker.py --coordinator http://head-node:8050
"""

import argparse
import os
import subprocess
import sys
import time
import threading
import signal
import socket

import requests

DEFAULT_RPC_PORT = 5000
HEARTBEAT_INTERVAL = 10


def get_system_memory():
    vram_mb = 0
    ram_mb = 0

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            vrams = [int(x.strip()) for x in result.stdout.strip().split("\n") if x.strip()]
            vram_mb = sum(vrams)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    if vram_mb == 0:
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                vram_mb += info.free // (1024 * 1024)
        except (ImportError, Exception):
            pass

    try:
        import psutil
        ram_mb = psutil.virtual_memory().available // (1024 * 1024)
    except ImportError:
        try:
            result = subprocess.run(
                ["free", "-m"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                parts = lines[1].split()
                ram_mb = int(parts[3])
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
            ram_mb = 0

    return vram_mb, ram_mb


def find_llama_rpc_server():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "llama-rpc-server"),
        os.path.join(script_dir, "..", "rpc-server"),
        "llama-rpc-server",
        "./llama-rpc-server",
        "rpc-server",
        "./rpc-server",
        os.path.expanduser("~/llama.cpp/build/bin/llama-rpc-server"),
        os.path.expanduser("~/llama.cpp/build/bin/rpc-server"),
        "/usr/local/bin/llama-rpc-server",
        "/usr/local/bin/rpc-server",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return os.path.abspath(c)
        try:
            subprocess.run([c, "--help"], capture_output=True, timeout=5)
            return c
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def log_resource_usage(prefix="[RESOURCES]"):
    vram_mb, ram_mb = get_system_memory()
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.3)
        ram_total = psutil.virtual_memory().total // (1024 * 1024)
        print(f"{prefix} CPU: {cpu}% | RAM: {ram_mb} MB free / {ram_total} MB total | VRAM: {vram_mb} MB free")
    except ImportError:
        print(f"{prefix} RAM free: {ram_mb} MB | VRAM free: {vram_mb} MB")


class ClusterWorker:
    def __init__(self, coordinator_url: str, rpc_port: int = DEFAULT_RPC_PORT,
                 llama_rpc_bin: str = None, label: str = ""):
        self.coordinator_url = coordinator_url.rstrip("/")
        self.rpc_port = rpc_port
        self.llama_rpc_bin = llama_rpc_bin or find_llama_rpc_server()
        self.label = label
        self.worker_id = None
        self.rpc_process = None
        self._running = False
        self._total_tokens = 0

    def start(self):
        hostname = socket.gethostname()

        if self.llama_rpc_bin:
            cmd = [self.llama_rpc_bin, "--host", "0.0.0.0", "--port", str(self.rpc_port)]
            print(f"[CLUSTER] Starting: {' '.join(cmd)}")
            self.rpc_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            threading.Thread(target=self._monitor_rpc_output, daemon=True).start()
            time.sleep(2)
        else:
            print(f"[CLUSTER] No llama-rpc-server binary found.")
            print(f"[CLUSTER] Run it manually on port {self.rpc_port}")

        vram_mb, ram_mb = get_system_memory()

        try:
            resp = requests.post(
                f"{self.coordinator_url}/api/v1/workers/register",
                json={
                    "host": hostname,
                    "port": self.rpc_port,
                    "vram_mb": vram_mb,
                    "ram_mb": ram_mb,
                    "label": self.label or f"worker-{hostname}",
                },
                timeout=10,
            )
            data = resp.json()
            self.worker_id = data["worker_id"]
            print(f"[CLUSTER] Registered. ID: {self.worker_id}")
            print(f"[CLUSTER] VRAM: {vram_mb} MB, RAM: {ram_mb} MB")
        except requests.RequestException as e:
            print(f"[CLUSTER] Registration failed: {e}")
            return

        self._running = True
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

        log_resource_usage()
        print(f"[CLUSTER] Running. PID: {os.getpid()}, RPC port: {self.rpc_port}")

    def _monitor_rpc_output(self):
        for line in iter(self.rpc_process.stdout.readline, b''):
            if not line:
                break
            text = line.decode(errors="replace").rstrip()
            print(f"  [rpc] {text}")

    def _heartbeat_loop(self):
        while self._running:
            try:
                resp = requests.post(
                    f"{self.coordinator_url}/api/v1/workers/heartbeat",
                    json={"worker_id": self.worker_id},
                    timeout=5,
                )
                if resp.ok:
                    data = resp.json()
                    self._total_tokens = data.get("tokens_processed", self._total_tokens)
                    for report in data.get("reports", []):
                        prompt = report.get("prompt", "")
                        tokens = report.get("tokens", 0)
                        prompt_short = prompt[:80] + "..." if len(prompt) > 80 else prompt
                        print(f"[INFERENCE] +{tokens} tokens | Prompt: {prompt_short}")
            except requests.RequestException:
                pass

            log_resource_usage()
            status = "busy" if self._total_tokens > 0 else "idle"
            print(f"[CLUSTER] Status: {status} | Total tokens contributed: {self._total_tokens}")

            time.sleep(HEARTBEAT_INTERVAL)

    def stop(self):
        self._running = False
        print(f"[CLUSTER] Total tokens contributed this session: {self._total_tokens}")
        if self.worker_id:
            try:
                requests.delete(
                    f"{self.coordinator_url}/api/v1/workers/{self.worker_id}",
                    timeout=5,
                )
            except requests.RequestException:
                pass
        if self.rpc_process:
            self.rpc_process.terminate()
            self.rpc_process.wait(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Younify Cluster Worker Sidecar")
    parser.add_argument("--coordinator", default=os.environ.get("COORDINATOR_URL", "http://localhost:8050"))
    parser.add_argument("--rpc-port", type=int, default=int(os.environ.get("RPC_PORT", DEFAULT_RPC_PORT)))
    parser.add_argument("--label", default=os.environ.get("WORKER_LABEL", ""))
    parser.add_argument("--llama-rpc-bin", default=os.environ.get("LLAMA_RPC_BIN", ""))
    args = parser.parse_args()

    worker = ClusterWorker(
        coordinator_url=args.coordinator,
        rpc_port=args.rpc_port,
        llama_rpc_bin=args.llama_rpc_bin or None,
        label=args.label,
    )

    def _signal_handler(signum, frame):
        print("\n[CLUSTER] Shutting down...")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    worker.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        worker.stop()
