"""MIR ethics modules, each to its clause of docs/guides/DEME_EFM_Design_Guide_v0.1.md section 4."""

from erisml.ethics.mir.modules.autonomy_consent import AutonomyConsentEM
from erisml.ethics.mir.modules.oversight import HumanOversightEM
from erisml.ethics.mir.modules.safety import CorePhysicalSafetyEM, ProxemicsSafetyEM
from erisml.ethics.mir.modules.welfare import BeneficenceEM, PrivacyEM

__all__ = [
    "AutonomyConsentEM",
    "BeneficenceEM",
    "CorePhysicalSafetyEM",
    "HumanOversightEM",
    "PrivacyEM",
    "ProxemicsSafetyEM",
]
