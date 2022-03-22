# Example configuration file
# CONFIG_VERSION = "X.X.X" # sym version currently not used
#
# set_load_tester_url( url:str) # use to set the base url for the subsequent tests
# set_load_tester_url can be called multiple times, the last one called before any
# add_XXX_test will be used
#
# add_locust_test(duration:str|duration, users:int,  spawn_rate:int|None=None,
#                 name:str|None=None,description:str|None=None, url:str|None=None,
#                 id:str|None=None)
#
# adds test to be run by a locust load tester
#
# add_vegeta_test(duration:str|duration, test_type: str, freq:int, per:str|duration,
#        config:dict, name:str|None=None, description:str|None=None)
#
# adds a test to be run by a vegeta load tester (not the default vegeta load tester
# but our (Sentry) webservice wrapper
#


CONFIG_VERSION = "1.0.0"
LOCUST_URL = "http://locust_server"
VEGETA_URL = "http://vegeta_server"


def add_locust_tests():
    add_locust_test(
        duration=duration("10m"),
        users=30,
        spawn_rate=None,
        name="warmup"
    )
    add_locust_test(
        duration="11m",
        users=40,
        spawn_rate=4,
        name="second",
        description="duration passed as string"
    )
    add_locust_test(
        duration="12m",
        users=50,
        name="third",
        description="override the load tester server",
        url="http://special_locust_server"
    )

    add_locust_test("10m5s", 22, description="positional params")

    for num_users in range(20, 100, 20):
        add_locust_test(
            url=LOCUST_URL,
            users=num_users,
            duration=duration("10m"),
            name="a lot of releases with %d users" % num_users
        )


def add_vegeta_tests():
    add_vegeta_test(
        duration=duration("5m1s"),
        test_type = "session",
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
        name="session",
        description="vegeta test description"

    )


# setup some locust tests
set_load_tester_url(LOCUST_URL)
add_locust_tests()

# setup some vegeta tests
set_load_tester_url(VEGETA_URL)
add_vegeta_tests()
