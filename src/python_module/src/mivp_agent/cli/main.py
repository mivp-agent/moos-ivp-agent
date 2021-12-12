import argparse

from .info import Info
from .log import Log

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

Info(subparsers.add_parser('info'))
Log(subparsers.add_parser('log'))

def main():
  args = parser.parse_args()
  args.func(args)

if __name__ == 'main':
  main()