# geoipupdate

Repo: https://github.com/getsentry/docker-geoipupdate

geoipupdate is a DaemonSet which runs in the `sentry-system` namespace as a system level provided tool.

geoipupdate's entire purpose is to lay down our GeoIP system data, and keep it up to date.

It involves mounting a volume from the Node's host, in `/mnt/stateful_partition` (this is the only writable path on the host), in which other Deployments and Pods are able to mount back in and use the data there.

There is a ConfigMap which contains our license key. In theory this is a secret, but in practice for us, it's very low on the security threshold and not worth protecting. It's been in source control since it's inception.

See all of the `geoip_*` macros from within `sentry-kube --list-macros`. You most likely want to pair all of them together.

### Note

Copied from https://github.com/getsentry/ops/tree/master/k8s/services/geoipupdate
