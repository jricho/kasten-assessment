
# Kubernetes Enterprise Assessment Toolkit

Designed for Veeam / Kasten pre‑sales discovery.

## Workflow

1. Run cluster scan

python advanced_scanner.py

2. Generate architecture diagram

python architecture_diagram.py

3. Generate maturity score

python maturity_scorecard.py

Outputs:

cluster_inventory.json
architecture_diagram.png
maturity_scorecard.json

These files can be used to produce an executive assessment report.
