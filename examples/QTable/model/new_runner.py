#!/usr/bin/env python3
import argparse
import time

from mivp_agent.episodic_manager import EpisodicManager

from constants import DEFAULT_RUN_MODEL
from model import load_model


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--model', default=DEFAULT_RUN_MODEL)
  parser.add_argument('--enemy', default='drone_21')
  args = parser.parse_args()
  q, attack_actions, retreat_actions = load_model(args.model)
  with EpisodicManager('runner', log=False) as mgr:
    mgr.run(q, attack_actions, retreat_actions)
