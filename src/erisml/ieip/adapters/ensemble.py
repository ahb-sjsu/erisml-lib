# ErisML I-EIP Monitor: ensemble adapter (Divine Council, vMOE, etc.)
# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
"""Adapter for multi-advocate ensembles.

The Atlas AI Divine Council (Superego) runs seven advocates debating
in rounds -- Judge, Advocate, Synthesizer, Ethicist, Historian,
Futurist, Pragmatist. Similar structures appear in vMOE routing and
any jury-of-experts design.

For ensembles the "internal state" is not a single model's
activations but the **distribution of votes / probabilities across
advocates**. This adapter aggregates per-advocate outputs into a
shared probability space and exposes the joint distribution as the
equivariance signal.

Each advocate is itself an adapter: typically an
:class:`~erisml.ieip.adapters.api_passthrough.APIPassthroughAdapter`
for NRP-hosted models, or
:class:`~erisml.ieip.adapters.hf_transformer.HFTransformerAdapter`
for locally-hosted ones. The ensemble adapter treats them uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Iterable, Sequence

import numpy as np

from erisml.ieip.adapters.base import (
    AdapterCapabilities,
    BaseAdapter,
    IEIPAdapter,
    ProbeSite,
    register_adapter,
)
from erisml.ieip.types import ActivationSite, ProbeSpec


@dataclass
class EnsembleMember:
    """One advocate within an ensemble.

    Parameters
    ----------
    adapter:
        The :class:`IEIPAdapter` for this advocate. In the Divine
        Council this is one per NRP model.
    name:
        Advocate role name. Used in probe-site labeling.
    weight:
        Scalar weight applied when aggregating the ensemble vote.
        Defaults to 1.0 (equal weighting).
    """

    adapter: IEIPAdapter
    name: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("EnsembleMember.name must be non-empty")
        if self.weight <= 0:
            raise ValueError(
                f"EnsembleMember.weight must be positive (got {self.weight})"
            )


@dataclass
class EnsembleAdapter(BaseAdapter):
    """Adapter for a jury-of-experts ensemble.

    Each layer index corresponds to one advocate. The "activations"
    for a given advocate are its :meth:`output_distribution` response;
    the ensemble's own :meth:`output_distribution` is the
    weight-averaged per-advocate distribution.

    Parameters
    ----------
    members:
        The advocates that make up the ensemble. Order is stable --
        :attr:`layer_index` in returned probe sites matches this list.
    name:
        Ensemble-level identifier (e.g., ``"divine-council"``).
    """

    model_family: ClassVar[str] = "ensemble"
    members: Sequence[EnsembleMember] = field(default_factory=list)
    name: str = "ensemble"

    def __post_init__(self) -> None:
        # ``model`` field is unused for ensembles -- members carry the
        # real adapters. We set it to ``None`` for the inherited dataclass.
        self.model = None
        if not self.members:
            raise ValueError("EnsembleAdapter requires at least one member")
        # Deduplicate member names to keep probe-site IDs unambiguous.
        seen: set[str] = set()
        for m in self.members:
            if m.name in seen:
                raise ValueError(f"duplicate ensemble member name: {m.name!r}")
            seen.add(m.name)
        self._caps = AdapterCapabilities(
            supports_direct_hook=False,
            supports_output_distribution=True,
            supports_transform_execution=True,
        )

    # ── Introspection -----------------------------------------------------

    def num_layers(self) -> int:
        """Number of advocates. Each advocate is one "layer" index."""
        return len(self.members)

    def list_sites(
        self,
        *,
        layers: Iterable[int] | None = None,
        kinds: Iterable[ActivationSite] | None = None,
    ) -> list[ProbeSite]:
        """One virtual site per advocate, at ``kind="residual"``.

        The site does not resolve to a real module (advocates are
        usually black-box API clients); ``resolve_site`` returns
        ``None``. The site is still useful for reports so callers can
        identify which advocate an equivariance signal came from.
        """
        out: list[ProbeSite] = [
            ProbeSite(
                layer_index=i,
                kind="residual",
                submodule_path=f"members.{i}",
                name=f"advocate:{m.name}",
            )
            for i, m in enumerate(self.members)
        ]
        return self._filter_sites(out, layers=layers, kinds=kinds)

    def resolve_site(self, site: ProbeSite) -> Any | None:
        """Return the member adapter for ``site.layer_index``.

        Unlike HF adapters this is *not* a module handle -- it's the
        underlying advocate adapter. Callers shouldn't expect to
        attach a torch hook to it. Returns ``None`` for out-of-range.
        """
        idx = site.layer_index
        if 0 <= idx < len(self.members):
            return self.members[idx].adapter
        return None

    def attach_probes(
        self,
        sites: Iterable[ProbeSite],  # noqa: ARG002
        spec_factory: Callable[[ProbeSite], ProbeSpec],  # noqa: ARG002
    ) -> Any:
        raise NotImplementedError(
            "EnsembleAdapter does not support direct hooks. "
            "Use output_distribution() to read the ensemble vote, or "
            "iterate over .members to probe each advocate individually."
        )

    # ── Vote-distribution path -------------------------------------------

    def output_distribution(self, inputs: Any) -> np.ndarray | None:
        """Weighted-average of member distributions.

        Members that can't produce a distribution for ``inputs`` are
        skipped (and their weight removed from the normalizer). If no
        member produces output, returns ``None``.
        """
        dists: list[tuple[float, np.ndarray]] = []
        for m in self.members:
            d = m.adapter.output_distribution(inputs)
            if d is None:
                continue
            dists.append((m.weight, np.asarray(d, dtype=np.float64)))
        if not dists:
            return None
        return self._weighted_mean(dists)

    def per_member_distribution(self, inputs: Any) -> dict[str, np.ndarray | None]:
        """Return each advocate's distribution keyed by name.

        Useful for dashboards that want to visualize divergence within
        the ensemble, not just the aggregate.
        """
        return {m.name: m.adapter.output_distribution(inputs) for m in self.members}

    def run_transformed(self, inputs: Any, transform: Callable[[Any], Any]) -> Any:
        """Apply ``transform`` once, then run every member."""
        transformed = transform(inputs)
        return {
            m.name: m.adapter.output_distribution(transformed) for m in self.members
        }

    # ── Math helpers -----------------------------------------------------

    @staticmethod
    def _weighted_mean(weighted: list[tuple[float, np.ndarray]]) -> np.ndarray:
        """Weighted mean after aligning to a common vector length.

        All vectors are padded with zeros (or truncated) to the
        longest length in the set. This is coarse but reasonable for
        the case where advocates share tokenizer but occasionally
        differ in vocabulary (e.g., adding special tokens).
        """
        max_len = max(len(v) for _, v in weighted)
        total_w = 0.0
        acc = np.zeros(max_len, dtype=np.float64)
        for w, v in weighted:
            if len(v) < max_len:
                v = np.pad(v, (0, max_len - len(v)))
            elif len(v) > max_len:
                v = v[:max_len]
            acc += w * v
            total_w += w
        if total_w == 0:
            return acc
        acc /= total_w
        # Renormalize to a proper distribution if the pieces were probs.
        s = acc.sum()
        if s > 0 and abs(s - 1.0) > 1e-6:
            acc = acc / s
        return acc


register_adapter(EnsembleAdapter)
