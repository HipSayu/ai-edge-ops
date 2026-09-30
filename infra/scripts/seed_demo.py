"""Seed demo fleet data into the Cloud through its REST API (so it lands in Postgres via the real services).

    python infra/scripts/seed_demo.py --url http://<cloud-host> --key <CLOUD_API_KEYS entry> [--sims 4]
    python infra/scripts/seed_demo.py --url ... --key ... --deploy-runtimes   # once the sims are online

Creates 4 clusters with 9 nodes. The first node of each cluster is backed by a simulated edge agent
(infra/scripts/edge-sim.sh); its identity is written to infra/compose/edge-sim/sim-<i>.env.
The other nodes have no agent and stay REGISTERED. Re-running is safe: existing items are reused.
`--deploy-runtimes` then deploys a lightweight placeholder runtime (nginx) to every online sim.
"""

import argparse
import pathlib
import sys

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[2]
SIM_SECRETS = ROOT / "infra" / "compose" / "edge-sim"
# Sims join the cloud compose network, where the broker is `mqtt`
SIM_MQTT_HOST = "mqtt"

# PPE (personal protective equipment) compliance monitoring on 4 construction sites (one FL client each).
# `conditions` = what the site's camera data looks like; `ppe_rules` = what each zone enforces.
CLUSTERS = [
    {
        "name": "Công trường A - Thi công móng/hầm",
        "location": "Công trường A",
        "description": "Giám sát PPE khu thi công móng và tầng hầm: nhiều bùn đất, ánh sáng nhân tạo/thiếu sáng, camera nhìn ngang",
        "metadata": {"site_code": "CT-A", "client": 1, "industry": "construction", "phase": "foundation",
                     "conditions": ["mud", "low_light", "artificial_light", "eye_level_view"],
                     "timezone": "Asia/Ho_Chi_Minh", "demo": True},
        "nodes": [
            ("Hố móng", {"zone": "Hố móng", "cameras": 4, "hardware": "Jetson Orin NX 16GB",
                         "ppe_rules": ["helmet", "safety_vest", "safety_shoes"]}),
            ("Tầng hầm B1", {"zone": "Tầng hầm B1", "cameras": 4, "hardware": "Jetson Orin NX 16GB",
                             "ppe_rules": ["helmet", "safety_vest", "safety_shoes"]}),
            ("Lối lên dốc hầm", {"zone": "Lối lên dốc hầm", "cameras": 2, "hardware": "Intel NUC 13 + RTX A2000",
                                 "ppe_rules": ["helmet", "safety_vest"]}),
        ],
    },
    {
        "name": "Công trường B - Nhà cao tầng",
        "location": "Công trường B",
        "description": "Giám sát PPE thi công nhà cao tầng: ánh sáng tự nhiên chói gắt, nhiều gió, camera nhìn từ cẩu tháp xuống (top-down)",
        "metadata": {"site_code": "CT-B", "client": 2, "industry": "construction", "phase": "high_rise",
                     "conditions": ["harsh_sunlight", "wind", "top_down_view"],
                     "timezone": "Asia/Ho_Chi_Minh", "demo": True},
        "nodes": [
            ("Cẩu tháp", {"zone": "Camera cẩu tháp", "cameras": 3, "hardware": "Jetson AGX Orin 32GB",
                          "ppe_rules": ["helmet", "safety_vest", "safety_harness"]}),
            ("Sàn thi công", {"zone": "Sàn thi công tầng trên", "cameras": 4, "hardware": "Jetson Orin Nano 8GB",
                              "ppe_rules": ["helmet", "safety_harness"]}),
        ],
    },
    {
        "name": "Công trường C - Hoàn thiện nội thất",
        "location": "Công trường C",
        "description": "Giám sát PPE giai đoạn hoàn thiện nội thất: mật độ công nhân đông, không gian hẹp, che khuất lẫn nhau nhiều",
        "metadata": {"site_code": "CT-C", "client": 3, "industry": "construction", "phase": "interior_finishing",
                     "conditions": ["crowded", "narrow_space", "occlusion"],
                     "timezone": "Asia/Ho_Chi_Minh", "demo": True},
        "nodes": [
            ("Hành lang tầng", {"zone": "Hành lang tầng", "cameras": 6, "hardware": "x86 + RTX 4000 Ada",
                                "ppe_rules": ["helmet", "safety_vest"]}),
            ("Khu căn hộ mẫu", {"zone": "Khu căn hộ mẫu", "cameras": 4, "hardware": "Jetson Orin NX 8GB",
                                "ppe_rules": ["helmet", "gloves"]}),
        ],
    },
    {
        "name": "Công trường D - Thi công đường giao thông",
        "location": "Công trường D",
        "description": "Giám sát PPE thi công ngoài trời/đường giao thông: không gian rộng, nhiều bụi, máy móc di chuyển, ánh sáng thay đổi, công nhân nhỏ và dễ bị che khuất",
        "metadata": {"site_code": "CT-D", "client": 4, "industry": "construction", "phase": "road_works",
                     "conditions": ["wide_area", "dust", "moving_machinery", "variable_light", "small_objects",
                                    "occlusion"],
                     "timezone": "Asia/Ho_Chi_Minh", "demo": True},
        "nodes": [
            ("Mặt đường thi công", {"zone": "Mặt đường thi công", "cameras": 6, "hardware": "Jetson AGX Orin 32GB",
                                    "ppe_rules": ["helmet", "safety_vest"]}),
            ("Bãi máy móc", {"zone": "Bãi tập kết máy móc", "cameras": 3, "hardware": "Jetson Orin NX 16GB",
                             "ppe_rules": ["helmet", "safety_vest", "restricted_zone"]}),
        ],
    },
]

