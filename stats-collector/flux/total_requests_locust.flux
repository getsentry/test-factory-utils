start = {start}
end = {stop}
q = {quantile}

from(bucket: "statsd")
  |> range(start: start, stop: end)
  |> filter(fn: (r) => r["_measurement"] == "locust_requests_current_rps" )
  |> filter(fn: (r) => r["_field"] == "gauge")
  |> filter(fn: (r) => r["name"] == "Aggregated")
  |> filter(fn: (r) => r["_value"] != 0)
  |> toFloat()
  |> quantile(q: q)
