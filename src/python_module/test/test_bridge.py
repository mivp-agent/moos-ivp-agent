import unittest
from threading import Thread
import socket
import time

import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
bridgedir = os.path.join(os.path.dirname(currentdir), 'RLquaticus')
sys.path.append(bridgedir)

from bridge import ModelBridgeServer, ModelBridgeClient

DUMMY_ACTION = {
  'speed': 2.0,
  'course': 90,
  'MOOS_VARS': {}
}

DUMMY_ACTION_2 = {
  'speed': 2.0,
  'course': 180,
  'MOOS_VARS': {}
}

DUMMY_ACTION_NO_SPEED = {
  'course': 90,
  'MOOS_VARS': {}
}

DUMMY_ACTION_NO_COURSE = {
  'speed': 2.0,
  'MOOS_VARS': {}
}

DUMMY_ACTION_NO_MOOS_VARS = {
  'speed': 2.0,
  'course': 90
}

DUMMY_STATE = {
  'NAV_X': 58.1,
  'NAV_Y': 76.0,
  'MOOS_VARS': {}
}

DUMMY_MUST_POST = {
  'EPISODE_MNGR_CTRL': 'type=start'
}

DUMMY_MUST_POST_2 = {
  'I_HATE': 'programming'
}


class TestSocket(unittest.TestCase):

  def test_server_offline_state(self):
    with ModelBridgeServer() as server:
      self.assertFalse(server.send_action(DUMMY_ACTION))
      self.assertFalse(server.listen_state())
    with ModelBridgeClient() as client:
      self.assertFalse(client.send_state(DUMMY_STATE))
      self.assertFalse(client.listen())
  
  def test_socket_send_action(self):
    with ModelBridgeServer() as server:
      # Part 1: Check type checking / connection check
      self.assertRaises(AssertionError, server.send_action, "Wrong Type")
      self.assertRaises(AssertionError, server.send_action, DUMMY_ACTION_NO_SPEED)
      self.assertRaises(AssertionError, server.send_action, DUMMY_ACTION_NO_COURSE)
      self.assertRaises(AssertionError, server.send_action, DUMMY_ACTION_NO_MOOS_VARS)
      self.assertFalse(server.send_action(DUMMY_ACTION))
    
      # Part 2: Check simple action sending
      with ModelBridgeClient() as client:
        def dummy_connect_client(client):
          time.sleep(1)

          client.connect()
          rsp = client.listen()

          self.assertEqual(rsp['action'], DUMMY_ACTION)

        # Use another thread to connect client
        t =  Thread(target=dummy_connect_client, args=(client,))
        t.start()

        # Start server
        server.accept()
        
        self.assertTrue(server.send_action(DUMMY_ACTION))

        t.join()
      
  def test_socket_listen_action(self):
    # Part 2: Check that client gets most recent action
      with ModelBridgeClient() as client:
        with ModelBridgeServer() as server: 
          def dummy_connect_server(server):
            server.accept()
          
          # Use another thread to connect client
          t =  Thread(target=dummy_connect_server, args=(server,))
          t.start()
          client.connect()
          t.join()

          # Test action order
          self.assertTrue(server.send_action(DUMMY_ACTION))
          self.assertTrue(server.send_action(DUMMY_ACTION))
          self.assertTrue(server.send_action(DUMMY_ACTION))
          self.assertTrue(server.send_action(DUMMY_ACTION))
          self.assertTrue(server.send_action(DUMMY_ACTION_2))

          rsp = client.listen(timeout=None)

          self.assertEqual(rsp['action'], DUMMY_ACTION_2)

          # And test must posts
          self.assertTrue(server.send_action(DUMMY_ACTION_2))
          self.assertTrue(server.send_action(DUMMY_ACTION))
          self.assertTrue(server.send_must_post(DUMMY_MUST_POST))
          self.assertTrue(server.send_must_post(DUMMY_MUST_POST_2))

          rsp = client.listen(timeout=None)

          # TODO: Test for dummy posts
          self.assertEqual(rsp['action'], DUMMY_ACTION)

  def test_socket_send_state(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:
        def dummy_connect_server(server):
          server.accept()
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
  
  def test_socket_timeout(self):
    with ModelBridgeServer() as server:
      with ModelBridgeClient() as client:

        # Assert that the client will timeout 
        self.assertFalse(client.connect())
        # TODO: Time it

        # Start the server
        def dummy_connect_server(server):
          server.accept()
        t = Thread(target=dummy_connect_server, args=(server,))
        t.start()

        client.connect()

        t.join() # Don't need the server for the rest of the tests

        # Assert that timout happens 
        self.assertFalse(client.listen())

  def test_spam_state(self):
    # Part 2: Check that client gets most recent action
      with ModelBridgeClient() as client:
        with ModelBridgeServer() as server: 
          def dummy_connect_client(client):
            client.connect()
          
          # Use another thread to connect client
          t =  Thread(target=dummy_connect_client, args=(client,))
          t.start()
          server.accept()
          t.join()

          self.assertTrue(client.send_state(DUMMY_STATE))
          rsp, _ = server.listen_state()
          self.assertEqual(rsp, DUMMY_STATE)


          for x in range(1, 40):
            for i in range(x):
              self.assertTrue(client.send_state(DUMMY_STATE))
            rsp, _ = server.listen_state()
            self.assertEqual(rsp, DUMMY_STATE)



if __name__ == '__main__':
  unittest.main()