# Names used by earlier versions of this seed -> current names (see --rename)
LEGACY_NAMES = {
    **dict.fromkeys(["hanoi-factory", "ppe-hanoi-assembly-plant", "Nhà máy Bắc Thăng Long"],
                    "Công trường A - Thi công móng/hầm"),
    **dict.fromkeys(["hcm-warehouse", "ppe-hcm-logistics-hub", "Kho vận Tân Tạo"], "Công trường B - Nhà cao tầng"),
    **dict.fromkeys(["danang-port", "ppe-danang-port", "Cảng Tiên Sa"], "Công trường C - Hoàn thiện nội thất"),
    **dict.fromkeys(["hn-line-a-01", "hn-assembly-line-a", "Dây chuyền lắp ráp A"], "Hố móng"),
    **dict.fromkeys(["hn-line-b-01", "hn-assembly-line-b", "Dây chuyền lắp ráp B"], "Tầng hầm B1"),
    **dict.fromkeys(["hn-gate-01", "hn-main-gate", "Cổng chính"], "Lối lên dốc hầm"),
    **dict.fromkeys(["hcm-dock-01", "hcm-loading-dock", "Khu bốc xếp"], "Cẩu tháp"),
    **dict.fromkeys(["hcm-aisle-01", "hcm-forklift-aisle", "Làn xe nâng"], "Sàn thi công"),
    **dict.fromkeys(["dn-crane-01", "dn-crane-zone", "Khu cẩu trục"], "Hành lang tầng"),
    **dict.fromkeys(["dn-yard-01", "dn-container-yard", "Bãi container"], "Khu căn hộ mẫu"),
}


def node_metadata(spec: dict, name: str) -> dict:
    """A node's seeded metadata plus its code <site_code>-<nn> (e.g. CT-A-01), by position in the cluster."""
    names = [node_name for node_name, _ in spec["nodes"]]
    return {**dict(spec["nodes"])[name], "code": f"{spec['metadata']['site_code']}-{names.index(name) + 1:02d}"}


class CloudClient:
    def __init__(self, url: str, key: str) -> None:
        self._http = httpx.Client(base_url=f"{url.rstrip('/')}/api/v1", headers={"Authorization": f"Bearer {key}"},
                                  timeout=20)

    def get(self, path: str, **params):
        r = self._http.get(path, params=params)
        r.raise_for_status()
        return r.json()

    def patch(self, path: str, body: dict) -> dict:
        r = self._http.patch(path, json=body)
        r.raise_for_status()
        return r.json()

    def create(self, path: str, body: dict) -> tuple[dict | None, int]:
        r = self._http.post(path, json=body)
        if r.status_code == 409:
            return None, 409
        r.raise_for_status()
        return r.json(), r.status_code


