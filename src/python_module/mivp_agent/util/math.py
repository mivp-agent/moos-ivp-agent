import numpy as np

def dist(p1, p2):
    np1 = np.array(p1)
    np2 = np.array(p2)

    return np.linalg.norm(np1-np2)