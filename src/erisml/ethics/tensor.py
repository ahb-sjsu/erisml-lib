"""
MoralTensor: Multi-dimensional ethical representation.
"""

import numpy as np
from typing import Tuple, Optional


class MoralTensor:
    """
    A tensor wrapper for ethical values (Good/Bad, Lawful/Chaotic, etc).
    """

    def __init__(self, data: Optional[np.ndarray] = None):
        if data is None:
            self.data = np.zeros((1,))
        else:
            self.data = np.array(data)

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.data.shape

    def to_numpy(self) -> np.ndarray:
        return self.data
