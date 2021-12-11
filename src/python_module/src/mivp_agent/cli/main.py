import argparse

from .info import Info

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

Info(subparsers.add_parser('info'))

def main():
  args = parser.parse_args()
  args.func(args)

if __name__ == 'main':
  main()