# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Bond Invariance Principle (BIP) verification.

Provides tools for verifying that ethical decisions depend on morally
relevant structure rather than arbitrary representational choices.

Version: 2.0.0 (DEME 2.0)
"""

from erisml.ethics.bip.verifier import (
    BIPVerifier,
    BIPVerificationResult,
    TransformType,
)

__all__ = [
    "BIPVerifier",
    "BIPVerificationResult",
    "TransformType",
]
