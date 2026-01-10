# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
MoralTensor: Multi-rank tensor representation of ethical assessment.

DEME V3 introduces multi-rank moral tensors that extend MoralVector for
multi-agent ethics. This provides:

1. Rank-1 (9,): V2-compatible MoralVector equivalent
2. Rank-2 (9, n): Per-party distributional ethics
3. Rank-3 (9, n, τ): Temporal evolution
4. Rank-4 (9, n, a, c): Coalition actions
5. Rank-5 (9, n, τ, s): Uncertainty samples
6. Rank-6 (9, n, τ, a, c, s): Full multi-agent context

The 9 ethical dimensions are derived from a 3×3 matrix (per "Nine Dimensions
of Ethical Assessment" paper):

|                | What Matters       | Who Decides            | What We Know          |
|----------------|-------------------|------------------------|----------------------|
| Individual     | Autonomy/Agency   | Rights/Duties          | Privacy/Data         |
| Relational     | Virtue/Care       | Consequences/Welfare   | Epistemic Status     |
| Collective     | Justice/Fairness  | Procedural Legitimacy  | Societal/Environmental |

Version: 3.0.0 (DEME V3)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from erisml.ethics.moral_vector import MoralVector

# Standard dimension names (from Nine Dimensions paper)
# Maps k=0..8 to dimension names
MORAL_DIMENSION_NAMES: Tuple[str, ...] = (
    "physical_harm",         # 0: Consequences/Welfare
    "rights_respect",        # 1: Rights/Duties
    "fairness_equity",       # 2: Justice/Fairness
    "autonomy_respect",      # 3: Autonomy/Agency
    "privacy_protection",    # 4: Privacy/Data
    "societal_environmental",  # 5: Societal/Environmental
    "virtue_care",           # 6: Virtue/Care
    "legitimacy_trust",      # 7: Procedural Legitimacy
    "epistemic_quality",     # 8: Epistemic Status
)

# Dimension index mapping
DIMENSION_INDEX: Dict[str, int] = {name: i for i, name in enumerate(MORAL_DIMENSION_NAMES)}

# Standard axis names by position for each rank
# rank 1: (k,)
# rank 2: (k, n)
# rank 3: (k, n, tau)
# rank 4: (k, n, a, c)
# rank 5: (k, n, tau, s)
# rank 6: (k, n, tau, a, c, s)
DEFAULT_AXIS_NAMES: Dict[int, Tuple[str, ...]] = {
    1: ("k",),
    2: ("k", "n"),
    3: ("k", "n", "tau"),
    4: ("k", "n", "a", "c"),
    5: ("k", "n", "tau", "s"),
    6: ("k", "n", "tau", "a", "c", "s"),
}


@dataclass
class SparseCOO:
    """
    COO sparse tensor storage for memory efficiency.

    Uses coordinate format (COO) for efficient storage of sparse tensors
    where most values are a constant fill value.
    """

    coords: np.ndarray
    """(nnz, rank) array of coordinates for non-fill values."""

    values: np.ndarray
    """(nnz,) array of values at the coordinates."""

    shape: Tuple[int, ...]
    """Shape of the dense tensor."""

    fill_value: float = 0.0
    """Value used for unspecified coordinates."""

    def __post_init__(self) -> None:
        """Validate sparse tensor structure."""
        if self.coords.ndim != 2:
            raise ValueError(f"coords must be 2D, got shape {self.coords.shape}")
        if self.values.ndim != 1:
            raise ValueError(f"values must be 1D, got shape {self.values.shape}")
        if len(self.coords) != len(self.values):
            raise ValueError(
                f"coords and values must have same length, got {len(self.coords)} and {len(self.values)}"
            )
        if self.coords.shape[1] != len(self.shape):
            raise ValueError(
                f"coords columns ({self.coords.shape[1]}) must match rank ({len(self.shape)})"
            )

    @property
    def nnz(self) -> int:
        """Number of non-fill values."""
        return len(self.values)

    @property
    def rank(self) -> int:
        """Tensor rank."""
        return len(self.shape)

    def to_dense(self) -> np.ndarray:
        """Convert to dense NumPy array."""
        dense = np.full(self.shape, self.fill_value, dtype=np.float64)
        if self.nnz > 0:
            # Convert coords to tuple of index arrays for advanced indexing
            idx = tuple(self.coords[:, i] for i in range(self.rank))
            dense[idx] = self.values
        return dense

    @classmethod
    def from_dense(
        cls, data: np.ndarray, fill_value: float = 0.0, tol: float = 1e-10
    ) -> SparseCOO:
        """
        Create sparse tensor from dense array.

        Args:
            data: Dense NumPy array.
            fill_value: Value to treat as sparse (default 0.0).
            tol: Tolerance for comparing to fill_value.

        Returns:
            SparseCOO representation.
        """
        # Find non-fill entries
        if fill_value == 0.0:
            mask = np.abs(data) > tol
        else:
            mask = np.abs(data - fill_value) > tol

        coords = np.argwhere(mask)
        values = data[mask]

        return cls(
            coords=coords.astype(np.int32),
            values=values.astype(np.float64),
            shape=data.shape,
            fill_value=fill_value,
        )


@dataclass
class MoralTensor:
    """
    Multi-rank tensor for ethical assessment (ranks 1-6).

    Provides a unified representation for single-agent and multi-agent
    ethical assessments with support for temporal evolution, coalitions,
    and uncertainty quantification.

    Attributes:
        _data: Internal storage (dense np.ndarray or SparseCOO).
        shape: Tensor shape. First dimension must be 9.
        rank: Number of dimensions (1-6).
        axis_names: Names for each axis.
        axis_labels: Labels for indices along each axis.
        veto_flags: List of triggered veto conditions.
        veto_locations: Coordinates where vetoes apply.
        reason_codes: Machine-readable reason codes.
        is_sparse: Whether using sparse storage.
        metadata: Additional metadata.
        extensions: Domain-specific extensions.
    """

    _data: Union[np.ndarray, SparseCOO]
    """Internal tensor storage."""

    shape: Tuple[int, ...]
    """Tensor shape (first dim must be 9)."""

    rank: int
    """Tensor rank (1-6)."""

    axis_names: Tuple[str, ...] = field(default_factory=lambda: ("k",))
    """Names for each axis."""

    axis_labels: Dict[str, List[str]] = field(default_factory=dict)
    """Labels for indices along each axis (e.g., party names for 'n')."""

    veto_flags: List[str] = field(default_factory=list)
    """List of triggered veto conditions."""

    veto_locations: List[Tuple[int, ...]] = field(default_factory=list)
    """Coordinates where vetoes apply (empty tuple = global veto)."""

    reason_codes: List[str] = field(default_factory=list)
    """Machine-readable reason codes for audit trail."""

    is_sparse: bool = False
    """Whether using sparse storage."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata (timestamps, source, etc.)."""

    extensions: Dict[str, Any] = field(default_factory=dict)
    """Domain-specific extensions."""

    def __post_init__(self) -> None:
        """Validate tensor structure after initialization."""
        self._validate_rank()
        self._validate_shape()
        self._validate_first_dimension()
        self._validate_bounds()
        self._validate_axis_names()
        self._validate_veto_locations()

    def _validate_rank(self) -> None:
        """Ensure rank is 1-6."""
        if not 1 <= self.rank <= 6:
            raise ValueError(f"Rank must be 1-6, got {self.rank}")
        if self.rank != len(self.shape):
            raise ValueError(f"Rank ({self.rank}) must match shape dimensions ({len(self.shape)})")

    def _validate_shape(self) -> None:
        """Ensure shape is valid."""
        if len(self.shape) == 0:
            raise ValueError("Shape cannot be empty")
        for i, dim in enumerate(self.shape):
            if dim <= 0:
                raise ValueError(f"Dimension {i} must be positive, got {dim}")

    def _validate_first_dimension(self) -> None:
        """First dimension must be k=9 (moral dimensions)."""
        if self.shape[0] != 9:
            raise ValueError(f"First dimension must be 9 (moral dimensions), got {self.shape[0]}")

    def _validate_bounds(self) -> None:
        """All values must be in [0, 1]."""
        data = self.to_dense()
        if np.any(data < 0.0) or np.any(data > 1.0):
            raise ValueError("All tensor values must be in [0, 1]")

    def _validate_axis_names(self) -> None:
        """Ensure axis names match rank."""
        if len(self.axis_names) != self.rank:
            raise ValueError(
                f"axis_names length ({len(self.axis_names)}) must match rank ({self.rank})"
            )

    def _validate_veto_locations(self) -> None:
        """Ensure veto locations are valid coordinates.

        Veto locations are coordinates in the non-k dimensions (shape[1:]).
        An empty tuple means a global veto.
        """
        non_k_shape = self.shape[1:]  # Shape excluding k dimension
        for loc in self.veto_locations:
            if len(loc) > len(non_k_shape):
                raise ValueError(
                    f"Veto location {loc} has more dimensions than non-k axes ({len(non_k_shape)})"
                )
            for i, idx in enumerate(loc):
                if idx < 0 or idx >= non_k_shape[i]:
                    raise ValueError(
                        f"Veto location {loc} index {idx} out of bounds for axis {i+1} (size {non_k_shape[i]})"
                    )

    # -------------------------------------------------------------------------
    # Data Access
    # -------------------------------------------------------------------------

    def to_dense(self) -> np.ndarray:
        """Get dense NumPy array representation."""
        if isinstance(self._data, SparseCOO):
            return self._data.to_dense()
        # _data is np.ndarray at this point
        assert isinstance(self._data, np.ndarray)
        return np.array(self._data, dtype=np.float64)

    def to_sparse(self, fill_value: float = 0.0) -> SparseCOO:
        """Get sparse COO representation."""
        if isinstance(self._data, SparseCOO):
            return self._data
        return SparseCOO.from_dense(self._data, fill_value=fill_value)

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_dense(
        cls,
        data: np.ndarray,
        axis_names: Optional[Tuple[str, ...]] = None,
        axis_labels: Optional[Dict[str, List[str]]] = None,
        veto_flags: Optional[List[str]] = None,
        veto_locations: Optional[List[Tuple[int, ...]]] = None,
        reason_codes: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ) -> MoralTensor:
        """
        Create MoralTensor from dense NumPy array.

        Args:
            data: NumPy array with shape (9, ...).
            axis_names: Names for each axis (defaults by rank).
            axis_labels: Labels for indices along each axis.
            veto_flags: Veto condition flags.
            veto_locations: Coordinates where vetoes apply.
            reason_codes: Reason codes for audit.
            metadata: Additional metadata.
            extensions: Domain-specific extensions.

        Returns:
            MoralTensor instance.
        """
        data = np.asarray(data, dtype=np.float64)
        rank = data.ndim
        shape = data.shape

        if axis_names is None:
            axis_names = DEFAULT_AXIS_NAMES.get(rank, tuple(f"dim{i}" for i in range(rank)))

        return cls(
            _data=data,
            shape=shape,
            rank=rank,
            axis_names=axis_names,
            axis_labels=axis_labels or {},
            veto_flags=veto_flags or [],
            veto_locations=veto_locations or [],
            reason_codes=reason_codes or [],
            is_sparse=False,
            metadata=metadata or {},
            extensions=extensions or {},
        )

    @classmethod
    def from_sparse(
        cls,
        coords: np.ndarray,
        values: np.ndarray,
        shape: Tuple[int, ...],
        fill_value: float = 0.0,
        axis_names: Optional[Tuple[str, ...]] = None,
        axis_labels: Optional[Dict[str, List[str]]] = None,
        veto_flags: Optional[List[str]] = None,
        veto_locations: Optional[List[Tuple[int, ...]]] = None,
        reason_codes: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ) -> MoralTensor:
        """
        Create MoralTensor from sparse COO format.

        Args:
            coords: (nnz, rank) array of coordinates.
            values: (nnz,) array of values.
            shape: Tensor shape.
            fill_value: Fill value for unspecified coordinates.
            axis_names: Names for each axis.
            axis_labels: Labels for indices along each axis.
            veto_flags: Veto condition flags.
            veto_locations: Coordinates where vetoes apply.
            reason_codes: Reason codes for audit.
            metadata: Additional metadata.
            extensions: Domain-specific extensions.

        Returns:
            MoralTensor instance.
        """
        sparse_data = SparseCOO(
            coords=np.asarray(coords, dtype=np.int32),
            values=np.asarray(values, dtype=np.float64),
            shape=shape,
            fill_value=fill_value,
        )
        rank = len(shape)

        if axis_names is None:
            axis_names = DEFAULT_AXIS_NAMES.get(rank, tuple(f"dim{i}" for i in range(rank)))

        return cls(
            _data=sparse_data,
            shape=shape,
            rank=rank,
            axis_names=axis_names,
            axis_labels=axis_labels or {},
            veto_flags=veto_flags or [],
            veto_locations=veto_locations or [],
            reason_codes=reason_codes or [],
            is_sparse=True,
            metadata=metadata or {},
            extensions=extensions or {},
        )

    @classmethod
    def from_moral_vector(cls, vec: MoralVector) -> MoralTensor:
        """
        Create rank-1 tensor from MoralVector (backward compatibility).

        Args:
            vec: V2 MoralVector instance.

        Returns:
            Rank-1 MoralTensor equivalent to the MoralVector.
        """
        data = np.array([
            vec.physical_harm,
            vec.rights_respect,
            vec.fairness_equity,
            vec.autonomy_respect,
            vec.privacy_protection,
            vec.societal_environmental,
            vec.virtue_care,
            vec.legitimacy_trust,
            vec.epistemic_quality,
        ], dtype=np.float64)

        return cls(
            _data=data,
            shape=(9,),
            rank=1,
            axis_names=("k",),
            axis_labels={"k": list(MORAL_DIMENSION_NAMES)},
            veto_flags=vec.veto_flags.copy(),
            veto_locations=[],  # Rank-1 has no specific locations
            reason_codes=vec.reason_codes.copy(),
            is_sparse=False,
            metadata={},
            extensions=dict(vec.extensions) if vec.extensions else {},
        )

    @classmethod
    def from_moral_vectors(
        cls,
        vectors: Dict[str, "MoralVector"],
        axis_name: str = "n",
    ) -> MoralTensor:
        """
        Stack multiple MoralVectors into a rank-2 tensor.

        Args:
            vectors: Dict mapping party/entity names to MoralVectors.
            axis_name: Name for the stacked axis (default "n").

        Returns:
            Rank-2 MoralTensor of shape (9, n).
        """
        if not vectors:
            raise ValueError("vectors dict cannot be empty")

        names = list(vectors.keys())
        n = len(names)

        data = np.zeros((9, n), dtype=np.float64)
        all_veto_flags: List[str] = []
        all_veto_locations: List[Tuple[int, ...]] = []
        all_reason_codes: List[str] = []

        for j, name in enumerate(names):
            vec = vectors[name]
            data[0, j] = vec.physical_harm
            data[1, j] = vec.rights_respect
            data[2, j] = vec.fairness_equity
            data[3, j] = vec.autonomy_respect
            data[4, j] = vec.privacy_protection
            data[5, j] = vec.societal_environmental
            data[6, j] = vec.virtue_care
            data[7, j] = vec.legitimacy_trust
            data[8, j] = vec.epistemic_quality

            # Collect vetoes with location
            for veto in vec.veto_flags:
                if veto not in all_veto_flags:
                    all_veto_flags.append(veto)
                # Associate veto with this party's column
                all_veto_locations.append((j,))

            for code in vec.reason_codes:
                if code not in all_reason_codes:
                    all_reason_codes.append(code)

        return cls(
            _data=data,
            shape=(9, n),
            rank=2,
            axis_names=("k", axis_name),
            axis_labels={"k": list(MORAL_DIMENSION_NAMES), axis_name: names},
            veto_flags=all_veto_flags,
            veto_locations=all_veto_locations,
            reason_codes=all_reason_codes,
            is_sparse=False,
            metadata={},
            extensions={},
        )

    @classmethod
    def zeros(cls, shape: Tuple[int, ...]) -> MoralTensor:
        """
        Create worst-case tensor (harm=1, others=0).

        This represents the ethically worst scenario where harm is
        maximized and all positive dimensions are minimized.

        Args:
            shape: Tensor shape (first dim must be 9).

        Returns:
            MoralTensor with worst-case values.
        """
        if shape[0] != 9:
            raise ValueError(f"First dimension must be 9, got {shape[0]}")

        data = np.zeros(shape, dtype=np.float64)
        # Set physical_harm (dim 0) to 1.0 (worst case)
        data[0, ...] = 1.0

        rank = len(shape)
        axis_names = DEFAULT_AXIS_NAMES.get(rank, tuple(f"dim{i}" for i in range(rank)))

        return cls(
            _data=data,
            shape=shape,
            rank=rank,
            axis_names=axis_names,
            axis_labels={},
            veto_flags=[],
            veto_locations=[],
            reason_codes=[],
            is_sparse=False,
            metadata={},
            extensions={},
        )

    @classmethod
    def ones(cls, shape: Tuple[int, ...]) -> MoralTensor:
        """
        Create ideal tensor (harm=0, others=1).

        This represents the ethically ideal scenario where harm is
        minimized and all positive dimensions are maximized.

        Args:
            shape: Tensor shape (first dim must be 9).

        Returns:
            MoralTensor with ideal values.
        """
        if shape[0] != 9:
            raise ValueError(f"First dimension must be 9, got {shape[0]}")

        data = np.ones(shape, dtype=np.float64)
        # Set physical_harm (dim 0) to 0.0 (best case)
        data[0, ...] = 0.0

        rank = len(shape)
        axis_names = DEFAULT_AXIS_NAMES.get(rank, tuple(f"dim{i}" for i in range(rank)))

        return cls(
            _data=data,
            shape=shape,
            rank=rank,
            axis_names=axis_names,
            axis_labels={},
            veto_flags=[],
            veto_locations=[],
            reason_codes=[],
            is_sparse=False,
            metadata={},
            extensions={},
        )

    # -------------------------------------------------------------------------
    # Conversion to MoralVector
    # -------------------------------------------------------------------------

    def to_moral_vector(self) -> "MoralVector":
        """
        Convert rank-1 tensor to MoralVector.

        Returns:
            MoralVector with equivalent values.

        Raises:
            ValueError: If tensor rank > 1.
        """
        if self.rank != 1:
            raise ValueError(f"Can only convert rank-1 tensor to MoralVector, got rank {self.rank}")

        # Import here to avoid circular dependency
        from erisml.ethics.moral_vector import MoralVector

        data = self.to_dense()
        return MoralVector(
            physical_harm=float(data[0]),
            rights_respect=float(data[1]),
            fairness_equity=float(data[2]),
            autonomy_respect=float(data[3]),
            privacy_protection=float(data[4]),
            societal_environmental=float(data[5]),
            virtue_care=float(data[6]),
            legitimacy_trust=float(data[7]),
            epistemic_quality=float(data[8]),
            extensions=dict(self.extensions),
            veto_flags=self.veto_flags.copy(),
            reason_codes=self.reason_codes.copy(),
        )

    # -------------------------------------------------------------------------
    # Indexing and Slicing
    # -------------------------------------------------------------------------

    def __getitem__(self, key: Any) -> Union[float, "MoralTensor"]:
        """
        Index or slice the tensor.

        Args:
            key: Index, slice, or tuple of indices/slices.

        Returns:
            Float for scalar access, MoralTensor for slices.
        """
        data = self.to_dense()
        result = data[key]

        if isinstance(result, np.ndarray):
            # Preserve axis names for remaining dimensions
            # This is simplified - a full implementation would track axis mapping
            if result.ndim > 0:
                return MoralTensor.from_dense(
                    result,
                    veto_flags=self.veto_flags.copy(),
                    reason_codes=self.reason_codes.copy(),
                    metadata=self.metadata.copy(),
                    extensions=self.extensions.copy(),
                )
        return float(result)

    def slice_axis(
        self, axis: str, index: Union[int, slice]
    ) -> "MoralTensor":
        """
        Slice tensor by named axis.

        Args:
            axis: Axis name to slice.
            index: Index or slice for that axis.

        Returns:
            Sliced MoralTensor.

        Raises:
            ValueError: If axis name not found.
        """
        if axis not in self.axis_names:
            raise ValueError(f"Axis '{axis}' not found in {self.axis_names}")

        axis_idx = self.axis_names.index(axis)
        data = self.to_dense()

        # Build slice tuple
        slices: List[Any] = [slice(None)] * self.rank
        slices[axis_idx] = index
        result = data[tuple(slices)]

        # Build new axis names (remove axis if single index)
        if isinstance(index, int):
            new_axis_names = tuple(n for i, n in enumerate(self.axis_names) if i != axis_idx)
        else:
            new_axis_names = self.axis_names

        if result.ndim == 0:
            return float(result)  # type: ignore

        return MoralTensor.from_dense(
            result,
            axis_names=new_axis_names if new_axis_names else None,
            veto_flags=self.veto_flags.copy(),
            reason_codes=self.reason_codes.copy(),
            metadata=self.metadata.copy(),
            extensions=self.extensions.copy(),
        )

    # -------------------------------------------------------------------------
    # Reduction Operations
    # -------------------------------------------------------------------------

    def reduce(
        self,
        axis: str,
        method: str = "mean",
        keepdims: bool = False,
    ) -> "MoralTensor":
        """
        Reduce tensor along named axis.

        Args:
            axis: Axis name to reduce.
            method: Reduction method - "mean", "sum", "min", "max".
            keepdims: Whether to keep reduced dimension.

        Returns:
            Reduced MoralTensor.
        """
        if axis not in self.axis_names:
            raise ValueError(f"Axis '{axis}' not found in {self.axis_names}")

        axis_idx = self.axis_names.index(axis)
        data = self.to_dense()

        if method == "mean":
            result = np.mean(data, axis=axis_idx, keepdims=keepdims)
        elif method == "sum":
            result = np.clip(np.sum(data, axis=axis_idx, keepdims=keepdims), 0.0, 1.0)
        elif method == "min":
            result = np.min(data, axis=axis_idx, keepdims=keepdims)
        elif method == "max":
            result = np.max(data, axis=axis_idx, keepdims=keepdims)
        else:
            raise ValueError(f"Unknown reduction method: {method}")

        # Build new axis names
        if keepdims:
            new_axis_names = self.axis_names
        else:
            new_axis_names = tuple(n for i, n in enumerate(self.axis_names) if i != axis_idx)

        return MoralTensor.from_dense(
            result,
            axis_names=new_axis_names if new_axis_names else None,
            veto_flags=self.veto_flags.copy(),
            reason_codes=self.reason_codes.copy(),
            metadata=self.metadata.copy(),
            extensions=self.extensions.copy(),
        )

    # -------------------------------------------------------------------------
    # Arithmetic Operations
    # -------------------------------------------------------------------------

    def __add__(self, other: Union["MoralTensor", float]) -> "MoralTensor":
        """
        Element-wise addition with clamping to [0, 1].

        Args:
            other: MoralTensor or scalar to add.

        Returns:
            New MoralTensor with summed values clamped to [0, 1].
        """
        data = self.to_dense()

        if isinstance(other, MoralTensor):
            other_data = other.to_dense()
            if data.shape != other_data.shape:
                raise ValueError(f"Shape mismatch: {data.shape} vs {other_data.shape}")
            result = np.clip(data + other_data, 0.0, 1.0)
            merged_vetoes = list(set(self.veto_flags) | set(other.veto_flags))
            merged_reasons = list(set(self.reason_codes) | set(other.reason_codes))
        else:
            result = np.clip(data + float(other), 0.0, 1.0)
            merged_vetoes = self.veto_flags.copy()
            merged_reasons = self.reason_codes.copy()

        return MoralTensor.from_dense(
            result,
            axis_names=self.axis_names,
            axis_labels=self.axis_labels.copy(),
            veto_flags=merged_vetoes,
            reason_codes=merged_reasons,
            metadata=self.metadata.copy(),
            extensions=self.extensions.copy(),
        )

    def __radd__(self, other: float) -> "MoralTensor":
        """Right addition."""
        return self.__add__(other)

    def __mul__(self, other: Union["MoralTensor", float]) -> "MoralTensor":
        """
        Element-wise or scalar multiplication with clamping to [0, 1].

        Args:
            other: MoralTensor or scalar to multiply.

        Returns:
            New MoralTensor with product values clamped to [0, 1].
        """
        data = self.to_dense()

        if isinstance(other, MoralTensor):
            other_data = other.to_dense()
            if data.shape != other_data.shape:
                raise ValueError(f"Shape mismatch: {data.shape} vs {other_data.shape}")
            result = np.clip(data * other_data, 0.0, 1.0)
            merged_vetoes = list(set(self.veto_flags) | set(other.veto_flags))
            merged_reasons = list(set(self.reason_codes) | set(other.reason_codes))
        else:
            result = np.clip(data * float(other), 0.0, 1.0)
            merged_vetoes = self.veto_flags.copy()
            merged_reasons = self.reason_codes.copy()

        return MoralTensor.from_dense(
            result,
            axis_names=self.axis_names,
            axis_labels=self.axis_labels.copy(),
            veto_flags=merged_vetoes,
            reason_codes=merged_reasons,
            metadata=self.metadata.copy(),
            extensions=self.extensions.copy(),
        )

    def __rmul__(self, other: float) -> "MoralTensor":
        """Right multiplication."""
        return self.__mul__(other)

    # -------------------------------------------------------------------------
    # Comparison Operations
    # -------------------------------------------------------------------------

    def dominates(self, other: "MoralTensor") -> bool:
        """
        Check if this tensor Pareto-dominates another.

        A tensor dominates another if it is at least as good in all
        dimensions and strictly better in at least one dimension.

        Note: physical_harm (dim 0) is inverted (lower is better).

        Args:
            other: MoralTensor to compare against.

        Returns:
            True if this tensor Pareto-dominates other.
        """
        if self.shape != other.shape:
            raise ValueError(f"Shape mismatch: {self.shape} vs {other.shape}")

        self_data = self.to_dense()
        other_data = other.to_dense()

        # For physical_harm (dim 0), lower is better
        harm_self = self_data[0, ...]
        harm_other = other_data[0, ...]

        # Check harm dimension (lower is better)
        if np.any(harm_self > harm_other):
            return False  # Worse in some harm location

        # Check other dimensions (higher is better)
        for k in range(1, 9):
            if np.any(self_data[k, ...] < other_data[k, ...]):
                return False  # Worse in some location

        # Must be strictly better in at least one place
        harm_strictly_better = bool(np.any(harm_self < harm_other))
        other_strictly_better = any(
            bool(np.any(self_data[k, ...] > other_data[k, ...]))
            for k in range(1, 9)
        )

        return harm_strictly_better or other_strictly_better

    def distance(
        self,
        other: "MoralTensor",
        metric: str = "frobenius",
    ) -> float:
        """
        Compute distance to another MoralTensor.

        Args:
            other: MoralTensor to compare against.
            metric: Distance metric - "frobenius", "max", "mean_abs".

        Returns:
            Distance value (>= 0).
        """
        if self.shape != other.shape:
            raise ValueError(f"Shape mismatch: {self.shape} vs {other.shape}")

        diff = self.to_dense() - other.to_dense()

        if metric == "frobenius":
            return float(np.linalg.norm(diff))
        elif metric == "max":
            return float(np.max(np.abs(diff)))
        elif metric == "mean_abs":
            return float(np.mean(np.abs(diff)))
        else:
            raise ValueError(f"Unknown metric: {metric}")

    # -------------------------------------------------------------------------
    # Veto Handling
    # -------------------------------------------------------------------------

    def has_veto(self) -> bool:
        """Check if any veto flags are set."""
        return len(self.veto_flags) > 0

    def has_veto_at(self, **coords: int) -> bool:
        """
        Check if a veto applies at specific coordinates.

        Args:
            **coords: Named coordinates (e.g., n=2, tau=5).

        Returns:
            True if a veto applies at the specified location.
        """
        if not self.veto_flags:
            return False

        # Build coordinate tuple from kwargs
        target: List[Optional[int]] = []
        for axis_name in self.axis_names[1:]:  # Skip 'k' dimension
            if axis_name in coords:
                target.append(coords[axis_name])
            else:
                target.append(None)  # Wildcard

        # Check each veto location
        for loc in self.veto_locations:
            if not loc:  # Empty tuple = global veto
                return True

            # Check if location matches (considering wildcards)
            matches = True
            for i, (loc_idx, tgt_idx) in enumerate(zip(loc, target)):
                if tgt_idx is not None and loc_idx != tgt_idx:
                    matches = False
                    break
            if matches:
                return True

        # If no specific locations, any veto flag is global
        if self.veto_flags and not self.veto_locations:
            return True

        return False

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to JSON-compatible dict.

        Returns:
            Dict representation suitable for JSON serialization.
        """
        result: Dict[str, Any] = {
            "version": "3.0.0",
            "shape": list(self.shape),
            "rank": self.rank,
            "axis_names": list(self.axis_names),
            "axis_labels": self.axis_labels,
            "veto_flags": self.veto_flags,
            "veto_locations": [list(loc) for loc in self.veto_locations],
            "reason_codes": self.reason_codes,
            "is_sparse": self.is_sparse,
            "metadata": self.metadata,
            "extensions": self.extensions,
        }

        if self.is_sparse:
            sparse = self.to_sparse()
            result["sparse_coords"] = sparse.coords.tolist()
            result["sparse_values"] = sparse.values.tolist()
            result["fill_value"] = sparse.fill_value
        else:
            result["data"] = self.to_dense().tolist()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MoralTensor":
        """
        Deserialize from dict.

        Args:
            data: Dict representation from to_dict().

        Returns:
            MoralTensor instance.
        """
        shape = tuple(data["shape"])
        rank = data["rank"]
        axis_names = tuple(data["axis_names"])
        axis_labels = data.get("axis_labels", {})
        veto_flags = data.get("veto_flags", [])
        veto_locations = [tuple(loc) for loc in data.get("veto_locations", [])]
        reason_codes = data.get("reason_codes", [])
        is_sparse = data.get("is_sparse", False)
        metadata = data.get("metadata", {})
        extensions = data.get("extensions", {})

        if is_sparse:
            return cls.from_sparse(
                coords=np.array(data["sparse_coords"], dtype=np.int32),
                values=np.array(data["sparse_values"], dtype=np.float64),
                shape=shape,
                fill_value=data.get("fill_value", 0.0),
                axis_names=axis_names,
                axis_labels=axis_labels,
                veto_flags=veto_flags,
                veto_locations=veto_locations,
                reason_codes=reason_codes,
                metadata=metadata,
                extensions=extensions,
            )
        else:
            return cls.from_dense(
                data=np.array(data["data"], dtype=np.float64),
                axis_names=axis_names,
                axis_labels=axis_labels,
                veto_flags=veto_flags,
                veto_locations=veto_locations,
                reason_codes=reason_codes,
                metadata=metadata,
                extensions=extensions,
            )

    # -------------------------------------------------------------------------
    # Special Methods
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        """Concise string representation."""
        sparse_str = ", sparse" if self.is_sparse else ""
        veto_str = f", vetoes={len(self.veto_flags)}" if self.veto_flags else ""
        return f"MoralTensor(rank={self.rank}, shape={self.shape}{sparse_str}{veto_str})"

    def __eq__(self, other: object) -> bool:
        """
        Equality with numerical tolerance.

        Args:
            other: Object to compare.

        Returns:
            True if tensors are equal (within tolerance).
        """
        if not isinstance(other, MoralTensor):
            return False

        if self.shape != other.shape:
            return False

        if not np.allclose(self.to_dense(), other.to_dense(), rtol=1e-9, atol=1e-9):
            return False

        if set(self.veto_flags) != set(other.veto_flags):
            return False

        return True

    def summary(self) -> str:
        """
        Human-readable statistics summary.

        Returns:
            Multi-line string with tensor statistics.
        """
        data = self.to_dense()
        lines = [
            f"MoralTensor Summary",
            f"  Shape: {self.shape}",
            f"  Rank: {self.rank}",
            f"  Axes: {self.axis_names}",
            f"  Sparse: {self.is_sparse}",
            f"  Vetoes: {self.veto_flags if self.veto_flags else 'None'}",
            "",
            "  Dimension Statistics (across all indices):",
        ]

        for k, name in enumerate(MORAL_DIMENSION_NAMES):
            dim_data = data[k, ...].flatten()
            lines.append(
                f"    {name}: mean={dim_data.mean():.3f}, "
                f"min={dim_data.min():.3f}, max={dim_data.max():.3f}"
            )

        return "\n".join(lines)


__all__ = [
    "MoralTensor",
    "SparseCOO",
    "MORAL_DIMENSION_NAMES",
    "DIMENSION_INDEX",
    "DEFAULT_AXIS_NAMES",
]
