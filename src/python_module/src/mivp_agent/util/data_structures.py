import numpy as np

# source: https://instructobit.com/tutorial/131/Python-stack-like-list-with-a-maximum-number-of-elements
class DropList(list):
  def __init__(self, max_size):
    super().__init__()
    self.max_size = max_size

  # Simply here to adhere more to a stack
  def push(self, element):
    self.append(element)
    
  def append(self, element):
    super().append(element)
    # If the list has now exceeded the maximum size, remove the element at the tail of the list
    if super().__len__() > self.max_size:
      super().__delitem__(0)

class LimitedHistory:
  def __init__(self, max_frames, size):
    self.max_frames = max_frames
    self.size = size

    # Create data structure
    self._data = np.zeros((self.max_frames, self.size))

    # Initalize state
    self.write_row = max_frames - 1
    self.is_full = False
  
  def push_frame(self, frame):
    assert isinstance(frame, np.ndarray), "Frame must be a numpy array"
    assert frame.shape == (self.size, ), "Frame must be of shape (frame_size, )"

    self._data[self.write_row,:] = frame
    
    self.write_row -= 1

    # Reset at end and singnal full 
    if self.write_row == -1:
      self.write_row = self.max_frames - 1
      self.is_full = True
  
  def get_frames(self):
    # Return None if nothing has been added yet
    if self.is_full == False and self.write_row == self.max_frames - 1:
      return None

    frames = None

    # Read forward from write row
    for i in range(1, self.max_frames+1):
      row = self.write_row + i

      # Check if we are at end and have not yet filled the buffer
      if row == self.max_frames and self.is_full == False:
        break

      # Wrapp to other side of buffer if needed
      row %= self.max_frames

      # Add frame or initilze the return structure
      if frames is None:
        row_data = self._data[row,:]
        frames = np.expand_dims(row_data, axis=0)
      else:
        frames = np.append(frames, np.expand_dims(self._data[row,:], axis=0), axis=0) 
    
    return frames
  
  def entry_history(self, entry):
    assert entry < self.size, "Entry index out of bounds"

    # Return empty if nothing has been added yet
    if not self.is_full and self.write_row == self.max_frames - 1:
      return np.zeros(0)

    # Get the entry buffer
    entry_buffer = self._data[:,entry]

    # Create a map to translate buffer to ordered history (recent first)
    idx = []
    for i in range(1, self.max_frames+1):
      row = self.write_row + i

      # Check if we are at end and have not yet filled the buffer
      if row == self.max_frames and not self.is_full:
        break

      # Wrapp to other side of buffer if needed
      row %= self.max_frames

      idx.append(row)
    
    return entry_buffer[idx]
  
  def select_history(self, idxs, scale=None):
    for i in idxs:
      assert i < self.size, "Entry index in 'idx' out of bounds"
    
    # Return empty if nothing has been added yet
    if not self.is_full and self.write_row == self.max_frames - 1:
      return None

    # Get frame history
    history = self.get_frames()
    history = history[:, idxs]

    if scale is None:
      return history


    for row in range(history.shape[0]):
      row_min = history[row].min()
      row_max = history[row].max()

      history[row] -= row_min
      history[row] /= (row_max-row_min)
    
    return history
    

