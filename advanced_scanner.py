
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
report["nodes"] = [
    {
        "name": n["metadata"].get("name", ""),
        "labels": n["metadata"].get("labels", {}),
        "taints": n.get("spec", {}).get("taints", []),
        "status": n.get("status", {})
    }
    for n in nodes.get("items", [])
]
report["pvc_count"] = len(pvc.get("items", []))
report["pvcs"] = [
    {
        "name": p["metadata"].get("name", ""),
        "namespace": p["metadata"].get("namespace", ""),
        "status": p.get("status", {}).get("phase", ""),
        "storage_class": p.get("spec", {}).get("storageClassName", ""),
        "capacity": p.get("status", {}).get("capacity", {}).get("storage", "")
    }
    for p in pvc.get("items", [])
]
report["pods"] = [
    {
        "name": pod["metadata"].get("name", ""),
        "namespace": pod["metadata"].get("namespace", ""),
        "status": pod.get("status", {}).get("phase", ""),
        "node": pod.get("spec", {}).get("nodeName", ""),
        "containers": [c.get("name", "") for c in pod.get("spec", {}).get("containers", [])]
    }
    for pod in pods.get("items", [])
]

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

# Collect Kasten K10 inventory helper command output
k10_inventory = {
    "storagerepositories": run("kubectl get storagerepositories.kio.kasten.io -n kasten-io 2>/dev/null"),
    "restorepoints_namespace_based": run("kubectl get restorepoints -A -l '!k10.kasten.io/addType' 2>/dev/null"),
    "restorepoints_vm_based": run("kubectl get restorepoints -A -l k10.kasten.io/appType=virtualMachine 2>/dev/null"),
    "applications": run("kubectl get applications.apps.kio.kasten.io -A 2>/dev/null"),
    "profiles": run("kubectl get profiles.config.kio.kasten.io -n kasten-io 2>/dev/null"),
    "policies": run("kubectl get policies.config.kio.kasten.io -n kasten-io 2>/dev/null"),
    "actionsets": run("kubectl get actionsets -n kasten-io 2>/dev/null"),
    "blueprints": run("kubectl get blueprints.cr.kanister.io -n kasten-io 2>/dev/null"),
    "csidrivers": run("kubectl get csidriver 2>/dev/null"),
    "csinodes": run("kubectl get csinodes 2>/dev/null"),
}
report["k10_inventory"] = k10_inventory

with open("cluster_inventory.json","w") as f:
    json.dump(report,f,indent=2)

