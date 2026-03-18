
import subprocess, json, html

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True)
    except:
        return ""

def run_json(cmd):
    try:
        return json.loads(run(cmd))
    except:
        return {}

report = {}

nodes = run_json("kubectl get nodes -o json")
pvc = run_json("kubectl get pvc -A -o json")
pods = run_json("kubectl get pods -A -o json")

report["node_count"] = len(nodes.get("items", []))
report["pvc_count"] = len(pvc.get("items", []))

# Get Kubernetes version
version_info = run_json("kubectl version -o json")
server_version = version_info.get("serverVersion", {}).get("gitVersion", "Unknown")
report["kubernetes_version"] = server_version

# Get CRDs
crds = run_json("kubectl get crd -o json")
report["crd_count"] = len(crds.get("items", []))
report["crds"] = [crd["metadata"]["name"] for crd in crds.get("items", [])]

# Get Kasten K10 namespace(s)
namespaces = run_json("kubectl get ns -o json")
k10_namespaces = []
for ns in namespaces.get("items", []):
    name = ns["metadata"].get("name", "")
    if "kasten" in name or "k10" in name:
        k10_namespaces.append(name)

if not k10_namespaces:
    # Fallback: detect K10 deployment namespaces by label selectors
    deployments = run_json("kubectl get deploy -A -l app=k10 -o json")
    for d in deployments.get("items", []):
        ns = d["metadata"].get("namespace")
        if ns and ns not in k10_namespaces:
            k10_namespaces.append(ns)

k10_namespaces = sorted(set(k10_namespaces))

# Get RBAC objects for Kasten K10 only
roles = {"items": []}
role_bindings = {"items": []}
service_accounts = {"items": []}
for ns in k10_namespaces:
    roles_ns = run_json(f"kubectl get role -n {ns} -o json")
    role_bindings_ns = run_json(f"kubectl get rolebinding -n {ns} -o json")
    sa_ns = run_json(f"kubectl get sa -n {ns} -o json")
    roles["items"].extend(roles_ns.get("items", []))
    role_bindings["items"].extend(role_bindings_ns.get("items", []))
    service_accounts["items"].extend(sa_ns.get("items", []))

cluster_roles_all = run_json("kubectl get clusterrole -o json")
cluster_role_bindings_all = run_json("kubectl get clusterrolebinding -o json")

cluster_roles = {
    "items": [cr for cr in cluster_roles_all.get("items", []) if "kasten" in cr["metadata"].get("name", "").lower() or "k10" in cr["metadata"].get("name", "").lower()]
}

cluster_role_bindings = {
    "items": [
        crb for crb in cluster_role_bindings_all.get("items", [])
        if "kasten" in crb["metadata"].get("name", "").lower()
        or "k10" in crb["metadata"].get("name", "").lower()
        or any(
            (subj.get("namespace") in k10_namespaces or "kasten" in subj.get("name", "").lower() or "k10" in subj.get("name", "").lower())
            for subj in crb.get("subjects", [])
        )
        or "kasten" in crb.get("roleRef", {}).get("name", "").lower()
        or "k10" in crb.get("roleRef", {}).get("name", "").lower()
    ]
}

report["rbac"] = {
    "k10_namespaces": k10_namespaces,
    "role_count": len(roles.get("items", [])),
    "role_binding_count": len(role_bindings.get("items", [])),
    "cluster_role_count": len(cluster_roles.get("items", [])),
    "cluster_role_binding_count": len(cluster_role_bindings.get("items", [])),
    "service_account_count": len(service_accounts.get("items", [])),
    "roles": [f"{r['metadata'].get('namespace','<cluster>')}/{r['metadata'].get('name','')}" for r in roles.get("items", [])],
    "role_bindings": [f"{rb['metadata'].get('namespace','<cluster>')}/{rb['metadata'].get('name','')}" for rb in role_bindings.get("items", [])],
    "cluster_roles": [cr['metadata'].get('name','') for cr in cluster_roles.get("items", [])],
    "cluster_role_bindings": [crb['metadata'].get('name','') for crb in cluster_role_bindings.get("items", [])],
    "service_accounts": [f"{sa['metadata'].get('namespace','')}/{sa['metadata'].get('name','')}" for sa in service_accounts.get("items", [])],
}

stateful_images = []
db_patterns = ["postgres","mongo","redis","kafka","mysql","cassandra","elastic"]

for pod in pods.get("items", []):
    for c in pod["spec"].get("containers", []):
        img = c.get("image","").lower()
        for p in db_patterns:
            if p in img:
                stateful_images.append({
                    "namespace": pod["metadata"]["namespace"],
                    "image": img
                })

report["stateful_platforms"] = stateful_images

try:
    snaps = run_json("kubectl get volumesnapshotclass -o json")
    report["snapshot_support"] = len(snaps.get("items", [])) > 0
except:
    report["snapshot_support"] = False

# Include helper command snippets for Kasten K10
try:
    with open("commands.md", "r") as f:
        report["commands_md"] = f.read().strip()
except Exception:
    report["commands_md"] = ""

with open("cluster_inventory.json","w") as f:
    json.dump(report,f,indent=2)

# Generate a standalone HTML report with embedded commands
try:
    with open("report_template.html", "r") as f:
        tpl = f.read()
    commands_html = html.escape(report.get("commands_md", ""))
    report_html = tpl.replace("{{COMMANDS}}", commands_html)
    with open("report.html", "w") as f:
        f.write(report_html)
except Exception:
    pass

# Run Kasten K10 primer
print("Running Kasten K10 primer...")
try:
    subprocess.run("curl https://docs.kasten.io/downloads/8.3.5/tools/k10_primer.sh | bash", shell=True, check=True)
    print("K10 primer completed.")
except subprocess.CalledProcessError as e:
    print(f"K10 primer failed: {e}")

print("Scan complete -> cluster_inventory.json and report.html")
