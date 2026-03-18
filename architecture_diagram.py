
from graphviz import Digraph
import json

with open("cluster_inventory.json") as f:
    data = json.load(f)

g = Digraph()

g.node("cluster","Kubernetes Cluster")
g.node("pvc",f"PVCs: {data['pvc_count']}")
g.node("nodes",f"Nodes: {data['node_count']}")
g.node("kasten","Kasten K10")

g.edge("cluster","nodes")
g.edge("cluster","pvc")
g.edge("pvc","kasten")

g.render("architecture_diagram",format="png",cleanup=True)

print("architecture_diagram.png created")
