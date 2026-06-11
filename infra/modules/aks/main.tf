# ──────────────────────────────────────────────────────────────────────────────
# Module: AKS – Stub Cluster
#
# This is a minimal AKS configuration for the lab to illustrate the deployment
# pattern.  It is NOT production-grade.
#
# CPS-managed Kubernetes note:
#   In real MSI environments, Kubernetes clusters are typically provisioned and
#   managed by the Cloud Platform Services (CPS) team.  Application teams
#   receive a namespace and RBAC bindings rather than owning the cluster.  This
#   stub is provided for architectural reference only.
# ──────────────────────────────────────────────────────────────────────────────

resource "azurerm_kubernetes_cluster" "lab" {
  name                = "${var.project_prefix}-aks-${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  dns_prefix          = "${var.project_prefix}-aks-${var.suffix}"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_DS2_v2"

    upgrade_settings {
      max_surge = "10%"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
