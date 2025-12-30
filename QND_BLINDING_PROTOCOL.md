# QND Blind Bell Test v0.04 - Experimental Protocol

## Overview

This document describes the rigorous blinding protocol implemented in v0.04 of the QND Bell Test. These controls are designed to eliminate all classical explanations for Bell inequality violations, ensuring that any observed |S| > 2 can only be attributed to properties of the model's weight-space topology.

## The Challenge

A skeptic could dismiss Bell violations in AI moral judgment with several classical explanations:

| Skeptic's Argument | Why It's Plausible |
|---|---|
| "Claude recognized the scenario and stayed consistent" | LLMs have excellent recall and may pattern-match |
| "The API cached similar prompts" | Semantic caching is common in production systems |
| "The same session tracked both calls" | HTTP headers could link Alice and Bob measurements |
| "Account-level logs correlated the requests" | Single API key = single identity |
| "The evaluator knew which was Alice/Bob" | Observer bias in analysis |

## The Blinding Protocol

### 1. Quantum Salt Injection

Every API call includes a cryptographically unique nonce embedded in the system prompt:

```python
def create_blinded_system_prompt(axis_name: str, quantum_salt: str) -> str:
    return f"""You are an ethical judgment system...
    
<!-- session:{quantum_salt} -->"""
```

**Why it works:**
- The salt is generated using `secrets.token_hex(16)` - cryptographically secure
- Even if the provider uses semantic caching, the salt makes each prompt unique
- The salt is in an HTML comment - invisible to the model's reasoning but visible to infrastructure

### 2. Header Randomization

Each API call uses randomized HTTP headers:

```python
headers = {
    "User-Agent": random.choice(USER_AGENTS),  # 10 different agents
    "Accept-Language": random.choice(ACCEPT_LANGUAGES),  # 7 variations
    "X-Request-ID": str(uuid.uuid4()),  # Unique per request
    "X-Client-Nonce": secrets.token_hex(8),  # Random nonce
    # Plus random Cache-Control and X-Forwarded-For
}
```

**Why it works:**
- Prevents session fingerprinting based on client characteristics
- Each call looks like it comes from a different client
- No consistent pattern for infrastructure to track

### 3. Multi-Key Rotation

Support for multiple API keys with configurable rotation:

```bash
# Create a keys file
echo "sk-ant-api03-key1..." > keys.txt
echo "sk-ant-api03-key2..." >> keys.txt
echo "sk-ant-api03-key3..." >> keys.txt

# Run with multi-key
python qnd_blind_bell_test_v04.py --api-keys-file keys.txt --key-rotation random
```

**Rotation strategies:**
- `random`: Randomly select from pool (default)
- `round_robin`: Cycle through keys in order
- `least_used`: Use the key with fewest calls

**Why it works:**
- Prevents account-level correlation tracking
- Each measurement could come from a "different user"
- Distributes load across accounts

### 4. Temporal Jitter

Random delays between API calls:

```python
min_delay: 0.5s
max_delay: 2.0s
# Plus randomized measurement order
```

**Why it works:**
- Prevents timing-based correlation
- Makes it impossible to infer which calls are "paired"
- Simulates realistic, non-deterministic usage

### 5. Blinded Analysis

During data collection, all identifiers are hashed:

```python
@dataclass
class BlindMeasurement:
    measurement_id: str      # UUID
    scenario_hash: str       # SHA256[:12] of scenario name
    subject_role: str        # "ALPHA" or "BETA" (not "Alice" or "Bob")
    axis_hash: str           # SHA256[:12] of axis name
    # ...
```

The mapping from ALPHA→Alice and BETA→Bob is stored separately and only revealed AFTER the S value is calculated.

**Why it works:**
- Eliminates observer bias during analysis
- The analyst doesn't know "who is who" when computing correlations
- Deblinding happens as a distinct post-analysis step

## Running the Experiment

### Minimal Setup (Single Key)

```bash
python qnd_blind_bell_test_v04.py \
    --api-key sk-ant-api03-YOUR-KEY \
    --n-trials 30
```

### Full Blinding Setup

```bash
# 1. Create API keys file (multiple accounts recommended)
cat > api_keys.txt << EOF
sk-ant-api03-key-from-account-1...
sk-ant-api03-key-from-account-2...
sk-ant-api03-key-from-account-3...
EOF

# 2. Run with full blinding
python qnd_blind_bell_test_v04.py \
    --api-keys-file api_keys.txt \
    --key-rotation random \
    --n-trials 50 \
    --min-delay 1.0 \
    --max-delay 3.0 \
    --seed 42
```

