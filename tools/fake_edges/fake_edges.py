"""Fake edge nodes: a fleet of simulated edges that send violation events to the cloud over MQTT, with no cameras and
no model. For demos and load tests.

  provision   makes the fleet in the cloud (a cluster, N nodes, K cameras each) and writes fleet.json
  run         every node of fleet.json connects to the broker as its own user and sends events at random

The broker needs a user per node (name = node id, same password for the whole fleet):
  bash docs/mosquitto/add-users.sh <password> edge-sim-01 edge-sim-02 ...     (or `users` below prints the command)

  python tools/fake_edges/fake_edges.py provision --api http://localhost:8200 --admin-password ... --nodes 12
  python tools/fake_edges/fake_edges.py users --nodes 12
  python tools/fake_edges/fake_edges.py run --host localhost --port 8883 --ca volume/mosquitto/certs/ca.crt --password ...
"""

import argparse
import json
import os
import random
import signal
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import httpx
import numpy as np

HERE = Path(__file__).resolve()
# From the repository (tools/fake_edges/), or from the image (edge_link copied next to the script).
for candidate in (HERE.parent / "edge_link/src", *(p / "package/edge_link/src" for p in HERE.parents)):
    if candidate.exists():
        sys.path.insert(0, str(candidate))
        break

from edge_link import EventPublisher, ViolationMessage  # noqa: E402

VIOLATIONS = ("no_helmet", "no_vest", "no_gloves", "no_safety_boots")
WEIGHTS = (0.4, 0.3, 0.2, 0.1)  # helmets are missed the most
# A 1x1 JPEG, for when OpenCV is not installed.
_TINY_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc2000b080001000101011100ffc4001410010000000000"
    "00000000000000000000000000ffda0008010100013f10ffd9"
)


