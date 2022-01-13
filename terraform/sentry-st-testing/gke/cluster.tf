resource "google_container_cluster" "cluster_1" {
  #   provider           = google-beta
  name               = "cluster-1"
  project            = local.project
  location           = "${local.region}-${local.zone}"
  network            = "default"
  subnetwork         = "default"
  min_master_version = "1.19.15"

  #   ip_allocation_policy {
  #     cluster_secondary_range_name  = "gke-zdpwkxst-pods"
  #     services_secondary_range_name = "gke-zdpwkxst-services"
  #   }

  #   private_cluster_config {
  #     enable_private_endpoint = true
  #     enable_private_nodes    = true
  #     master_ipv4_cidr_block  = "172.16.0.16/28"
  #     master_global_access_config {
  #       enabled = true
  #     }
  #   }

  #   master_authorized_networks_config {
  #     dynamic "cidr_blocks" {
  #       for_each = local.master_authorized_cidr_blocks

  #       content {
  #         cidr_block = cidr_blocks.value
  #       }
  #     }
  #   }

  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  workload_identity_config {
    workload_pool = "${local.project}.svc.id.goog"
  }

  initial_node_count = 0
  #   remove_default_node_pool = true
}

# # Default catch-all pool
# module "node_pool_zdpwkxst_default_01" {
#   source           = "../../_modules/gke_nodepool"
#   name             = "default-01"
#   label            = "default"
#   cluster          = google_container_cluster.gke_zdpwkxst.name
#   machine_type     = "n2-highcpu-16"
#   min_cpu_platform = "cascadelake"
#   min_node_count   = 1
#   max_node_count   = 32
#   node_metadata     = "GKE_METADATA_SERVER"
# }

# Dedicated pool for loads that we want to measure in isolation
module "node_pool_loads" {
  source           = "../../_modules/gke_nodepool"
  name             = "loads"
  label            = "loads"
  cluster          = google_container_cluster.cluster_1.name
  machine_type     = "n2-standard-8"
  min_cpu_platform = "Intel Cascade Lake"
  min_node_count   = 0
  max_node_count   = 2
  metadata_mode    = "GKE_METADATA"
  taint_nodes      = true
}

module "node_pool_ingest_load_tester" {
  source           = "../../_modules/gke_nodepool"
  name             = "ingest-load-tester"
  label            = "ingest-load-tester"
  cluster          = google_container_cluster.cluster_1.name
  machine_type     = "n2-standard-8"
  min_cpu_platform = "Intel Cascade Lake"
  min_node_count   = 0
  max_node_count   = 3
  metadata_mode    = "GKE_METADATA"
  taint_nodes      = true
}
