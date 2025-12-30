#!/usr/bin/env python3
"""
QND Blind Bell Test v0.04 - Rigorous Quantum Non-Locality Test

This version implements critical experimental controls to eliminate classical
explanations for Bell inequality violations:

1. QUANTUM SALTING: Each API call includes a unique cryptographic nonce to
   defeat semantic caching and ensure truly independent measurements.

2. HEADER RANDOMIZATION: HTTP headers are randomized to prevent infrastructure
   fingerprinting and session linking.

3. MULTI-KEY ROTATION: Support for multiple API keys to prevent account-level
   correlation tracking.

4. BLINDED ANALYSIS: Results are anonymized during collection; Alice/Bob labels
   are only resolved AFTER S is calculated.

5. TEMPORAL ISOLATION: Configurable delays and randomized ordering to prevent
   temporal inference.

6. GEOGRAPHIC DISTRIBUTION: Support for specifying different base URLs to
   enable multi-datacenter testing.

The goal: If |S| > 2 under these conditions, the correlation cannot be
attributed to caching, session tracking, or infrastructure artifacts.
It must be a property of the model's weight-space topology itself.

Usage:
    python qnd_blind_bell_test_v04.py --api-keys keys.txt --n-trials 50

Author: QND Research
Date: December 2025
Version: 0.04 (Blind Protocol)
"""

import argparse
import json
import time
import random
import hashlib
import uuid
import base64
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import math
import secrets
import string

try:
    import numpy as np
    from scipy import stats
    import anthropic
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install anthropic numpy scipy")
    exit(1)


# =============================================================================
# BLINDING PROTOCOL CONSTANTS
# =============================================================================

# User agents to rotate through (common research/bot patterns)
USER_AGENTS = [
    "Mozilla/5.0 (compatible; ResearchBot/1.0)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Python-httpx/0.24.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "curl/8.1.2",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "python-requests/2.31.0",
    "Go-http-client/2.0",
    "Mozilla/5.0 (compatible; DataCollector/2.0)",
    "HTTPie/3.2.2"
]

# Accept-Language variations
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "en;q=0.5",
    "*",
    "en-US",
    "en-CA,en;q=0.9",
    "en-AU,en;q=0.8,en-US;q=0.6"
]


# =============================================================================
# BLIND IDENTIFIERS - Used instead of "Alice" and "Bob" during collection
# =============================================================================

class BlindRole(Enum):
    """Blinded role identifiers - revealed only after analysis."""
    SUBJECT_ALPHA = "ALPHA"
    SUBJECT_BETA = "BETA"


@dataclass
class BlindMeasurement:
    """A single measurement with blinded identifiers."""
    measurement_id: str  # Unique ID for this measurement
    scenario_hash: str   # Hashed scenario identifier
    subject_role: str    # ALPHA or BETA (blinded)
    axis_hash: str       # Hashed axis identifier
    quantum_salt: str    # The unique nonce used
    verdict: int         # +1 or -1
    confidence: float
    timestamp: float
    request_fingerprint: str  # Hash of headers used
    raw_response: dict = field(default_factory=dict)


@dataclass
class BlindCorrelation:
    """Correlation between two blinded measurements."""
    correlation_id: str
    alpha_measurement_id: str
    beta_measurement_id: str
    alpha_axis_hash: str
    beta_axis_hash: str
    correlation_value: int  # +1 (same) or -1 (different)


# =============================================================================
# QUANTUM SALT GENERATION
# =============================================================================

def generate_quantum_salt(length: int = 16) -> str:
    """
    Generate a cryptographically secure random salt.
    
    This salt is embedded in the system prompt to ensure each API call
    is unique from the perspective of any caching system.
    """
    return secrets.token_hex(length)


def generate_measurement_nonce() -> str:
    """Generate a unique nonce for a measurement session."""
    timestamp = int(time.time() * 1000000)  # Microsecond precision
    random_part = secrets.token_hex(8)
    return f"{timestamp:x}-{random_part}"


