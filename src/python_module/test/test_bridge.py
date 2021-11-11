import unittest
from threading import Thread
import socket
import time


from mivp_agent.bridge import ModelBridgeServer, ModelBridgeClient
from mivp_agent.const import KEY_EPISODE_MGR_REPORT, KEY_EPISODE_MGR_STATE, KEY_ID

DUMMY_INSTR = {
  'speed': 2.0,
  'course': 120.0,
  'posts': {},
  'ctrl_msg': 'SEND_STATE'
}

DUMMY_STATE = {
  KEY_ID: 'felix',
  'MOOS_TIME': 16923.012,
  'NAV_X': 98.0,
  'NAV_Y': 40.0,
  'NAV_HEADING': 180,
  KEY_EPISODE_MGR_REPORT: None
}

def dummy_connect_client(client):
  while not client.connect():
    time.sleep(0.2)

class TestBridge(unittest.TestCase):

  def test_offline_state(self):
    with ModelBridgeClient() as client:
      self.assertFalse(client.send_state(DUMMY_STATE))
      self.assertFalse(client.listen())
      self.assertFalse(client.connect())
    with ModelBridgeServer() as server:
      self.assertRaises(RuntimeError, server.send_instr, 'addr', DUMMY_INSTR)
      self.assertRaises(RuntimeError, server.listen, 'addr')
      self.assertIsNone(server.accept())
  
  def test_validation(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        # Connect
        t = Thread(target=dummy_connect_client, args=(client,))
        t.start()

        addr = None
        while addr is None:
          time.sleep(0.2)
          addr = server.accept()
        
        # Clean up our thread
        t.join()
        
        # Client
        # Sorta check for type check
        self.assertRaises(AssertionError, client.send_state, 'Wrong type')

        # Assert all keys are tested for
        for key in DUMMY_STATE:
          if key == KEY_EPISODE_MGR_REPORT or key == KEY_EPISODE_MGR_STATE:
            continue
          state = DUMMY_STATE.copy()
          state.pop(key) # Removes key

          self.assertRaises(AssertionError, client.send_state, state)

        # Server
        # Sorta check for type check 
        self.assertRaises(AssertionError, server.send_instr, addr, 'Wrong type')

        # Assert all keys are tested for
        for key in DUMMY_INSTR:
          instr = DUMMY_INSTR.copy()
          instr.pop(key) # Removes key

          self.assertRaises(AssertionError, server.send_instr, addr, instr)
  
  def test_connect(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        t = Thread(target=dummy_connect_client, args=(client,))
        t.start()

        addr = None
        while addr is None:
          time.sleep(1)
          addr = server.accept()
        
        # Clean up our thread
        t.join()

        self.assertFalse(client.listen())
        self.assertIsNone(server.listen(addr))
        self.assertIsNone(server.listen(addr))

  def test_instr(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        t = Thread(target=dummy_connect_client, args=(client,))
        t.start()

        addr = None
        while addr is None:
          time.sleep(0.2)
          addr = server.accept()
        
        # Clean up our thread
        t.join()

        self.assertTrue(server.send_instr(addr, DUMMY_INSTR))
        time.sleep(0.1)
        self.assertEqual(client.listen(), DUMMY_INSTR)

  def test_state(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        t = Thread(target=dummy_connect_client, args=(client,))
        t.start()

        addr = None
        while addr is None:
          time.sleep(0.2)
          addr = server.accept()
        
        # Clean up our thread
        t.join()

        self.assertTrue(client.send_state(DUMMY_STATE))
        time.sleep(0.1)
        self.assertEqual(server.listen(addr), DUMMY_STATE)       

if __name__ == '__main__':
  unittest.main()