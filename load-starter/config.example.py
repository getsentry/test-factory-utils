# type TestRun struct {
#     name             string
# duration         time.Duration
# startCommand     string
# startCommandVerb string // GET,POST...
#     startBody        string
# stopCommand      string
# stopCommandVerb  string // GET, POST...
#     stopBody         string
# }

# def add_load_test("name", start_command, start_body, start_verb="POST", end_command=None, end_body=NONE, end_verb="POST")

startCommand = "https://the-server/start"
endCommand = "https://theServer/stop"
start_verb = "POST"
end_verb = "GET"

def locust_start_body(users):
    spawn_rate= users/4
    return "user_count=%s&spawn_rate=%s" % (users, spawn_rate)

def add_locust_test(users,duration, name="", description=""):
    start_body = locust_start_body(users)
    add_load_test(
        duration= duration,
        name = name,
        description = description,
        start_command = startCommand,
        start_verb = start_verb,
        start_body = start_body,
        end_command = endCommand,
        end_verb = end_verb
    )

# we need a function if we want to use loops
def main():
    for users in range(10,31,5):
        add_locust_test(users, '60s')
    add_locust_test(40, "100s")
    for users in range(30, 19, -2):
        add_locust_test(users, '60s')
main()