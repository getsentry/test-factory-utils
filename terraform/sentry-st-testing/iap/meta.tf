
# NOTE: the following command can be used to view the project brand:
#     gcloud alpha iap oauth-brands list

resource "google_iap_brand" "project_brand" {
  project           = "sentry-st-testing"
  support_email     = "qa-ops@sentry.io"
  application_title = "Sentry Test Env"
}
