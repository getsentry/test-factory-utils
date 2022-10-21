from mongo_data import MeasurementInfo, get_measurements, AggregationInfo


def test_get_measurements():
    docs = [
        {
            "results": {
                "measurements": {
                    "cpu_usage": {"mean": 1, "q05": 2, "max": 4},
                    "ram_usage": {"mean": 1, "q051": 2, "q091": 3, "max": 4},
                }
            }
        },
        {
            "results": {
                "measurements": {
                    "cpu_usage": {"q05": 2, "q09": 3, "max": 4},
                    "disc_usage": {"mean": 1, "q05": 2, "max": 4},
                }
            }
        },
        {
            "results": {
                "measurements": {
                    "net_usage": {"mean": 1, "max": 4},
                }
            }
        },
    ]

    measurements = get_measurements(docs)

    assert set([m.name for m in measurements]) == {
        "cpu_usage",
        "ram_usage",
        "net_usage",
        "disc_usage",
    }

    for measurement in measurements:
        assert isinstance(measurement, MeasurementInfo)
        assert measurement.name in ["cpu_usage", "ram_usage", "net_usage", "disc_usage"]
        if measurement.name == "cpu_usage":
            assert set(measurement.aggregations) == {
                AggregationInfo(id="q05", name="q05", description=None),
                AggregationInfo(id="q09", name="q09", description=None),
                AggregationInfo(id="max", name="max", description=None),
                AggregationInfo(id="mean", name="mean", description=None),
            }
        elif measurement.name == "ram_usage":
            assert set(measurement.aggregations) == {
                AggregationInfo(id="q051", name="q051", description=None),
                AggregationInfo(id="q091", name="q091", description=None),
                AggregationInfo(id="max", name="max", description=None),
                AggregationInfo(id="mean", name="mean", description=None),
            }
        elif measurement.name == "net_usage":
            assert set(measurement.aggregations) == {
                AggregationInfo(id="max", name="max", description=None),
                AggregationInfo(id="mean", name="mean", description=None),
            }
        elif measurement.name == "disc_usage":
            assert set(measurement.aggregations) == {
                AggregationInfo(id="q05", name="q05", description=None),
                AggregationInfo(id="max", name="max", description=None),
                AggregationInfo(id="mean", name="mean", description=None),
            }


def test_measurements_metadata():
    docs = [
        {
            "results": {
                "_meta": {
                    "measurements": {
                        "cpu_usage": {
                            "aggregations": {
                                "mean": {
                                    "name": "mean_extended",
                                    "description": "some description",
                                }
                            },
                            "unit": "cores",
                            "name": "CPU Usage",
                            "description": "CPU Usage in cores",
                        },
                        "ram_usage": {},
                    }
                },
                "measurements": {
                    "cpu_usage": {"mean": 1, "max": 4},
                },
            }
        }
    ]

    measurements = get_measurements(docs)

    assert measurements == [
        MeasurementInfo(
            id="cpu_usage",
            aggregations=[
                AggregationInfo(id="max", name="max", description=None),
                AggregationInfo(
                    id="mean", name="mean_extended", description="some description"
                ),
            ],
            name="CPU Usage",
            description="CPU Usage in cores",
            unit="cores",
            bigger_is_better=False,
        )
    ]
