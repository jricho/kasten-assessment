
import json

with open("cluster_inventory.json") as f:
    data = json.load(f)

score = {}

score["backup"] = 2
score["snapshot"] = 4 if data["snapshot_support"] else 1
score["dr"] = 1
score["cyber"] = 1
score["automation"] = 2

overall = sum(score.values())/len(score)

result = {
    "scores": score,
    "overall_score": round(overall,2)
}

with open("maturity_scorecard.json","w") as f:
    json.dump(result,f,indent=2)

print("maturity_scorecard.json generated")
