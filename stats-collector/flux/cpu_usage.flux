start = {start}
stop = {stop}
q = {quantile}

from(bucket: "statsd")
  |> range(start: start, stop: stop)
  |> filter(fn: (r) => r["_measurement"] == "kubernetes_pod_container")
  |> filter(fn: (r) => r["_field"] == "cpu_usage_nanocores")
  |> filter(fn: (r) => r["container_name"] == "relay")
  |> toFloat()
  |> quantile(q: q)
  |> map(fn: (r) => ({{
      r with
      _value: r._value / 1000000000.0
    }})
  )