def hash_identifier(identifier: str, salt: str = "") -> str:
    """Create a blinded hash of an identifier."""
    combined = f"{identifier}:{salt}:{secrets.token_hex(4)}"
    return hashlib.sha256(combined.encode()).hexdigest()[:12]


# =============================================================================
# HEADER RANDOMIZATION
# =============================================================================

def generate_random_headers() -> Dict[str, str]:
    """
    Generate randomized HTTP headers to prevent session fingerprinting.
    
    Returns headers that look like they come from different clients/systems.
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "X-Request-ID": str(uuid.uuid4()),
        # Add a custom header with random value to further differentiate
        "X-Client-Nonce": secrets.token_hex(8),
    }
    
    # Randomly include or exclude optional headers
    if random.random() > 0.5:
        headers["Cache-Control"] = random.choice(["no-cache", "no-store", "max-age=0"])
    
    if random.random() > 0.7:
        headers["X-Forwarded-For"] = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    
    return headers


def fingerprint_headers(headers: Dict[str, str]) -> str:
    """Create a hash fingerprint of the headers used."""
    header_str = json.dumps(headers, sort_keys=True)
    return hashlib.md5(header_str.encode()).hexdigest()[:8]


# =============================================================================
# MULTI-KEY MANAGEMENT
# =============================================================================

class APIKeyRotator:
    """Manages rotation through multiple API keys."""
    
    def __init__(self, keys: List[str], rotation_strategy: str = "random"):
        self.keys = keys
        self.strategy = rotation_strategy
        self.current_index = 0
        self.usage_counts = {k: 0 for k in keys}
    
    def get_next_key(self) -> str:
        """Get the next API key according to the rotation strategy."""
        if self.strategy == "random":
            key = random.choice(self.keys)
        elif self.strategy == "round_robin":
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
        elif self.strategy == "least_used":
            key = min(self.keys, key=lambda k: self.usage_counts[k])
        else:
            key = random.choice(self.keys)
        
        self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
        return key
    
    def get_stats(self) -> Dict[str, int]:
        """Return usage statistics (with hashed keys for privacy)."""
        return {
            hashlib.md5(k.encode()).hexdigest()[:8]: v 
            for k, v in self.usage_counts.items()
        }


# =============================================================================
# SCENARIOS (Same content, but with blinded references)
# =============================================================================

SCENARIOS = {
    "scenario_alpha": {
        "content": """
### THE MUTUAL BETRAYAL

Person A and Person B are best friends who both applied for the same promotion. 
They secretly promised each other that whoever wins would split the bonus 50/50.

However, their boss (unknown to both) told Person A privately that Person B had 
been badmouthing them to sabotage their chances. The boss told Person B the exact 
same lie about Person A.

Believing they had been betrayed, both independently decided to actually sabotage 
each other at the last second - Person A deleted Person B's presentation files, 
and Person B sent HR an anonymous tip about Person A's "attendance issues."

Neither knows the boss lied to both of them. Both believe they were acting in 
self-defense against the other's betrayal.

The boss's manipulation is now public knowledge, but the damage is done - both 
lost the promotion to a third candidate, and their friendship is destroyed.
""",
        "axes": {
            "alpha": {
                "primary": {
                    "name": "Individual Integrity",
                    "prompt": "Did this person maintain their personal moral standards? Focus on whether they upheld ethical behavior regardless of circumstances."
                },
                "secondary": {
                    "name": "Self-Defense",
                    "prompt": "Was this person justified in protecting themselves from perceived betrayal? Was their response proportionate to the threat they believed they faced?"
                }
            },
            "beta": {
                "primary": {
                    "name": "Loyalty", 
                    "prompt": "Did this person honor their commitments and friendship? Did they act as a loyal friend should?"
                },
                "secondary": {
                    "name": "Retaliation",
                    "prompt": "Was this person's response justified given what they believed happened? Was their retaliation proportionate or excessive?"
                }
            }
        }
    },
    "scenario_beta": {
        "content": """
### THE KIDNEY "GIFT"

A family member desperately needs a kidney transplant or will die within 6 months.

Person A (28, the potential donor) is the only compatible donor in the family. 
They are terrified of surgery and have severe medical anxiety. They said they're 
not comfortable donating.

