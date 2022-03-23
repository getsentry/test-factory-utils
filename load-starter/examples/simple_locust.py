# Example configuration file
# CONFIG_VERSION = "X.X.X" # sym version currently not used
#
# set_load_tester_url( url:str) # use to set the base url for the subsequent tests
# set_load_tester_url can be called multiple times, the last one called before any
# add_XXX_test will be used (


CONFIG_VERSION = "1.0.0"
LOCUST_URL = "http://0.0.0.0:8089"


def add_locust_tests():
    for users in range( 20, 61, 20):
        add_locust_test(
            duration=duration("10s"),
            users=users,
            spawn_rate=None,
            name="test with:%d users" % users,
            description="Some detailed description for test with %d users" % users,
        )


# setup some locust tests
set_load_tester_url(LOCUST_URL)
add_locust_tests()
