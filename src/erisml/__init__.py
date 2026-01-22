__version__ = "0.1.0"

try:
    from erisml.ethics import (
        DEME,
        MoralTensor,
        StrategicLayer,
        NashResult,
        CooperativeLayer,
    )
except ImportError:
    # Fallback for setup.py when dependencies aren't installed yet
    DEME = None
    MoralTensor = None
    StrategicLayer = None
    NashResult = None
    CooperativeLayer = None

__all__ = [
    "DEME",
    "MoralTensor",
    "StrategicLayer",
    "NashResult",
    "CooperativeLayer",
]
