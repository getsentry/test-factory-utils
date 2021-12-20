start = {start}
stop = {stop}
q = {quantile}

from(bucket: "statsd")
  |> range(start: start, stop: stop)
  |> filter(fn: (r) => r["_measurement"] == "relay_event_processing_time")
  |> filter(fn: (r) => r["_field"] == "upper")
  |> group(columns: [], mode: "by")
  |> quantile(q: q)
