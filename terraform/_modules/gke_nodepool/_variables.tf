variable "name" {
  type        = string
  description = "public name for this node pool"
}

variable "label" {
  type        = string
  description = "label to target this node pool"
  default     = ""
}

variable "cluster" {
  type        = string
  description = "the gke cluster this node pool belongs too"
}

variable "project" {
  type        = string
  description = "gcp project to use"
  default     = "sentry-st-testing"
}

variable "region" {
  type        = string
  description = "name of the region to use"
  default     = "europe-west3"
}

variable "zone" {
  type        = string
  description = "suffix of the zone to use within a region"
  default     = "b"
}

variable "machine_type" {
  type        = string
  description = "size of instance (machine type) to use (default: n1-standard-1)"
  default     = "n2-standard-2"
}

variable "root_disk_type" {
  type        = string
  description = "type of disk for sda root (default: pd-standard)"
  default     = "pd-standard"
}

variable "root_disk_size_gb" {
  type        = string
  description = "the size od disk for sda root in GBs (default: 100)"
  default     = "100"
}

variable "min_node_count" {
  type        = string
  description = "the minimum number of nodes this pool can contain"
  default     = "1"
}

variable "max_node_count" {
  type        = string
  description = "the maximum number of nodes this pool can contain"
  default     = "10"
}

variable "min_cpu_platform" {
  type        = string
  description = "minimum CPU platform for VM instances"
  default     = "Intel Cascade Lake"
}

variable "initial_node_count" {
  type        = number
  description = "initial number of nodes in the pool"
  default     = 1
}

variable "metadata_mode" {
  type        = string
  description = "how to expose the node metadata to the workload running on the node. usual acceptable values for us are null and GKE_METADATA"
  default     = null
}

variable "taint_nodes" {
  type        = bool
  description = "should the nodes in the pool be tainted by a pool-specific key"
  default     = false
}

locals {
  resource_name = "${var.name}-${random_id.unique_id.hex}"
  label         = var.label != "" ? var.label : var.name
}
