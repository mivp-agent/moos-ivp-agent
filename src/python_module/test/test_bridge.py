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



class TestServer(unittest.TestCase):


  def test_server_offline_state(self):
    with ModelBridgeServer() as server:
      self.assertFalse(server.send_action('dummy'))
  
  def test_socket_send_action(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        def dummy_connect_client(client):
          client.connect()
          action = client.get_action()

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
  

if __name__ == '__main__':
  unittest.main()