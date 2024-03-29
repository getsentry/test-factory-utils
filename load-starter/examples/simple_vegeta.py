CONFIG_VERSION = "1.0.0"
VEGETA_URL = "http://localhost:7770"

def add_vegeta_tests():
    add_sleep("10s")
    add_vegeta_test(
        duration=duration("1m"),
        test_type="session",
        name="warm-up",
        description="load the caches",
        freq=22,
        per=duration("1s"),
        config={
            "startedRange": "1m",
            "durationRange": "2m",
            "numReleases": 3,
            "numEnvironments": 4,
            "numUsers": 5,
            "okWeight": 6,
            "exitedWeight": 7,
            "erroredWeight": 8,
            "crashedWeight": 9,
            "abnormalWeight": 10
        },
        produce_report=False,
        labels=(("l1", "v1"), ("l2", "v2"))
    )
    add_vegeta_test(
        duration=duration("30s"),
        test_type="session",
        name="Test title",
        description="Some test",
        freq=22,
        per=duration("1s"),
        config={
            "startedRange": "1m",
            "durationRange": "2m",
            "numReleases": 3,
            "numEnvironments": 4,
            "numUsers": 5,
            "okWeight": 6,
            "exitedWeight": 7,
            "erroredWeight": 8,
            "crashedWeight": 9,
            "abnormalWeight": 10
        },
        labels={"ll1":"v1", "ll2":"v2"}
    )
    add_sleep(duration("20s"))


# setup some vegeta tests
set_load_tester_url(VEGETA_URL)
add_vegeta_tests()

# --->report result:
# {
#     "startTime": "",
#     "name": "",
#     "desc": "",
#     "duration":"",
#     "spec": {
#         "numMessages":"",
#         "per":"",
#         "params": {}
#     }
# }
#
# {
#     "startTime": "",
#     "name": "",
#     "desc": "",
#     "duration":"",
#     "spec": {
#         "users": 33,
#         "rampup": 10
#     }
#}
