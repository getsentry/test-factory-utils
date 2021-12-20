start = {start}
stop = {stop}
q = {quantile}


// 1 second as a float value ( it is 10^9 ns)
sec = float(v: int( v: 1s))
// convert from duration to seconds, returns a float
toSeconds = (v) => float(v: int(v: v))/sec

windowPeriod = 10s // ideally that should be max(10s, v.windowPeriod)

from(bucket: "statsd")
  |> range(start: start, stop: stop)
  |> filter(fn: (r) => r["_measurement"] == "relay_processing_event_produced")
  |> filter(fn: (r) => r["_field"] == "value")
  |> group(columns: ["event_type"], mode: "by")
  |> aggregateWindow(every: windowPeriod, fn: sum, createEmpty: false)
  |> toFloat()
  |> map(fn: (r) => ({{ r with _value: r._value / toSeconds(v: windowPeriod) }}))
  |> quantile(q: q)
