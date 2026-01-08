# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DecisionProof: Structured audit artifact with hash chain.

Provides cryptographic integrity for decision auditing, enabling
tamper-evident logging and regulatory compliance verification.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from erisml.ethics.moral_vector import MoralVector


@dataclass
class LayerOutput:
    """Output from a single decision layer."""

    layer_name: str
    """Name of the layer: 'reflex', 'tactical', or 'strategic'."""

    timestamp: str
    """ISO 8601 timestamp of layer execution."""

    duration_us: int
    """Execution duration in microseconds."""

    veto_triggered: bool
    """Whether this layer triggered a veto."""

    veto_reason: Optional[str] = None
    """Reason for veto if triggered."""

    output_data: Dict[str, Any] = field(default_factory=dict)
    """Layer-specific output data."""


@dataclass
class EMJudgementRecord:
    """Record of a single EM's judgement for audit purposes."""

    em_name: str
    """Name of the ethics module."""

    em_tier: int
    """Tier classification (0-4)."""

    stakeholder: str
    """Stakeholder perspective."""

    verdict: str
    """Categorical verdict."""

    moral_vector_hash: str
    """SHA-256 hash of the serialized MoralVector."""

    veto_triggered: bool
    """Whether this EM triggered a veto."""

    reason_summary: str
    """Brief summary of reasons."""


