# IP address for all IAP-protected services
resource "google_compute_global_address" "iap_ingress_address" {
  name    = "iap-ingress-address"
  project = local.project

  lifecycle {
    prevent_destroy = true
  }
}
