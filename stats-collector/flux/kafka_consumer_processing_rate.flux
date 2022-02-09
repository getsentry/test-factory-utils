start = {start}
stop = {stop}
q = {quantile}
consumer_group = "{consumer_group}"

from(bucket: "statsd")
  |> range(start: start, stop: stop)
  |> filter(fn: (r) => r["_measurement"] == "kafka_consumer_cur_offset")
  |> filter(fn: (r) => r["group"] == consumer_group)
  |> derivative(unit: 1s, nonNegative: false)
  |> toFloat()
  |> quantile(q: q)
