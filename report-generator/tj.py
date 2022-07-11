"""
quick and dirty jmespath Tester

Tests queries on the test doc load_test.json
"""
from typing import List
from pprint import pprint
import cmd

import json
import jmespath


class JmesPathTester(cmd.Cmd):

    def do_q(self, line):
        """execute a jmespath query"""
        if line is None or len(line) == 0:
            print("enter a jmespath expression")
        self.search_expression(line)

    def do_EOF(self, line):
        return True

    def preloop(self):
        with open("load_test.json") as f:
            self.doc = json.load(f)

    def search_expression(self, line):
        try:
            result = jmespath.search(line, self.doc)
            pprint(result)
        except Exception as ex:
            print("JmesPath returned exception:\n", ex)

#
# def load_test_doc():
#     with open("load_test.json") as f:
#         doc = json.load(f)
#     return doc
#
#
# def main(args: List[str]):
#     arg0 = args[1]
#     doc = load_test_doc()
#     result = jmespath.search(arg0, doc)
#     pprint(result)


if __name__ == '__main__':
    JmesPathTester().cmdloop()
