
# List all repositories
kubectl get storagerepositories.kio.kasten.io -n kasten-io

# List all namespace-based Restorepoints
kubectl get restorepoints -A -l '!k10.kasten.io/addType'

# List all VM-based RestorePoints
kubectl get restorepoints -A -l k10.kasten.io/appType=virtualMachine

# List all discovered applications
kubectl get applications.apps.kio.kasten.io -A

# List all Profiles
kubectl get profiles.config.kio.kasten.io -n kasten-io

# List all Policies
kubectl get policies.config.kio.kasten.io -n kasten-io

# List all ActionSets
kubectl get actionsets -n kasten-io

# List all Blueprints
kubectl get blueprints.cr.kanister.io -n kasten-io
