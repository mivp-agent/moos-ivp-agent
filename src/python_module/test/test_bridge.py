import unittest
from threading import Thread

import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
bridgedir = os.path.join(os.path.dirname(currentdir), 'RLquaticus')
sys.path.append(bridgedir)

from bridge import ModelBridgeServer, ModelBridgeClient

DUMMY_ACTION = {
  'speed': 2.0,
  'course': 90,
  'MOOS_VARS': ()
}

DUMMY_ACTION_NO_SPEED = {
  'course': 90,
  'MOOS_VARS': ()
}

DUMMY_ACTION_NO_COURSE = {
  'speed': 2.0,
  'MOOS_VARS': ()
}

DUMMY_ACTION_NO_MOOS_VARS = {
  'speed': 2.0,
  'course': 90
}

DUMMY_STATE = {
  'NAV_X': 58.1,
  'NAV_Y': 76.0
}



class TestServer(unittest.TestCase):

  def test_server_offline_state(self):
    with ModelBridgeServer() as server:
      self.assertFalse(server.send_action(DUMMY_ACTION))
      self.assertFalse(server.listen_state())
    with ModelBridgeClient() as client:
      self.assertFalse(client.send_state(DUMMY_STATE))
      self.assertFalse(client.listen_action())
  
  def test_socket_send_action(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        def dummy_connect_client(client):
          client.connect()
          action = client.listen_action()

          self.assertEqual(action, DUMMY_ACTION)

        # Use another thread to connect client
        t =  Thread(target=dummy_connect_client, args=(client,))
        t.start()

        # Start server
        server.start()

        self.assertRaises(AssertionError, server.send_action, "Wrong Type")
        self.assertRaises(AssertionError, server.send_action, DUMMY_ACTION_NO_SPEED)
        self.assertRaises(AssertionError, server.send_action, DUMMY_ACTION_NO_COURSE)
        self.assertRaises(AssertionError, server.send_action, DUMMY_ACTION_NO_MOOS_VARS)
        
        self.assertTrue(server.send_action(DUMMY_ACTION))

        t.join()
  
  def test_socket_send_action(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        def dummy_connect_server(server):
          server.start()
          state = server.listen_state()

          self.assertEqual(state, DUMMY_STATE)

        # Use another thread to connect client
        t =  Thread(target=dummy_connect_server, args=(server,))
        t.start()

        # Start server
        client.connect()

        self.assertRaises(AssertionError, client.send_state, "Wrong Type")
        self.assertTrue(client.send_state(DUMMY_STATE))

        t.join()
  
  

if __name__ == '__main__':
  unittest.main()