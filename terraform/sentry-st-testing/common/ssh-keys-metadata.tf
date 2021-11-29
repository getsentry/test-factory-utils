locals {
  ssh_keys = {
    "anton" = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/BNYIBOXMjkL602WoD56/VwYopJDLmVSRssS+PorzYXuaXUPCHwLIKKgqkhbnWs16xTckcF5ET/aQHtC1HrW3oo962ZpgkBEO+o4ZyB37rpIEUDGO5YkJYU3MI90XlnnyjggTBhJLrhA+inHAFtg82fHbxDXATLfiBWX8l6p2/oPCbKQPRsfS9WkGur2AjKL8y6qWU5QUvraMz4pZbH9sWbH33111MizF/TIvHlwhjS5KFHpqZ3A+Ty584YbPS2u5NzdfYZhTXfHx1VqqUW3ddo9I9X0ZEqGXRrJFpH5pBQJe9yo6rkmLZqAOg7opsRCjPc7W9rXLPb09ociVC0iZ anton"
    # "radu"  = ""
  }

  ssh_users = concat(
    formatlist("%s:%s", keys(local.ssh_keys), values(local.ssh_keys)),
  )
  ssh_metadata_value = join("\n", local.ssh_users)
}


resource "google_compute_project_metadata_item" "ssh_metadata" {
  key   = "ssh-keys"
  value = local.ssh_metadata_value
}
