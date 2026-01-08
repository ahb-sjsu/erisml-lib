# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
EM Registry: Central registry for ethics modules with tier classification.

Provides decorator-based registration and tier-based lookup for the
DEME 2.0 tiered EM architecture.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.modules.base import EthicsModuleV2


@dataclass
class EMRegistryEntry:
    """Entry in the EM registry."""

    em_class: Type[EthicsModuleV2]
    """The EM class."""

    tier: int
    """Tier classification (0-4)."""

    default_weight: float
    """Default weight for governance aggregation."""

    veto_capable: bool
    """Whether this EM can trigger vetoes."""

    description: str
    """Human-readable description."""

    tags: List[str]
    """Classification tags for filtering."""


class EMRegistry:
    """
    Central registry for ethics modules.

    Provides:
    - Decorator-based registration
    - Tier-based lookup
    - Tag-based filtering
    - Default weight configuration
    """

    _entries: Dict[str, EMRegistryEntry] = {}
    _by_tier: Dict[int, List[str]] = {i: [] for i in range(5)}

    @classmethod
    def register(
        cls,
        tier: int,
        default_weight: float = 1.0,
        veto_capable: bool = True,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Callable[[Type[EthicsModuleV2]], Type[EthicsModuleV2]]:
        """
        Decorator to register an EM.

        Args:
            tier: Tier classification (0-4).
            default_weight: Default weight for aggregation.
            veto_capable: Whether EM can trigger vetoes.
            description: Human-readable description.
            tags: Classification tags.

        Returns:
            Decorator function.

        Example:
            @EMRegistry.register(
                tier=0,
                default_weight=10.0,
                veto_capable=True,
                description="Geneva convention constraints",
            )
            class GenevaEMV2(BaseEthicsModuleV2):
                ...
        """
        if tags is None:
            tags = []

        def decorator(em_class: Type[EthicsModuleV2]) -> Type[EthicsModuleV2]:
            name = em_class.__name__
            entry = EMRegistryEntry(
                em_class=em_class,
                tier=tier,
                default_weight=default_weight,
                veto_capable=veto_capable,
                description=description,
                tags=tags,
            )
            cls._entries[name] = entry
            cls._by_tier[tier].append(name)
            return em_class

        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[EMRegistryEntry]:
        """Get an entry by EM class name."""
        return cls._entries.get(name)

    @classmethod
    def get_class(cls, name: str) -> Optional[Type[EthicsModuleV2]]:
        """Get an EM class by name."""
        entry = cls._entries.get(name)
        return entry.em_class if entry else None

    @classmethod
    def get_by_tier(cls, tier: int) -> List[EMRegistryEntry]:
        """Get all entries for a tier."""
        names = cls._by_tier.get(tier, [])
        return [cls._entries[name] for name in names if name in cls._entries]

    @classmethod
    def get_by_tag(cls, tag: str) -> List[EMRegistryEntry]:
        """Get all entries with a specific tag."""
        return [entry for entry in cls._entries.values() if tag in entry.tags]

    @classmethod
    def all_entries(cls) -> List[EMRegistryEntry]:
        """Get all registered entries."""
        return list(cls._entries.values())

    @classmethod
    def tier_names(cls) -> Dict[int, str]:
        """Get human-readable tier names."""
        return {
            0: "Constitutional",
            1: "Core Safety",
            2: "Rights/Fairness",
            3: "Soft Values",
            4: "Meta-Governance",
        }

    @classmethod
    def instantiate(cls, name: str, **kwargs) -> Optional[EthicsModuleV2]:
        """
        Instantiate an EM by name.

        Args:
            name: Class name of the EM.
            **kwargs: Arguments to pass to constructor.

        Returns:
            Instantiated EM or None if not found.
        """
        em_class = cls.get_class(name)
        if em_class is None:
            return None
        return em_class(**kwargs)

    @classmethod
    def instantiate_tier(cls, tier: int, **kwargs) -> List[EthicsModuleV2]:
        """
        Instantiate all EMs in a tier.

        Args:
            tier: Tier number (0-4).
            **kwargs: Arguments to pass to constructors.

        Returns:
            List of instantiated EMs.
        """
        entries = cls.get_by_tier(tier)
        return [entry.em_class(**kwargs) for entry in entries]

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (for testing)."""
        cls._entries.clear()
        cls._by_tier = {i: [] for i in range(5)}


__all__ = [
    "EMRegistryEntry",
    "EMRegistry",
]
