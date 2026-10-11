"""An executed governance profile: the lens of the Bond Invariance Principle, in the shape of
docs/guides/DEME_EFM_Design_Guide_v0.1.md section 7.

A profile names a context template, a composition pattern, its levels and, per level, the active
modules with their binding mode and parameters. Unlike the stored profiles of profile_v03 and
profile_v04 ("these fields do not by themselves enforce anything"), this one is executed: `apply`
runs the pattern it names over a MIR, and every result carries the profile's hash.

Format (JSON or a YAML file with the same keys):

    {"name": "home_care_robot", "version": "1.0", "template": "ROUTINE_CIVIL",
     "pattern": "lexicographic",
     "levels": [{"name": "safety", "modules": [{"module": "core_physical_safety",
                                                "params": {"injury_threshold": 0.3}}]}, ...],
     "theta_prob": 0.5, "theta_count": 10}

Validation (the integrity the Guide asks of ProfileIntegrity-EM, 4.5.2): a known pattern, known
module names, no module twice, a module's params a mapping, no empty level, and, when
`required_modules` is given, each of them present. A profile that fails validation does not load.
The order of levels is the profile's to choose (Guide 5.3 names the levels by content, and 6.2 wraps
HumanOversight around the pattern rather than ordering it by tier).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from erisml.ethics.mir.modules import (
    AutonomyConsentEM,
    BeneficenceEM,
    CorePhysicalSafetyEM,
    HumanOversightEM,
    PrivacyEM,
    ProxemicsSafetyEM,
)
from erisml.ethics.mir.pattern import (
    Level,
    ModuleSlot,
    PatternResult,
    run_lexicographic,
)
from erisml.ethics.mir.record import MoralInterfaceRecord

MODULES = {
    m.name: m
    for m in (
        AutonomyConsentEM(),
        BeneficenceEM(),
        CorePhysicalSafetyEM(),
        HumanOversightEM(),
        PrivacyEM(),
        ProxemicsSafetyEM(),
    )
}
PATTERNS = ("lexicographic",)


class ProfileError(ValueError):
    """A profile that does not pass validation."""


@dataclass(frozen=True)
class ExecutedProfile:
    name: str
    version: str
    template: str
    pattern: str
    levels: tuple
    theta_prob: float
    theta_count: int
    source: Mapping[str, Any]

    @property
    def hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.source, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def apply(self, mir: MoralInterfaceRecord) -> "LensResult":
        result = run_lexicographic(mir, self.levels)
        return LensResult(result, self.hash, self.name, self.version)


@dataclass(frozen=True)
class LensResult:
    pattern: PatternResult
    profile_hash: str
    profile_name: str
    profile_version: str

    @property
    def selected(self) -> Optional[str]:
        return self.pattern.selected

    def proof(self, previous: Optional[Any] = None) -> Any:
        """A finalized DecisionProof for the audit ledger: the MIR hash as the input hash, the
        profile's name and hash, one layer record per pattern level, the ranking, the vetoed and
        soft-blocked actions, and a link to `previous` (a DecisionProof) when given."""
        from datetime import datetime, timezone

        from erisml.ethics.decision_proof import DecisionProof, LayerOutput

        now = datetime.now(timezone.utc).isoformat()
        p = self.pattern
        layers = [
            LayerOutput(
                layer_name=t.name,
                timestamp=now,
                duration_us=0,
                veto_triggered=bool(t.vetoed),
                veto_reason="; ".join(
                    f"{a}: {', '.join(r)}" for a, r in t.vetoed.items()
                )
                or None,
                output_data={
                    "entered": t.entered,
                    "kept": t.kept,
                    "scores": t.scores,
                    "failures": t.failures,
                },
            )
            for t in p.trace
        ]
        candidates = list(
            dict.fromkeys(t for lt in p.trace for t in lt.entered)
        ) or list(p.ranked)
        rationale = (
            f"lexicographic under {self.profile_name} {self.profile_version}: selected {p.selected}"
            if p.selected
            else f"lexicographic under {self.profile_name} {self.profile_version}: "
            f"no action survived"
        )
        proof = DecisionProof(
            input_facts_hash=p.mir_hash,
            profile_hash=self.profile_hash,
            profile_name=self.profile_name,
            em_catalog_version="mir-1.0",
            layer_outputs=layers,
            candidate_option_ids=candidates,
            selected_option_id=p.selected,
            ranked_options=list(p.ranked),
            forbidden_options=sorted(p.vetoed),
            governance_rationale=rationale,
            previous_proof_hash=getattr(previous, "proof_hash", None),
            metadata={
                "soft_blocked": p.soft_blocked,
                "annotations": p.annotations,
                "health_ok": p.health_ok,
                "vetoed": p.vetoed,
            },
        )
        proof.finalize()
        return proof


def load_profile(
    source: Union[str, Path, Mapping[str, Any]], required_modules: Sequence[str] = ()
) -> ExecutedProfile:
    if not isinstance(source, Mapping):
        path = Path(source)
        text = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            import yaml

            source = yaml.safe_load(text)
        else:
            source = json.loads(text)
    data: Dict[str, Any] = dict(source)
    for key in ("name", "version", "template", "pattern", "levels"):
        if key not in data:
            raise ProfileError(f"profile has no {key!r}")
    if data["pattern"] not in PATTERNS:
        raise ProfileError(f"pattern {data['pattern']!r} is not one of {PATTERNS}")
    seen: List[str] = []
    levels: List[Level] = []
    for spec in data["levels"]:
        slots = []
        for m in spec.get("modules", []):
            name = m.get("module")
            if name not in MODULES:
                raise ProfileError(
                    f"unknown module {name!r} (known: {sorted(MODULES)})"
                )
            if name in seen:
                raise ProfileError(f"module {name!r} appears twice")
            params = m.get("params", {})
            if not isinstance(params, Mapping):
                raise ProfileError(f"params of {name!r} are not a mapping")
            binding = m.get("binding")
            if binding is not None and not isinstance(binding, bool):
                raise ProfileError(f"binding of {name!r} is not a boolean")
            seen.append(name)
            slots.append(ModuleSlot(MODULES[name], dict(params), binding))
        if not slots:
            raise ProfileError(f"level {spec.get('name')!r} has no modules")
        levels.append(
            Level(
                str(spec.get("name")), tuple(slots), float(spec.get("tolerance", 1e-9))
            )
        )
    missing = [m for m in required_modules if m not in seen]
    if missing:
        raise ProfileError(f"required modules missing: {missing}")
    return ExecutedProfile(
        str(data["name"]),
        str(data["version"]),
        str(data["template"]),
        data["pattern"],
        tuple(levels),
        float(data.get("theta_prob", 0.5)),
        int(data.get("theta_count", 10)),
        data,
    )
