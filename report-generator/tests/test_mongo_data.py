from mongo_data import get_measurements, MeasurementInfo


def test_get_measurements():
    docs = [
        {"results": {"measurements": {
            "cpu_usage": {"mean": 1, "q05": 2, "max": 4},
            "ram_usage": {"mean": 1, "q051": 2, "q091": 3, "max": 4},
        }}},
        {"results": {"measurements": {
            "cpu_usage": {"q05": 2, "q09": 3, "max": 4},
            "disc_usage": {"mean": 1, "q05": 2, "max": 4},
        }}},
        {"results": {"measurements": {
            "net_usage": {"mean": 1, "max": 4},
        }}},
    ]

    measurements = get_measurements(docs)

    assert set([m.name for m in measurements]) == {"cpu_usage", "ram_usage", "net_usage", "disc_usage"}

    for measurement in measurements:
        assert isinstance(measurement, MeasurementInfo)
        assert measurement.name in ["cpu_usage", "ram_usage", "net_usage", "disc_usage"]
        if measurement.name == "cpu_usage":
            assert set(measurement.aggregations) == {"mean", "q05", "q09", "max"}
        elif measurement.name == "ram_usage":
            assert set(measurement.aggregations) == {"mean", "q051", "q091", "max"}
        elif measurement.name == "net_usage":
            assert set(measurement.aggregations) == {"mean", "max"}
        elif measurement.name == "disc_usage":
            assert set(measurement.aggregations) == {"mean", "q05", "max"}

