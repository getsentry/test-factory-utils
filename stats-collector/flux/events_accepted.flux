sec = float(v: int( v: 1s))
// convert from duration to seconds, returns a float
toSeconds = (v) => float(v: int(v: v))/sec

start = {start}
stop = {stop}
windowPeriod = {windowPeriod}

from(bucket: "statsd")
  |> range(start: start, stop: stop)
  |> filter(fn: (r) => r["_measurement"] == "relay_event_accepted")
  |> filter(fn: (r) => r["_field"] == "value")
  |> group(columns: ["_measurement"], mode:"by")
  |> toFloat()
  |> aggregateWindow(every: windowPeriod, fn: sum, createEmpty: false)
  |> map(fn: (r) => ({{ r with _value: r._value / toSeconds(v: windowPeriod) }}))
  |> {func}()
