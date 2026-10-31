"""Process-local offline and network guard, imported by Python before user code."""
from __future__ import annotations
import json, os, socket
from datetime import datetime, timezone
from pathlib import Path

for _name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "PYTHONDONTWRITEBYTECODE"):
    os.environ[_name] = "1"

_log = os.environ.get("PINNED_REPLAY_NETWORK_LOG")

def _blocked(operation, target=None):
    event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "operation": operation, "target": repr(target), "status": "BLOCKED_BY_PROCESS_GUARD"}
    if _log:
        path = Path(_log); path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
    raise RuntimeError("NETWORK_ATTEMPT_BLOCKED_BY_PROCESS_GUARD")

def _connect(self, address): return _blocked("socket.connect", address)
def _connect_ex(self, address): return _blocked("socket.connect_ex", address)
def _create_connection(address, *args, **kwargs): return _blocked("socket.create_connection", address)
def _getaddrinfo(host, *args, **kwargs): return _blocked("socket.getaddrinfo", host)

socket.socket.connect = _connect
socket.socket.connect_ex = _connect_ex
socket.create_connection = _create_connection
socket.getaddrinfo = _getaddrinfo
