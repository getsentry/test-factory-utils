#!/usr/bin/env python3
### Temporary wrapper to extract "--version" arg from command lines
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--version', '-v')
args, _ = parser.parse_known_args()

if args.version and '=' not in args.version:
    print(args.version)
