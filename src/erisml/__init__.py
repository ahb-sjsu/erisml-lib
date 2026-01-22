__version__ = "0.1.0"

try:
    from erisml.ethics import (
        DEME,
        MoralTensor,
        StrategicLayer,
        NashResult,
        CooperativeLayer,
    )  # noqa: F401
except ImportError:
    # Fallback if dependencies are missing
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