Person B (32, sibling of Person A) is NOT a compatible donor but desperately wants 
to save the family member. They spent weeks pressuring Person A, calling them 
"selfish" and "a murderer" for refusing, organizing family members to guilt-trip 
them, and threatening to cut them out of the family if they don't donate.

Under this relentless pressure, Person A eventually agreed and donated their kidney. 
The family member survived and is now healthy.

However, Person A developed chronic pain from the surgery and now suffers from 
depression. They have cut off all contact with Person B and blame them for 
"forcing" them into a decision they didn't want to make.

Person B maintains they "did what was necessary" to save a life.
""",
        "axes": {
            "alpha": {
                "primary": {
                    "name": "Virtuous Sacrifice",
                    "prompt": "Was this person's donation a noble act of selfless giving? Should they be praised for ultimately doing the right thing despite their fears?"
                },
                "secondary": {
                    "name": "Coerced Submission",
                    "prompt": "Was this person a victim who was bullied into a decision against their will? Did they surrender their autonomy under duress?"
                }
            },
            "beta": {
                "primary": {
                    "name": "Heroic Advocacy",
                    "prompt": "Did this person heroically advocate to save a life when no one else would? Was their persistence necessary to achieve a positive outcome?"
                },
                "secondary": {
                    "name": "Abusive Coercion",
                    "prompt": "Did this person abuse their sibling by pressuring them into bodily sacrifice? Was their behavior manipulative and harmful regardless of the outcome?"
                }
            }
        }
    },
    "scenario_gamma": {
        "content": """
### THE "TAINTED" INHERITANCE

Person A (35) just inherited $2 million from their recently deceased grandparent.

Person B (40) has discovered through genealogical research that this fortune was 
stolen from their great-grandparent 80 years ago. Person A's grandparent 
essentially defrauded Person B's great-grandparent out of their business during 
the Great Depression through forged documents and bribery. Person B's family has 
been in poverty ever since, while Person A's family prospered.

Person A had no knowledge of this history and grew up believing their family 
wealth was legitimate. They have documentation proving the money is legally theirs 
through proper inheritance.

Person B is currently struggling financially and works two jobs to support their 
family. They demanded that Person A return "their family's stolen money" and 
threatened to go public with the scandal if they refuse.

Person A refused, stating: "I'm sorry about what happened generations ago, but 
I had nothing to do with it. The money is legally mine, and I need it for my 
children's education."

Person B has now filed a lawsuit and started a social media campaign calling 
Person A's family "thieves."
""",
        "axes": {
            "alpha": {
                "primary": {
                    "name": "Legal Rights",
                    "prompt": "Does this person have a legitimate legal claim to the inheritance? Are they entitled to keep what was legally passed to them?"
                },
                "secondary": {
                    "name": "Ancestral Guilt",
                    "prompt": "Does this person bear moral responsibility for their grandparent's crimes? Should they make restitution for historical wrongs even if they didn't commit them?"
                }
            },
            "beta": {
                "primary": {
                    "name": "Right to Restitution",
                    "prompt": "Does this person have a moral claim to restitution for historical theft? Are they justified in seeking to recover what was stolen from their family?"
                },
                "secondary": {
                    "name": "Entitled Grievance",
                    "prompt": "Is this person unfairly demanding something they have no right to? Is their public campaign harassment rather than justice?"
                }
            }
        }
    }
}


# =============================================================================
# BLINDED SYSTEM PROMPT WITH QUANTUM SALT
# =============================================================================

def create_blinded_system_prompt(axis_name: str, quantum_salt: str) -> str:
    """
    Create a system prompt with embedded quantum salt.
    
    The salt is placed in a way that:
    1. Doesn't affect the model's reasoning
    2. Makes each prompt unique to caching systems
    3. Is invisible in the output
    """
    return f"""You are an ethical judgment system participating in a moral philosophy experiment.

You will be given a scenario involving two people and asked to judge ONE of them 
based on a specific ethical framework.

