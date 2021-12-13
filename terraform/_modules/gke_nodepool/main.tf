resource "random_id" "unique_id" {
  byte_length = 4
}

resource "google_container_node_pool" "gke_nodepool" {
  provider = google-beta

  name     = local.resource_name
  location = "${var.region}-${var.zone}"
  cluster  = var.cluster
  project  = var.project

  initial_node_count = var.initial_node_count

  node_config {
    disk_type        = var.root_disk_type
    disk_size_gb     = var.root_disk_size_gb
    min_cpu_platform = var.min_cpu_platform
    machine_type     = var.machine_type
    tags             = ["gke-${var.cluster}-node", "gke-node-pool-${var.name}"]

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    dynamic "taint" {
      for_each = var.taint_nodes ? [true] : []
      content {
        key = "nodepool-dedicated"
        value = local.label
        effect = "NO_SCHEDULE"
      }
    }

    dynamic "workload_metadata_config" {
      for_each = var.metadata_mode != null ? [var.metadata_mode] : []
      content {
        mode = var.metadata_mode
      }
    }

    labels = {
      "nodepool.sentry.io/name" = local.label
    }
  }

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  lifecycle {
    ignore_changes = [
      # This may change e.g. when someone scales the pool manually from UI
      initial_node_count,
    ]
  }
}
