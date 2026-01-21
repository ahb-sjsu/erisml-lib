__version__ = "0.1.0"

try:
    from erisml.ethics import DEME, EthicsModule, MoralTensor
    __all__ = ["DEME", "EthicsModule", "MoralTensor"]
except ImportError:
    __all__ = []