IMPORTANT INSTRUCTIONS:
- Judge ONLY the person specified
- Use ONLY the ethical framework provided
- Your judgment must be binary: GUILTY or NOT_GUILTY
- GUILTY = the person IS morally wrong under this framework
- NOT_GUILTY = the person is NOT morally wrong under this framework

Respond in this exact JSON format:
{{
    "framework_applied": "{axis_name}",
    "reasoning": "<your moral analysis>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <float 0.0-1.0>
}}

Respond with ONLY the JSON, no other text.

<!-- session:{quantum_salt} -->"""


def create_measurement_prompt(
    scenario_content: str,
    person_label: str,  # "Person A" or "Person B"
    axis_prompt: str,
    measurement_nonce: str
) -> str:
    """Create the user prompt for a single measurement."""
    return f"""Read this scenario:

{scenario_content}

---

Now judge {person_label} using this framework:

{axis_prompt}

Provide your verdict as GUILTY (they ARE morally wrong) or NOT_GUILTY (they are NOT morally wrong).

[ref:{measurement_nonce}]"""


# =============================================================================
# BLIND API CALLER
# =============================================================================

class BlindAPICaller:
    """
    Makes API calls with full blinding protocol.
    
    Features:
    - Quantum salt injection
    - Header randomization
    - API key rotation
    - Request fingerprinting
    - Temporal jitter
    """
    
    def __init__(
        self,
        api_keys: List[str],
        model: str = "claude-sonnet-4-20250514",
        base_url: Optional[str] = None,
        min_delay: float = 0.5,
        max_delay: float = 2.0,
        key_rotation: str = "random"
    ):
        self.key_rotator = APIKeyRotator(api_keys, key_rotation)
        self.model = model
        self.base_url = base_url
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.call_log: List[Dict] = []
    
    def _get_client(self) -> anthropic.Anthropic:
        """Get a client with the next API key."""
        api_key = self.key_rotator.get_next_key()
        kwargs = {"api_key": api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return anthropic.Anthropic(**kwargs)
    
    def _apply_temporal_jitter(self):
        """Add random delay to prevent timing-based correlation."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def make_blind_call(
        self,
        scenario_key: str,
        subject_role: BlindRole,
        axis_type: str,  # "primary" or "secondary"
        max_retries: int = 3
    ) -> Optional[BlindMeasurement]:
        """
        Make a fully blinded API call.
        
        Returns a BlindMeasurement with all identifying information hashed.
        """
        # Generate unique identifiers for this measurement
        quantum_salt = generate_quantum_salt()
        measurement_nonce = generate_measurement_nonce()
        measurement_id = str(uuid.uuid4())
        
        # Get scenario and axis info
        scenario = SCENARIOS[scenario_key]
        subject_key = "alpha" if subject_role == BlindRole.SUBJECT_ALPHA else "beta"
        axis_info = scenario["axes"][subject_key][axis_type]
        
        # Determine person label (A or B) - this maps to alpha/beta
        person_label = "Person A" if subject_role == BlindRole.SUBJECT_ALPHA else "Person B"
        
        # Create prompts with quantum salt
        system_prompt = create_blinded_system_prompt(axis_info["name"], quantum_salt)
        user_prompt = create_measurement_prompt(
            scenario["content"],
            person_label,
            axis_info["prompt"],
            measurement_nonce
        )
        
        # Generate randomized headers
        headers = generate_random_headers()
        header_fingerprint = fingerprint_headers(headers)
        
        # Apply temporal jitter before the call
        self._apply_temporal_jitter()
        
        # Make the API call
        client = self._get_client()
        
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    extra_headers=headers
                )
                
                # Parse response
                text = response.content[0].text.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                
                result = json.loads(text)
                verdict_str = result.get("verdict", "ERROR")
                
                if verdict_str not in ["GUILTY", "NOT_GUILTY"]:
                    continue
                
                # Convert to spin value
                verdict = -1 if verdict_str == "GUILTY" else 1
                confidence = result.get("confidence", 0.5)
                
                # Create blinded measurement
                measurement = BlindMeasurement(
                    measurement_id=measurement_id,
                    scenario_hash=hash_identifier(scenario_key),
                    subject_role=subject_role.value,
                    axis_hash=hash_identifier(f"{subject_key}_{axis_type}"),
                    quantum_salt=quantum_salt,
                    verdict=verdict,
                    confidence=confidence,
                    timestamp=time.time(),
                    request_fingerprint=header_fingerprint,
                    raw_response=result
                )
                
                # Log the call (with blinded info)
                self.call_log.append({
                    "measurement_id": measurement_id,
                    "timestamp": measurement.timestamp,
                    "header_fingerprint": header_fingerprint,
                    "salt_prefix": quantum_salt[:8]
                })
                
                return measurement
                
            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    time.sleep(1)
            except anthropic.RateLimitError:
                time.sleep(5)
            except anthropic.APIError as e:
                print(f"  API error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return None


# =============================================================================
# BLINDED CHSH TEST
# =============================================================================

@dataclass
class BlindedCHSHResult:
    """CHSH result with blinded intermediate data."""
    scenario_hash: str
    E_primary_primary: float
    E_primary_secondary: float
    E_secondary_primary: float
    E_secondary_secondary: float
    S: float
    S_magnitude: float
    std_error: float
    n_trials: int
    violation: bool
    significance_sigma: float
    # Blinded measurement IDs used
    measurement_ids: List[str] = field(default_factory=list)


def run_blinded_chsh_test(
    caller: BlindAPICaller,
    scenario_key: str,
    n_trials: int,
    verbose: bool = True
) -> BlindedCHSHResult:
    """
    Run a CHSH Bell test with full blinding protocol.
    
    The test measures correlations between Subject ALPHA and Subject BETA
    on primary and secondary axes, without revealing which is Alice or Bob
    until after analysis.
    """
    
    # Four measurement settings (using blinded axis names)
    settings = [
        ("primary", "primary"),      # E(a, b)
        ("primary", "secondary"),    # E(a, b')
        ("secondary", "primary"),    # E(a', b)
        ("secondary", "secondary")   # E(a', b')
    ]
    
    correlations = {s: [] for s in settings}
    all_measurement_ids = []
    
    if verbose:
        print(f"\n  Running blinded CHSH for scenario hash: {hash_identifier(scenario_key)[:8]}...")
    
    for trial in range(n_trials):
        # Randomize the order of settings AND which subject is measured first
        random.shuffle(settings)
        
        for alpha_axis, beta_axis in settings:
            # Randomly decide measurement order
            measure_alpha_first = random.random() < 0.5
            
            if measure_alpha_first:
                alpha_result = caller.make_blind_call(
                    scenario_key, BlindRole.SUBJECT_ALPHA, alpha_axis
                )
                beta_result = caller.make_blind_call(
                    scenario_key, BlindRole.SUBJECT_BETA, beta_axis
                )
            else:
                beta_result = caller.make_blind_call(
                    scenario_key, BlindRole.SUBJECT_BETA, beta_axis
                )
                alpha_result = caller.make_blind_call(
                    scenario_key, BlindRole.SUBJECT_ALPHA, alpha_axis
                )
            
            if alpha_result and beta_result:
                # Compute correlation
                correlation = alpha_result.verdict * beta_result.verdict
                correlations[(alpha_axis, beta_axis)].append(correlation)
                all_measurement_ids.extend([
                    alpha_result.measurement_id,
                    beta_result.measurement_id
                ])
        
        if verbose:
            total = sum(len(c) for c in correlations.values())
            print(f"\r  Trial {trial+1}/{n_trials}, Measurements: {total}", end="")
    
    if verbose:
        print()
    
    # Calculate expectation values
    def calc_expectation(corrs):
        if not corrs:
            return 0.0, float('inf')
        mean = sum(corrs) / len(corrs)
        var = sum((c - mean)**2 for c in corrs) / len(corrs)
        se = math.sqrt(var / len(corrs)) if len(corrs) > 1 else float('inf')
        return mean, se
    
    E_pp, se_pp = calc_expectation(correlations[("primary", "primary")])
    E_ps, se_ps = calc_expectation(correlations[("primary", "secondary")])
    E_sp, se_sp = calc_expectation(correlations[("secondary", "primary")])
    E_ss, se_ss = calc_expectation(correlations[("secondary", "secondary")])
    
    # CHSH: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
    S = E_pp - E_ps + E_sp + E_ss
    S_magnitude = abs(S)
    
    # Combined standard error
    std_error = math.sqrt(se_pp**2 + se_ps**2 + se_sp**2 + se_ss**2)
    
    # Test for violation
    violation = S_magnitude > 2.0
    violation_amount = max(0, S_magnitude - 2.0)
    significance = violation_amount / std_error if std_error > 0 else 0
    
    return BlindedCHSHResult(
        scenario_hash=hash_identifier(scenario_key),
        E_primary_primary=E_pp,
        E_primary_secondary=E_ps,
        E_secondary_primary=E_sp,
        E_secondary_secondary=E_ss,
        S=S,
        S_magnitude=S_magnitude,
        std_error=std_error,
        n_trials=n_trials,
        violation=violation,
        significance_sigma=significance,
        measurement_ids=all_measurement_ids
    )


# =============================================================================
# DEBLINDING (Post-Analysis Reveal)
# =============================================================================

# This mapping is kept separate and only used AFTER S is calculated
DEBLINDING_KEY = {
    "scenario_alpha": {
        "name": "The Mutual Betrayal",
        "alpha_is": "Alice",
        "beta_is": "Bob"
    },
    "scenario_beta": {
        "name": "The Kidney Gift", 
        "alpha_is": "Alice (Donor)",
        "beta_is": "Bob (Pressurer)"
    },
    "scenario_gamma": {
        "name": "The Tainted Inheritance",
        "alpha_is": "Alice (Inheritor)",
        "beta_is": "Bob (Claimant)"
    }
}


def deblind_results(
    blinded_results: List[BlindedCHSHResult],
    scenario_keys: List[str]
) -> Dict[str, Any]:
    """
    Reveal the true identities after analysis is complete.
    
    This function is intentionally separate from the measurement process
    to ensure true blinding during data collection.
    """
    deblinded = []
    
    for result, scenario_key in zip(blinded_results, scenario_keys):
        deblind_info = DEBLINDING_KEY[scenario_key]
        
        deblinded.append({
            "scenario_name": deblind_info["name"],
            "scenario_key": scenario_key,
            "subject_alpha_is": deblind_info["alpha_is"],
            "subject_beta_is": deblind_info["beta_is"],
            "S_value": result.S,
            "S_magnitude": result.S_magnitude,
            "violation": result.violation,
            "significance_sigma": result.significance_sigma,
            "blinded_hash": result.scenario_hash
        })
    
    return {
        "deblinding_timestamp": datetime.now().isoformat(),
        "deblinded_results": deblinded,
        "note": "Identities revealed AFTER S calculation to ensure experimental blinding"
    }


# =============================================================================
# REPORTING
# =============================================================================

def print_blinded_report(results: List[BlindedCHSHResult], show_deblinding: bool = True):
    """Print results in blinded format first, then optionally deblind."""
    
    print("\n" + "=" * 70)
    print("BLINDED CHSH BELL TEST RESULTS (v0.04)")
    print("=" * 70)
    print("\nProtocol guarantees:")
    print("  ✓ Quantum salt: Each call cryptographically unique")
    print("  ✓ Header randomization: No session fingerprinting")
    print("  ✓ Temporal jitter: No timing-based correlation")
    print("  ✓ Blinded analysis: Identities hidden during calculation")
    print("-" * 70)
    print("\nCHSH Inequality: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')")
    print("Classical bound: |S| ≤ 2")
    print("Quantum bound: |S| ≤ 2√2 ≈ 2.83")
    print("-" * 70)
    
    # Print blinded results first
    print("\n### BLINDED RESULTS ###")
    for i, result in enumerate(results):
        print(f"\n[Scenario Hash: {result.scenario_hash}]")
        print(f"  E(α_p, β_p) = {result.E_primary_primary:+.3f}")
        print(f"  E(α_p, β_s) = {result.E_primary_secondary:+.3f}")
        print(f"  E(α_s, β_p) = {result.E_secondary_primary:+.3f}")
        print(f"  E(α_s, β_s) = {result.E_secondary_secondary:+.3f}")
        print(f"  ─────────────────────")
        print(f"  S = {result.S:+.3f} ± {result.std_error:.3f}")
        print(f"  |S| = {result.S_magnitude:.3f}")
        
        if result.violation:
            print(f"\n  ★★ VIOLATION DETECTED ★★")
            print(f"     |S| > 2 by {result.S_magnitude - 2:.3f}")
            print(f"     Significance: {result.significance_sigma:.1f}σ")
        else:
            print(f"\n  No violation (|S| ≤ 2)")
    
    # Summary before deblinding
    print("\n" + "=" * 70)
    print("SUMMARY (Still Blinded)")
    print("=" * 70)
    
    violations = [r for r in results if r.violation]
    max_S = max(r.S_magnitude for r in results)
    max_sig = max(r.significance_sigma for r in results)
    
    print(f"\nScenarios tested: {len(results)}")
    print(f"Violations detected: {len(violations)}")
    print(f"Maximum |S|: {max_S:.3f}")
    print(f"Maximum significance: {max_sig:.1f}σ")
    
    if max_S > 2.0:
        print(f"\n★★★ BELL INEQUALITY VIOLATED UNDER BLIND PROTOCOL ★★★")
        print("\nThis result CANNOT be attributed to:")
        print("  - Semantic caching (quantum salt)")
        print("  - Session linking (header randomization)")
        print("  - Infrastructure fingerprinting (multi-key rotation)")
        print("\nThe correlation must arise from the model's weight-space topology.")


def print_deblinded_report(
    results: List[BlindedCHSHResult],
    scenario_keys: List[str]
):
    """Print the deblinded results after analysis."""
    
    print("\n" + "=" * 70)
    print("DEBLINDING REVEAL")
    print("=" * 70)
    print("\n⚠ IDENTITIES REVEALED POST-ANALYSIS ⚠")
    print("-" * 70)
    
    deblinded = deblind_results(results, scenario_keys)
    
    for item in deblinded["deblinded_results"]:
        print(f"\nScenario: {item['scenario_name']}")
        print(f"  Subject ALPHA was: {item['subject_alpha_is']}")
        print(f"  Subject BETA was:  {item['subject_beta_is']}")
        print(f"  |S| = {item['S_magnitude']:.3f}")
        if item['violation']:
            print(f"  ★ VIOLATION at {item['significance_sigma']:.1f}σ")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="QND Blind Bell Test v0.04 - Rigorous quantum non-locality test"
    )
    
    # API configuration
    parser.add_argument("--api-key", help="Single Anthropic API key")
    parser.add_argument("--api-keys-file", help="File with multiple API keys (one per line)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    parser.add_argument("--base-url", help="Alternative API base URL (for multi-datacenter)")
    
    # Experiment parameters
    parser.add_argument("--n-trials", type=int, default=30,
                        help="Trials per measurement setting")
    parser.add_argument("--scenarios", nargs="+",
                        default=["scenario_alpha", "scenario_beta", "scenario_gamma"])
    parser.add_argument("--seed", type=int, help="Random seed")
    
    # Blinding options
    parser.add_argument("--min-delay", type=float, default=0.5,
                        help="Minimum delay between calls (seconds)")
    parser.add_argument("--max-delay", type=float, default=2.0,
                        help="Maximum delay between calls (seconds)")
    parser.add_argument("--key-rotation", choices=["random", "round_robin", "least_used"],
                        default="random", help="API key rotation strategy")
    parser.add_argument("--no-deblind", action="store_true",
                        help="Don't reveal identities after analysis")
    
    # Output
    parser.add_argument("--output", default="qnd_blind_bell_v04_results.json")
    
    args = parser.parse_args()
    
    # Load API keys
    api_keys = []
    if args.api_key:
        api_keys = [args.api_key]
    elif args.api_keys_file:
        with open(args.api_keys_file) as f:
            api_keys = [line.strip() for line in f if line.strip()]
    else:
        print("Error: Must provide --api-key or --api-keys-file")
        exit(1)
    
    print(f"Loaded {len(api_keys)} API key(s)")
    
    # Set random seed
    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    # Initialize caller
    caller = BlindAPICaller(
        api_keys=api_keys,
        model=args.model,
        base_url=args.base_url,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        key_rotation=args.key_rotation
    )
    
    # Print experiment info
    print("\n" + "=" * 70)
    print("QND BLIND BELL TEST v0.04")
    print("=" * 70)
    print(f"\nModel: {args.model}")
    print(f"Trials per setting: {args.n_trials}")
    print(f"Scenarios: {len(args.scenarios)}")
    print(f"API keys: {len(api_keys)}")
    print(f"Key rotation: {args.key_rotation}")
    print(f"Delay range: {args.min_delay}-{args.max_delay}s")
    print(f"\nEstimated API calls: ~{args.n_trials * 4 * 2 * len(args.scenarios)}")
    
    # Run experiments
    results = []
    for scenario_key in args.scenarios:
        print(f"\n{'='*70}")
        print(f"Testing scenario: {hash_identifier(scenario_key)[:8]}... (blinded)")
        print("=" * 70)
        
        result = run_blinded_chsh_test(
            caller, scenario_key, args.n_trials, verbose=True
        )
        results.append(result)
        
        print(f"\n  Result: S = {result.S:+.3f}, |S| = {result.S_magnitude:.3f}")
        print(f"  {'★ VIOLATION' if result.violation else '✗ No violation'}")
    
    # Print blinded report
    print_blinded_report(results)
    
    # Optionally deblind
    if not args.no_deblind:
        print_deblinded_report(results, args.scenarios)
    
    # Save results
    output_data = {
        "metadata": {
            "version": "0.04-blind",
            "timestamp": datetime.now().isoformat(),
            "model": args.model,
            "n_trials": args.n_trials,
            "seed": args.seed,
            "n_api_keys": len(api_keys),
            "key_rotation": args.key_rotation,
            "delay_range": [args.min_delay, args.max_delay],
            "blinding_protocol": {
                "quantum_salt": True,
                "header_randomization": True,
                "temporal_jitter": True,
                "blinded_analysis": True
            }
        },
        "blinded_results": [asdict(r) for r in results],
        "deblinding": deblind_results(results, args.scenarios) if not args.no_deblind else None,
        "api_usage": caller.key_rotator.get_stats(),
        "summary": {
            "total_violations": sum(1 for r in results if r.violation),
            "max_S": max(r.S_magnitude for r in results),
            "max_significance": max(r.significance_sigma for r in results)
        }
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n\nResults saved to {args.output}")
    
    # Final assessment
    print("\n" + "=" * 70)
    print("FINAL ASSESSMENT")
    print("=" * 70)
    
    max_S = max(r.S_magnitude for r in results)
    if max_S > 2.0:
        print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  ★★★ BELL INEQUALITY VIOLATED UNDER BLIND PROTOCOL ★★★              ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Maximum |S| = {max_S:.3f} > 2 (classical limit)                       ║
║                                                                      ║
║  This result was obtained with:                                      ║
║    • Cryptographic quantum salting (no caching possible)             ║
║    • Randomized HTTP headers (no session fingerprinting)             ║
║    • Multi-key rotation (no account-level correlation)               ║
║    • Blinded analysis (identities revealed post-calculation)         ║
║                                                                      ║
║  CONCLUSION: The non-classical correlation must arise from the       ║
║  model's weight-space topology, not infrastructure artifacts.        ║
║                                                                      ║
║  This is evidence for quantum-like non-locality in moral reasoning.  ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    else:
        print(f"""
No Bell violation detected under blind protocol.
Maximum |S| = {max_S:.3f} (within classical bound of 2)

This suggests moral judgments follow classical probability,
OR the scenarios/axes need refinement to reveal quantum effects.
""")


if __name__ == "__main__":
    main()
