# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the MIT License. See LICENSE.txt at the root of this repository.

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
