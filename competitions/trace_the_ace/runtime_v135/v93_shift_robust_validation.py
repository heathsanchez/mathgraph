"""Runtime compatibility shim: V94 imports folds_from_groups, but inference never calls it."""
import numpy as np
from sklearn.model_selection import GroupKFold

def folds_from_groups(groups,n=5):
    g=np.asarray(groups).astype(str)
    k=min(n,len(np.unique(g)))
    if k<2: raise ValueError('need at least two groups')
    return list(GroupKFold(k).split(np.zeros(len(g)),np.zeros(len(g)),g))
