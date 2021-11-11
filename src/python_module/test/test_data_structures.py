import unittest
import numpy as np

from mivp_agent.util.data_structures import LimitedHistory 

class TestLimitedHistory(unittest.TestCase):

  def test_init(self):
    h = LimitedHistory(3, 2)
    blank = np.array([[0,0], [0,0], [0,0]])

    self.assertTrue(np.array_equal(h._data, blank))
  
  def test_insert(self):
    h = LimitedHistory(3, 2)

    insert = np.array([1, 2])
    h.push_frame(insert)
    compare = np.array([[0,0], [0,0], [1,2]])
    self.assertTrue(np.array_equal(h._data, compare))

    insert = np.array([3, 4])
    h.push_frame(insert)
    compare = np.array([[0,0], [3,4], [1,2]])
    self.assertTrue(np.array_equal(h._data, compare))

    insert = np.array([5, 6])
    h.push_frame(insert)
    compare = np.array([[5,6], [3,4], [1,2]])
    self.assertTrue(np.array_equal(h._data, compare))

    insert = np.array([7, 8])
    h.push_frame(insert)
    compare = np.array([[5,6], [3,4], [7,8]])
    self.assertTrue(np.array_equal(h._data, compare))
  
  def test_get_frames(self):
    h = LimitedHistory(3, 2)

    self.assertIsNone(h.get_frames())

    insert = np.array([1, 2])
    h.push_frame(insert)
    compare = np.array([[1,2]])
    self.assertTrue(np.array_equal(h.get_frames(), compare))

    insert = np.array([3, 4])
    h.push_frame(insert)

    compare = np.array([[3,4], [1,2]])
    self.assertTrue(np.array_equal(h.get_frames(), compare))
  
  def test_entry_history(self):
    h = LimitedHistory(3, 2)
    self.assertRaises(AssertionError, h.entry_history, 2)
    self.assertTrue(np.array_equal(h.entry_history(0), np.zeros(0)))

    insert = np.array([1, 2])
    h.push_frame(insert)
    compare = np.array([1,])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([2,])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

    insert = np.array([3, 4])
    h.push_frame(insert)
    compare = np.array([3, 1])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([4, 2])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

    insert = np.array([5, 6])
    h.push_frame(insert)
    compare = np.array([5, 3, 1])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([6, 4, 2])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

    insert = np.array([7, 8])
    h.push_frame(insert)
    compare = np.array([7, 5, 3])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([8, 6, 4])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

    # For sanity check a few more
    insert = np.array([9, 10])
    h.push_frame(insert)
    compare = np.array([9, 7, 5])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([10, 8, 6])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

    insert = np.array([11, 12])
    h.push_frame(insert)
    compare = np.array([11, 9, 7])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([12, 10, 8])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

    insert = np.array([13, 14])
    h.push_frame(insert)
    compare = np.array([13, 11, 9])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([14, 12, 10])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

    insert = np.array([15, 16])
    h.push_frame(insert)
    compare = np.array([15, 13, 11])
    self.assertTrue(np.array_equal(h.entry_history(0), compare))
    compare = np.array([16, 14, 12])
    self.assertTrue(np.array_equal(h.entry_history(1), compare))

  def test_selected_history(self):
    h = LimitedHistory(3, 3)

    insert = np.array([0, 50, 100])
    h.push_frame(insert)
    insert = np.array([100, 24, 0])
    h.push_frame(insert)
    insert = np.array([1, 2, 3])
    h.push_frame(insert)

    compare = np.array([
      [1, 2, 3],
      [100, 24, 0],
      [0, 50, 100],
    ])
    self.assertTrue(np.array_equal(h.select_history([0,1,2]), compare))
    compare = np.array([
      [1, 3],
      [100, 0],
      [0, 100],
    ])
    self.assertTrue(np.array_equal(h.select_history([0,2]), compare))

    compare = np.array([
      [0, 0.5, 1],
      [1, .24, 0],
      [0, 0.5, 1],
    ])
    self.assertTrue(np.array_equal(h.select_history([0,1,2], scale=1.0), compare))

    insert = np.array([500, 200, 350])
    h.push_frame(insert)
    compare = np.array([
      [1, 0, 0.5],
      [0, 0.5, 1],
      [1, .24, 0],
    ])
    self.assertTrue(np.array_equal(h.select_history([0,1,2], scale=1.0), compare))


  


if __name__ == '__main__':
  unittest.main()