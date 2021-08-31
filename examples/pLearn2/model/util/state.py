import numpy as np

def state2vec(s, const):
    if(s==None):
        print("NULL STATE")
    temp = []
    for state in s:
        temp.append(float(state))
    temp.append(1)
    for param in const.state:
        if const.state[param].standardized:
            if const.state[param].type != "binary":
                temp[const.state[param].index]=float(int(temp[const.state[param].index])-const.state[param].range[0])/const.state[param].range[1]
    return np.array([temp])

def dist(p1, p2):
    np1 = np.array(p1)
    np2 = np.array(p2)

    return np.linalg.norm(np1-np2)
