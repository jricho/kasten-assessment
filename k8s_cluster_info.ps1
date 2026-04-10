# k8s_cluster_info.ps1
# PowerShell native version for Windows
# Usage: .\k8s_cluster_info.ps1

function Write-Section {
    param([string]$Title)
    Write-Host "`n$Title" -ForegroundColor Cyan -BackgroundColor Black -NoNewline
    Write-Host "`n$('-' * 60)" -ForegroundColor DarkGray
}

function Write-Subsection {
    param([string]$Title)
    Write-Host "`n$Title" -ForegroundColor Yellow
    Write-Host "`n$('-' * 40)" -ForegroundColor DarkGray
}

Write-Section "[ℹ️] ==== Kubernetes Cluster Info ===="

Write-Section "[⚙️] Kubernetes Version"
kubectl version --short 2>$null

Write-Section "[🚀] Nodes"
kubectl get nodes -o wide 2>$null

Write-Section "[🐳] Pods"
kubectl get pods -A -o wide 2>$null

Write-Section "[📁] PersistentVolumeClaims (PVCs)"
kubectl get pvc -A -o wide 2>$null

Write-Section "[📝] CustomResourceDefinitions (CRDs)"
kubectl get crd 2>$null

Write-Section "[🚧] CSI Drivers"
kubectl get csidriver 2>$null

Write-Section "[🚧] CSI Nodes"
kubectl get csinodes 2>$null

Write-Section "[📊] VolumeSnapshotClass"
kubectl get volumesnapshotclass 2>$null

Write-Section "[🔖] Kasten K10 Namespaces"
kubectl get ns | Select-String -Pattern 'kasten|k10' -SimpleMatch

Write-Section "[⚙️] ClusterRoles (kasten/csi/k10)"
kubectl get clusterrole 2>$null | Select-String -Pattern 'kasten|csi|k10' -SimpleMatch

Write-Section "[⚙️] ClusterRoleBindings (kasten/csi/k10)"
kubectl get clusterrolebinding 2>$null | Select-String -Pattern 'kasten|csi|k10' -SimpleMatch

if (kubectl get ns | Select-String 'kasten-io') {
    Write-Subsection "[💾] Kasten K10 Inventory"
    $resources = @(
        'storagerepositories.kio.kasten.io',
        'restorepoints',
        'applications.apps.kio.kasten.io',
        'profiles.config.kio.kasten.io',
        'policies.config.kio.kasten.io',
        'actionsets',
        'blueprints.cr.kanister.io'
    )
    foreach ($r in $resources) {
        Write-Host "Resource: $r" -ForegroundColor Magenta
        kubectl get $r -A 2>$null
        Write-Host ""
    }
    Write-Subsection "[💾] RestorePoints (namespace-based)"
    kubectl get restorepoints -A -l '!k10.kasten.io/addType' 2>$null
    Write-Subsection "[💾] RestorePoints (VM-based)"
    kubectl get restorepoints -A -l k10.kasten.io/appType=virtualMachine 2>$null
}

Write-Section "[ℹ️] ==== End of Report ===="