# Generate an HTML report from the template and embed all scanner output
try:
    with open("report_template.html", "r") as f:
        tpl = f.read()
    
    # Build K10 inventory section
    k10_content = []
    for label, text in report.get("k10_inventory", {}).items():
        output_text = text.strip() or "(none)"
        k10_content.append(f"<div class=\"k10-command-item\"><h3>{label.replace('_', ' ').title()}</h3><pre>{html.escape(output_text)}</pre></div>")
    if not k10_content:
        k10_content.append("<p>No Kasten K10 inventory data was collected.</p>")
    
    # Build cluster overview section
    cluster_overview = []
    # Nodes summary
    nodes_list = report.get('nodes', [])
    nodes_html = "\n".join([
        f"Name: {n['name']} | Labels: {n['labels']} | Taints: {n['taints']}" for n in nodes_list
    ]) or "(none)"
    cluster_overview.append(f"<div class=\"k10-command-item\"><h3>Nodes</h3><pre>{report.get('node_count', 0)}\n{html.escape(nodes_html)}</pre></div>")
    # PVCs summary
    pvcs_list = report.get('pvcs', [])
    pvcs_html = "\n".join([
        f"Name: {p['name']} | NS: {p['namespace']} | Status: {p['status']} | SC: {p['storage_class']} | Cap: {p['capacity']}" for p in pvcs_list
    ]) or "(none)"
    cluster_overview.append(f"<div class=\"k10-command-item\"><h3>PVCs</h3><pre>{report.get('pvc_count', 0)}\n{html.escape(pvcs_html)}</pre></div>")
    # Pods summary
    pods_list = report.get('pods', [])
    pods_html = "\n".join([
        f"Name: {pod['name']} | NS: {pod['namespace']} | Status: {pod['status']} | Node: {pod['node']} | Containers: {', '.join(pod['containers'])}" for pod in pods_list
    ]) or "(none)"
    cluster_overview.append(f"<div class=\"k10-command-item\"><h3>Pods</h3><pre>{html.escape(pods_html)}</pre></div>")
    # Kubernetes version
    cluster_overview.append(f"<div class=\"k10-command-item\"><h3>Kubernetes Version</h3><pre>{report.get('kubernetes_version', 'Unknown')}</pre></div>")
    # CRDs
    cluster_overview.append(f"<div class=\"k10-command-item\"><h3>CRDs Count</h3><pre>{report.get('crd_count', 0)}</pre></div>")
    crds_text = "\n".join(report.get('crds', [])) or "(none)"
    cluster_overview.append(f"<div class=\"k10-command-item\"><h3>CRD List</h3><pre>{html.escape(crds_text)}</pre></div>")
    # Snapshot support
    cluster_overview.append(f"<div class=\"k10-command-item\"><h3>Snapshot Support</h3><pre>{report.get('snapshot_support', False)}</pre></div>")
    
    # Build RBAC analysis section
    rbac = report.get("rbac", {})
    rbac_analysis = []
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>K10 Namespaces</h3><pre>{', '.join(rbac.get('k10_namespaces', [])) or '(none)'}</pre></div>")
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Roles Count</h3><pre>{rbac.get('role_count', 0)}</pre></div>")
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Role Bindings Count</h3><pre>{rbac.get('role_binding_count', 0)}</pre></div>")
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Cluster Roles Count</h3><pre>{rbac.get('cluster_role_count', 0)}</pre></div>")
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Cluster Role Bindings Count</h3><pre>{rbac.get('cluster_role_binding_count', 0)}</pre></div>")
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Service Accounts Count</h3><pre>{rbac.get('service_account_count', 0)}</pre></div>")
    roles_text = "\n".join(rbac.get('roles', [])) or "(none)"
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Roles</h3><pre>{html.escape(roles_text)}</pre></div>")
    role_bindings_text = "\n".join(rbac.get('role_bindings', [])) or "(none)"
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Role Bindings</h3><pre>{html.escape(role_bindings_text)}</pre></div>")
    cluster_roles_text = "\n".join(rbac.get('cluster_roles', [])) or "(none)"
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Cluster Roles</h3><pre>{html.escape(cluster_roles_text)}</pre></div>")
    cluster_role_bindings_text = "\n".join(rbac.get('cluster_role_bindings', [])) or "(none)"
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Cluster Role Bindings</h3><pre>{html.escape(cluster_role_bindings_text)}</pre></div>")
    service_accounts_text = "\n".join(rbac.get('service_accounts', [])) or "(none)"
    rbac_analysis.append(f"<div class=\"k10-command-item\"><h3>Service Accounts</h3><pre>{html.escape(service_accounts_text)}</pre></div>")
    
    # Build stateful platforms section
    stateful_platforms = []
    if report.get('stateful_platforms'):
        stateful_text = json.dumps(report.get('stateful_platforms', []), indent=2)
        stateful_platforms.append(f"<div class=\"k10-command-item\"><h3>Stateful Platforms</h3><pre>{html.escape(stateful_text)}</pre></div>")
    else:
        stateful_platforms.append("<div class=\"k10-command-item\"><h3>Stateful Platforms</h3><pre>(none)</pre></div>")
    
    # Replace all placeholders with actual values
    report_html = tpl
    # Fill summary bar placeholders
    report_html = report_html.replace("{{SUMMARY_NODES}}", str(report.get('node_count', 0)))
    report_html = report_html.replace("{{SUMMARY_PVCS}}", str(report.get('pvc_count', 0)))
    report_html = report_html.replace("{{SUMMARY_VERSION}}", str(report.get('kubernetes_version', 'Unknown')))
    report_html = report_html.replace("{{SUMMARY_CRDS}}", str(report.get('crd_count', 0)))
    report_html = report_html.replace("{{SUMMARY_SNAPSHOT}}", str(report.get('snapshot_support', False)))
    # Fill main sections
    report_html = report_html.replace("{{CLUSTER_OVERVIEW}}", "\n".join(cluster_overview))
    report_html = report_html.replace("{{RBAC_ANALYSIS}}", "\n".join(rbac_analysis))
    report_html = report_html.replace("{{STATEFUL_PLATFORMS}}", "\n".join(stateful_platforms))
    report_html = report_html.replace("{{K10_COMMANDS}}", "\n".join(k10_content))
    # Fill report date
    from datetime import datetime
    report_html = report_html.replace("{{REPORT_DATE}}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    with open("report.html", "w") as f:
        f.write(report_html)
except FileNotFoundError:
    print("WARNING: report_template.html not found. Skipping HTML report generation.")
except Exception as e:
    print(f"WARNING: Could not generate report.html: {e}")

print("Scan complete -> cluster_inventory.json and report.html")