def seed(cloud: CloudClient, sims: int) -> list[dict]:
    existing = {c["name"]: c for c in cloud.get("/clusters")}
    sim_nodes = []
    for spec in CLUSTERS:
        cluster, _ = cloud.create("/clusters", {k: spec[k] for k in ("name", "location", "description", "metadata")})
        cluster = cluster or existing[spec["name"]]
        print(f"cluster {cluster['name']:<40} {cluster['id']}")
        nodes = {n["name"]: n for n in cloud.get("/nodes", cluster_id=cluster["id"])}
        for index, (name, metadata) in enumerate(spec["nodes"]):
            node, _ = cloud.create("/nodes", {"cluster_id": cluster["id"], "name": name,
                                              "metadata": {**node_metadata(spec, name), "simulated": index == 0}})
            node = node or nodes[name]
            print(f"  node {name:<14} {node['id']}  {'<- sim' if index == 0 else ''}")
            if index == 0:
                sim_nodes.append(node)
    return sim_nodes[:sims]


def write_sim_env(sim_nodes: list[dict]) -> None:
    SIM_SECRETS.mkdir(parents=True, exist_ok=True)
    for i, node in enumerate(sim_nodes, start=1):
        path = SIM_SECRETS / f"sim-{i}.env"
        path.write_text(
            f"EDGE_CLUSTER_ID={node['cluster_id']}\n"
            f"EDGE_NODE_ID={node['id']}\n"
            f"EDGE_MQTT_HOST={SIM_MQTT_HOST}\n"
            "EDGE_MQTT_PORT=1883\n"
            "EDGE_LOG_JSON=true\n"
            "EDGE_AGENT_VERSION=0.1.0-sim\n",
            encoding="utf-8", newline="\n",
        )
        print(f"wrote {path.relative_to(ROOT)} ({node['name']})")


def deploy_runtimes(cloud: CloudClient) -> None:
    deployed = {(d["node_id"], d["spec"].get("name")) for d in cloud.get("/deployments")}
    for node in cloud.get("/nodes"):
        # Only the demo sims run it (agents started elsewhere may have no Docker)
        if node["status"] != "ONLINE" or not (node["agent_version"] or "").endswith("-sim"):
            continue
        if (node["id"], "ppe-detector") in deployed:
            print(f"runtime already on {node['name']}")
            continue
        # Placeholder image: small and always pullable; stands in for the PPE runtime in demos
        body = {"node_id": node["id"], "name": "ppe-detector", "image_uri": "nginx", "image_tag": "1.27-alpine",
                "config": {"demo": True, "model": "yolov8n-ppe", "target_fps": 15},
                "resource_limits": {"cpus": "100m", "memory": "64Mi"}}
        deployment, status = cloud.create("/deployments", body)
        print(f"deploy -> {node['name']}: {deployment['status'] if deployment else status}")


def rename(cloud: CloudClient) -> None:
    """Moves items seeded under LEGACY_NAMES to the current names/content via PATCH (ids kept, agents unaffected)."""

    def current(name: str) -> str:
        return LEGACY_NAMES.get(name, name)

    specs = {spec["name"]: spec for spec in CLUSTERS}
    for cluster in cloud.get("/clusters"):
        spec = specs.get(current(cluster["name"]))
        if spec is None:
            continue
        body = {k: spec[k] for k in ("name", "location", "description")}
        body["metadata"] = {k: v for k, v in cluster["metadata"].items() if k != "site"} | spec["metadata"]
        cloud.patch(f"/clusters/{cluster['id']}", body)
        print(f"cluster {cluster['name']} -> {spec['name']}")
        node_specs = dict(spec["nodes"])
        for node in cloud.get("/nodes", cluster_id=cluster["id"]):
            name = current(node["name"])
            if name not in node_specs:
                continue
            cloud.patch(f"/nodes/{node['id']}", {"name": name, "metadata": node["metadata"] | node_metadata(spec, name)})
            print(f"  node {node['name']} -> {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="Cloud base URL, e.g. http://ec2-...amazonaws.com")
    parser.add_argument("--key", help="a service API key (CLOUD_API_KEYS)")
    parser.add_argument("--sims", type=int, default=4, help="simulated edge agents to prepare (max 4)")
    parser.add_argument("--deploy-runtimes", action="store_true", help="deploy the demo runtime to sim nodes")
    parser.add_argument("--rename", action="store_true",
                        help="rename items from earlier seeds to the current names/content (PATCH, ids kept)")
    args = parser.parse_args()

    if not (args.url and args.key):
        parser.error("--url and --key are required")
    cloud = CloudClient(args.url, args.key)
    if args.rename:
        rename(cloud)
    elif args.deploy_runtimes:
        deploy_runtimes(cloud)
    else:
        write_sim_env(seed(cloud, args.sims))
    return 0


if __name__ == "__main__":
    sys.exit(main())