def snapshot(node: str, camera: int, violation: str) -> bytes:
    """A placeholder frame that says where and what, so the dashboard has something to show."""
    frame = np.full((360, 640, 3), 32, dtype=np.uint8)
    cv2.rectangle(frame, (4, 4), (635, 355), (60, 70, 80), 1)
    cv2.putText(frame, "FAKE EDGE", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80, 160, 220), 2)
    cv2.putText(frame, f"{node}  cam {camera}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (220, 220, 220), 2)
    cv2.putText(frame, violation, (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (60, 72, 229), 3)
    cv2.putText(frame, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), (20, 330),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (140, 150, 160), 1)
    ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return jpeg.tobytes() if ok else _TINY_JPEG


def node_names(count: int, prefix: str) -> list[str]:
    width = max(2, len(str(count)))
    return [f"{prefix}-{i:0{width}d}" for i in range(1, count + 1)]


# ---------------------------------------------------------------- provision

def provision(args: argparse.Namespace) -> None:
    with httpx.Client(base_url=args.api, timeout=30) as http:
        token = http.post("/api/auth/login", json={"username": args.admin_user, "password": args.admin_password})
        token.raise_for_status()
        http.headers["Authorization"] = f"Bearer {token.json()['access_token']}"

        def listing(path: str) -> list[dict]:
            r = http.get(path)
            r.raise_for_status()
            return r.json()

        def ensure(path: str, existing: list[dict], body: dict) -> dict:
            for item in existing:
                if item["name"] == body["name"] and all(item.get(k) == v for k, v in body.items() if k.endswith("_id")):
                    return item
            r = http.post(path, json=body)
            r.raise_for_status()
            return r.json()

        cluster = ensure("/api/v1/clusters", listing("/api/v1/clusters"), {"name": args.cluster})
        nodes, cameras = listing("/api/v1/nodes"), listing("/api/v1/cameras")
        fleet: dict[str, list[int]] = {}
        for name in node_names(args.nodes, args.prefix):
            node = ensure("/api/v1/nodes", nodes, {
                "name": name, "cluster_id": cluster["id"], "max_cameras": max(16, args.cameras),
                "description": "Fake edge", "ip_address": None,
            })
            ids = []
            for k in range(1, args.cameras + 1):
                camera = ensure("/api/v1/cameras", cameras, {"name": f"{name}-cam-{k}", "node_id": node["id"]})
                ids.append(camera["id"])
            fleet[name] = ids
    Path(args.fleet).parent.mkdir(parents=True, exist_ok=True)
    Path(args.fleet).write_text(json.dumps(fleet, indent=2), encoding="utf-8")
    print(f"{len(fleet)} nodes, {sum(len(v) for v in fleet.values())} cameras in cluster {args.cluster!r} -> {args.fleet}")


def users(args: argparse.Namespace) -> None:
    names = node_names(args.nodes, args.prefix)
    print(f"bash docs/mosquitto/add-users.sh '<password>' {' '.join(names)}")


# ---------------------------------------------------------------- run

def run(args: argparse.Namespace) -> None:
    fleet: dict[str, list[int]] = json.loads(Path(args.fleet).read_text(encoding="utf-8"))
    publishers = {
        node: EventPublisher(node, args.host, args.port, node, args.password, tls_ca=args.ca) for node in fleet
    }
    for publisher in publishers.values():
        publisher.start()
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    sent = 0
    started = time.time()
    # one timeline for the whole fleet: events arrive as a Poisson stream with `interval` seconds per node on average
    rate = len(fleet) / args.interval
    print(f"{len(fleet)} fake edges -> {args.host}:{args.port}, about {rate:.1f} events/s. Ctrl-C to stop.")
    while not stop.is_set() and (not args.duration or time.time() - started < args.duration):
        if stop.wait(random.expovariate(rate)):
            break
        node = random.choice(list(fleet))
        camera = random.choice(fleet[node])
        violation = random.choices(VIOLATIONS, WEIGHTS)[0]
        publishers[node].send(ViolationMessage(
            event_id=uuid.uuid4().hex, node_id=node, camera_id=camera, violation_type=violation,
            confidence=random.uniform(0.45, 0.98), occurred_at=datetime.now(timezone.utc).isoformat(),
            video_ts_sec=random.uniform(0, 600), snapshot_jpeg=snapshot(node, camera, violation),
        ))
        sent += 1
        if sent % 50 == 0:
            print(f"{sent} events sent")
    for publisher in publishers.values():
        publisher.stop()
    print(f"stopped after {sent} events")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles are not UTF-8
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--fleet", default=os.environ.get("FAKE_FLEET", "volume/data/fake-edges/fleet.json"))
        p.add_argument("--nodes", type=int, default=12)
        p.add_argument("--prefix", default="edge-sim")

    p = sub.add_parser("provision", help="create the nodes and cameras in the cloud")
    common(p)
    p.add_argument("--api", default=os.environ.get("FAKE_API", "http://localhost:8200"))
    p.add_argument("--admin-user", default=os.environ.get("FAKE_ADMIN_USER", "admin"))
    p.add_argument("--admin-password", default=os.environ.get("FAKE_ADMIN_PASSWORD"), required="FAKE_ADMIN_PASSWORD" not in os.environ)
    p.add_argument("--cluster", default="Giả lập edge")
    p.add_argument("--cameras", type=int, default=3, help="cameras per node")
    p.set_defaults(func=provision)

    p = sub.add_parser("users", help="print the command that makes the broker users")
    common(p)
    p.set_defaults(func=users)

    p = sub.add_parser("run", help="send events")
    common(p)
    p.add_argument("--host", default=os.environ.get("FAKE_MQTT_HOST", "localhost"))
    p.add_argument("--port", type=int, default=int(os.environ.get("FAKE_MQTT_PORT", "8883")))
    p.add_argument("--ca", default=os.environ.get("FAKE_MQTT_CA", "volume/mosquitto/certs/ca.crt"))
    p.add_argument("--password", default=os.environ.get("FAKE_MQTT_PASSWORD"), required="FAKE_MQTT_PASSWORD" not in os.environ)
    p.add_argument("--interval", type=float, default=10.0, help="mean seconds between events of one node")
    p.add_argument("--duration", type=float, default=0, help="stop after this many seconds (0: until Ctrl-C)")
    p.set_defaults(func=run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