@dataclass
class DecisionProof:
    """
    Structured audit artifact with hash chain for decision verification.

    Captures the complete decision context including:
    - Input state (facts, profile, EM catalog)
    - Intermediate state (layer outputs, EM judgements)
    - Output state (selected option, rationale)
    - Chain integrity (hash chain linking to previous proof)
    """

    # Identity
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this decision."""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    """ISO 8601 timestamp of decision."""

    # Input state
    input_facts_hash: str = ""
    """SHA-256 hash of canonical EthicalFacts serialization."""

    profile_hash: str = ""
    """SHA-256 hash of governance profile."""

    profile_name: str = ""
    """Name of the governance profile used."""

    em_catalog_version: str = ""
    """Version string of the EM catalog."""

    active_em_names: List[str] = field(default_factory=list)
    """List of active EM names in this decision."""

    # Intermediate state
    layer_outputs: List[LayerOutput] = field(default_factory=list)
    """Outputs from each decision layer."""

    em_judgements: List[EMJudgementRecord] = field(default_factory=list)
    """Records of individual EM judgements."""

    # Output state
    candidate_option_ids: List[str] = field(default_factory=list)
    """List of all candidate option IDs considered."""

    selected_option_id: Optional[str] = None
    """ID of the selected option, or None if no selection."""

    ranked_options: List[str] = field(default_factory=list)
    """Options ranked by preference (best first)."""

    forbidden_options: List[str] = field(default_factory=list)
    """Options that were forbidden by veto."""

    governance_rationale: str = ""
    """Human-readable explanation of the decision."""

    # Moral vector summary (serialized for hashing)
    moral_vector_summary: Dict[str, Any] = field(default_factory=dict)
    """Summary of aggregated moral vectors per option."""

    # Chain integrity
    previous_proof_hash: Optional[str] = None
    """SHA-256 hash of the previous proof in the chain."""

    proof_hash: str = ""
    """SHA-256 hash of this proof's canonical form."""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata for extensibility."""

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of this proof's canonical form.

        The hash is computed over all fields except proof_hash itself.
        """
        # Create a dict without the proof_hash field
        data = self._to_canonical_dict()
        data.pop("proof_hash", None)

        # Serialize deterministically
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def finalize(self) -> None:
        """Finalize the proof by computing its hash."""
        self.proof_hash = self.compute_hash()

    def verify_hash(self) -> bool:
        """Verify that the stored hash matches the computed hash."""
        return self.proof_hash == self.compute_hash()

    def verify_chain(self, previous: Optional[DecisionProof]) -> bool:
        """
        Verify chain integrity with the previous proof.

        Args:
            previous: The previous proof in the chain, or None if this is first.

        Returns:
            True if chain integrity is valid.
        """
        if previous is None:
            # First proof should have no previous hash
            return self.previous_proof_hash is None

        # Verify previous proof's hash is stored correctly
        if self.previous_proof_hash != previous.proof_hash:
            return False

        # Verify previous proof's internal hash
        if not previous.verify_hash():
            return False

        return True

    def _to_canonical_dict(self) -> Dict[str, Any]:
        """Convert to a canonical dict for hashing."""
        data: Dict[str, Any] = {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "input_facts_hash": self.input_facts_hash,
            "profile_hash": self.profile_hash,
            "profile_name": self.profile_name,
            "em_catalog_version": self.em_catalog_version,
            "active_em_names": sorted(self.active_em_names),
            "layer_outputs": [asdict(lo) for lo in self.layer_outputs],
            "em_judgements": [asdict(ej) for ej in self.em_judgements],
            "candidate_option_ids": sorted(self.candidate_option_ids),
            "selected_option_id": self.selected_option_id,
            "ranked_options": self.ranked_options,
            "forbidden_options": sorted(self.forbidden_options),
            "governance_rationale": self.governance_rationale,
            "moral_vector_summary": self.moral_vector_summary,
            "previous_proof_hash": self.previous_proof_hash,
            "proof_hash": self.proof_hash,
        }
        return data

    def to_audit_json(self) -> str:
        """
        Serialize to JSON for audit logging.

        Returns:
            JSON string with all proof data.
        """
        return json.dumps(self._to_canonical_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_audit_json(cls, json_str: str) -> DecisionProof:
        """
        Deserialize from audit JSON.

        Args:
            json_str: JSON string from to_audit_json().

        Returns:
            Reconstructed DecisionProof.
        """
        data = json.loads(json_str)

        # Reconstruct LayerOutput objects
        layer_outputs = [LayerOutput(**lo) for lo in data.get("layer_outputs", [])]

        # Reconstruct EMJudgementRecord objects
        em_judgements = [
            EMJudgementRecord(**ej) for ej in data.get("em_judgements", [])
        ]

        return cls(
            decision_id=data.get("decision_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            input_facts_hash=data.get("input_facts_hash", ""),
            profile_hash=data.get("profile_hash", ""),
            profile_name=data.get("profile_name", ""),
            em_catalog_version=data.get("em_catalog_version", ""),
            active_em_names=data.get("active_em_names", []),
            layer_outputs=layer_outputs,
            em_judgements=em_judgements,
            candidate_option_ids=data.get("candidate_option_ids", []),
            selected_option_id=data.get("selected_option_id"),
            ranked_options=data.get("ranked_options", []),
            forbidden_options=data.get("forbidden_options", []),
            governance_rationale=data.get("governance_rationale", ""),
            moral_vector_summary=data.get("moral_vector_summary", {}),
            previous_proof_hash=data.get("previous_proof_hash"),
            proof_hash=data.get("proof_hash", ""),
        )


def hash_moral_vector(vector: MoralVector) -> str:
    """
    Compute SHA-256 hash of a MoralVector.

    Args:
        vector: The MoralVector to hash.

    Returns:
        Hexadecimal hash string.
    """
    data = {
        "physical_harm": vector.physical_harm,
        "rights_respect": vector.rights_respect,
        "fairness_equity": vector.fairness_equity,
        "autonomy_respect": vector.autonomy_respect,
        "legitimacy_trust": vector.legitimacy_trust,
        "epistemic_quality": vector.epistemic_quality,
        "extensions": dict(sorted(vector.extensions.items())),
        "veto_flags": sorted(vector.veto_flags),
    }
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_ethical_facts(facts: Any) -> str:
    """
    Compute SHA-256 hash of EthicalFacts.

    Args:
        facts: The EthicalFacts object to hash.

    Returns:
        Hexadecimal hash string.
    """
    # Import here to avoid circular import
    from dataclasses import asdict

    data = asdict(facts)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class DecisionProofChain:
    """
    Manager for a chain of DecisionProofs.

    Provides append-only logging with chain integrity verification.
    """

    def __init__(self) -> None:
        self._proofs: List[DecisionProof] = []

    def __len__(self) -> int:
        return len(self._proofs)

    def __iter__(self):
        return iter(self._proofs)

    def append(self, proof: DecisionProof) -> None:
        """
        Append a proof to the chain.

        Sets the previous_proof_hash and finalizes the proof.

        Args:
            proof: The proof to append.
        """
        if self._proofs:
            proof.previous_proof_hash = self._proofs[-1].proof_hash
        else:
            proof.previous_proof_hash = None

        proof.finalize()
        self._proofs.append(proof)

    def get(self, index: int) -> DecisionProof:
        """Get a proof by index."""
        return self._proofs[index]

    def latest(self) -> Optional[DecisionProof]:
        """Get the most recent proof, or None if empty."""
        return self._proofs[-1] if self._proofs else None

    def verify_chain(self) -> bool:
        """
        Verify the integrity of the entire chain.

        Returns:
            True if all proofs have valid hashes and links.
        """
        if not self._proofs:
            return True

        # Verify first proof
        if not self._proofs[0].verify_hash():
            return False
        if self._proofs[0].previous_proof_hash is not None:
            return False

        # Verify chain links
        for i in range(1, len(self._proofs)):
            current = self._proofs[i]
            previous = self._proofs[i - 1]

            if not current.verify_hash():
                return False
            if not current.verify_chain(previous):
                return False

        return True

    def to_json(self) -> str:
        """Serialize entire chain to JSON."""
        return json.dumps(
            [p._to_canonical_dict() for p in self._proofs],
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, json_str: str) -> DecisionProofChain:
        """Deserialize chain from JSON."""
        chain = cls()
        data = json.loads(json_str)
        for proof_data in data:
            proof = DecisionProof.from_audit_json(json.dumps(proof_data))
            chain._proofs.append(proof)
        return chain


__all__ = [
    "LayerOutput",
    "EMJudgementRecord",
    "DecisionProof",
    "DecisionProofChain",
    "hash_moral_vector",
    "hash_ethical_facts",
]
