# Example configuration file
# CONFIG_VERSION = "X.X.X" # sym version currently not used
#
# Built-ins:
#
# set_load_tester_url( url:str)
#
#   Use to set the base url for the subsequent tests
#   set_load_tester_url can be called multiple times, the last one called before any
#   add_XXX_test will be used
#
# add_locust_test(duration:str|duration, users:int,  spawn_rate:int|None=None,
#                 name:str|None=None,description:str|None=None, url:str|None=None,
#                 id:str|None=None)
#
#   Adds test to be run by a Locust load tester.
#
# add_vegeta_test(duration:str|duration, test_type: str, freq:int, per:str|duration,
#                 config:dict, name:str|None=None, description:str|None=None)
#
#   Adds a test to be run by a vegeta load tester (not the default vegeta load tester
#   but our (Sentry) webservice wrapper.
#
# run_external(cmd:str[])
#
#   Runs an external script
#


CONFIG_VERSION = "1.0.0"
LOCUST_URL = "http://0.0.0.0:8089"
VEGETA_URL = "http://localhost:7770"


def add_vegeta_tests():
    add_vegeta_test(
        duration=duration("30s"),
        test_type="session",
        name="The test",
        description="Some test description",
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
            "abnormalWeight": 10,
        },
    )


def add_locust_tests():
    for users in range(20, 61, 20):
        add_locust_test(
            duration=duration("10s"),
            users=users,
            spawn_rate=None,
            name="test with:%d users" % users,
            description="Some detailed description for test with %d users" % users,
        )
        run_external(["/bin/bash", "restart_relay.sh"])


# setup some locust tests
set_load_tester_url(LOCUST_URL)
add_locust_tests()

# setup some vegeta tests
set_load_tester_url(VEGETA_URL)
add_vegeta_tests()