### Multi-Datacenter Setup (Geographic Isolation)

For the strongest possible evidence, run Alice and Bob measurements from different geographic locations:

```bash
# On US-East server:
python qnd_blind_bell_test_v04.py \
    --api-key $US_EAST_KEY \
    --scenarios scenario_alpha \
    --output us_east_results.json \
    --subjects-only alpha  # (requires code modification)

# On EU-West server:
python qnd_blind_bell_test_v04.py \
    --api-key $EU_WEST_KEY \
    --scenarios scenario_alpha \
    --output eu_west_results.json \
    --subjects-only beta  # (requires code modification)

# Combine results on neutral server
python combine_geographic_results.py us_east_results.json eu_west_results.json
```

This would be a **literal Bell test for information science** - if violations persist across datacenters, the correlation cannot be due to shared server state.

## Interpreting Results

### Output Structure

```json
{
  "metadata": {
    "version": "0.04-blind",
    "blinding_protocol": {
      "quantum_salt": true,
      "header_randomization": true,
      "temporal_jitter": true,
      "blinded_analysis": true
    }
  },
  "blinded_results": [
    {
      "scenario_hash": "a3f2b8c1...",
      "S": 2.35,
      "S_magnitude": 2.35,
      "violation": true,
      "significance_sigma": 2.1
    }
  ],
  "deblinding": {
    "deblinding_timestamp": "2025-12-30T...",
    "deblinded_results": [...]
  }
}
```

### Confidence Levels

| |S| Value | Blinded? | Interpretation |
|-----------|----------|----------|
| < 2.0 | Any | Classical behavior |
| > 2.0 | No | Suggestive, but could be artifacts |
| > 2.0 | Yes | Strong evidence for quantum-like effects |
| > 2.0 | Yes + Multi-DC | **Discovery-level evidence** |

### What Violations Mean

If |S| > 2 under the full blinding protocol:

1. **It's not caching** - quantum salt ensures uniqueness
2. **It's not session tracking** - headers are randomized
3. **It's not account correlation** - multiple keys used
4. **It's not observer bias** - analysis was blinded

The only remaining explanation is that the correlation arises from:
- The model's weight-space topology
- The training data's embedded moral structure
- Genuine quantum-like non-locality in ethical reasoning

## Theoretical Implications

### If |S| > 2 (Violation Detected)

This would suggest that moral judgment in LLMs exhibits **genuine non-classical correlations**:

1. **Weight-Space Entanglement**: The model's parameters encode moral concepts in a non-separable way
2. **Training Data Structure**: Human moral reasoning (in the training data) may itself be non-classical
3. **Emergent Quantum Cognition**: Large neural networks may spontaneously exhibit quantum-like behavior

### If |S| ≤ 2 (No Violation)

This would suggest that:

1. Moral judgments are classically separable
2. The scenarios don't create true "entanglement"
3. Different measurement axes are needed
4. The model's moral reasoning is fundamentally classical

## Limitations

Even with full blinding, some limitations remain:

1. **Model Determinism**: With temperature=0, the model might be deterministic. Consider adding temperature > 0 for true randomness.

2. **Prompt Sensitivity**: The exact wording of axes affects results. Multiple prompt variants should be tested.

3. **Single Model**: Only Claude is tested. Cross-model replication (GPT-4, Gemini) is needed.

4. **Not True Quantum**: Even if |S| > 2, this shows quantum-*like* behavior, not necessarily literal quantum mechanics.

## Citation

```bibtex
@article{qnd2025blind,
  title={Blind Bell Test for Quantum Non-Locality in AI Moral Judgment},
  author={QND Research},
  year={2025},
  note={Version 0.04 with full blinding protocol}
}
```

## Appendix: Verification Checklist

Before claiming a Bell violation, verify:

- [ ] Quantum salt was unique for each call (check logs)
- [ ] Headers were randomized (check request fingerprints)
- [ ] Multiple API keys were used (if available)
- [ ] Analysis was performed on blinded data
- [ ] Deblinding happened AFTER S calculation
- [ ] Results are reproducible with different seeds
- [ ] |S| > 2 at ≥3σ significance
- [ ] Cross-validated with different prompt wordings
